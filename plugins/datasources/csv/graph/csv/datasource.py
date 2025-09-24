import itertools
from API.graph.services import DataSourcePlugin
from API.graph.models.graph import Graph, Node, Edge, GraphDirection
from typing import Any, Iterator


class CsvTreeLoader(DataSourcePlugin):
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
       
        return Graph([],[])
    
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