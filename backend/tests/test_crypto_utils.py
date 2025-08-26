import sys
import os
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

# Ensure the package root is on sys.path so imports work when pytest runs this file
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Provide a minimal 'jwt' module so crypto_utils can call jwt.algorithms.ECAlgorithm.from_jwk
import types
import json as _json

def _b64url_to_int(s: str) -> int:
    # Add padding and decode
    padding = '=' * (-len(s) % 4)
    raw = base64.urlsafe_b64decode(s + padding)
    return int.from_bytes(raw, 'big')

class _FakeECAlgorithm:
    @staticmethod
    def from_jwk(jwk_json: str):
        jwk = _json.loads(jwk_json)
        x = _b64url_to_int(jwk['x'])
        y = _b64url_to_int(jwk['y'])
        nums = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1())
        return nums.public_key()

fake_jwt = types.ModuleType('jwt')
fake_jwt.algorithms = types.SimpleNamespace(ECAlgorithm=_FakeECAlgorithm)
sys.modules['jwt'] = fake_jwt

from app.utils.crypto_utils import verify_signature


def int_to_base64url(n: int, length: int = 32) -> str:
    b = n.to_bytes(length, 'big')
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode('ascii')


def make_jwk_from_public_key(public_key: ec.EllipticCurvePublicKey) -> dict:
    numbers = public_key.public_numbers()
    return {
        "kty": "EC",
        "crv": "P-256",
        "x": int_to_base64url(numbers.x, 32),
        "y": int_to_base64url(numbers.y, 32),
    }


def test_verify_signature_der_and_raw():
    # Generate a fresh P-256 keypair
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    jwk = make_jwk_from_public_key(public_key)

    message = "test-message"
    message_bytes = message.encode('utf-8')

    # Create a DER-encoded signature (what cryptography.sign returns)
    der_sig = private_key.sign(message_bytes, ec.ECDSA(hashes.SHA256()))
    der_hex = der_sig.hex()

    assert verify_signature(jwk, message, der_hex) is True

    # Create a raw (r||s) 64-byte signature like Web Crypto's output
    r, s = decode_dss_signature(der_sig)
    r_bytes = r.to_bytes(32, 'big')
    s_bytes = s.to_bytes(32, 'big')
    raw_sig = r_bytes + s_bytes
    raw_hex = raw_sig.hex()

    assert verify_signature(jwk, message, raw_hex) is True


def test_verify_signature_invalid_returns_false():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    jwk = make_jwk_from_public_key(public_key)

    message = "another-message"
    message_bytes = message.encode('utf-8')
    der_sig = private_key.sign(message_bytes, ec.ECDSA(hashes.SHA256()))

    # Tamper with the signature: flip a byte
    tampered = bytearray(der_sig)
    tampered[10] ^= 0xFF
    tampered_hex = bytes(tampered).hex()

    assert verify_signature(jwk, message, tampered_hex) is False
