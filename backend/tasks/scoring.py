"""
Smart Task Priority Scoring Algorithm

This module implements an intelligent multi-factor scoring system that analyzes
tasks based on urgency, importance, effort, and dependencies to produce
actionable priority rankings.

Algorithm Overview:
==================
The scoring system uses a weighted multi-factor approach where each component
contributes to a final normalized score (0-100). The algorithm is designed to
handle edge cases gracefully and provide meaningful explanations for its decisions.

Scoring Components:
- Urgency Score (0-100): Based on days until due date
- Importance Score (0-100): Normalized from user's 1-10 rating
- Effort Score (0-100): Quick wins get higher scores
- Dependency Score (0-100): Tasks blocking others are prioritized

Author: Candidate for Software Development Intern Position
"""

from datetime import date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class SortingStrategy(Enum):
    """Available sorting strategies for task prioritization."""
    SMART_BALANCE = "smart_balance"
    FASTEST_WINS = "fastest_wins"
    HIGH_IMPACT = "high_impact"
    DEADLINE_DRIVEN = "deadline_driven"


@dataclass
class ScoringWeights:
    """
    Configurable weights for the scoring algorithm.
    All weights should sum to 1.0 for normalized scoring.
    """
    urgency: float = 0.30
    importance: float = 0.35
    effort: float = 0.15
    dependency: float = 0.20
    
    def __post_init__(self):
        """Validate that weights sum to 1.0"""
        total = self.urgency + self.importance + self.effort + self.dependency
        if not (0.99 <= total <= 1.01):  # Allow small floating point tolerance
            # Normalize weights if they don't sum to 1
            self.urgency /= total
            self.importance /= total
            self.effort /= total
            self.dependency /= total


# Predefined weight configurations for different strategies
STRATEGY_WEIGHTS = {
    SortingStrategy.SMART_BALANCE: ScoringWeights(
        urgency=0.30, importance=0.35, effort=0.15, dependency=0.20
    ),
    SortingStrategy.FASTEST_WINS: ScoringWeights(
        urgency=0.15, importance=0.15, effort=0.60, dependency=0.10
    ),
    SortingStrategy.HIGH_IMPACT: ScoringWeights(
        urgency=0.10, importance=0.70, effort=0.05, dependency=0.15
    ),
    SortingStrategy.DEADLINE_DRIVEN: ScoringWeights(
        urgency=0.65, importance=0.15, effort=0.05, dependency=0.15
    ),
}


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected in the task graph."""
    pass


class TaskValidator:
    """Validates and sanitizes task data before scoring."""
    
    @staticmethod
    def validate_task(task: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Validate and sanitize a task dictionary.
        
        Returns:
            Tuple of (sanitized_task, list_of_warnings)
        """
        warnings = []
        sanitized = {}
        
        # Title validation
        title = task.get('title', '').strip()
        if not title:
            title = "Untitled Task"
            warnings.append("Missing title - defaulted to 'Untitled Task'")
        sanitized['title'] = title
        
        # Due date validation
        due_date = task.get('due_date')
        if due_date:
            if isinstance(due_date, str):
                try:
                    sanitized['due_date'] = date.fromisoformat(due_date)
                except ValueError:
                    sanitized['due_date'] = None
                    warnings.append(f"Invalid date format '{due_date}' - treating as no due date")
            elif isinstance(due_date, date):
                sanitized['due_date'] = due_date
            else:
                sanitized['due_date'] = None
                warnings.append("Invalid due_date type - treating as no due date")
        else:
            sanitized['due_date'] = None
        
        # Estimated hours validation
        estimated_hours = task.get('estimated_hours', 1.0)
        try:
            estimated_hours = float(estimated_hours)
            if estimated_hours <= 0:
                estimated_hours = 1.0
                warnings.append("Invalid estimated_hours (<=0) - defaulted to 1.0")
            elif estimated_hours > 100:
                warnings.append(f"Very high estimated_hours ({estimated_hours}) - consider breaking down the task")
        except (TypeError, ValueError):
            estimated_hours = 1.0
            warnings.append("Invalid estimated_hours format - defaulted to 1.0")
        sanitized['estimated_hours'] = estimated_hours
        
        # Importance validation
        importance = task.get('importance', 5)
        try:
            importance = int(importance)
            importance = max(1, min(10, importance))  # Clamp to 1-10
        except (TypeError, ValueError):
            importance = 5
            warnings.append("Invalid importance format - defaulted to 5")
        sanitized['importance'] = importance
        
        # Dependencies validation
        dependencies = task.get('dependencies', [])
        if not isinstance(dependencies, list):
            dependencies = []
            warnings.append("Invalid dependencies format - defaulted to empty list")
        sanitized['dependencies'] = dependencies
        
        # Preserve ID if present
        if 'id' in task:
            sanitized['id'] = task['id']
        
        return sanitized, warnings


