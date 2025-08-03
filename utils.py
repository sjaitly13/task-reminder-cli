"""
Utility Functions Module

Provides helper functions for formatting, validation, and common operations.
"""

import os
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich import print as rprint
import logging

logger = logging.getLogger(__name__)
console = Console()


def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display."""
    if timestamp is None:
        return "None"
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return timestamp


def format_priority(priority: str) -> str:
    """Format priority for display with colors."""
    priority_map = {
        'high': '[red]HIGH[/red]',
        'medium': '[yellow]MEDIUM[/yellow]',
        'low': '[green]LOW[/green]'
    }
    return priority_map.get(priority.lower(), priority)


def format_status(status: str) -> str:
    """Format status for display with colors."""
    status_map = {
        'pending': '[yellow]PENDING[/yellow]',
        'in_progress': '[blue]IN PROGRESS[/blue]',
        'completed': '[green]COMPLETED[/green]',
        'cancelled': '[red]CANCELLED[/red]'
    }
    return status_map.get(status.lower(), status)


def validate_priority(priority: str) -> bool:
    """Validate priority value."""
    valid_priorities = ['low', 'medium', 'high']
    return priority.lower() in valid_priorities


def validate_status(status: str) -> bool:
    """Validate status value."""
    valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
    return status.lower() in valid_statuses


def validate_date(date_str: str) -> bool:
    """Validate date string format."""
    try:
        datetime.fromisoformat(date_str)
        return True
    except ValueError:
        return False


def parse_date(date_str: str) -> Optional[str]:
    """Parse and validate date string."""
    if not date_str:
        return None
    
    # Try different date formats
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
        '%d/%m/%Y',
        '%m/%d/%Y'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.isoformat()
        except ValueError:
            continue
    
    return None


def create_task_table(tasks: List[Dict[str, Any]], title: str = "Tasks") -> Table:
    """Create a rich table for displaying tasks."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Priority", style="white")
    table.add_column("Status", style="white")
    table.add_column("Created", style="dim")
    table.add_column("Due Date", style="dim")
    
    for task in tasks:
        table.add_row(
            task.get('id', ''),
            task.get('title', '')[:50] + ('...' if len(task.get('title', '')) > 50 else ''),
            format_priority(task.get('priority', 'medium')),
            format_status(task.get('status', 'pending')),
            format_timestamp(task.get('created_at', '')),
            format_timestamp(task.get('due_date', '')) if task.get('due_date') else '-'
        )
    
    return table


def create_statistics_panel(stats: Dict[str, Any]) -> Panel:
    """Create a rich panel for displaying statistics."""
    if 'error' in stats:
        return Panel(f"[red]Error: {stats['error']}[/red]", title="Statistics")
    
    content = f"""
[bold]Total Tasks:[/bold] {stats.get('total', 0)}
[bold]Completed:[/bold] {stats.get('completed', 0)}
[bold]Pending:[/bold] {stats.get('pending', 0)}
[bold]Completion Rate:[/bold] {stats.get('completion_rate', 0):.1f}%

[bold]By Priority:[/bold]
"""
    
    for priority, count in stats.get('by_priority', {}).items():
        content += f"  {priority.title()}: {count}\n"
    
    content += "\n[bold]By Status:[/bold]\n"
    for status, count in stats.get('by_status', {}).items():
        content += f"  {status.replace('_', ' ').title()}: {count}\n"
    
    return Panel(content, title="Task Statistics")


def create_cloud_health_panel(health: Dict[str, Any]) -> Panel:
    """Create a rich panel for displaying cloud health."""
    if health.get('status') == 'connected':
        content = f"""
[green]✓ Connected to MongoDB Atlas[/green]

[bold]Database:[/bold] {health.get('database', {}).get('name', 'N/A')}
[bold]Collections:[/bold] {health.get('database', {}).get('collections', 0)}
[bold]Data Size:[/bold] {health.get('database', {}).get('data_size', 0)} bytes

[bold]Collection:[/bold] {health.get('collection', {}).get('name', 'N/A')}
[bold]Documents:[/bold] {health.get('collection', {}).get('documents', 0)}
[bold]Size:[/bold] {health.get('collection', {}).get('size', 0)} bytes

[dim]Last Check: {health.get('last_check', 'N/A')}[/dim]
"""
    else:
        content = f"[red]✗ {health.get('message', 'Unknown error')}[/red]"
    
    return Panel(content, title="Cloud Health")


def show_progress_with_spinner(message: str):
    """Show a progress spinner with message."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(message, total=None)
        return progress, task


def prompt_for_task_details() -> Dict[str, Any]:
    """Prompt user for task details."""
    title = Prompt.ask("[bold cyan]Task title[/bold cyan]")
    
    description = Prompt.ask(
        "[bold cyan]Description[/bold cyan] (optional)",
        default=""
    )
    
    priority = Prompt.ask(
        "[bold cyan]Priority[/bold cyan]",
        choices=["low", "medium", "high"],
        default="medium"
    )
    
    tags_input = Prompt.ask(
        "[bold cyan]Tags[/bold cyan] (comma-separated, optional)",
        default=""
    )
    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []
    
    due_date = Prompt.ask(
        "[bold cyan]Due date[/bold cyan] (YYYY-MM-DD, optional)",
        default=""
    )
    
    return {
        'title': title,
        'description': description if description else None,
        'priority': priority,
        'tags': tags,
        'due_date': parse_date(due_date) if due_date else None
    }


def confirm_action(message: str) -> bool:
    """Confirm an action with the user."""
    return Confirm.ask(f"[bold yellow]{message}[/bold yellow]")


def print_success(message: str):
    """Print a success message."""
    console.print(f"[green]✓ {message}[/green]")


def print_error(message: str):
    """Print an error message."""
    console.print(f"[red]✗ {message}[/red]")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"[yellow]⚠ {message}[/yellow]")


def print_info(message: str):
    """Print an info message."""
    console.print(f"[blue]ℹ {message}[/blue]")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Ensure filename is not empty
    return filename or 'untitled'


def ensure_directory_exists(path: str) -> None:
    """Ensure directory exists, create if it doesn't."""
    os.makedirs(path, exist_ok=True)


def get_file_size_mb(filepath: str) -> float:
    """Get file size in megabytes."""
    try:
        size_bytes = os.path.getsize(filepath)
        return size_bytes / (1024 * 1024)
    except OSError:
        return 0.0


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to specified length."""
    if text is None:
        return "None"
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def highlight_search_term(text: str, search_term: str) -> str:
    """Highlight search term in text."""
    if text is None:
        return "None"
    if not search_term:
        return text
    
    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
    return pattern.sub(lambda m: f"[yellow]{m.group()}[/yellow]", text)


def create_search_results_table(results: List[Dict[str, Any]], query: str) -> Table:
    """Create a table for search results."""
    table = Table(title=f"Search Results for '{query}'", show_header=True, header_style="bold magenta")
    
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Description", style="white")
    table.add_column("Tags", style="dim")
    
    for result in results:
        title = highlight_search_term(result.get('title', ''), query)
        description = highlight_search_term(result.get('description', ''), query) if result.get('description') else '-'
        tags = ', '.join(result.get('tags', []))
        
        table.add_row(
            result.get('id', ''),
            title,
            truncate_text(description, 40),
            truncate_text(tags, 30)
        )
    
    return table 