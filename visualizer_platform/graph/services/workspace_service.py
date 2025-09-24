import uuid
from typing import Dict, List, Optional
from datetime import datetime
from API.graph.models.graph import Graph
from API.graph.models.workspace import Workspace
from visualizer_platform.graph.services.cli_service import CommandService, CommandResult, CommandType


class WorkspaceService:
    def __init__(self):
        self._workspaces: Dict[str, Workspace] = {}
        self.command_service = CommandService()
        self.command_error = None
    
    def create_workspace(self, graph, name: str, 
                        datasource_plugin=None, visualizer_plugin=None) -> str:
        """Create a new workspace with a graph"""
        workspace_id = str(uuid.uuid4())
        self._workspaces[workspace_id] = Workspace(
            workspace_id=workspace_id,
            graph=graph,
            name=name,
            datasource_plugin=datasource_plugin,
            visualizer_plugin=visualizer_plugin
        )
        return workspace_id
    
    def create_workspace_from_file(self, name: str, datasource_plugin, file_contents: str, visualizer_plugin=None) -> str:
        """Create workspace by loading graph from file using datasource plugin"""
        graph = datasource_plugin.load(file_contents)
        return self.create_workspace(
            graph=graph,
            name=name,
            datasource_plugin=datasource_plugin,
            visualizer_plugin=visualizer_plugin
        )
    
    def update_workspace_visualizer(self, workspace_id: str, visualizer_plugin):
        """Update the visualizer plugin for a workspace"""
        if workspace_id in self._workspaces:
            self._workspaces[workspace_id].visualizer_plugin = visualizer_plugin
    
    def update_workspace_datasource(self, workspace_id: str, datasource_plugin):
        """Update the datasource plugin for a workspace"""
        if workspace_id in self._workspaces:
            self._workspaces[workspace_id].datasource_plugin = datasource_plugin

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        return self._workspaces.get(workspace_id)
    
    def delete_workspace(self, workspace_id: str):
        if workspace_id in self._workspaces:
            del self._workspaces[workspace_id]

    def get_all_workspaces(self) -> list[Workspace]:
        return self._workspaces.values()
    
    def rename_workspace(self, workspace_id: str, new_name: str):
        """Rename a workspace"""
        if workspace_id in self._workspaces and new_name.strip():
            self._workspaces[workspace_id].name = new_name.strip()

    def add_search_to_workspace(self, workspace_id: str, query: str):
        if workspace_id in self._workspaces:
            self._workspaces[workspace_id].add_search(query)
    
    def add_filter_to_workspace(self, workspace_id: str, attribute: str, operator: str, value: str):
        if workspace_id in self._workspaces:
            self._workspaces[workspace_id].add_filter(attribute, operator, value)
    
    def remove_search_from_workspace(self, workspace_id: str, index: int):
        if workspace_id in self._workspaces:
            self._workspaces[workspace_id].remove_search(index)
    
    def remove_filter_from_workspace(self, workspace_id: str, index: int):
        if workspace_id in self._workspaces:
            self._workspaces[workspace_id].remove_filter(index)
    
    def apply_filters_to_workspace(self, workspace_id: str) -> Optional[tuple[Graph, list[str]]]:
        if workspace_id in self._workspaces:
            return self._workspaces[workspace_id].apply_filters()
        return None
    
    def execute_command(self, command: str, workspace_id: str) -> bool:
        """CLI command processor"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            self.command_error = f"Workspace {workspace_id} not found"
            return False
        
        try:
            # This modifies the graph in-place through references
            result = self.command_service.parse_command(command, workspace.graph)
            
            # Handle filters and searches
            if result.command_type == CommandType.FILTER and result.data:
                for filter_cond in result.data:
                    self.add_filter_to_workspace(workspace_id, filter_cond.attribute, 
                                            filter_cond.operator, filter_cond.value)
            elif result.command_type == CommandType.SEARCH and result.data:
                self.add_search_to_workspace(workspace_id, result.data.query)
            
            self.command_error = None
            return True
            
        except Exception as e:
            self.command_error = str(e)
            return False

    def get_command_error(self) -> Optional[str]:
        """Get the last command error"""
        return self.command_error

    def clear_command_error(self):
        """Clear the command error"""
        self.command_error = None

workspace_service = WorkspaceService()