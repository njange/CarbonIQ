from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal, List
from datetime import datetime
from enum import Enum
from bson import ObjectId

class RewardType(str, Enum):
    POINTS = "points"
    BADGE = "badge"
    ACHIEVEMENT = "achievement"
    BONUS = "bonus"

class BadgeType(str, Enum):
    # Reporting badges
    FIRST_REPORT = "first_report"
    WEEKLY_REPORTER = "weekly_reporter"
    MONTHLY_REPORTER = "monthly_reporter"
    ECO_WARRIOR = "eco_warrior"  # 100+ reports
    
    # Quality badges
    PHOTO_MASTER = "photo_master"  # Reports with images
    DETAIL_ORIENTED = "detail_oriented"  # Complete reports with all fields
    SAFETY_FIRST = "safety_first"  # Reports in safe areas
    
    # Community badges
    URBAN_GUARDIAN = "urban_guardian"  # Urban area reports
    RURAL_PROTECTOR = "rural_protector"  # Rural area reports
    WASTE_CATEGORIZER = "waste_categorizer"  # Different waste types
    
    # Special badges
    STREAK_MASTER = "streak_master"  # Consecutive days reporting
    EARLY_ADOPTER = "early_adopter"  # First 100 users
    COMMUNITY_LEADER = "community_leader"  # Most reports in institution

class ActionType(str, Enum):
    REPORT_CREATED = "report_created"
    REPORT_WITH_IMAGE = "report_with_image"
    REPORT_DETAILED = "report_detailed"
    DAILY_STREAK = "daily_streak"
    WEEKLY_GOAL = "weekly_goal"
    MONTHLY_GOAL = "monthly_goal"
    BADGE_EARNED = "badge_earned"

class RewardRule(BaseModel):
    """Defines how points are awarded for different actions"""
    action_type: ActionType
    points: int
    description: str
    multiplier_conditions: Optional[dict] = None  # e.g., {"waste_type": "e_waste", "multiplier": 2}

class UserReward(BaseModel):
    """Individual reward earned by a user"""
    user_email: str
    reward_type: RewardType
    points: Optional[int] = None
    badge_type: Optional[BadgeType] = None
    action_type: ActionType
    description: str
    earned_at: datetime = Field(default_factory=datetime.utcnow)
    report_id: Optional[str] = None  # If reward is related to a specific report

class UserRewardPublic(UserReward):
    id: str = Field(alias="_id")

class UserStats(BaseModel):
    """User statistics for leaderboard and profile"""
    user_email: str
    full_name: str
    total_points: int = 0
    total_reports: int = 0
    badges_earned: List[BadgeType] = []
    current_streak: int = 0  # Current consecutive days
    longest_streak: int = 0
    reports_with_images: int = 0
    reports_by_waste_type: dict = {}  # {"organic": 5, "plastic": 3, ...}
    last_report_date: Optional[datetime] = None
    rank: Optional[int] = None
    institution_id: Optional[str] = None

class UserStatsPublic(UserStats):
    id: str = Field(alias="_id")

class LeaderboardEntry(BaseModel):
    """Single entry in leaderboard"""
    rank: int
    user_email: str
    full_name: str
    total_points: int
    total_reports: int
    badges_count: int
    institution_name: Optional[str] = None
    current_streak: int = 0

class LeaderboardResponse(BaseModel):
    """Complete leaderboard response"""
    global_leaderboard: List[LeaderboardEntry]
    institution_leaderboard: Optional[List[LeaderboardEntry]] = None
    user_rank: Optional[LeaderboardEntry] = None
    period: Literal["all_time", "monthly", "weekly"] = "all_time"

class AchievementProgress(BaseModel):
    """Progress towards earning a badge/achievement"""
    badge_type: BadgeType
    name: str
    description: str
    progress: int
    target: int
    completed: bool = False
    progress_percentage: float = 0.0

