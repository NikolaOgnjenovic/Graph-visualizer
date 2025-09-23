from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('visualize', views.visualize, name="visualize"),
    path('visualizer-plugin/<str:id>/', views.visualizer_plugin, name='visualizer_plugin'),
    path('datasource-plugin/<str:id>/', views.datasource_plugin, name='datasource_plugin'),
    path('workspace/<str:workspace_id>/close/', views.close_workspace, name='close_workspace'),
    path('workspace/<str:workspace_id>/rename/', views.rename_workspace, name='rename_workspace'),
    path('workspace/<str:workspace_id>/switch/', views.switch_workspace, name='switch_workspace'),
]