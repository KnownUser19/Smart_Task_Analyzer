"""
API Views for Smart Task Analyzer

This module provides REST API endpoints for task analysis and suggestions.
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import (
    TaskListInputSerializer,
    AnalysisResultSerializer,
    SuggestionsResultSerializer
)
from .scoring import analyze_tasks_with_strategy, get_task_suggestions


@api_view(['POST'])
def analyze_tasks(request):
    """
    Analyze and prioritize a list of tasks.
    
    POST /api/tasks/analyze/
    
    Request Body:
    {
        "tasks": [
            {
                "title": "Task name",
                "due_date": "2025-01-15",
                "estimated_hours": 3,
                "importance": 8,
                "dependencies": []
            }
        ],
        "strategy": "smart_balance",  // optional
        "custom_weights": {            // optional
            "urgency": 0.3,
            "importance": 0.35,
            "effort": 0.15,
            "dependency": 0.2
        }
    }
    
    Response:
    {
        "tasks": [...sorted tasks with scores...],
        "total_count": 5,
        "strategy": "smart_balance",
        "weights": {...},
        "circular_dependencies": [],
        "analysis_date": "2025-01-10",
        "priority_distribution": {"high": 2, "medium": 2, "low": 1}
    }
    """
    # Handle both direct task array and wrapped format
    data = request.data
    if isinstance(data, list):
        data = {'tasks': data, 'strategy': 'smart_balance'}
    
    serializer = TaskListInputSerializer(data=data)
    
    if not serializer.is_valid():
        return Response(
            {
                'error': 'Invalid input data',
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    tasks = validated_data['tasks']
    strategy = validated_data.get('strategy', 'smart_balance')
    custom_weights = validated_data.get('custom_weights')
    
    try:
        result = analyze_tasks_with_strategy(
            tasks=tasks,
            strategy=strategy,
            custom_weights=custom_weights
        )
        
        return Response(result, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {
                'error': 'Analysis failed',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST', 'GET'])
def suggest_tasks(request):
    """
    Get top task suggestions with explanations.
    
    POST /api/tasks/suggest/
    
    Request Body (for POST):
    {
        "tasks": [...],
        "strategy": "smart_balance",  // optional
        "count": 3                     // optional, default 3
    }
    
    GET /api/tasks/suggest/?strategy=smart_balance&count=3
    (Uses tasks stored in session/database - for demo purposes)
    
    Response:
    {
        "suggestions": [
            {
                "rank": 1,
                "task": {...task with scores...},
                "recommendation_reason": "...",
                "actionable_insight": "..."
            }
        ],
        "strategy": "smart_balance",
        "analysis_date": "2025-01-10",
        "total_tasks_analyzed": 5
    }
    """
    if request.method == 'GET':
        # For GET requests, return sample suggestions or empty
        return Response(
            {
                'message': 'POST task data to get suggestions',
                'example_request': {
                    'tasks': [
                        {
                            'title': 'Example task',
                            'due_date': '2025-01-15',
                            'estimated_hours': 2,
                            'importance': 7,
                            'dependencies': []
                        }
                    ],
                    'strategy': 'smart_balance',
                    'count': 3
                }
            },
            status=status.HTTP_200_OK
        )
    
    # Handle POST request
    data = request.data
    if isinstance(data, list):
        data = {'tasks': data}
    
    tasks = data.get('tasks', [])
    strategy = data.get('strategy', 'smart_balance')
    count = data.get('count', 3)
    
    if not tasks:
        return Response(
            {
                'error': 'No tasks provided',
                'details': 'Please provide a list of tasks to analyze'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Validate count
        count = max(1, min(10, int(count)))
        
        result = get_task_suggestions(
            tasks=tasks,
            strategy=strategy,
            count=count
        )
        
        return Response(result, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {
                'error': 'Suggestion generation failed',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def api_info(request):
    """
    Get API information and available endpoints.
    
    GET /api/
    """
    return Response({
        'name': 'Smart Task Analyzer API',
        'version': '1.0.0',
        'description': 'Intelligent task prioritization and analysis',
        'endpoints': {
            'POST /api/tasks/analyze/': 'Analyze and sort tasks by priority',
            'POST /api/tasks/suggest/': 'Get top task suggestions with explanations',
            'GET /api/': 'This info endpoint'
        },
        'available_strategies': [
            {
                'name': 'smart_balance',
                'description': 'Balanced algorithm considering all factors'
            },
            {
                'name': 'fastest_wins',
                'description': 'Prioritize low-effort quick wins'
            },
            {
                'name': 'high_impact',
                'description': 'Prioritize importance over everything'
            },
            {
                'name': 'deadline_driven',
                'description': 'Prioritize based on due date urgency'
            }
        ],
        'scoring_factors': [
            'urgency (based on due date)',
            'importance (user rating 1-10)',
            'effort (estimated hours - favors quick wins)',
            'dependencies (tasks blocking others rank higher)'
        ]
    })


@api_view(['POST'])
def validate_tasks(request):
    """
    Validate task data without scoring.
    
    POST /api/tasks/validate/
    
    Useful for checking task data format before analysis.
    """
    from .scoring import TaskValidator
    
    tasks = request.data.get('tasks', [])
    if isinstance(request.data, list):
        tasks = request.data
    
    if not tasks:
        return Response(
            {'error': 'No tasks provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validation_results = []
    for i, task in enumerate(tasks):
        validated, warnings = TaskValidator.validate_task(task)
        validation_results.append({
            'index': i,
            'original': task,
            'validated': {
                **validated,
                'due_date': validated['due_date'].isoformat() if validated['due_date'] else None
            },
            'warnings': warnings,
            'is_valid': len(warnings) == 0
        })
    
    all_valid = all(r['is_valid'] for r in validation_results)
    
    return Response({
        'all_valid': all_valid,
        'total_tasks': len(tasks),
        'tasks_with_warnings': sum(1 for r in validation_results if r['warnings']),
        'results': validation_results
    })
