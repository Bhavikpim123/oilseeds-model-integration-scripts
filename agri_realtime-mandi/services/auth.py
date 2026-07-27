from fastapi import Header, HTTPException
from firebase_admin import auth as fb_auth

async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = authorization.split(" ")[1]

    try:
        decoded = fb_auth.verify_id_token(token)
        return decoded
    except Exception as e:
        print("Token verification failed:", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token")