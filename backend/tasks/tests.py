"""
Unit Tests for Smart Task Analyzer

Comprehensive test suite covering:
- Scoring algorithm correctness
- Edge case handling
- Circular dependency detection
- Different sorting strategies
- Input validation

Run with: python manage.py test tasks
"""
from datetime import date, timedelta
from django.test import TestCase
from .scoring import (
    TaskScorer,
    SortingStrategy,
    ScoringWeights,
    DependencyAnalyzer,
    TaskValidator,
    analyze_tasks_with_strategy,
    get_task_suggestions
)


class TestUrgencyScoring(TestCase):
    """Tests for urgency score calculation."""
    
    def setUp(self):
        self.scorer = TaskScorer()
        self.today = date.today()
    
    def test_overdue_task_gets_high_urgency(self):
        """Overdue tasks should receive urgency score > 100."""
        yesterday = self.today - timedelta(days=1)
        score, explanation = self.scorer.calculate_urgency_score(yesterday)
        
        self.assertGreater(score, 100)
        self.assertIn('OVERDUE', explanation)
    
    def test_due_today_gets_maximum_urgency(self):
        """Tasks due today should receive urgency score of 100."""
        score, explanation = self.scorer.calculate_urgency_score(self.today)
        
        self.assertEqual(score, 100.0)
        self.assertIn('TODAY', explanation)
    
    def test_due_tomorrow_gets_high_urgency(self):
        """Tasks due tomorrow should receive high urgency score."""
        tomorrow = self.today + timedelta(days=1)
        score, explanation = self.scorer.calculate_urgency_score(tomorrow)
        
        self.assertEqual(score, 90.0)
        self.assertIn('tomorrow', explanation)
    
    def test_no_due_date_gets_baseline_urgency(self):
        """Tasks without due date should get baseline score."""
        score, explanation = self.scorer.calculate_urgency_score(None)
        
        self.assertEqual(score, 20.0)
        self.assertIn('No due date', explanation)
    
    def test_far_future_gets_low_urgency(self):
        """Tasks due far in the future should get low urgency."""
        far_future = self.today + timedelta(days=60)
        score, explanation = self.scorer.calculate_urgency_score(far_future)
        
        self.assertLess(score, 30)


class TestImportanceScoring(TestCase):
    """Tests for importance score calculation."""
    
    def setUp(self):
        self.scorer = TaskScorer()
    
    def test_importance_10_gets_highest_score(self):
        """Maximum importance should get close to 100 score."""
        score, explanation = self.scorer.calculate_importance_score(10)
        
        self.assertGreater(score, 90)
        self.assertIn('Critical', explanation)
    
    def test_importance_1_gets_lowest_score(self):
        """Minimum importance should get close to 0 score."""
        score, explanation = self.scorer.calculate_importance_score(1)
        
        self.assertLess(score, 10)
        self.assertIn('Low', explanation)
    
    def test_importance_scales_appropriately(self):
        """Higher importance should always yield higher scores."""
        scores = []
        for importance in range(1, 11):
            score, _ = self.scorer.calculate_importance_score(importance)
            scores.append(score)
        
        # Verify monotonically increasing
        for i in range(len(scores) - 1):
            self.assertLess(scores[i], scores[i + 1])


class TestEffortScoring(TestCase):
    """Tests for effort score calculation."""
    
    def setUp(self):
        self.scorer = TaskScorer()
    
    def test_quick_task_gets_high_effort_score(self):
        """Quick tasks (< 1 hour) should be prioritized."""
        score, explanation = self.scorer.calculate_effort_score(0.5)
        
        self.assertGreater(score, 90)
        self.assertIn('Quick', explanation)
    
    def test_long_task_gets_lower_effort_score(self):
        """Long tasks should get lower effort scores."""
        score, explanation = self.scorer.calculate_effort_score(10)
        
        self.assertLess(score, 40)
    
    def test_effort_inverse_relationship(self):
        """Lower effort should yield higher scores."""
        short_score, _ = self.scorer.calculate_effort_score(1)
        long_score, _ = self.scorer.calculate_effort_score(8)
        
        self.assertGreater(short_score, long_score)


