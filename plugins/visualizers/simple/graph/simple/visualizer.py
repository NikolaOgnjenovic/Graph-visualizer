from pathlib import Path
from typing import Any
from jinja2 import Environment, FileSystemLoader, PackageLoader, ChoiceLoader
from API.graph.services import VisualizerPlugin
from API.graph.models.graph import Graph, Node, Edge


class SimpleVisualizer(VisualizerPlugin):
    def name(self) -> str:
        return "Simple graph visualizer"

    def identifier(self) -> str:
        return "simple_graph_visualizer"

    @staticmethod
    def _node_to_dict(node: Node) -> dict[str, Any]:
        return {
            "node_id": node.node_id,
            "attributes": node.attributes,
            "name": node.name,
        }

    @staticmethod
    def _edge_to_dict(edge: Edge) -> dict[str, Any]:
        return {
            "source": edge.source.node_id,
            "target": edge.destination.node_id,
            "direction": edge.direction.name,
            "attributes": edge.attributes,
        }

    def visualize(self, graph: Graph) -> str:
        # Build absolute path to the templates directory
        base_path = Path(__file__).resolve().parent
        templates_path = (base_path / ".." / ".." / "templates").resolve()

        # Initialize Jinja2 environment with a ChoiceLoader so it works from source and from installed package.
        loaders = [FileSystemLoader(str(templates_path))]
        try:
            loaders.append(PackageLoader("graph.simple", "templates"))
        except Exception:
            pass
        env = Environment(loader=ChoiceLoader(loaders))
        template = env.get_template("simple_graph_template.html")

        # Prepare context
        context = {
            "nodes": [self._node_to_dict(node) for node in graph.nodes],
            "edges": [self._edge_to_dict(edge) for edge in graph.edges],
        }

        # Render HTML
        return template.render(context)
