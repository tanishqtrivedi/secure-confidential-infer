# Secure Model Inference in Encrypted Docker Container (Confidential VM–Ready)

This project implements a secure inference pipeline for a sensitive ML model using **Python**, **TensorFlow**, and **Docker**, designed to be deployable inside a **Confidential VM** (e.g., Azure Confidential VM). The current codebase demonstrates the full encrypted‑model + container flow locally, and documents the intended Confidential VM deployment, which is blocked on an Azure for Students subscription by tenant policy (`RequestDisallowedByAzure`). [web:2][web:20][web:89][web:90]

---

## 1. Overview

- Trains and saves a simple TensorFlow model (simulating a medical imaging model). [web:47][web:48]  
- Encrypts the model artifact before packaging it into a Docker image.  
- Runs a FastAPI/Uvicorn server inside a container that:
  - Decrypts the model **only in RAM**.
  - Exposes a single `/infer` endpoint.
  - Never exposes raw model weights.  
- Includes CLI scripts and commands for an Azure Confidential VM deployment design, with notes on why actual VM creation is blocked on the student subscription. [web:2][web:20][web:89][web:90]

---

## 2. Project Structure


secure-confidential-infer/
├─ Dockerfile
├─ README.md
├─ model/
│  ├─ medical_model.keras      # plaintext Keras model (local only)
│  ├─ medical_model.enc        # encrypted model artifact
│  └─ model.key                # symmetric key (ignored by git)
├─ server/
│  ├─ app.py                   # FastAPI inference server
│  ├─ crypto_utils.py          # Fernet-based decrypt helper
│  └─ entrypoint.sh            # container entrypoint
├─ client/
│  └─ client.py                # simple Python client using requests
└─ scripts/
   ├─ create_model.py          # build & save TensorFlow model
   └─ encrypt_model.py         # encrypt .keras into .enc
Note: model/model.key is not committed to git; it is generated locally and passed to the container via an environment variable.

3. Local Setup and Usage
3.1 Prerequisites

macOS (Apple Silicon or Intel)

Python 3.10+

Docker Desktop

Azure CLI (only needed if you want to run the Azure CLI examples) [web:27][web:31][web:38]

3.2 Create virtual environment and install Python deps

bash
cd ~/secure-confidential-infer

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install tensorflow-macos tensorflow-metal cryptography fastapi uvicorn[standard] requests
TensorFlow on Apple Silicon is installed via tensorflow-macos and tensorflow-metal. [web:47][web:49][web:58]

Verify TensorFlow:

bash
python -c "import tensorflow as tf; print(tf.__version__); print(tf.reduce_sum(tf.random.normal()))"
3.3 Create and encrypt the model

Create Keras model

bash
python scripts/create_model.py
# Output: "Model saved to model/medical_model.keras"
Encrypt the model

bash
python scripts/encrypt_model.py
# Output:
# Encrypted model at model/medical_model.enc
# Symmetric key stored at model/model.key
You should now see:

bash
ls model/
# medical_model.keras  medical_model.enc  model.key
The .enc file is what will go into the container; .key is used only to generate a base64 key for the env var.

4. Dockerized Secure Inference
4.1 Build the Docker image

bash
docker build --no-cache -t confidential-infer:latest .
The image contains:

Python 3.11 slim base

TensorFlow CPU, FastAPI, Uvicorn, cryptography

Encrypted model at /opt/model/medical_model.enc

server/ code to decrypt and run the model

4.2 Export the model key (base64)

bash
source .venv/bin/activate

export MODEL_KEY_BASE64=$(python - << 'EOF'
from base64 import b64encode
from pathlib import Path
key = Path("model/model.key").read_bytes()
print(b64encode(key).decode())
EOF
)

echo "$MODEL_KEY_BASE64" | head -c 20; echo   # sanity check (not empty)
4.3 Run the secure inference container

bash
docker run --rm -p 8443:8443 \
  -e MODEL_KEY_BASE64="$MODEL_KEY_BASE64" \
  confidential-infer:latest
On startup, the container:

Reads MODEL_KEY_BASE64.

