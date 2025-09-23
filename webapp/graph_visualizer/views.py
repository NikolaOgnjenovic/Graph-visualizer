from django.shortcuts import render, redirect
from visualizer_platform.graph.use_cases.const import DATASOURCE_GROUP, VISUALIZER_GROUP
from visualizer_platform.graph.use_cases.plugin_recognition import PluginService
from visualizer_platform.graph.use_cases.views.graph_main_view import MainView
from visualizer_platform.graph.use_cases.views.graph_bird_view import BirdView
from visualizer_platform.graph.use_cases.views.graph_tree_view import TreeView
from visualizer_platform.graph.services.worspace_service import WorkspaceService
from django.apps import apps


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
    request.session['selected_visualizer_plugin'] = id
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

    simple_visualizer = next((p for p in visualizer_plugins if p.identifier() == 'simple_graph_visualizer'),
                                 visualizer_plugins[0])
    block_visualizer = next((p for p in visualizer_plugins if p.identifier() == 'block_graph_visualizer'),
                                 visualizer_plugins[0])

    if request.FILES.get('graph_file'):
        uploaded_file = request.FILES['graph_file']
        file_type = uploaded_file.name.split(".")[-1]
        file_contents = uploaded_file.read().decode('utf-8')
        ds_plugin = next((p for p in datasource_plugins if
                          p.identifier() == f'{file_type}_to_graph_loader' or file_type in p.identifier()),
                         datasource_plugins[0])
    
        workspace_id = workspace_service.create_workspace_from_file("Workspace",
            ds_plugin,
            file_contents
        )
        session['current_workspace_id'] = workspace_id

    elif session.get("current_workspace_id"):
        workspace_id = session.get("current_workspace_id")
    else:
        page_data = {
            'title': 'Graph visualizer',
            'datasource_plugins': datasource_plugins,
            'visualizer_plugins': visualizer_plugins,
            'main_graph_view': None,
            'bird_view': None,
            'tree_view': None,
        }
        return render(request, 'index.html', page_data)
    
    workspace_id = session['current_workspace_id']
    graph = workspace_service.get_workspace(workspace_id).graph

    # Wrap the simple visualizer output with the new main view (adds pan/zoom/drag, tooltips)
    main_graph_view = MainView.render(graph, block_visualizer)
    bird_view = BirdView.render(graph, block_visualizer)
    tree_view = TreeView.render(graph, block_visualizer)

    return render(request, 'index.html', {
        'title': 'Graph visualizer',
        'datasource_plugins': datasource_plugins,
        'visualizer_plugins': visualizer_plugins,
        'main_graph_view': main_graph_view,
        'bird_view': bird_view,
        'tree_view': tree_view
    })
