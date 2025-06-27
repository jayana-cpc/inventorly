from fastapi import FastAPI, File, UploadFile
from db import create_embedding, insert_image_embedding, upload_image, view_db, close_db, search_image

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello, World!"}

@app.post("/upload")
async def create_upload_file(file: UploadFile = File(...)):
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    url = upload_image(content, file.filename)
    embedding = create_embedding(content)
    insert_image_embedding(file.filename, url, embedding)
    close_db()
    return {"filename": file.filename, "size_mb": round(size_mb, 2)}

@app.post("/search")
async def query(file: UploadFile = File(...)):
    content = await file.read()
    embedding = create_embedding(content)
    results = search_image(embedding)
    print(results)
    close_db()
    return {"results": results}



