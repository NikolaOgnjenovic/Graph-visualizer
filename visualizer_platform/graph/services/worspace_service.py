import uuid
from typing import Dict, List, Optional
from datetime import datetime
from API.graph.models.graph import Graph
from API.graph.models.workspace import Workspace


class WorkspaceService:
    def __init__(self):
        self._workspaces: Dict[str, Workspace] = {}
    
    def create_workspace_from_file(self, name: str, datasource_plugin, file_contents) -> str:
        workspace_id = str(uuid.uuid4())
        graph = datasource_plugin.load(file_contents)
        self._workspaces[workspace_id] = Workspace(
            workspace_id=workspace_id,
            graph=graph,
            name=name
        )
        return workspace_id
    
    def create_workspace_from_graph(self, name: str, graph) -> str:
        workspace_id = str(uuid.uuid4())
        self._workspaces[workspace_id] = Workspace(
            workspace_id=workspace_id,
            graph=graph,
            name=name
        )
        return workspace_id
    
    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        return self._workspaces.get(workspace_id)
    
    
    def delete_workspace(self, workspace_id: str):
        if workspace_id in self._workspaces:
            del self._workspaces[workspace_id]

    def get_all_workspaces(self) -> list[str]:
        return self._workspaces.keys


workspace_service = WorkspaceService()