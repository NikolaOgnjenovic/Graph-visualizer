from API.graph.models.graph import Graph, Node, Edge, GraphDirection
from API.graph.services import DataSourcePlugin
from typing import Any, Iterator
from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ETree
import itertools


class XmlTreeLoader(DataSourcePlugin):
    """
    Load an XML document into a Graph structure.

    The loader treats the input XML as a tree under a synthetic ROOT node and
    then adds extra edges for cross-references detected via common reference
    keys (e.g., "ref", "reference", "parent_ref").

    Behavior summary:
    - For each XML object (dict), a child node is created under the current
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
        return "XML to graph loader"

    def identifier(self) -> str:
        """
        Retrieves a stable identifier for this datasource plugin.

        :return: Unique plugin identifier used by the plugin system.
        :rtype: str
        """
        return "xml_to_graph_loader"

    def load(self, xml_string: str) -> Graph:
        """
        Parse the XML string and convert it into a Graph.

        :param xml_string: XML content to parse.
        :type xml_string: str
        :return: Graph containing nodes and edges derived from the XML.
        :rtype: Graph
        """
        # Parse XML
        try:
            root_element: Element = ETree.fromstring(xml_string)
        except ETree.ParseError as e:
            raise ValueError(f"Invalid XML input: {e}")

        # Build context
        ctx = _BuildContext(self._uid)

        # Create synthetic root node
        root_node = ctx.new_node("ROOT")
        ctx.add_vertex(root_node)

        # Recursively build the tree starting from XML root
        self._build_tree_from_element(ctx, root_node, root_element)

        # Add cross-reference edges (ref, parent_ref, etc.)
        self._link_cross_references(ctx)

        # Construct the final Graph
        return Graph(ctx.vertices, ctx.edges)



    def _build_tree_from_element(self, ctx: "_BuildContext", parent: Node, element: Element) -> None:
        """
        Recursively build the tree from an XML Element.
        """
        # Create a node for this element
        current = ctx.new_node(element.tag)

        # Add attributes as node attributes
        for attr_name, attr_value in element.attrib.items():
            current.add_attribute(attr_name, attr_value)

        # If element has text, store it too (ignore pure whitespace)
        text = (element.text or "").strip()
        if text:
            current.add_attribute("value", text)

        # Recurse into children
        for child in element:
            self._build_tree_from_element(ctx, current, child)

        # Attach this element's node under parent
        ctx.connect(parent, current)
        ctx.add_vertex(current)


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
