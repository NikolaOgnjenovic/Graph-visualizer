from django.apps import AppConfig

from visualizer_platform.graph.use_cases.plugin_recognition import PluginService
from visualizer_platform.graph.use_cases.const import DATASOURCE_GROUP, VISUALIZER_GROUP
from visualizer_platform.graph.services.workspace_service import WorkspaceService


class GraphVisualizerConfig(AppConfig):
    name = "graph_visualizer"
    plugin_service = PluginService()
    workspace_service = WorkspaceService()

    def ready(self):
        self.plugin_service.load_datasource_plugins(DATASOURCE_GROUP)
        self.plugin_service.load_visualizer_plugins(VISUALIZER_GROUP)
