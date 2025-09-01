from django.apps import AppConfig

from platform.graph.use_cases.plugin_recognition import PluginService
from platform.graph.use_cases.const import DATASOURCE_GROUP, VISUALIZER_GROUP


class GraphVisualizerConfig(AppConfig):
    plugin_service = PluginService()

    def ready(self):
        self.plugin_service.load_datasource_plugins(DATASOURCE_GROUP)
        self.plugin_service.load_visualizer_plugins(VISUALIZER_GROUP)