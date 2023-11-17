import math
import secrets

RANDOM_STRING_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def must_update_salt(salt: str, expected_entropy: int) -> bool:
    # Each character in the salt provides log_2(len(alphabet)) bits of entropy.
    return len(salt) * math.log2(len(RANDOM_STRING_CHARS)) < expected_entropy


def get_random_string(length: int, allowed_chars: str = RANDOM_STRING_CHARS) -> str:
    """
    Return a securely generated random string.

    The bit length of the returned value can be calculated with the formula:
        log_2(len(allowed_chars)^length)

    For example, with default `allowed_chars` (26+26+10), this gives:
      * length: 12, bit length =~ 71 bits
      * length: 22, bit length =~ 131 bits
    """
    return "".join(
        secrets.choice(allowed_chars) for _ in range(length)
    )  # pragma no cover
