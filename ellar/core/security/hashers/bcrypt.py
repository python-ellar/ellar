from passlib.hash import django_bcrypt, django_bcrypt_sha256

from .base import BaseHasher


class BCryptSHA256Hasher(BaseHasher):
    """
    Secure password hashing using the bcrypt algorithm (recommended)

    This is considered by many to be the most secure algorithm but you
    must first install the bcrypt library.  Please be warned that
    this library depends on native C code and might cause portability
    issues.
    """

    hasher = django_bcrypt_sha256
    algorithm = "bcrypt_sha256"
    rounds = 12

    def _get_using_kwargs(self) -> dict:
        return {
            "rounds": self.rounds,
        }

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
