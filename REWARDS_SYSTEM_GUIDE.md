# CarbonIQ Reward System & Leaderboard

## Overview

The CarbonIQ reward system gamifies waste reporting by awarding points, badges, and maintaining leaderboards to encourage user engagement and data quality. Users earn rewards for various actions and can compete in global and institutional leaderboards.

## Features

### 1. Points System
Users earn points for various activities:
- **Base Report Creation**: 10 points
- **Report with Image**: +5 bonus points
- **Detailed Report**: +3 points (includes measurements and feedback)
- **Daily Streak**: +2 points per consecutive day
- **Weekly Goal**: +25 points (5+ reports in a week)
- **Monthly Goal**: +100 points (20+ reports in a month)
- **Badge Earned**: +50 points

### 2. Badge System
14 different badges available:

#### Reporting Badges
- **First Steps** - Create your first waste report
- **Weekly Warrior** - Create 5 reports in a week
- **Monthly Champion** - Create 20 reports in a month
- **Eco Warrior** - Create 100+ waste reports

#### Quality Badges
- **Photo Master** - Include images in 25 reports
- **Detail Oriented** - Submit 10 detailed reports with measurements
- **Safety First** - Report 50 waste sites marked as safe

#### Community Badges
- **Urban Guardian** - Report 30 urban waste sites
- **Rural Protector** - Report 20 rural waste sites
- **Waste Categorizer** - Report all 7 waste types

#### Special Badges
- **Streak Master** - Maintain a 7-day reporting streak
- **Early Adopter** - Be among the first 100 users
- **Community Leader** - Have the most reports in your institution

### 3. Level System
Users progress through levels based on total points:
- Level 1: 0 points
- Level 2: 100 points
- Level 3: 250 points
- Level 4: 500 points
- Level 5: 1,000 points
- And so on... (15 levels total)

### 4. Leaderboards
Multiple leaderboard views:
- **Global Leaderboard** - All users ranked by points
- **Institution Leaderboard** - Users within same institution
- **Category Leaderboards** - By reports, points, streaks, or badges
- **Institution Rankings** - Institutions ranked by collective performance
- **Time-based Rankings** - Weekly, monthly, or all-time

## API Endpoints

### User Profile & Stats

#### Get User Profile
```
GET /rewards/profile
```
Returns comprehensive user profile including stats, recent rewards, and achievement progress.

#### Get User Statistics
```
GET /rewards/stats
```
Returns detailed statistics with points breakdown by category.

#### Get Reward History
```
GET /rewards/history?limit=50&skip=0&reward_type=points
```
Returns paginated reward history with optional filtering.

### Achievements & Badges

#### Get Achievement Progress
```
GET /rewards/achievements
```
Returns progress towards all unearned badges.

#### Get Badge Information
```
GET /rewards/badges
```
Returns information about all available badges and requirements.

### Leaderboards

#### Complete Leaderboard
```
GET /rewards/leaderboard?period=all_time&limit=50
```
Returns global leaderboard, institution leaderboard (if applicable), and user's rank.

#### Global Leaderboard
```
GET /rewards/leaderboard/global?period=weekly&limit=50
```
Returns global leaderboard across all users.

#### Institution Leaderboard
```
GET /rewards/leaderboard/institution/{institution_id}?period=monthly
```
Returns leaderboard for specific institution.

#### Category Leaderboard
```
GET /rewards/leaderboard/category/reports?limit=20
```
Categories: `reports`, `points`, `streak`, `badges`

#### Institution Rankings
```
GET /rewards/leaderboard/institutions?limit=20
```
Returns institutions ranked by collective performance.

#### My Rank
```
GET /rewards/my-rank?period=all_time
```
Returns current user's rank and position.

### Community Features

#### Recent Achievements
```
GET /rewards/recent-achievements?limit=20
```
Returns recent badge achievements across all users (community feed).

### Utility Endpoints

#### Sync User Stats
```
POST /rewards/sync-stats
```
Manually trigger user stats synchronization.

#### Admin: Recalculate Ranks
```
POST /rewards/admin/recalculate-ranks
```
Admin-only endpoint to recalculate all user ranks.