Decrypts /opt/model/medical_model.enc to /dev/shm/medical_model.keras using the key.

Loads the Keras model into memory and starts FastAPI on port 8443.

You should see logs similar to:

text
Model decrypted to /dev/shm/medical_model.keras
Model loaded successfully
INFO: Uvicorn running on http://0.0.0.0:8443
The model is never written in plaintext to persistent storage inside the container.

4.4 Call the /infer endpoint

In another terminal:

bash
cd ~/secure-confidential-infer
source .venv/bin/activate
pip install requests
bash
python client/client.py
# or inline test:
python - << 'EOF'
import requests
url = "http://localhost:8443/infer"
data = [[0.0] * (224*224*3)]
resp = requests.post(url, json={"data": data}, timeout=10)
print(resp.status_code, resp.text)
EOF
Expected output:

text
200 {"prediction": 0.5}
This demonstrates a complete encrypted model → container → secure inference loop.

5. Azure Confidential VM Design (Blocked on Azure for Students)
The project is designed to be deployed on an Azure Confidential VM so that model decryption and inference run inside a hardware‑protected TEE. On the current Azure for Students subscription, creation of Container Registry and Confidential VMs is blocked by tenant policy (RequestDisallowedByAzure), so these steps are documented but not executed. [web:89][web:90][web:94][web:119][web:121]

5.1 Intended steps (conceptual)

Resource group

bash
az group create -n secure-conf-rg -l eastus
Confidential VM

bash
az vm create \
  --resource-group secure-conf-rg \
  --name secure-conf-vm \
  --image Ubuntu2204 \
  --size Standard_DC2as_v5 \
  --security-type ConfidentialVM \
  --os-disk-security-encryption-type VMGuestStateOnly \
  --location westeurope \
  --admin-username azureuser \
  --generate-ssh-keys
--security-type ConfidentialVM enables confidential computing. [web:2][web:127]

--os-disk-security-encryption-type VMGuestStateOnly configures OS disk guest‑state encryption with platform‑managed keys. [web:127][web:137]

Inside the VM

Install Docker.

Copy this repository or pull a prebuilt image.

Run the same container with MODEL_KEY_BASE64 provided from a secure key management source (Key Vault + attestation in a real deployment).

Due to subscription policy, the above fails with:

text
(RequestDisallowedByAzure) Resource 'secure-conf-vmVNET' was disallowed by Azure ...
The README keeps these commands to show how this container is designed to fit into a Confidential VM architecture, even though actual VM creation is blocked on this tenant. [web:89][web:90][web:119]

6. Security Model
Model at rest

Stored as medical_model.enc using Fernet symmetric encryption.

Under a real deployment, the data key would be wrapped with a cloud KMS/Key Vault key and released only after successful attestation. [web:1][web:8][web:16][web:19]

Model in use

Decrypted into /dev/shm/medical_model.keras (RAM‑backed filesystem) inside the container.

Kept only in process memory during the container lifetime.

API surface

Single /infer endpoint.

No endpoints for downloading weights or inspecting internal tensors.

Confidential VM (design)

When run inside a Confidential VM, CPU memory is encrypted and isolated from the host/hypervisor, protecting data in use. [web:2][web:20][web:133]

7. How to Run Tests / Demo
For the assignment demo:

Start container:

bash
docker run --rm -p 8443:8443 \
  -e MODEL_KEY_BASE64="$MODEL_KEY_BASE64" \
  confidential-infer:latest
Call /infer from client/client.py.

Capture screenshots of:

docker build success.

docker run logs with decryption + model loaded.

Client 200 response.

Azure CLI errors showing RequestDisallowedByAzure for Confidential VM resources (to demonstrate awareness of real‑world cloud constraints). [web:89][web:90][web:119]

8. Future Work
Replace Fernet demo key with proper key management (Azure Key Vault / AWS KMS) bound to VM/enclave attestation. [web:1][web:8][web:16][web:19]

Add remote attestation endpoint on the server so clients can verify the measurement before sending data.

Port the design to AWS Nitro Enclaves using vsock, S3, and KMS for a second confidential‑computing backend. [web:6][web:9][web:15][web:18]
