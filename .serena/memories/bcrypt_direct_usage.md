# bcrypt Direct Usage (No passlib)

## Important Note

This project uses **bcrypt directly** instead of passlib due to compatibility issues between passlib and bcrypt 5.0+.

## Why?

passlib has compatibility issues with bcrypt 5.0+ that cause:
- `AttributeError: module 'bcrypt' has no attribute '__about__'`
- `ValueError: password cannot be longer than 72 bytes`

## Implementation

We use bcrypt directly:

```python
import bcrypt

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")\ndef verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_bytes = plain_password.encode("utf-8")
    hash_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(plain_bytes, hash_bytes)
```

## Dependencies

```toml
dependencies = [
    "bcrypt>=4.0.0",
]
```

## Security Notes

- bcrypt automatically handles salts
- bcrypt has 72-byte input limit
- bcrypt uses adaptive hashing
- Default work factor: 12
