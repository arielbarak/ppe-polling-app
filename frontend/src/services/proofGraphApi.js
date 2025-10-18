/**
 * API client for proof graph operations.
 */

const API_BASE = 'http://localhost:8000';

/**
 * Get the complete proof graph for a poll.
 * 
 * @param {string} pollId - Poll identifier
 * @returns {Promise<Object>} Complete proof graph
 */
export async function getProofGraph(pollId) {
  const response = await fetch(`${API_BASE}/polls/${pollId}/proof/graph`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get proof graph');
  }

  return response.json();
}

/**
 * Get a summary of the proof graph.
 * 
 * @param {string} pollId - Poll identifier
 * @returns {Promise<Object>} Proof graph summary
 */
export async function getProofSummary(pollId) {
  const response = await fetch(`${API_BASE}/polls/${pollId}/proof/summary`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get proof summary');
  }

  return response.json();
}

/**
 * Export the proof graph as a downloadable JSON file.
 * 
 * @param {string} pollId - Poll identifier
 * @returns {Promise<void>}
 */
export async function exportProofGraph(pollId) {
  const response = await fetch(`${API_BASE}/polls/${pollId}/proof/export`, {
    method: 'GET',
  });

  if (!response.ok) {
    throw new Error('Failed to export proof graph');
  }

  // Download the file
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `proof_graph_${pollId}.json`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

/**
 * Force reconstruction of the proof graph.
 * 
 * @param {string} pollId - Poll identifier
 * @returns {Promise<Object>} Reconstruction result
 */
export async function reconstructProofGraph(pollId) {
  const response = await fetch(`${API_BASE}/polls/${pollId}/proof/reconstruct`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to reconstruct proof graph');
  }

  return response.json();
}

/**
 * Verify the proof graph hash.
 * 
 * @param {string} pollId - Poll identifier
 * @returns {Promise<Object>} Hash verification result
 */
export async function verifyProofHash(pollId) {
  const response = await fetch(`${API_BASE}/polls/${pollId}/proof/verify-hash`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to verify hash');
  }

  return response.json();
}