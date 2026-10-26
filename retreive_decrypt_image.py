
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
        # Retrieve encrypted image and encryption information
        cur.execute("""
            SELECT encrypted_image, encryption_nonce, encrypted_key
            FROM satellite_images
            WHERE image_id = 1
        """)

        row = cur.fetchone()

        if row is None or any(value is None for value in row):
            raise RuntimeError("Encrypted image information is incomplete.")

        encrypted_image, nonce, protected_key = row

        # Ask Vault to decrypt the protected AES key
        result = vault.secrets.transit.decrypt_data(
            name="satellite-images",
            ciphertext=protected_key
        )

        aes_key = base64.b64decode(
            result["data"]["plaintext"]
        )

        # Decrypt the image
        original_image = AESGCM(aes_key).decrypt(
            bytes(nonce),
            bytes(encrypted_image),
            None
        )

        # Save the recovered image separately
        with open("recovered_satellite1.jpg", "wb") as image_file:
            image_file.write(original_image)

        print("Image decrypted successfully!")
        print("Recovered file: recovered_satellite1.jpg")
        print("Recovered bytes:", len(original_image))

finally:
    conn.close()
