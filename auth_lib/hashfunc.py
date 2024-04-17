import hmac
import hashlib
import base64

def encode(username, user_uuid, secret_key):
    combined_string = username + str(user_uuid)
    hashed = hmac.new(secret_key.encode(), combined_string.encode(), hashlib.sha256)
    return base64.b64encode(hashed.digest()).decode()

def is_valid(encoded_string, username, user_uuid, secret_key):
    combined_string = username + str(user_uuid)
    hashed = hmac.new(secret_key.encode(), combined_string.encode(), hashlib.sha256)
    return hmac.compare_digest(base64.b64encode(hashed.digest()).decode(), encoded_string)