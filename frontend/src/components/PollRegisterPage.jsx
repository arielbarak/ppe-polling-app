import React, { useState, useEffect } from 'react';
import { pollApi } from '../api/pollApi';

function PollRegisterPage({ pollId, userPublicKey, navigateToVote }) {
  const [poll, setPoll] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRegistering, setIsRegistering] = useState(false);
  const [registrationMessage, setRegistrationMessage] = useState('');
  const [copySuccess, setCopySuccess] = useState('');

  useEffect(() => {
    const fetchPoll = async () => {
      try {
        const pollData = await pollApi.getPoll(pollId);
        setPoll(pollData);
      } finally {
        setIsLoading(false);
      }
    };
    fetchPoll();
  }, [pollId]);

  const handleRegister = async () => {
    setIsRegistering(true);
    setRegistrationMessage('');
    try {
      await pollApi.register(pollId, userPublicKey);
      setRegistrationMessage('Registration successful! Navigating...');
      setTimeout(() => navigateToVote(pollId), 1000); // Wait 1 sec to show message
    } catch (err) {
      setRegistrationMessage(`Error: ${err.message}`);
    } finally {
      setIsRegistering(false);
    }
  };

  const copyToClipboard = () => {
    const textArea = document.createElement("textarea");
    textArea.value = pollId;
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
      setCopySuccess('Copied!');
      setTimeout(() => setCopySuccess(''), 2000); // Hide message after 2 seconds
    } catch (err) {
      setCopySuccess('Failed to copy');
    }
    document.body.removeChild(textArea);
  };

  if (isLoading) return <p>Loading poll...</p>;
  if (!poll) return <p>Poll not found.</p>;

  return (
    <div className="poll-page-container">
      <h2>{poll.question}</h2>

      <div className="share-poll-section">
        <h3>Share this Poll</h3>
        <p>Use this ID to let others join the poll.</p>
        <div className="poll-id-display">
          <span>{pollId}</span>
          <button onClick={copyToClipboard}>Copy ID</button>
        </div>
        {copySuccess && <span className="copy-success">{copySuccess}</span>}
      </div>

      <div className="registration-section">
        <p>You must register to participate in this poll.</p>
        <button onClick={handleRegister} disabled={isRegistering}>
          {isRegistering ? 'Registering...' : 'Register Now'}
        </button>
        {registrationMessage &&
          <p className={registrationMessage.startsWith('Error') ? 'error-message' : 'success-message'}>
            {registrationMessage}
          </p>
        }
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
    </div>
  );
}

export default PollRegisterPage;
