from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
from zoho_service import (
    initiate_zoho_auth, handle_zoho_callback, get_zoho_leads, create_zoho_lead
)
from fastapi.middleware.cors import CORSMiddleware
from salesforce_service import (
    initiate_salesforce_auth, handle_salesforce_callback,
    get_salesforce_leads, create_salesforce_lead
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Existing Zoho routes
@app.get("/zoho/auth/initiate")
def zoho_auth():
    return RedirectResponse(initiate_zoho_auth())

@app.get("/zoho/auth/callback")
def zoho_callback(code: str):
    return handle_zoho_callback(code)

@app.get("/zoho/get-leads")
def get_zoho_leads_route():
    return get_zoho_leads()

@app.post("/zoho/create-lead")
def post_zoho_lead(payload: dict):
    return create_zoho_lead(payload)

# Existing Salesforce routes
@app.get("/salesforce/auth/initiate")
def salesforce_auth():
    return RedirectResponse(initiate_salesforce_auth())

@app.get("/salesforce/auth/callback")
async def salesforce_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is missing in the callback URL")
    return handle_salesforce_callback(code)

@app.get("/salesforce/get-leads")
def sf_get_leads_route():
    return get_salesforce_leads()

@app.post("/salesforce/create-lead")
def sf_create_lead_route(payload: dict):
    return create_salesforce_lead(payload)

# Unified generic routes with `crm` query parameter
@app.get("/crm/auth/initiate")
def crm_auth_initiate(crm: str = Query(..., description="Choose 'zoho' or 'salesforce'")):
    crm = crm.lower()
    if crm == "zoho":
        return RedirectResponse(initiate_zoho_auth())
    elif crm == "salesforce":
        return RedirectResponse(initiate_salesforce_auth())
    else:
        raise HTTPException(status_code=400, detail="Invalid CRM selected")

@app.get("/crm/auth/callback")
async def crm_auth_callback(request: Request, crm: str = Query(..., description="Choose 'zoho' or 'salesforce'")):
    crm = crm.lower()
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is missing in the callback URL")

    if crm == "zoho":
        return handle_zoho_callback(code)
    elif crm == "salesforce":
        return handle_salesforce_callback(code)
    else:
        raise HTTPException(status_code=400, detail="Invalid CRM selected")

@app.get("/crm/get-leads")
def crm_get_leads(crm: str = Query(..., description="Choose 'zoho' or 'salesforce'")):
    crm = crm.lower()
    if crm == "zoho":
        return get_zoho_leads()
    elif crm == "salesforce":
        return get_salesforce_leads()
    else:
        raise HTTPException(status_code=400, detail="Invalid CRM selected")

@app.post("/crm/create-lead")
def crm_create_lead(payload: dict, crm: str = Query(..., description="Choose 'zoho' or 'salesforce'")):
    crm = crm.lower()
    if crm == "zoho":
        return create_zoho_lead(payload)
    elif crm == "salesforce":
        return create_salesforce_lead(payload)
    else:
        raise HTTPException(status_code=400, detail="Invalid CRM selected")
