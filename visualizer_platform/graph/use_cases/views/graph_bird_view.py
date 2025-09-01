from API.graph.services.plugin import VisualizerPlugin
from jinja2 import Environment, FileSystemLoader
from API.graph.models.graph import Graph
import os


class BirdView(object):
    @staticmethod
    def render(graph: Graph, visualizer_plugin: VisualizerPlugin) -> str:
        """
        Returns the required body HTML content (the minimap JS) that needs to be included
        in the page to provide the bird/minimap view. The implementation does not require
        the visualizer output directly, as it subscribes to GraphMain events.
        :param graph: Graph data to be rendered (unused here).
        :param visualizer_plugin: Visualizer plugin to be used (unused here).
        :return: HTML string that should be included in the page.
        """
        current_dir = os.path.dirname(__file__)
        templates_dir = os.path.join(current_dir, '..', '..', '..', 'templates')
        templates_dir = os.path.abspath(templates_dir)

        env = Environment(loader=FileSystemLoader(templates_dir))

        # Render the JS body that draws and syncs the minimap
        template = env.get_template('graph-bird-view-body.html')

        body_html = template.render()
        return body_html
