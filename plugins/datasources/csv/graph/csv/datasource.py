from API.graph.models.graph import Graph, Node, Edge, GraphDirection
from API.graph.services import DataSourcePlugin
from typing import Any, Iterator
import itertools
import csv
from io import StringIO
from collections import deque


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

        print("LOADING ENDED")

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
        Add edges based on cross-reference attributes, avoiding duplicates and cycles.
        """
        keywords = {"ref", "refs", "parent_ref", "child_ref", "link", "reference"}
        
        # Create a mapping for faster lookup
        node_map = {}
        for node in ctx.vertices:
            node_map[node.name.lower()] = node
            for attr in ("id", "node_id"):
                if attr in node.attributes:
                    node_map[str(node.attributes[attr]).strip().lower()] = node
        
        # Track already created edges to avoid duplicates
        created_edges = set()
        
        for node in ctx.vertices:
            for attr_key, attr_val in list(node.attributes.items()):
                if (isinstance(attr_val, str) and 
                    attr_key.strip().lower() in keywords):
                    
                    references = [ref.strip() for ref in attr_val.split(',')]
                    for ref in references:
                        if ref:  # Skip empty references
                            target = node_map.get(ref.lower())
                            if target and target != node:  # Avoid self-references
                                edge_key = (node.name, target.name)
                                if edge_key not in created_edges:
                                    ctx.connect(node, target)
                                    created_edges.add(edge_key)

    def _find_by_name(self, ctx: "_BuildContext", target_name: str) -> Node | None:
        """
        Find a node by name, or by attributes "id"/"node_id" matching target_name.
        Uses pre-built mapping for efficiency.
        """
        # This method can be simplified or removed if we use the mapping approach above
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
    def __init__(self, uid: Iterator[int]):
        self._uid_iter: Iterator[int] = uid
        self.vertices: list[Node] = []
        self.edges: list[Edge] = []
        self._edge_set: set[tuple[str, str]] = set()  # Track edges by (src_name, dst_name)

    def new_node(self, name: str) -> Node:
        return Node(name, str(next(self._uid_iter)))

    def add_vertex(self, node: Node) -> None:
        self.vertices.append(node)

    def connect(self, src: Node, dst: Node) -> None:
        """Append a directed edge from src to dst, avoiding duplicates."""
        edge_key = (src.name, dst.name)
        if edge_key not in self._edge_set:
            self.edges.append(Edge(src, dst, GraphDirection.DIRECTED))
            self._edge_set.add(edge_key)