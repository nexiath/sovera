"""
Project members management router for Sovera.
Handles invitations, role management, and member operations.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path, Query, BackgroundTasks
from sqlmodel import Session, select
import logging
from datetime import datetime, timedelta

from auth.dependencies import get_current_user
from database.session import get_session
from models.user import User
from models.project import Project
from models.project_membership import (
    ProjectMembership, 
    ProjectMembershipCreate, 
    ProjectMembershipUpdate,
    ProjectMembershipResponse,
    ProjectInvitation,
    ProjectRole,
    InvitationStatus
)
from utils.rbac import (
    require_project_owner,
    require_project_viewer,
    get_project_with_membership,
    PermissionManager
)

logger = logging.getLogger(__name__)
router = APIRouter()

class MembersError(Exception):
    """Custom exception for members operations"""
    pass

async def send_invitation_email(
    user_email: str, 
    project_name: str, 
    role: ProjectRole,
    inviter_name: str,
    invitation_id: int,
    message: str = None
):
    """
    Send invitation email to user.
    In production, this would integrate with an email service.
    """
    # TODO: Implement email sending
    logger.info(f"Sending invitation email to {user_email} for project {project_name}")
    logger.info(f"Role: {role}, Inviter: {inviter_name}, ID: {invitation_id}")
    if message:
        logger.info(f"Message: {message}")

@router.post("/projects/{project_id}/members/invite", response_model=ProjectMembershipResponse)
async def invite_user_to_project(
    project_id: int = Path(..., description="Project ID", gt=0),
    invitation: ProjectMembershipCreate = ...,
    background_tasks: BackgroundTasks = ...,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_owner)
):
    """
    Invite a user to join a project with a specific role.
    
    Only project owners can invite users.
    If the user doesn't exist, they will be prompted to register.
    """
    try:
        logger.info(f"Inviting user {invitation.user_email} to project {project_id} with role {invitation.role}")
        
        # Check if user exists
        invited_user = session.exec(
            select(User).where(User.email == invitation.user_email)
        ).first()
        
        if not invited_user:
            raise HTTPException(
                status_code=404, 
                detail=f"User with email '{invitation.user_email}' not found. They need to register first."
            )
        
        # Check if user is already a member
        existing_membership = session.exec(
            select(ProjectMembership).where(
                ProjectMembership.user_id == invited_user.id,
                ProjectMembership.project_id == project_id
            )
        ).first()
        
        if existing_membership:
            if existing_membership.status == InvitationStatus.ACCEPTED:
                raise HTTPException(
                    status_code=400, 
                    detail="User is already a member of this project"
                )
            elif existing_membership.status == InvitationStatus.PENDING:
                raise HTTPException(
                    status_code=400, 
                    detail="User already has a pending invitation to this project"
                )
            else:
                # Update existing rejected/expired invitation
                existing_membership.role = invitation.role
                existing_membership.status = InvitationStatus.PENDING
                existing_membership.invited_at = datetime.utcnow()
                existing_membership.invited_by = current_user.id
                membership = existing_membership
        else:
            # Create new membership
            membership = ProjectMembership(
                project_id=project_id,
                user_id=invited_user.id,
                role=invitation.role,
                invited_by=current_user.id,
                status=InvitationStatus.PENDING
            )
            session.add(membership)
        
        session.commit()
        session.refresh(membership)
        
        # Send invitation email
        background_tasks.add_task(
            send_invitation_email,
            invitation.user_email,
            project.name,
            invitation.role,
            current_user.email,
            membership.id,
            invitation.message
        )
        
        logger.info(f"Successfully invited user {invitation.user_email} to project {project_id}")
        
        return ProjectMembershipResponse(
            id=membership.id,
            project_id=project_id,
            project_name=project.name,
            user_id=invited_user.id,
            user_email=invited_user.email,
            role=membership.role,
            status=membership.status,
            invited_at=membership.invited_at,
            accepted_at=membership.accepted_at,
            inviter_email=current_user.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to invite user to project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send invitation")

@router.get("/projects/{project_id}/members", response_model=List[ProjectMembershipResponse])
async def list_project_members(
    project_id: int = Path(..., description="Project ID", gt=0),
    status: InvitationStatus = Query(None, description="Filter by invitation status"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_viewer)
):
    """
    List all members of a project.
    
    All project members can view the member list.
    """
    try:
        logger.info(f"Listing members for project {project_id}")
        
        # Get all memberships for the project
        query = select(ProjectMembership).where(
            ProjectMembership.project_id == project_id
        )
        
        if status:
            query = query.where(ProjectMembership.status == status)
        
        memberships = session.exec(query).all()
        
        # Build response
        members = []
        
        # Add project owner
        members.append(ProjectMembershipResponse(
            id=0,  # Special ID for owner
            project_id=project_id,
            project_name=project.name,
            user_id=project.owner_id,
            user_email=project.owner.email,
            role=ProjectRole.OWNER,
            status=InvitationStatus.ACCEPTED,
            invited_at=project.created_at,
            accepted_at=project.created_at,
            inviter_email=None
        ))
        
        # Add members
        for membership in memberships:
            inviter_email = None
            if membership.invited_by:
                inviter = session.get(User, membership.invited_by)
                inviter_email = inviter.email if inviter else None
            
            members.append(ProjectMembershipResponse(
                id=membership.id,
                project_id=project_id,
                project_name=project.name,
                user_id=membership.user_id,
                user_email=membership.user.email,
                role=membership.role,
                status=membership.status,
                invited_at=membership.invited_at,
                accepted_at=membership.accepted_at,
                inviter_email=inviter_email
            ))
        
        logger.info(f"Found {len(members)} members for project {project_id}")
        return members
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list members for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list project members")

@router.patch("/projects/{project_id}/members/{membership_id}", response_model=ProjectMembershipResponse)
async def update_project_member(
    project_id: int = Path(..., description="Project ID", gt=0),
    membership_id: int = Path(..., description="Membership ID", gt=0),
    update_data: ProjectMembershipUpdate = ...,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_owner)
):
    """
    Update a project member's role or status.
    
    Only project owners can update memberships.
    """
    try:
        logger.info(f"Updating membership {membership_id} for project {project_id}")
        
        # Get membership
        membership = session.exec(
            select(ProjectMembership).where(
                ProjectMembership.id == membership_id,
                ProjectMembership.project_id == project_id
            )
        ).first()
        
        if not membership:
            raise HTTPException(status_code=404, detail="Membership not found")
        
        # Update fields
        if update_data.role is not None:
            membership.role = update_data.role
        
        if update_data.status is not None:
            membership.status = update_data.status
            if update_data.status == InvitationStatus.ACCEPTED:
                membership.accepted_at = datetime.utcnow()
        
        session.commit()
        session.refresh(membership)
        
        logger.info(f"Successfully updated membership {membership_id}")
        
        return ProjectMembershipResponse(
            id=membership.id,
            project_id=project_id,
            project_name=project.name,
            user_id=membership.user_id,
            user_email=membership.user.email,
            role=membership.role,
            status=membership.status,
            invited_at=membership.invited_at,
            accepted_at=membership.accepted_at,
            inviter_email=current_user.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update membership {membership_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update membership")

@router.delete("/projects/{project_id}/members/{membership_id}")
async def remove_project_member(
    project_id: int = Path(..., description="Project ID", gt=0),
    membership_id: int = Path(..., description="Membership ID", gt=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_owner)
):
    """
    Remove a member from a project.
    
    Only project owners can remove members.
    """
    try:
        logger.info(f"Removing membership {membership_id} from project {project_id}")
        
        # Get membership
        membership = session.exec(
            select(ProjectMembership).where(
                ProjectMembership.id == membership_id,
                ProjectMembership.project_id == project_id
            )
        ).first()
        
        if not membership:
            raise HTTPException(status_code=404, detail="Membership not found")
        
        # Delete membership
        session.delete(membership)
        session.commit()
        
        logger.info(f"Successfully removed membership {membership_id}")
        
        return {"message": "Member removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove membership {membership_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove member")

@router.get("/invitations", response_model=List[ProjectInvitation])
async def list_user_invitations(
    status: InvitationStatus = Query(InvitationStatus.PENDING, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    List all invitations for the current user.
    """
    try:
        logger.info(f"Listing invitations for user {current_user.id}")
        
        # Get user's invitations
        memberships = session.exec(
            select(ProjectMembership).where(
                ProjectMembership.user_id == current_user.id,
                ProjectMembership.status == status
            )
        ).all()
        
        invitations = []
        for membership in memberships:
            inviter = session.get(User, membership.invited_by) if membership.invited_by else None
            
            invitations.append(ProjectInvitation(
                id=membership.id,
                project_id=membership.project_id,
                project_name=membership.project.name,
                project_description=membership.project.description,
                role=membership.role,
                invited_by_name=inviter.email if inviter else None,
                invited_by_email=inviter.email if inviter else None,
                invited_at=membership.invited_at,
                message=None,  # TODO: Add message field to membership
                status=membership.status
            ))
        
        logger.info(f"Found {len(invitations)} invitations for user {current_user.id}")
        return invitations
        
    except Exception as e:
        logger.error(f"Failed to list invitations for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list invitations")

