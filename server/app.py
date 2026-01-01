from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import tensorflow as tf
from pathlib import Path
from .crypto_utils import decrypt_model
import os
from base64 import b64decode

app = FastAPI()
model = None

class InferRequest(BaseModel):
    data: list  # demo input

@app.on_event("startup")
async def startup_event():
    global model
    enc_path = "/opt/model/medical_model.enc"
    out_path = Path("/dev/shm/medical_model.keras")
    key_b64 = os.environ.get("MODEL_KEY_BASE64")
    if not key_b64:
        raise RuntimeError("MODEL_KEY_BASE64 not set")
    
    decrypt_model(enc_path, out_path, b64decode(key_b64))
    model = tf.keras.models.load_model(out_path)
    print("Model loaded successfully")

@app.post("/infer")
async def infer(req: InferRequest):
    global model
    arr = np.array(req.data, dtype=np.float32).reshape(1, -1)[:1, :224*224*3].reshape(1, 224, 224, 3)
    preds = model(arr)
    return {"prediction": float(preds[0, 0])}
