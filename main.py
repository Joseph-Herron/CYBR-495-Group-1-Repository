
# Secure Satellite Image Database
# This file runs the Python backend for our senior design project.
# It connects the website to the database and handles image security.

import os
import base64

import hvac
import httpx
import psycopg2

from jose import jwt, JWTError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response, FileResponse


# This creates the FastAPI application.
# FastAPI handles requests sent from our website.

app = FastAPI(
    title="Secure Satellite Image Database",
    version="1.1.0",
)


# --------------------------------------------------
# KEYCLOAK CONFIGURATION
# --------------------------------------------------

# Keycloak manages user authentication and roles.
# These settings tell the backend where Keycloak is located.

KEYCLOAK_ISSUER = os.getenv(
    "KEYCLOAK_ISSUER",
    "http://127.0.0.1:8080/realms/satellite_security",
)

KEYCLOAK_CLIENT_ID = "satellite-api"

# This allows us to handle missing login tokens.
# Failed authentication attempts can also be recorded.

security = HTTPBearer(auto_error=False)


# --------------------------------------------------
# POSTGRESQL DATABASE CONNECTION
# --------------------------------------------------

# This function connects our application to PostgreSQL.
# PostgreSQL stores satellite images and their information.

def get_connection():
    password = os.getenv("DB_PASSWORD")

    connection_args = {
        "dbname": "satellite_security_db",
        "user": "postgres",
        "port": 5432,
    }

    # Use the database password if one is provided.
    if password:
        connection_args["host"] = "localhost"
        connection_args["password"] = password

    return psycopg2.connect(**connection_args)


# --------------------------------------------------
# ACCESS LOGGING
# --------------------------------------------------

# This function records user activity in the database.
# It saves who made a request, what they did, and the result.

def log_access(username, user_role, action, resource, status_code):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.access_logs
                    (username, user_role, action, resource, status_code)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (username, user_role, action, resource, status_code),
                )

    except Exception as e:
        # A logging error should not stop the original request.
        print(f"Access logging failed: {e}")


# --------------------------------------------------
# USER AUTHENTICATION
# --------------------------------------------------

# This function checks the user's Keycloak access token.
# A valid token tells us who the user is and what roles they have.

def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):

    # Reject requests that do not include a login token.
    if credentials is None:
        log_access(
            username="anonymous",
            user_role="unauthenticated",
            action="authentication_failed",
            resource=request.url.path,
            status_code=401,
        )

        raise HTTPException(
            status_code=401,
            detail="Login required. Provide a Keycloak access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Read the key ID from the token.
        token_header = jwt.get_unverified_header(token)
        token_kid = token_header.get("kid")

        # Request Keycloak's public keys.
        # These keys help verify that the token is legitimate.
        response = httpx.get(
            f"{KEYCLOAK_ISSUER}/protocol/openid-connect/certs",
            timeout=5.0,
        )

        response.raise_for_status()
        jwks = response.json()

        # Find the public key that matches the token.
        signing_key = next(
            (
                key for key in jwks["keys"]
                if key.get("kid") == token_kid
            ),
            None,
        )

        # Reject the token if its signing key is not recognized.
        if signing_key is None:
            log_access(
                username="unknown",
                user_role="unauthenticated",
                action="authentication_failed",
                resource=request.url.path,
                status_code=401,
            )

            raise HTTPException(
                status_code=401,
                detail="Token signing key not recognized",
            )

        # Check the token signature, expiration date, and issuer.
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=KEYCLOAK_ISSUER,
            options={"verify_aud": False},
        )

        # Make sure the token belongs to our application.
        if claims.get("azp") != KEYCLOAK_CLIENT_ID:
            log_access(
                username=claims.get("preferred_username", "unknown"),
                user_role="unauthenticated",
                action="authentication_failed",
                resource=request.url.path,
                status_code=401,
            )

            raise HTTPException(
                status_code=401,
                detail="Token was not issued for this application",
            )

        # Get the user's name and assigned roles from Keycloak.
        roles = claims.get("realm_access", {}).get("roles", [])

        return {
            "username": claims.get("preferred_username", "unknown"),
            "roles": roles,
        }

    except HTTPException:
        raise

    # Reject invalid or expired login tokens.
    except JWTError as e:
        print(f"JWT validation error: {type(e).__name__}: {e}")

        log_access(
            username="unknown",
            user_role="unauthenticated",
            action="authentication_failed",
            resource=request.url.path,
            status_code=401,
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
        )

    # Display an error if Keycloak cannot verify the token.
    except (httpx.HTTPError, KeyError, ValueError) as e:
        print(f"Keycloak verification error: {type(e).__name__}: {e}")

        raise HTTPException(
            status_code=503,
            detail="Unable to verify login with Keycloak",
        )


# --------------------------------------------------
# ROLE-BASED ACCESS CONTROL
# --------------------------------------------------

# This function checks whether a user has permission
# to perform an action based on their assigned role.

def require_roles(*allowed_roles):

    def role_checker(
        request: Request,
        user: dict = Depends(get_current_user),
    ):

        # Check if the user has at least one allowed role.
        if not any(
            role in user["roles"] for role in allowed_roles
        ):

            # Record the denied request in the access logs.
            log_access(
                username=user.get("username", "unknown"),
                user_role=", ".join(user.get("roles", [])),
                action="authorization_denied",
                resource=request.url.path,
                status_code=403,
            )

            raise HTTPException(
                status_code=403,
                detail="Your role is not authorized for this action",
            )

        # Allow the request if the user has permission.
        return user

    return role_checker


