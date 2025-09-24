from API.graph.models.graph import Graph, Node, Edge, GraphDirection
from API.graph.services import DataSourcePlugin
from typing import Iterator
import itertools
import csv
from io import StringIO

class CsvTreeLoader(DataSourcePlugin):
    def __init__(self):
        self._uid = itertools.count()

    def name(self) -> str:
        return "CSV to graph loader"

    def identifier(self) -> str:
        return "csv_to_graph_loader"

    def load(self, csv_string: str) -> Graph:
        ctx = _BuildContext(uid=self._uid)

        # Parse CSV
        csv_reader = csv.reader(StringIO(csv_string.strip()))
        rows = list(csv_reader)
        if not rows:
            return Graph([], [])

        headers = [h.strip() for h in rows[0]]
        root = ctx.new_node("ROOT")
        ctx.add_vertex(root)

        # Create all nodes
        for row_index, row in enumerate(rows[1:], start=1):
            if not row:
                continue
            node_name = row[0] or f"row_{row_index}"
            node = ctx.new_node(node_name)
            for col_index, value in enumerate(row):
                if col_index < len(headers) and value:
                    node.add_attribute(headers[col_index], value)
            node.add_attribute("row_index", row_index)
            ctx.add_vertex(node)
            ctx.connect(root, node)  # Attach each node to ROOT by default

        # Add edges for cross-references
        self._link_cross_references(ctx)

        return Graph(ctx.vertices, ctx.edges)

    def _link_cross_references(self, ctx: "_BuildContext") -> None:
        keywords = {"ref", "refs", "parent_ref", "child_ref", "link", "reference"}

        # Build lookup map
        node_map = {}
        for node in ctx.vertices:
            node_map[node.name.lower()] = node
            for attr in ("id", "node_id"):
                if attr in node.attributes:
                    node_map[str(node.attributes[attr]).strip().lower()] = node

        created_edges = set()
        for node in ctx.vertices:
            for attr_key, attr_val in list(node.attributes.items()):
                if isinstance(attr_val, str) and attr_key.lower() in keywords:
                    refs = [r.strip() for r in attr_val.split(",") if r.strip()]
                    for ref in refs:
                        target = node_map.get(ref.lower())
                        if target and target != node:
                            edge_key = (node.name, target.name)
                            if edge_key not in created_edges:
                                ctx.connect(node, target)
                                created_edges.add(edge_key)

class _BuildContext:
    def __init__(self, uid: Iterator[int]):
        self._uid_iter = uid
        self.vertices = []
        self.edges = []
        self._edge_set = set()

    def new_node(self, name: str) -> Node:
        return Node(name, str(next(self._uid_iter)))

    def add_vertex(self, node: Node) -> None:
        self.vertices.append(node)

    def connect(self, src: Node, dst: Node) -> None:
        edge_key = (src.name, dst.name)
        if edge_key not in self._edge_set:
            self.edges.append(Edge(src, dst, GraphDirection.DIRECTED))
            self._edge_set.add(edge_key)