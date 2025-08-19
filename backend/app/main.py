from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.code.config import settings
from app.db.mongo import get_db
from app.routes import auth, reports, institutions, rewards

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://carboniq254.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(institutions.router)
app.include_router(reports.router)
app.include_router(rewards.router)

app.mount("/static/images", StaticFiles(directory="storage/images"), name="images")

@app.on_event("startup")
async def init_indexes():
    db = get_db()
    # users
    await db.users.create_index("email", unique=True)
    # institutions
    await db.institutions.create_index([("location", "2dsphere")])
    # reports
    await db.reports.create_index([("location", "2dsphere")])
    await db.reports.create_index("timestamp")
    await db.reports.create_index("created_by")
    # rewards and leaderboard
    await db.user_rewards.create_index("user_email")
    await db.user_rewards.create_index("earned_at")
    await db.user_rewards.create_index([("user_email", 1), ("action_type", 1)])
    await db.user_stats.create_index("user_email", unique=True)
    await db.user_stats.create_index([("total_points", -1), ("total_reports", -1)])
    await db.user_stats.create_index("institution_id")