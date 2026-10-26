
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

# Find the first satellite image on your Mac
image_path = (
    Path.home()
    / "Library/Mobile Documents/com~apple~CloudDocs/"
      "SatelliteProject/images/satellite1.jpg"
)

try:
    # Read the original image
    with open(image_path, "rb") as image_file:
        original_data = image_file.read()

    # Generate a temporary 256-bit encryption key
    key = AESGCM.generate_key(bit_length=256)
    aes = AESGCM(key)

    # Generate a unique nonce for this encryption
    nonce = os.urandom(12)

    # Encrypt the image
    encrypted_data = aes.encrypt(nonce, original_data, None)

    # Decrypt the image
    decrypted_data = aes.decrypt(nonce, encrypted_data, None)

    print("Original image size:", len(original_data), "bytes")
    print("Encrypted data size:", len(encrypted_data), "bytes")
    print("Original and decrypted images match:", original_data == decrypted_data)

    if original_data == decrypted_data:
        print("SUCCESS: AES-256-GCM encryption and decryption work!")
    else:
        print("ERROR: The decrypted image does not match.")

except FileNotFoundError:
    print("Image file not found:", image_path)

except Exception as error:
    print("Encryption test failed:", error)
