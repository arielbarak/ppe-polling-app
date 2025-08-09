const API_BASE_URL = 'http://localhost:8000';

export const pollApi = {
  createPoll: async (pollData) => {
    const response = await fetch(`${API_BASE_URL}/polls`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pollData),
    });
    if (!response.ok) throw new Error('Failed to create poll');
    return response.json();
  },

  getPoll: async (pollId) => {
    const response = await fetch(`${API_BASE_URL}/polls/${pollId}`);
    if (!response.ok) throw new Error(`Failed to fetch poll with id ${pollId}`);
    return response.json();
  },

  register: async (pollId, publicKeyJwk) => {
    const response = await fetch(`${API_BASE_URL}/polls/${pollId}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(publicKeyJwk)
    });
    if (!response.ok) throw new Error('Failed to register for poll');
    return response.json();
  },

  submitVote: async (pollId, voteData) => {
    const response = await fetch(`${API_BASE_URL}/polls/${pollId}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(voteData)
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit vote');
    }
    return response.json();
  }
};
