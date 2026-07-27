from datetime import date, datetime

from app.firebase_init import db
from .notify import send_advisory_notification

def get_days_after_sowing(sowing_date_str: str) -> int:
    sowing_date = datetime.fromisoformat(sowing_date_str).date()
    return (date.today() - sowing_date).days

def get_crop_stage(crop_name: str, sowing_date_str: str) -> str:
    days = get_days_after_sowing(sowing_date_str)

    query = (
        db.collection("crop_stages")
        .where("crop_name", "==", crop_name)
        .where("start_day_after_sowing", "<=", days)
        .where("end_day_after_sowing", ">=", days)
    )

    docs = list(query.stream())
    if not docs:
        return "Unknown"

    data = docs[0].to_dict() or {}
    return data.get("stage_name", "Unknown")

def generate_advisories_for_field(field_id: str):
    field_doc = db.collection("fields").document(field_id).get()
    if not field_doc.exists:
        return []

    field = field_doc.to_dict() or {}
    crop_name = field["crop_name"]
    sowing_date = field["sowing_date"]
    lat = field["lat"]
    lon = field["lon"]
    farmer_uid = field["farmer_uid"]

    crop_stage = get_crop_stage(crop_name, sowing_date)
    today_str = date.today().isoformat()

    weather_query = (
        db.collection("weather_daily")
        .where("lat", "==", lat)
        .where("lon", "==", lon)
        .where("date", "==", today_str)
        .limit(1)
    )

    weather = None
    for doc in weather_query.stream():
        weather = doc.to_dict()
        break

    advisories_to_insert = []

    if not weather:
        advisories_to_insert.append({
            "field_id": field_id,
            "farmer_uid": farmer_uid,
            "advisory_date": today_str,
            "crop_stage": crop_stage,
            "type": "info",
            "severity": "info",
            "title": "No weather data",
            "message": "Weather data is not available for your location today. Please check later.",
        })
    else:
        rain_mm = weather.get("rain_mm", 0)
        humidity = weather.get("humidity", 0)
        temp_max = weather.get("temp_max", 0)

        if rain_mm > 20:
            advisories_to_insert.append({
                "field_id": field_id,
                "farmer_uid": farmer_uid,
                "advisory_date": today_str,
                "crop_stage": crop_stage,
                "type": "weather",
                "severity": "warning",
                "title": "Heavy rainfall expected",
                "message": f"Rainfall of {rain_mm} mm expected. Avoid irrigation and ensure proper drainage.",
            })

        if humidity > 80 and 24 <= temp_max <= 32:
            advisories_to_insert.append({
                "field_id": field_id,
                "farmer_uid": farmer_uid,
                "advisory_date": today_str,
                "crop_stage": crop_stage,
                "type": "disease",
                "severity": "warning",
                "title": "High risk of fungal disease",
                "message": "High humidity and suitable temperature can increase fungal diseases. Inspect your crop and act if symptoms appear.",
            })

        advisories_to_insert.append({
            "field_id": field_id,
            "farmer_uid": farmer_uid,
            "advisory_date": today_str,
            "crop_stage": crop_stage,
            "type": "general",
            "severity": "info",
            "title": f"Stage advisory: {crop_stage}",
            "message": f"Your crop is in {crop_stage} stage. Follow recommended practices for this stage.",
        })

    if not advisories_to_insert:
        return []

    batch = db.batch()
    adv_collection = db.collection("advisories")
    now = datetime.utcnow()

    for adv in advisories_to_insert:
        adv["created_at"] = now
        doc_ref = adv_collection.document()
        batch.set(doc_ref, adv)

    batch.commit()

    for adv in advisories_to_insert:
        if adv.get("severity") in ("warning", "critical"):
            send_advisory_notification(
                farmer_uid,
                adv["title"],
                adv["message"][:100] + "..."
            )

    return advisories_to_insert
