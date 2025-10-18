/**
 * Computational PPE component.
 * Proof-of-work style challenge.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { Cpu, Hash, Play, Pause, CheckCircle, AlertCircle } from 'lucide-react';
import './ppe-components.css';

const ComputationalPPE = ({ execution, onSubmit, onComplete }) => {
  const [isComputing, setIsComputing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [solution, setSolution] = useState(null);
  const [hashesComputed, setHashesComputed] = useState(0);
  const [workerRef, setWorkerRef] = useState(null);

  const challengeData = execution.challenge_data;

  // Create web worker for computation
  useEffect(() => {
    const createWorker = () => {
      const workerScript = `
        let isRunning = false;
        
        function sha256(str) {
          // Simple SHA-256 implementation for demo
          // In production, use crypto.subtle.digest()
          return crypto.subtle.digest('SHA-256', new TextEncoder().encode(str))
            .then(buffer => Array.from(new Uint8Array(buffer))
              .map(b => b.toString(16).padStart(2, '0')).join(''));
        }
        
        async function findNonce(challengeString, target, startNonce = 0, batchSize = 10000) {
          isRunning = true;
          let nonce = startNonce;
          let hashCount = 0;
          
          while (isRunning && nonce < startNonce + 1000000) {
            for (let i = 0; i < batchSize && isRunning; i++, nonce++, hashCount++) {
              const input = challengeString + '||' + nonce;
              const hashHex = await sha256(input);
              const hashValue = BigInt('0x' + hashHex);
              
              if (hashValue < BigInt(target)) {
                self.postMessage({
                  type: 'solution',
                  nonce: nonce.toString(),
                  hashCount
                });
                return;
              }
            }
            
            self.postMessage({
              type: 'progress',
              nonce,
              hashCount
            });
            
            // Yield to prevent blocking
            await new Promise(resolve => setTimeout(resolve, 1));
          }
          
          self.postMessage({
            type: 'timeout',
            hashCount
          });
        }
        
        self.onmessage = function(e) {
          if (e.data.type === 'start') {
            findNonce(e.data.challengeString, e.data.target);
          } else if (e.data.type === 'stop') {
            isRunning = false;
          }
        };
      `;
      
      const blob = new Blob([workerScript], { type: 'application/javascript' });
      return new Worker(URL.createObjectURL(blob));
    };

    const worker = createWorker();
    setWorkerRef(worker);

    worker.onmessage = (e) => {
      const { type, nonce, hashCount } = e.data;
      
      setHashesComputed(hashCount);
      
      if (type === 'solution') {
        setSolution(nonce);
        setIsComputing(false);
        setProgress(100);
      } else if (type === 'progress') {
        setProgress(Math.min(95, (hashCount / 1000000) * 100));
      } else if (type === 'timeout') {
        setIsComputing(false);
        onComplete(false, 'Computation timeout - no solution found');
      }
    };

    return () => {
      worker.terminate();
    };
  }, [onComplete]);

  const startComputation = useCallback(() => {
    if (!workerRef) return;
    
    setIsComputing(true);
    setProgress(0);
    setHashesComputed(0);
    
    workerRef.postMessage({
      type: 'start',
      challengeString: challengeData.challenge_string,
      target: challengeData.target_hex
    });
  }, [workerRef, challengeData]);

  const stopComputation = useCallback(() => {
    if (!workerRef) return;
    
    workerRef.postMessage({ type: 'stop' });
    setIsComputing(false);
  }, [workerRef]);

  const handleSubmit = async () => {
    if (!solution) return;
    
    const response = { nonce: solution };
    
    try {
      const result = await onSubmit(response);
      onComplete(result.success, result.failure_reason);
    } catch (error) {
      onComplete(false, error.message);
    }
  };

  return (
    <Card className="ppe-card">
      <CardHeader>
        <CardTitle className="ppe-header">
          <Cpu className="title-icon" />
          <span>Computational Proof-of-Work</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="ppe-content">
        <Alert className="ppe-info">
          <AlertDescription>
            <strong>Challenge:</strong> Find a number (nonce) that makes the hash start with {challengeData.difficulty_bits} zero bits.
            This requires computational effort and cannot be easily faked.
          </AlertDescription>
        </Alert>

        {/* Challenge Details */}
        <div className="computational-details">
          <div className="detail-row">
            <span className="detail-label">Difficulty:</span>
            <span className="detail-value">{challengeData.difficulty_bits} leading zero bits</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Target:</span>
            <span className="detail-value hash-value">{challengeData.target_hex}</span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Challenge:</span>
            <span className="detail-value challenge-text">{challengeData.challenge_string}</span>
          </div>
        </div>

        {/* Progress Section */}
        <div className="computation-progress">
          <div className="progress-header">
            <span>Computation Progress</span>
            <span className="hash-counter">{hashesComputed.toLocaleString()} hashes</span>
          </div>
          
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            />
          </div>
          
          <div className="progress-text">
            {progress.toFixed(1)}% complete
          </div>
        </div>

        {/* Control Buttons */}
        <div className="computational-controls">
          {!isComputing && !solution && (
            <Button onClick={startComputation} className="compute-button">
              <Play className="button-icon" />
              Start Computing
            </Button>
          )}
          
          {isComputing && (
            <Button onClick={stopComputation} variant="outline" className="stop-button">
              <Pause className="button-icon" />
              Stop Computing
            </Button>
          )}
          
          {solution && (
            <div className="solution-section">
              <Alert className="solution-alert">
                <CheckCircle className="alert-icon" />
                <AlertDescription>
                  <strong>Solution found!</strong> Nonce: {solution}
                </AlertDescription>
              </Alert>
              
              <Button onClick={handleSubmit} className="submit-solution-button">
                <Hash className="button-icon" />
                Submit Solution
              </Button>
            </div>
          )}
        </div>

        <div className="ppe-description">
          This computational challenge proves you've expended CPU effort. 
          The difficulty adjusts the time required to find a solution.
        </div>
      </CardContent>
    </Card>
  );
};

export default ComputationalPPE;