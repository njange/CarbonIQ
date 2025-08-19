from fastapi import APIRouter, Depends
from app.db.mongo import get_db
from app.models.institution import InstitutionCreate, InstitutionPublic
from app.deps import require_role

router = APIRouter(prefix="/institutions", tags=["institutions"])

@router.post("/", response_model=InstitutionPublic)
async def create_institution(payload: InstitutionCreate, db = Depends(get_db), user = Depends(require_role("admin", "staff"))):
    res = await db.institutions.insert_one(payload.model_dump())
    doc = await db.institutions.find_one({"_id": res.inserted_id})
    # Optionally convert _id → str for JSON
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc

@router.get("/", response_model=list[InstitutionPublic])
async def list_institutions(db = Depends(get_db)):
    return [d async for d in db.institutions.find({}).limit(200)]