# Secure Satellite Image Database

## Project Overview

The Secure Satellite Image Database is a cybersecurity capstone project focused on securely storing, managing, and retrieving satellite imagery and its associated metadata. Satellite imagery can contain sensitive geographic information, including coordinates, sensing timestamps, and other details that could be misused if accessed by unauthorized individuals.

The system implements multiple layers of security, including image encryption, encryption key management, user authentication, role-based access control (RBAC), and security event logging.

## Project Objectives

1. Develop a secure database for satellite imagery and associated metadata.
2. Encrypt satellite images before storing them in the database.
3. Protect encryption keys using a dedicated secrets-management system.
4. Authenticate users before granting access to protected API endpoints.
5. Enforce role-based permissions for administrators, analysts, and viewers.
6. Restrict access to satellite imagery according to assigned permissions.
7. Detect unauthorized modifications to encrypted image data.
8. Evaluate security through encryption, authentication, authorization, and failure-handling tests.
9. Explore geographic restrictions for controlling access to satellite data.

## Technical Architecture

The system uses Python, FastAPI, PostgreSQL, HashiCorp Vault, and Keycloak to provide a layered security architecture.

### Python and FastAPI

Python and FastAPI provide the backend API connecting users, authentication services, the database, and encryption services.

The backend is responsible for:

- Processing API requests.
- Validating Keycloak authentication tokens.
- Enforcing role-based authorization.
- Retrieving and decrypting authorized satellite images.
- Communicating with PostgreSQL and HashiCorp Vault.
- Recording security-related events.

### PostgreSQL Database

PostgreSQL is the primary database for satellite imagery records, associated metadata, encryption-related fields, and access logs.

The database contains three primary tables:

- **`satellite_images`** — Stores image identifiers, product information, satellite details, processing information, cloud-cover information, and encrypted image data with the associated encryption fields.
- **`satellite_metadata`** — Stores geographic coordinates, sensing timestamps, tile identifiers, and orbit information, along with the project's metadata-protection fields.
- **`access_logs`** — Records security events, including user information, roles, requested actions, resources, HTTP status codes, and timestamps.

The database separates image records, metadata, and security auditing into distinct tables.

### Image Encryption and Key Management

The system uses AES-GCM authenticated encryption to protect satellite image data. HashiCorp Vault Transit provides a separate service for protecting the image-encryption keys.

The general image-encryption workflow is:

1. Satellite image data is prepared for storage.
2. The image is encrypted using AES-GCM.
3. Vault Transit protects the image-encryption key.
4. PostgreSQL stores the encrypted image, encryption nonce, and Vault-protected key.
5. An authorized user requests an image through the API.
6. FastAPI retrieves the encrypted image and its associated encryption information.
7. Vault is used to recover the encryption key.
8. AES-GCM decrypts and authenticates the image data.
9. The decrypted image is returned only after the request passes authorization.

Plaintext image-encryption keys are not intended to be stored in PostgreSQL. The stored key field contains a Vault-protected key rather than the plaintext key.

AES-GCM also provides integrity protection: unauthorized changes to ciphertext or the associated authentication data should cause decryption to fail.

### Keycloak Authentication and Role-Based Access Control

Keycloak handles user authentication and role assignments. FastAPI validates access tokens and checks role permissions before processing protected requests.

The implemented roles are:

- **Admin:** Can list satellite images and retrieve individual images.
- **Analyst:** Can list satellite images and retrieve individual images.
- **Viewer:** Can retrieve individual satellite images but cannot access the image-listing endpoint.

The verified endpoint permissions are:

| API endpoint | Admin | Analyst | Viewer |
|---|---|---|---|
| `GET /` | Public | Public | Public |
| `GET /health` | Public | Public | Public |
| `GET /images` | Allowed | Allowed | Denied |
| `GET /images/{image_id}/view` | Allowed | Allowed | Allowed |

Requests without a valid access token are rejected by protected endpoints. Authenticated requests that lack the required role are rejected with HTTP 403.

These permissions describe the implemented API behavior. They do not imply that separate administrative management endpoints have been developed.

### Access Logging and Auditing

The application records security-related events in PostgreSQL through the `access_logs` table.

Logged events include:

- Successful image-list requests.
- Successful image retrievals.
- Authentication failures.
- Authorization denials.
- Requests for nonexistent images.
- Image retrieval or decryption failures.

The logs support auditing, troubleshooting, and review of attempted unauthorized access.

### Sensitive Metadata Protection

The project includes protection for sensitive satellite metadata, including geographic coordinates and sensing timestamps.

Metadata protection should be evaluated alongside the image-encryption controls because encrypting image files alone does not protect sensitive information exposed through database columns, API responses, or logs.

The API's image-list endpoint is restricted to the Admin and Analyst roles because it returns catalog and metadata information.

### Geospatial Processing — Future Enhancement

GeoPandas is a potential extension for processing geographic coordinates and boundaries and enforcing location-based access restrictions.

Geographic access restrictions should be considered a future enhancement unless the corresponding functionality is implemented and verified.

## Dataset

The project uses a test dataset containing **20 satellite images** and associated metadata.

The dataset includes information such as:

- Satellite and product identifiers.
- Processing levels.
- Tile identifiers.
- Cloud-cover percentages.
- Geographic coordinates.
- Sensing timestamps.
- Orbit information.

