import uuid
from enum import Enum
from typing import List, Dict, Any


class GraphDirection(Enum):
    """
    Direction of an edge in a graph.

    - DIRECTED: The edge goes from source to destination only.
    - UNDIRECTED: The edge connects nodes symmetrically.
    """
    DIRECTED = 0
    UNDIRECTED = 1


class Node:
    """
    A vertex in a graph.

    Attributes:
        node_id: Stable identifier of the node within a graph.
        name: Human-readable label of the node.
        attributes: Arbitrary key-value mapping attached to the node.
    """

    def __init__(self, name: str, node_id: str):
        """
        Create a new node.

        :param name: Display name of the node.
        :param node_id: Unique identifier of the node (stringified if not str elsewhere).
        """
        self.node_id: str = node_id
        self.name: str = name
        self.attributes: Dict[str, Any] = {}

    def add_attribute(self, atr: str, value: Any) -> None:
        """Attach or overwrite an attribute on this node.

        :param atr: Attribute name.
        :type atr: str
        :param value: Attribute value.
        :type value: Any
        :rtype: None
        """
        self.attributes[atr] = value

    def remove_attribute(self, atr: str) -> None:
        """Remove an attribute from this node. KeyError if missing.

        :param atr: Attribute name to remove.
        :type atr: str
        :rtype: None
        """
        del self.attributes[atr]

    def __str__(self) -> str:
        """Human-friendly representation: "<id>: <name>".

        :rtype: str
        """
        return self.node_id + ': ' + self.name

    def __hash__(self) -> int:
        """
        Hash based on the string representation. Note: this ties hashing to node_id and name.
        Nodes are typically identified by node_id; ensure node_id stability if used as dict keys.

        :rtype: int
        """
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
        """
        Equality is based on node_id only. Two Node instances with the same node_id are considered equal.

        :param other: Object to compare against.
        :type other: object
        :rtype: bool
        """
        if not isinstance(other, Node):
            return NotImplemented
        return self.node_id == other.node_id


class Edge:
    """
    A connection between two nodes.

    Attributes:
        source: Source node of the edge.
        destination: Destination node of the edge.
        direction: GraphDirection indicating whether the edge is directed or undirected.
        attributes: Arbitrary key-value mapping attached to the edge.
    """

    def __init__(self, source: Node, dest: Node, direction: GraphDirection):
        """Create a new edge between source and dest.

        :param source: Source node.
        :type source: Node
        :param dest: Destination node.
        :type dest: Node
        :param direction: Direction type.
        :type direction: GraphDirection
        """
        self.source: Node = source
        self.destination: Node = dest
        self.direction: GraphDirection = direction
        self.attributes: Dict[str, Any] = {}

    def add_attribute(self, atr: str, value: Any) -> None:
        """Attach or overwrite an attribute on this edge.

        :param atr: Attribute name.
        :type atr: str
        :param value: Attribute value.
        :type value: Any
        :rtype: None
        """
        self.attributes[atr] = value

    def remove_attribute(self, atr: str) -> None:
        """Remove an attribute from this edge. KeyError if missing.

        :param atr: Attribute name to remove.
        :type atr: str
        :rtype: None
        """
        del self.attributes[atr]

    def __str__(self) -> str:
        """Human-friendly representation: "<src_id> + <dst_id>".

        :rtype: str
        """
        return self.source.node_id + " + " + self.destination.node_id


class Graph(object):
    """
    A simple in-memory graph model with a list of nodes and edges.

    Attributes:
        graph_id: UUID identifying this graph instance.
        nodes: Collection of nodes belonging to the graph.
        edges: Collection of edges belonging to the graph.
    """

    def __init__(self, nodes: List[Node], edges: List[Edge], graph_id: uuid.UUID = None):
        """
        Create a new Graph instance.

        :param nodes: Nodes comprising the graph.
        :type nodes: List[Node]
        :param edges: Edges connecting the nodes.
        :type edges: List[Edge]
        :param graph_id: Optional fixed UUID. If omitted, a new one is generated.
        :type graph_id: uuid.UUID | None
        :rtype: None
        """
        self.graph_id = graph_id or uuid.uuid4()
        self.nodes: List[Node] = nodes
        self.edges: List[Edge] = edges