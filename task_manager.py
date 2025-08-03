"""
Task Manager Module

Handles local task storage and operations using JSON file.
Provides CRUD operations for tasks with offline support.
"""

import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(Enum):
    """Task status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Task data structure."""
    id: str
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = None
    updated_at: str = None
    completed_at: Optional[str] = None
    tags: List[str] = None
    due_date: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for JSON serialization."""
        task_dict = asdict(self)
        task_dict['priority'] = self.priority.value
        task_dict['status'] = self.status.value
        return task_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary."""
        data['priority'] = Priority(data['priority'])
        data['status'] = TaskStatus(data['status'])
        return cls(**data)


class TaskManager:
    """Manages local task storage and operations."""

    def __init__(self, db_path: str = "./tasks.json"):
        self.db_path = db_path
        self.tasks: Dict[str, Task] = {}
        self._load_tasks()

    def _load_tasks(self) -> None:
        """Load tasks from JSON file."""
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = {
                        task_id: Task.from_dict(task_data)
                        for task_id, task_data in data.items()
                    }
                logger.info(f"Loaded {len(self.tasks)} tasks from {self.db_path}")
            else:
                logger.info(f"No existing task file found at {self.db_path}")
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            self.tasks = {}

    def _save_tasks(self) -> None:
        """Save tasks to JSON file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(
                    {task_id: task.to_dict() for task_id, task in self.tasks.items()},
                    f, indent=2, ensure_ascii=False
                )
            logger.info(f"Saved {len(self.tasks)} tasks to {self.db_path}")
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
            raise

    def add_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: Priority = Priority.MEDIUM,
        tags: List[str] = None,
        due_date: Optional[str] = None
    ) -> Task:
        """Add a new task."""
        task_id = str(len(self.tasks) + 1)
        task = Task(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            tags=tags or [],
            due_date=due_date
        )
        
        self.tasks[task_id] = task
        self._save_tasks()
        logger.info(f"Added task: {title}")
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return list(self.tasks.values())

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get tasks filtered by status."""
        return [task for task in self.tasks.values() if task.status == status]

    def get_tasks_by_priority(self, priority: Priority) -> List[Task]:
        """Get tasks filtered by priority."""
        return [task for task in self.tasks.values() if task.priority == priority]

    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[Priority] = None,
        status: Optional[TaskStatus] = None,
        tags: Optional[List[str]] = None,
        due_date: Optional[str] = None
    ) -> Optional[Task]:
        """Update an existing task."""
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found")
            return None

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = priority
        if status is not None:
            task.status = status
            if status == TaskStatus.COMPLETED and task.completed_at is None:
                task.completed_at = datetime.now(timezone.utc).isoformat()
        if tags is not None:
            task.tags = tags
        if due_date is not None:
            task.due_date = due_date

        task.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_tasks()
        logger.info(f"Updated task {task_id}")
        return task

    def complete_task(self, task_id: str) -> Optional[Task]:
        """Mark a task as completed."""
        return self.update_task(task_id, status=TaskStatus.COMPLETED)

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id in self.tasks:
            task_title = self.tasks[task_id].title
            del self.tasks[task_id]
            self._save_tasks()
            logger.info(f"Deleted task: {task_title}")
            return True
        logger.warning(f"Task {task_id} not found for deletion")
        return False

    def get_task_statistics(self) -> Dict[str, Any]:
        """Get task statistics."""
        total_tasks = len(self.tasks)
        if total_tasks == 0:
            return {
                "total": 0,
                "completed": 0,
                "pending": 0,
                "completion_rate": 0.0,
                "by_priority": {},
                "by_status": {}
            }

        completed_tasks = len(self.get_tasks_by_status(TaskStatus.COMPLETED))
        pending_tasks = len(self.get_tasks_by_status(TaskStatus.PENDING))
        
        # Group by priority
        by_priority = {}
        for priority in Priority:
            by_priority[priority.value] = len(self.get_tasks_by_priority(priority))

        # Group by status
        by_status = {}
        for status in TaskStatus:
            by_status[status.value] = len(self.get_tasks_by_status(status))

        return {
            "total": total_tasks,
            "completed": completed_tasks,
            "pending": pending_tasks,
            "completion_rate": (completed_tasks / total_tasks) * 100,
            "by_priority": by_priority,
            "by_status": by_status
        }

    def search_tasks(self, query: str) -> List[Task]:
        """Search tasks by title or description."""
        query_lower = query.lower()
        results = []
        
        for task in self.tasks.values():
            if (query_lower in task.title.lower() or
                (task.description and query_lower in task.description.lower()) or
                any(query_lower in tag.lower() for tag in task.tags)):
                results.append(task)
        
        return results

    def export_tasks(self) -> Dict[str, Any]:
        """Export all tasks for cloud sync."""
        return {
            task_id: task.to_dict()
            for task_id, task in self.tasks.items()
        }

    def import_tasks(self, tasks_data: Dict[str, Any]) -> None:
        """Import tasks from cloud sync."""
        for task_id, task_data in tasks_data.items():
            try:
                task = Task.from_dict(task_data)
                self.tasks[task_id] = task
            except Exception as e:
                logger.error(f"Error importing task {task_id}: {e}")
        
        self._save_tasks()
        logger.info(f"Imported {len(tasks_data)} tasks from cloud") 