"""Local account passwords (argon2id)."""

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return str(_hasher.hash(password))


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return bool(_hasher.verify(password_hash, password))
    except VerificationError:
        return False
