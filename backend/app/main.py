from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.code.config import settings
from app.db.mongo import get_db
from app.routes import auth, reports, institutions

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(institutions.router)
app.include_router(reports.router)

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