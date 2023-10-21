import pytest
import regex
from ellar.core.security.hashers import (
    _UNUSABLE_PASSWORD_PREFIX,
    _UNUSABLE_PASSWORD_SUFFIX_LENGTH,
    BaseHasher,
    BCryptHasher,
    BCryptSHA256Hasher,
    MD5Hasher,
    PBKDF2Hasher,
    PBKDF2SHA1Hasher,
    ScryptHasher,
    check_password,
    get_hasher,
    identify_hasher,
    is_password_usable,
    make_password,
)


class TestUtilsHashPass:
    def test_simple(self):
        encoded = make_password("lètmein")
        assert encoded.startswith("pbkdf2_sha256$") is True
        assert is_password_usable(encoded)
        assert check_password("lètmein", encoded) is True
        assert check_password("lètmeinz", encoded) is False
        # Blank passwords
        blank_encoded = make_password("")
        assert blank_encoded.startswith("pbkdf2_sha256$") is True
        assert is_password_usable(blank_encoded) is True
        assert check_password("", blank_encoded) is True
        assert check_password(" ", blank_encoded) is False

    def test_bytes(self):
        encoded = make_password(b"bytes_password")
        assert encoded.startswith("pbkdf2_sha256$") is True
        assert is_password_usable(encoded) is True
        assert check_password(b"bytes_password", encoded) is True

    def test_invalid_password(self):
        msg = "Password must be a string or bytes, got int."
        with pytest.raises(TypeError, match=msg):
            make_password(1)

    def test_check_password_invalid_hasher(self):
        encoded = make_password(
            "lètmein",
            "pbkdf2_sha256",
            "seasalt",
        )
        assert check_password("lètmein", f"asas+{encoded}") is False

    def test_pbkdf2(self):
        encoded = make_password(
            "lètmein",
            "pbkdf2_sha256",
            "seasalt",
        )
        assert (
            encoded
            == "pbkdf2_sha256$870000$seasalt$wJSpLMQRQz0Dhj/pFpbyjMj71B2gUYp6HJS5AU+32Ac="
        )

        assert is_password_usable(encoded) is True
        assert check_password("lètmein", encoded) is True
        assert check_password("lètmeinz", encoded) is False
        assert identify_hasher(encoded).algorithm == "pbkdf2_sha256"
        # Blank passwords
        blank_encoded = make_password("", "pbkdf2_sha256", "seasalt")
        assert blank_encoded.startswith("pbkdf2_sha256$") is True
        assert is_password_usable(blank_encoded) is True
        assert check_password("", blank_encoded) is True
        assert check_password(" ", blank_encoded) is False
        # Salt entropy check.
        hasher = get_hasher("pbkdf2_sha256")
        encoded_weak_salt = make_password("lètmein", "pbkdf2_sha256", "iodizedsalt")
        encoded_strong_salt = make_password("lètmein", "pbkdf2_sha256")
        assert hasher.must_update(encoded_weak_salt) is True
        assert hasher.must_update(encoded_strong_salt) is False

    def test_md5(self):
        encoded = make_password("lètmein", "md5", "seasalt")
        assert encoded == "md5$1$seasalt$Q3MX8tNkWyI.wLEm02R47."
        assert is_password_usable(encoded) is True
        assert check_password("lètmein", encoded) is True
        assert check_password("lètmeinz", encoded) is False
        assert identify_hasher(encoded).algorithm == "md5"
        # Blank passwords
        blank_encoded = make_password("", "md5", "seasalt")
        assert blank_encoded.startswith("md5$")
        assert is_password_usable(blank_encoded) is True
        assert check_password("", blank_encoded) is True
        assert check_password(" ", blank_encoded) is False
        # Salt entropy check.
        hasher = get_hasher("md5")
        encoded_weak_salt = make_password("lètmein", "md5", "iodize")
        encoded_strong_salt = make_password("lètmein", "md5")
        assert hasher.must_update(encoded_weak_salt) is True
        assert hasher.must_update(encoded_strong_salt) is False

    def test_bcrypt_sha256(self):
        encoded = make_password("lètmein", algorithm="bcrypt_sha256")
        assert is_password_usable(encoded) is True
        assert encoded.startswith("bcrypt_sha256$") is True
        assert check_password("lètmein", encoded) is True
        assert check_password("lètmeinz", encoded) is False
        assert identify_hasher(encoded).algorithm == "bcrypt_sha256"

        # password truncation no longer works
        password = (
            "VSK0UYV6FFQVZ0KG88DYN9WADAADZO1CTSIVDJUNZSUML6IBX7LN7ZS3R5"
            "JGB3RGZ7VI7G7DJQ9NI8BQFSRPTG6UWTTVESA5ZPUN"
        )
        encoded = make_password(password, algorithm="bcrypt_sha256")
        assert (
            check_password(password, encoded, preferred_algorithm="bcrypt_sha256")
            is True
        )
        assert check_password(password[:72], encoded) is False
        # Blank passwords
        blank_encoded = make_password("", algorithm="bcrypt_sha256")
        assert blank_encoded.startswith("bcrypt_sha256$")
        assert is_password_usable(blank_encoded) is True
        assert check_password("", blank_encoded) is True
        assert check_password(" ", blank_encoded) is False

    def test_bcrypt(self):
        encoded = make_password("lètmein", algorithm="bcrypt")
        assert is_password_usable(encoded) is True
        assert encoded.startswith("bcrypt$")
        assert check_password("lètmein", encoded) is True
        assert check_password("lètmeinz", encoded) is False
        assert identify_hasher(encoded).algorithm == "bcrypt"
        # Blank passwords
        blank_encoded = make_password("", algorithm="bcrypt")
        assert blank_encoded.startswith("bcrypt$") is True
        assert is_password_usable(blank_encoded) is True
        assert check_password("", blank_encoded) is True
        assert check_password(" ", blank_encoded) is False

    def test_bcrypt_upgrade(self):
        hasher = get_hasher("bcrypt")
        assert "bcrypt" == hasher.algorithm
        assert hasher.rounds != 4
        # Generate a password with 4 rounds.
        hasher.rounds = 4
        encoded = hasher.encode("letmein")
        rounds = hasher.decode(encoded)["work_factor"]
        assert rounds == 4

        state = {"upgraded": False}

        def setter(password):
            state["upgraded"] = True

        # No upgrade is triggered.
        assert check_password("letmein", encoded, setter, "bcrypt") is True
        assert state["upgraded"] is True

    def test_unusable(self):
        encoded = make_password(None)
        assert (
            len(encoded)
            == len(_UNUSABLE_PASSWORD_PREFIX) + _UNUSABLE_PASSWORD_SUFFIX_LENGTH
        )

        assert is_password_usable(encoded) is False
        assert check_password(None, encoded) is False
        assert check_password(encoded, encoded) is False
        assert check_password(_UNUSABLE_PASSWORD_PREFIX, encoded) is False
        assert check_password("", encoded) is False
        assert check_password("lètmein", encoded) is False
        assert check_password("lètmeinz", encoded) is False

        with pytest.raises(ValueError, match="Unable to identify Hasher"):
            identify_hasher(encoded)
        # Assert that the unusable passwords actually contain a random part.
        # This might fail one day due to a hash collision.
        assert encoded != make_password(None), "Random password collision?"

    def test_unspecified_password(self):
        """
        Makes sure specifying no plain password with a valid encoded password
        returns `False`.
        """
        assert check_password(None, make_password("lètmein")) is False

    def test_bad_algorithm(self):
        msg = (
            "Unknown password hashing algorithm 'lolcat'. "
            "Please use `add_hasher` in `ellar.core.security.hashers` package to add implementation for 'lolcat'"
        )
        with pytest.raises(ValueError, match=msg):
            make_password("lètmein", algorithm="lolcat")
        with pytest.raises(ValueError, match="Unable to identify Hasher"):
            identify_hasher("lolcat$salt$hash")

    @pytest.mark.parametrize("password", ("lètmein_badencoded", "", None))
    def test_is_password_usable(self, password):
        assert is_password_usable(password) is True

    def test_low_level_pbkdf2(self):
        hasher = PBKDF2Hasher()
        encoded = hasher.encode("lètmein", "seasalt2")
        assert (
            encoded
            == "pbkdf2_sha256$870000$seasalt2$nxgnNHRsZWSmi4hRSKq2MRigfaRmjDhH1NH4g2sQRbU="
        )
        assert hasher.verify("lètmein", encoded) is True

    def test_low_level_pbkdf2_sha1(self):
        hasher = PBKDF2SHA1Hasher()
        encoded = hasher.encode("lètmein", "seasalt2")
        assert encoded == "pbkdf2_sha1$870000$seasalt2$iFPKnrkYfxxyxaeIqxq+c3nJ/j4="
        assert hasher.verify("lètmein", encoded) is True

    def test_bcrypt_salt_check(self):
        hasher = BCryptHasher()
        encoded = hasher.encode("lètmein")
        assert hasher.must_update(encoded) is False

    def test_bcryptsha256_salt_check(self):
        hasher = BCryptSHA256Hasher()
        encoded = hasher.encode("lètmein")
        assert hasher.must_update(encoded) is False

    def test_no_upgrade(self):
        encoded = make_password("lètmein")
        state = {"upgraded": False}

        def setter():
            state["upgraded"] = True

        assert check_password("WRONG", encoded, setter) is False
        assert not state["upgraded"]

    def test_pbkdf2_upgrade(self):
        hasher = get_hasher()
        assert "pbkdf2_sha256" == hasher.algorithm
        assert hasher.iterations != 1

        # Generate a password with 1 iteration.
        hasher.iterations = 1
        encoded = hasher.encode("letmein")
        algo, iterations, salt, hash_ = encoded.split("$", 3)
        assert iterations == "1"

        state = {"upgraded": False}

        def setter(password):
            state["upgraded"] = True

        # No upgrade is triggered
        assert check_password("letmein", encoded, setter) is True
        assert state["upgraded"]

    @pytest.mark.parametrize(
        "hasher_class",
        [
            MD5Hasher,
            PBKDF2Hasher,
            PBKDF2SHA1Hasher,
            ScryptHasher,
        ],
    )
    def test_encode_invalid_salt(self, hasher_class):
        msg = "salt cannot contain $."
        hasher = hasher_class()
        with pytest.raises(ValueError, match=regex.escape(msg)):
            hasher.encode("password", "sea$salt")

    @pytest.mark.parametrize(
        "hasher_class",
        [
            MD5Hasher,
            PBKDF2Hasher,
            PBKDF2SHA1Hasher,
            ScryptHasher,
        ],
    )
    def test_encode_password_required(self, hasher_class):
        msg = "password must be provided."
        hasher = hasher_class()
        with pytest.raises(TypeError, match=regex.escape(msg)):
            hasher.encode(
                None,
            )

    def test_load_library_no_algorithm(self):
        class InvalidPasswordHasher(BaseHasher):
            def must_update(self, encoded: str) -> bool:
                pass

            def decode(self, encoded: str) -> dict:
                pass

        msg = "'InvalidPasswordHasher' doesn't specify a `hasher` attribute"
        with pytest.raises(ValueError, match=msg):
            InvalidPasswordHasher()


