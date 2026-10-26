
import os
import base64

import hvac
import httpx
import psycopg2
from jose import jwt, JWTError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response

app = FastAPI(
    title="Secure Satellite Image Database",
    version="1.1.0",
)

# Keycloak configuration
KEYCLOAK_ISSUER = os.getenv(
    "KEYCLOAK_ISSUER",
    "http://127.0.0.1:8080/realms/satellite_security",
)
KEYCLOAK_CLIENT_ID = "satellite-api"

# Let the application handle missing tokens so they can be logged.
security = HTTPBearer(auto_error=False)


# Connect to PostgreSQL
def get_connection():
    password = os.getenv("DB_PASSWORD")

    if not password:
        raise RuntimeError("DB_PASSWORD is not set")

    return psycopg2.connect(
        dbname="satellite_security",
        host="localhost",
        user="postgres",
        password=password,
        port=5432,
    )


# Record API access in PostgreSQL
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
        # Logging failures should not hide the original API response.
        print(f"Access logging failed: {e}")


# Verify Keycloak login tokens
def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
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
        # Read the token's key ID
        token_header = jwt.get_unverified_header(token)
        token_kid = token_header.get("kid")

        # Retrieve Keycloak's public signing keys
        response = httpx.get(
            f"{KEYCLOAK_ISSUER}/protocol/openid-connect/certs",
            timeout=5.0,
        )
        response.raise_for_status()
        jwks = response.json()

        signing_key = next(
            (
                key for key in jwks["keys"]
                if key.get("kid") == token_kid
            ),
            None,
        )

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

        # Verify signature, expiration, and issuer
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=KEYCLOAK_ISSUER,
            options={"verify_aud": False},
        )

        # Ensure the token was issued for this application
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

        # Read the user's Keycloak realm roles
        roles = claims.get("realm_access", {}).get("roles", [])

        return {
            "username": claims.get("preferred_username", "unknown"),
            "roles": roles,
        }

    except HTTPException:
        raise

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

    except (httpx.HTTPError, KeyError, ValueError) as e:
        print(f"Keycloak verification error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=503,
            detail="Unable to verify login with Keycloak",
        )


# Check whether the user has an allowed role
def require_roles(*allowed_roles):
    def role_checker(
        request: Request,
        user: dict = Depends(get_current_user),
    ):
        if not any(
            role in user["roles"] for role in allowed_roles
        ):
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

        return user

    return role_checker


# Connect to HashiCorp Vault
def get_vault_client():
    vault_addr = os.getenv(
        "VAULT_ADDR",
        "http://127.0.0.1:8200",
    )
    vault_token = os.getenv("VAULT_TOKEN")

    if not vault_token:
        raise RuntimeError("VAULT_TOKEN is not set")

    client = hvac.Client(
        url=vault_addr,
        token=vault_token,
    )

    if not client.is_authenticated():
        raise RuntimeError("Vault authentication failed")

    return client


# Public home endpoint
@app.get("/")
def home():
    return {
        "message": "Secure Satellite Image Database API is running"
    }


# Public health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Only admins and analysts can retrieve the image list
@app.get("/images")
def get_images(
    user: dict = Depends(require_roles("admin", "analyst")),
):
    try:
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

                columns = [column[0] for column in cur.description]
                rows = cur.fetchall()

        images = [dict(zip(columns, row)) for row in rows]

        log_access(
            username=user.get("username", "unknown"),
            user_role=", ".join(user.get("roles", [])),
            action="list_images",
            resource="/images",
            status_code=200,
        )

        return images

    except psycopg2.Error:
        raise HTTPException(
            status_code=500,
            detail="Database query failed",
        )


# Admins, analysts, and viewers can retrieve individual images
@app.get("/images/{image_id}/view")
def view_image(
    image_id: int,
    user: dict = Depends(
        require_roles("admin", "analyst", "viewer")
    ),
):
    try:
        # Retrieve the encrypted image and encryption information
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

        encrypted_image, nonce, encrypted_key = row

        if (
            encrypted_image is None
            or nonce is None
            or encrypted_key is None
        ):
            raise HTTPException(
                status_code=500,
                detail="Image encryption data is incomplete",
            )

        # Ask Vault to decrypt the protected AES key
        vault = get_vault_client()

        key_response = vault.secrets.transit.decrypt_data(
            name="satellite-images",
            ciphertext=encrypted_key,
        )

        aes_key = base64.b64decode(
            key_response["data"]["plaintext"]
        )

        # Decrypt the image using AES-GCM
        image_bytes = AESGCM(aes_key).decrypt(
            bytes(nonce),
            bytes(encrypted_image),
            None,
        )

        # Record successful image access
        log_access(
            username=user.get("username", "unknown"),
            user_role=", ".join(user.get("roles", [])),
            action="view_image",
            resource=f"/images/{image_id}/view",
            status_code=200,
        )

        # Return the decrypted image as a download
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
        print(f"Image error: {e!r}")

        raise HTTPException(
            status_code=500,
            detail="Image retrieval or decryption failed",
        )
