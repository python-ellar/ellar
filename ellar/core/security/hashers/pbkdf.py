from ellar.utils.crypto import must_update_salt
from passlib.hash import django_pbkdf2_sha1, django_pbkdf2_sha256

from .base import BaseHasher


class PBKDF2Hasher(BaseHasher):
    """
    Handles PBKDF2 passwords
    """

    hasher = django_pbkdf2_sha256
    algorithm: str = "pbkdf2_sha256"
    iterations: int = 870000

    def _get_using_kwargs(self) -> dict:
        return {"rounds": self.iterations}

    def decode(self, encoded: str) -> dict:
        algorithm, iterations, salt, _hash = encoded.split("$", 3)
        assert algorithm == self.algorithm
        return {
            "algorithm": algorithm,
            "hash": _hash,
            "iterations": int(iterations),
            "salt": salt,
        }

    def must_update(self, encoded: str) -> bool:
        decoded = self.decode(encoded)
        update_salt = must_update_salt(decoded["salt"], self.salt_entropy)
        return (decoded["iterations"] != self.iterations) or update_salt


class PBKDF2SHA1Hasher(PBKDF2Hasher):
    """
    Alternate PBKDF2 hasher which uses SHA1, the default PRF
    recommended by PKCS #5. This is compatible with other
    implementations of PBKDF2, such as openssl's
    PKCS5_PBKDF2_HMAC_SHA1().
    """

    hasher = django_pbkdf2_sha1
    algorithm: str = "pbkdf2_sha1"
