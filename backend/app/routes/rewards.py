from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional, List
from app.db.mongo import get_db
from app.deps import get_current_user
from app.models.rewards import (
    UserRewardPublic, UserProfile, AchievementProgress, 
    LeaderboardResponse, LeaderboardEntry, BadgeType, BADGE_REQUIREMENTS
)
from app.services.rewards import RewardsService
from app.services.leaderboard import LeaderboardService

router = APIRouter(prefix="/rewards", tags=["rewards"])

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get comprehensive user profile with stats, rewards, and achievements.
    """
    rewards_service = RewardsService(db)
    
    try:
        # Get user stats
        stats = await rewards_service.get_user_stats(user["email"])
        
        # Get recent rewards (last 10)
        cursor = db.user_rewards.find(
            {"user_email": user["email"]}
        ).sort("earned_at", -1).limit(10)
        
        recent_rewards = []
        async for reward_doc in cursor:
            reward_doc["_id"] = str(reward_doc["_id"])  # Convert ObjectId to string
            recent_rewards.append(UserRewardPublic(**reward_doc))
        
        # Get achievement progress
        achievement_progress = await rewards_service.get_achievement_progress(user["email"])
        
        # Calculate user level
        level, next_level_points = rewards_service.calculate_user_level(stats.total_points)
        
        return UserProfile(
            user_email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            stats=stats,
            recent_rewards=recent_rewards,
            achievement_progress=achievement_progress,
            level=level,
            next_level_points=next_level_points
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")

@router.get("/stats", response_model=dict)
async def get_user_stats(
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get detailed user statistics and rewards summary.
    """
    rewards_service = RewardsService(db)
    
    try:
        stats = await rewards_service.get_user_stats(user["email"])
        
        # Get total points by category
        points_pipeline = [
            {"$match": {"user_email": user["email"], "points": {"$exists": True}}},
            {"$group": {
                "_id": "$action_type",
                "total_points": {"$sum": "$points"},
                "count": {"$sum": 1}
            }}
        ]
        
        points_cursor = db.user_rewards.aggregate(points_pipeline)
        points_breakdown = {doc["_id"]: {"points": doc["total_points"], "count": doc["count"]} 
                          async for doc in points_cursor}
        
        # Calculate level info
        level, next_level_points = rewards_service.calculate_user_level(stats.total_points)
        
        return {
            "user_stats": stats,
            "points_breakdown": points_breakdown,
            "level": level,
            "next_level_points": next_level_points,
            "points_to_next_level": max(0, next_level_points - stats.total_points)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user stats: {str(e)}")

@router.get("/history", response_model=List[UserRewardPublic])
async def get_reward_history(
    limit: int = Query(50, le=200),
    skip: int = Query(0, ge=0),
    reward_type: Optional[str] = None,
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get user's reward history with pagination and filtering.
    """
    try:
        query = {"user_email": user["email"]}
        if reward_type:
            query["reward_type"] = reward_type
        
        cursor = db.user_rewards.find(query).sort("earned_at", -1).skip(skip).limit(limit)
        
        rewards = []
        async for reward_doc in cursor:
            reward_doc["id"] = str(reward_doc["_id"])
            rewards.append(UserRewardPublic(**reward_doc))
        
        return rewards
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get reward history: {str(e)}")

@router.get("/achievements", response_model=List[AchievementProgress])
async def get_achievements_progress(
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get user's progress towards all available achievements/badges.
    """
    rewards_service = RewardsService(db)
    
    try:
        return await rewards_service.get_achievement_progress(user["email"])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get achievements: {str(e)}")

@router.get("/badges", response_model=dict)
async def get_badge_information():
    """
    Get information about all available badges and their requirements.
    """
    badge_info = {}
    for badge_type, info in BADGE_REQUIREMENTS.items():
        badge_info[badge_type.value] = {
            "name": info["name"],
            "description": info["description"],
            "requirement": info["requirement"]
        }
    
    return {
        "badges": badge_info,
        "total_badges": len(badge_info)
    }

@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    period: str = Query("all_time", regex="^(all_time|weekly|monthly)$"),
    limit: int = Query(50, le=100),
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get complete leaderboard including global and institution rankings.
    
    Periods: all_time, weekly, monthly
    """
    leaderboard_service = LeaderboardService(db)
    
    try:
        return await leaderboard_service.get_complete_leaderboard(
            user["email"], limit, period
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")

@router.get("/leaderboard/global", response_model=List[LeaderboardEntry])
async def get_global_leaderboard(
    period: str = Query("all_time", regex="^(all_time|weekly|monthly)$"),
    limit: int = Query(50, le=100),
    db = Depends(get_db)
):
    """
    Get global leaderboard across all users.
    """
    leaderboard_service = LeaderboardService(db)
    
    try:
        return await leaderboard_service.get_global_leaderboard(limit, period)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get global leaderboard: {str(e)}")

@router.get("/leaderboard/institution/{institution_id}", response_model=List[LeaderboardEntry])
async def get_institution_leaderboard(
    institution_id: str,
    period: str = Query("all_time", regex="^(all_time|weekly|monthly)$"),
    limit: int = Query(20, le=50),
    db = Depends(get_db)
):
    """
    Get leaderboard for a specific institution.
    """
    leaderboard_service = LeaderboardService(db)
    
    try:
        return await leaderboard_service.get_institution_leaderboard(
            institution_id, limit, period
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get institution leaderboard: {str(e)}")

@router.get("/leaderboard/category/{category}", response_model=List[LeaderboardEntry])
async def get_category_leaderboard(
    category: str = Path(..., regex="^(reports|points|streak|badges)$"),
    limit: int = Query(20, le=50),
    db = Depends(get_db)
):
    """
    Get top performers in specific categories.
    
    Categories: reports, points, streak, badges
    """
    leaderboard_service = LeaderboardService(db)
    
    try:
        return await leaderboard_service.get_top_performers_by_category(category, limit)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get category leaderboard: {str(e)}")

@router.get("/leaderboard/institutions", response_model=List[dict])
async def get_institution_rankings(
    limit: int = Query(20, le=50),
    db = Depends(get_db)
):
    """
    Get rankings of institutions by their members' collective performance.
    """
    leaderboard_service = LeaderboardService(db)
    
    try:
        return await leaderboard_service.get_institution_rankings(limit)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get institution rankings: {str(e)}")

@router.get("/my-rank", response_model=LeaderboardEntry)
async def get_my_rank(
    period: str = Query("all_time", regex="^(all_time|weekly|monthly)$"),
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get current user's rank and position in leaderboard.
    """
    leaderboard_service = LeaderboardService(db)
    
    try:
        rank = await leaderboard_service.get_user_rank(user["email"], period)
        if not rank:
            raise HTTPException(status_code=404, detail="User not found in rankings")
        
        return rank
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user rank: {str(e)}")

@router.get("/recent-achievements", response_model=List[dict])
async def get_recent_achievements(
    limit: int = Query(20, le=50),
    db = Depends(get_db)
):
    """
    Get recent badge achievements across all users (community feed).
    """
    leaderboard_service = LeaderboardService(db)
    
    try:
        return await leaderboard_service.get_recent_achievements(limit)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent achievements: {str(e)}")

@router.post("/sync-stats")
async def sync_user_stats(
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Manually trigger user stats synchronization.
    Useful for updating stats if there are discrepancies.
    """
    rewards_service = RewardsService(db)
    
    try:
        # Recalculate all user stats
        await rewards_service._update_user_stats(user["email"], {})
        
        return {"message": "User stats synchronized successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync stats: {str(e)}")

@router.post("/admin/recalculate-ranks", dependencies=[Depends(get_current_user)])
async def recalculate_all_ranks(
    db = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Admin endpoint to recalculate all user ranks.
    Only admins can access this endpoint.
    """
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    leaderboard_service = LeaderboardService(db)
    
    try:
        await leaderboard_service.update_all_user_ranks()
        return {"message": "All user ranks recalculated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recalculate ranks: {str(e)}")
