from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('plugin/visualizer/<str:id>/', views.visualizer_plugin, name="visualizer_plugin"),
    path('visualize', views.visualize, name="visualize"),
]