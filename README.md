# Secure Satellite Image Database

## Project Description

The Secure Satellite Image Database is a cybersecurity project focused on securely storing, managing, and retrieving satellite imagery and its associated metadata. Satellite imagery can contain sensitive geographic information, including coordinates, sensing timestamps, tile identifiers, and other details that could be misused if accessed or modified by unauthorized individuals.

The project develops a secure database application with a web-based dashboard. It uses multiple layers of security, including image encryption, protected encryption key management, user authentication, role-based access control (RBAC), and security event logging.

The application allows authorized users to access satellite imagery through a backend API and website interface while enforcing permissions based on their assigned roles.

## Project Objectives

1. Develop a secure database for satellite imagery and associated metadata.
2. Encrypt satellite images before storing them in the database.
3. Protect encryption keys using a dedicated secrets-management system.
4. Authenticate users accessing the application.
5. Enforce role-based access control for administrators, analysts, and viewers.
6. Restrict access to data according to assigned permissions.
7. Detect unauthorized modifications to encrypted data.
8. Test the system against simulated database exposure and unauthorized access attempts.
9. Develop a website interface for interacting with the secure satellite image database.
10. Explore geographic restrictions for controlling access to satellite data.

## Technical Architecture

### Website Dashboard

The project includes a web-based dashboard that provides an interface for interacting with the Secure Satellite Image Database.

The website is built using HTML, CSS, and JavaScript and is served by the FastAPI backend. Users can access the dashboard through the application's `/dashboard` endpoint.

The website provides the following functionality:

- Displays the Secure Satellite Image Database dashboard.
- Checks the backend health endpoint to display the application's connection status.
- Accepts a Keycloak access token for user authentication.
- Sends authenticated requests to the FastAPI backend.
- Retrieves and displays satellite image information for users with the appropriate permissions.
- Provides download functionality for retrieving individual satellite images.
- Displays information about the security technologies used in the application, including AES-GCM, HashiCorp Vault, Keycloak, RBAC, and access logging.

The current website uses a manual token-entry process. Users authenticate through Keycloak, obtain an access token, and paste that token into the website. The website includes the token in its requests to the backend using HTTP Bearer authentication.

The website communicates with the following API endpoints:

| Endpoint                  | Purpose                                                      |
| ------------------------- | ------------------------------------------------------------ |
| `/dashboard`              | Serves the website dashboard.                                |
| `/health`                 | Checks backend application availability.                     |
| `/images`                 | Retrieves the list of satellite images for authorized users. |
| `/images/{image_id}/view` | Retrieves an individual satellite image after authorization. |

The website follows the same role-based permissions enforced by the backend. Administrators and analysts can access the image-listing functionality, while viewers cannot list images. Viewers are permitted to retrieve individual images when they have the appropriate image identifier and authorization.

### Python and FastAPI

Python and FastAPI provide the backend API that connects the website, authentication services, database, and encryption services.

The backend is responsible for:

- Processing API requests from the website and other clients.
- Serving the website dashboard.
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

**Current implementation note:** Image encryption and decryption are implemented and verified. Sensitive metadata fields are represented in the database schema, but encryption of those fields is future work until implemented and tested.

### Keycloak Authentication and RBAC

Keycloak handles user authentication and role assignments. FastAPI checks the user's access token and enforces authorization rules for protected endpoints.

The three configured roles are:

- **Admin:** Can list satellite images and retrieve individual images.
- **Analyst:** Can list satellite images and retrieve individual images.
- **Viewer:** Can retrieve individual satellite images but cannot access the image-listing endpoint.

The current API permissions are:

| Endpoint                      | Authorized roles       |
| ----------------------------- | ---------------------- |
| `GET /images`                 | Admin, Analyst         |
| `GET /images/{image_id}/view` | Admin, Analyst, Viewer |

These permissions describe the currently implemented API behavior. Additional administrative functions and finer-grained permissions remain outside the verified endpoint set.

