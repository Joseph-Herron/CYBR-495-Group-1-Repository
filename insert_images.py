
from pathlib import Path
import psycopg2
import getpass

# Location of my 20 satellite images
IMAGE_FOLDER = Path.home() / (
    "Library/Mobile Documents/com~apple~CloudDocs/"
    "SatelliteProject/images"
)

try:
    connection = psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        database="satellite_security",
        user="postgres",
        password=getpass.getpass("PostgreSQL password: ")
    )

    cursor = connection.cursor()

    # Find satellite1.jpg through satellite20.jpg,
    # except satellite3.png
    images = []

    for number in range(1, 21):
        extension = ".png" if number == 3 else ".jpg"
        image_path = IMAGE_FOLDER / f"satellite{number}{extension}"

        if image_path.is_file():
            images.append(image_path)
        else:
            print(f"Missing image: {image_path.name}")

    cursor.execute("SELECT COUNT(*) FROM satellite_images;")
    database_count = cursor.fetchone()[0]

    print(f"\nImage files found: {len(images)}")
    print(f"Database records: {database_count}")

    if len(images) == 20 and database_count == 20:
        print("All 20 image files and database records are ready!")
    else:
        print("Check the missing files or database record count.")

    cursor.close()
    connection.close()

except psycopg2.Error as error:
    print("Database error:")
    print(error)