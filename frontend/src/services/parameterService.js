/**
 * Parameter service for API calls.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ParameterService {
  async validateParameters(params) {
    const response = await fetch(`${API_BASE_URL}/api/parameters/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    
    if (!response.ok) {
      throw new Error(`Validation failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  async calculateParameters(m, securityLevel, customConstraints = null) {
    const params = new URLSearchParams({
      m: m.toString(),
      security_level: securityLevel
    });
    
    const url = `${API_BASE_URL}/api/parameters/calculate?${params}`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: customConstraints ? JSON.stringify(customConstraints) : null
    });
    
    if (!response.ok) {
      throw new Error(`Calculation failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getPresets() {
    const response = await fetch(`${API_BASE_URL}/api/parameters/presets`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch presets: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getPreset(securityLevel) {
    const response = await fetch(`${API_BASE_URL}/api/parameters/presets/${securityLevel}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch preset: ${response.statusText}`);
    }
    
    return response.json();
  }

  async optimizeForEffort(m, maxPPEsPerUser, minSecurityLevel = 0.9) {
    const params = new URLSearchParams({
      m: m.toString(),
      max_ppes_per_user: maxPPEsPerUser.toString(),
      min_security_level: minSecurityLevel.toString()
    });
    
    const response = await fetch(
      `${API_BASE_URL}/api/parameters/optimize-effort?${params}`,
      { method: 'POST' }
    );
    
    if (!response.ok) {
      throw new Error(`Optimization failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  async estimateMinimumParticipants(d, kappa = 40, etaV = 0.025) {
    const params = new URLSearchParams({
      d: d.toString(),
      kappa: kappa.toString(),
      eta_v: etaV.toString()
    });
    
    const response = await fetch(
      `${API_BASE_URL}/api/parameters/estimate-minimum-participants?${params}`
    );
    
    if (!response.ok) {
      throw new Error(`Estimation failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  async savePollParameters(pollId, params) {
    const response = await fetch(
      `${API_BASE_URL}/api/parameters/poll/${pollId}/parameters`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      }
    );
    
    if (!response.ok) {
      throw new Error(`Failed to save parameters: ${response.statusText}`);
    }
    
    return response.json();
  }

  async getPollParameters(pollId) {
    const response = await fetch(
      `${API_BASE_URL}/api/parameters/poll/${pollId}/parameters`
    );
    
    if (!response.ok) {
      throw new Error(`Failed to get parameters: ${response.statusText}`);
    }
    
    return response.json();
  }
}

export const parameterService = new ParameterService();