"""
Security utilities: password hashing/verification using PBKDF2-HMAC-SHA256
with a per-user random salt. No external dependencies required beyond
Python's standard library, which keeps deployment simple.
"""

import hashlib
import os
import secrets


PBKDF2_ITERATIONS = 260_000


def generate_salt() -> str:
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    """Derive a hex digest from password + salt using PBKDF2-HMAC-SHA256."""
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return dk.hex()


def create_password_record(password: str) -> tuple[str, str]:
    """Returns (password_hash, salt) for storing a new user."""
    salt = generate_salt()
    pwd_hash = hash_password(password, salt)
    return pwd_hash, salt


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    candidate = hash_password(password, salt)
    return secrets.compare_digest(candidate, stored_hash)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Basic password policy suitable for a club-management tool:
    minimum 8 characters, at least one letter and one digit.
    Returns (is_valid, message).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    return True, ""
