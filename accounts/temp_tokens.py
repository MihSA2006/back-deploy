import uuid
from datetime import datetime, timedelta

# Stockage temporaire des tokens (en mémoire)
TEMP_TOKENS = {}

def generate_temp_token(user_id):
    token = str(uuid.uuid4())
    expiration = datetime.now() + timedelta(minutes=5)  # expire dans 5 minutes
    TEMP_TOKENS[token] = {"user_id": user_id, "expires_at": expiration}
    return token

def validate_temp_token(token):
    data = TEMP_TOKENS.get(token)
    if not data:
        return None
    if datetime.now() > data["expires_at"]:
        del TEMP_TOKENS[token]
        return None
    return data["user_id"]

def delete_temp_token(token):
    TEMP_TOKENS.pop(token, None)
