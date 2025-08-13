from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from datetime import datetime
from pathlib import Path
from app.db.mongo import get_db
from app.models.report import ReportCreate, ReportPublic
from app.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])
STORAGE_DIR = Path("storage/images")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload", response_model=dict)
async def upload_image(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix
    name = f"{int(datetime.utcnow().timestamp())}_{file.filename.replace(' ', '_')}"
    dest = STORAGE_DIR / name
    with dest.open("wb") as f:
        f.write(await file.read())
    return {"url": f"/static/images/{name}"}

@router.post("/", response_model=ReportPublic)
async def create_report(payload: ReportCreate, db = Depends(get_db), user = Depends(get_current_user)):
    doc = payload.model_dump()
    doc.update({
        "status": "new",
        "priority": 0,
        "created_by": user["email"],
    })
    res = await db.reports.insert_one(doc)
    saved = await db.reports.find_one({"_id": res.inserted_id})
    return saved

@router.get("/near", response_model=list[ReportPublic])
async def near_reports(lng: float, lat: float, radius_m: int = 500, db = Depends(get_db)):
    # requires 2dsphere index on reports.location
    cursor = db.reports.find({
        "location": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                "$maxDistance": radius_m
            }
        }
    }).limit(200)
    return [d async for d in cursor]