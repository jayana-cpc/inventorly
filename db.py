import psycopg2
import os
import io
from dotenv import load_dotenv
from PIL import Image
import requests
import torch
from transformers import CLIPProcessor, CLIPModel
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    port=5432
)

def insert_image_embedding(filename, file_path, embedding):
    embedding = embedding.tolist() 
    cur = conn.cursor()
    cur.execute("INSERT INTO image_embeddings (filename, file_path, embedding) VALUES(%s, %s, %s)", (filename, file_path, embedding))
    conn.commit()
    cur.close()

def create_embedding(image):
    image = Image.open(io.BytesIO(image)).convert("RGB")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch16")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch16")

    inputs = processor(images=image, return_tensors="pt") # type: ignore
    with torch.no_grad():
        outputs = model.get_image_features(pixel_values=inputs["pixel_values"]) # type: ignore
        embedding = outputs[0].cpu().numpy()
    
    return embedding

conn.close()




"""
Created table for immage embeddings

CREATE TABLE IF NOT EXISTS image_embeddings (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    embedding vector(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""