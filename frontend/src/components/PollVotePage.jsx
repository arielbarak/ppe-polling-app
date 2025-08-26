import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Card, Button, Typography, List, Space, Alert, Spin, Progress, Divider, message } from 'antd';
import { HomeOutlined, CheckCircleOutlined, UserOutlined, LockOutlined } from '@ant-design/icons';
import { pollApi } from '../api/pollApi';
import { cryptoService } from '../services/cryptoService';
import { calculateNeighbors } from '../services/graphService';
import { sha256 } from 'js-sha256';
import CaptchaModal from './CaptchaModal';

const { Title, Text } = Typography;

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

  const handleVerifyUser = async (userId) => {
    try {
        await pollApi.verifyUser(pollId, userId, userPublicKey);
        socketRef.current.send(JSON.stringify({
            type: 'verification_accepted',
            target: userId
        }));
        await fetchPoll();
    } catch (error) {
        message.error('Failed to verify user');
    }
  };

  const fetchUserData = async () => {
    try {
        const userId = await pollApi.getUserId(userPublicKey);
        const verifications = await pollApi.getUserVerifications(pollId, userPublicKey);
        
        if (!verifications.can_vote) {
            message.error('You need to be verified before voting');
            navigateToHome();
        }
    } catch (error) {
        message.error('Failed to verify voting eligibility');
        navigateToHome();
    }
  };

  useEffect(() => {
    fetchUserData();
  }, [pollId, userPublicKey]);

  if (isLoading) return <Spin size="large" />;
  if (!poll) return <Alert message="Poll not found" type="error" />;

  const hasVoted = currentUserId && poll.votes[currentUserId];

  const renderVerificationRequests = () => (
    <Card title="Verification Requests">
        <List
            dataSource={Object.entries(poll.registrants)
                .filter(([id]) => !poll.verifications[id]?.verified_by.includes(currentUserId))
                .filter(([id]) => id !== currentUserId)}
            renderItem={([userId, publicKey]) => (
                <List.Item
                    actions={[
                        <Button
                            type="primary"
                            onClick={() => handleVerifyUser(userId)}
                            icon={<CheckCircleOutlined />}
                        >
                            Verify User
                        </Button>
                    ]}
                >
                    <List.Item.Meta
                        avatar={<UserOutlined />}
                        title={`User: ${userId.substring(0, 12)}...`}
                        description="Requesting verification"
                    />
                </List.Item>
            )}
        />
    </Card>
);

  return (
    <Space direction="vertical" size="large" style={{ width: '100%', maxWidth: 800 }}>
      {ppeState.step === 'solving' && (
        <CaptchaModal
          peerId={ppeState.peerId}
          challengeText={ppeState.peerChallengeText}
          onSolve={handleCaptchaSolve}
          onClose={() => setPpeState({ step: 'idle' })}
        />
      )}

      <Card>
        <Title level={2}>{poll.question}</Title>
      </Card>

      {!hasVoted && (
        <Card title={<Title level={3}><LockOutlined /> Step 1: Certify with Peers</Title>}>
          <List
            dataSource={neighbors.length ? neighbors : ['Waiting for other users to register...']}
            renderItem={neighborId => (
              <List.Item
                actions={[
                  neighbors.length && (
                    certifiedPeers.has(neighborId) ? (
                      <Text type="success"><CheckCircleOutlined /> Certified</Text>
                    ) : (
                      <Button 
                        type="primary" 
                        onClick={() => handleStartCertification(neighborId)}
                      >
                        Start PPE
                      </Button>
                    )
                  )
                ]}
              >
                <List.Item.Meta
                  avatar={<UserOutlined />}
                  title={neighbors.length ? `Peer: ${neighborId.substring(0, 12)}...` : neighborId}
                />
              </List.Item>
            )}
          />
        </Card>
      )}

      {!hasVoted && renderVerificationRequests()}

      <Card title={<Title level={3}>Step 2: Cast Your Vote</Title>}>
        {hasVoted ? (
          <Alert
            message="Vote Submitted"
            description={`You have voted for: ${poll.votes[currentUserId]?.option}`}
            type="success"
            showIcon
          />
        ) : (
          <Space wrap>
            {poll.options.map((option, index) => (
              <Button
                key={`vote-option-${index}`}
                type="primary"
                size="large"
                onClick={() => handleVote(option)}
              >
                {option}
              </Button>
            ))}
          </Space>
        )}
      </Card>

      <Card title={<Title level={3}>Live Results</Title>}>
        <List
          dataSource={poll.options}
          renderItem={(option) => {
            const voteCount = Object.values(poll.votes).filter(v => v.option === option).length;
            const totalVotes = Object.keys(poll.votes).length;
            const percentage = totalVotes ? (voteCount / totalVotes) * 100 : 0;

            return (
              <List.Item>
                <List.Item.Meta
                  title={option}
                  description={
                    <Progress 
                      percent={Math.round(percentage)} 
                      format={() => `${voteCount} vote${voteCount !== 1 ? 's' : ''}`}
                    />
                  }
                />
              </List.Item>
            );
          }}
        />
      </Card>

      <Button 
        icon={<HomeOutlined />}
        onClick={navigateToHome}
        style={{ alignSelf: 'center' }}
      >
        Back to Home
      </Button>
    </Space>
  );
}

export default PollVotePage;
