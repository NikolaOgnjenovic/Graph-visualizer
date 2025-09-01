from django.shortcuts import render, redirect
from visualizer_platform.graph.use_cases.const import DATASOURCE_GROUP, VISUALIZER_GROUP
from visualizer_platform.graph.use_cases.plugin_recognition import PluginService
from django.apps import apps

def index(request):
    config = apps.get_app_config("graph_visualizer")
    plugin_service: PluginService = config.plugin_service
    datasource_plugins = plugin_service.datasource_plugins.get(DATASOURCE_GROUP, [])
    visualizer_plugins = plugin_service.visualizer_plugins.get(VISUALIZER_GROUP, [])

    return render(request, 'index.html', {
        'title': 'Graph visualizer',
        'datasource_plugins': datasource_plugins,
        'visualizer_plugins': visualizer_plugins,
        "current_workspace_id": request.session.get("current_workspace_id")
    })

def visualizer_plugin(request, id):
    request.session['selected_visualizer_plugin'] = id
    return redirect('visualize')

def visualize(request):
    """
    Load a graph from an uploaded JSON file and render it with the simple visualizer.
    For now we ignore workspace/session handling and any advanced options.
    """
    config = apps.get_app_config("graph_visualizer")
    plugin_service: PluginService = config.plugin_service

    datasource_plugins = plugin_service.datasource_plugins.get(DATASOURCE_GROUP, [])
    visualizer_plugins = plugin_service.visualizer_plugins.get(VISUALIZER_GROUP, [])

    if not datasource_plugins or not visualizer_plugins:
        return render(request, 'index.html', {
            'title': 'Graph visualizer',
            'datasource_plugins': datasource_plugins,
            'visualizer_plugins': visualizer_plugins,
            'graph_html': None,
        })

    ds_plugin = next((p for p in datasource_plugins if p.identifier() == 'json_to_graph_loader' or 'json' in p.identifier()), datasource_plugins[0])
    simple_visualizer = next((p for p in visualizer_plugins if p.identifier() == 'simple_graph_visualizer'), visualizer_plugins[0])

    if request.FILES.get('graph_file'):
        uploaded_file = request.FILES['graph_file']
        file_contents = uploaded_file.read().decode('utf-8')
        graph = ds_plugin.load(file_contents)
        graph_html = simple_visualizer.visualize(graph)
    else:
        graph_html = None

    page_data = {
        'title': 'Graph visualizer',
        'datasource_plugins': datasource_plugins,
        'visualizer_plugins': visualizer_plugins,
        'graph_html': graph_html,
    }

    return render(request, 'index.html', page_data)