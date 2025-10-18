/**
 * Hook for managing PPE execution.
 */

import { useState, useCallback } from 'react';
import { ppeService } from '../services/ppeService';

export const usePPEExecution = (pollId, userId) => {
  const [executing, setExecuting] = useState(false);
  const [currentExecution, setCurrentExecution] = useState(null);
  const [error, setError] = useState(null);

  const initiatePPE = useCallback(async (partnerId, ppeType) => {
    setExecuting(true);
    setError(null);
    
    try {
      const execution = await ppeService.initiatePPE({
        poll_id: pollId,
        prover_id: userId,
        verifier_id: partnerId,
        ppe_type: ppeType
      });
      
      setCurrentExecution(execution);
      return execution;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setExecuting(false);
    }
  }, [pollId, userId]);

  const submitResponse = useCallback(async (executionId, response) => {
    try {
      const result = await ppeService.submitResponse(executionId, response);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const getStatus = useCallback(async (executionId) => {
    try {
      const status = await ppeService.getStatus(executionId);
      return status;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const getActivePPEs = useCallback(async () => {
    try {
      const active = await ppeService.getActivePPEs(pollId, userId);
      return active;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [pollId, userId]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const reset = useCallback(() => {
    setExecuting(false);
    setCurrentExecution(null);
    setError(null);
  }, []);

  return {
    executing,
    currentExecution,
    error,
    initiatePPE,
    submitResponse,
    getStatus,
    getActivePPEs,
    clearError,
    reset
  };
};