class TestUtilsHashPassArgon2:
    def test_argon2(self):
        encoded = make_password("lètmein", algorithm="argon2")
        assert is_password_usable(encoded)
        assert encoded.startswith("$argon2id$")
        assert check_password("lètmein", encoded)
        assert not check_password("lètmeinz", encoded)
        assert identify_hasher(encoded).algorithm == "argon2"
        # Blank passwords
        blank_encoded = make_password("", algorithm="argon2")
        assert blank_encoded.startswith("$argon2id$")
        assert is_password_usable(blank_encoded)
        assert check_password("", blank_encoded)
        assert not check_password(" ", blank_encoded)
        # Old hashes without version attribute
        encoded = (
            "$argon2i$m=8,t=1,p=1$c29tZXNhbHQ$gwQOXSNhxiOxPOA0+PY10P9QFO"
            "4NAYysnqRt1GSQLE55m+2GYDt9FEjPMHhP2Cuf0nOEXXMocVrsJAtNSsKyfg"
        )
        assert check_password("secret", encoded)
        assert not check_password("wrong", encoded)
        # Old hashes with version attribute.
        encoded = "$argon2i$v=19$m=8,t=1,p=1$c2FsdHNhbHQ$YC9+jJCrQhs5R6db7LlN8Q"
        assert check_password("secret", encoded)
        assert not check_password("wrong", encoded)
        # Salt entropy check.
        hasher = get_hasher("argon2")
        encoded_weak_salt = make_password("lètmein", "argon2", "iodizedsalt")
        encoded_strong_salt = make_password("lètmein", "argon2")
        assert hasher.must_update(encoded_weak_salt)
        assert not hasher.must_update(encoded_strong_salt)

    def test_argon2_decode(self):
        salt = "abcdefghijk"
        encoded = make_password("lètmein", salt=salt, algorithm="argon2")
        hasher = get_hasher("argon2")
        decoded = hasher.decode(encoded)

        assert decoded["memory_cost"] == hasher.memory_cost
        assert decoded["parallelism"] == hasher.parallelism
        assert decoded["salt"] == b"abcdefghijk"
        assert decoded["time_cost"] == hasher.time_cost

    def test_argon2_upgrade(self):
        self._test_argon2_upgrade("time_cost", "time cost", 1)
        self._test_argon2_upgrade("memory_cost", "memory cost", 64)
        self._test_argon2_upgrade("parallelism", "parallelism", 1)

    def test_argon2_version_upgrade(self):
        state = {"upgraded": False}
        encoded = (
            "$argon2id$v=19$m=102400,t=2,p=8$Y041dExhNkljRUUy$TMa6A8fPJh" "CAUXRhJXCXdw"
        )

        def setter(password):
            state["upgraded"] = True

        assert check_password("secret", encoded, setter, "argon2")
        assert state["upgraded"]

    def _test_argon2_upgrade(self, attr, summary_key, new_value):
        hasher = get_hasher("argon2")
        assert "argon2" == hasher.algorithm
        assert getattr(hasher, attr) != new_value

        # Generate hash with attr set to 1
        setattr(hasher, attr, new_value)
        encoded = hasher.encode("letmein")

        state = {"upgraded": False}

        def setter(password):
            state["upgraded"] = True

        # No upgrade is triggered.
        assert check_password("letmein", encoded, setter, "argon2")
        assert state["upgraded"]


