import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from cryptography.exceptions import InvalidSignature
import jwt

def verify_signature(public_key_jwk: dict, message: str, signature_hex: str) -> bool:
    """
    Verifies an ECDSA signature from the Web Crypto API.
    It handles the conversion from the raw signature format (r||s) to the
    DER format expected by the cryptography library.
    """
    try:
        public_key = jwt.algorithms.ECAlgorithm.from_jwk(json.dumps(public_key_jwk))
        signature_bytes_raw = bytes.fromhex(signature_hex)
        message_bytes = message.encode('utf-8')

        # The Web Crypto API returns a raw signature (a concatenation of r and s).
        # The 'cryptography' library's default verify function expects a
        # DER-encoded signature. We must convert it.
        # For the P-256 curve, r and s are 32 bytes each, making the raw signature 64 bytes.
        if len(signature_bytes_raw) != 64:
            print(f"Invalid signature length: expected 64, got {len(signature_bytes_raw)}")
            return False

        # Split the raw signature into r and s
        r = int.from_bytes(signature_bytes_raw[:32], 'big')
        s = int.from_bytes(signature_bytes_raw[32:], 'big')

        # Encode r and s into the DER format that the verify() function expects
        der_signature = encode_dss_signature(r, s)

        # Perform the verification with the correctly formatted signature
        public_key.verify(
            der_signature,
            message_bytes,
            ec.ECDSA(hashes.SHA256())
        )
        print("Signature verified successfully.")
        return True
    except InvalidSignature:
        print("Signature verification failed: Invalid signature.")
        return False
    except Exception as e:
        print(f"An error occurred during signature verification: {e}")
        return False
