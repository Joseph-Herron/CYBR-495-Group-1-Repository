# CYBR-495 Secure Satellite Image Database — Testing Documentation

## 1. Purpose

This document describes the testing procedures used to evaluate the security and functionality of the Secure Satellite Image Database.

Testing focuses on:

- Satellite image encryption and decryption.
- Encryption key protection using HashiCorp Vault Transit.
- Authentication and role-based access control through Keycloak.
- API behavior for authorized and unauthorized requests.
- Detection of modified encrypted image data.
- Security event logging in PostgreSQL.
- Repository secret scanning and handling of local backup files.

## 2. Test Environment

The project uses the following components:

| Component | Purpose |
|---|---|
| Python | Application logic and test scripts |
| FastAPI | Backend API |
| PostgreSQL | Image records, metadata, and access logs |
| HashiCorp Vault Transit | Encryption key protection |
| Keycloak | Authentication and role-based access control |
| AES-GCM | Authenticated image encryption |
| Gitleaks | Secret scanning |

The local API is configured to run at `http://127.0.0.1:8001`. Keycloak is configured for the `satellite_security` realm.

Test commands should be run from the project directory unless otherwise specified.

## 3. Image Encryption and Decryption

### Objective

Verify that satellite images can be encrypted, stored, decrypted, and recovered without changing their original contents.

### Test Scripts

- `test_one_image_encryption.py`
- `verify_all_images.py`
- `verify_original_hashes.py`
- `test_encryption.py`

### Procedure

1. Encrypt the test images using the project's encryption workflow.
2. Decrypt the encrypted image data.
3. Compare the original files with their recovered versions using SHA-256 hashes.
4. Review the verification output for mismatches or errors.

### Reported Results

| Measurement | Result |
|---|---:|
| Images tested | 20 |
| Matching hashes | 20 |
| Mismatches | 0 |
| Errors | 0 |

**Status:** Passed, based on the reported verification results.

Matching hashes confirm that the recovered test images have the same contents as their original files.

## 4. Vault Integration and Key Protection

### Objective

Verify that HashiCorp Vault Transit protects image-encryption keys and supports authorized image decryption.

### Test Scripts

- `test_vault_database.py`
- `test_vault_image.py`

### Procedure

1. Confirm that Vault is running and the Transit engine is enabled.
2. Verify that the `satellite-images` Transit key is configured.
3. Test the configured encryption and decryption workflow.
4. Retrieve an authorized encrypted image through the API.
5. Verify that the image can be decrypted and returned successfully.

### Failure Handling

Vault unavailability was tested during development. The reported results confirmed safe failure handling and recovery after Vault became available again.

The application should not return decrypted image data when the required key cannot be recovered or image authentication fails.

**Status:** Vault integration and failure-handling tests were reported as completed.

## 5. Authentication and Role-Based Access Control

### Objective

Verify that Keycloak authentication and FastAPI authorization enforce the intended role permissions.

### API Endpoints

| Endpoint | Permission |
|---|---|
| `GET /` | Public |
| `GET /health` | Public |
| `GET /images` | Admin and Analyst |
| `GET /images/{image_id}/view` | Admin, Analyst, and Viewer |

### Test Cases

| Test | Expected HTTP status | Reported result |
|---|---:|---|
| Admin lists images | 200 OK | Passed |
| Analyst lists images | 200 OK | Passed |
| Viewer attempts to list images | 403 Forbidden | Passed |
| Viewer retrieves image 1 | 200 OK | Passed |
| Request to a protected endpoint without a token | 401 Unauthorized | Passed |
| Authenticated request for a nonexistent image | 404 Not Found | Passed |

### Manual Verification

1. Start the FastAPI server.
2. Obtain an access token from the configured Keycloak realm using an authorized test account.
3. Send requests to the API with the appropriate role token.
4. Confirm that the response matches the role's permissions.
5. Repeat a protected request without a token and verify that access is denied.

Example health check:

```bash
curl -i http://127.0.0.1:8001/health
```

Example request without a token:

```bash
curl -i http://127.0.0.1:8001/images
```

The second request should return HTTP 401 if no valid token is provided.

**Status:** The listed authentication and role-permission tests were reported as passed.

## 6. Image Retrieval

### Objective

Verify that authorized users can retrieve individual satellite images through the API.

