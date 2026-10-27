
import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from main import get_connection, get_vault_client


def test_temporary_data_tampering():
    """Test AES-GCM tamper detection using temporary sample data."""

    # Generate a temporary AES-256 key and nonce.
    key = AESGCM.generate_key(bit_length=256)
    aes = AESGCM(key)
    nonce = os.urandom(12)

    # Use sample data rather than a real stored image.
    original_data = b"Temporary satellite image test data"

    # Encrypt the sample.
    encrypted_data = aes.encrypt(nonce, original_data, None)

    # Verify normal decryption works.
    decrypted_data = aes.decrypt(nonce, encrypted_data, None)
    assert decrypted_data == original_data

    print("PASS: Original sample ciphertext decrypts correctly.")

    # Alter one byte in a temporary copy of the ciphertext.
    tampered_data = bytearray(encrypted_data)
    tampered_data[0] ^= 1

    # AES-GCM should reject the altered ciphertext.
    try:
        aes.decrypt(nonce, bytes(tampered_data), None)
    except InvalidTag:
        print("PASS: Tampered sample ciphertext was rejected (InvalidTag).")
    else:
        raise AssertionError("FAIL: Tampered sample ciphertext was accepted.")

    print("PASS: Temporary-data tampering test completed.")


def test_database_image_tampering():
    """Test tamper detection on encrypted image data retrieved from PostgreSQL."""

    image_id = 1

    # Read the stored encrypted image and encryption information.
    # This query does not change the database.
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT encrypted_image, encryption_nonce, encrypted_key
                FROM satellite_images
                WHERE image_id = %s;
                """,
                (image_id,),
            )
            row = cursor.fetchone()

    if row is None:
        raise RuntimeError(f"Image ID {image_id} was not found.")

    encrypted_image, nonce, encrypted_key = row

    if (
        encrypted_image is None
        or nonce is None
        or encrypted_key is None
    ):
        raise RuntimeError(
            f"Image ID {image_id} has incomplete encryption data."
        )

    # Recover the AES key using Vault Transit.
    vault = get_vault_client()

    response = vault.secrets.transit.decrypt_data(
        name="satellite-images",
        ciphertext=encrypted_key,
    )

    aes_key = base64.b64decode(response["data"]["plaintext"])

    # Convert database values to bytes.
    ciphertext = bytes(encrypted_image)
    nonce = bytes(nonce)

    if len(ciphertext) == 0:
        raise RuntimeError(f"Image ID {image_id} has empty ciphertext.")

    aes = AESGCM(aes_key)

    # Verify the original database ciphertext decrypts successfully.
    recovered_data = aes.decrypt(nonce, ciphertext, None)

    print(
        f"PASS: Database image {image_id} decrypts correctly."
    )
    print(f"Recovered image size: {len(recovered_data):,} bytes.")

    # Modify only an in-memory copy of the ciphertext.
    # The database record is never updated.
    tampered_data = bytearray(ciphertext)
    tampered_data[0] ^= 1

    # AES-GCM should reject the modified ciphertext.
    try:
        aes.decrypt(nonce, bytes(tampered_data), None)
    except InvalidTag:
        print(
            f"PASS: Tampering with database image {image_id} "
            "was detected (InvalidTag)."
        )
    else:
        raise AssertionError(
            "FAIL: Tampered database ciphertext was accepted."
        )

    print("PASS: Database contents were not modified.")


if __name__ == "__main__":
    test_temporary_data_tampering()
    test_database_image_tampering()

    print("\nSUCCESS: Both tamper-detection tests passed.")
