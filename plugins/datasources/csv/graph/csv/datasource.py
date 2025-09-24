from API.graph.models.graph import Graph, Node, Edge, GraphDirection
from API.graph.services import DataSourcePlugin
from typing import Any, Iterator
import itertools
import csv
from io import StringIO


class CsvTreeLoader(DataSourcePlugin):
    """
    Load a CSV document into a Graph structure.

    The loader treats the input CSV as a tree under a synthetic ROOT node and
    then adds extra edges for cross-references detected via common reference
    keys (e.g., "ref", "reference", "parent_ref").

    Behavior summary:
    - First row is treated as header (column names)
    - Each subsequent row becomes a child node under ROOT
    - Column values are stored as attributes on the row nodes using header names
    - After the tree is built, additional directed edges are created when a
      node has attributes named in {ref, refs, parent_ref, child_ref, link,
      reference}. The referenced value is matched against the target node name, or
      against attributes "id" or "node_id" of nodes.
    - Orphaned nodes (whitout incoming edges) are connected to ROOT
    """

    def __init__(self):
        self._uid = itertools.count()

    def name(self) -> str:
        """
        Retrieves the name of this datasource plugin.

        :return: Human-readable plugin name.
        :rtype: str
        """
        return "CSV to graph loader"

    def identifier(self) -> str:
        """
        Retrieves a stable identifier for this datasource plugin.

        :return: Unique plugin identifier used by the plugin system.
        :rtype: str
        """
        return "csv_to_graph_loader"

    def load(self, csv_string: str) -> Graph:
        """
        Parse the CSV string and convert it into a Graph.

        :param csv_string: CSV content to parse.
        :type csv_string: str
        :return: Graph containing nodes and edges derived from the CSV.
        :rtype: Graph
        """
        # Create a fresh per-call context
        ctx = _BuildContext(uid=self._uid)

        # Parse CSV
        csv_reader = csv.reader(StringIO(csv_string.strip()))
        rows = list(csv_reader)
        
        if not rows:
            return Graph([], [])

        # First row is header
        headers = [header.strip() for header in rows[0]]
        
        # Create root node
        root = ctx.new_node("ROOT")
        ctx.add_vertex(root)

        # Build tree from CSV rows
        self._build_tree_from_csv_rows(ctx, root, rows[1:], headers)

        # Post-process cross-references
        self._link_cross_references(ctx)

        # Link orphaned nodes to root
        self._link_orphaned_nodes_to_root(ctx, root)

        return Graph(ctx.vertices, ctx.edges)

    def _build_tree_from_csv_rows(self, ctx: "_BuildContext", parent: Node, data_rows: list, headers: list) -> None:
        """
        Convert CSV rows into nodes and connect them to parent node.

        Each row becomes a node with attributes from column values.
        Only the first node is connected directly to parent; other nodes
        rely on cross-references for connections.

        :param ctx: Build context holding vertices/edges and UID generator.
        :type ctx: _BuildContext
        :param parent: Node to attach the first newly created node to.
        :type parent: Node
        :param data_rows: CSV data rows (excluding header).
        :type data_rows: list
        :param headers: Column headers from first row.
        :type headers: list
        :rtype: None
        """

        first_node = None

        for row_index, row in enumerate(data_rows, start=1):
            if not row:  # Skip empty rows
                continue
                
            # Create node for this row (use first column value as name or generic name)
            node_name = row[0] if row and row[0] else f"row_{row_index}"
            row_node = ctx.new_node(node_name)
            
            # Add all columns as attributes
            for col_index, value in enumerate(row):
                if col_index < len(headers) and value is not None and value != "":
                    row_node.add_attribute(headers[col_index], value)
            
            # Add row index as attribute
            row_node.add_attribute("row_index", row_index)

            # Store first node for ROOT connection
            if row_index == 1:
                first_node = row_node
            
            ctx.add_vertex(row_node)
        
        # Connect ROOT only to the first node
        if first_node:
            ctx.connect(parent, first_node)

    def _link_cross_references(self, ctx: "_BuildContext") -> None:
        """
        Add edges based on cross-reference attributes present on nodes.

        The following attribute names are recognized (case-insensitive):
        {"ref", "refs", "parent_ref", "child_ref", "link", "reference"}.
        When such an attribute holds a string value, it is matched against node
        names and against node attributes "id" and "node_id".

        :param ctx: Build context with current graph data.
        :type ctx: _BuildContext
        :rtype: None
        """
        keywords = {"ref", "refs", "parent_ref", "child_ref", "link", "reference"}
    
        for node in ctx.vertices:
            for attr_key, attr_val in list(node.attributes.items()):
                if isinstance(attr_val, str) and attr_key.strip().lower() in keywords:
                    references = [ref.strip() for ref in attr_val.split(',')]
                    
                    for ref in references:
                        if ref:  # Skipping empty references
                            target = self._find_by_name(ctx, ref)
                            if target:
                                ctx.connect(node, target)

    def _link_orphaned_nodes_to_root(self, ctx: "_BuildContext", root: Node) -> None:
        """
        Connect all nodes that have no incoming edges (except from ROOT) to the ROOT node.
        This ensures the graph has a single entry point and no disconnected nodes.

        :param ctx: Build context with current graph data.
        :type ctx: _BuildContext
        :param root: Root node to connect orphaned nodes to.
        :type root: Node
        :rtype: None
        """
        # Find all nodes that are not ROOT
        non_root_nodes = [node for node in ctx.vertices if node.name != "ROOT"]
        
        if not non_root_nodes:
            return
        
        # Set of nodes that have incoming edges
        nodes_with_incoming_edges = set()
        for edge in ctx.edges:
            if edge.destination != root:  # Ignore incoming edges from ROOT
                nodes_with_incoming_edges.add(edge.destination)
        
        # Find orphaned nodes
        orphaned_nodes = [node for node in non_root_nodes if node not in nodes_with_incoming_edges]
        
        # Link orphaned nodes to ROOT
        for orphan in orphaned_nodes:
            ctx.connect(root, orphan)

    def _find_by_name(self, ctx: "_BuildContext", target_name: str) -> Node | None:
        """
        Find a node by name, or by attributes "id"/"node_id" matching target_name.
        Matching is case-insensitive and ignores surrounding whitespace.

        :param ctx: Build context with nodes to search in.
        :type ctx: _BuildContext
        :param target_name: Name or id to match.
        :type target_name: str
        :return: The matching node if found, otherwise None.
        :rtype: Node | None
        """
        t = target_name.strip().lower()
        for node in ctx.vertices:
            if node.name.lower() == t:
                return node
            for attr in ("id", "node_id"):
                val = str(node.attributes.get(attr, "")).strip().lower()
                if val == t:
                    return node
        return None


class _BuildContext:
    """Mutable build state used during a single load() call."""
    def __init__(self, uid: Iterator[int]):
        """
        :param uid: An iterator yielding unique integer ids for nodes.
        :type uid: Iterator[int]
        :rtype: None
        """
        self._uid_iter: Iterator[int] = uid
        self.vertices: list[Node] = []
        self.edges: list[Edge] = []

    def new_node(self, name: str) -> Node:
        """
        Create a new Node with an auto-incremented string id.

        :param name: Name to assign to the node.
        :type name: str
        :return: Newly created node.
        :rtype: Node
        """
        return Node(name, str(next(self._uid_iter)))

    def add_vertex(self, node: Node) -> None:
        """
        Register a node in the current graph under construction.

        :param node: Node to add to the vertices collection.
        :type node: Node
        :rtype: None
        """
        self.vertices.append(node)

    def connect(self, src: Node, dst: Node) -> None:
        """
        Append a directed edge from src to dst.

        :param src: Source node.
        :type src: Node
        :param dst: Destination node.
        :type dst: Node
        :rtype: None
        """
        self.edges.append(Edge(src, dst, GraphDirection.DIRECTED))