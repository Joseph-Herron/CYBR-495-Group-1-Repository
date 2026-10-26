from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

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
print("PASS: Original ciphertext decrypts correctly.")

# Alter one byte in a temporary copy of the ciphertext.
tampered_data = bytearray(encrypted_data)
tampered_data[0] ^= 1

# AES-GCM should reject the altered ciphertext.
try:
    aes.decrypt(nonce, bytes(tampered_data), None)
    print("FAIL: Tampered ciphertext was accepted.")
    raise SystemExit(1)
except Exception as error:
    if error.__class__.__name__ == "InvalidTag":
        print("PASS: Tampered ciphertext was rejected (InvalidTag).")
    else:
        raise

print("SUCCESS: AES-GCM tamper-detection test passed.")
