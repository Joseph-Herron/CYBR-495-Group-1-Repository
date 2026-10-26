import psycopg2
import getpass

try:
    connection = psycopg2.connect(
        host = "127.0.0.1",
        port = 5432,
        database = "satellite_security",
        user = "postgres",
        password = getpass.getpass("Enter your PostgreSQL password: ")

    )

    print("Connected to Satellite_Security Sucessfully!!!")

    cursor = connection.cursor()

    cursor.execute("SELECT COUNT (*) FROM satellite_images;")
    image_count = cursor.fetchone()[0]
    print("Satellite image records:", image_count)

    cursor.execute("SELECT COUNT(*)FROM satellite_metadata;")
    metadata_count = cursor.fetchone()[0]
    print("Satellite metadata records: ", metadata_count)

    cursor.close()
    connection.close()
    print("Database connection closed successfully.")

except psycopg2.Error as error:
    print("Database connection failed:")
    print(error)