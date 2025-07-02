import psycopg2
from psycopg2.errors import UniqueViolation
import os
from fastapi import HTTPException
import io
from dotenv import load_dotenv
from PIL import Image
import boto3
import requests
import torch
from transformers import CLIPProcessor, CLIPModel
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def get_db_connection():
    return psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    port=5432
    )



def insert_image_embedding(image_name, image_url, embedding, description, user_email):
    conn = get_db_connection()
    embedding = embedding.tolist() 
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO image_embeddings (image_name, image_url, embedding, description, user_email) VALUES(%s, %s, %s, %s, %s)
            """, 
            (image_name, image_url, embedding, description, user_email)
        )
        conn.commit()
    except UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=409, detail="Image with this URL already exists.")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        cur.close()
        conn.close()

def create_embedding(image):
    image = Image.open(io.BytesIO(image)).convert("RGB")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch16")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch16")

    inputs = processor(images=image, return_tensors="pt") # type: ignore
    with torch.no_grad():
        outputs = model.get_image_features(pixel_values=inputs["pixel_values"]) # type: ignore
        embedding = outputs[0].cpu().numpy()
    
    return embedding

def upload_image(file_bytes, filename):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_S3_REGION")
    )
    bucket = os.getenv("AWS_S3_BUCKET")
    s3.upload_fileobj(io.BytesIO(file_bytes), bucket, filename)
    url = f"https://{bucket}.s3.{os.getenv('AWS_S3_REGION')}.amazonaws.com/{filename}"
    return url

def search_image(embedding, top_k=1, user_email=None):
    conn = get_db_connection()
    cur = conn.cursor()
    embedding = embedding.tolist()
    try:
        cur.execute(
        """
        SELECT id, image_name, image_url, embedding, description, created_at
        FROM image_embeddings
        WHERE user_email = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
        """,
        (user_email,embedding, top_k)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "filename": row[1],
                "image_url": row[2],
                "created_at": row[4]
            }
            for row in rows
        ]
    finally:
        cur.close()
        conn.close()


def view_db():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
        """
        SELECT * FROM image_embeddings;
        """
        )
        rows = cur.fetchall()
        result = ""
        for row in rows:
            result += f"ID: {row[0]}, Image Name: {row[1]}, Image URL: {row[2]}, Description: {row[4]}, Created At: {row[5]}\n"
        return result
    finally:
        cur.close()
        conn.close()



"""
Created table for immage embeddings

CREATE TABLE IF NOT EXISTS image_embeddings (
    id SERIAL PRIMARY KEY,
    image_name VARCHAR(255) NOT NULL,
    image_url VARCHAR(1000) NOT NULL UNIQUE,
    embedding vector(512),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""