class DependencyAnalyzer:
    """Analyzes task dependencies and detects circular references."""
    
    def __init__(self, tasks: List[Dict[str, Any]]):
        self.tasks = tasks
        self.task_ids = {t.get('id') for t in tasks if 'id' in t}
        self._build_dependency_graph()
    
    def _build_dependency_graph(self):
        """Build adjacency list representation of dependency graph."""
        self.graph = {}
        self.reverse_graph = {}  # Tasks blocked BY this task
        
        for task in self.tasks:
            task_id = task.get('id')
            if task_id is not None:
                deps = task.get('dependencies', [])
                # Filter to only valid dependencies
                valid_deps = [d for d in deps if d in self.task_ids]
                self.graph[task_id] = valid_deps
                
                # Build reverse graph (who depends on this task)
                for dep_id in valid_deps:
                    if dep_id not in self.reverse_graph:
                        self.reverse_graph[dep_id] = []
                    self.reverse_graph[dep_id].append(task_id)
    
    def detect_circular_dependencies(self) -> List[List[Any]]:
        """
        Detect all circular dependencies in the task graph.
        
        Uses Tarjan's algorithm to find strongly connected components.
        
        Returns:
            List of cycles found (each cycle is a list of task IDs)
        """
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    cycle = dfs(neighbor, path)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:]
            
            path.pop()
            rec_stack.remove(node)
            return None
        
        for task_id in self.graph:
            if task_id not in visited:
                cycle = dfs(task_id, [])
                if cycle:
                    cycles.append(cycle)
        
        return cycles
    
    def get_blocking_count(self, task_id: Any) -> int:
        """
        Get the number of tasks blocked by this task.
        
        Uses BFS to count all transitively dependent tasks.
        """
        if task_id not in self.reverse_graph:
            return 0
        
        blocked = set()
        queue = list(self.reverse_graph.get(task_id, []))
        
        while queue:
            current = queue.pop(0)
            if current not in blocked:
                blocked.add(current)
                queue.extend(self.reverse_graph.get(current, []))
        
        return len(blocked)
    
    def has_unmet_dependencies(self, task_id: Any, completed_ids: set = None) -> bool:
        """Check if a task has dependencies that aren't completed."""
        completed_ids = completed_ids or set()
        deps = self.graph.get(task_id, [])
        return any(d not in completed_ids for d in deps)


