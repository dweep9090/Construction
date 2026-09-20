import json
import httpx

url = 'http://localhost:8000/api/projects/1/ai-summary'

from app.auth.security import create_access_token
token = create_access_token({'sub': 'pm@demo.com'})
headers = {'Authorization': f'Bearer {token}'}

try:
    resp = httpx.post(url, headers=headers, timeout=10.0)
    print(resp.status_code)
    print(resp.text)
except Exception as e:
    print(f"Exception: {e}")
