from fastapi import FastAPI, File, UploadFile, Form
from db import create_embedding, insert_image_embedding, upload_image, view_db, search_image
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import RedirectResponse
import requests
import os
from jose import jwt
app = FastAPI()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")  


@app.get("/")
def home():
    return {"message": "Welcome to Inventorly"}

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

@app.post("/upload")
async def create_upload_file(file: UploadFile = File(...), description: str = Form(...)):
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    url = upload_image(content, file.filename)
    embedding = create_embedding(content)
    insert_image_embedding(file.filename, url, embedding, description)
    return {"filename": file.filename, "size_mb": round(size_mb, 2)}

@app.post("/search")
async def query(file: UploadFile = File(...)):
    content = await file.read()
    embedding = create_embedding(content)
    results = search_image(embedding)
    print(results)
    return {"results": results}

@app.post("/view")
async def print_db():
    result = view_db()
    return {"message": result}