class TaskScorer:
    """
    Core scoring engine for task prioritization.
    
    This class implements the multi-factor scoring algorithm that evaluates
    tasks based on urgency, importance, effort, and dependency relationships.
    """
    
    def __init__(
        self,
        strategy: SortingStrategy = SortingStrategy.SMART_BALANCE,
        custom_weights: Optional[ScoringWeights] = None,
        reference_date: Optional[date] = None
    ):
        """
        Initialize the scorer with a strategy and optional custom weights.
        
        Args:
            strategy: The sorting strategy to use
            custom_weights: Optional custom weight configuration
            reference_date: Date to use for urgency calculations (defaults to today)
        """
        self.strategy = strategy
        self.weights = custom_weights or STRATEGY_WEIGHTS[strategy]
        self.reference_date = reference_date or date.today()
    
    def calculate_urgency_score(self, due_date: Optional[date]) -> Tuple[float, str]:
        """
        Calculate urgency score based on days until due date.
        
        Scoring Logic:
        - Overdue tasks: 100 + penalty (capped at 150 for extreme cases)
        - Due today: 100
        - Due tomorrow: 90
        - Due within a week: 70-90
        - Due within a month: 30-70
        - Due later: 10-30
        - No due date: 20 (neutral-low urgency)
        
        Returns:
            Tuple of (score, explanation)
        """
        if due_date is None:
            return 20.0, "No due date set - assigned baseline urgency"
        
        days_until_due = (due_date - self.reference_date).days
        
        if days_until_due < 0:
            # Overdue - high urgency with increasing penalty
            overdue_days = abs(days_until_due)
            score = min(150, 100 + (overdue_days * 5))
            return score, f"OVERDUE by {overdue_days} day(s) - critical priority"
        elif days_until_due == 0:
            return 100.0, "Due TODAY - maximum urgency"
        elif days_until_due == 1:
            return 90.0, "Due tomorrow - very high urgency"
        elif days_until_due <= 3:
            score = 90 - (days_until_due - 1) * 5
            return score, f"Due in {days_until_due} days - high urgency"
        elif days_until_due <= 7:
            score = 80 - (days_until_due - 3) * 2.5
            return score, f"Due this week ({days_until_due} days) - moderate-high urgency"
        elif days_until_due <= 14:
            score = 70 - (days_until_due - 7) * 2
            return score, f"Due in {days_until_due} days - moderate urgency"
        elif days_until_due <= 30:
            score = 56 - (days_until_due - 14) * 1
            return score, f"Due in {days_until_due} days - lower urgency"
        else:
            # Far future - minimal urgency but not zero
            score = max(10, 40 - (days_until_due - 30) * 0.5)
            return score, f"Due in {days_until_due} days - low urgency"
    
    def calculate_importance_score(self, importance: int) -> Tuple[float, str]:
        """
        Convert 1-10 importance rating to 0-100 score.
        
        Uses a slightly non-linear scale to emphasize high-importance tasks.
        """
        # Non-linear scaling: importance^1.2 to make high values more impactful
        normalized = ((importance - 1) / 9) ** 1.1 * 100
        
        if importance >= 9:
            explanation = f"Critical importance ({importance}/10)"
        elif importance >= 7:
            explanation = f"High importance ({importance}/10)"
        elif importance >= 5:
            explanation = f"Medium importance ({importance}/10)"
        elif importance >= 3:
            explanation = f"Lower importance ({importance}/10)"
        else:
            explanation = f"Low importance ({importance}/10)"
        
        return normalized, explanation
    
    def calculate_effort_score(self, estimated_hours: float) -> Tuple[float, str]:
        """
        Calculate effort score favoring quick wins.
        
        Scoring Logic (inverse relationship - lower effort = higher score):
        - < 1 hour: 90-100 (quick wins)
        - 1-2 hours: 70-90
        - 2-4 hours: 50-70
        - 4-8 hours: 30-50
        - > 8 hours: 10-30
        
        Uses logarithmic scaling for smooth transitions.
        """
        if estimated_hours < 0.5:
            score = 100
            explanation = f"Quick win ({estimated_hours}h) - very low effort"
        elif estimated_hours < 1:
            score = 95
            explanation = f"Quick task ({estimated_hours}h) - low effort"
        elif estimated_hours <= 2:
            score = 90 - (estimated_hours - 1) * 20
            explanation = f"Short task ({estimated_hours}h) - manageable effort"
        elif estimated_hours <= 4:
            score = 70 - (estimated_hours - 2) * 10
            explanation = f"Medium task ({estimated_hours}h) - moderate effort"
        elif estimated_hours <= 8:
            score = 50 - (estimated_hours - 4) * 5
            explanation = f"Long task ({estimated_hours}h) - significant effort"
        else:
            # Large tasks - use log scale to avoid negative scores
            score = max(10, 30 - math.log2(estimated_hours / 8) * 10)
            explanation = f"Major task ({estimated_hours}h) - consider breaking down"
        
        return score, explanation
    
    def calculate_dependency_score(
        self,
        task_id: Any,
        dependency_analyzer: Optional[DependencyAnalyzer]
    ) -> Tuple[float, str]:
        """
        Calculate dependency score based on how many tasks this one blocks.
        
        Tasks that block many other tasks get higher priority.
        """
        if dependency_analyzer is None or task_id is None:
            return 50.0, "No dependency analysis available"
        
        blocking_count = dependency_analyzer.get_blocking_count(task_id)
        has_unmet = dependency_analyzer.has_unmet_dependencies(task_id)
        
        if blocking_count == 0:
            base_score = 40
            explanation = "Doesn't block other tasks"
        elif blocking_count == 1:
            base_score = 70
            explanation = "Blocks 1 other task"
        elif blocking_count <= 3:
            base_score = 85
            explanation = f"Blocks {blocking_count} tasks - important dependency"
        else:
            base_score = 100
            explanation = f"Blocks {blocking_count} tasks - critical path"
        
        # Reduce score if this task has unmet dependencies
        if has_unmet:
            base_score *= 0.7
            explanation += " (has unmet dependencies)"
        
        return base_score, explanation
    
    def score_task(
        self,
        task: Dict[str, Any],
        dependency_analyzer: Optional[DependencyAnalyzer] = None
    ) -> Dict[str, Any]:
        """
        Calculate the complete priority score for a single task.
        
        Returns:
            Dictionary containing the task data plus scoring details
        """
        # Validate and sanitize task
        validated_task, warnings = TaskValidator.validate_task(task)
        
        # Calculate component scores
        urgency_score, urgency_explanation = self.calculate_urgency_score(
            validated_task['due_date']
        )
        importance_score, importance_explanation = self.calculate_importance_score(
            validated_task['importance']
        )
        effort_score, effort_explanation = self.calculate_effort_score(
            validated_task['estimated_hours']
        )
        dependency_score, dependency_explanation = self.calculate_dependency_score(
            validated_task.get('id'),
            dependency_analyzer
        )
        
        # Calculate weighted final score
        final_score = (
            urgency_score * self.weights.urgency +
            importance_score * self.weights.importance +
            effort_score * self.weights.effort +
            dependency_score * self.weights.dependency
        )
        
        # Normalize to 0-100 range (accounting for overdue bonus)
        final_score = min(100, final_score)
        
        # Determine priority level
        if final_score >= 80:
            priority_level = "HIGH"
        elif final_score >= 50:
            priority_level = "MEDIUM"
        else:
            priority_level = "LOW"
        
        # Build comprehensive result
        result = {
            **validated_task,
            'priority_score': round(final_score, 2),
            'priority_level': priority_level,
            'scoring_breakdown': {
                'urgency': {
                    'score': round(urgency_score, 2),
                    'weight': self.weights.urgency,
                    'weighted_score': round(urgency_score * self.weights.urgency, 2),
                    'explanation': urgency_explanation
                },
                'importance': {
                    'score': round(importance_score, 2),
                    'weight': self.weights.importance,
                    'weighted_score': round(importance_score * self.weights.importance, 2),
                    'explanation': importance_explanation
                },
                'effort': {
                    'score': round(effort_score, 2),
                    'weight': self.weights.effort,
                    'weighted_score': round(effort_score * self.weights.effort, 2),
                    'explanation': effort_explanation
                },
                'dependency': {
                    'score': round(dependency_score, 2),
                    'weight': self.weights.dependency,
                    'weighted_score': round(dependency_score * self.weights.dependency, 2),
                    'explanation': dependency_explanation
                }
            },
            'strategy_used': self.strategy.value,
            'warnings': warnings
        }
        
        # Convert date back to string for JSON serialization
        if result['due_date']:
            result['due_date'] = result['due_date'].isoformat()
        
        return result
    
    def analyze_tasks(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze and score a list of tasks.
        
        Returns:
            Dictionary containing sorted tasks and metadata
        """
        if not tasks:
            return {
                'tasks': [],
                'total_count': 0,
                'strategy': self.strategy.value,
                'circular_dependencies': [],
                'analysis_date': self.reference_date.isoformat()
            }
        
        # Assign IDs to tasks that don't have them
        for i, task in enumerate(tasks):
            if 'id' not in task:
                task['id'] = f"task_{i}"
        
        # Build dependency analyzer
        dep_analyzer = DependencyAnalyzer(tasks)
        
        # Check for circular dependencies
        circular_deps = dep_analyzer.detect_circular_dependencies()
        
        # Score all tasks
        scored_tasks = [
            self.score_task(task, dep_analyzer)
            for task in tasks
        ]
        
        # Sort by priority score (descending)
        scored_tasks.sort(key=lambda t: t['priority_score'], reverse=True)
        
        return {
            'tasks': scored_tasks,
            'total_count': len(scored_tasks),
            'strategy': self.strategy.value,
            'weights': {
                'urgency': self.weights.urgency,
                'importance': self.weights.importance,
                'effort': self.weights.effort,
                'dependency': self.weights.dependency
            },
            'circular_dependencies': circular_deps,
            'analysis_date': self.reference_date.isoformat(),
            'priority_distribution': {
                'high': sum(1 for t in scored_tasks if t['priority_level'] == 'HIGH'),
                'medium': sum(1 for t in scored_tasks if t['priority_level'] == 'MEDIUM'),
                'low': sum(1 for t in scored_tasks if t['priority_level'] == 'LOW')
            }
        }
    
    def get_suggestions(
        self,
        tasks: List[Dict[str, Any]],
        count: int = 3
    ) -> Dict[str, Any]:
        """
        Get top task suggestions with detailed explanations.
        
        Returns the top N tasks with human-readable explanations
        of why they were chosen.
        """
        analysis = self.analyze_tasks(tasks)
        top_tasks = analysis['tasks'][:count]
        
        suggestions = []
        for i, task in enumerate(top_tasks, 1):
            # Build recommendation explanation
            breakdown = task['scoring_breakdown']
            factors = []
            
            # Find the dominant factors
            scores = [
                ('urgency', breakdown['urgency']['weighted_score'], breakdown['urgency']['explanation']),
                ('importance', breakdown['importance']['weighted_score'], breakdown['importance']['explanation']),
                ('effort', breakdown['effort']['weighted_score'], breakdown['effort']['explanation']),
                ('dependency', breakdown['dependency']['weighted_score'], breakdown['dependency']['explanation'])
            ]
            scores.sort(key=lambda x: x[1], reverse=True)
            
            # Take top 2 factors for explanation
            top_factors = scores[:2]
            
            reason = f"Recommended because: {top_factors[0][2].lower()}"
            if top_factors[1][1] > 10:  # Only mention second factor if significant
                reason += f", and {top_factors[1][2].lower()}"
            
            suggestions.append({
                'rank': i,
                'task': task,
                'recommendation_reason': reason,
                'actionable_insight': self._get_actionable_insight(task)
            })
        
        return {
            'suggestions': suggestions,
            'strategy': self.strategy.value,
            'analysis_date': analysis['analysis_date'],
            'total_tasks_analyzed': analysis['total_count']
        }
    
    def _get_actionable_insight(self, task: Dict[str, Any]) -> str:
        """Generate an actionable insight for a task."""
        breakdown = task['scoring_breakdown']
        
        if task['priority_level'] == 'HIGH':
            if 'OVERDUE' in breakdown['urgency']['explanation']:
                return "⚠️ This task is overdue! Address immediately to avoid further delays."
            elif 'TODAY' in breakdown['urgency']['explanation']:
                return "📅 Due today! Block time now to complete this task."
            elif breakdown['dependency']['score'] > 80:
                return "🔗 This task is blocking others. Completing it will unblock your team."
            else:
                return "🎯 High priority task. Consider starting your day with this."
        elif task['priority_level'] == 'MEDIUM':
            if task['estimated_hours'] <= 2:
                return "⚡ Medium priority but quick to complete. Good for between meetings."
            else:
                return "📋 Schedule dedicated time for this task this week."
        else:
            return "📝 Lower priority. Good for when you have spare capacity."


def analyze_tasks_with_strategy(
    tasks: List[Dict[str, Any]],
    strategy: str = "smart_balance",
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Convenience function to analyze tasks with a specified strategy.
    
    Args:
        tasks: List of task dictionaries
        strategy: One of 'smart_balance', 'fastest_wins', 'high_impact', 'deadline_driven'
        custom_weights: Optional dict with 'urgency', 'importance', 'effort', 'dependency' keys
    
    Returns:
        Analysis results dictionary
    """
    try:
        strategy_enum = SortingStrategy(strategy)
    except ValueError:
        strategy_enum = SortingStrategy.SMART_BALANCE
    
    weights = None
    if custom_weights:
        weights = ScoringWeights(
            urgency=custom_weights.get('urgency', 0.3),
            importance=custom_weights.get('importance', 0.35),
            effort=custom_weights.get('effort', 0.15),
            dependency=custom_weights.get('dependency', 0.2)
        )
    
    scorer = TaskScorer(strategy=strategy_enum, custom_weights=weights)
    return scorer.analyze_tasks(tasks)


def get_task_suggestions(
    tasks: List[Dict[str, Any]],
    strategy: str = "smart_balance",
    count: int = 3
) -> Dict[str, Any]:
    """
    Convenience function to get task suggestions.
    
    Args:
        tasks: List of task dictionaries
        strategy: Sorting strategy to use
        count: Number of suggestions to return
    
    Returns:
        Suggestions dictionary with ranked recommendations
    """
    try:
        strategy_enum = SortingStrategy(strategy)
    except ValueError:
        strategy_enum = SortingStrategy.SMART_BALANCE
    
    scorer = TaskScorer(strategy=strategy_enum)
    return scorer.get_suggestions(tasks, count)
