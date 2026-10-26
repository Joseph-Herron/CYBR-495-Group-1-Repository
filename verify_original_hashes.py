import os
import base64
import hashlib
import getpass
from pathlib import Path

import hvac
import psycopg2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Original satellite files
folder = (
    Path.home()
    / "Library/Mobile Documents/com~apple~CloudDocs"
    / "SatelliteProject"
    / "images"
)

# Only satellite1.jpg through satellite20.jpg/png
originals = [
    folder / f"satellite{i}.{ext}"
    for i in range(1, 21)
    for ext in ("jpg", "png")
    if (folder / f"satellite{i}.{ext}").is_file()
]

if not originals:
    raise SystemExit("No numbered satellite image files found.")

# Calculate original file hashes
original_hashes = {}
for path in originals:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    original_hashes.setdefault(digest, []).append(path.name)

# Connect to Vault
client = hvac.Client(
    url=os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200"),
    token=os.environ.get("VAULT_TOKEN")
)

if not client.is_authenticated():
    raise SystemExit("Vault is not authenticated. Check VAULT_TOKEN.")

# Connect to PostgreSQL
password = getpass.getpass("PostgreSQL password: ")
conn = psycopg2.connect(
    dbname="satellite_security",
    host="localhost",
    user="postgres",
    password=password,
    port=5432
)

try:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT image_id, encrypted_image,
                   encryption_nonce, encrypted_key
            FROM satellite_images
            ORDER BY image_id
        """)
        rows = cur.fetchall()

    matches = 0
    mismatches = 0

    print("\nSHA-256 verification results\n")

    for image_id, ciphertext, nonce, protected_key in rows:
        try:
            result = client.secrets.transit.decrypt_data(
                name="satellite-images",
                ciphertext=protected_key
            )
            aes_key = base64.b64decode(result["data"]["plaintext"])

            recovered = AESGCM(aes_key).decrypt(
                bytes(nonce), bytes(ciphertext), None
            )
            recovered_hash = hashlib.sha256(recovered).hexdigest()

            names = original_hashes.get(recovered_hash)

            if names:
                print(f"Image {image_id}: MATCH — {', '.join(names)}")
                matches += 1
            else:
                print(f"Image {image_id}: NO MATCH")
                mismatches += 1

        except Exception as error:
            print(f"Image {image_id}: ERROR — {type(error).__name__}")
            mismatches += 1

    print(f"\nDatabase images checked: {len(rows)}")
    print(f"Exact matches: {matches}")
    print(f"No matches/errors: {mismatches}")
    print(f"Original numbered files found: {len(originals)}")

finally:
    conn.close()