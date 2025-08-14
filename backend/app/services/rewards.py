from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from bson import ObjectId
from app.models.rewards import (
    UserReward, UserStats, UserStatsPublic, BadgeType, ActionType, RewardType,
    DEFAULT_REWARD_RULES, BADGE_REQUIREMENTS, LEVEL_THRESHOLDS, AchievementProgress
)
from app.db.mongo import get_db

class RewardsService:
    """Service for managing user rewards, points, and achievements"""
    
    def __init__(self, db):
        self.db = db
        self.reward_rules = {rule.action_type: rule for rule in DEFAULT_REWARD_RULES}
    
    async def process_report_rewards(self, report: dict, user_email: str) -> List[UserReward]:
        """Process all rewards for a newly created report"""
        rewards = []
        
        # Base points for creating a report
        base_reward = await self._create_reward(
            user_email=user_email,
            action_type=ActionType.REPORT_CREATED,
            report_id=str(report["_id"])
        )
        rewards.append(base_reward)
        
        # Bonus for image
        if report.get("image_url"):
            image_reward = await self._create_reward(
                user_email=user_email,
                action_type=ActionType.REPORT_WITH_IMAGE,
                report_id=str(report["_id"])
            )
            rewards.append(image_reward)
        
        # Bonus for detailed report (has measurements and feedback)
        if (report.get("measure_height_cm") and 
            report.get("measure_width_cm") and 
            report.get("feedback")):
            detail_reward = await self._create_reward(
                user_email=user_email,
                action_type=ActionType.REPORT_DETAILED,
                report_id=str(report["_id"])
            )
            rewards.append(detail_reward)
        
        # Check for streak rewards
        streak_rewards = await self._process_streak_rewards(user_email)
        rewards.extend(streak_rewards)
        
        # Check for badges
        badge_rewards = await self._check_and_award_badges(user_email)
        rewards.extend(badge_rewards)
        
        # Update user stats
        await self._update_user_stats(user_email, report)
        
        return rewards
    
    async def _create_reward(self, user_email: str, action_type: ActionType, 
                           report_id: Optional[str] = None) -> UserReward:
        """Create and save a reward"""
        rule = self.reward_rules.get(action_type)
        if not rule:
            raise ValueError(f"No rule found for action type: {action_type}")
        
        reward = UserReward(
            user_email=user_email,
            reward_type=RewardType.POINTS,
            points=rule.points,
            action_type=action_type,
            description=rule.description,
            report_id=report_id
        )
        
        # Save to database
        reward_doc = reward.model_dump()
        await self.db.user_rewards.insert_one(reward_doc)
        
        return reward
    
    async def _process_streak_rewards(self, user_email: str) -> List[UserReward]:
        """Check and award streak-based rewards"""
        rewards = []
        stats = await self.get_user_stats(user_email)
        
        if stats.current_streak > 1:  # Don't award on first day
            streak_reward = await self._create_reward(
                user_email=user_email,
                action_type=ActionType.DAILY_STREAK
            )
            rewards.append(streak_reward)
        
        # Check weekly goal (5+ reports in current week)
        week_start = datetime.utcnow() - timedelta(days=7)
        weekly_count = await self.db.reports.count_documents({
            "created_by": user_email,
            "timestamp": {"$gte": week_start}
        })
        
        if weekly_count >= 5:
            # Check if we already awarded this week
            existing_weekly = await self.db.user_rewards.find_one({
                "user_email": user_email,
                "action_type": ActionType.WEEKLY_GOAL,
                "earned_at": {"$gte": week_start}
            })
            
            if not existing_weekly:
                weekly_reward = await self._create_reward(
                    user_email=user_email,
                    action_type=ActionType.WEEKLY_GOAL
                )
                rewards.append(weekly_reward)
        
        # Check monthly goal (20+ reports in current month)
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_count = await self.db.reports.count_documents({
            "created_by": user_email,
            "timestamp": {"$gte": month_start}
        })
        
        if monthly_count >= 20:
            # Check if we already awarded this month
            existing_monthly = await self.db.user_rewards.find_one({
                "user_email": user_email,
                "action_type": ActionType.MONTHLY_GOAL,
                "earned_at": {"$gte": month_start}
            })
            
            if not existing_monthly:
                monthly_reward = await self._create_reward(
                    user_email=user_email,
                    action_type=ActionType.MONTHLY_GOAL
                )
                rewards.append(monthly_reward)
        
        return rewards
    
    async def _check_and_award_badges(self, user_email: str) -> List[UserReward]:
        """Check if user qualifies for any new badges"""
        rewards = []
        stats = await self.get_user_stats(user_email)
        
        # Get already earned badges
        earned_badges = set(stats.badges_earned)
        
        for badge_type, requirements in BADGE_REQUIREMENTS.items():
            if badge_type in earned_badges:
                continue  # Already has this badge
            
            if await self._check_badge_requirement(user_email, badge_type, requirements["requirement"]):
                # Award the badge
                badge_reward = UserReward(
                    user_email=user_email,
                    reward_type=RewardType.BADGE,
                    badge_type=badge_type,
                    action_type=ActionType.BADGE_EARNED,
                    description=f"Earned badge: {requirements['name']}"
                )
                
                # Save badge
                badge_doc = badge_reward.model_dump()
                await self.db.user_rewards.insert_one(badge_doc)
                rewards.append(badge_reward)
                
                # Award bonus points for badge
                points_reward = await self._create_reward(
                    user_email=user_email,
                    action_type=ActionType.BADGE_EARNED
                )
                rewards.append(points_reward)
        
        return rewards
    
    async def _check_badge_requirement(self, user_email: str, badge_type: BadgeType, 
                                     requirement: dict) -> bool:
        """Check if user meets badge requirements"""
        stats = await self.get_user_stats(user_email)
        
        # Check different requirement types
        if "total_reports" in requirement:
            return stats.total_reports >= requirement["total_reports"]
        
        if "reports_with_images" in requirement:
            return stats.reports_with_images >= requirement["reports_with_images"]
        
        if "streak_days" in requirement:
            return stats.longest_streak >= requirement["streak_days"]
        
        if "unique_waste_types" in requirement:
            return len(stats.reports_by_waste_type) >= requirement["unique_waste_types"]
        
        if "weekly_reports" in requirement:
            week_start = datetime.utcnow() - timedelta(days=7)
            weekly_count = await self.db.reports.count_documents({
                "created_by": user_email,
                "timestamp": {"$gte": week_start}
            })
            return weekly_count >= requirement["weekly_reports"]
        
        if "monthly_reports" in requirement:
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_count = await self.db.reports.count_documents({
                "created_by": user_email,
                "timestamp": {"$gte": month_start}
            })
            return monthly_count >= requirement["monthly_reports"]
        
        if "safe_reports" in requirement:
            safe_count = await self.db.reports.count_documents({
                "created_by": user_email,
                "safe": True
            })
            return safe_count >= requirement["safe_reports"]
        
        if "urban_reports" in requirement:
            urban_count = await self.db.reports.count_documents({
                "created_by": user_email,
                "urban_area": True
            })
            return urban_count >= requirement["urban_reports"]
        
        if "rural_reports" in requirement:
            rural_count = await self.db.reports.count_documents({
                "created_by": user_email,
                "urban_area": False
            })
            return rural_count >= requirement["rural_reports"]
        
        if "detailed_reports" in requirement:
            detailed_count = await self.db.reports.count_documents({
                "created_by": user_email,
                "measure_height_cm": {"$exists": True, "$ne": None},
                "measure_width_cm": {"$exists": True, "$ne": None},
                "feedback": {"$exists": True, "$ne": None}
            })
            return detailed_count >= requirement["detailed_reports"]
        
        return False
    
    async def _update_user_stats(self, user_email: str, report: dict):
        """Update user statistics after a new report"""
        # Calculate current streak
        current_streak = await self._calculate_current_streak(user_email)
        
        # Get waste type counts
        waste_type_counts = await self._get_waste_type_counts(user_email)
        
        # Count reports with images
        reports_with_images = await self.db.reports.count_documents({
            "created_by": user_email,
            "image_url": {"$exists": True, "$ne": None}
        })
        
        # Total reports
        total_reports = await self.db.reports.count_documents({
            "created_by": user_email
        })
        
        # Calculate total points
        total_points = await self._calculate_total_points(user_email)
        
        # Get earned badges
        earned_badges = await self._get_earned_badges(user_email)
        
        # Get user info
        user = await self.db.users.find_one({"email": user_email})
        if not user:
            return
        
        # Update or create user stats
        stats_data = {
            "user_email": user_email,
            "full_name": user["full_name"],
            "total_points": total_points,
            "total_reports": total_reports,
            "badges_earned": earned_badges,
            "current_streak": current_streak,
            "longest_streak": max(current_streak, await self._get_longest_streak(user_email)),
            "reports_with_images": reports_with_images,
            "reports_by_waste_type": waste_type_counts,
            "last_report_date": datetime.utcnow(),
            "institution_id": user.get("institution_id")
        }
        
        await self.db.user_stats.update_one(
            {"user_email": user_email},
            {"$set": stats_data},
            upsert=True
        )
    
    async def _calculate_current_streak(self, user_email: str) -> int:
        """Calculate current consecutive days streak"""
        # Get user's reports ordered by date (most recent first)
        cursor = self.db.reports.find(
            {"created_by": user_email},
            {"timestamp": 1}
        ).sort("timestamp", -1)
        
        reports = await cursor.to_list(length=None)
        
        if not reports:
            return 0
        
        # Check if user reported today
        today = datetime.utcnow().date()
        most_recent = reports[0]["timestamp"].date()
        
        if most_recent != today:
            return 0  # Streak broken
        
        # Count consecutive days
        streak = 1
        current_date = today
        
        for report in reports[1:]:
            report_date = report["timestamp"].date()
            expected_date = current_date - timedelta(days=1)
            
            if report_date == expected_date:
                streak += 1
                current_date = expected_date
            elif report_date < expected_date:
                break  # Gap in streak
        
        return streak
    
    async def _get_longest_streak(self, user_email: str) -> int:
        """Get the longest streak ever achieved by user"""
        existing_stats = await self.db.user_stats.find_one({"user_email": user_email})
        return existing_stats.get("longest_streak", 0) if existing_stats else 0
    
    async def _get_waste_type_counts(self, user_email: str) -> dict:
        """Get count of reports by waste type"""
        pipeline = [
            {"$match": {"created_by": user_email}},
            {"$group": {"_id": "$waste_type", "count": {"$sum": 1}}}
        ]
        
        cursor = self.db.reports.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        return {item["_id"]: item["count"] for item in results}
    
    async def _calculate_total_points(self, user_email: str) -> int:
        """Calculate total points earned by user"""
        pipeline = [
            {"$match": {"user_email": user_email, "points": {"$exists": True}}},
            {"$group": {"_id": None, "total": {"$sum": "$points"}}}
        ]
        
        cursor = self.db.user_rewards.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        
        return result[0]["total"] if result else 0
    
    async def _get_earned_badges(self, user_email: str) -> List[BadgeType]:
        """Get list of badges earned by user"""
        cursor = self.db.user_rewards.find({
            "user_email": user_email,
            "reward_type": RewardType.BADGE,
            "badge_type": {"$exists": True}
        })
        
        rewards = await cursor.to_list(length=None)
        return [reward["badge_type"] for reward in rewards]
    
    async def get_user_stats(self, user_email: str) -> UserStats:
        """Get comprehensive user statistics"""
        stats_doc = await self.db.user_stats.find_one({"user_email": user_email})
        
        if not stats_doc:
            # Create initial stats for new user
            user = await self.db.users.find_one({"email": user_email})
            if not user:
                raise ValueError(f"User not found: {user_email}")
            
            initial_stats = UserStats(
                user_email=user_email,
                full_name=user["full_name"],
                institution_id=user.get("institution_id")
            )
            
            # Save initial stats
            await self.db.user_stats.insert_one(initial_stats.model_dump())
            return initial_stats
        
        return UserStats(**stats_doc)
    
    async def get_achievement_progress(self, user_email: str) -> List[AchievementProgress]:
        """Get user's progress towards unearned achievements"""
        stats = await self.get_user_stats(user_email)
        earned_badges = set(stats.badges_earned)
        
        progress_list = []
        
        for badge_type, info in BADGE_REQUIREMENTS.items():
            if badge_type in earned_badges:
                continue  # Already earned
            
            # Calculate progress based on requirement type
            requirement = info["requirement"]
            current_progress = 0
            target = 0
            
            if "total_reports" in requirement:
                target = requirement["total_reports"]
                current_progress = stats.total_reports
            elif "reports_with_images" in requirement:
                target = requirement["reports_with_images"]
                current_progress = stats.reports_with_images
            elif "streak_days" in requirement:
                target = requirement["streak_days"]
                current_progress = stats.longest_streak
            elif "unique_waste_types" in requirement:
                target = requirement["unique_waste_types"]
                current_progress = len(stats.reports_by_waste_type)
            # Add more requirement types as needed
            
            if target > 0:
                progress_percentage = min(100.0, (current_progress / target) * 100)
                
                progress_list.append(AchievementProgress(
                    badge_type=badge_type,
                    name=info["name"],
                    description=info["description"],
                    progress=current_progress,
                    target=target,
                    completed=current_progress >= target,
                    progress_percentage=progress_percentage
                ))
        
        return sorted(progress_list, key=lambda x: x.progress_percentage, reverse=True)
    
    def calculate_user_level(self, total_points: int) -> tuple[int, int]:
        """Calculate user level and points needed for next level"""
        level = 1
        for threshold in LEVEL_THRESHOLDS[1:]:
            if total_points >= threshold:
                level += 1
            else:
                break
        
        next_level_points = LEVEL_THRESHOLDS[level] if level < len(LEVEL_THRESHOLDS) else 0
        
        return level, next_level_points