# --------------------------------------------------
# HASHICORP VAULT CONNECTION
# --------------------------------------------------

# This function connects to HashiCorp Vault.
# Vault protects the encryption keys used for satellite images.

def get_vault_client():
    vault_addr = os.getenv(
        "VAULT_ADDR",
        "http://127.0.0.1:8200",
    )

    vault_token = os.getenv("VAULT_TOKEN")

    # A Vault token is required to access protected keys.
    if not vault_token:
        raise RuntimeError("VAULT_TOKEN is not set")

    client = hvac.Client(
        url=vault_addr,
        token=vault_token,
    )

    # Make sure Vault accepts the supplied token.
    if not client.is_authenticated():
        raise RuntimeError("Vault authentication failed")

    return client


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

# This route confirms that our API is running.
# It displays a simple message when the main address is opened.

@app.get("/")
def home():
    return {
        "message": "Secure Satellite Image Database API is running"
    }


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

# This route checks whether the Python backend is responding.
# Our website uses this route to display the server status.

@app.get("/health")
def health_check():
    return {"status": "healthy"}


# --------------------------------------------------
# SATELLITE IMAGE LIBRARY
# --------------------------------------------------

# This route retrieves satellite image information from PostgreSQL.
# Only administrators and analysts can view the complete image list.

@app.get("/images")
def get_images(
    user: dict = Depends(require_roles("admin", "analyst")),
):

    try:
        # Connect to the database and request image information.
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        i.image_id,
                        i.product_name,
                        i.satellite,
                        i.processing_level,
                        i.tile_id,
                        i.cloud_cover,
                        m.latitude,
                        m.longitude,
                        m.sensing_time,
                        m.orbit_number
                    FROM satellite_images AS i
                    LEFT JOIN satellite_metadata AS m
                        ON i.image_id = m.image_id
                    ORDER BY i.image_id;
                    """
                )

                # Read the database column names and results.
                columns = [column[0] for column in cur.description]
                rows = cur.fetchall()

        # Convert the database results into image records.
        images = [dict(zip(columns, row)) for row in rows]

        # Record that the user successfully viewed the image list.
        log_access(
            username=user.get("username", "unknown"),
            user_role=", ".join(user.get("roles", [])),
            action="list_images",
            resource="/images",
            status_code=200,
        )

        # Send the image information back to the website.
        return images

    except psycopg2.Error:
        # Display an error if the database request fails.
        raise HTTPException(
            status_code=500,
            detail="Database query failed",
        )


# --------------------------------------------------
# SATELLITE IMAGE DECRYPTION
# --------------------------------------------------

# This route retrieves and decrypts a satellite image.
# Admins, analysts, and viewers can request individual images.

@app.get("/images/{image_id}/view")
def view_image(
    image_id: int,
    user: dict = Depends(
        require_roles("admin", "analyst", "viewer")
    ),
):

    try:
        # Find the encrypted satellite image in PostgreSQL.
        # The database also stores the information needed to decrypt it.
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        encrypted_image,
                        encryption_nonce,
                        encrypted_key
                    FROM satellite_images
                    WHERE image_id = %s;
                    """,
                    (image_id,),
                )

                row = cur.fetchone()

        # Return an error if the requested image does not exist.
        if row is None:
            log_access(
                username=user.get("username", "unknown"),
                user_role=", ".join(user.get("roles", [])),
                action="image_not_found",
                resource=f"/images/{image_id}/view",
                status_code=404,
            )

            raise HTTPException(
                status_code=404,
                detail="Image not found",
            )

        # Separate the encrypted image and its encryption information.
        encrypted_image, nonce, encrypted_key = row

        # Check that the required encryption information exists.
        if (
            encrypted_image is None
            or nonce is None
            or encrypted_key is None
        ):
            raise HTTPException(
                status_code=500,
                detail="Image encryption data is incomplete",
            )

        # Connect to Vault and request the original AES key.
        # Vault decrypts the protected key before it is used.
        vault = get_vault_client()

        key_response = vault.secrets.transit.decrypt_data(
            name="satellite-images",
            ciphertext=encrypted_key,
        )

        # Convert the returned key into bytes.
        aes_key = base64.b64decode(
            key_response["data"]["plaintext"]
        )

        # Use AES-GCM to decrypt the satellite image.
        image_bytes = AESGCM(aes_key).decrypt(
            bytes(nonce),
            bytes(encrypted_image),
            None,
        )

        # Record the successful image request.
        log_access(
            username=user.get("username", "unknown"),
            user_role=", ".join(user.get("roles", [])),
            action="view_image",
            resource=f"/images/{image_id}/view",
            status_code=200,
        )

        # Send the decrypted image back as a downloadable file.
        return Response(
            content=image_bytes,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition":
                    f'attachment; filename="satellite_{image_id}"'
            },
        )

    except HTTPException:
        raise

    except Exception as e:
        # Record the problem without displaying private error details.
        print(f"Image error: {e!r}")

        log_access(
            username=user.get("username", "unknown"),
            user_role=", ".join(user.get("roles", [])),
            action="image_retrieval_failed",
            resource=f"/images/{image_id}/view",
            status_code=503,
        )

        raise HTTPException(
            status_code=503,
            detail="Image service temporarily unavailable",
        )


# --------------------------------------------------
# WEBSITE DASHBOARD
# --------------------------------------------------

# This route opens our website through the Python backend.
# The website is stored in index.html in the project folder.
# This allows the website to communicate with FastAPI directly.

@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(
        os.path.join(os.path.dirname(__file__), "index.html")
    )
