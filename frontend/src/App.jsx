import React, { useState, useEffect } from 'react';
import { cryptoService } from './services/cryptoService';
import CreatePoll from './components/CreatePoll';
import PollRegisterPage from './components/PollRegisterPage';
import PollVotePage from './components/PollVotePage';
import './App.css';

// Updated HomePage component with "Join Poll" functionality
const HomePage = ({ navigateToCreate, navigateToPoll }) => {
  const [joinPollId, setJoinPollId] = useState('');

  const handleJoin = () => {
    if (joinPollId.trim()) {
      navigateToPoll(joinPollId.trim());
    }
  };

  return (
    <div className="homepage-container">
      <div className="homepage-action">
        <h2>Create a Poll</h2>
        <p>Create a new secure, publicly verifiable poll.</p>
        <button onClick={navigateToCreate}>Create New Poll</button>
      </div>
      <div className="homepage-action">
        <h2>Join a Poll</h2>
        <p>Have a poll ID? Enter it here to join.</p>
        <input
          type="text"
          value={joinPollId}
          onChange={(e) => setJoinPollId(e.target.value)}
          placeholder="Enter Poll ID"
        />
        <button onClick={handleJoin}>Join Poll</button>
      </div>
    </div>
  );
};

function App() {
  const [publicKey, setPublicKey] = useState(null);
  const [view, setView] = useState({ page: 'home', pollId: null });

  // --- Navigation Functions ---
  const navigateToHome = () => setView({ page: 'home', pollId: null });
  const navigateToCreate = () => setView({ page: 'create', pollId: null });
  const navigateToPoll = (pollId) => setView({ page: 'register', pollId: pollId });
  const navigateToVote = (pollId) => setView({ page: 'vote', pollId: pollId });

  useEffect(() => {
    const initializeIdentity = async () => {
      let keyPair = await cryptoService.loadKeys();
      if (!keyPair) {
        keyPair = await cryptoService.generateKeys();
        await cryptoService.saveKeys(keyPair);
      }
      const publicKeyJwk = await cryptoService.getPublicKeyAsJwk(keyPair.publicKey);
      setPublicKey(publicKeyJwk);
    };
    initializeIdentity();
  }, []);

  const renderView = () => {
    switch (view.page) {
      case 'create':
        return <CreatePoll navigateToPoll={navigateToPoll} />;
      case 'register':
        return <PollRegisterPage pollId={view.pollId} userPublicKey={publicKey} navigateToVote={navigateToVote} />;
      case 'vote':
        return <PollVotePage pollId={view.pollId} userPublicKey={publicKey} navigateToHome={navigateToHome} />;
      case 'home':
      default:
        return <HomePage navigateToCreate={navigateToCreate} navigateToPoll={navigateToPoll} />;
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>PPE Polling System</h1>
      </header>
      <main>
        {renderView()}
      </main>
      <footer className="App-footer">
        {publicKey && <p className="key-status">Identity Loaded</p>}
      </footer>
    </div>
  );
}

export default App;
