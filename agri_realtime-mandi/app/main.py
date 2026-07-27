from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from firebase_admin import firestore as firestore_admin

from .firebase_init import db
from services.auth import get_current_user
from services.advisory import generate_advisories_for_field
from services.notify import save_fcm_token

from services.seed_data import seed_crop_stages


app = FastAPI(title="Agri Advisory Backend")

def firestore_ts_to_iso(ts):
    if ts is None:
        return None
    return ts.isoformat()

class FarmerProfile(BaseModel):
    uid: str
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class FarmerUpdateIn(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None

class FieldIn(BaseModel):
    name: str
    crop_name: str
    sowing_date: str  # "YYYY-MM-DD"
    lat: float
    lon: float
    area_ha: float

class FCMTokenIn(BaseModel):
    token: str

class AdvisoryOut(BaseModel):
    id: Optional[str] = None
    advisory_date: str
    crop_stage: str
    type: str
    severity: str
    title: str
    message: str

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/me", response_model=FarmerProfile)
async def get_or_create_profile(user=Depends(get_current_user)):
    uid = user["uid"]
    email = user.get("email")
    phone = user.get("phone_number") or user.get("phoneNumber")

    farmer_ref = db.collection("farmers").document(uid)
    doc = farmer_ref.get()

    now = datetime.utcnow()

    if not doc.exists:
        default_data = {
            "name": None,
            "phone": phone,
            "email": email,
            "created_at": now,
            "updated_at": now,
        }
        farmer_ref.set(default_data)
        profile = default_data
    else:
        profile = doc.to_dict() or {}
        if "updated_at" not in profile:
            farmer_ref.update({"updated_at": now})
            profile["updated_at"] = now

    return FarmerProfile(
        uid=uid,
        name=profile.get("name"),
        phone=profile.get("phone"),
        email=profile.get("email"),
        created_at=firestore_ts_to_iso(profile.get("created_at")),
        updated_at=firestore_ts_to_iso(profile.get("updated_at")),
    )

@app.post("/me", response_model=FarmerProfile)
async def update_profile(data: FarmerUpdateIn, user=Depends(get_current_user)):
    uid = user["uid"]
    email = user.get("email")
    phone_from_auth = user.get("phone_number") or user.get("phoneNumber")

    farmer_ref = db.collection("farmers").document(uid)
    doc = farmer_ref.get()
    now = datetime.utcnow()

    if not doc.exists:
        new_data = {
            "name": data.name,
            "phone": data.phone or phone_from_auth,
            "email": email,
            "created_at": now,
            "updated_at": now,
        }
        farmer_ref.set(new_data)
        profile = new_data
    else:
        updates = {"updated_at": now}
        if data.name is not None:
            updates["name"] = data.name
        if data.phone is not None:
            updates["phone"] = data.phone
        farmer_ref.update(updates)
        profile = farmer_ref.get().to_dict() or {}

    return FarmerProfile(
        uid=uid,
        name=profile.get("name"),
        phone=profile.get("phone"),
        email=profile.get("email"),
        created_at=firestore_ts_to_iso(profile.get("created_at")),
        updated_at=firestore_ts_to_iso(profile.get("updated_at")),
    )

@app.post("/fields")
async def create_field(data: FieldIn, user=Depends(get_current_user)):
    uid = user["uid"]
    fields_ref = db.collection("fields")
    now = datetime.utcnow()

    field_doc = fields_ref.document()
    field_doc.set(
        {
            "farmer_uid": uid,
            "name": data.name,
            "crop_name": data.crop_name,
            "sowing_date": data.sowing_date,
            "lat": data.lat,
            "lon": data.lon,
            "area_ha": data.area_ha,
            "created_at": now,
        }
    )

    return {"field_id": field_doc.id}

@app.post("/admin/seed-crop-stages")
async def seed_crop_stages_endpoint(user=Depends(get_current_user)):
    """
    Seed the crop_stages collection with predefined data.
    Call this ONCE after deploying backend.

    Optional: you could restrict this to an admin user by checking user["uid"].
    """
    result = seed_crop_stages(overwrite=False)
    return result


@app.get("/advisories")
async def get_advisories_for_user(user = Depends(get_current_user)):
    uid = user["uid"]

    # 1. Get all fields for this user
    fields_ref = db.collection("fields").where("farmer_uid", "==", uid)
    fields = list(fields_ref.stream())

    if not fields:
        raise HTTPException(status_code=404, detail="No fields found for this user")

    # 2. Use the latest created field
    # (Recommended if user has only one field)
    fields_sorted = sorted(fields, key=lambda x: x.to_dict().get("created_at"), reverse=True)
    field_doc = fields_sorted[0]
    field_id = field_doc.id

    # 3. Generate advisories for this field
    generate_advisories_for_field(field_id)

    # 4. Fetch advisories
    adv_query = (
        db.collection("advisories")
        .where("field_id", "==", field_id)
        .order_by("created_at", direction=firestore_admin.Query.DESCENDING)
        .limit(10)
    )

    advisories = []
    for d in adv_query.stream():
        item = d.to_dict()
        advisories.append({
            "id": d.id,
            "advisory_date": item.get("advisory_date"),
            "crop_stage": item.get("crop_stage"),
            "type": item.get("type"),
            "severity": item.get("severity"),
            "title": item.get("title"),
            "message": item.get("message"),
        })

    return {
        "field_id": field_id,
        "field_name": field_doc.to_dict().get("name"),
        "advisories": advisories
    }


@app.post("/fcm-token")
async def set_fcm_token(data: FCMTokenIn, user=Depends(get_current_user)):
    uid = user["uid"]
    save_fcm_token(uid, data.token)
    return {"status": "ok"}
