
from pathlib import Path
import psycopg2
import getpass

IMAGE_FOLDER = Path.home() / (
    "Library/Mobile Documents/com~apple~CloudDocs/"
    "SatelliteProject/images"
)

def main():
    password = getpass.getpass("PostgreSQL password: ")

    connection = psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        database="satellite_security",
        user="postgres",
        password=password
    )

    try:
        with connection.cursor() as cursor:
            for image_id in range(1, 21):
                extension = ".png" if image_id == 3 else ".jpg"
                image_path = IMAGE_FOLDER / (
                    f"satellite{image_id}{extension}"
                )

                if not image_path.is_file():
                    raise FileNotFoundError(
                        f"Image not found: {image_path}"
                    )

                image_bytes = image_path.read_bytes()

                cursor.execute(
                    """
                    UPDATE satellite_images
                    SET encrypted_image = %s
                    WHERE image_id = %s
                      AND encrypted_image IS NULL;
                    """,
                    (psycopg2.Binary(image_bytes), image_id)
                )

                if cursor.rowcount != 1:
                    raise RuntimeError(
                        f"Image ID {image_id} was not updated. "
                        "It may be missing or already contain data."
                    )

                print(
                    f"Image {image_id} stored: "
                    f"{image_path.name} ({len(image_bytes):,} bytes)"
                )

        connection.commit()
        print("\nAll 20 images were stored successfully!")

    except Exception:
        connection.rollback()
        print("\nOperation failed. Database changes were rolled back.")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
