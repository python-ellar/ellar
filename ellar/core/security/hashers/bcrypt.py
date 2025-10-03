import hashlib
import math
import typing as t

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

    def _sha256_hash(self, password: EncodingType) -> str:
        """
        Hash password with SHA256 and return as hex string.
        This matches what passlib's django_bcrypt_sha256 does internally.
        """
        if isinstance(password, str):
            password_bytes = password.encode("utf-8")
        else:
            password_bytes = password

        return hashlib.sha256(password_bytes).hexdigest()

    def encode(
        self, password: EncodingType, salt: EncodingSalt = None
    ) -> t.Union[str, t.Any]:
        self._check_encode_args(password, salt)

        default_salt_size = math.ceil(
            self.salt_entropy / math.log2(len(RANDOM_STRING_CHARS))
        )
        using_kw = {"default_salt_size": default_salt_size, "salt": salt}
        using_kw.update(self._get_using_kwargs())

        # Try passlib first (works on Python < 3.13)
        try:
            return self.hasher.using(**using_kw).hash(password)
        except ValueError as e:
            # Python 3.13+ bcrypt enforces 72-byte limit before passlib can pre-hash
            # So we pre-hash manually and use the plain bcrypt hasher
            if "password cannot be longer than 72 bytes" in str(e):
                hashed = self._sha256_hash(password)
                return self.hasher.using(**using_kw).hash(hashed)
            raise

    def verify(self, secret: EncodingType, hash_secret: str) -> bool:
        """
        Verify secret against an existing hash.
        """
        # Try passlib first (works on Python < 3.13)
        try:
            return self.hasher.verify(secret, hash_secret)  # type:ignore[no-any-return]
        except ValueError as e:
            # Python 3.13+ bcrypt enforces 72-byte limit before passlib can pre-hash
            # So we pre-hash manually
            if "password cannot be longer than 72 bytes" in str(e):
                hashed = self._sha256_hash(secret)
                return self.hasher.verify(hashed, hash_secret)  # type:ignore[no-any-return]
            raise

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

        # Truncate password to 72 bytes for bcrypt compatibility (Python 3.13+)
        if isinstance(password, str):
            password_bytes = password.encode("utf-8")[:72]
        else:
            password_bytes = password[:72]

        default_salt_size = math.ceil(
            self.salt_entropy / math.log2(len(RANDOM_STRING_CHARS))
        )
        using_kw = {"default_salt_size": default_salt_size, "salt": salt}
        using_kw.update(self._get_using_kwargs())
        return self.hasher.using(**using_kw).hash(password_bytes)

    def verify(self, secret: EncodingType, hash_secret: str) -> bool:
        """
        Verify secret against an existing hash, truncating to 72 bytes.
        """
        # Truncate secret to 72 bytes for bcrypt compatibility (Python 3.13+)
        if isinstance(secret, str):
            secret_bytes = secret.encode("utf-8")[:72]
        else:
            secret_bytes = secret[:72]

        return self.hasher.verify(secret_bytes, hash_secret)  # type:ignore[no-any-return]
