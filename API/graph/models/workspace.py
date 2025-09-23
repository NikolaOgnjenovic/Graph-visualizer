from datetime import datetime
from .graph import Graph


class Workspace:
    def __init__(self, workspace_id: str, graph : Graph, name: str):
        self.workspace_id = workspace_id
        self.graph = graph
        self.name = name

    
    def add_operation(self, operation: str):
        """Record an operation performed on this workspace"""
        self.operations.append(f"{datetime.now()}: {operation}")
