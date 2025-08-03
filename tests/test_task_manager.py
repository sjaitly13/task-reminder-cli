"""
Unit tests for Task Manager module.
"""

import pytest
import tempfile
import os
import json
from datetime import datetime, timezone
from unittest.mock import patch

from task_manager import TaskManager, Task, Priority, TaskStatus


class TestTask:
    """Test Task data structure."""

    def test_task_creation(self):
        """Test basic task creation."""
        task = Task(
            id="1",
            title="Test Task",
            description="Test Description",
            priority=Priority.HIGH,
            status=TaskStatus.PENDING
        )
        
        assert task.id == "1"
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.priority == Priority.HIGH
        assert task.status == TaskStatus.PENDING
        assert task.created_at is not None
        assert task.updated_at is not None
        assert task.tags == []

    def test_task_to_dict(self):
        """Test task serialization to dictionary."""
        task = Task(
            id="1",
            title="Test Task",
            priority=Priority.MEDIUM,
            status=TaskStatus.COMPLETED
        )
        
        task_dict = task.to_dict()
        
        assert task_dict['id'] == "1"
        assert task_dict['title'] == "Test Task"
        assert task_dict['priority'] == "medium"
        assert task_dict['status'] == "completed"
        assert 'created_at' in task_dict
        assert 'updated_at' in task_dict

    def test_task_from_dict(self):
        """Test task deserialization from dictionary."""
        task_data = {
            'id': '2',
            'title': 'Test Task 2',
            'description': 'Test Description 2',
            'priority': 'high',
            'status': 'pending',
            'created_at': '2023-01-01T00:00:00+00:00',
            'updated_at': '2023-01-01T00:00:00+00:00',
            'tags': ['test', 'example']
        }
        
        task = Task.from_dict(task_data)
        
        assert task.id == "2"
        assert task.title == "Test Task 2"
        assert task.description == "Test Description 2"
        assert task.priority == Priority.HIGH
        assert task.status == TaskStatus.PENDING
        assert task.tags == ['test', 'example']