class TestDependencyAnalysis(TestCase):
    """Tests for dependency analysis and circular detection."""
    
    def test_detects_simple_circular_dependency(self):
        """Should detect A -> B -> A cycle."""
        tasks = [
            {'id': 'A', 'title': 'Task A', 'dependencies': ['B']},
            {'id': 'B', 'title': 'Task B', 'dependencies': ['A']}
        ]
        
        analyzer = DependencyAnalyzer(tasks)
        cycles = analyzer.detect_circular_dependencies()
        
        self.assertTrue(len(cycles) > 0)
    
    def test_detects_longer_circular_dependency(self):
        """Should detect A -> B -> C -> A cycle."""
        tasks = [
            {'id': 'A', 'title': 'Task A', 'dependencies': ['B']},
            {'id': 'B', 'title': 'Task B', 'dependencies': ['C']},
            {'id': 'C', 'title': 'Task C', 'dependencies': ['A']}
        ]
        
        analyzer = DependencyAnalyzer(tasks)
        cycles = analyzer.detect_circular_dependencies()
        
        self.assertTrue(len(cycles) > 0)
    
    def test_no_circular_dependency_in_valid_graph(self):
        """Should not report cycles in a valid dependency graph."""
        tasks = [
            {'id': 'A', 'title': 'Task A', 'dependencies': []},
            {'id': 'B', 'title': 'Task B', 'dependencies': ['A']},
            {'id': 'C', 'title': 'Task C', 'dependencies': ['A', 'B']}
        ]
        
        analyzer = DependencyAnalyzer(tasks)
        cycles = analyzer.detect_circular_dependencies()
        
        self.assertEqual(len(cycles), 0)
    
    def test_blocking_count_calculation(self):
        """Should correctly count tasks blocked by a task."""
        tasks = [
            {'id': 'A', 'title': 'Task A', 'dependencies': []},
            {'id': 'B', 'title': 'Task B', 'dependencies': ['A']},
            {'id': 'C', 'title': 'Task C', 'dependencies': ['A']},
            {'id': 'D', 'title': 'Task D', 'dependencies': ['B']}
        ]
        
        analyzer = DependencyAnalyzer(tasks)
        
        # Task A blocks B, C, and D (transitively)
        self.assertEqual(analyzer.get_blocking_count('A'), 3)
        # Task B only blocks D
        self.assertEqual(analyzer.get_blocking_count('B'), 1)
        # Task C blocks nothing
        self.assertEqual(analyzer.get_blocking_count('C'), 0)


class TestTaskValidator(TestCase):
    """Tests for task input validation."""
    
    def test_validates_missing_title(self):
        """Should add warning and default title for missing title."""
        task = {'due_date': '2025-01-15', 'importance': 5}
        validated, warnings = TaskValidator.validate_task(task)
        
        self.assertEqual(validated['title'], 'Untitled Task')
        self.assertTrue(any('title' in w.lower() for w in warnings))
    
    def test_validates_invalid_date_format(self):
        """Should handle invalid date format gracefully."""
        task = {'title': 'Test', 'due_date': 'not-a-date'}
        validated, warnings = TaskValidator.validate_task(task)
        
        self.assertIsNone(validated['due_date'])
        self.assertTrue(any('date' in w.lower() for w in warnings))
    
    def test_clamps_importance_to_valid_range(self):
        """Should clamp importance to 1-10 range."""
        task_low = {'title': 'Test', 'importance': -5}
        task_high = {'title': 'Test', 'importance': 100}
        
        validated_low, _ = TaskValidator.validate_task(task_low)
        validated_high, _ = TaskValidator.validate_task(task_high)
        
        self.assertEqual(validated_low['importance'], 1)
        self.assertEqual(validated_high['importance'], 10)
    
    def test_handles_invalid_estimated_hours(self):
        """Should default invalid estimated hours."""
        task = {'title': 'Test', 'estimated_hours': 'not-a-number'}
        validated, warnings = TaskValidator.validate_task(task)
        
        self.assertEqual(validated['estimated_hours'], 1.0)
        self.assertTrue(any('estimated_hours' in w.lower() for w in warnings))


class TestSortingStrategies(TestCase):
    """Tests for different sorting strategies."""
    
    def setUp(self):
        self.today = date.today()
        self.tasks = [
            {
                'id': '1',
                'title': 'Quick important task',
                'due_date': (self.today + timedelta(days=7)).isoformat(),
                'estimated_hours': 1,
                'importance': 9,
                'dependencies': []
            },
            {
                'id': '2',
                'title': 'Long urgent task',
                'due_date': (self.today + timedelta(days=1)).isoformat(),
                'estimated_hours': 8,
                'importance': 5,
                'dependencies': []
            },
            {
                'id': '3',
                'title': 'Quick low priority',
                'due_date': (self.today + timedelta(days=14)).isoformat(),
                'estimated_hours': 0.5,
                'importance': 3,
                'dependencies': []
            }
        ]
    
    def test_fastest_wins_prioritizes_low_effort(self):
        """Fastest wins strategy should put quick tasks first."""
        result = analyze_tasks_with_strategy(self.tasks, 'fastest_wins')
        
        sorted_tasks = result['tasks']
        # The quick low priority task should rank higher due to effort weight
        quick_task_idx = next(
            i for i, t in enumerate(sorted_tasks)
            if t['title'] == 'Quick low priority'
        )
        long_task_idx = next(
            i for i, t in enumerate(sorted_tasks)
            if t['title'] == 'Long urgent task'
        )
        
        # Quick task should be ranked higher (lower index)
        self.assertLess(quick_task_idx, long_task_idx)
    
    def test_deadline_driven_prioritizes_urgent(self):
        """Deadline driven strategy should prioritize by due date."""
        result = analyze_tasks_with_strategy(self.tasks, 'deadline_driven')
        
        sorted_tasks = result['tasks']
        # The urgent task (due tomorrow) should be first
        self.assertEqual(sorted_tasks[0]['title'], 'Long urgent task')
    
    def test_high_impact_prioritizes_importance(self):
        """High impact strategy should prioritize by importance."""
        result = analyze_tasks_with_strategy(self.tasks, 'high_impact')
        
        sorted_tasks = result['tasks']
        # The high importance task should be first
        self.assertEqual(sorted_tasks[0]['title'], 'Quick important task')


