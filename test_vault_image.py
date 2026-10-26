
import base64
import os
from pathlib import Path

import hvac

# Connect to the local Vault server
client = hvac.Client(
    url=os.environ["VAULT_ADDR"],
    token=os.environ["VAULT_TOKEN"]
)

if not client.is_authenticated():
    raise RuntimeError("Vault authentication failed.")

# Use a smaller image for the first test
image_path = (
    Path.home()
    / "Library/Mobile Documents/com~apple~CloudDocs"
    / "SatelliteProject/images/satellite2.jpg"
)

# Read the original image
with open(image_path, "rb") as image_file:
    original_bytes = image_file.read()

# Vault Transit expects base64-encoded data
plaintext = base64.b64encode(original_bytes).decode("utf-8")

# Encrypt through Vault
encrypt_result = client.secrets.transit.encrypt_data(
    name="satellite-images",
    plaintext=plaintext
)

ciphertext = encrypt_result["data"]["ciphertext"]
print("Image encrypted successfully through Vault.")

# Decrypt through Vault
decrypt_result = client.secrets.transit.decrypt_data(
    name="satellite-images",
    ciphertext=ciphertext
)

recovered_bytes = base64.b64decode(
    decrypt_result["data"]["plaintext"]
)

# Verify the recovered image is identical
if recovered_bytes == original_bytes:
    print("SUCCESS: Original and decrypted images match!")
else:
    raise RuntimeError("Image verification failed.")