Image records and associated metadata are maintained in PostgreSQL. The dataset supports testing of encrypted storage, image retrieval, access control, and security auditing.

## Implementation and Testing Results

The following results summarize the tests completed during development.

### Image Encryption and Decryption

All 20 satellite images were tested using the project's encryption and verification scripts.

Verification compared the original images against their recovered, decrypted versions using SHA-256 hashes.

**Reported result:**
- 20 images verified.
- 20 matching original and recovered hashes.
- 0 mismatches.
- 0 errors.

This confirms that the tested images could be encrypted and recovered without changing their contents.

### Authentication and Role-Based Access Control

The following API tests passed during development:

| Test | Expected result | Result |
|---|---|---|
| Admin lists images | HTTP 200 | Passed |
| Analyst lists images | HTTP 200 | Passed |
| Viewer lists images | HTTP 403 | Passed |
| Viewer retrieves an individual image | HTTP 200 | Passed |
| Request to a protected endpoint without a token | HTTP 401 | Passed |
| Authenticated request for a nonexistent image | HTTP 404 | Passed |

These tests demonstrate the intended distinction between authentication and authorization: users must authenticate, and their assigned roles determine which endpoints they can access.

### Vault Integration and Failure Handling

Vault Transit was configured to protect the image-encryption keys. Encryption and decryption operations were tested during development.

Failure-handling tests also covered Vault unavailability. The application was tested for safe failure behavior and recovery after Vault service availability was restored.

The application must not return decrypted image data when it cannot successfully recover the required key and authenticate the image data.

### Tamper Detection

The project's tamper-detection tests evaluated the behavior of authenticated encryption when encrypted data is modified.

Tests included temporary sample data and a stored encrypted image. Modified ciphertext should fail AES-GCM authentication instead of producing an accepted plaintext image.

Tamper testing must be performed against test data or a safely isolated copy so that the original stored images are not damaged.

### Access Logging

Access logging was tested for successful and unsuccessful requests.

The application records events for permitted requests, authentication failures, authorization denials, and requests for nonexistent images. The database logs provide a record of these events for auditing and verification.

### Database and Secret-Handling Review

The repository underwent secret-scanning checks using Gitleaks. The directory and Git scans reported no leaks.

Repository review also identified local recovery backups and other generated artifacts. These files were excluded from Git tracking through ignore rules or verified as untracked for the checked filename patterns.

Secret scanning reduces the risk of accidentally committing credentials, but it does not replace secure credential management, review of Git history, or protection of local backup files.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root endpoint |
| `GET` | `/health` | Reports API health |
| `GET` | `/images` | Lists image records for authorized Admin and Analyst users |
| `GET` | `/images/{image_id}/view` | Retrieves and decrypts an individual image for authorized users |

The API uses Keycloak-issued access tokens for protected operations.

## Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Programming language | Python | Application logic and testing |
| Backend API | FastAPI | HTTP endpoints and access enforcement |
| Database | PostgreSQL | Image records, metadata, and access logs |
| Image encryption | AES-GCM | Confidentiality and authenticated integrity |
| Key management | HashiCorp Vault Transit | Protection of image-encryption keys |
| Authentication and RBAC | Keycloak | Identity, tokens, and role assignments |
| Geospatial extension | GeoPandas | Potential location-based access controls |

## Local Development Setup

The following instructions assume the project dependencies and local services have been configured.

### Prerequisites

- Python and a virtual environment.
- PostgreSQL with the project database configured.
- HashiCorp Vault with Transit enabled and the required encryption key configured.
- Keycloak with the `satellite_security` realm, the `satellite-api` client, and the required users and roles.
- The project's Python dependencies.

### Configure Environment Variables

Configure required database and Vault settings in your local environment. For example:

```bash
export DB_PASSWORD="your-local-database-password"
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="your-local-vault-token"
```

Use your own local credentials. Do not commit real passwords, access tokens, or other secrets to GitHub.

Configure the Keycloak issuer and any other required settings according to the application's current configuration.

### Start the API

From the project directory, activate the virtual environment and start FastAPI:

```bash
source .venv/bin/activate
uvicorn main:app --reload --port 8001
```

Check the health endpoint:

```bash
curl -i http://127.0.0.1:8001/health
```

A successful health check returns HTTP 200.

### Authentication

Obtain an access token from the configured Keycloak realm using an authorized test account. Supply the token to protected API requests through the `Authorization: Bearer` header.

Do not place real credentials or access tokens in the README, source code, screenshots, or public test output.

## Security Considerations

- Keep database credentials and Vault tokens out of source control.
- Restrict Vault policies to the minimum capabilities needed by each identity.
- Keep plaintext encryption keys out of persistent database storage.
- Validate authentication and authorization before releasing protected data.
- Do not expose decrypted images when decryption or integrity verification fails.
- Review API responses and access logs for unnecessary disclosure of sensitive metadata.
- Keep local database dumps, recovery backups, and decrypted image files out of the public repository.
- Continue testing failure behavior and reviewing changes to security-sensitive code.

## Future Work

Potential extensions include:

- Location-based access control using geographic boundaries.
- AI-assisted satellite image analysis.
- More granular permissions and additional administrative functionality.
- Expanded security testing and automated regression tests.
- Further evaluation of metadata exposure through database queries, API responses, and audit logs.

## Project Sponsors

The project was developed as part of the CYBR-495 capstone. Sponsor information can be added here if required by the final project submission.

