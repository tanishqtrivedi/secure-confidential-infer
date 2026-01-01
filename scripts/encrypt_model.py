from cryptography.fernet import Fernet
from pathlib import Path

model_path = Path("model/medical_model.keras")
enc_path = Path("model/medical_model.enc")
key_path = Path("model/model.key")

# Generate key and encrypt
key = Fernet.generate_key()
key_path.write_bytes(key)

f = Fernet(key)
enc_path.write_bytes(f.encrypt(model_path.read_bytes()))

print("Encrypted model at", enc_path)
print("Symmetric key stored at", key_path)
