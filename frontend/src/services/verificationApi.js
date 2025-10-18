/**
 * API client for advanced verification operations.
 */

const API_BASE = 'http://localhost:8000';

/**
 * Perform comprehensive verification of a poll.
 * 
 * @param {string} pollId - Poll identifier
 * @returns {Promise<Object>} Complete verification result
 */
export async function verifyPollComprehensive(pollId) {
  const response = await fetch(
    `${API_BASE}/polls/${pollId}/verification/comprehensive`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Verification failed');
  }

  return response.json();
}

/**
 * Get graph properties analysis.
 * 
 * @param {string} pollId - Poll identifier
 * @returns {Promise<Object>} Graph properties
 */
export async function getGraphProperties(pollId) {
  const response = await fetch(
    `${API_BASE}/polls/${pollId}/verification/graph-properties`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to get graph properties');
  }

  return response.json();
}

/**
 * Run Sybil attack detection.
 * 
 * @param {string} pollId - Poll identifier
 * @returns {Promise<Object>} Sybil detection results
 */
export async function detectSybilAttacks(pollId) {
  const response = await fetch(
    `${API_BASE}/polls/${pollId}/verification/sybil-detection`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to run Sybil detection');
  }

  return response.json();
}

/**
 * Validate all votes.
 * 
 * @param {string} pollId - Poll identifier
 * @returns {Promise<Object>} Vote validation results
 */
export async function validateVotes(pollId) {
  const response = await fetch(
    `${API_BASE}/polls/${pollId}/verification/vote-validation`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to validate votes');
  }

  return response.json();
}

/**
 * Get statistical analysis.
 * 
 * @param {string} pollId - Poll identifier
 * @returns {Promise<Object>} Statistical analysis
 */
export async function getStatisticalAnalysis(pollId) {
  const response = await fetch(
    `${API_BASE}/polls/${pollId}/verification/statistical-analysis`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to get statistical analysis');
  }

  return response.json();
}