class TestUtilsHashPassScrypt:
    def test_scrypt(self):
        encoded = make_password("lètmein", "scrypt", "seasalt")
        assert (
            encoded
            == "scrypt$16384$seasalt$8$1$Qj3+9PPyRjSJIebHnG81TMjsqtaIGxNQG/aEB/NY"
            "afTJ7tibgfYz71m0ldQESkXFRkdVCBhhY8mx7rQwite/Pw=="
        )
        assert is_password_usable(encoded)
        assert check_password("lètmein", encoded)
        assert not check_password("lètmeinz", encoded)
        assert identify_hasher(encoded).algorithm == "scrypt"
        # Blank passwords.
        blank_encoded = make_password("", "scrypt", "seasalt")
        assert blank_encoded.startswith("scrypt$")
        assert is_password_usable(blank_encoded)
        assert check_password("", blank_encoded)
        assert not check_password(" ", blank_encoded)

    encoded_for_test_scrypt_decode = make_password("lètmein", "scrypt", "seasalt")

    @pytest.mark.parametrize(
        "key, value",
        [
            ("block_size", ScryptHasher.block_size),
            ("parallelism", ScryptHasher.parallelism),
            ("salt", "seasalt"),
            ("work_factor", ScryptHasher.work_factor),
        ],
    )
    def test_scrypt_decode(self, key, value):
        hasher = get_hasher("scrypt")
        decoded = hasher.decode(self.encoded_for_test_scrypt_decode)
        assert decoded[key] == value

    def _test_scrypt_upgrade(self, attr, summary_key, new_value):
        hasher = get_hasher("scrypt")
        assert hasher.algorithm == "scrypt"
        assert getattr(hasher, attr) != new_value

        getattr(hasher, attr)
        # Generate hash with attr set to the new value.
        setattr(hasher, attr, new_value)
        encoded = hasher.encode("lètmein", "seasalt")

        state = {"upgraded": False}

        def setter(password):
            state["upgraded"] = True

        # No update is triggered.
        assert check_password("lètmein", encoded, setter, "scrypt")
        assert state["upgraded"]

    @pytest.mark.parametrize(
        "attr, summary_key, new_value",
        [
            ("work_factor", "work factor", 2**11),
            ("block_size", "block size", 10),
            ("parallelism", "parallelism", 2),
        ],
    )
    def test_scrypt_upgrade(self, attr, summary_key, new_value):
        self._test_scrypt_upgrade(attr, summary_key, new_value)
