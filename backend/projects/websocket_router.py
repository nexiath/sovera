"""
WebSocket router for real-time table updates in Sovera.
Provides live data synchronization for project tables.
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from sqlmodel import Session
import jwt

from auth.dependencies import get_current_user
from core.config import settings
from database.session import get_session
from models.user import User
from models.project import Project
from utils.rbac import PermissionManager
from utils.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

async def get_user_from_token(token: str, session: Session) -> User:
    """Get user from JWT token for WebSocket authentication"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = session.get(User, int(user_id))
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.websocket("/ws/projects/{project_id}/tables/{table_name}")
async def websocket_table_endpoint(
    websocket: WebSocket,
    project_id: int,
    table_name: str,
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for real-time table updates.
    
    Clients connect to receive live updates when data in a specific table changes.
    Requires authentication and appropriate project permissions.
    
    **Authentication:**
    - Pass JWT token as query parameter: ?token=your_jwt_token
    
    **Permissions:**
    - Requires at least viewer role for the project
    
    **Message Types:**
    - `connection_established`: Sent when connection is successful
    - `table_insert`: New row inserted
    - `table_update`: Existing row updated  
    - `table_delete`: Row deleted
    - `error`: Error message
    
    **Example Usage:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/projects/1/tables/users?token=your_jwt_token');
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log('Received:', message);
    };
    ```
    """
    session = None
    try:
        # Get database session
        from database.session import get_session
        session_gen = get_session()
        session = next(session_gen)
        
        # Authenticate user
        user = await get_user_from_token(token, session)
        
        # Check project access
        project = session.get(Project, project_id)
        if not project:
            await websocket.close(code=4004, reason="Project not found")
            return
        
        # Check if user has access to project
        user_role = PermissionManager.get_user_role(user.id, project_id, session)
        if not user_role:
            await websocket.close(code=4003, reason="Access denied: No access to this project")
            return
        
        # Check if user has permission to read data
        if not PermissionManager.has_permission(user_role, "data:read"):
            await websocket.close(code=4003, reason="Access denied: Missing data:read permission")
            return
        
        # Check if project is ready
        if project.provisioning_status != "completed":
            await websocket.close(code=4000, reason="Project infrastructure not ready")
            return
        
        # Connect to WebSocket manager
        await websocket_manager.connect(websocket, project_id, table_name, user)
        
        try:
            # Keep connection alive and handle messages
            while True:
                # Wait for messages from client (for potential future features like filtering)
                try:
                    message = await websocket.receive_text()
                    # For now, we just log client messages
                    logger.info(f"Received message from client: {message}")
                except WebSocketDisconnect:
                    break
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: user {user.id} from project {project_id} table {table_name}")
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=4000, reason=str(e))
        except:
            pass
    finally:
        # Clean up
        if websocket in websocket_manager.connection_users:
            await websocket_manager.disconnect(websocket)
        
        if session:
            try:
                session.close()
            except:
                pass

@router.get("/ws/stats")
async def get_websocket_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get WebSocket connection statistics.
    
    Returns information about active WebSocket connections,
    useful for monitoring and debugging.
    """
    stats = websocket_manager.get_connection_stats()
    
    return {
        "stats": stats,
        "timestamp": "now"
    }

@router.post("/projects/{project_id}/tables/{table_name}/notify")
async def manual_notify_test(
    project_id: int,
    table_name: str,
    operation: str,
    data: dict,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Manually trigger a table change notification for testing.
    
    This endpoint is useful for testing WebSocket functionality
    without actually modifying data.
    """
    # Check project access
    user_role = PermissionManager.get_user_role(current_user.id, project_id, session)
    if not user_role:
        raise HTTPException(status_code=403, detail="Access denied: No access to this project")
    
    # Check editor permission for manual notifications
    if not PermissionManager.has_permission(user_role, "data:create"):
        raise HTTPException(status_code=403, detail="Access denied: Missing data:create permission")
    
    # Send notification
    from utils.websocket_manager import notify_table_change
    await notify_table_change(project_id, table_name, operation, data)
    
    return {
        "message": "Notification sent",
        "project_id": project_id,
        "table_name": table_name,
        "operation": operation
    }