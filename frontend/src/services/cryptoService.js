const KEY_PAIR_STORAGE_KEY = 'ppe-key-pair';

/**
 * Generates a new ECDSA key pair for signing.
 * @returns {Promise<CryptoKeyPair>} A promise that resolves to the generated key pair.
 */
const generateKeys = async () => {
  try {
    const keyPair = await window.crypto.subtle.generateKey(
      {
        name: 'ECDSA',
        namedCurve: 'P-256', // A standard, widely supported curve
      },
      true, // The key is extractable (so we can save it)
      ['sign', 'verify'] // The key can be used for signing and verification
    );
    return keyPair;
  } catch (error) {
    console.error('Error generating keys:', error);
    throw error;
  }
};

/**
 * Saves the key pair to the browser's localStorage.
 * NOTE: localStorage is simple, but for a real-world app, IndexedDB is more secure.
 * @param {CryptoKeyPair} keyPair - The key pair to save.
 */
const saveKeys = async (keyPair) => {
  try {
    // Export the private and public keys in JWK (JSON Web Key) format
    const privateKeyJwk = await window.crypto.subtle.exportKey('jwk', keyPair.privateKey);
    const publicKeyJwk = await window.crypto.subtle.exportKey('jwk', keyPair.publicKey);

    const keys = {
      privateKey: privateKeyJwk,
      publicKey: publicKeyJwk,
    };

    // Store the JSON string in localStorage
    localStorage.setItem(KEY_PAIR_STORAGE_KEY, JSON.stringify(keys));
    console.log('Keys saved to localStorage.');
  } catch (error) {
    console.error('Error saving keys:', error);
  }
};

/**
 * Loads the key pair from localStorage.
 * @returns {Promise<CryptoKeyPair|null>} A promise that resolves to the imported key pair, or null if not found.
 */
const loadKeys = async () => {
  const storedKeys = localStorage.getItem(KEY_PAIR_STORAGE_KEY);
  if (!storedKeys) {
    console.log('No keys found in localStorage.');
    return null;
  }

  try {
    const keys = JSON.parse(storedKeys);
    // Import the keys back into a CryptoKeyPair object
    const keyPair = {
      privateKey: await window.crypto.subtle.importKey(
        'jwk',
        keys.privateKey,
        { name: 'ECDSA', namedCurve: 'P-256' },
        true,
        ['sign']
      ),
      publicKey: await window.crypto.subtle.importKey(
        'jwk',
        keys.publicKey,
        { name: 'ECDSA', namedCurve: 'P-256' },
        true,
        ['verify']
      ),
    };
    console.log('Keys loaded from localStorage.');
    return keyPair;
  } catch (error) {
    console.error('Error loading keys:', error);
    return null;
  }
};

/**
 * Gets the public key in a simple, exportable format.
 * @param {CryptoKey} publicKey - The public key part of the CryptoKeyPair.
 * @returns {Promise<Object>} A promise that resolves to the JWK representation of the public key.
 */
const getPublicKeyAsJwk = async (publicKey) => {
    if (!publicKey) return null;
    return await window.crypto.subtle.exportKey('jwk', publicKey);
};

/**
 * Signs a message with the user's private key.
 * @param {CryptoKey} privateKey - The private key to sign with.
 * @param {string} message - The message to sign.
 * @returns {Promise<string>} The signature in hexadecimal format.
 */
const signMessage = async (privateKey, message) => {
  if (!privateKey) throw new Error("Private key is not available for signing.");
  const encodedMessage = new TextEncoder().encode(message);
  const signature = await window.crypto.subtle.sign(
    {
      name: 'ECDSA',
      hash: { name: 'SHA-256' },
    },
    privateKey,
    encodedMessage
  );
  // Convert the signature ArrayBuffer to a hex string for easy transport
  return Array.from(new Uint8Array(signature)).map(b => b.toString(16).padStart(2, '0')).join('');
};

// Export all the functions so other parts of our app can use them
export const cryptoService = {
  generateKeys,
  saveKeys,
  loadKeys,
  getPublicKeyAsJwk,
  signMessage, // Add the new function to the export
};
