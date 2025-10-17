/**
 * API client for ideal certification graph operations.
 */

const API_BASE = 'http://localhost:8000';

/**
 * Generate or retrieve the ideal graph for a poll.
 * 
 * @param {string} pollId - Poll identifier
 * @param {number} k - Desired degree (default 3)
 * @returns {Promise<Object>} Graph properties and metrics
 */
export async function generateGraph(pollId, k = 3) {
  const response = await fetch(
    `${API_BASE}/polls/${pollId}/graph/generate?k=${k}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate graph');
  }

  return response.json();
}

/**
 * Get assigned PPE neighbors for a user.
 * 
 * @param {string} pollId - Poll identifier
 * @param {string} userId - User identifier
 * @returns {Promise<Object>} Object with neighbors array
 */
export async function getNeighbors(pollId, userId) {
  const response = await fetch(
    `${API_BASE}/polls/${pollId}/graph/neighbors?user_id=${userId}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get neighbors');
  }

  return response.json();
}

/**
 * Get the complete ideal graph for a poll.
 * 
 * @param {string} pollId - Poll identifier
 * @returns {Promise<Object>} Complete graph structure
 */
export async function getFullGraph(pollId) {
  const response = await fetch(
    `${API_BASE}/polls/${pollId}/graph/`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get graph');
  }

  return response.json();
}

/**
 * Invalidate cached graph (force regeneration).
 * 
 * @param {string} pollId - Poll identifier
 * @returns {Promise<Object>} Success message
 */
export async function invalidateGraph(pollId) {
  const response = await fetch(
    `${API_BASE}/polls/${pollId}/graph/invalidate`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to invalidate graph');
  }

  return response.json();
}