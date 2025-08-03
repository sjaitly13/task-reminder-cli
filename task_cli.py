#!/usr/bin/env python3
"""
Task Reminder CLI Tool

A command-line interface for managing tasks with cloud synchronization.
Supports local JSON storage and MongoDB Atlas cloud sync.
"""

import argparse
import sys
import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

from task_manager import TaskManager, Priority, TaskStatus
from cloud_sync import MongoDBCloudSync, CloudSyncError
from auth_handler import get_auth_handler
from utils import (
    create_task_table, create_statistics_panel, create_cloud_health_panel,
    prompt_for_task_details, confirm_action, print_success, print_error,
    print_warning, print_info, create_search_results_table,
    validate_priority, validate_status, parse_date, console
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskCLI:
    """Main CLI application for task management."""

    def __init__(self):
        self.task_manager = TaskManager()
        self.cloud_sync = MongoDBCloudSync()
        self.auth_handler = get_auth_handler()

    def add_task(self, title: str, description: str = None, priority: str = "medium",
                 tags: List[str] = None, due_date: str = None) -> None:
        """Add a new task."""
        try:
            # Validate priority
            if not validate_priority(priority):
                print_error(f"Invalid priority: {priority}. Use: low, medium, high")
                return

            # Parse due date
            parsed_due_date = parse_date(due_date) if due_date else None

            # Add task
            task = self.task_manager.add_task(
                title=title,
                description=description,
                priority=Priority(priority),
                tags=tags or [],
                due_date=parsed_due_date
            )

            print_success(f"Task added successfully: {task.title}")

            # Sync to cloud if connected
            if self.cloud_sync.is_connected():
                try:
                    self.cloud_sync.sync_tasks_to_cloud(
                        self.task_manager.export_tasks(),
                        user_id=self.auth_handler.get_user_info().get('user_id', 'default')
                    )
                    print_info("Task synced to cloud")
                except CloudSyncError as e:
                    print_warning(f"Cloud sync failed: {e}")

        except Exception as e:
            print_error(f"Error adding task: {e}")
            logger.error(f"Error adding task: {e}")

    def list_tasks(self, status: str = None, priority: str = None, 
                   show_completed: bool = False) -> None:
        """List tasks with optional filtering."""
        try:
            tasks = self.task_manager.get_all_tasks()

            # Filter by status
            if status:
                if not validate_status(status):
                    print_error(f"Invalid status: {status}")
                    return
                tasks = [task for task in tasks if task.status.value == status]

            # Filter by priority
            if priority:
                if not validate_priority(priority):
                    print_error(f"Invalid priority: {priority}")
                    return
                tasks = [task for task in tasks if task.priority.value == priority]

            # Filter completed tasks
            if not show_completed:
                tasks = [task for task in tasks if task.status != TaskStatus.COMPLETED]

            if not tasks:
                print_info("No tasks found")
                return

            # Convert to dict format for display
            task_dicts = [task.to_dict() for task in tasks]
            table = create_task_table(task_dicts)
            console.print(table)

        except Exception as e:
            print_error(f"Error listing tasks: {e}")
            logger.error(f"Error listing tasks: {e}")

    def complete_task(self, task_id: str) -> None:
        """Mark a task as completed."""
        try:
            task = self.task_manager.complete_task(task_id)
            if task:
                print_success(f"Task completed: {task.title}")

                # Sync to cloud if connected
                if self.cloud_sync.is_connected():
                    try:
                        self.cloud_sync.sync_tasks_to_cloud(
                            self.task_manager.export_tasks(),
                            user_id=self.auth_handler.get_user_info().get('user_id', 'default')
                        )
                        print_info("Task sync updated in cloud")
                    except CloudSyncError as e:
                        print_warning(f"Cloud sync failed: {e}")
            else:
                print_error(f"Task {task_id} not found")

        except Exception as e:
            print_error(f"Error completing task: {e}")
            logger.error(f"Error completing task: {e}")

    def delete_task(self, task_id: str) -> None:
        """Delete a task."""
        try:
            if confirm_action(f"Are you sure you want to delete task {task_id}?"):
                if self.task_manager.delete_task(task_id):
                    print_success(f"Task {task_id} deleted")

                    # Delete from cloud if connected
                    if self.cloud_sync.is_connected():
                        try:
                            self.cloud_sync.delete_task_from_cloud(
                                task_id,
                                user_id=self.auth_handler.get_user_info().get('user_id', 'default')
                            )
                            print_info("Task deleted from cloud")
                        except CloudSyncError as e:
                            print_warning(f"Cloud delete failed: {e}")
                else:
                    print_error(f"Task {task_id} not found")

        except Exception as e:
            print_error(f"Error deleting task: {e}")
            logger.error(f"Error deleting task: {e}")

    def update_task(self, task_id: str, **kwargs) -> None:
        """Update a task."""
        try:
            # Validate inputs
            if 'priority' in kwargs and not validate_priority(kwargs['priority']):
                print_error(f"Invalid priority: {kwargs['priority']}")
                return

            if 'status' in kwargs and not validate_status(kwargs['status']):
                print_error(f"Invalid status: {kwargs['status']}")
                return

            if 'due_date' in kwargs and kwargs['due_date']:
                parsed_date = parse_date(kwargs['due_date'])
                if not parsed_date:
                    print_error(f"Invalid date format: {kwargs['due_date']}")
                    return
                kwargs['due_date'] = parsed_date

            # Convert string values to enums
            if 'priority' in kwargs:
                kwargs['priority'] = Priority(kwargs['priority'])
            if 'status' in kwargs:
                kwargs['status'] = TaskStatus(kwargs['status'])

            task = self.task_manager.update_task(task_id, **kwargs)
            if task:
                print_success(f"Task updated: {task.title}")

                # Sync to cloud if connected
                if self.cloud_sync.is_connected():
                    try:
                        self.cloud_sync.sync_tasks_to_cloud(
                            self.task_manager.export_tasks(),
                            user_id=self.auth_handler.get_user_info().get('user_id', 'default')
                        )
                        print_info("Task sync updated in cloud")
                    except CloudSyncError as e:
                        print_warning(f"Cloud sync failed: {e}")
            else:
                print_error(f"Task {task_id} not found")

        except Exception as e:
            print_error(f"Error updating task: {e}")
            logger.error(f"Error updating task: {e}")

    def show_statistics(self) -> None:
        """Show task statistics."""
        try:
            stats = self.task_manager.get_task_statistics()
            panel = create_statistics_panel(stats)
            console.print(panel)

            # Show cloud statistics if connected
            if self.cloud_sync.is_connected():
                cloud_stats = self.cloud_sync.get_cloud_statistics(
                    user_id=self.auth_handler.get_user_info().get('user_id', 'default')
                )
                if 'error' not in cloud_stats:
                    print_info("Cloud statistics available")
                    print(f"Cloud tasks by status: {cloud_stats}")

        except Exception as e:
            print_error(f"Error showing statistics: {e}")
            logger.error(f"Error showing statistics: {e}")

    def search_tasks(self, query: str) -> None:
        """Search tasks by title, description, or tags."""
        try:
            results = self.task_manager.search_tasks(query)
            
            if not results:
                print_info(f"No tasks found matching '{query}'")
                return

            # Convert to dict format for display
            result_dicts = [task.to_dict() for task in results]
            table = create_search_results_table(result_dicts, query)
            console.print(table)

        except Exception as e:
            print_error(f"Error searching tasks: {e}")
            logger.error(f"Error searching tasks: {e}")

    def sync_with_cloud(self, direction: str = "both") -> None:
        """Sync tasks with cloud database."""
        try:
            if not self.cloud_sync.is_connected():
                print_warning("Not connected to cloud database")
                return

            user_id = self.auth_handler.get_user_info().get('user_id', 'default')

            if direction in ["up", "both"]:
                print_info("Syncing local tasks to cloud...")
                self.cloud_sync.sync_tasks_to_cloud(
                    self.task_manager.export_tasks(),
                    user_id=user_id
                )
                print_success("Tasks synced to cloud")

            if direction in ["down", "both"]:
                print_info("Syncing tasks from cloud...")
                cloud_tasks = self.cloud_sync.sync_tasks_from_cloud(user_id=user_id)
                if cloud_tasks:
                    self.task_manager.import_tasks(cloud_tasks)
                    print_success(f"Synced {len(cloud_tasks)} tasks from cloud")
                else:
                    print_info("No tasks found in cloud")

        except CloudSyncError as e:
            print_error(f"Cloud sync error: {e}")
        except Exception as e:
            print_error(f"Error syncing with cloud: {e}")
            logger.error(f"Error syncing with cloud: {e}")

    def show_cloud_health(self) -> None:
        """Show cloud database health status."""
        try:
            health = self.cloud_sync.get_cloud_health()
            panel = create_cloud_health_panel(health)
            console.print(panel)

        except Exception as e:
            print_error(f"Error checking cloud health: {e}")
            logger.error(f"Error checking cloud health: {e}")

    def authenticate(self) -> None:
        """Authenticate user."""
        try:
            if self.auth_handler.authenticate():
                user_info = self.auth_handler.get_user_info()
                print_success(f"Authenticated as: {user_info.get('name', 'Unknown')}")
            else:
                print_error("Authentication failed")

        except Exception as e:
            print_error(f"Authentication error: {e}")
            logger.error(f"Authentication error: {e}")

    def logout(self) -> None:
        """Logout user."""
        try:
            self.auth_handler.logout()
            print_success("Logged out successfully")

        except Exception as e:
            print_error(f"Logout error: {e}")
            logger.error(f"Logout error: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Task Reminder CLI Tool with Cloud Sync",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python task_cli.py add "Complete project" --priority high
  python task_cli.py list --status pending
  python task_cli.py complete 1
  python task_cli.py stats
  python task_cli.py sync
  python task_cli.py auth
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add task command
    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('title', help='Task title')
    add_parser.add_argument('--description', '-d', help='Task description')
    add_parser.add_argument('--priority', '-p', choices=['low', 'medium', 'high'],
                           default='medium', help='Task priority')
    add_parser.add_argument('--tags', '-t', nargs='+', help='Task tags')
    add_parser.add_argument('--due-date', help='Due date (YYYY-MM-DD)')

    # List tasks command
    list_parser = subparsers.add_parser('list', help='List tasks')
    list_parser.add_argument('--status', '-s', choices=['pending', 'in_progress', 'completed', 'cancelled'],
                            help='Filter by status')
    list_parser.add_argument('--priority', '-p', choices=['low', 'medium', 'high'],
                            help='Filter by priority')
    list_parser.add_argument('--show-completed', action='store_true',
                            help='Show completed tasks')

    # Complete task command
    complete_parser = subparsers.add_parser('complete', help='Mark task as completed')
    complete_parser.add_argument('task_id', help='Task ID to complete')

    # Delete task command
    delete_parser = subparsers.add_parser('delete', help='Delete a task')
    delete_parser.add_argument('task_id', help='Task ID to delete')

    # Update task command
    update_parser = subparsers.add_parser('update', help='Update a task')
    update_parser.add_argument('task_id', help='Task ID to update')
    update_parser.add_argument('--title', help='New task title')
    update_parser.add_argument('--description', help='New task description')
    update_parser.add_argument('--priority', choices=['low', 'medium', 'high'],
                              help='New task priority')
    update_parser.add_argument('--status', choices=['pending', 'in_progress', 'completed', 'cancelled'],
                              help='New task status')
    update_parser.add_argument('--tags', nargs='+', help='New task tags')
    update_parser.add_argument('--due-date', help='New due date (YYYY-MM-DD)')

    # Statistics command
    subparsers.add_parser('stats', help='Show task statistics')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search tasks')
    search_parser.add_argument('query', help='Search query')

    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync with cloud database')
    sync_parser.add_argument('--direction', choices=['up', 'down', 'both'],
                            default='both', help='Sync direction')

    # Cloud health command
    subparsers.add_parser('health', help='Show cloud database health')

    # Authentication commands
    subparsers.add_parser('auth', help='Authenticate user')
    subparsers.add_parser('logout', help='Logout user')

    # Interactive mode
    subparsers.add_parser('interactive', help='Start interactive mode')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = TaskCLI()

    try:
        if args.command == 'add':
            cli.add_task(
                title=args.title,
                description=args.description,
                priority=args.priority,
                tags=args.tags,
                due_date=args.due_date
            )

        elif args.command == 'list':
            cli.list_tasks(
                status=args.status,
                priority=args.priority,
                show_completed=args.show_completed
            )

        elif args.command == 'complete':
            cli.complete_task(args.task_id)

        elif args.command == 'delete':
            cli.delete_task(args.task_id)

        elif args.command == 'update':
            update_kwargs = {}
            if args.title:
                update_kwargs['title'] = args.title
            if args.description:
                update_kwargs['description'] = args.description
            if args.priority:
                update_kwargs['priority'] = args.priority
            if args.status:
                update_kwargs['status'] = args.status
            if args.tags:
                update_kwargs['tags'] = args.tags
            if args.due_date:
                update_kwargs['due_date'] = args.due_date

            cli.update_task(args.task_id, **update_kwargs)

        elif args.command == 'stats':
            cli.show_statistics()

        elif args.command == 'search':
            cli.search_tasks(args.query)

        elif args.command == 'sync':
            cli.sync_with_cloud(args.direction)

        elif args.command == 'health':
            cli.show_cloud_health()

        elif args.command == 'auth':
            cli.authenticate()

        elif args.command == 'logout':
            cli.logout()

        elif args.command == 'interactive':
            run_interactive_mode(cli)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


def run_interactive_mode(cli: TaskCLI):
    """Run interactive mode for task management."""
    print("Welcome to Task Reminder CLI Interactive Mode!")
    print("Type 'help' for available commands, 'quit' to exit.")

    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command == 'quit' or command == 'exit':
                print("Goodbye!")
                break
            elif command == 'help':
                print("""
Available commands:
  add <title> - Add a new task
  list - List all tasks
  complete <id> - Mark task as completed
  delete <id> - Delete a task
  stats - Show statistics
  search <query> - Search tasks
  sync - Sync with cloud
  health - Show cloud health
  auth - Authenticate
  logout - Logout
  quit - Exit
                """)
            elif command.startswith('add '):
                title = command[4:].strip()
                if title:
                    cli.add_task(title)
                else:
                    print_error("Please provide a task title")
            elif command == 'list':
                cli.list_tasks()
            elif command.startswith('complete '):
                task_id = command[9:].strip()
                if task_id:
                    cli.complete_task(task_id)
                else:
                    print_error("Please provide a task ID")
            elif command.startswith('delete '):
                task_id = command[7:].strip()
                if task_id:
                    cli.delete_task(task_id)
                else:
                    print_error("Please provide a task ID")
            elif command == 'stats':
                cli.show_statistics()
            elif command.startswith('search '):
                query = command[7:].strip()
                if query:
                    cli.search_tasks(query)
                else:
                    print_error("Please provide a search query")
            elif command == 'sync':
                cli.sync_with_cloud()
            elif command == 'health':
                cli.show_cloud_health()
            elif command == 'auth':
                cli.authenticate()
            elif command == 'logout':
                cli.logout()
            else:
                print_error("Unknown command. Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\nExiting interactive mode...")
            break
        except Exception as e:
            print_error(f"Error: {e}")


if __name__ == '__main__':
    main() 