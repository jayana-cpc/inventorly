from fastapi import FastAPI, File, UploadFile, Form
from db import create_embedding, insert_image_embedding, upload_image, view_db, search_image
from fastapi import FastAPI, Request, Response, HTTPException, Cookie, Depends
from fastapi.responses import RedirectResponse
import requests
import os
from jose import jwt
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Dealing with CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google OAuth2 Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")  
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI_DEV") 
 
# Home Route
@app.get("/")
def home():
    return {"message": "Welcome to Inventorly"}

"""
This route is used to redirect the user to the Google OAuth2 login page.
It is used to get the user's email and password from Google.
The frontend will redirect the user to this route when the user clicks the login button.
"""
@app.get("/login")
def login():
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
        "&prompt=consent"
    )
    return RedirectResponse(google_auth_url)

"""
This route is used to handle the callback from Google OAuth2.
It is used to get the user's email and password from Google.
The frontend will redirect the user to this route when the user is logged in.
"""
@app.get("/auth/callback")
def auth_callback(request: Request, response: Response, code: Optional[str] = None):
    if not code:
        raise HTTPException(status_code=400, detail="Missing code in callback")

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    r = requests.post(token_url, data=data)
    if not r.ok:
        raise HTTPException(status_code=400, detail="Failed to get token from Google")
    tokens = r.json()
    id_token = tokens["id_token"]

    id_info = jwt.get_unverified_claims(id_token)
    user_email = id_info["email"]

    resp = RedirectResponse(url=f"http://localhost:3000/signin/callback?id_token={id_token}")    
    resp.set_cookie(
        key="user_email",
        value=user_email,
        httponly=True,
        secure=False,     
        samesite="lax"   
    )
    return resp

"""
This function is used to get the current user from the cookie.
Converts Cookie => email
"""
def get_current_user(user_email: str = Cookie(None)):
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_email
"""
This route is used to upload an image to the database.
"""
@app.post("/upload")
async def create_upload_file(file: UploadFile = File(...), description: str = Form(...), user_email: str = Depends(get_current_user)):
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    url = upload_image(content, file.filename)
    embedding = create_embedding(content)
    insert_image_embedding(file.filename, url, embedding, description, user_email)
    return {"filename": file.filename, "size_mb": round(size_mb, 2)}

"""
This route is used to query an image to the database.
"""
@app.post("/search")
async def query(file: UploadFile = File(...), user_email: str = Form(...)):
    content = await file.read()
    embedding = create_embedding(content)
    results = search_image(embedding, user_email=user_email)
    print(results)
    return {"results": results}

@app.post("/view")
async def print_db():
    result = view_db()
    return {"message": result}



