from cryptography.fernet import Fernet
from pathlib import Path
import os

def decrypt_model(enc_path: str, out_path: str, key: bytes):
    enc_path = Path(enc_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    f = Fernet(key)
    decrypted_bytes = f.decrypt(enc_path.read_bytes())
    out_path.write_bytes(decrypted_bytes)

    print(f"Model decrypted to {out_path}")
