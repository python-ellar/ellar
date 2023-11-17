import typing as t

from ellar.common.utils.crypto import must_update_salt
from passlib.hash import md5_crypt

from .base import BaseHasher, EncodingSalt, EncodingType


class MD5Hasher(BaseHasher):
    """
    The Salted MD5 password hashing algorithm (not recommended)
    """

    hasher = md5_crypt
    algorithm = "md5"
    salt_entropy = 45

    def decode(self, encoded: str) -> dict:
        (
            algorithm,
            _,
            salt,
            hash_,
        ) = encoded.split("$", 3)
        assert algorithm == self.algorithm
        return {
            "algorithm": algorithm,
            "hash": hash_,
            "salt": salt,
        }

    def encode(
        self, password: EncodingType, salt: EncodingSalt = None
    ) -> t.Union[str, t.Any]:
        _hash = super().encode(password, salt)
        return "%s%s" % (self.algorithm, _hash)

    @classmethod
    def identity(cls, encoded: str) -> bool:
        return cls.hasher.identify(  # type:ignore[no-any-return]
            encoded.replace(cls.algorithm, "")
        )

    def verify(self, secret: EncodingType, hash_secret: str) -> bool:
        return self.hasher.verify(  # type:ignore[no-any-return]
            secret, hash_secret.replace(self.algorithm, "")
        )

    def must_update(self, encoded: str) -> bool:
        decoded = self.decode(encoded)
        return must_update_salt(decoded["salt"], self.salt_entropy)
