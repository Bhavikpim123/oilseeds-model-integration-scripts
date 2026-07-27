from datetime import datetime
from firebase_admin import messaging

from app.firebase_init import db

def save_fcm_token(uid: str, token: str) -> None:
    doc_ref = db.collection("fcm_tokens").document(uid)
    doc_ref.set(
        {
            "token": token,
            "updated_at": datetime.utcnow(),
        },
        merge=True,
    )

def send_advisory_notification(uid: str, title: str, body: str) -> None:
    doc = db.collection("fcm_tokens").document(uid).get()
    if not doc.exists:
        return

    data = doc.to_dict() or {}
    token = data.get("token")
    if not token:
        return

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=token,
        data={"screen": "advisory"},
    )

    try:
        messaging.send(message)
    except Exception as e:
        print("Error sending FCM notification:", e)
