"""
Security utilities for password hashing and JWT token handling.
"""
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to compare against.
        
    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash.
        
    Returns:
        The hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(
    user_id: UUID,
    tenant_id: UUID,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict[str, Any]] = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: The user's UUID to encode in the token.
        tenant_id: The tenant's UUID to encode in the token.
        expires_delta: Optional custom expiration time.
        additional_claims: Optional additional claims to include.
        
    Returns:
        The encoded JWT token string.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode: dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decode and verify a JWT access token.
    
    Args:
        token: The JWT token string to decode.
        
    Returns:
        The decoded token payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user_id from a JWT token.
    
    Args:
        token: The JWT token string.
        
    Returns:
        The user_id if valid, None otherwise.
    """
    payload = decode_access_token(token)
    if payload:
        return payload.get("sub")
    return None


def get_tenant_id_from_token(token: str) -> Optional[str]:
    """
    Extract tenant_id from a JWT token.
    
    Args:
        token: The JWT token string.
        
    Returns:
        The tenant_id if valid, None otherwise.
    """
    payload = decode_access_token(token)
    if payload:
        return payload.get("tenant_id")
    return None
