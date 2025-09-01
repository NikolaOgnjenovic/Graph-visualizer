from importlib.metadata import entry_points
from typing import List, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from API.graph.services import DataSourcePlugin, VisualizerPlugin  # type: ignore
else:
    DataSourcePlugin = Any  # type: ignore
    VisualizerPlugin = Any  # type: ignore


class PluginService(object):

    def __init__(self):
        self.datasource_plugins: dict[str, List[DataSourcePlugin]] = {}
        self.visualizer_plugins: dict[str, List[VisualizerPlugin]] = {}

    def load_datasource_plugins(self, group: str) -> None:
        """
        Dynamically loads datasource plugins based on entrypoint group.
        """
        self.datasource_plugins[group] = []
        for ep in entry_points(group=group):
            p = ep.load()
            plugin: DataSourcePlugin = p()
            self.datasource_plugins[group].append(plugin)

    def load_visualizer_plugins(self, group: str) -> None:
        """
        Dynamically loads visualizer plugins based on entrypoint group.
        """
        self.visualizer_plugins[group] = []
        for ep in entry_points(group=group):
            p = ep.load()
            plugin: VisualizerPlugin = p()
            self.visualizer_plugins[group].append(plugin)
