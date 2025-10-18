/**
 * Service for managing PPE protocol on the client side.
 * 
 * Implements the symmetric CAPTCHA PPE protocol with commitment scheme.
 */

/**
 * Generate a random secret key for challenge generation.
 * 
 * @returns {string} Base64-encoded secret key
 */
export function generateSecret() {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode(...array));
}

/**
 * Generate a deterministic challenge from a secret and session ID.
 * 
 * @param {string} secret - Base64-encoded secret
 * @param {string} sessionId - Session identifier
 * @returns {Promise<{challengeText: string, solution: string}>}
 */
export async function generateChallengeWithSecret(secret, sessionId) {
  // Create deterministic seed
  const seedInput = `${secret}:${sessionId}`;
  const encoder = new TextEncoder();
  const data = encoder.encode(seedInput);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = new Uint8Array(hashBuffer);
  
  // Use hash as seed for random generation
  let seed = 0;
  for (let i = 0; i < 8; i++) {
    seed = (seed << 8) | hashArray[i];
  }
  
  // Simple seeded random generator
  const seededRandom = (function(s) {
    return function() {
      s = (s * 9301 + 49297) % 233280;
      return s / 233280;
    };
  })(seed);
  
  // Generate solution
  const chars = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789';
  let solution = '';
  for (let i = 0; i < 6; i++) {
    const index = Math.floor(seededRandom() * chars.length);
    solution += chars[index];
  }
  
  // Challenge text with spaces
  const challengeText = solution.split('').join(' ');
  
  return { challengeText, solution };
}

/**
 * Create a commitment to a solution.
 * 
 * @param {string} solution - The solution to commit to
 * @returns {Promise<{commitment: string, nonce: string}>}
 */
export async function createCommitment(solution) {
  // Generate nonce
  const nonceArray = new Uint8Array(16);
  crypto.getRandomValues(nonceArray);
  const nonce = btoa(String.fromCharCode(...nonceArray));
  
  // Create commitment: H(solution || nonce)
  const commitmentInput = `${solution.toLowerCase().trim()}:${nonce}`;
  const encoder = new TextEncoder();
  const data = encoder.encode(commitmentInput);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = new Uint8Array(hashBuffer);
  const commitment = Array.from(hashArray)
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
  
  return { commitment, nonce };
}

/**
 * Verify a commitment opening.
 * 
 * @param {string} solution - The revealed solution
 * @param {string} nonce - The revealed nonce
 * @param {string} expectedCommitment - The original commitment
 * @returns {Promise<boolean>}
 */
export async function verifyCommitment(solution, nonce, expectedCommitment) {
  // Recompute commitment
  const commitmentInput = `${solution.toLowerCase().trim()}:${nonce}`;
  const encoder = new TextEncoder();
  const data = encoder.encode(commitmentInput);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = new Uint8Array(hashBuffer);
  const computed = Array.from(hashArray)
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
  
  return computed === expectedCommitment;
}

/**
 * Verify that a challenge was generated correctly using a secret.
 * 
 * @param {string} secret - Base64-encoded secret
 * @param {string} sessionId - Session identifier
 * @param {string} solution - The solution that was committed to
 * @returns {Promise<boolean>}
 */
export async function verifyChallengeGeneration(secret, sessionId, solution) {
  const { solution: regenerated } = await generateChallengeWithSecret(secret, sessionId);
  return regenerated.toLowerCase() === solution.toLowerCase();
}

/**
 * Verify that a solution correctly solves a challenge.
 * 
 * @param {string} challengeText - The challenge text
 * @param {string} solution - The proposed solution
 * @returns {boolean}
 */
export function verifySolutionCorrectness(challengeText, solution) {
  const expected = challengeText.replace(/\s/g, '').toLowerCase().trim();
  const provided = solution.toLowerCase().trim();
  return expected === provided;
}

/**
 * Create a session ID for PPE between two users.
 * 
 * @param {string} user1Id - First user ID
 * @param {string} user2Id - Second user ID
 * @param {string} pollId - Poll ID
 * @returns {Promise<string>}
 */
export async function createPPESessionId(user1Id, user2Id, pollId) {
  // Sort user IDs
  const sorted = [user1Id, user2Id].sort();
  const sessionInput = `${pollId}:${sorted[0]}:${sorted[1]}`;
  
  const encoder = new TextEncoder();
  const data = encoder.encode(sessionInput);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = new Uint8Array(hashBuffer);
  
  // Take first 16 characters of hex
  return Array.from(hashArray.slice(0, 8))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}