from fastapi import HTTPException
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

load_dotenv()

# CONFIG
SF_CLIENT_ID = os.getenv("SF_CLIENT_ID")
SF_CLIENT_SECRET = os.getenv("SF_CLIENT_SECRET")
SF_REDIRECT_URI = "http://localhost:8000/salesforce/auth/callback"
TOKEN_URL = "https://login.salesforce.com/services/oauth2/token"
TOKEN_FILE = "/home/site/wwwroot/salesforce_tokens.json"


# Global variables
access_token = None
instance_url = None
token_expiry = None
refresh_token = None

def load_tokens():
    """Load tokens from file if they exist"""
    global access_token, instance_url, token_expiry, refresh_token
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                tokens = json.load(f)
                access_token = tokens.get('access_token')
                instance_url = tokens.get('instance_url')
                token_expiry = datetime.fromisoformat(tokens.get('token_expiry'))
                refresh_token = tokens.get('refresh_token')
    except Exception as e:
        print(f"Error loading tokens: {e}")

def save_tokens(tokens):
    """Save tokens to file"""
    global access_token, instance_url, token_expiry, refresh_token
    access_token = tokens.get('access_token')
    instance_url = tokens.get('instance_url')
    expires_in = tokens.get('expires_in', 7200)  
    token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)  
    refresh_token = tokens.get('refresh_token', refresh_token) 
    
    with open(TOKEN_FILE, 'w') as f:
        json.dump({
            'access_token': access_token,
            'instance_url': instance_url,
            'token_expiry': token_expiry.isoformat(),
            'refresh_token': refresh_token
        }, f)

def refresh_access_token():
    """Refresh the access token using the refresh token"""
    global refresh_token
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="No refresh token available. Please re-authenticate."
        )
    
    try:
        res = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": SF_CLIENT_ID,
                "client_secret": SF_CLIENT_SECRET
            }
        )
        res.raise_for_status()
        tokens = res.json()
        save_tokens(tokens)
        return tokens
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error refreshing token: {str(e)}"
        )

def check_and_refresh_token():
    """Check if token is expired or about to expire, and refresh if needed"""
    if not access_token or not token_expiry or datetime.now() >= token_expiry:
        refresh_access_token()

# Load tokens when module starts
load_tokens()

def initiate_salesforce_auth():
    return (
        f"https://login.salesforce.com/services/oauth2/authorize"
        f"?response_type=code&client_id={SF_CLIENT_ID}"
        f"&redirect_uri={SF_REDIRECT_URI}"
        f"&prompt=consent"  
    )

def handle_salesforce_callback(code):
    try:
        res = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": SF_CLIENT_ID,
                "client_secret": SF_CLIENT_SECRET,
                "redirect_uri": SF_REDIRECT_URI,
            },
        )
        res.raise_for_status()
        tokens = res.json()
        save_tokens(tokens)
        return tokens
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error exchanging code for token: {str(e)}"
        )

def get_salesforce_leads():
    check_and_refresh_token()
    
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        res = requests.get(
            f"{instance_url}/services/data/v52.0/query?q=SELECT+Id,+FirstName,+LastName,+Company+FROM+Lead",
            headers=headers
        )
        if res.status_code == 401:  
            refresh_access_token()
            headers["Authorization"] = f"Bearer {access_token}"
            res = requests.get(
                f"{instance_url}/services/data/v52.0/query?q=SELECT+Id,+FirstName,+LastName,+Company+FROM+Lead",
                headers=headers
            )
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching Salesforce leads: {str(e)}"
        )

def create_salesforce_lead(payload: dict):
    check_and_refresh_token()
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    try:
        res = requests.post(
            f"{instance_url}/services/data/v52.0/sobjects/Lead/",
            headers=headers,
            json=payload
        )
        if res.status_code == 401:  
            refresh_access_token()
            headers["Authorization"] = f"Bearer {access_token}"
            res = requests.post(
                f"{instance_url}/services/data/v52.0/sobjects/Lead/",
                headers=headers,
                json=payload
            )
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating Salesforce lead: {str(e)}"
        )