### Access Logging

The application records security-related events in PostgreSQL, including:

- Successful image retrievals.
- Permitted image-list requests.
- Authorization denials.
- Authentication failures.
- Requests for nonexistent images.

These records support auditing and help identify unsuccessful or unauthorized access attempts.

### Geospatial Processing — Planned

GeoPandas may be incorporated to process geographic coordinates, work with geographic boundaries, and support location-based access control.

Geographic restrictions have not yet been verified as an implemented feature.

## Dataset

The project uses satellite imagery and associated metadata, including geographic coordinates, sensing times, tile identifiers, processing levels, and cloud-cover information.

The current test dataset contains 20 satellite images. Image records and their associated metadata are maintained in PostgreSQL.

## Implementation and Testing Results

### Encryption and Decryption

- All 20 satellite images were encrypted.
- A verification script compared the original images with the recovered, decrypted files using SHA-256 hashes.
- **Result: 20 matching hashes, zero mismatches, and zero errors.**

These results demonstrate that the application successfully recovered the original image files after encryption and decryption.

### Authentication and Role-Based Access Control

The following API tests passed:

| Test                                          | Expected result | Result |
| --------------------------------------------- | --------------- | ------ |
| Admin lists images                            | HTTP 200        | Passed |
| Analyst lists images                          | HTTP 200        | Passed |
| Viewer lists images                           | HTTP 403        | Passed |
| Viewer retrieves image 1                      | HTTP 200        | Passed |
| Request without an access token               | HTTP 401        | Passed |
| Authenticated request for a nonexistent image | HTTP 404        | Passed |

These tests demonstrate that the API enforces the configured permissions and rejects requests that do not meet authentication or authorization requirements.

### Website Integration

The website dashboard was integrated with the FastAPI backend and tested locally.

Verified functionality includes:

- Successful access to the dashboard through `/dashboard`.
- Successful communication with the backend health endpoint.
- Successful Keycloak access-token generation.
- Successful manual token authentication through the website.
- Successful loading of satellite image information through the authenticated API.

The website uses the same backend authentication and authorization controls as the API.

### Access Logging

Tests confirmed that the application records successful retrievals, permitted listing requests, denied requests, authentication failures, and requests for nonexistent images.

### Tamper Detection

AES-GCM tamper detection was tested using both temporary sample data and an encrypted image stored in the database.

The tests verified that modified encrypted data fails authentication during decryption, producing an integrity verification failure rather than returning corrupted image data.

### Vault Failure Handling

Vault failure handling was tested to verify that the application responds appropriately when the key-management service is unavailable.

The application does not treat an unavailable Vault service as a successful decryption operation.

### Remaining Security Validation

The following areas require additional testing or implementation before they can be reported as complete:

- **Database exposure:** Further validate that a database-only copy does not reveal plaintext satellite imagery or plaintext encryption keys.
- **Metadata protection:** Determine which metadata fields require encryption and implement and test that protection.
- **Location-based access control:** Implement geographic restrictions if time permits.
- **Expanded website functionality:** Consider automatic Keycloak login and additional administrative features.

## Future Work

Potential extensions include:

- Location-based access control using geographic boundaries.
- Encryption of sensitive satellite metadata.
- Automatic Keycloak authentication through the website.
- Expanded administrative functionality.
- Additional security testing and validation.
- AI-assisted satellite image analysis.
- Additional geospatial processing using GeoPandas.

## Technology Stack

- **Programming Language:** Python
- **Backend API:** FastAPI
- **Website:** HTML, CSS, JavaScript
- **Database:** PostgreSQL
- **Image Encryption:** AES-256-GCM
- **Encryption Key Protection:** HashiCorp Vault Transit
- **Authentication and Roles:** Keycloak
- **Geospatial Extension (Planned):** GeoPandas

## Project Sponsor

**Dr. Jian Wang**

Dr. Jian Wang provides project guidance, feedback, and oversight.

