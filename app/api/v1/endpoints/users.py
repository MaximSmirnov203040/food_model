from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.base import get_db
from app.core.security import get_current_active_user
from app.models.models import User
from app.schemas.schemas import User, UserUpdate, UserPreferences
import json

router = APIRouter()

@router.get("/me", response_model=User)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user profile
    """
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile
    """
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/me/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user preferences
    """
    return UserPreferences(
        dietary_restrictions=json.loads(current_user.dietary_restrictions or "[]"),
        favorite_cuisines=json.loads(current_user.favorite_cuisines or "[]")
    )

@router.put("/me/preferences", response_model=UserPreferences)
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user preferences
    """
    current_user.dietary_restrictions = json.dumps(preferences.dietary_restrictions)
    current_user.favorite_cuisines = json.dumps(preferences.favorite_cuisines)
    
    db.commit()
    db.refresh(current_user)
    
    return UserPreferences(
        dietary_restrictions=json.loads(current_user.dietary_restrictions),
        favorite_cuisines=json.loads(current_user.favorite_cuisines)
    )

@router.get("/me/favorites", response_model=List[Recipe])
async def get_user_favorites(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's favorite recipes
    """
    favorites = db.query(UserRecipeInteraction).filter(
        UserRecipeInteraction.user_id == current_user.id,
        UserRecipeInteraction.interaction_type == "save"
    ).all()
    
    return [favorite.recipe for favorite in favorites]

@router.post("/me/favorites/{recipe_id}")
async def add_to_favorites(
    recipe_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add recipe to user's favorites
    """
    interaction = UserRecipeInteraction(
        user_id=current_user.id,
        recipe_id=recipe_id,
        interaction_type="save"
    )
    db.add(interaction)
    db.commit()
    return {"message": "Recipe added to favorites"}

@router.delete("/me/favorites/{recipe_id}")
async def remove_from_favorites(
    recipe_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove recipe from user's favorites
    """
    interaction = db.query(UserRecipeInteraction).filter(
        UserRecipeInteraction.user_id == current_user.id,
        UserRecipeInteraction.recipe_id == recipe_id,
        UserRecipeInteraction.interaction_type == "save"
    ).first()
    
    if interaction:
        db.delete(interaction)
        db.commit()
        return {"message": "Recipe removed from favorites"}
    raise HTTPException(
        status_code=404,
        detail="Recipe not found in favorites"
    ) 