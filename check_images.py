
import psycopg2
import getpass

try:
    connection = psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        database="satellite_security",
        user="postgres",
        password=getpass.getpass("PostgreSQL password: ")
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            image_id,
            product_name,
            encrypted_image IS NULL
        FROM satellite_images
        ORDER BY image_id;
    """)

    records = cursor.fetchall()

    print("\nExisting satellite image records:")
    for record in records:
        image_id, product_name, image_is_empty = record
        print(
            f"ID: {image_id} | "
            f"Image data empty: {image_is_empty} | "
            f"Product: {product_name}"
        )

    print(f"\nTotal records: {len(records)}")

    cursor.close()
    connection.close()

except psycopg2.Error as error:
    print("Database error:")
    print("Image check complete")