## Integration with Reports

The reward system automatically processes rewards when reports are created. Each time a user creates a report via:
- `POST /reports/`
- `POST /reports/with-image`

The system:
1. Awards base points for report creation
2. Awards bonus points for images and detailed reports
3. Checks for streak milestones
4. Evaluates badge requirements
5. Updates user statistics
6. Processes weekly/monthly goals

## Database Collections

### user_rewards
Stores individual rewards earned by users:
```json
{
  "_id": ObjectId,
  "user_email": "user@example.com",
  "reward_type": "points|badge",
  "points": 10,
  "badge_type": "first_report",
  "action_type": "report_created",
  "description": "Base points for creating a waste report",
  "earned_at": ISODate,
  "report_id": "report_object_id"
}
```

### user_stats
Aggregated user statistics:
```json
{
  "_id": ObjectId,
  "user_email": "user@example.com",
  "full_name": "John Doe",
  "total_points": 156,
  "total_reports": 12,
  "badges_earned": ["first_report", "weekly_warrior"],
  "current_streak": 3,
  "longest_streak": 5,
  "reports_with_images": 8,
  "reports_by_waste_type": {"organic": 5, "plastic": 4, "mixed": 3},
  "last_report_date": ISODate,
  "rank": 45,
  "institution_id": "institution_object_id"
}
```

## Testing the Reward System

### 1. Create Reports and Check Rewards
```bash
# Create a report
curl -X POST "http://localhost:8000/reports/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "12345",
    "waste_type": "organic",
    "location": {"type": "Point", "coordinates": [-1.286389, 36.817223]},
    "safe": true,
    "urban_area": true
  }'

# Check your profile
curl -X GET "http://localhost:8000/rewards/profile" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. View Leaderboard
```bash
# Get global leaderboard
curl -X GET "http://localhost:8000/rewards/leaderboard/global" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get your rank
curl -X GET "http://localhost:8000/rewards/my-rank" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Check Achievement Progress
```bash
# See progress towards badges
curl -X GET "http://localhost:8000/rewards/achievements" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Best Practices

### For Frontend Integration
1. **Show Real-time Feedback**: Display earned rewards immediately after report creation
2. **Progress Indicators**: Show progress bars for badge achievements
3. **Leaderboard Updates**: Refresh leaderboards regularly (consider caching)
4. **Achievement Notifications**: Highlight when users earn new badges
5. **Streak Visualization**: Show streak counters and streak risks

### For Gamification
1. **Daily Goals**: Encourage daily reporting for streak maintenance
2. **Weekly Challenges**: Promote weekly goal achievements
3. **Social Features**: Show recent community achievements
4. **Institution Competition**: Highlight institution vs institution competition
5. **Personal Progress**: Show level progression and next level targets

### For Performance
1. **Batch Processing**: Reward calculations run asynchronously
2. **Caching**: Cache leaderboards for better performance
3. **Indexing**: Proper database indexes for fast queries
4. **Periodic Updates**: Run rank recalculation periodically

## Future Enhancements

1. **Seasonal Events**: Special badges and multipliers during campaigns
2. **Team Challenges**: Group challenges between institutions
3. **Referral Rewards**: Points for bringing new users
4. **Quality Metrics**: Rewards based on report accuracy/verification
5. **Environmental Impact**: Track and reward actual environmental impact
6. **Social Sharing**: Integration with social media for achievements
7. **Push Notifications**: Alert users about achievements and leaderboard changes

## Troubleshooting

### Common Issues

1. **Rewards Not Processing**: Check RewardsService logs for errors
2. **Incorrect Stats**: Use `/rewards/sync-stats` to recalculate
3. **Missing Badges**: Verify badge requirements in `BADGE_REQUIREMENTS`
4. **Leaderboard Issues**: Run admin rank recalculation
5. **Performance Issues**: Check database indexes and query optimization

### Error Handling
The reward system is designed to not interfere with core functionality. If reward processing fails, report creation still succeeds, and rewards can be recalculated later.
