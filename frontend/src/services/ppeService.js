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

/**
 * Enhanced PPE API functions for multiple PPE types
 */

const API_BASE = process.env.REACT_APP_API_URL || '';

/**
 * Get available PPE types for a poll.
 * 
 * @param {string} pollId - Poll identifier
 * @returns {Promise<Object>} Available PPE types and configuration
 */
export async function getAvailableTypes(pollId) {
  const response = await fetch(`${API_BASE}/api/ppe/available-types/${pollId}`);
  if (!response.ok) {
    throw new Error(`Failed to get PPE types: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Initiate a new PPE execution.
 * 
 * @param {Object} request - PPE initiation request
 * @param {string} request.poll_id - Poll ID
 * @param {string} request.prover_id - Prover user ID
 * @param {string} request.verifier_id - Verifier user ID
 * @param {string} [request.ppe_type] - PPE type (optional, uses default if not specified)
 * @returns {Promise<Object>} PPE execution details
 */
export async function initiatePPE(request) {
  const response = await fetch(`${API_BASE}/api/ppe/initiate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to initiate PPE: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Submit a response to a PPE challenge.
 * 
 * @param {string} executionId - PPE execution ID
 * @param {Object} response - Response data (varies by PPE type)
 * @returns {Promise<Object>} Submission result
 */
export async function submitResponse(executionId, response) {
  const apiResponse = await fetch(`${API_BASE}/api/ppe/submit/${executionId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(response),
  });
  
  if (!apiResponse.ok) {
    throw new Error(`Failed to submit PPE response: ${apiResponse.statusText}`);
  }
  
  return apiResponse.json();
}

/**
 * Get the status of a PPE execution.
 * 
 * @param {string} executionId - PPE execution ID
 * @returns {Promise<Object>} Execution status
 */
export async function getStatus(executionId) {
  const response = await fetch(`${API_BASE}/api/ppe/status/${executionId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to get PPE status: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get all active PPEs for a user in a poll.
 * 
 * @param {string} pollId - Poll ID
 * @param {string} userId - User ID
 * @returns {Promise<Object>} Active PPEs
 */
export async function getActivePPEs(pollId, userId) {
  const response = await fetch(`${API_BASE}/api/ppe/active/${pollId}/${userId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to get active PPEs: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get PPE configuration for a poll.
 * 
 * @param {string} pollId - Poll ID
 * @returns {Promise<Object>} PPE configuration
 */
export async function getPPEConfig(pollId) {
  const response = await fetch(`${API_BASE}/api/ppe/config/${pollId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to get PPE config: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * List all available PPE types with descriptions.
 * 
 * @returns {Promise<Object>} PPE types information
 */
export async function listAllPPETypes() {
  const response = await fetch(`${API_BASE}/api/ppe/types`);
  
  if (!response.ok) {
    throw new Error(`Failed to list PPE types: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Clean up expired PPE executions for a poll.
 * 
 * @param {string} pollId - Poll ID
 * @returns {Promise<Object>} Cleanup result
 */
export async function cleanupExpiredPPEs(pollId) {
  const response = await fetch(`${API_BASE}/api/ppe/cleanup/${pollId}`, {
    method: 'POST'
  });
  
  if (!response.ok) {
    throw new Error(`Failed to cleanup PPEs: ${response.statusText}`);
  }
  
  return response.json();
}

// Export as default object for backwards compatibility
export const ppeService = {
  // Legacy functions
  generateSecret,
  generateChallengeWithSecret,
  createCommitment,
  verifyCommitment,
  verifyChallengeGeneration,
  verifySolutionCorrectness,
  createPPESessionId,
  
  // New API functions
  getAvailableTypes,
  initiatePPE,
  submitResponse,
  getStatus,
  getActivePPEs,
  getPPEConfig,
  listAllPPETypes,
  cleanupExpiredPPEs
};