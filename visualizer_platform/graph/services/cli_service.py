import shlex
from enum import Enum
from typing import Optional, Union
from API.graph.models.workspace import FilterCondition, SearchCondition
from API.graph.models.graph import Node, Edge, Graph, GraphDirection
import re


class CommandType(Enum):
    CREATE_NODE = "create_node"
    CREATE_EDGE = "create_edge"
    EDIT_NODE = "edit_node"
    EDIT_EDGE = "edit_edge"
    DELETE_NODE = "delete_node"
    DELETE_EDGE = "delete_edge"
    CLEAR_GRAPH = "clear_graph"
    FILTER = "filter"
    SEARCH = "search"


class CommandResult:
    def __init__(self, command_type: CommandType, data: Optional[Union[list, SearchCondition]] = None):
        self.command_type = command_type
        self.data = data


class CommandParser:
    
    def __init__(self, graph: Graph):
        self.graph = graph
        self._handlers = {
            'create': self._parse_create,
            'edit': self._parse_edit,
            'delete': self._parse_delete,
            'clear': self._parse_clear,
            'filter': self._parse_filter,
            'search': self._parse_search
        }

    def parse(self, command: str) -> CommandResult:
        if not command or command.isspace():
            raise ValueError("Empty command")
            
        tokens = shlex.split(command)
        primary_command = tokens[0].lower()
        
        if primary_command not in self._handlers:
            raise ValueError(f"Unknown command: {primary_command}")
            
        return self._handlers[primary_command](tokens)

    def _parse_create(self, tokens: list[str]) -> CommandResult:
        if len(tokens) < 2:
            raise ValueError("Create command requires target (node/edge)")
            
        target = tokens[1].lower()
        args = tokens[2:]
        
        if target == "node":
            node = self._create_node_from_args(args)
            self.graph.nodes.append(node)
            return CommandResult(CommandType.CREATE_NODE)
        elif target == "edge":
            edge = self._create_edge_from_args(args)
            self.graph.edges.append(edge)
            return CommandResult(CommandType.CREATE_EDGE)
        else:
            raise ValueError(f"Unknown create target: {target}")

    def _parse_edit(self, tokens: list[str]) -> CommandResult:
        if len(tokens) < 2:
            raise ValueError("Edit command requires target (node/edge)")
            
        target = tokens[1].lower()
        args = tokens[2:]
        
        if target == "node":
            self._edit_node_from_args(args)
            return CommandResult(CommandType.EDIT_NODE)
        elif target == "edge":
            self._edit_edge_from_args(args)
            return CommandResult(CommandType.EDIT_EDGE)
        else:
            raise ValueError(f"Unknown edit target: {target}")

    def _parse_delete(self, tokens: list[str]) -> CommandResult:
        if len(tokens) < 2:
            raise ValueError("Delete command requires target (node/edge)")
            
        target = tokens[1].lower()
        args = tokens[2:]
        
        if target == "node":
            self._delete_node_from_args(args)
            return CommandResult(CommandType.DELETE_NODE)
        elif target == "edge":
            self._delete_edge_from_args(args)
            return CommandResult(CommandType.DELETE_EDGE)
        else:
            raise ValueError(f"Unknown delete target: {target}")

    def _parse_clear(self, tokens: list[str]) -> CommandResult:
        if len(tokens) < 2 or tokens[1].lower() != "graph":
            raise ValueError("Clear command requires 'graph' target")
            
        self.graph.nodes.clear()
        self.graph.edges.clear()
        return CommandResult(CommandType.CLEAR_GRAPH)

    def _parse_filter(self, tokens: list[str]) -> CommandResult:
        if len(tokens) < 2:
            raise ValueError("Filter command requires conditions")
            
        filter_expr = " ".join(tokens[1:])
        filters = self._parse_filter_expression(filter_expr)
        return CommandResult(CommandType.FILTER, filters)

    def _parse_search(self, tokens: list[str]) -> CommandResult:
        if len(tokens) < 2:
            raise ValueError("Search command requires search term")
            
        search_term = " ".join(tokens[1:])
        search_filter = SearchCondition(search_term)
        return CommandResult(CommandType.SEARCH, search_filter)

    def _create_node_from_args(self, args: list[str]) -> Node:
        params = self._parse_arguments(args, required_fields=['id'])
        
        node_id = params['id']
        properties = params.get('properties', {})
        
        if any(node.node_id == node_id for node in self.graph.nodes):
            raise ValueError(f"Node with ID '{node_id}' already exists")
        
        name = properties.get('name') or properties.get('Name') or f"Node_{node_id}"
        node = Node(name, node_id)
        
        for key, value in properties.items():
            node.add_attribute(key, value)
                
        return node

    def _create_edge_from_args(self, args: list[str]) -> Edge:
        params = self._parse_arguments(args)
        node_ids = params.get('positional', [])
        
        if len(node_ids) != 2:
            raise ValueError("Edge must specify exactly 2 node IDs")
            
        src_id, dst_id = node_ids
        properties = params.get('properties', {})
        is_directed = not params.get('undirected', False)
        
        src_node = self._find_node(src_id)
        dst_node = self._find_node(dst_id)
        
        if self._edge_exists(src_id, dst_id):
            raise ValueError("Edge already exists between these nodes")
            
        direction = GraphDirection.DIRECTED if is_directed else GraphDirection.UNDIRECTED
        edge = Edge(source=src_node, dest=dst_node, direction=direction)
        
        for key, value in properties.items():
            edge.add_attribute(key, value)
            
        return edge

    def _edit_node_from_args(self, args: list[str]):
        params = self._parse_arguments(args, required_fields=['id'])
        
        node_id = params['id']
        properties = params.get('properties', {})
        removals = params.get('removals', [])
        
        node = self._find_node(node_id)
        
        for key, value in properties.items():
            node.add_attribute(key, value)
            
        for removal in removals:
            node.remove_attribute(removal)

    def _edit_edge_from_args(self, args: list[str]):
        params = self._parse_arguments(args)
        node_ids = params.get('positional', [])
        
        if len(node_ids) != 2:
            raise ValueError("Edge must specify exactly 2 node IDs")
            
        src_id, dst_id = node_ids
        properties = params.get('properties', {})
        removals = params.get('removals', [])
        direction = params.get('direction')
        
        edge = self._find_edge(src_id, dst_id)
        
        for key, value in properties.items():
            edge.attributes[key] = value
            
        for removal in removals:
            edge.remove_attribute(removal)
            
        if direction is not None:
            edge.direction = direction

    def _delete_node_from_args(self, args: list[str]):
        params = self._parse_arguments(args, required_fields=['id'])
        node_id = params['id']
        
        node = self._find_node(node_id)
        
        if any(edge.source == node or edge.destination == node for edge in self.graph.edges):
            raise ValueError("Cannot delete node with connected edges")
            
        self.graph.nodes.remove(node)

    def _delete_edge_from_args(self, args: list[str]):
        if len(args) != 2:
            raise ValueError("Edge delete requires exactly 2 node IDs")
            
        src_id, dst_id = args
        edge = self._find_edge(src_id, dst_id)
        self.graph.edges.remove(edge)

    def _parse_arguments(self, args: list[str], required_fields: list[str] = None) -> dict:
        if required_fields is None:
            required_fields = []
            
        result = {
            'properties': {},
            'removals': [],
            'positional': []
        }
        
        i = 0
        while i < len(args):
            arg = args[i]
            
            if arg.startswith('--id='):
                result['id'] = arg.split('=', 1)[1]
            elif arg == '--property':
                if i + 1 >= len(args):
                    raise ValueError("Expected property after --property")
                key, value = self._parse_key_value(args[i + 1])
                result['properties'][key] = value
                i += 1
            elif arg == '--unset-property':
                if i + 1 >= len(args):
                    raise ValueError("Expected property name after --unset-property")
                result['removals'].append(args[i + 1])
                i += 1
            elif arg == '--undirected':
                result['undirected'] = True
            elif arg == '--directed':
                result['direction'] = GraphDirection.DIRECTED
            elif arg == '--undirected':
                result['direction'] = GraphDirection.UNDIRECTED
            else:
                result['positional'].append(arg)
                
            i += 1
        
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Required field '{field}' is missing")
                
        return result

    def _parse_filter_expression(self, expr: str) -> list[FilterCondition]:
        
        # Poboljšani regex koji jasno razdvaja operatore i vrednosti
        pattern = r'(\w+)\s*(==|!=|<=|>=|<|>|=)\s*("[^"]+"|\'[^\']+\'|\S+)'
        matches = re.findall(pattern, expr)
        
        if not matches:
            raise ValueError(f"Invalid filter expression: {expr}")
        
        filters = []
        for match in matches:
            attr, op, value = match
            
            # Ukloni navodnike ako postoje
            if (value.startswith('"') and value.endswith('"')) or \
            (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            # Normalizacija operatora
            if op == '=':
                op = '=='
                
            filters.append(FilterCondition(attr, value, op))
        
        return filters

    def _find_node(self, node_id: str) -> Node:
        for node in self.graph.nodes:
            if node.node_id == node_id:
                return node
        raise ValueError(f"Node '{node_id}' not found")

    def _find_edge(self, src_id: str, dst_id: str) -> Edge:
        for edge in self.graph.edges:
            if (edge.source.node_id == src_id and 
                edge.destination.node_id == dst_id):
                return edge
        raise ValueError(f"Edge from '{src_id}' to '{dst_id}' not found")

    def _edge_exists(self, src_id: str, dst_id: str) -> bool:
        try:
            self._find_edge(src_id, dst_id)
            return True
        except ValueError:
            return False

    @staticmethod
    def _parse_key_value(kv_string: str) -> tuple[str, str]:
        if '=' not in kv_string:
            raise ValueError(f"Invalid key=value format: {kv_string}")
        key, value = kv_string.split('=', 1)
        return key.strip(), value.strip()


class CommandService:
    
    def __init__(self):
        self.parser = None
    
    def parse_command(self, command: str, graph: Graph) -> CommandResult:
        self.parser = CommandParser(graph)
        return self.parser.parse(command)