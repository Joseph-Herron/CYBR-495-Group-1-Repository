
import os
import base64
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
        # Read the original image
        cur.execute(
            "SELECT encrypted_image FROM satellite_images WHERE image_id = 1"
        )
        row = cur.fetchone()

        if row is None or row[0] is None:
            raise RuntimeError("Image ID 1 has no image data.")

        original = bytes(row[0])

        # Encrypt the image using AES-256-GCM
        aes_key = AESGCM.generate_key(bit_length=256)
        nonce = os.urandom(12)
        encrypted_image = AESGCM(aes_key).encrypt(
            nonce, original, None
        )

        # Protect the AES key using Vault Transit
        result = vault.secrets.transit.encrypt_data(
            name="satellite-images",
            plaintext=base64.b64encode(aes_key).decode("utf-8")
        )
        protected_key = result["data"]["ciphertext"]

        # Store the encrypted image and key information
        cur.execute(
            """
            UPDATE satellite_images
            SET encrypted_image = %s,
                encryption_nonce = %s,
                encrypted_key = %s
            WHERE image_id = 1
            """,
            (psycopg2.Binary(encrypted_image),
             psycopg2.Binary(nonce),
             protected_key)
        )

    conn.commit()
    print("Encrypted image stored in PostgreSQL!")
    print("Vault-protected key stored successfully!")

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
