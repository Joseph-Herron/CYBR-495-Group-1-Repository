# Secure Satellite Image Database

## Project Description

This project develops a secure database system for storing and managing satellite imagery and its associated metadata. Satellite imagery can contain sensitive geographic information, including coordinates, timestamps, and other details that could be misused if accessed by unauthorized individuals.

The system uses multiple layers of security, including image encryption, secure encryption key management, user authentication, role-based access control (RBAC), and security event logging.

**Sponsors:** Dr. Wang and Dr. Pharris

## Project Objectives

1. Develop a secure database for satellite imagery and associated metadata.
2. Encrypt satellite images before storing them in the database.
3. Protect encryption keys using a dedicated secrets-management system.
4. Authenticate users accessing the application.
5. Enforce role-based access control for administrators, analysts, and viewers.
6. Restrict access to data according to assigned permissions.
7. Detect unauthorized modifications to encrypted data.
8. Test the system against simulated database exposure and unauthorized access attempts.
9. Explore geographic restrictions for controlling access to satellite data.

## Technical Architecture

### Python and FastAPI

Python and FastAPI provide the backend API that connects users, authentication services, the database, and encryption services.

The backend is responsible for:
- Processing API requests.
- Validating authentication tokens.
- Enforcing role-based authorization.
- Retrieving and decrypting authorized satellite imagery.
- Communicating with PostgreSQL and HashiCorp Vault.
- Recording security-related events.

### PostgreSQL

PostgreSQL is the primary database. It stores satellite image records, associated metadata, encrypted image data, encryption nonces, Vault-protected encryption keys, and access logs.

The database includes three main tables:
- `satellite_images` — image identifiers, product information, encrypted image data, and encryption-related fields.
- `satellite_metadata` — geographic coordinates, sensing timestamps, tile identifiers, and orbit information.
- `access_logs` — usernames, roles, actions, requested resources, HTTP status codes, and timestamps.

### Image Encryption and Key Management

The application uses AES-GCM to encrypt satellite image data. HashiCorp Vault Transit protects the encryption keys separately from the application's image-encryption process.

The general workflow is:

1. The application receives satellite image data.
2. The image is encrypted using AES-GCM.
3. Vault Transit protects the image's encryption key.
4. The encrypted image, nonce, and Vault-protected key are stored in PostgreSQL.
5. When an authorized user requests an image, the backend retrieves the encrypted data.
6. The backend uses Vault to recover the encryption key and decrypt the image.
7. The application returns the recovered image only after authorization succeeds.

Plaintext encryption keys are not stored in PostgreSQL. The stored `encrypted_key` field contains a Vault-protected key rather than the plaintext key.

**Current implementation note:** Image encryption is implemented and verified. Sensitive metadata fields are currently represented in the database schema, but encryption of those fields should be treated as future work until implemented and tested.

### Keycloak Authentication and RBAC

Keycloak handles user authentication and role assignments. FastAPI checks the user's token and enforces authorization rules for protected endpoints.

The three configured roles are:

- **Admin:** Can list satellite images and retrieve individual images.
- **Analyst:** Can list satellite images and retrieve individual images.
- **Viewer:** Can retrieve individual satellite images but cannot access the image-listing endpoint.

The current API permissions are:

| Endpoint | Authorized roles |
|---|---|
| `GET /images` | Admin, Analyst |
| `GET /images/{image_id}/view` | Admin, Analyst, Viewer |

These permissions describe the currently implemented API behavior; additional administrative functions and finer-grained permissions remain outside the verified endpoint set.

### Access Logging

The application records security-related events in PostgreSQL, including successful image retrievals, image-list requests, authorization denials, authentication failures, and missing-image requests.

These records support auditing and help identify unsuccessful or unauthorized access attempts.

### Geospatial Processing — Planned

GeoPandas may be incorporated to process geographic coordinates, work with geographic boundaries, and support location-based access control.

Geographic restrictions have not yet been verified as an implemented feature.

## Dataset

The project uses satellite imagery and associated metadata, including geographic coordinates, sensing times, tile identifiers, processing levels, and cloud-cover information.

The current test dataset contains 20 satellite images. Image records and their metadata are maintained in PostgreSQL.

## Implementation and Testing Results

### Encryption and Decryption

- All 20 satellite images were encrypted.
- A verification script compared the original images with the recovered, decrypted files using SHA-256 hashes.
- **Result:** 20 matching hashes, zero mismatches, and zero errors.

### Authentication and Role-Based Access Control

The following API tests have passed:

| Test | Expected result | Result |
|---|---|---|
| Admin lists images | HTTP 200 | Passed |
| Analyst lists images | HTTP 200 | Passed |
| Viewer lists images | HTTP 403 | Passed |
| Viewer retrieves image 1 | HTTP 200 | Passed |
| Request without an access token | HTTP 401 | Passed |
| Authenticated request for a nonexistent image | HTTP 404 | Passed |

### Access Logging

Tests confirmed that the application records successful retrievals, permitted listing requests, denied requests, authentication failures, and requests for nonexistent images.

### Remaining Security Tests

The following areas require additional testing or implementation before they can be reported as complete:

- **Database exposure:** Verify that a database-only copy does not reveal plaintext satellite imagery or plaintext encryption keys.
- **Tamper detection:** Modify encrypted image data and verify that AES-GCM authentication rejects the altered ciphertext.
- **Key management:** Test behavior when Vault is unavailable and verify that unauthorized requests cannot obtain protected keys.
- **Metadata protection:** Determine which metadata fields require encryption and implement and test that protection.
- **Location-based access control:** Implement geographic restrictions if time permits.

## Future Work

Potential extensions include location-based access control, AI-assisted satellite image analysis, expanded administrative functionality, and additional security testing.

## Technology Stack

- **Language:** Python
- **Backend API:** FastAPI
- **Database:** PostgreSQL
- **Image encryption:** AES-GCM
- **Encryption key protection:** HashiCorp Vault Transit
- **Authentication and roles:** Keycloak
- **Potential geospatial extension:** GeoPandas

## Project Sponsors

Dr. Wang will provide project guidance, feedback, and oversight throughout development.
