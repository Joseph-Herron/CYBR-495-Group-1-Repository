import os
import base64
import getpass

import hvac
import psycopg2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Connect to Vault
client = hvac.Client(
    url=os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200"),
    token=os.environ.get("VAULT_TOKEN")
)

if not client.is_authenticated():
    raise RuntimeError("Vault is not authenticated. Check your Vault login.")

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
        images = cur.fetchall()

    verified = 0

    for image_id, ciphertext, nonce, protected_key in images:
        try:
            # Ask Vault to decrypt the protected AES key
            result = client.secrets.transit.decrypt_data(
                name="satellite-images",
                ciphertext=protected_key
            )
            aes_key = base64.b64decode(result["data"]["plaintext"])

            # Decrypt the image in memory
            plaintext = AESGCM(aes_key).decrypt(
                bytes(nonce),
                bytes(ciphertext),
                None
            )

            print(f"Image {image_id}: PASS ({len(plaintext):,} bytes)")
            verified += 1

        except Exception as error:
            print(f"Image {image_id}: FAIL ({type(error).__name__})")

    print(f"\nVerified: {verified}/{len(images)} images")

finally:
    conn.close()