from API.graph.services.plugin import VisualizerPlugin
from jinja2 import Environment, FileSystemLoader
from API.graph.models.graph import Graph
import os


class MainView(object):
    @staticmethod
    def render(graph: Graph, visualizer_plugin: VisualizerPlugin) -> str:
        """
        Returns the required body html content that needs to be included in page
        in order to provide main view layout.
        :param graph: Graph data to be rendered.
        :param visualizer_plugin: Visualizer plugin to be used.
        :return: html body string that should be included in page.
        """
        main_view = visualizer_plugin.visualize(graph)
        current_dir = os.path.dirname(__file__)
        templates_dir = os.path.join(current_dir, '..', '..', '..', 'templates')
        templates_dir = os.path.abspath(templates_dir)

        env = Environment(loader=FileSystemLoader(templates_dir))

        template = env.get_template('graph-main-view.html')

        body_html = template.render(body=main_view)
        return body_html
