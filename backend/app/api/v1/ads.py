from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db
from app.models.ad import Ad
from app.schemas.ad import AdRead, AdCreate

router = APIRouter(prefix="/ads", tags=["Ads"])

@router.get("/", response_model=List[AdRead])
def get_ads(x_admin_key: str = Header(None), db: Session = Depends(get_db)):
    """Get ads. Admins see all; public sees only active."""
    print(f"DEBUG: get_ads called. Key: {x_admin_key}")
    query = db.query(Ad)
    if x_admin_key != "batman":
        query = query.filter(Ad.is_active == True)
    results = query.all()
    print(f"DEBUG: Returning {len(results)} ads from DB")
    return results

@router.post("/", response_model=AdRead, status_code=status.HTTP_201_CREATED)
def create_ad(ad: AdCreate, db: Session = Depends(get_db)):
    """Create a new ad."""
    print(f"DEBUG: create_ad called. Title: {ad.title}, URL: {ad.image_url}")
    new_ad = Ad(**ad.dict())
    db.add(new_ad)
    db.commit()
    db.refresh(new_ad)
    print(f"DEBUG: Ad created successfully. ID: {new_ad.id}")
    return new_ad

from fastapi import Header

def admin_required(x_admin_key: str = Header(None)):
    if x_admin_key != "batman": # Simple secret for this demo
        raise HTTPException(status_code=403, detail="Invalid Admin Key")
    return True

@router.delete("/{ad_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ad(ad_id: str, authorized: bool = Depends(admin_required), db: Session = Depends(get_db)):
    """Delete an ad (Admin only)."""
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    
    db.delete(ad)
    db.commit()
    return None

@router.patch("/{ad_id}", response_model=AdRead)
def update_ad(ad_id: str, active: bool, authorized: bool = Depends(admin_required), db: Session = Depends(get_db)):
    """Toggle ad status (Admin only)."""
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    
    ad.is_active = active
    db.commit()
    db.refresh(ad)
    return ad

# Seed initial ads if empty (Helper for demo)
@router.post("/seed", status_code=status.HTTP_201_CREATED)
def seed_ads(db: Session = Depends(get_db)):
    """Seed default Epochly ads if none exist."""
    if db.query(Ad).first():
        return {"message": "Ads already exist"}
    
    ads = [
        {
            "title": "Epochly Pilot",
            "image_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop",
            "target_url": "/register?plan=pilot",
            "duration_seconds": 10
        },
        {
            "title": "Epochly Researcher",
            "image_url": "https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?q=80&w=2574&auto=format&fit=crop",
            "target_url": "/register?plan=researcher",
            "duration_seconds": 10
        },
        {
            "title": "Epochly Lab",
            "image_url": "https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?q=80&w=2535&auto=format&fit=crop",
            "target_url": "/register?plan=lab",
            "duration_seconds": 10
        }
    ]
    
    for ad_data in ads:
        db.add(Ad(**ad_data))
    
    db.commit()
    return {"message": "Seeded 3 ads"}


from fastapi import File, UploadFile
import shutil
import os
import io
from PIL import Image, ImageOps
from app.config import settings

@router.post("/upload")
async def upload_ad_image(file: UploadFile = File(...)):
    """Upload an image/video file for an ad to Firebase Storage."""
    try:
        from app.services.firebase_service import FirebaseService
        firebase = FirebaseService()
        
        # Clean filename
        import uuid
        ext = os.path.splitext(file.filename)[1]
        safe_filename = file.filename.replace(" ", "_").lower()
        if not ext:
             ext = ".jpg" # Default behavior
             
        # Generate unique path: ads/{uuid}_{filename}
        file_uuid = str(uuid.uuid4())[:8]
        destination_path = f"ads/{file_uuid}_{safe_filename}"
        
        content = await file.read()
        
        # Check if video (bypass processing)
        if file.content_type.startswith("video/") or safe_filename.endswith((".mp4", ".mov", ".webm", ".avi")):
            print(f"DEBUG: Uploading Video to Firebase: {destination_path}")
            # Reset file pointer for upload
            file.file.seek(0)
            public_url = firebase.upload_file(file.file, destination_path, content_type=file.content_type)
            return {"url": public_url}

        # Process Image (Optimize before upload)
        # Force .jpg extension for images if not present
        if not ext in [".jpg", ".jpeg", ".png", ".webp"]:
             destination_path += ".jpg"
             
        try:
             image = Image.open(io.BytesIO(content))
             image = ImageOps.exif_transpose(image)
             if image.mode != "RGB":
                 image = image.convert("RGB")
             
             # Optimize size (max 1920px)
             if image.width > 1920 or image.height > 1920:
                 image.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
             
             # Save to buffer
             buffer = io.BytesIO()
             image.save(buffer, "JPEG", quality=85)
             buffer.seek(0)
             
             # Upload to Firebase
             print(f"DEBUG: Uploading Image to Firebase: {destination_path}")
             public_url = firebase.upload_file(buffer, destination_path, content_type="image/jpeg")
             
             return {"url": public_url}
             
        except Exception as img_err:
             print(f"⚠️ Image processing failed, uploading original: {img_err}")
             file.file.seek(0)
             public_url = firebase.upload_file(file.file, destination_path, content_type=file.content_type)
             return {"url": public_url}

    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Firebase upload failed: {str(e)}")
