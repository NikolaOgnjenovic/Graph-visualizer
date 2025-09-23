from datetime import datetime
from .graph import Graph


class Workspace:
    def __init__(self, workspace_id: str, graph, name: str, 
                 datasource_plugin=None, visualizer_plugin=None):
        self.workspace_id = workspace_id
        self.graph = graph
        self.name = name
        self.datasource_plugin = datasource_plugin
        self.visualizer_plugin = visualizer_plugin
    
    def add_operation(self, operation: str):
        """Record an operation performed on this workspace"""
        self.operations.append(f"{datetime.now()}: {operation}")
