"""
Task Model for Smart Task Analyzer

This module defines the Task model which stores task information
including title, due date, estimated hours, importance, and dependencies.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Task(models.Model):
    """
    Task model representing a unit of work to be prioritized.
    
    Attributes:
        title: Brief description of the task
        due_date: When the task needs to be completed
        estimated_hours: Expected time to complete the task
        importance: User-provided priority rating (1-10)
        dependencies: List of task IDs that must be completed first
        created_at: Timestamp when the task was created
    """
    title = models.CharField(max_length=255)
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.FloatField(
        validators=[MinValueValidator(0.1)],
        default=1.0
    )
    importance = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=5
    )
    dependencies = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} (Importance: {self.importance})"
