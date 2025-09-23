from django.shortcuts import render, redirect
from visualizer_platform.graph.use_cases.const import DATASOURCE_GROUP, VISUALIZER_GROUP
from visualizer_platform.graph.use_cases.plugin_recognition import PluginService
from visualizer_platform.graph.use_cases.views.graph_main_view import MainView
from visualizer_platform.graph.use_cases.views.graph_bird_view import BirdView
from visualizer_platform.graph.use_cases.views.graph_tree_view import TreeView
from visualizer_platform.graph.services.workspace_service import WorkspaceService
from django.apps import apps
from django.http import JsonResponse


def index(request):
    config = apps.get_app_config("graph_visualizer")
    plugin_service: PluginService = config.plugin_service
    workspace_service: WorkspaceService = config.workspace_service
    datasource_plugins = plugin_service.datasource_plugins.get(DATASOURCE_GROUP, [])
    visualizer_plugins = plugin_service.visualizer_plugins.get(VISUALIZER_GROUP, [])

    return render(request, 'index.html', {
        'title': 'Graph visualizer',
        'datasource_plugins': datasource_plugins,
        'visualizer_plugins': visualizer_plugins,
        "all_workspaces": workspace_service.get_all_workspaces(),
        "current_workspace_id": request.session.get("current_workspace_id")
    })


def visualizer_plugin(request, id):
    workspace_id = request.session.get("current_workspace_id")
    if workspace_id:
        config = apps.get_app_config("graph_visualizer")
        workspace_service = config.workspace_service
        plugin_service: PluginService = config.plugin_service
        
        visualizer_plugins = plugin_service.visualizer_plugins.get(VISUALIZER_GROUP, [])
        visualizer_plugin = next((p for p in visualizer_plugins if p.identifier() == id), None)
        
        if visualizer_plugin:
            workspace_service.update_workspace_visualizer(workspace_id, visualizer_plugin)
    
    return redirect('visualize')


def datasource_plugin(request, id):
    workspace_id = request.session.get("current_workspace_id")
    if workspace_id:
        config = apps.get_app_config("graph_visualizer")
        workspace_service = config.workspace_service
        plugin_service: PluginService = config.plugin_service
        
        datasource_plugins = plugin_service.datasource_plugins.get(DATASOURCE_GROUP, [])
        datasource_plugin = next((p for p in datasource_plugins if p.identifier() == id), None)
        
        if datasource_plugin:
            workspace_service.update_workspace_datasource(workspace_id, datasource_plugin)
    
    return redirect('visualize')


def close_workspace(request, workspace_id):
    """Close a workspace"""
    config = apps.get_app_config("graph_visualizer")
    workspace_service = config.workspace_service
    
    workspace_service.delete_workspace(workspace_id)
    
    # If we're closing the current workspace, switch to another or clear
    if request.session.get("current_workspace_id") == workspace_id:
        remaining_workspaces = list(workspace_service.get_all_workspaces())
        if remaining_workspaces:
            request.session['current_workspace_id'] = remaining_workspaces[0].workspace_id
        else:
            request.session['current_workspace_id'] = None
    
    return redirect('visualize')


