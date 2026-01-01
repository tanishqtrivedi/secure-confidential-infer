#!/usr/bin/env bash
set -e

# In real life, here you would:
# 1. Perform Azure Attestation.
# 2. Call Key Vault and get MODEL_KEY_BASE64.
# For assignment demo, we assume MODEL_KEY_BASE64 is passed as env variable.

uvicorn server.app:app --host 0.0.0.0 --port 8443
