import base64
import hashlib
import secrets
import typing as t

from .base import BaseHasher, EncodingSalt, EncodingType


class ScryptHasher(BaseHasher):
    """
    Secure password hashing using the Scrypt algorithm.
    """

    hasher = hashlib.scrypt
    algorithm = "scrypt"

    block_size = 8
    maxmem = 0
    parallelism = 1
    work_factor = 2**14

    def _encode_action(
        self,
        password: EncodingType,
        n: int,
        r: int,
        p: int,
        salt: EncodingSalt,
    ) -> str:
        hash_ = self.hasher(  # type:ignore[misc]
            password.encode(),  # type:ignore[union-attr]
            salt=salt.encode(),  # type:ignore[union-attr]
            n=n,
            r=r,
            p=p,
            maxmem=self.maxmem,
            dklen=64,
        )
        hash_ = (
            base64.b64encode(hash_).decode("ascii").strip()  # type:ignore[assignment]
        )
        return "%s$%d$%s$%d$%d$%s" % (
            self.algorithm,
            n,
            salt,
            r,
            p,
            hash_,
        )  # type:ignore[str-bytes-safe]

    def encode(
        self, password: EncodingType, salt: EncodingSalt = None
    ) -> t.Union[str, t.Any]:
        salt = salt or self.get_salt()
        self._check_encode_args(password, salt)

        n = self.work_factor
        r = self.block_size
        p = self.parallelism
        return self._encode_action(password, n, r, p, salt)

    def decode(self, encoded: str) -> dict:
        algorithm, work_factor, salt, block_size, parallelism, hash_ = encoded.split(
            "$", 6
        )
        assert algorithm == self.algorithm
        return {
            "algorithm": algorithm,
            "work_factor": int(work_factor),
            "salt": salt,
            "block_size": int(block_size),
            "parallelism": int(parallelism),
            "hash": hash_,
        }

    def verify(self, secret: EncodingType, hash_secret: str) -> bool:
        decoded = self.decode(hash_secret)
        encoded_2 = self._encode_action(
            password=secret,
            salt=decoded["salt"],
            n=decoded["work_factor"],
            r=decoded["block_size"],
            p=decoded["parallelism"],
        )
        return secrets.compare_digest(hash_secret, encoded_2)

    def must_update(self, encoded: str) -> bool:
        decoded = self.decode(encoded)
        return (  # type: ignore[no-any-return]
            decoded["work_factor"] != self.work_factor
            or decoded["block_size"] != self.block_size
            or decoded["parallelism"] != self.parallelism
        )

    @classmethod
    def identity(cls, encoded: str) -> bool:
        algorithm = encoded.split("$", 1)[0]
        return algorithm == cls.algorithm
