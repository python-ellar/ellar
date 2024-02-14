import typing as t

from ellar.utils.crypto import must_update_salt
from passlib.hash import argon2

from .base import BaseHasher, EncodingSalt, EncodingType


class Argon2Hasher(BaseHasher):
    """
    Secure password hashing using the argon2 algorithm.

    This is the winner of the Password Hashing Competition 2013-2015
    (https://password-hashing.net). It requires the argon2-cffi library which
    depends on native C code and might cause portability issues.
    """

    algorithm = "argon2"
    hasher = argon2

    time_cost = 2
    memory_cost = argon2.memory_cost
    parallelism = argon2.parallelism

    def _get_using_kwargs(self) -> dict:
        return {
            "time_cost": self.time_cost,
            "memory_cost": self.memory_cost,
            "parallelism": self.parallelism,
        }

    def encode(
        self, password: EncodingType, salt: EncodingSalt = None
    ) -> t.Union[str, t.Any]:
        salt = bytes(salt, "utf-8") if salt else salt  # type:ignore[arg-type]
        return super().encode(password, salt)

    def decode(self, encoded: str) -> dict:
        argon_2 = t.cast(t.Any, self.hasher.from_string(encoded))
        return {
            "algorithm": self.algorithm,
            "memory_cost": argon_2.memory_cost,
            "parallelism": argon_2.parallelism,
            "salt": argon_2.salt,
            "time_cost": argon_2.rounds,
            "hash": argon_2.data,
        }

    def must_update(self, encoded: str) -> bool:
        decoded = self.decode(encoded)

        update_salt = must_update_salt(decoded["salt"], self.salt_entropy)
        if update_salt:
            return update_salt

        if decoded["time_cost"] != self.time_cost:
            return True
        return self.hasher.needs_update(encoded)  # type:ignore[no-any-return]
