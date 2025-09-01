from API.graph.models.graph import Graph
from abc import abstractmethod, ABC


class Plugin(ABC):
    @abstractmethod
    def name(self) -> str:
        """
        Retrieves the name of the data source plugin.

        :return: The name of the data source plugin.
        :rtype: str
        """
        pass

    @abstractmethod
    def identifier(self) -> str:
        """
        Retrieves a unique identifier for the data source plugin.

        :return: The unique identifier of the data source plugin.
        :rtype: str
        """
        pass

class DataSourcePlugin(Plugin):
    """
    An abstraction representing a plugin for loading graph data from a specific data source.
    """

    @abstractmethod
    def load(self, content: str) -> Graph:
        """
        Loads data from the data source and returns it as Graph structure.

        :param content: String value of the data source file.
        :type content: str
        :return: Graph objects from the datasource.
        :rtype: Graph
        """
        pass

class VisualizerPlugin(Plugin):
    """
    An abstraction representing a plugin for visualizing graph structures.
    """

    @abstractmethod
    def visualize(self, graph: Graph) -> str:
        """
        Visualizes the graph loaded from the datasource plugin.

        :param graph: Graph loaded from the datasource plugin.
        :type graph: Graph
        :return: Rendered html string.
        :rtype: str
        """
        pass