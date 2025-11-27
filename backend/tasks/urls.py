"""
URL Configuration for Tasks API

Routes for task analysis and suggestion endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.api_info, name='api-info'),
    path('tasks/analyze/', views.analyze_tasks, name='analyze-tasks'),
    path('tasks/suggest/', views.suggest_tasks, name='suggest-tasks'),
    path('tasks/validate/', views.validate_tasks, name='validate-tasks'),
]
