from fastapi import FastAPI, File, UploadFile
from typing import Optional


app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello, World!"}

@app.post("/upload")
async def create_upload_file(file: UploadFile = File(...)):
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    return {"filename": file.filename, "size_mb": round(size_mb, 2)}