from datetime import datetime
from .graph import Graph

from datetime import datetime
from typing import List, Dict, Any
from .graph import Graph

class SearchCondition:
    def __init__(self, query: str):
        self.query = query.lower()
        self.type = "search"

class FilterCondition:
    def __init__(self, attribute: str, operator: str, value: str):
        self.attribute = attribute
        self.operator = operator
        self.value = value
        self.type = "filter"

class Workspace:
    def __init__(self, workspace_id: str, graph: Graph, name: str, 
                 datasource_plugin=None, visualizer_plugin=None):
        self.workspace_id = workspace_id
        self.graph = graph
        self.name = name
        self.datasource_plugin = datasource_plugin
        self.visualizer_plugin = visualizer_plugin
        self.searches: List[SearchCondition] = []
        self.filters: List[FilterCondition] = []
        self.filtered_graph: Graph = graph 
        self.created_at = datetime.now()
    
    def add_search(self, query: str):
        self.searches.append(SearchCondition(query))
    
    def add_filter(self, attribute: str, operator: str, value: str):
        self.filters.append(FilterCondition(attribute, operator, value))
    
    def remove_search(self, index: int):
        if 0 <= index < len(self.searches):
            self.searches.pop(index)
    
    def remove_filter(self, index: int):
        if 0 <= index < len(self.filters):
            self.filters.pop(index)
    
    def apply_filters(self) -> tuple[Graph, list[str]]:
        """Apply all searches and filters to create a filtered graph.
        Returns (filtered_graph, error_messages)."""
        errors: list[str] = []

        if not self.searches and not self.filters:
            self.filtered_graph = self.graph
            return self.filtered_graph, errors

        filtered_nodes = list(self.graph.nodes)

        for search in self.searches:
            filtered_nodes = [
                node for node in filtered_nodes
                if self._node_matches_search(node, search.query)
            ]

        for filter_cond in self.filters:
            new_nodes = []
            for node in filtered_nodes:
                match, error = self._node_matches_filter(node, filter_cond)
                if error:
                    errors.append(error)
                if match:
                    new_nodes.append(node)
            filtered_nodes = new_nodes

        filtered_node_ids = {node.node_id for node in filtered_nodes}
        filtered_edges = [
            edge for edge in self.graph.edges
            if edge.source.node_id in filtered_node_ids and edge.destination.node_id in filtered_node_ids
        ]

        self.filtered_graph = Graph(nodes=filtered_nodes, edges=filtered_edges)
        return self.filtered_graph, errors

    
    def _node_matches_search(self, node, query: str) -> bool:
        """Check if node matches search query in name or attributes"""
        if query in node.name.lower():
            return True
        
        if query in node.node_id.lower():
            return True
        
        for attr_name, attr_value in node.attributes.items():
            if query in str(attr_name).lower() or query in str(attr_value).lower():
                return True
        
        return False
    
    def _node_matches_filter(self, node, filter_cond: FilterCondition) -> tuple[bool, str | None]:
        """Check if node matches filter condition by casting filter value to attribute type.
        Returns (match, error_message)."""
        attribute_value = node.attributes.get(filter_cond.attribute)

        if attribute_value is None:
            return False, None  # attribute not found just means no match

        attr_type = type(attribute_value)

        try:
            # Try to cast the filter value to the attribute type
            if attr_type is bool:
                if isinstance(filter_cond.value, str):
                    cast_value = filter_cond.value.lower() in ["true", "1", "yes"]
                else:
                    cast_value = bool(filter_cond.value)
            else:
                cast_value = attr_type(filter_cond.value)
        except (ValueError, TypeError):
            return False, (
                f"Invalid filter value '{filter_cond.value}' for attribute "
                f"'{filter_cond.attribute}' (expected {attr_type.__name__})."
            )

        # Check operator compatibility
        try:
            if filter_cond.operator == "==":
                return attribute_value == cast_value, None
            elif filter_cond.operator == "!=":
                return attribute_value != cast_value, None
            elif filter_cond.operator == ">" and isinstance(attribute_value, (int, float, datetime)):
                return attribute_value > cast_value, None
            elif filter_cond.operator == "<" and isinstance(attribute_value, (int, float, datetime)):
                return attribute_value < cast_value, None
            elif filter_cond.operator == ">=" and isinstance(attribute_value, (int, float, datetime)):
                return attribute_value >= cast_value, None
            elif filter_cond.operator == "<=" and isinstance(attribute_value, (int, float, datetime)):
                return attribute_value <= cast_value, None
            else:
                return False, (
                    f"Operator '{filter_cond.operator}' not supported for type {attr_type.__name__}."
                )
        except Exception as e:
            return False, f"Error applying filter {filter_cond.attribute} {filter_cond.operator} {filter_cond.value}: {e}"
