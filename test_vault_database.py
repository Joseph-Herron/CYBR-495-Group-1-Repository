

import os
import getpass
import hvac
import psycopg2

# Connect to Vault
vault = hvac.Client(
    url=os.environ["VAULT_ADDR"],
    token=os.environ["VAULT_TOKEN"]
)

if vault.is_authenticated():
    print("Vault connected successfully!")
else:
    print("Vault authentication failed!")

# Connect to PostgreSQL
password = getpass.getpass("Enter your PostgreSQL password: ")

conn = psycopg2.connect(
    dbname="satellite_security",
    host="localhost",
    user="postgres",
    password=password,
    port=5432
)

print("PostgreSQL connected successfully!")

cur = conn.cursor()

cur.execute("""
    SELECT image_id, product_name
    FROM satellite_images
    WHERE image_id = 1
""")

image = cur.fetchone()
print("Image record:", image)

cur.close()

conn.close()
