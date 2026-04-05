import json
import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

KEY_FILE = "private_key.pem"


def _load_or_generate_key():
    """Load existing private key from disk, or generate and save a new one."""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return serialization.load_pem_private_key(f.read(), password=None)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with open(KEY_FILE, "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    return key


_private_key = _load_or_generate_key()
_public_key  = _private_key.public_key()

_PSS = padding.PSS(
    mgf=padding.MGF1(hashes.SHA256()),
    salt_length=padding.PSS.MAX_LENGTH,
)


def sign_payload(data: dict) -> tuple[str, str]:
    """Return (json_payload, hex_signature)."""
    payload = json.dumps(data, separators=(",", ":"), sort_keys=True)
    sig = _private_key.sign(payload.encode(), _PSS, hashes.SHA256())
    return payload, sig.hex()


def verify_payload(payload: str, signature_hex: str) -> bool:
    """Return True if signature is valid, False otherwise."""
    try:
        _public_key.verify(
            bytes.fromhex(signature_hex),
            payload.encode(),
            _PSS,
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False
