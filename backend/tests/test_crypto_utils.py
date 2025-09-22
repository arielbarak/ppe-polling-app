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
    """Test digital signature verification with both DER and raw formats.
    
    This test validates that the verify_signature function correctly verifies
    signatures in both DER (Distinguished Encoding Rules) format and raw format.
    It creates a test key pair, signs a message, and verifies the signature in
    both formats.
    
    The test:
    1. Generates an EC private/public key pair
    2. Signs a test message with the private key
    3. Verifies the signature using the public key in JWK format
    4. Tests both DER-encoded and raw signature formats
    
    Returns:
        None
        
    Raises:
        AssertionError: If signature verification fails for either format.
    """
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
    """Test that invalid signatures are properly rejected.
    
    This test verifies that the verify_signature function correctly returns
    False when an invalid signature is provided. It tests with a signature
    that doesn't match the message being verified.
    
    The test:
    1. Generates an EC private/public key pair
    2. Signs a test message with the private key
    3. Attempts to verify a different message with the same signature
    4. Confirms that verification fails (returns False)
    
    Returns:
        None
        
    Raises:
        AssertionError: If invalid signatures are not properly rejected.
    """
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
    
    # Also test with wrong message
    assert verify_signature(jwk, "wrong-message", der_sig.hex()) is False


def test_verify_signature_exception_handling():
    """Test that exceptions during signature verification are properly handled.
    
    This test verifies that the verify_signature function gracefully handles
    various error conditions and returns False instead of raising exceptions.
    It tests several error scenarios:
    
    1. Invalid JWK format for the public key
    2. Non-hexadecimal signature string
    3. Signature that's too short to be valid
    
    For all these cases, the function should return False rather than raising
    an exception, ensuring robust error handling in the application.
    
    Returns:
        None
        
    Raises:
        AssertionError: If exceptions are not properly handled.
    """
    # Invalid public key format
    invalid_jwk = {"kty": "EC", "crv": "P-256", "x": "invalid-x", "y": "invalid-y"}
    
    # This should return False due to exception handling in verify_signature
    assert verify_signature(invalid_jwk, "message", "00" * 32) is False
    
    # Test with invalid hex string
    valid_private_key = ec.generate_private_key(ec.SECP256R1())
    valid_jwk = make_jwk_from_public_key(valid_private_key.public_key())
    
    # Invalid hex string (not hex characters)
    assert verify_signature(valid_jwk, "message", "not-a-hex-string") is False
    
    # Too short signature
    assert verify_signature(valid_jwk, "message", "aabb") is False
