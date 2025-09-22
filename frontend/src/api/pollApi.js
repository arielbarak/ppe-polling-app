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

getAllPolls: async () => {
    const response = await fetch(`${API_BASE_URL}/polls/`);
    if (!response.ok) throw new Error('Failed to fetch polls');
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

  verifyUser: async (pollId, userId, verifierKey) => {
    const response = await fetch(`${API_BASE_URL}/polls/${pollId}/verify/${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(verifierKey)
    });
    if (!response.ok) throw new Error('Failed to verify user');
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
  },

  getUserId: async (publicKey) => {
    const response = await fetch(`${API_BASE_URL}/polls/userid`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(publicKey)
    });
    if (!response.ok) throw new Error('Failed to get user ID');
    return response.text();
  },

  getUserVerifications: async (pollId, publicKey) => {
    const encodedKey = encodeURIComponent(JSON.stringify(publicKey));
    const response = await fetch(
      `${API_BASE_URL}/polls/${pollId}/verifications?public_key_str=${encodedKey}`,
      {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    if (!response.ok) throw new Error('Failed to get verifications');
    return response.json();
  },

  recordPPECertification: async (pollId, user1PublicKey, user2PublicKey) => {
    const response = await fetch(`${API_BASE_URL}/polls/${pollId}/ppe-certification`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user1_public_key: user1PublicKey,
        user2_public_key: user2PublicKey
      })
    });
    if (!response.ok) throw new Error('Failed to record PPE certification');
    return response.json();
  },

  getPPECertifications: async (pollId, publicKey) => {
    const encodedKey = encodeURIComponent(JSON.stringify(publicKey));
    const response = await fetch(
      `${API_BASE_URL}/polls/${pollId}/ppe-certifications?public_key_str=${encodedKey}`,
      {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    if (!response.ok) throw new Error('Failed to get PPE certifications');
    return response.json();
  },
  
  getVerificationData: async (pollId) => {
    const response = await fetch(`${API_BASE_URL}/polls/${pollId}/verify`);
    if (!response.ok) throw new Error('Failed to get verification data');
    return response.json();
  }
};
