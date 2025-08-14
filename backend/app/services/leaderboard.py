from datetime import datetime, timedelta
from typing import List, Optional
from app.models.rewards import (
    LeaderboardEntry, LeaderboardResponse, UserStats
)

class LeaderboardService:
    """Service for managing leaderboards and rankings"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_global_leaderboard(self, limit: int = 50, period: str = "all_time") -> List[LeaderboardEntry]:
        """Get global leaderboard across all users"""
        
        # Determine date filter based on period
        date_filter = self._get_date_filter(period)
        
        # Build aggregation pipeline
        pipeline = [
            {"$match": date_filter} if date_filter else {"$match": {}},
            {"$sort": {"total_points": -1, "total_reports": -1}},
            {"$limit": limit}
        ]
        
        cursor = self.db.user_stats.aggregate(pipeline)
        stats_docs = await cursor.to_list(length=None)
        
        # Convert to leaderboard entries with ranks
        leaderboard = []
        for rank, stats_doc in enumerate(stats_docs, 1):
            # Get institution name if available
            institution_name = None
            if stats_doc.get("institution_id"):
                institution = await self.db.institutions.find_one({
                    "_id": stats_doc["institution_id"]
                })
                institution_name = institution.get("name") if institution else None
            
            entry = LeaderboardEntry(
                rank=rank,
                user_email=stats_doc["user_email"],
                full_name=stats_doc["full_name"],
                total_points=stats_doc["total_points"],
                total_reports=stats_doc["total_reports"],
                badges_count=len(stats_doc.get("badges_earned", [])),
                institution_name=institution_name,
                current_streak=stats_doc.get("current_streak", 0)
            )
            leaderboard.append(entry)
        
        return leaderboard
    
    async def get_institution_leaderboard(self, institution_id: str, 
                                        limit: int = 20, period: str = "all_time") -> List[LeaderboardEntry]:
        """Get leaderboard for a specific institution"""
        
        date_filter = self._get_date_filter(period)
        match_condition = {"institution_id": institution_id}
        
        if date_filter:
            match_condition.update(date_filter)
        
        pipeline = [
            {"$match": match_condition},
            {"$sort": {"total_points": -1, "total_reports": -1}},
            {"$limit": limit}
        ]
        
        cursor = self.db.user_stats.aggregate(pipeline)
        stats_docs = await cursor.to_list(length=None)
        
        # Get institution name
        institution = await self.db.institutions.find_one({"_id": institution_id})
        institution_name = institution.get("name") if institution else "Unknown Institution"
        
        # Convert to leaderboard entries
        leaderboard = []
        for rank, stats_doc in enumerate(stats_docs, 1):
            entry = LeaderboardEntry(
                rank=rank,
                user_email=stats_doc["user_email"],
                full_name=stats_doc["full_name"],
                total_points=stats_doc["total_points"],
                total_reports=stats_doc["total_reports"],
                badges_count=len(stats_doc.get("badges_earned", [])),
                institution_name=institution_name,
                current_streak=stats_doc.get("current_streak", 0)
            )
            leaderboard.append(entry)
        
        return leaderboard
    
    async def get_user_rank(self, user_email: str, period: str = "all_time") -> Optional[LeaderboardEntry]:
        """Get a specific user's rank and position"""
        
        # Get user's stats
        user_stats = await self.db.user_stats.find_one({"user_email": user_email})
        if not user_stats:
            return None
        
        # Count users with higher scores
        date_filter = self._get_date_filter(period)
        match_condition = {
            "$or": [
                {"total_points": {"$gt": user_stats["total_points"]}},
                {
                    "total_points": user_stats["total_points"],
                    "total_reports": {"$gt": user_stats["total_reports"]}
                }
            ]
        }
        
        if date_filter:
            match_condition.update(date_filter)
        
        users_ahead = await self.db.user_stats.count_documents(match_condition)
        user_rank = users_ahead + 1
        
        # Get institution name if available
        institution_name = None
        if user_stats.get("institution_id"):
            institution = await self.db.institutions.find_one({
                "_id": user_stats["institution_id"]
            })
            institution_name = institution.get("name") if institution else None
        
        return LeaderboardEntry(
            rank=user_rank,
            user_email=user_stats["user_email"],
            full_name=user_stats["full_name"],
            total_points=user_stats["total_points"],
            total_reports=user_stats["total_reports"],
            badges_count=len(user_stats.get("badges_earned", [])),
            institution_name=institution_name,
            current_streak=user_stats.get("current_streak", 0)
        )
    
    async def get_complete_leaderboard(self, user_email: str, limit: int = 50, 
                                     period: str = "all_time") -> LeaderboardResponse:
        """Get complete leaderboard response including user's position"""
        
        # Get global leaderboard
        global_leaderboard = await self.get_global_leaderboard(limit, period)
        
        # Get user's rank
        user_rank = await self.get_user_rank(user_email, period)
        
        # Get institution leaderboard if user belongs to one
        institution_leaderboard = None
        if user_rank and user_rank.institution_name:
            user_stats = await self.db.user_stats.find_one({"user_email": user_email})
            if user_stats and user_stats.get("institution_id"):
                institution_leaderboard = await self.get_institution_leaderboard(
                    user_stats["institution_id"], 20, period
                )
        
        return LeaderboardResponse(
            global_leaderboard=global_leaderboard,
            institution_leaderboard=institution_leaderboard,
            user_rank=user_rank,
            period=period
        )
    
    async def get_top_performers_by_category(self, category: str, limit: int = 10) -> List[LeaderboardEntry]:
        """Get top performers in specific categories"""
        
        sort_field = {
            "reports": "total_reports",
            "points": "total_points",
            "streak": "longest_streak",
            "badges": "badges_earned"
        }.get(category, "total_points")
        
        if category == "badges":
            # Special handling for badges (count array length)
            pipeline = [
                {"$addFields": {"badges_count": {"$size": {"$ifNull": ["$badges_earned", []]}}}},
                {"$sort": {"badges_count": -1, "total_points": -1}},
                {"$limit": limit}
            ]
        else:
            pipeline = [
                {"$sort": {sort_field: -1, "total_points": -1}},
                {"$limit": limit}
            ]
        
        cursor = self.db.user_stats.aggregate(pipeline)
        stats_docs = await cursor.to_list(length=None)
        
        # Convert to leaderboard entries
        leaderboard = []
        for rank, stats_doc in enumerate(stats_docs, 1):
            # Get institution name if available
            institution_name = None
            if stats_doc.get("institution_id"):
                institution = await self.db.institutions.find_one({
                    "_id": stats_doc["institution_id"]
                })
                institution_name = institution.get("name") if institution else None
            
            entry = LeaderboardEntry(
                rank=rank,
                user_email=stats_doc["user_email"],
                full_name=stats_doc["full_name"],
                total_points=stats_doc["total_points"],
                total_reports=stats_doc["total_reports"],
                badges_count=len(stats_doc.get("badges_earned", [])),
                institution_name=institution_name,
                current_streak=stats_doc.get("current_streak", 0)
            )
            leaderboard.append(entry)
        
        return leaderboard
    
    async def get_institution_rankings(self, limit: int = 20) -> List[dict]:
        """Get rankings of institutions by their members' performance"""
        
        pipeline = [
            {"$match": {"institution_id": {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": "$institution_id",
                "total_members": {"$sum": 1},
                "total_points": {"$sum": "$total_points"},
                "total_reports": {"$sum": "$total_reports"},
                "avg_points_per_member": {"$avg": "$total_points"},
                "top_streak": {"$max": "$longest_streak"}
            }},
            {"$sort": {"total_points": -1}},
            {"$limit": limit}
        ]
        
        cursor = self.db.user_stats.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        # Enrich with institution names
        institution_rankings = []
        for rank, result in enumerate(results, 1):
            institution = await self.db.institutions.find_one({
                "_id": result["_id"]
            })
            
            institution_rankings.append({
                "rank": rank,
                "institution_id": result["_id"],
                "institution_name": institution.get("name") if institution else "Unknown",
                "total_members": result["total_members"],
                "total_points": result["total_points"],
                "total_reports": result["total_reports"],
                "avg_points_per_member": round(result["avg_points_per_member"], 1),
                "top_streak": result["top_streak"]
            })
        
        return institution_rankings
    
    def _get_date_filter(self, period: str) -> Optional[dict]:
        """Get date filter for different time periods"""
        now = datetime.utcnow()
        
        if period == "weekly":
            week_start = now - timedelta(days=7)
            return {"last_report_date": {"$gte": week_start}}
        elif period == "monthly":
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return {"last_report_date": {"$gte": month_start}}
        elif period == "all_time":
            return None  # No filter for all time
        else:
            return None
    
    async def update_all_user_ranks(self):
        """Update rank field for all users (can be run periodically)"""
        
        # Get all users sorted by points and reports
        cursor = self.db.user_stats.find().sort([
            ("total_points", -1),
            ("total_reports", -1)
        ])
        
        users = await cursor.to_list(length=None)
        
        # Update ranks
        for rank, user in enumerate(users, 1):
            await self.db.user_stats.update_one(
                {"_id": user["_id"]},
                {"$set": {"rank": rank}}
            )
    
    async def get_recent_achievements(self, limit: int = 20) -> List[dict]:
        """Get recent badge achievements across all users"""
        
        pipeline = [
            {"$match": {"reward_type": "badge", "badge_type": {"$exists": True}}},
            {"$sort": {"earned_at": -1}},
            {"$limit": limit},
            {"$lookup": {
                "from": "users",
                "localField": "user_email",
                "foreignField": "email",
                "as": "user_info"
            }},
            {"$unwind": "$user_info"},
            {"$project": {
                "user_email": 1,
                "full_name": "$user_info.full_name",
                "badge_type": 1,
                "description": 1,
                "earned_at": 1
            }}
        ]
        
        cursor = self.db.user_rewards.aggregate(pipeline)
        return await cursor.to_list(length=None)
