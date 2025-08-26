import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from cryptography.exceptions import InvalidSignature
import jwt

def verify_signature(public_key_jwk: dict, message: str, signature_hex: str) -> bool:
    """
    Verifies an ECDSA signature from the Web Crypto API.
    It handles both raw signature format (r||s) and DER-encoded signatures.
    """
    try:
        public_key = jwt.algorithms.ECAlgorithm.from_jwk(json.dumps(public_key_jwk))
        signature_bytes = bytes.fromhex(signature_hex)
        message_bytes = message.encode('utf-8')

        # Accept either raw (r||s) 64-byte signatures for P-256 or DER-encoded signatures
        if len(signature_bytes) == 64:
            r = int.from_bytes(signature_bytes[:32], 'big')
            s = int.from_bytes(signature_bytes[32:], 'big')
            der_signature = encode_dss_signature(r, s)
        else:
            der_signature = signature_bytes

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