class TestFullAnalysis(TestCase):
    """Integration tests for complete analysis flow."""
    
    def test_analyze_returns_correct_structure(self):
        """Analysis should return all required fields."""
        tasks = [
            {
                'title': 'Test task',
                'due_date': date.today().isoformat(),
                'estimated_hours': 2,
                'importance': 7,
                'dependencies': []
            }
        ]
        
        result = analyze_tasks_with_strategy(tasks)
        
        self.assertIn('tasks', result)
        self.assertIn('total_count', result)
        self.assertIn('strategy', result)
        self.assertIn('circular_dependencies', result)
        self.assertIn('priority_distribution', result)
        
        # Check task has scoring details
        task = result['tasks'][0]
        self.assertIn('priority_score', task)
        self.assertIn('priority_level', task)
        self.assertIn('scoring_breakdown', task)
    
    def test_suggestions_returns_correct_count(self):
        """Suggestions should return requested number of tasks."""
        tasks = [
            {'title': f'Task {i}', 'importance': i}
            for i in range(1, 6)
        ]
        
        result = get_task_suggestions(tasks, count=3)
        
        self.assertEqual(len(result['suggestions']), 3)
    
    def test_empty_task_list_handled(self):
        """Should handle empty task list gracefully."""
        result = analyze_tasks_with_strategy([])
        
        self.assertEqual(result['total_count'], 0)
        self.assertEqual(len(result['tasks']), 0)
    
    def test_tasks_sorted_by_priority_descending(self):
        """Tasks should be sorted from highest to lowest priority."""
        tasks = [
            {'title': 'Low', 'importance': 1},
            {'title': 'High', 'importance': 10},
            {'title': 'Medium', 'importance': 5}
        ]
        
        result = analyze_tasks_with_strategy(tasks)
        scores = [t['priority_score'] for t in result['tasks']]
        
        # Verify descending order
        self.assertEqual(scores, sorted(scores, reverse=True))


class TestEdgeCases(TestCase):
    """Tests for edge cases and boundary conditions."""
    
    def test_extreme_overdue_task(self):
        """Should handle tasks overdue by many days."""
        today = date.today()
        tasks = [{
            'title': 'Very overdue',
            'due_date': (today - timedelta(days=100)).isoformat(),
            'importance': 5
        }]
        
        result = analyze_tasks_with_strategy(tasks)
        task = result['tasks'][0]
        
        # Should still be HIGH priority
        self.assertEqual(task['priority_level'], 'HIGH')
    
    def test_very_large_estimated_hours(self):
        """Should handle very large estimated hours."""
        tasks = [{
            'title': 'Huge task',
            'estimated_hours': 1000,
            'importance': 5
        }]
        
        result = analyze_tasks_with_strategy(tasks)
        task = result['tasks'][0]
        
        # Should still produce a valid score
        self.assertGreaterEqual(task['priority_score'], 0)
        self.assertLessEqual(task['priority_score'], 100)
    
    def test_handles_invalid_dependency_references(self):
        """Should ignore dependencies to non-existent tasks."""
        tasks = [
            {'id': '1', 'title': 'Task 1', 'dependencies': ['non_existent']},
            {'id': '2', 'title': 'Task 2', 'dependencies': ['1']}
        ]
        
        result = analyze_tasks_with_strategy(tasks)
        
        # Should complete without error
        self.assertEqual(result['total_count'], 2)
    
    def test_handles_self_dependency(self):
        """Should handle task depending on itself."""
        tasks = [
            {'id': '1', 'title': 'Self dependent', 'dependencies': ['1']}
        ]
        
        result = analyze_tasks_with_strategy(tasks)
        
        # Should detect as circular dependency
        self.assertTrue(len(result['circular_dependencies']) > 0)
