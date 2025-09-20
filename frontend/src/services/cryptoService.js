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

/**
 * Encrypts text using AES-GCM with a password-derived key
 * @param {string} text - The text to encrypt
 * @param {string} password - The password to derive the key from
 * @returns {Promise<string>} Base64 encoded encrypted data with IV
 */
const encryptText = async (text, password) => {
  try {
    // Convert password to key using PBKDF2
    const encoder = new TextEncoder();
    const passwordBuffer = encoder.encode(password);
    
    // Generate a random salt
    const salt = window.crypto.getRandomValues(new Uint8Array(16));
    
    // Import password as key material
    const keyMaterial = await window.crypto.subtle.importKey(
      'raw',
      passwordBuffer,
      { name: 'PBKDF2' },
      false,
      ['deriveKey']
    );
    
    // Derive AES key from password
    const key = await window.crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: salt,
        iterations: 100000,
        hash: 'SHA-256'
      },
      keyMaterial,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt']
    );
    
    // Generate random IV
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    
    // Encrypt the text
    const encodedText = encoder.encode(text);
    const encryptedBuffer = await window.crypto.subtle.encrypt(
      {
        name: 'AES-GCM',
        iv: iv
      },
      key,
      encodedText
    );
    
    // Combine salt + iv + encrypted data
    const combined = new Uint8Array(salt.length + iv.length + encryptedBuffer.byteLength);
    combined.set(salt, 0);
    combined.set(iv, salt.length);
    combined.set(new Uint8Array(encryptedBuffer), salt.length + iv.length);
    
    // Return base64 encoded result
    return btoa(String.fromCharCode(...combined));
  } catch (error) {
    console.error('Error encrypting text:', error);
    throw error;
  }
};

/**
 * Decrypts text using AES-GCM with a password-derived key
 * @param {string} encryptedData - Base64 encoded encrypted data
 * @param {string} password - The password to derive the key from
 * @returns {Promise<string>} The decrypted text
 */
const decryptText = async (encryptedData, password) => {
  try {
    // Convert from base64
    const combined = new Uint8Array(atob(encryptedData).split('').map(c => c.charCodeAt(0)));
    
    // Extract components
    const salt = combined.slice(0, 16);
    const iv = combined.slice(16, 28);
    const encrypted = combined.slice(28);
    
    // Convert password to key using PBKDF2
    const encoder = new TextEncoder();
    const passwordBuffer = encoder.encode(password);
    
    // Import password as key material
    const keyMaterial = await window.crypto.subtle.importKey(
      'raw',
      passwordBuffer,
      { name: 'PBKDF2' },
      false,
      ['deriveKey']
    );
    
    // Derive AES key from password
    const key = await window.crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: salt,
        iterations: 100000,
        hash: 'SHA-256'
      },
      keyMaterial,
      { name: 'AES-GCM', length: 256 },
      false,
      ['decrypt']
    );
    
    // Decrypt the data
    const decryptedBuffer = await window.crypto.subtle.decrypt(
      {
        name: 'AES-GCM',
        iv: iv
      },
      key,
      encrypted
    );
    
    // Convert back to text
    const decoder = new TextDecoder();
    return decoder.decode(decryptedBuffer);
  } catch (error) {
    console.error('Error decrypting text:', error);
    throw error;
  }
};

// Export all the functions so other parts of our app can use them
export const cryptoService = {
  generateKeys,
  saveKeys,
  loadKeys,
  getPublicKeyAsJwk,
  signMessage,
  encryptText,
  decryptText
};
