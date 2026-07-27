# app/services/seed_data.py

from app.firebase_init import db

def get_crop_stages_seed_data():
    """
    Returns a list of crop stage records for multiple crops.
    You can expand/customize these later as needed.
    """
    data = []

    # ---------- COTTON ----------
    data += [
        {"crop_name": "Cotton", "stage_name": "Sowing & Emergence", "start_day_after_sowing": 0, "end_day_after_sowing": 10},
        {"crop_name": "Cotton", "stage_name": "Seedling", "start_day_after_sowing": 11, "end_day_after_sowing": 25},
        {"crop_name": "Cotton", "stage_name": "Vegetative / Square Formation", "start_day_after_sowing": 26, "end_day_after_sowing": 45},
        {"crop_name": "Cotton", "stage_name": "Flowering", "start_day_after_sowing": 46, "end_day_after_sowing": 80},
        {"crop_name": "Cotton", "stage_name": "Boll Development", "start_day_after_sowing": 81, "end_day_after_sowing": 130},
        {"crop_name": "Cotton", "stage_name": "Boll Opening & Maturity", "start_day_after_sowing": 131, "end_day_after_sowing": 170},
    ]

    # ---------- SOYBEAN ----------
    data += [
        {"crop_name": "Soybean", "stage_name": "Sowing & Emergence", "start_day_after_sowing": 0, "end_day_after_sowing": 7},
        {"crop_name": "Soybean", "stage_name": "Vegetative", "start_day_after_sowing": 8, "end_day_after_sowing": 30},
        {"crop_name": "Soybean", "stage_name": "Flowering", "start_day_after_sowing": 31, "end_day_after_sowing": 50},
        {"crop_name": "Soybean", "stage_name": "Pod Formation", "start_day_after_sowing": 51, "end_day_after_sowing": 75},
        {"crop_name": "Soybean", "stage_name": "Maturity", "start_day_after_sowing": 76, "end_day_after_sowing": 105},
    ]

    # ---------- WHEAT ----------
    data += [
        {"crop_name": "Wheat", "stage_name": "Sowing & Germination", "start_day_after_sowing": 0, "end_day_after_sowing": 10},
        {"crop_name": "Wheat", "stage_name": "Tillering", "start_day_after_sowing": 11, "end_day_after_sowing": 35},
        {"crop_name": "Wheat", "stage_name": "Stem Elongation", "start_day_after_sowing": 36, "end_day_after_sowing": 55},
        {"crop_name": "Wheat", "stage_name": "Heading & Flowering", "start_day_after_sowing": 56, "end_day_after_sowing": 80},
        {"crop_name": "Wheat", "stage_name": "Grain Filling", "start_day_after_sowing": 81, "end_day_after_sowing": 105},
        {"crop_name": "Wheat", "stage_name": "Maturity", "start_day_after_sowing": 106, "end_day_after_sowing": 130},
    ]

    # ---------- RICE / PADDY ----------
    data += [
        {"crop_name": "Rice", "stage_name": "Nursery / Early Establishment", "start_day_after_sowing": 0, "end_day_after_sowing": 20},
        {"crop_name": "Rice", "stage_name": "Tillering", "start_day_after_sowing": 21, "end_day_after_sowing": 45},
        {"crop_name": "Rice", "stage_name": "Panicle Initiation", "start_day_after_sowing": 46, "end_day_after_sowing": 65},
        {"crop_name": "Rice", "stage_name": "Flowering", "start_day_after_sowing": 66, "end_day_after_sowing": 85},
        {"crop_name": "Rice", "stage_name": "Grain Filling", "start_day_after_sowing": 86, "end_day_after_sowing": 110},
        {"crop_name": "Rice", "stage_name": "Maturity", "start_day_after_sowing": 111, "end_day_after_sowing": 135},
    ]

    # ---------- MAIZE ----------
    data += [
        {"crop_name": "Maize", "stage_name": "Emergence", "start_day_after_sowing": 0, "end_day_after_sowing": 7},
        {"crop_name": "Maize", "stage_name": "Vegetative", "start_day_after_sowing": 8, "end_day_after_sowing": 30},
        {"crop_name": "Maize", "stage_name": "Tasseling", "start_day_after_sowing": 31, "end_day_after_sowing": 50},
        {"crop_name": "Maize", "stage_name": "Silking", "start_day_after_sowing": 51, "end_day_after_sowing": 65},
        {"crop_name": "Maize", "stage_name": "Grain Filling", "start_day_after_sowing": 66, "end_day_after_sowing": 95},
        {"crop_name": "Maize", "stage_name": "Maturity", "start_day_after_sowing": 96, "end_day_after_sowing": 120},
    ]

    # ---------- GRAM (CHICKPEA) ----------
    data += [
        {"crop_name": "Gram", "stage_name": "Sowing & Emergence", "start_day_after_sowing": 0, "end_day_after_sowing": 10},
        {"crop_name": "Gram", "stage_name": "Vegetative", "start_day_after_sowing": 11, "end_day_after_sowing": 35},
        {"crop_name": "Gram", "stage_name": "Flowering", "start_day_after_sowing": 36, "end_day_after_sowing": 55},
        {"crop_name": "Gram", "stage_name": "Pod Development", "start_day_after_sowing": 56, "end_day_after_sowing": 80},
        {"crop_name": "Gram", "stage_name": "Maturity", "start_day_after_sowing": 81, "end_day_after_sowing": 110},
    ]

    # ---------- TUR (PIGEON PEA) ----------
    data += [
        {"crop_name": "Tur", "stage_name": "Sowing & Emergence", "start_day_after_sowing": 0, "end_day_after_sowing": 12},
        {"crop_name": "Tur", "stage_name": "Vegetative", "start_day_after_sowing": 13, "end_day_after_sowing": 45},
        {"crop_name": "Tur", "stage_name": "Flowering", "start_day_after_sowing": 46, "end_day_after_sowing": 80},
        {"crop_name": "Tur", "stage_name": "Pod Formation", "start_day_after_sowing": 81, "end_day_after_sowing": 120},
        {"crop_name": "Tur", "stage_name": "Maturity", "start_day_after_sowing": 121, "end_day_after_sowing": 160},
    ]

    return data

def seed_crop_stages(overwrite: bool = False):
    """
    Writes crop stage definitions into Firestore collection `crop_stages`.

    If overwrite = False and collection already has data -> do nothing.
    If overwrite = True -> delete all existing docs and insert fresh.
    """
    col = db.collection("crop_stages")

    # check if already seeded
    existing = list(col.limit(1).stream())
    if existing and not overwrite:
        return {"status": "skipped", "reason": "crop_stages already contains data"}

    # if overwrite == True, clear existing docs
    if overwrite:
        batch = db.batch()
        for doc in col.stream():
            batch.delete(doc.reference)
        batch.commit()

    seed_data = get_crop_stages_seed_data()

    batch = db.batch()
    for item in seed_data:
        doc_ref = col.document()
        batch.set(doc_ref, item)

    batch.commit()

    return {"status": "ok", "inserted": len(seed_data)}