class TestTaskManager:
    """Test TaskManager functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def task_manager(self, temp_db_path):
        """Create a TaskManager instance with temporary database."""
        return TaskManager(db_path=temp_db_path)

    def test_add_task(self, task_manager):
        """Test adding a task."""
        task = task_manager.add_task(
            title="Test Task",
            description="Test Description",
            priority=Priority.HIGH,
            tags=["test", "example"]
        )
        
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.priority == Priority.HIGH
        assert task.status == TaskStatus.PENDING
        assert task.tags == ["test", "example"]
        assert task.id == "1"

    def test_get_task(self, task_manager):
        """Test getting a task by ID."""
        task_manager.add_task("Test Task")
        task = task_manager.get_task("1")
        
        assert task is not None
        assert task.title == "Test Task"

    def test_get_all_tasks(self, task_manager):
        """Test getting all tasks."""
        task_manager.add_task("Task 1")
        task_manager.add_task("Task 2")
        task_manager.add_task("Task 3")
        
        tasks = task_manager.get_all_tasks()
        assert len(tasks) == 3
        assert all(isinstance(task, Task) for task in tasks)

    def test_get_tasks_by_status(self, task_manager):
        """Test filtering tasks by status."""
        task_manager.add_task("Task 1")
        task_manager.add_task("Task 2")
        task_manager.complete_task("1")
        
        pending_tasks = task_manager.get_tasks_by_status(TaskStatus.PENDING)
        completed_tasks = task_manager.get_tasks_by_status(TaskStatus.COMPLETED)
        
        assert len(pending_tasks) == 1
        assert len(completed_tasks) == 1
        assert pending_tasks[0].title == "Task 2"
        assert completed_tasks[0].title == "Task 1"

    def test_get_tasks_by_priority(self, task_manager):
        """Test filtering tasks by priority."""
        task_manager.add_task("Task 1", priority=Priority.LOW)
        task_manager.add_task("Task 2", priority=Priority.HIGH)
        task_manager.add_task("Task 3", priority=Priority.MEDIUM)
        
        high_priority_tasks = task_manager.get_tasks_by_priority(Priority.HIGH)
        low_priority_tasks = task_manager.get_tasks_by_priority(Priority.LOW)
        
        assert len(high_priority_tasks) == 1
        assert len(low_priority_tasks) == 1
        assert high_priority_tasks[0].title == "Task 2"
        assert low_priority_tasks[0].title == "Task 1"

    def test_update_task(self, task_manager):
        """Test updating a task."""
        task_manager.add_task("Original Title")
        
        updated_task = task_manager.update_task(
            "1",
            title="Updated Title",
            priority=Priority.HIGH,
            status=TaskStatus.IN_PROGRESS
        )
        
        assert updated_task.title == "Updated Title"
        assert updated_task.priority == Priority.HIGH
        assert updated_task.status == TaskStatus.IN_PROGRESS

    def test_complete_task(self, task_manager):
        """Test completing a task."""
        task_manager.add_task("Test Task")
        completed_task = task_manager.complete_task("1")
        
        assert completed_task.status == TaskStatus.COMPLETED
        assert completed_task.completed_at is not None

    def test_delete_task(self, task_manager):
        """Test deleting a task."""
        task_manager.add_task("Test Task")
        
        # Verify task exists
        assert task_manager.get_task("1") is not None
        
        # Delete task
        result = task_manager.delete_task("1")
        assert result is True
        
        # Verify task is deleted
        assert task_manager.get_task("1") is None

    def test_delete_nonexistent_task(self, task_manager):
        """Test deleting a non-existent task."""
        result = task_manager.delete_task("999")
        assert result is False

    def test_get_task_statistics(self, task_manager):
        """Test getting task statistics."""
        # Add some tasks
        task_manager.add_task("Task 1", priority=Priority.HIGH)
        task_manager.add_task("Task 2", priority=Priority.MEDIUM)
        task_manager.add_task("Task 3", priority=Priority.LOW)
        task_manager.complete_task("1")
        
        stats = task_manager.get_task_statistics()
        
        assert stats['total'] == 3
        assert stats['completed'] == 1
        assert stats['pending'] == 2
        assert stats['completion_rate'] == pytest.approx(33.33, rel=1e-2)
        assert stats['by_priority']['high'] == 1
        assert stats['by_priority']['medium'] == 1
        assert stats['by_priority']['low'] == 1
        assert stats['by_status']['completed'] == 1
        assert stats['by_status']['pending'] == 2

    def test_get_task_statistics_empty(self, task_manager):
        """Test getting statistics for empty task list."""
        stats = task_manager.get_task_statistics()
        
        assert stats['total'] == 0
        assert stats['completed'] == 0
        assert stats['pending'] == 0
        assert stats['completion_rate'] == 0.0

    def test_search_tasks(self, task_manager):
        """Test searching tasks."""
        task_manager.add_task("Python programming task")
        task_manager.add_task("JavaScript development")
        task_manager.add_task("Database design", tags=["database", "sql"])
        
        # Search by title
        results = task_manager.search_tasks("python")
        assert len(results) == 1
        assert results[0].title == "Python programming task"
        
        # Search by tags
        results = task_manager.search_tasks("database")
        assert len(results) == 1
        assert results[0].title == "Database design"

    def test_export_tasks(self, task_manager):
        """Test exporting tasks for cloud sync."""
        task_manager.add_task("Task 1")
        task_manager.add_task("Task 2")
        
        exported = task_manager.export_tasks()
        
        assert len(exported) == 2
        assert "1" in exported
        assert "2" in exported
        assert exported["1"]["title"] == "Task 1"
        assert exported["2"]["title"] == "Task 2"

    def test_import_tasks(self, task_manager):
        """Test importing tasks from cloud sync."""
        cloud_tasks = {
            "1": {
                "id": "1",
                "title": "Cloud Task 1",
                "priority": "high",
                "status": "pending",
                "created_at": "2023-01-01T00:00:00+00:00",
                "updated_at": "2023-01-01T00:00:00+00:00",
                "tags": []
            },
            "2": {
                "id": "2",
                "title": "Cloud Task 2",
                "priority": "medium",
                "status": "completed",
                "created_at": "2023-01-01T00:00:00+00:00",
                "updated_at": "2023-01-01T00:00:00+00:00",
                "tags": ["cloud"]
            }
        }
        
        task_manager.import_tasks(cloud_tasks)
        
        tasks = task_manager.get_all_tasks()
        assert len(tasks) == 2
        assert tasks[0].title == "Cloud Task 1"
        assert tasks[1].title == "Cloud Task 2"

    def test_persistence(self, temp_db_path):
        """Test that tasks are persisted to file."""
        # Create first manager and add task
        manager1 = TaskManager(db_path=temp_db_path)
        manager1.add_task("Persistent Task")
        
        # Create second manager and verify task exists
        manager2 = TaskManager(db_path=temp_db_path)
        task = manager2.get_task("1")
        
        assert task is not None
        assert task.title == "Persistent Task"

    def test_invalid_priority(self, task_manager):
        """Test handling of invalid priority."""
        with pytest.raises(ValueError):
            Task.from_dict({
                'id': '1',
                'title': 'Test',
                'priority': 'invalid',
                'status': 'pending',
                'created_at': '2023-01-01T00:00:00+00:00',
                'updated_at': '2023-01-01T00:00:00+00:00'
            })

    def test_invalid_status(self, task_manager):
        """Test handling of invalid status."""
        with pytest.raises(ValueError):
            Task.from_dict({
                'id': '1',
                'title': 'Test',
                'priority': 'medium',
                'status': 'invalid',
                'created_at': '2023-01-01T00:00:00+00:00',
                'updated_at': '2023-01-01T00:00:00+00:00'
            }) 