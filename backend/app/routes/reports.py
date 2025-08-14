from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from datetime import datetime
from pathlib import Path
from typing import Optional
from bson import ObjectId
from app.db.mongo import get_db
from app.models.reports import ReportCreate, ReportPublic
from app.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])
STORAGE_DIR = Path("storage/images")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload", response_model=dict)
async def upload_image(file: UploadFile = File(...), user = Depends(get_current_user)):
    """
    Upload an image for a waste report.
    
    Returns the image URL that can be used when creating a report.
    Requires authentication.
    """
    # Validate file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    suffix = Path(file.filename).suffix.lower()
    
    if suffix not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {suffix} not allowed. Use: {', '.join(allowed_extensions)}"
        )
    
    # Generate unique filename with user info
    timestamp = int(datetime.utcnow().timestamp())
    user_id = user.get("email", "unknown").split("@")[0]  # Use email prefix
    clean_filename = file.filename.replace(' ', '_').replace('/', '_')
    name = f"{timestamp}_{user_id}_{clean_filename}"
    
    dest = STORAGE_DIR / name
    
    try:
        # Save file
        with dest.open("wb") as f:
            content = await file.read()
            f.write(content)
        
        # Return both filename and URL
        return {
            "filename": name,
            "url": f"/static/images/{name}",
            "size": len(content),
            "uploaded_by": user["email"],
            "uploaded_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

@router.post("/", response_model=ReportPublic)
async def create_report(payload: ReportCreate, db = Depends(get_db), user = Depends(get_current_user)):
    """
    Create a new waste report.
    
    The image_url field should contain a URL from the /upload endpoint.
    """
    doc = payload.model_dump()
    doc.update({
        "status": "new",
        "priority": 0,
        "created_by": user["email"],
    })
    res = await db.reports.insert_one(doc)
    saved = await db.reports.find_one({"_id": res.inserted_id})
    return saved

@router.post("reports/with-image", response_model=ReportPublic)
async def create_report_with_image(
    student_id: str = Form(...),
    waste_type: str = Form(...),
    longitude: float = Form(...),
    latitude: float = Form(...),
    safe: bool = Form(True),
    urban_area: bool = Form(True),
    children_present: bool = Form(False),
    flood_risk: bool = Form(False),
    animals_present: bool = Form(False),
    nearest_institution_id: Optional[str] = Form(None),
    measure_height_cm: Optional[float] = Form(None),
    measure_width_cm: Optional[float] = Form(None),
    feedback: Optional[str] = Form(None),
    collection_method: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Create a waste report with optional image upload in a single request.
    
    This endpoint accepts form data and an optional image file.
    More convenient for mobile apps and frontend forms.
    """
    
    # Handle image upload if provided
    image_url = None
    if file and file.filename:
        # Validate file type
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        suffix = Path(file.filename).suffix.lower()
        
        if suffix not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {suffix} not allowed. Use: {', '.join(allowed_extensions)}"
            )
        
        # Save image
        timestamp = int(datetime.utcnow().timestamp())
        user_id = user.get("email", "unknown").split("@")[0]
        clean_filename = file.filename.replace(' ', '_').replace('/', '_')
        name = f"{timestamp}_{user_id}_{clean_filename}"
        dest = STORAGE_DIR / name
        
        try:
            with dest.open("wb") as f:
                await file.read()  # Read file content
                file.file.seek(0)  # Reset file pointer
                content = await file.read()
                f.write(content)
            image_url = f"/static/images/{name}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")
    
    # Create report document
    doc = {
        "student_id": student_id,
        "waste_type": waste_type,
        "location": {
            "type": "Point",
            "coordinates": [longitude, latitude]
        },
        "safe": safe,
        "urban_area": urban_area,
        "children_present": children_present,
        "flood_risk": flood_risk,
        "animals_present": animals_present,
        "nearest_institution_id": nearest_institution_id,
        "image_url": image_url,
        "measure_height_cm": measure_height_cm,
        "measure_width_cm": measure_width_cm,
        "feedback": feedback,
        "collection_method": collection_method,
        "timestamp": datetime.utcnow(),
        "status": "new",
        "priority": 0,
        "created_by": user["email"]
    }
    
    # Remove None values
    doc = {k: v for k, v in doc.items() if v is not None}
    
    # Insert into database
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

@router.patch("/{report_id}/image", response_model=dict)
async def add_image_to_report(
    report_id: str,
    file: UploadFile = File(...),
    db = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Add or update an image for an existing report.
    
    This allows you to upload an image to a report that was already created.
    """
    
    # Check if report exists and user has permission
    try:
        report = await db.reports.find_one({"_id": ObjectId(report_id)})
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Check if user owns this report or is admin/staff
        if report.get("created_by") != user["email"] and user.get("role") not in ["admin", "staff"]:
            raise HTTPException(status_code=403, detail="Not authorized to modify this report")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid report ID")
    
    # Validate and save image
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    suffix = Path(file.filename).suffix.lower()
    
    if suffix not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {suffix} not allowed. Use: {', '.join(allowed_extensions)}"
        )
    
    # Generate filename
    timestamp = int(datetime.utcnow().timestamp())
    user_id = user.get("email", "unknown").split("@")[0]
    clean_filename = file.filename.replace(' ', '_').replace('/', '_')
    name = f"{timestamp}_{user_id}_{clean_filename}"
    dest = STORAGE_DIR / name
    
    try:
        # Save file
        with dest.open("wb") as f:
            content = await file.read()
            f.write(content)
        
        image_url = f"/static/images/{name}"
        
        # Update report with image URL
        await db.reports.update_one(
            {"_id": ObjectId(report_id)},
            {"$set": {"image_url": image_url, "updated_at": datetime.utcnow()}}
        )
        
        return {
            "message": "Image added to report successfully",
            "report_id": report_id,
            "image_url": image_url,
            "filename": name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

@router.get("/{report_id}", response_model=ReportPublic)
async def get_report(report_id: str, db = Depends(get_db)):
    """
    Get a specific report by ID.
    """
    
    try:
        report = await db.reports.find_one({"_id": ObjectId(report_id)})
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid report ID")

@router.get("/", response_model=list[ReportPublic])
async def list_reports(
    limit: int = 100,
    skip: int = 0,
    waste_type: Optional[str] = None,
    status: Optional[str] = None,
    db = Depends(get_db)
):
    """
    List all reports with optional filtering.
    """
    query = {}
    if waste_type:
        query["waste_type"] = waste_type
    if status:
        query["status"] = status
    
    cursor = db.reports.find(query).skip(skip).limit(limit).sort("timestamp", -1)
    return [d async for d in cursor]