@router.post("/invitations/{invitation_id}/accept")
async def accept_invitation(
    invitation_id: int = Path(..., description="Invitation ID", gt=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Accept a project invitation.
    """
    try:
        logger.info(f"Accepting invitation {invitation_id} for user {current_user.id}")
        
        # Get invitation
        membership = session.exec(
            select(ProjectMembership).where(
                ProjectMembership.id == invitation_id,
                ProjectMembership.user_id == current_user.id,
                ProjectMembership.status == InvitationStatus.PENDING
            )
        ).first()
        
        if not membership:
            raise HTTPException(status_code=404, detail="Invitation not found or already processed")
        
        # Accept invitation
        membership.status = InvitationStatus.ACCEPTED
        membership.accepted_at = datetime.utcnow()
        
        session.commit()
        
        logger.info(f"Successfully accepted invitation {invitation_id}")
        
        return {"message": "Invitation accepted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to accept invitation {invitation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to accept invitation")

@router.post("/invitations/{invitation_id}/reject")
async def reject_invitation(
    invitation_id: int = Path(..., description="Invitation ID", gt=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Reject a project invitation.
    """
    try:
        logger.info(f"Rejecting invitation {invitation_id} for user {current_user.id}")
        
        # Get invitation
        membership = session.exec(
            select(ProjectMembership).where(
                ProjectMembership.id == invitation_id,
                ProjectMembership.user_id == current_user.id,
                ProjectMembership.status == InvitationStatus.PENDING
            )
        ).first()
        
        if not membership:
            raise HTTPException(status_code=404, detail="Invitation not found or already processed")
        
        # Reject invitation
        membership.status = InvitationStatus.REJECTED
        
        session.commit()
        
        logger.info(f"Successfully rejected invitation {invitation_id}")
        
        return {"message": "Invitation rejected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject invitation {invitation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject invitation")

@router.get("/projects/{project_id}/members/me", response_model=Dict[str, Any])
async def get_my_membership(
    project_id: int = Path(..., description="Project ID", gt=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get current user's membership and permissions for a project.
    """
    try:
        # Get user's role using RBAC
        user_role = PermissionManager.get_user_role(current_user.id, project_id, session)
        
        if not user_role:
            raise HTTPException(status_code=403, detail="No access to this project")
        
        # Get effective permissions
        permissions = PermissionManager.get_effective_permissions(user_role)
        
        # Get project info
        project = session.get(Project, project_id)
        
        return {
            "project_id": project_id,
            "project_name": project.name if project else None,
            "role": user_role,
            "permissions": list(permissions),
            "is_owner": user_role == ProjectRole.OWNER
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get membership for user {current_user.id} in project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get membership info")