import math
import typing as t
from abc import ABC, abstractmethod

import passlib.utils.handlers as uh
from ellar.utils.crypto import RANDOM_STRING_CHARS, get_random_string

# This will never be a valid encoded hash
UNUSABLE_PASSWORD_PREFIX = "!"
UNUSABLE_PASSWORD_SUFFIX_LENGTH = (
    40  # number of random chars to add after UNUSABLE_PASSWORD_PREFIX
)

__HASHERS_DICT: t.Dict[str, t.Type["BaseHasher"]] = {}
EncodingType = t.Union[str, bytes]
EncodingSalt = t.Optional[t.Union[str, bytes]]


class BaseHasher(ABC):
    hasher: t.Union[t.Type[uh.GenericHandler], t.Any]
    algorithm: str
    salt_entropy: int = 128

    def __init__(self) -> None:
        if not hasattr(self, "hasher"):
            raise ValueError(
                f"'{self.__class__.__name__}' doesn't specify a `hasher` attribute"
            )

    def _get_using_kwargs(self) -> dict:
        return {}

    def encode(
        self, password: EncodingType, salt: EncodingSalt = None
    ) -> t.Union[str, t.Any]:
        self._check_encode_args(password, salt)
        default_salt_size = math.ceil(
            self.salt_entropy / math.log2(len(RANDOM_STRING_CHARS))
        )
        using_kw = {"default_salt_size": default_salt_size, "salt": salt}
        using_kw.update(self._get_using_kwargs())
        return self.hasher.using(**using_kw).hash(password)

    def _check_encode_args(self, password: EncodingType, salt: EncodingSalt) -> None:
        if password is None:
            raise TypeError("password must be provided.")
        if not isinstance(salt, bytes) and salt and "$" in salt:
            raise ValueError("salt cannot contain $.")

    @abstractmethod
    def decode(self, encoded: str) -> dict:
        """
        Return a decoded database value.

        The result is a dictionary and should contain `algorithm`, `hash`, and
        `salt`. Extra keys can be algorithm specific like `iterations` or
        `work_factor`.
        """
        pass

    def verify(self, secret: EncodingType, hash_secret: str) -> bool:
        """
        verify secret against an existing hash
        """
        return self.hasher.verify(  # type:ignore[no-any-return]
            secret, hash_secret
        )

    @abstractmethod
    def must_update(self, encoded: str) -> bool:
        """Checks if a hash needs to be updated

        if you using passlib hash, simple call hasher.need_update(encoded)
        """
        pass

    @classmethod
    def identity(cls, encoded: str) -> bool:
        return cls.hasher.identify(encoded)  # type: ignore[no-any-return]

    def get_salt(self) -> str:
        """
        Generate a cryptographically secure nonce salt in ASCII with an entropy
        of at least `salt_entropy` bits.
        """
        # Each character in the salt provides
        # log_2(len(alphabet)) bits of entropy.

        char_count = math.ceil(self.salt_entropy / math.log2(len(RANDOM_STRING_CHARS)))
        return get_random_string(char_count, allowed_chars=RANDOM_STRING_CHARS)
