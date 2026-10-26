
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

print("Vault connected successfully!")

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
        # Select only images that have not been encrypted
        cur.execute("""
            SELECT image_id, encrypted_image
            FROM satellite_images
            WHERE encryption_nonce IS NULL
               OR encrypted_key IS NULL
            ORDER BY image_id
        """)

        images = cur.fetchall()
        print("Images to encrypt:", len(images))

        for image_id, image_data in images:
            if image_data is None:
                print(f"Skipping image {image_id}: no image data.")
                continue

            original = bytes(image_data)

            # Generate a unique AES-256 key and nonce
            aes_key = AESGCM.generate_key(bit_length=256)
            nonce = os.urandom(12)

            # Encrypt image bytes locally
            encrypted_image = AESGCM(aes_key).encrypt(
                nonce, original, None
            )

            # Protect the AES key using Vault Transit
            result = vault.secrets.transit.encrypt_data(
                name="satellite-images",
                plaintext=base64.b64encode(aes_key).decode("utf-8")
            )
            protected_key = result["data"]["ciphertext"]

            # Update the image and its encryption information
            cur.execute("""
                UPDATE satellite_images
                SET encrypted_image = %s,
                    encryption_nonce = %s,
                    encrypted_key = %s
                WHERE image_id = %s
                  AND (encryption_nonce IS NULL OR encrypted_key IS NULL)
            """, (
                psycopg2.Binary(encrypted_image),
                psycopg2.Binary(nonce),
                protected_key,
                image_id
            ))

            print(f"Encrypted image ID {image_id}")

    conn.commit()
    print("Finished encrypting eligible images.")

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
