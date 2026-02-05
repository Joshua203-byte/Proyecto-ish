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
    query = db.query(Ad)
    if x_admin_key != "batman":
        query = query.filter(Ad.is_active == True)
    return query.all()

@router.post("/", response_model=AdRead, status_code=status.HTTP_201_CREATED)
def create_ad(ad: AdCreate, db: Session = Depends(get_db)):
    """Create a new ad."""
    new_ad = Ad(**ad.dict())
    db.add(new_ad)
    db.commit()
    db.refresh(new_ad)
    db.refresh(new_ad)
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
from app.config import settings

@router.post("/upload")
def upload_ad_image(file: UploadFile = File(...)):
    """Upload an image file for an ad."""
    try:
        # Create uploads dir if not exists (backend/app/uploads)
        upload_dir = os.path.join(os.getcwd(), "app", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Clean filename
        safe_filename = file.filename.replace(" ", "_").lower()
        file_path = os.path.join(upload_dir, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Return full URL
        # Assumption: Backend URL serves /uploads
        # Note: If running via ngrok, this needs to be relative or use the public domain
        # Ideally, we return a relative path and the frontend handles the domain, 
        # or we return the full URL if we know it.
        # For simplicity in this setup:
        file_url = f"/uploads/{safe_filename}"
        
        return {"url": file_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")
