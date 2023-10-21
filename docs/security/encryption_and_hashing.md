# **Encryption and Hashing**

**Encryption** is the method of transforming data. This process changes the original information, referred to as plaintext, 
into an alternative form called ciphertext. 
The goal is to ensure that only authorized parties possess the capability to decrypt ciphertext back into plaintext and access the original information. 
Encryption doesn't inherently prevent interference but rather restricts the intelligible content from potential interceptors. 
Encryption is a bidirectional operation; what's encrypted can be decrypted using the correct key.

**Hashing** is the process of converting a given key into another value. 
A hash function is employed to create this new value following a mathematical algorithm. 
After hashing is applied, it should be practically impossible to reverse the process and derive the original 
input from the output.

## **Encryption**
In Python, the [`cryptography`](https://pypi.org/project/cryptography/) library provides a user-friendly way to implement encryption. 
One common encryption scheme is Fernet, which offers symmetric key encryption.

For example,
```python
from cryptography.fernet import Fernet

# Generate a random encryption key
key = Fernet.generate_key()

# Create a Fernet cipher object with the key
cipher_suite = Fernet(key)

# Text to be encrypted
plaintext = b"Hello, this is a secret message!"

# Encrypt the plaintext
cipher_text = cipher_suite.encrypt(plaintext)

# Decrypt the ciphertext
decrypted_text = cipher_suite.decrypt(cipher_text)

# Convert bytes to string for printing
original_message = decrypted_text.decode("utf-8")

print("Original Message: ", plaintext)
print("Encrypted Message: ", cipher_text)
print("Decrypted Message: ", original_message)

```
The provided Python example demonstrates this process, securing a message with encryption and then decrypting it using the same key. 
It's crucial to manage encryption keys securely in real applications to maintain the confidentiality and integrity of your data.

## **Hashing**
For hashing, Ellar works with [passlib](https://pypi.org/project/passlib/) and [hashlib](https://docs.python.org/3/library/hashlib.html)
to create a wrapper around some hashing algorithms listed below,

- **PBKDF2Hasher**: `pbkdf2_sha256` hashing algorithm wrapper
- **PBKDF2SHA1Hasher**: `pbkdf2_sha1` hashing algorithm wrapper
- **Argon2Hasher**: `argon2` hashing algorithm wrapper
- **BCryptSHA256Hasher**: `bcrypt_sha256` hashing algorithm wrapper
- **BCryptHasher**: `bcrypt` hashing algorithm wrapper
- **ScryptHasher**: `scrypt` hashing algorithm wrapper
- **MD5Hasher**: `md5` hashing algorithm wrapper

## **Password Hashing**
Ellar provides two important utility functions: `make_password` for password hashing 
and `check_password` for password validation. Both of these functions are available in the 
`ellar.core.security.hashers` package.

```python
def make_password(
    password: str|bytes,
    algorithm: str = "pbkdf2_sha256",
    salt: str|None = None,
) -> str:
    pass


def check_password(
    password: str|bytes,
    encoded: str,
    setter: Callable[..., Any]|None = None,
    preferred_algorithm: str = "pbkdf2_sha256",
) -> bool:
    pass
```

The `make_password` function takes plain text and generates a hashed result based on the provided hash algorithm. 
In the code snippet above, the default algorithm for `make_password` is `pbkdf2_sha256`.

The [PBKDF2](https://en.wikipedia.org/wiki/PBKDF2) algorithm with a SHA256 hash is a password stretching mechanism recommended by [NIST](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-132.pdf).
This should be sufficient for most users as it is quite secure and requires massive amounts of computing time to break.

!!! note
    All hashing wrappers are registered as `key-value` pairs and can be accessed by the algorithm names
    using the get_hasher utility function in the `ellar.core.security.hashers` package.

For an example,
```python
from ellar.core.security.hashers import make_password

## Using pbkdf2_sha256 - PBKDF2Hasher
password_hash = make_password('mypassword1234', algorithm="pbkdf2_sha256", salt='seasalt')
print(password_hash)
# pbkdf2_sha256$870000$seasalt$XE8bb8u57rxvyv2SThRFtMg9mzJLff2wjm3J8kGgFVI=

## Using bcrypt_sha256 - BCryptSHA256Hasher
password_hash = make_password('mypassword1234', algorithm="bcrypt_sha256", salt='20AmWL1wKJZAHPiI1HEk4k')
print(password_hash)
# bcrypt_sha256$$2b$12$20AmWL1wKJZAHPiI1HEk4eZuAlMGHkK1rw4oou26bnwGmAE8F0JGK
```

On the other hand, you can check or validate a password using the `check_password` function.

```python
from ellar.core.security.hashers import check_password

hash_secret = "bcrypt_sha256$$2b$12$20AmWL1wKJZAHPiI1HEk4eZuAlMGHkK1rw4oou26bnwGmAE8F0JGK"
assert check_password('mypassword1234', hash_secret) # True
```
