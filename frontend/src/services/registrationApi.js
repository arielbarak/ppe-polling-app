/**
 * API client for registration with initial PPE challenges.
 */

const API_BASE = 'http://localhost:8000';

/**
 * Request a registration challenge for a poll.
 * 
 * @param {string} pollId - Poll identifier
 * @param {string} difficulty - Challenge difficulty ('easy', 'medium', 'hard')
 * @returns {Promise<Object>} Challenge data with challenge_id and challenge_text
 */
export async function requestChallenge(pollId, difficulty = 'medium') {
  const response = await fetch(`${API_BASE}/registration/challenge`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      poll_id: pollId,
      difficulty: difficulty,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to request challenge');
  }

  const data = await response.json();
  return data.challenge;
}

/**
 * Validate a challenge solution.
 * 
 * @param {string} challengeId - Challenge identifier
 * @param {string} solution - User's solution
 * @returns {Promise<Object>} Validation result
 */
export async function validateChallenge(challengeId, solution) {
  const response = await fetch(`${API_BASE}/registration/validate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      challenge_id: challengeId,
      solution: solution,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to validate challenge');
  }

  return response.json();
}

/**
 * Register for a poll with challenge solution.
 * 
 * @param {string} pollId - Poll identifier
 * @param {Object} publicKey - User's public key (JWK format)
 * @param {string} challengeId - Challenge identifier
 * @param {string} solution - Challenge solution
 * @returns {Promise<Object>} Updated poll data
 */
export async function registerWithChallenge(pollId, publicKey, challengeId, solution) {
  const response = await fetch(`${API_BASE}/polls/${pollId}/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      public_key: publicKey,
      challenge_id: challengeId,
      challenge_solution: solution,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }

  return response.json();
}