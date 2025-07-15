"""
WebSocket manager for real-time updates in Sovera.
Handles live table data synchronization using PostgreSQL LISTEN/NOTIFY.
"""

import json
import logging
import asyncio
import asyncpg
from typing import Dict, Set, List, Optional, Callable
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from models.user import User
from models.project import Project
from utils.rbac import PermissionManager

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and real-time updates"""
    
    def __init__(self):
        # Store active connections: project_id -> table_name -> set of websockets
        self.connections: Dict[int, Dict[str, Set[WebSocket]]] = {}
        # Store user info for each connection
        self.connection_users: Dict[WebSocket, User] = {}
        # Store PostgreSQL listeners for each project
        self.pg_listeners: Dict[int, asyncpg.Connection] = {}
        
    async def connect(self, websocket: WebSocket, project_id: int, table_name: str, user: User):
        """Connect a WebSocket to receive updates for a specific project table"""
        await websocket.accept()
        
        # Initialize nested dicts if needed
        if project_id not in self.connections:
            self.connections[project_id] = {}
        if table_name not in self.connections[project_id]:
            self.connections[project_id][table_name] = set()
        
        # Add connection
        self.connections[project_id][table_name].add(websocket)
        self.connection_users[websocket] = user
        
        # Start PostgreSQL listener for this project if not already started
        if project_id not in self.pg_listeners:
            await self._start_pg_listener(project_id)
        
        logger.info(f"WebSocket connected: user {user.id} to project {project_id} table {table_name}")
        
        # Send initial connection message
        await self._send_message(websocket, {
            "type": "connection_established",
            "project_id": project_id,
            "table_name": table_name,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket and clean up"""
        user = self.connection_users.pop(websocket, None)
        
        # Remove from all connections
        for project_id, tables in self.connections.items():
            for table_name, connections in tables.items():
                connections.discard(websocket)
                
                # Clean up empty sets
                if not connections:
                    del tables[table_name]
            
            # Clean up empty project dicts
            if not tables:
                del self.connections[project_id]
                # Stop PostgreSQL listener if no more connections
                if project_id in self.pg_listeners:
                    await self._stop_pg_listener(project_id)
        
        if user:
            logger.info(f"WebSocket disconnected: user {user.id}")
    
    async def broadcast_table_update(self, project_id: int, table_name: str, message: dict):
        """Broadcast an update to all connected clients for a specific table"""
        if project_id not in self.connections:
            return
        
        if table_name not in self.connections[project_id]:
            return
        
        connections = self.connections[project_id][table_name].copy()
        disconnected = []
        
        for websocket in connections:
            try:
                await self._send_message(websocket, message)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected:
            await self.disconnect(websocket)
    
    async def _send_message(self, websocket: WebSocket, message: dict):
        """Send a JSON message to a WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            raise
    
    async def _start_pg_listener(self, project_id: int):
        """Start PostgreSQL LISTEN/NOTIFY listener for a project"""
        try:
            # Get project database connection info
            import os
            pg_host = os.getenv("POSTGRES_SERVER", "localhost")
            pg_user = os.getenv("POSTGRES_USER", "postgres")
            pg_password = os.getenv("POSTGRES_PASSWORD")
            
            # Connect to project database
            db_name = f"project_*_{project_id}_db"  # This would need to be looked up properly
            db_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}/{db_name}"
            
            # For now, we'll use the main database and simulate project-specific notifications
            main_db_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}/sovera"
            
            conn = await asyncpg.connect(main_db_url)
            self.pg_listeners[project_id] = conn
            
            # Listen for table changes
            await conn.add_listener(f'table_changes_{project_id}', self._handle_pg_notification)
            
            logger.info(f"Started PostgreSQL listener for project {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to start PostgreSQL listener for project {project_id}: {e}")
    
    async def _stop_pg_listener(self, project_id: int):
        """Stop PostgreSQL listener for a project"""
        if project_id in self.pg_listeners:
            try:
                conn = self.pg_listeners[project_id]
                await conn.remove_listener(f'table_changes_{project_id}', self._handle_pg_notification)
                await conn.close()
                del self.pg_listeners[project_id]
                logger.info(f"Stopped PostgreSQL listener for project {project_id}")
            except Exception as e:
                logger.error(f"Error stopping PostgreSQL listener for project {project_id}: {e}")
    
    async def _handle_pg_notification(self, connection, pid, channel, payload):
        """Handle PostgreSQL NOTIFY messages"""
        try:
            data = json.loads(payload)
            project_id = data.get('project_id')
            table_name = data.get('table_name')
            operation = data.get('operation')  # INSERT, UPDATE, DELETE
            row_data = data.get('data')
            
            if not all([project_id, table_name, operation]):
                logger.warning(f"Invalid notification payload: {payload}")
                return
            
            message = {
                "type": f"table_{operation.lower()}",
                "table_name": table_name,
                "data": row_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.broadcast_table_update(project_id, table_name, message)
            
        except Exception as e:
            logger.error(f"Error handling PostgreSQL notification: {e}")
    
    def get_connection_stats(self) -> dict:
        """Get statistics about active connections"""
        total_connections = 0
        project_stats = {}
        
        for project_id, tables in self.connections.items():
            table_stats = {}
            project_total = 0
            
            for table_name, connections in tables.items():
                count = len(connections)
                table_stats[table_name] = count
                project_total += count
            
            project_stats[project_id] = {
                "total": project_total,
                "tables": table_stats
            }
            total_connections += project_total
        
        return {
            "total_connections": total_connections,
            "projects": project_stats
        }

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

# Utility function to notify table changes
async def notify_table_change(project_id: int, table_name: str, operation: str, data: dict):
    """
    Utility function to notify about table changes.
    This can be called from table row operations.
    """
    message = {
        "type": f"table_{operation.lower()}",
        "table_name": table_name,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await websocket_manager.broadcast_table_update(project_id, table_name, message)

# Database trigger function (to be created in project databases)
CREATE_NOTIFY_TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION notify_table_changes() RETURNS trigger AS $$
DECLARE
    payload json;
BEGIN
    -- Create notification payload
    IF TG_OP = 'DELETE' THEN
        payload = json_build_object(
            'project_id', {project_id},
            'table_name', TG_TABLE_NAME,
            'operation', TG_OP,
            'data', row_to_json(OLD)
        );
    ELSE
        payload = json_build_object(
            'project_id', {project_id},
            'table_name', TG_TABLE_NAME,
            'operation', TG_OP,
            'data', row_to_json(NEW)
        );
    END IF;
    
    -- Send notification
    PERFORM pg_notify('table_changes_{project_id}', payload::text);
    
    RETURN CASE TG_OP
        WHEN 'DELETE' THEN OLD
        ELSE NEW
    END;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for a specific table
CREATE TRIGGER {table_name}_notify_trigger
    AFTER INSERT OR UPDATE OR DELETE ON {table_name}
    FOR EACH ROW EXECUTE FUNCTION notify_table_changes();
"""