
import os
import base64
import hashlib
import getpass
import hvac
import psycopg2

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Connect to Vault
vault = hvac.Client(
    url=os.environ["VAULT_ADDR"],
    token=os.environ["VAULT_TOKEN"]
)

if not vault.is_authenticated():
    raise RuntimeError("Vault authentication failed.")

print("Vault connected!")

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
        # Read image ID 1
        cur.execute(
            "SELECT encrypted_image FROM satellite_images WHERE image_id = 1"
        )
        row = cur.fetchone()

        if row is None or row[0] is None:
            raise RuntimeError("Image ID 1 has no image data.")

        original = bytes(row[0])
        print("Image loaded:", len(original), "bytes")

        # Generate a random AES-256 key and nonce
        aes_key = AESGCM.generate_key(bit_length=256)
        aes = AESGCM(aes_key)
        nonce = os.urandom(12)

        # Encrypt the image locally
        encrypted_image = aes.encrypt(nonce, original, None)

        # Ask Vault to protect the AES key
        result = vault.secrets.transit.encrypt_data(
            name="satellite-images",
            plaintext=base64.b64encode(aes_key).decode("utf-8")
        )
        protected_key = result["data"]["ciphertext"]

        # Unprotect the AES key using Vault
        result = vault.secrets.transit.decrypt_data(
            name="satellite-images",
            ciphertext=protected_key
        )
        recovered_key = base64.b64decode(
            result["data"]["plaintext"]
        )

        # Decrypt the image and verify it
        recovered_image = AESGCM(recovered_key).decrypt(
            nonce, encrypted_image, None
        )

        if hashlib.sha256(original).digest() != hashlib.sha256(
            recovered_image
        ).digest():
            raise RuntimeError("Verification failed.")

        print("AES-GCM encryption succeeded!")
        print("Vault key protection succeeded!")
        print("Image decryption verified!")
        print("Original and recovered image match.")

finally:
    conn.close()
