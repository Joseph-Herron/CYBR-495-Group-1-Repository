
import os
import base64
import hashlib
import hvac
import psycopg2
import getpass

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
        # Read image ID 1 without changing the database
        cur.execute(
            "SELECT encrypted_image FROM satellite_images WHERE image_id = 1"
        )
        row = cur.fetchone()

        if row is None or row[0] is None:
            raise RuntimeError("No image data found for image ID 1.")

        original = bytes(row[0])
        print("Original image bytes:", len(original))

        # Encrypt the image with Vault Transit
        encrypted = vault.secrets.transit.encrypt_data(
            name="satellite-images",
            plaintext=base64.b64encode(original).decode("utf-8")
        )
        ciphertext = encrypted["data"]["ciphertext"]
        print("Vault encryption succeeded!")

        # Decrypt the image
        decrypted = vault.secrets.transit.decrypt_data(
            name="satellite-images",
            ciphertext=ciphertext
        )
        recovered = base64.b64decode(
            decrypted["data"]["plaintext"]
        )

        # Compare original and recovered bytes
        if hashlib.sha256(original).digest() == hashlib.sha256(recovered).digest():
            print("SUCCESS: Original and recovered image match!")
        else:
            print("ERROR: Image bytes do not match.")

finally:
    conn.close()
