"""
Cloud Sync Module

Handles synchronization with MongoDB Atlas cloud database.
Provides RESTful API integration for task storage and retrieval.
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class CloudSyncError(Exception):
    """Custom exception for cloud sync errors."""
    pass


class MongoDBCloudSync:
    """Handles cloud synchronization with MongoDB Atlas."""

    def __init__(self):
        self.mongodb_uri = os.getenv('MONGODB_URI')
        self.client = None
        self.db = None
        self.collection = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to MongoDB Atlas."""
        if not self.mongodb_uri:
            logger.warning("MONGODB_URI not found in environment variables")
            return

        try:
            self.client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Test the connection
            self.client.admin.command('ping')
            
            self.db = self.client.task_reminder
            self.collection = self.db.tasks
            
            # Create indexes for better performance
            self.collection.create_index("user_id")
            self.collection.create_index("status")
            self.collection.create_index("priority")
            self.collection.create_index("created_at")
            
            logger.info("Successfully connected to MongoDB Atlas")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            self.client = None

    def is_connected(self) -> bool:
        """Check if connected to MongoDB."""
        return self.client is not None and self.client.admin.command('ping')

    def sync_tasks_to_cloud(self, tasks_data: Dict[str, Any], user_id: str = "default") -> bool:
        """Sync local tasks to cloud database."""
        if not self.is_connected():
            logger.warning("Not connected to MongoDB, skipping cloud sync")
            return False

        try:
            # Prepare tasks for cloud storage
            cloud_tasks = []
            for task_id, task_data in tasks_data.items():
                cloud_task = {
                    "task_id": task_id,
                    "user_id": user_id,
                    "data": task_data,
                    "synced_at": datetime.now(timezone.utc).isoformat()
                }
                cloud_tasks.append(cloud_task)

            # Use upsert to handle both insert and update
            for cloud_task in cloud_tasks:
                self.collection.update_one(
                    {"task_id": cloud_task["task_id"], "user_id": user_id},
                    {"$set": cloud_task},
                    upsert=True
                )

            logger.info(f"Successfully synced {len(cloud_tasks)} tasks to cloud")
            return True

        except Exception as e:
            logger.error(f"Error syncing tasks to cloud: {e}")
            raise CloudSyncError(f"Failed to sync tasks to cloud: {e}")

    def sync_tasks_from_cloud(self, user_id: str = "default") -> Dict[str, Any]:
        """Sync tasks from cloud database to local."""
        if not self.is_connected():
            logger.warning("Not connected to MongoDB, skipping cloud sync")
            return {}

        try:
            # Get all tasks for the user
            cloud_tasks = list(self.collection.find(
                {"user_id": user_id},
                {"_id": 0, "task_id": 1, "data": 1}
            ))

            # Convert to local format
            local_tasks = {}
            for cloud_task in cloud_tasks:
                local_tasks[cloud_task["task_id"]] = cloud_task["data"]

            logger.info(f"Successfully synced {len(local_tasks)} tasks from cloud")
            return local_tasks

        except Exception as e:
            logger.error(f"Error syncing tasks from cloud: {e}")
            raise CloudSyncError(f"Failed to sync tasks from cloud: {e}")

    def get_cloud_statistics(self, user_id: str = "default") -> Dict[str, Any]:
        """Get task statistics from cloud database."""
        if not self.is_connected():
            return {"error": "Not connected to cloud database"}

        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": "$data.status",
                    "count": {"$sum": 1}
                }}
            ]
            
            status_stats = list(self.collection.aggregate(pipeline))
            
            # Convert to readable format
            stats = {}
            for stat in status_stats:
                status = stat["_id"]
                count = stat["count"]
                stats[status] = count

            return stats

        except Exception as e:
            logger.error(f"Error getting cloud statistics: {e}")
            return {"error": str(e)}

    def delete_task_from_cloud(self, task_id: str, user_id: str = "default") -> bool:
        """Delete a task from cloud database."""
        if not self.is_connected():
            logger.warning("Not connected to MongoDB, skipping cloud delete")
            return False

        try:
            result = self.collection.delete_one({
                "task_id": task_id,
                "user_id": user_id
            })
            
            if result.deleted_count > 0:
                logger.info(f"Successfully deleted task {task_id} from cloud")
                return True
            else:
                logger.warning(f"Task {task_id} not found in cloud")
                return False

        except Exception as e:
            logger.error(f"Error deleting task from cloud: {e}")
            raise CloudSyncError(f"Failed to delete task from cloud: {e}")

    def search_tasks_in_cloud(self, query: str, user_id: str = "default") -> List[Dict[str, Any]]:
        """Search tasks in cloud database."""
        if not self.is_connected():
            logger.warning("Not connected to MongoDB, skipping cloud search")
            return []

        try:
            # MongoDB text search
            cloud_tasks = list(self.collection.find({
                "user_id": user_id,
                "$text": {"$search": query}
            }, {"_id": 0, "task_id": 1, "data": 1}))

            # Convert to local format
            results = []
            for cloud_task in cloud_tasks:
                results.append({
                    "task_id": cloud_task["task_id"],
                    **cloud_task["data"]
                })

            logger.info(f"Found {len(results)} tasks matching '{query}' in cloud")
            return results

        except Exception as e:
            logger.error(f"Error searching tasks in cloud: {e}")
            return []

    def get_cloud_health(self) -> Dict[str, Any]:
        """Get cloud database health status."""
        if not self.is_connected():
            return {
                "status": "disconnected",
                "message": "Not connected to MongoDB Atlas"
            }

        try:
            # Test connection
            self.client.admin.command('ping')
            
            # Get basic stats
            db_stats = self.db.command("dbStats")
            collection_stats = self.collection.stats()
            
            return {
                "status": "connected",
                "database": {
                    "name": self.db.name,
                    "collections": db_stats.get("collections", 0),
                    "data_size": db_stats.get("dataSize", 0)
                },
                "collection": {
                    "name": self.collection.name,
                    "documents": collection_stats.get("count", 0),
                    "size": collection_stats.get("size", 0)
                },
                "last_check": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error checking cloud health: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def close_connection(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")


class RESTfulAPIClient:
    """RESTful API client for task operations."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make HTTP request to API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise CloudSyncError(f"API request failed: {e}")

    def sync_tasks(self, tasks_data: Dict[str, Any], user_id: str = "default") -> bool:
        """Sync tasks via RESTful API."""
        try:
            data = {
                "user_id": user_id,
                "tasks": tasks_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            result = self._make_request('POST', '/api/tasks/sync', data)
            logger.info(f"Successfully synced tasks via API: {result}")
            return True

        except Exception as e:
            logger.error(f"Error syncing tasks via API: {e}")
            return False

    def get_tasks(self, user_id: str = "default") -> Dict[str, Any]:
        """Get tasks via RESTful API."""
        try:
            result = self._make_request('GET', f'/api/tasks?user_id={user_id}')
            return result.get('tasks', {})

        except Exception as e:
            logger.error(f"Error getting tasks via API: {e}")
            return {}

    def delete_task(self, task_id: str, user_id: str = "default") -> bool:
        """Delete task via RESTful API."""
        try:
            result = self._make_request('DELETE', f'/api/tasks/{task_id}?user_id={user_id}')
            logger.info(f"Successfully deleted task via API: {result}")
            return True

        except Exception as e:
            logger.error(f"Error deleting task via API: {e}")
            return False 