### Procedure

1. Authenticate through Keycloak.
2. Send an authorized request to `GET /images/{image_id}/view`.
3. Confirm that the API returns HTTP 200 for an existing image.
4. Confirm that the returned content is the decrypted image.
5. Test a nonexistent image identifier and verify that the API returns HTTP 404.

Example request using an existing local token variable:

```bash
curl -i \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  http://127.0.0.1:8001/images/1/view
```

Set `ACCESS_TOKEN` locally before running the command. Do not paste access tokens into documentation or commit them to source control.

**Status:** Successful image retrieval and decryption were reported for the tested image endpoints.

## 7. Tamper Detection

### Objective

Verify that AES-GCM detects unauthorized modifications to encrypted image data.

### Test Script

- `test_tamper_detection.py`

### Procedure

1. Use temporary test data or a safe test copy of an encrypted image.
2. Modify the encrypted data.
3. Attempt to decrypt the modified data.
4. Confirm that authentication fails and the modified data is not accepted as a valid recovered image.

### Expected Result

Modified ciphertext should fail AES-GCM authentication rather than produce accepted plaintext image data.

**Status:** Tamper-detection tests were reported as completed using temporary sample data and a stored encrypted image.

**Safety note:** Do not modify production records or overwrite the original encrypted images during testing.

## 8. Access Logging

### Objective

Verify that security-related API events are recorded in PostgreSQL.

### Database Table

`access_logs`

### Events to Verify

- Successful image-list requests.
- Successful image retrievals.
- Authentication failures.
- Authorization denials.
- Requests for nonexistent images.
- Image retrieval or decryption failures.

### Procedure

1. Make a successful authorized request.
2. Make an unauthorized or unauthenticated request.
3. Request a nonexistent image.
4. Inspect the `access_logs` table.
5. Confirm that the recorded events contain the expected action, status, resource, and timestamp information.

The exact column names should be checked against the current database schema.

**Status:** Access logging was reported as verified, including successful requests, authentication failures, denied requests, and missing-image requests.

## 9. Sensitive Metadata Protection

### Objective

Evaluate protection of sensitive metadata associated with satellite images, including geographic coordinates and sensing timestamps.

### Validation Considerations

- Confirm which metadata fields are protected.
- Verify the stored representation of protected values.
- Confirm that authorized application workflows can use the required metadata.
- Review API responses and access logs for unnecessary exposure.
- Ensure that database access alone does not reveal information that is intended to remain confidential.

**Status:** Metadata-protection work was reported as completed during development. The final submission should describe only the fields and protections that were actually implemented and tested.

## 10. Database and Repository Security

### Secret Scanning

Gitleaks was used to scan the project directory and Git repository.

Commands used:

```bash
gitleaks dir --redact .
gitleaks git --redact .
```

**Reported result:** Both scans completed without reporting secret leaks.

Secret scanning does not guarantee that every possible secret or historical exposure has been identified.

### Git Tracking Review

The repository was checked for tracked database dumps, recovered images, Keycloak database backups, and compiled artifacts.

The specified filename-pattern check returned no output, meaning no matching tracked files were found by that check.

Local recovery files may still exist on disk. Ignore rules prevent specified files from being added accidentally, but ignored files are not automatically deleted.

### Remaining Database Exposure Validation

A final review should confirm that a database-only copy does not expose plaintext image data, plaintext encryption keys, or sensitive metadata.

## 11. Test Summary

| Security area | Reported status |
|---|---|
| Image encryption and decryption | Passed — 20 images verified |
| Keycloak authentication | Passed |
| Role-based authorization | Passed |
| Individual image retrieval | Passed |
| Vault integration | Passed |
| Vault failure handling and recovery | Reported completed |
| AES-GCM tamper detection | Reported completed |
| Access logging | Verified |
| Gitleaks secret scans | No leaks reported |
| Database-only exposure review | Final validation required |
| Location-based access control | Future enhancement |

## 12. Conclusion

Testing performed during development demonstrates the core functionality of the Secure Satellite Image Database, including encrypted satellite image storage, controlled image retrieval, Keycloak authentication, role-based authorization, Vault integration, and security event logging.

The project uses multiple security controls rather than relying on a single mechanism. Continued validation of database-only exposure, metadata confidentiality, and deployment configuration will help strengthen the system before production use.