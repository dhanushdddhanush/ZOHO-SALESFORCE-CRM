import requests
import os
from dotenv import load_dotenv

load_dotenv()

# CONFIG
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REDIRECT_URI = "http://localhost:8000/zoho/auth/callback"
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")

TOKEN_URL = "https://accounts.zoho.in/oauth/v2/token"
API_BASE = "https://www.zohoapis.in/crm/v2"

access_token = None

def initiate_zoho_auth():
    return (
        f"https://accounts.zoho.in/oauth/v2/auth?scope=ZohoCRM.modules.ALL"
        f"&client_id={ZOHO_CLIENT_ID}&response_type=code&access_type=offline"
        f"&redirect_uri={ZOHO_REDIRECT_URI}"
        f"&prompt=consent"
    )

def handle_zoho_callback(code: str):
    global access_token
    res = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": ZOHO_CLIENT_ID,
            "client_secret": ZOHO_CLIENT_SECRET,
            "redirect_uri": ZOHO_REDIRECT_URI,
        },
    )
    data = res.json()
    access_token = data.get("access_token")
    return data

def refresh_access_token():
    global access_token
    res = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": ZOHO_REFRESH_TOKEN,
            "client_id": ZOHO_CLIENT_ID,
            "client_secret": ZOHO_CLIENT_SECRET,
        },
    )
    data = res.json()
    access_token = data.get("access_token")
    return data

def get_zoho_leads():
    global access_token
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    res = requests.get(f"{API_BASE}/Leads", headers=headers)
    if res.status_code == 401:  
        refresh_access_token()
        headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
        res = requests.get(f"{API_BASE}/Leads", headers=headers)
    return res.json()

def create_zoho_lead(payload):
    global access_token
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
    }
    data = {"data": [payload]}
    res = requests.post(f"{API_BASE}/Leads", headers=headers, json=data)
    if res.status_code == 401:
        refresh_access_token()
        headers["Authorization"] = f"Zoho-oauthtoken {access_token}"
        res = requests.post(f"{API_BASE}/Leads", headers=headers, json=data)
    return res.json()
