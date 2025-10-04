import hashlib
import math
import typing as t

import bcrypt
from ellar.utils.crypto import RANDOM_STRING_CHARS
from passlib.hash import django_bcrypt, django_bcrypt_sha256

from .base import BaseHasher, EncodingSalt, EncodingType


class BCryptSHA256Hasher(BaseHasher):
    """
    Secure password hashing using the bcrypt algorithm (recommended)

    This is considered by many to be the most secure algorithm but you
    must first install the bcrypt library.  Please be warned that
    this library depends on native C code and might cause portability
    issues.

    This hasher uses SHA256 to pre-hash passwords, allowing passwords
    of any length to be safely hashed without hitting bcrypt's 72-byte limit.
    """

    hasher = django_bcrypt_sha256
    algorithm = "bcrypt_sha256"
    rounds = 12

    def _get_using_kwargs(self) -> dict:
        return {
            "rounds": self.rounds,
        }

    def encode(
        self, password: EncodingType, salt: EncodingSalt = None
    ) -> t.Union[str, t.Any]:
        self._check_encode_args(password, salt)

        default_salt_size = math.ceil(
            self.salt_entropy / math.log2(len(RANDOM_STRING_CHARS))
        )
        using_kw = {"default_salt_size": default_salt_size, "salt": salt}
        using_kw.update(self._get_using_kwargs())

        # Avoid passlib's backend long-secret detection which raises on Python 3.13+
        # Pre-hash the secret with SHA256 and then use plain django_bcrypt,
        # rewriting the prefix to bcrypt_sha256 for compatibility.
        if isinstance(password, str):
            secret_bytes = password.encode("utf-8")
        else:
            secret_bytes = password

        digest_hex = hashlib.sha256(secret_bytes).hexdigest().encode("ascii")

        if salt is not None:
            salt_str = (
                salt.decode("ascii")
                if isinstance(salt, (bytes, bytearray))
                else str(salt)
            )
            salt_full = f"$2b${self.rounds:02d}${salt_str}".encode("ascii")
        else:
            salt_full = bcrypt.gensalt(self.rounds)

        hashed = bcrypt.hashpw(digest_hex, salt_full)
        return f"bcrypt_sha256${hashed.decode('ascii')}"

    def verify(self, secret: EncodingType, hash_secret: str) -> bool:
        """
        Verify secret against an existing hash.
        """
        # Verify by pre-hashing secret and delegating to django_bcrypt
        if isinstance(secret, str):
            secret_bytes = secret.encode("utf-8")
        else:
            secret_bytes = secret

        digest_hex = hashlib.sha256(secret_bytes).hexdigest().encode("ascii")
        if not hash_secret.startswith("bcrypt_sha256$"):
            return False
        hashed = hash_secret[len("bcrypt_sha256$") :].encode("ascii")
        return bcrypt.checkpw(digest_hex, hashed)

    def decode(self, encoded: str) -> dict:
        algorithm, empty, algostr, work_factor, data = encoded.split("$", 4)
        assert algorithm == self.algorithm
        return {
            "algorithm": algorithm,
            "algostr": algostr,
            "checksum": data[22:],
            "salt": data[:22],
            "work_factor": int(work_factor),
        }

    def must_update(self, encoded: str) -> bool:
        decoded = self.decode(encoded)
        return decoded["work_factor"] != self.rounds  # type:ignore[no-any-return]


class BCryptHasher(BCryptSHA256Hasher):
    """
    Secure password hashing using the bcrypt algorithm

    This is considered by many to be the most secure algorithm but you
    must first install the bcrypt library.  Please be warned that
    this library depends on native C code and might cause portability
    issues.

    This hasher does not first hash the password which means it is subject to
    bcrypt's 72 bytes password truncation. Most use cases should prefer the
    BCryptSHA256PasswordHasher.
    """

    algorithm = "bcrypt"
    hasher = django_bcrypt

    def encode(
        self, password: EncodingType, salt: EncodingSalt = None
    ) -> t.Union[str, t.Any]:
        self._check_encode_args(password, salt)

        # Truncate password to 72 bytes for bcrypt compatibility
        if isinstance(password, str):
            password_bytes = password.encode("utf-8")[:72]
        else:
            password_bytes = password[:72]

        if salt is not None:
            salt_str = (
                salt.decode("ascii")
                if isinstance(salt, (bytes, bytearray))
                else str(salt)
            )
            salt_full = f"$2b${self.rounds:02d}${salt_str}".encode("ascii")
        else:
            salt_full = bcrypt.gensalt(self.rounds)

        hashed = bcrypt.hashpw(password_bytes, salt_full)
        return f"bcrypt${hashed.decode('ascii')}"

    def verify(self, secret: EncodingType, hash_secret: str) -> bool:
        """
        Verify secret against an existing hash, truncating to 72 bytes.
        """
        if isinstance(secret, str):
            secret_bytes = secret.encode("utf-8")[:72]
        else:
            secret_bytes = secret[:72]

        if not hash_secret.startswith("bcrypt$"):
            return False
        hashed = hash_secret[len("bcrypt$") :].encode("ascii")
        return bcrypt.checkpw(secret_bytes, hashed)
