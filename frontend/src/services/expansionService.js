/**
 * Service for fetching graph expansion metrics from API
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ExpansionService {
  async getExpansionMetrics(pollId, attackEdges = null) {
    const url = new URL(`${API_BASE_URL}/api/expansion/${pollId}/metrics`);
    if (attackEdges !== null) {
      url.searchParams.append('attack_edges', attackEdges);
    }

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch expansion metrics: ${response.statusText}`);
    }

    return response.json();
  }

  async getSybilBound(pollId, attackEdges = null) {
    const url = new URL(`${API_BASE_URL}/api/expansion/${pollId}/sybil-bound`);
    if (attackEdges !== null) {
      url.searchParams.append('attack_edges', attackEdges);
    }

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch Sybil bound: ${response.statusText}`);
    }

    return response.json();
  }

  async getVertexExpansion(pollId) {
    const response = await fetch(`${API_BASE_URL}/api/expansion/${pollId}/expansion/vertex`);
    if (!response.ok) {
      throw new Error(`Failed to fetch vertex expansion: ${response.statusText}`);
    }
    return response.json();
  }

  async getEdgeExpansion(pollId) {
    const response = await fetch(`${API_BASE_URL}/api/expansion/${pollId}/expansion/edge`);
    if (!response.ok) {
      throw new Error(`Failed to fetch edge expansion: ${response.statusText}`);
    }
    return response.json();
  }

  async getSpectralGap(pollId) {
    const response = await fetch(`${API_BASE_URL}/api/expansion/${pollId}/expansion/spectral`);
    if (!response.ok) {
      throw new Error(`Failed to fetch spectral gap: ${response.statusText}`);
    }
    return response.json();
  }

  async getLSEProperty(pollId) {
    const response = await fetch(`${API_BASE_URL}/api/expansion/${pollId}/lse-property`);
    if (!response.ok) {
      throw new Error(`Failed to fetch LSE property: ${response.statusText}`);
    }
    return response.json();
  }
}

export const expansionService = new ExpansionService();