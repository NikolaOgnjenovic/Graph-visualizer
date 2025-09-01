from API.graph.models.graph import Graph, Node, Edge, GraphDirection
from API.graph.services import DataSourcePlugin
from typing import Any, Iterator
import itertools
import json


class JsonTreeLoader(DataSourcePlugin):
    """
    Load a JSON document into a Graph structure.

    The loader treats the input JSON as a tree under a synthetic ROOT node and
    then adds extra edges for cross-references detected via common reference
    keys (e.g., "ref", "reference", "parent_ref").

    Behavior summary:
    - For each JSON object (dict), a child node is created under the current
      parent. The child node's name is the key under which the object appears;
      when not available, it defaults to "object".
    - For arrays (list), each item is processed with the same label (defaults to
      "item" when no label is available).
    - Primitive values (str, int, bool, etc.) are stored as attributes on the
      current node using the corresponding key as the attribute name.
    - After the tree is built, additional directed edges are created when a
      node has attributes named in {ref, refs, parent_ref, child_ref, link,
      reference}. The referenced value is matched against the target node name, or
      against attributes "id" or "node_id" of nodes.
    """

    def __init__(self):
        self._uid = itertools.count()

    def name(self) -> str:
        """
        Retrieves the name of this datasource plugin.

        :return: Human-readable plugin name.
        :rtype: str
        """
        return "JSON to graph loader"

    def identifier(self) -> str:
        """
        Retrieves a stable identifier for this datasource plugin.

        :return: Unique plugin identifier used by the plugin system.
        :rtype: str
        """
        return "json_to_graph_loader"

    def load(self, json_string: str) -> Graph:
        """
        Parse the JSON string and convert it into a Graph.

        :param json_string: JSON content to parse.
        :type json_string: str
        :return: Graph containing nodes and edges derived from the JSON.
        :rtype: Graph
        """
        # Create a fresh per-call context
        ctx = _BuildContext(uid=self._uid)
        parsed = json.loads(json_string)

        root = ctx.new_node("ROOT")
        ctx.add_vertex(root)

        # Build tree
        self._build_tree(ctx, root, parsed)

        # Post-process cross-references
        self._link_cross_references(ctx)

        return Graph(ctx.vertices, ctx.edges)

    def _build_tree(self, ctx: "_BuildContext", parent: Node, content: Any, label: str | None = None) -> None:
        """
        Recursively convert JSON content into nodes and attributes.

        :param ctx: Build context holding vertices/edges and UID generator.
        :type ctx: _BuildContext
        :param parent: Node to attach newly created nodes/attributes to.
        :type parent: Node
        :param content: The current JSON fragment (dict, list, or primitive).
        :type content: Any
        :param label: Name to use for the node/attribute derived from content.
        :type label: str | None
        :rtype: None
        """
        if isinstance(content, dict):
            # For dicts, the parent receives a child node named by label (or 'object')
            child = ctx.new_node(label or "object")
            for k, v in content.items():
                self._build_tree(ctx, child, v, k)
            ctx.connect(parent, child)
            ctx.add_vertex(child)
        elif isinstance(content, list):
            for item in content:
                # Lists repeat the same label for each item (default 'item')
                self._build_tree(ctx, parent, item, label or "item")
        else:
            if content is not None and label is not None:
                parent.add_attribute(label, content)

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
                    target = self._find_by_name(ctx, attr_val)
                    if target:
                        ctx.connect(node, target)

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
