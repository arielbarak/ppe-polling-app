/**
 * Service for certification API calls.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class CertificationService {
  async getCertificationState(pollId, userId) {
    const response = await fetch(
      `${API_BASE_URL}/api/polls/${pollId}/certification/state?user_id=${userId}`
    );
    
    if (!response.ok) {
      throw new Error(`Failed to get certification state: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getAssignments(pollId, userId) {
    const response = await fetch(
      `${API_BASE_URL}/api/polls/${pollId}/certification/assignments?user_id=${userId}`
    );
    
    if (!response.ok) {
      throw new Error(`Failed to get assignments: ${response.statusText}`);
    }
    
    return response.json();
  }

  async completePPE(pollId, userId, partnerId, ppeId, signature) {
    const response = await fetch(
      `${API_BASE_URL}/api/polls/${pollId}/certification/complete-ppe`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, partner_id: partnerId, ppe_id: ppeId, signature })
      }
    );
    
    if (!response.ok) {
      throw new Error(`Failed to complete PPE: ${response.statusText}`);
    }
    
    return response.json();
  }

  async failPPE(pollId, userId, ppeId) {
    const response = await fetch(
      `${API_BASE_URL}/api/polls/${pollId}/certification/fail-ppe`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, ppe_id: ppeId })
      }
    );
    
    if (!response.ok) {
      throw new Error(`Failed to record PPE failure: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getVerificationRequirements(pollId, userId) {
    const response = await fetch(
      `${API_BASE_URL}/api/polls/${pollId}/verification/requirements?user_id=${userId}`
    );
    
    if (!response.ok) {
      throw new Error(`Failed to get requirements: ${response.statusText}`);
    }
    
    return response.json();
  }
}

export const certificationService = new CertificationService();