def rename_workspace(request, workspace_id):
    """Rename a workspace via AJAX"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        new_name = request.POST.get('name', '').strip()
        if new_name:
            config = apps.get_app_config("graph_visualizer")
            workspace_service = config.workspace_service
            workspace_service.rename_workspace(workspace_id, new_name)
            return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


def switch_workspace(request, workspace_id):
    """Switch to a different workspace"""
    config = apps.get_app_config("graph_visualizer")
    workspace_service = config.workspace_service
    
    workspace = workspace_service.get_workspace(workspace_id)
    if workspace:
        request.session['current_workspace_id'] = workspace_id
    
    return redirect('visualize')


def visualize(request):
    """
    Load a graph from an uploaded file and render it with the simple visualizer.
    For now we ignore workspace/session handling and any advanced options.
    """
    config = apps.get_app_config("graph_visualizer")
    plugin_service: PluginService = config.plugin_service
    workspace_service: WorkspaceService = config.workspace_service
    session = request.session

    datasource_plugins = plugin_service.datasource_plugins.get(DATASOURCE_GROUP, [])
    visualizer_plugins = plugin_service.visualizer_plugins.get(VISUALIZER_GROUP, [])

    if not datasource_plugins or not visualizer_plugins:
        return render(request, 'index.html', {
            'title': 'Graph visualizer',
            'datasource_plugins': datasource_plugins,
            'visualizer_plugins': visualizer_plugins,
            'main_graph_view': None,
        })

    # Get current workspace to determine which visualizer to use
    current_workspace = None
    current_visualizer = None
    
    if session.get("current_workspace_id"):
        workspace_id = session.get("current_workspace_id")
        current_workspace = workspace_service.get_workspace(workspace_id)
        if current_workspace and current_workspace.visualizer_plugin:
            current_visualizer = current_workspace.visualizer_plugin

    # Default visualizers
    simple_visualizer = next((p for p in visualizer_plugins if p.identifier() == 'simple_graph_visualizer'),
                             visualizer_plugins[0])
    block_visualizer = next((p for p in visualizer_plugins if p.identifier() == 'block_graph_visualizer'),
                             visualizer_plugins[0])
    
    # Use workspace visualizer if available, otherwise default
    visualizer_to_use = current_visualizer or simple_visualizer

    if request.FILES.get('graph_file'):
        uploaded_file = request.FILES['graph_file']
        file_type = uploaded_file.name.split(".")[-1]
        file_contents = uploaded_file.read().decode('utf-8')
        ds_plugin = next((p for p in datasource_plugins if
                          p.identifier() == f'{file_type}_to_graph_loader' or file_type in p.identifier()),
                         datasource_plugins[0])
    
        workspace_id = workspace_service.create_workspace_from_file(
            uploaded_file.name,
            ds_plugin,
            file_contents,
            simple_visualizer
        )
        session['current_workspace_id'] = workspace_id
        current_workspace = workspace_service.get_workspace(workspace_id)

    elif session.get("current_workspace_id"):
        workspace_id = session.get("current_workspace_id")
        current_workspace = workspace_service.get_workspace(workspace_id)
    else:
        page_data = {
            'title': 'Graph visualizer',
            'datasource_plugins': datasource_plugins,
            'visualizer_plugins': visualizer_plugins,
            'main_graph_view': None,
            'bird_view': None,
            'tree_view': None,
            'all_workspaces': workspace_service.get_all_workspaces(),
            'current_workspace': None
        }
        return render(request, 'index.html', page_data)
    
    if not current_workspace:
        page_data = {
            'title': 'Graph visualizer',
            'datasource_plugins': datasource_plugins,
            'visualizer_plugins': visualizer_plugins,
            'main_graph_view': None,
            'bird_view': None,
            'tree_view': None,
            'all_workspaces': workspace_service.get_all_workspaces(),
            'current_workspace': None
        }
        return render(request, 'index.html', page_data)

    # Get graph from current workspace
    graph = current_workspace.graph

    # Render views with current visualizer
    main_graph_view = MainView.render(graph, visualizer_to_use)
    bird_view = BirdView.render(graph, visualizer_to_use)
    tree_view = TreeView.render(graph, visualizer_to_use)

    return render(request, 'index.html', {
        'title': 'Graph visualizer',
        'datasource_plugins': datasource_plugins,
        'visualizer_plugins': visualizer_plugins,
        'main_graph_view': main_graph_view,
        'bird_view': bird_view,
        'tree_view': tree_view,
        'all_workspaces': workspace_service.get_all_workspaces(),
        'current_workspace': current_workspace,
        'current_workspace_id': current_workspace.workspace_id if current_workspace else None
    })