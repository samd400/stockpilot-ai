from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User
from app.models.branch import Branch
from app.schemas.branch import BranchCreate, BranchUpdate, BranchResponse
from typing import List

router = APIRouter(prefix="/branches", tags=["Branches"])


@router.post("/", response_model=BranchResponse)
def create_branch(
    branch: BranchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new branch for multi-branch inventory management"""
    new_branch = Branch(
        user_id=current_user.id,
        name=branch.name,
        location=branch.location,
        address=branch.address,
        phone=branch.phone,
        manager_name=branch.manager_name
    )
    db.add(new_branch)
    db.commit()
    db.refresh(new_branch)
    return new_branch


@router.get("/", response_model=List[BranchResponse])
def list_branches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all branches for the current user"""
    branches = db.query(Branch).filter(Branch.user_id == current_user.id).all()
    return branches


@router.get("/{branch_id}", response_model=BranchResponse)
def get_branch(
    branch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific branch"""
    branch = db.query(Branch).filter(
        Branch.id == branch_id,
        Branch.user_id == current_user.id
    ).first()
    
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    return branch


@router.put("/{branch_id}", response_model=BranchResponse)
def update_branch(
    branch_id: str,
    branch_update: BranchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a branch"""
    branch = db.query(Branch).filter(
        Branch.id == branch_id,
        Branch.user_id == current_user.id
    ).first()
    
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    update_data = branch_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(branch, key, value)
    
    db.commit()
    db.refresh(branch)
    return branch


@router.delete("/{branch_id}")
def delete_branch(
    branch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a branch"""
    branch = db.query(Branch).filter(
        Branch.id == branch_id,
        Branch.user_id == current_user.id
    ).first()
    
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    db.delete(branch)
    db.commit()
    
    return {"message": "Branch deleted successfully"}
