import React, { useState, useEffect, useMemo, useRef } from 'react';
import { pollApi } from '../api/pollApi';
import { cryptoService } from '../services/cryptoService';
import { calculateNeighbors } from '../services/graphService';
import { sha256 } from 'js-sha256';
import CaptchaModal from './CaptchaModal';

// Function to generate our own CAPTCHA challenge
const generateCaptchaText = (length = 6) => {
  const chars = 'AbCdEfGhIjKlMnOpQrStUvWxYz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
};

function PollVotePage({ pollId, userPublicKey, navigateToHome }) {
  const [poll, setPoll] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const socketRef = useRef(null);
  const [certifiedPeers, setCertifiedPeers] = useState(new Set());

  const [ppeState, setPpeState] = useState({
    step: 'idle',
    peerId: null,
    myChallengeText: null,
    peerChallengeText: null,
    mySolutionToPeerChallenge: null,
    peerSolutionCommitment: null,
  });
  const ppeStateRef = useRef(ppeState);
  ppeStateRef.current = ppeState;

  const currentUserId = useMemo(() => {
    if (!poll || !userPublicKey) return null;
    const entry = Object.entries(poll.registrants).find(
      ([id, key]) => JSON.stringify(key) === JSON.stringify(userPublicKey)
    );
    return entry ? entry[0] : null;
  }, [poll, userPublicKey]);

  const neighbors = useMemo(() => {
    if (!poll || !currentUserId) return [];
    const allUserIds = Object.keys(poll.registrants).filter(id => id !== currentUserId).sort();
    return calculateNeighbors(currentUserId, allUserIds);
  }, [poll, currentUserId]);

  const fetchPoll = async () => {
    try {
      const pollData = await pollApi.getPoll(pollId);
      setPoll(pollData);
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    fetchPoll();
  }, [pollId]);

  useEffect(() => {
    if (!pollId || !currentUserId) return;
    const wsUrl = `ws://localhost:8000/ws/${pollId}/${currentUserId}`;
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      console.log('Received message:', msg);
      const currentPpeState = ppeStateRef.current;

      if (msg.type === 'user_registered') { fetchPoll(); }
      
      // *** THE FIX: Corrected the message type from 'ppe_request' to 'request_ppe' ***
      if (msg.type === 'request_ppe') {
        if (window.confirm(`Accept certification request from ${msg.from.substring(0,12)}...?`)) {
          socket.send(JSON.stringify({ type: 'accept_ppe', target: msg.from }));
        }
      }

      if (msg.type === 'start_challenge') {
        const myChallenge = generateCaptchaText();
        setPpeState({ ...currentPpeState, step: 'challenging', peerId: msg.with, myChallengeText: myChallenge });
        socket.send(JSON.stringify({ type: 'challenge', target: msg.with, challenge: myChallenge }));
      }

      if (msg.type === 'challenge') {
        setPpeState({ ...currentPpeState, step: 'solving', peerId: msg.from, peerChallengeText: msg.challenge });
      }

      if (msg.type === 'commitment') {
        setPpeState(prev => ({ ...prev, step: 'revealing', peerSolutionCommitment: msg.commitment }));
        socket.send(JSON.stringify({ type: 'reveal', target: msg.from, solution: currentPpeState.mySolutionToPeerChallenge }));
      }

      if (msg.type === 'reveal') {
        const commitmentCheck = sha256(msg.solution) === currentPpeState.peerSolutionCommitment;
        if (commitmentCheck) {
          alert(`SUCCESS! Peer ${msg.from.substring(0,12)} has been certified.`);
          setCertifiedPeers(prev => new Set(prev).add(msg.from));
        } else {
          alert(`FAILED! Peer ${msg.from.substring(0,12)} provided an invalid solution.`);
        }
        setPpeState({ step: 'idle', peerId: null, myChallengeText: null, peerChallengeText: null, mySolutionToPeerChallenge: null, peerSolutionCommitment: null });
      }
    };

    return () => { if (socketRef.current) socketRef.current.close(); };
  }, [pollId, currentUserId]);

  const handleStartCertification = (neighborId) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'request_ppe', target: neighborId }));
    } else {
      alert("Connection not ready. Please try again in a moment.");
    }
  };
  
  const handleCaptchaSolve = (solution) => {
    const commitment = sha256(solution);
    setPpeState(prev => {
      socketRef.current.send(JSON.stringify({ type: 'commitment', target: prev.peerId, commitment: commitment }));
      return { ...prev, mySolutionToPeerChallenge: solution };
    });
  };

  const handleVote = async (option) => {
    try {
      const keyPair = await cryptoService.loadKeys();
      if (!keyPair) throw new Error("Keys not loaded.");
      const messageToSign = `${poll.id}:${option}`;
      const signature = await cryptoService.signMessage(keyPair.privateKey, messageToSign);
      const voteData = { publicKey: userPublicKey, option: option, signature: signature };
      await pollApi.submitVote(poll.id, voteData);
      alert(`Successfully voted for: ${option}`);
      fetchPoll();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  if (isLoading) return <p>Loading poll...</p>;
  if (!poll) return <p>Poll not found.</p>;

  const hasVoted = currentUserId && poll.votes[currentUserId];

  return (
    <div className="poll-page-container">
      {ppeState.step === 'solving' && (
        <CaptchaModal
          peerId={ppeState.peerId}
          challengeText={ppeState.peerChallengeText}
          onSolve={handleCaptchaSolve}
          onClose={() => setPpeState({ step: 'idle' })}
        />
      )}
      <h2>{poll.question}</h2>
      {!hasVoted && (
        <div className="certification-section">
          <h3>Step 1: Certify with Peers</h3>
          <ul>
            {neighbors.map(neighborId => (
              <li key={neighborId}>
                <span>Peer: {neighborId.substring(0, 12)}...</span>
                {certifiedPeers.has(neighborId) ? (
                  <span className="certified-label">✅ Certified</span>
                ) : (
                  <button onClick={() => handleStartCertification(neighborId)}>Start PPE</button>
                )}
              </li>
            ))}
             {neighbors.length === 0 && <li>Waiting for other users to register...</li>}
          </ul>
        </div>
      )}
      <div className="vote-section">
        <h3>Step 2: Cast Your Vote</h3>
        {hasVoted ? (
          <p>You have already voted for: <strong>{poll.votes[currentUserId]?.option}</strong></p>
        ) : (
          poll.options.map((option, index) => (
            <button key={`vote-option-${index}`} onClick={() => handleVote(option)} className="vote-button">
              {option}
            </button>
          ))
        )}
      </div>
       <div className="results-section">
        <h3>Live Results</h3>
        <ul>
          {poll.options.map((option, index) => {
            const voteCount = Object.values(poll.votes).filter(v => v.option === option).length;
            return <li key={`result-option-${index}`}><span>{option}:</span> <span>{voteCount} vote(s)</span></li>
          })}
        </ul>
      </div>
      <button onClick={navigateToHome} style={{ marginTop: '20px' }}>Back to Home</button>
    </div>
  );
}

export default PollVotePage;
