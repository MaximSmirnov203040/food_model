from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.base import get_db
from app.services.recommendation import RecommendationService
from app.schemas.recommendations import RecipeRecommendation
from app.core.security import get_current_user
from app.models.models import User

router = APIRouter()
recommendation_service = RecommendationService()

@router.get("/personalized", response_model=List[RecipeRecommendation])
async def get_personalized_recommendations(
    n_recommendations: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized recipe recommendations for the current user
    """
    try:
        recommendations = recommendation_service.get_recommendations(
            user_id=current_user.id,
            db=db,
            n_recommendations=n_recommendations
        )
        return recommendations
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting recommendations: {str(e)}"
        )

@router.get("/similar/{recipe_id}", response_model=List[RecipeRecommendation])
async def get_similar_recipes(
    recipe_id: int,
    n_recommendations: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get recipes similar to a given recipe
    """
    try:
        recommendations = recommendation_service.content_based_filtering(
            recipe_id=recipe_id,
            db=db
        )
        return recommendations[:n_recommendations]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting similar recipes: {str(e)}"
        )

@router.post("/train")
async def train_recommendation_model(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Train the recommendation model with current data
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    try:
        # Get training data from database
        # This is a placeholder - implement actual data collection
        training_data = []
        
        recommendation_service.train_model(training_data)
        return {"message": "Model trained successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error training model: {str(e)}"
        ) 