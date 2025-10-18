/**
 * Hook for managing certification state with persistence.
 * FIXES Issue #5: State survives page refresh.
 */

import { useState, useEffect, useCallback } from 'react';
import { certificationService } from '../services/certificationService';

export const useCertificationState = (pollId, userId) => {
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load state from backend
  const loadState = useCallback(async () => {
    if (!pollId || !userId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const data = await certificationService.getCertificationState(pollId, userId);
      
      if (data.exists) {
        setState(data.state);
      } else {
        setState(null);
      }
      
      setError(null);
    } catch (err) {
      console.error('Failed to load certification state:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [pollId, userId]);

  // Load on mount and when dependencies change
  useEffect(() => {
    loadState();
  }, [loadState]);

  // Refresh state periodically (every 5 seconds)
  useEffect(() => {
    const interval = setInterval(() => {
      loadState();
    }, 5000);

    return () => clearInterval(interval);
  }, [loadState]);

  // Update state optimistically
  const updateState = useCallback((updates) => {
    setState(prev => prev ? { ...prev, ...updates } : null);
  }, []);

  // Record PPE completion
  const completePPE = useCallback(async (ppeId, partnerId, signature) => {
    try {
      const result = await certificationService.completePPE(
        pollId,
        userId,
        partnerId,
        ppeId,
        signature
      );

      if (result.success) {
        setState(result.state);
      }

      return result;
    } catch (err) {
      console.error('Failed to record PPE completion:', err);
      throw err;
    }
  }, [pollId, userId]);

  // Record PPE failure
  const failPPE = useCallback(async (ppeId) => {
    try {
      const result = await certificationService.failPPE(pollId, userId, ppeId);

      if (result.success) {
        setState(result.state);
      }

      return result;
    } catch (err) {
      console.error('Failed to record PPE failure:', err);
      throw err;
    }
  }, [pollId, userId]);

  return {
    state,
    loading,
    error,
    reload: loadState,
    updateState,
    completePPE,
    failPPE,
    
    // Computed properties
    isReady: !loading && !error && state !== null,
    isCertified: state?.is_certified ?? false,
    isExcluded: state?.is_excluded ?? false,
    canVote: state?.is_certified && !state?.is_excluded && !state?.has_voted,
    hasVoted: state?.has_voted ?? false,
    progress: {
      required: state?.required_ppes ?? 0,
      completed: state?.completed_ppes ?? 0,
      failed: state?.failed_ppes ?? 0,
      remaining: state?.remaining_ppes ?? 0,
      percentage: state?.completion_percentage ?? 0
    }
  };
};