class UserProfile(BaseModel):
    """Extended user profile with rewards and achievements"""
    user_email: str
    full_name: str
    role: str
    stats: UserStats
    recent_rewards: List[UserRewardPublic] = []
    achievement_progress: List[AchievementProgress] = []
    level: int = 1  # Based on total points
    next_level_points: int = 100

# Default reward rules
DEFAULT_REWARD_RULES = [
    RewardRule(
        action_type=ActionType.REPORT_CREATED,
        points=10,
        description="Base points for creating a waste report"
    ),
    RewardRule(
        action_type=ActionType.REPORT_WITH_IMAGE,
        points=5,
        description="Bonus points for including an image",
        multiplier_conditions={"has_image": True}
    ),
    RewardRule(
        action_type=ActionType.REPORT_DETAILED,
        points=3,
        description="Bonus for complete report with measurements and feedback"
    ),
    RewardRule(
        action_type=ActionType.DAILY_STREAK,
        points=2,
        description="Daily streak bonus (per consecutive day)"
    ),
    RewardRule(
        action_type=ActionType.WEEKLY_GOAL,
        points=25,
        description="Weekly goal achievement (5+ reports)"
    ),
    RewardRule(
        action_type=ActionType.MONTHLY_GOAL,
        points=100,
        description="Monthly goal achievement (20+ reports)"
    ),
    RewardRule(
        action_type=ActionType.BADGE_EARNED,
        points=50,
        description="Bonus points for earning a new badge"
    )
]

# Badge definitions with requirements
BADGE_REQUIREMENTS = {
    BadgeType.FIRST_REPORT: {
        "name": "First Steps",
        "description": "Create your first waste report",
        "requirement": {"total_reports": 1}
    },
    BadgeType.WEEKLY_REPORTER: {
        "name": "Weekly Warrior",
        "description": "Create 5 reports in a week",
        "requirement": {"weekly_reports": 5}
    },
    BadgeType.MONTHLY_REPORTER: {
        "name": "Monthly Champion",
        "description": "Create 20 reports in a month",
        "requirement": {"monthly_reports": 20}
    },
    BadgeType.ECO_WARRIOR: {
        "name": "Eco Warrior",
        "description": "Create 100+ waste reports",
        "requirement": {"total_reports": 100}
    },
    BadgeType.PHOTO_MASTER: {
        "name": "Photo Master",
        "description": "Include images in 25 reports",
        "requirement": {"reports_with_images": 25}
    },
    BadgeType.DETAIL_ORIENTED: {
        "name": "Detail Oriented",
        "description": "Submit 10 detailed reports with measurements",
        "requirement": {"detailed_reports": 10}
    },
    BadgeType.SAFETY_FIRST: {
        "name": "Safety First",
        "description": "Report 50 waste sites marked as safe",
        "requirement": {"safe_reports": 50}
    },
    BadgeType.URBAN_GUARDIAN: {
        "name": "Urban Guardian",
        "description": "Report 30 urban waste sites",
        "requirement": {"urban_reports": 30}
    },
    BadgeType.RURAL_PROTECTOR: {
        "name": "Rural Protector",
        "description": "Report 20 rural waste sites",
        "requirement": {"rural_reports": 20}
    },
    BadgeType.WASTE_CATEGORIZER: {
        "name": "Waste Categorizer",
        "description": "Report all 7 waste types",
        "requirement": {"unique_waste_types": 7}
    },
    BadgeType.STREAK_MASTER: {
        "name": "Streak Master",
        "description": "Maintain a 7-day reporting streak",
        "requirement": {"streak_days": 7}
    },
    BadgeType.EARLY_ADOPTER: {
        "name": "Early Adopter",
        "description": "Be among the first 100 users",
        "requirement": {"user_rank_by_join": 100}
    },
    BadgeType.COMMUNITY_LEADER: {
        "name": "Community Leader",
        "description": "Have the most reports in your institution",
        "requirement": {"institution_rank": 1}
    }
}

# Level system based on total points
LEVEL_THRESHOLDS = [
    0, 100, 250, 500, 1000, 2000, 3500, 5500, 8000, 12000, 17000, 25000, 35000, 50000, 75000
]
