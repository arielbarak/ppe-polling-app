import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Card, Button, Typography, List, Space, Alert, Spin, Progress, Divider, message, Modal } from 'antd';
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
    showCaptchaModal: false
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
    } catch (error) {
      console.error('Failed to fetch poll:', error);
      // Don't show error message for network issues during background fetching
    } finally {
      setIsLoading(false);
    }
  };
  
  // Initial fetch only - rely on WebSocket for updates
  useEffect(() => {
    fetchPoll();
  }, [pollId]);

  useEffect(() => {
    if (!pollId || !currentUserId) return;
    // Clean currentUserId to remove any quotes that might be in it
    const cleanUserId = currentUserId.replace(/"/g, '');
    const wsUrl = `ws://localhost:8000/ws/${pollId}/${cleanUserId}`;
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      console.log('WebSocket connected');
    };

    socket.onclose = () => {
      console.log('WebSocket disconnected');
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      console.log('Received message:', msg);
      const currentPpeState = ppeStateRef.current;

      if (msg.type === 'error') {
        if (msg.error === 'target_offline') {
          message.error(`Peer is offline or not available: ${msg.target.substring(0, 8)}...`);
          setPpeState(prev => ({ ...prev, step: 'idle' }));
        } else {
          message.error(msg.message);
        }
        return;
      }

      if (msg.type === 'user_registered' || msg.type === 'user_verified') { 
        console.log('User change detected, refreshing poll data');
        fetchPoll(); 
      }
      
      if (msg.type === 'request_ppe') {
        // Only accept if we're not already in a PPE session
        if (currentPpeState.step !== 'idle') {
          socket.send(JSON.stringify({ 
            type: 'reject_ppe', 
            target: msg.from,
            reason: 'busy'
          }));
          return;
        }

        // Generate our challenge first
        const myChallenge = generateCaptchaText();
        
        Modal.confirm({
          title: 'PPE Certification Request',
          content: `Accept certification request from peer ${msg.from.substring(0,8)}...?`,
          onOk() {
            setPpeState({
              ...currentPpeState,
              step: 'challenging',
              peerId: msg.from,
              myChallengeText: myChallenge,
              challengeStartTime: Date.now()
            });
            
            // First accept, then immediately send our challenge
            socket.send(JSON.stringify({ 
              type: 'accept_ppe', 
              target: msg.from 
            }));
            
            // Send our challenge right away - encrypted
            setTimeout(() => {
              // Create consistent password by sorting the IDs
              const encryptionKey = [msg.from, currentUserId].sort().join('');
              console.log('Encrypting challenge for peer');
              
              cryptoService.encryptText(myChallenge, encryptionKey)
                .then(encryptedChallenge => {
                  socket.send(JSON.stringify({ 
                    type: 'challenge',
                    target: msg.from,
                    challenge: encryptedChallenge
                  }));
                })
                .catch(error => {
                  console.error('Failed to encrypt challenge:', error);
                  message.error('Failed to send encrypted challenge');
                });
            }, 100);
          },
          onCancel() {
            socket.send(JSON.stringify({ 
              type: 'reject_ppe', 
              target: msg.from 
            }));
          }
        });
      }

      if (msg.type === 'accept_ppe') {
        // Only process accept if we were the ones who sent the request
        if (currentPpeState.step !== 'requesting' || currentPpeState.peerId !== msg.from) {
          console.warn('Received unexpected accept_ppe, ignoring');
          return;
        }

        message.success(`Peer ${msg.from.substring(0,8)}... accepted your request`);
        
        // Generate our challenge and send it to them
        const myChallenge = generateCaptchaText();
        
        setPpeState({ 
          ...currentPpeState, 
          step: 'challenging',
          myChallengeText: myChallenge,
          challengeStartTime: Date.now()
        });

        // Send our challenge to them - encrypted
        // Create consistent password by sorting the IDs
        const encryptionKey = [msg.from, currentUserId].sort().join('');
        console.log('Encrypting challenge for peer');
        
        cryptoService.encryptText(myChallenge, encryptionKey)
          .then(encryptedChallenge => {
            socket.send(JSON.stringify({ 
              type: 'challenge',
              target: msg.from,
              challenge: encryptedChallenge
            }));
          })
          .catch(error => {
            console.error('Failed to encrypt challenge:', error);
            message.error('Failed to send encrypted challenge');
          });
      }

      if (msg.type === 'reject_ppe') {
        message.warning(`Peer ${msg.from.substring(0,8)}... rejected your request`);
      }

      if (msg.type === 'start_challenge') {
        // This message type is deprecated
        return;
      }

      if (msg.type === 'challenge') {
        // Verify we're in a valid state to receive a challenge
        const validStates = ['waiting_for_challenge', 'challenging'];
        if (!validStates.includes(currentPpeState.step) || currentPpeState.peerId !== msg.from) {
          console.warn(`Received challenge in invalid state: ${currentPpeState.step}, expected peer: ${currentPpeState.peerId}, got: ${msg.from}`);
          return;
        }

        console.log('Received encrypted challenge, decrypting...');
        
        // Decrypt the challenge before showing the modal
        // Create consistent password by sorting the IDs (same as encryption)
        const encryptionKey = [msg.from, currentUserId].sort().join('');
        console.log('Decrypting challenge from peer');
        
        cryptoService.decryptText(msg.challenge, encryptionKey)
          .then(decryptedChallenge => {
            console.log('Challenge decrypted successfully');
            // Set up challenge for solving and show modal
            setPpeState({ 
              ...currentPpeState, 
              step: 'solving', 
              peerChallengeText: decryptedChallenge,
              showCaptchaModal: true
            });
          })
          .catch(error => {
            console.error('Failed to decrypt challenge:', error);
            message.error('Failed to decrypt challenge from peer');
            setPpeState({ ...currentPpeState, step: 'idle' });
          });
      }

      if (msg.type === 'commitment') {
        setPpeState(prev => {
          const timeTaken = Date.now() - prev.challengeStartTime;
          const timeLimit = 30000; // 30 seconds time bound

          if (timeTaken > timeLimit) {
            message.error('Peer took too long to respond');
            return { ...prev, step: 'idle' };
          }

          if (prev.mySolutionToPeerChallenge) {
            // We've solved it, so now we can reveal
            socket.send(JSON.stringify({ 
              type: 'reveal', 
              target: msg.from, 
              solution: prev.mySolutionToPeerChallenge,
              timeTaken
            }));
            return { 
              ...prev, 
              step: 'revealing',
              peerSolutionCommitment: msg.commitment 
            };
          } else {
            // Still need to solve it
            return { 
              ...prev,
              peerSolutionCommitment: msg.commitment 
            };
          }
        });
      }

      if (msg.type === 'reveal') {
        console.log('Reveal message received from:', msg.from.substring(0,8));
        
        // Process the reveal message
        setPpeState(prev => {
          console.log('Current PPE state when processing reveal:', prev.step);
          
          if (msg.solution === null) {
            message.error(`Peer ${msg.from.substring(0,8)} failed to provide a solution`);
            return { step: 'idle', peerId: null, myChallengeText: null, peerChallengeText: null, mySolutionToPeerChallenge: null, peerSolutionCommitment: null, showCaptchaModal: false };
          }
          
          const peerCommitment = prev.peerSolutionCommitment;
          
          if (!peerCommitment) {
            // Check if this peer is already certified (duplicate reveal)
            if (certifiedPeers.has(msg.from)) {
              console.log('Received duplicate reveal from already certified peer');
              return prev; // Keep current state, ignore duplicate
            }
            
            console.warn('Reveal received but no commitment in state. Current state:', prev);
            // Don't immediately error - try to find commitment from recent messages
            return prev; // Keep state for now
          } 
          
          const computedCommitment = sha256(msg.solution);
          console.log('Verifying commitment match...');
          
          const commitmentCheck = computedCommitment === peerCommitment;
          if (commitmentCheck) {
            message.success(`Peer ${msg.from.substring(0,8)} has been certified!`);
            setCertifiedPeers(prevCertified => new Set(prevCertified).add(msg.from));
            
            // Only reset to idle if this completes the PPE process
            // Use setTimeout to allow any pending reveal messages to be processed
            setTimeout(() => {
              setPpeState(current => {
                // Only reset if we're still in revealing state
                if (current.step === 'revealing' || current.step === 'solving') {
                  return { step: 'idle', peerId: null, myChallengeText: null, peerChallengeText: null, mySolutionToPeerChallenge: null, peerSolutionCommitment: null, showCaptchaModal: false };
                }
                return current;
              });
            }, 100);
            
            return { ...prev, step: 'completed' }; // Mark as completed temporarily
          } else {
            message.error(`Peer ${msg.from.substring(0,8)} provided an invalid solution.`);
            return { step: 'idle', peerId: null, myChallengeText: null, peerChallengeText: null, mySolutionToPeerChallenge: null, peerSolutionCommitment: null, showCaptchaModal: false };
          }
        });
      }
    };

    return () => { if (socketRef.current) socketRef.current.close(); };
  }, [pollId, currentUserId]);

  const resetPpeState = () => {
    setPpeState({
      step: 'idle',
      peerId: null,
      myChallengeText: null,
      peerChallengeText: null,
      mySolutionToPeerChallenge: null,
      peerSolutionCommitment: null,
      challengeStartTime: null,
      showCaptchaModal: false
    });
  };

  const handleStartCertification = (neighborId) => {
    if (ppeState.step !== 'idle') {
      message.error("Please wait for the current PPE process to complete");
      return;
    }

    console.log('WebSocket state:', socketRef.current?.readyState);
    console.log('WebSocket OPEN constant:', WebSocket.OPEN);
    
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      message.info(`Sending PPE request to peer ${neighborId.substring(0, 8)}...`);
      
      // Clear any existing state first
      resetPpeState();
      
      setPpeState({
        step: 'requesting',
        peerId: neighborId,
        challengeStartTime: Date.now()
      });

      socketRef.current.send(JSON.stringify({ 
        type: 'request_ppe', 
        target: neighborId 
      }));

      // Add timeout to revert to idle if no response
      setTimeout(() => {
        setPpeState(current => {
          if (current.peerId === neighborId && 
              (current.step === 'requesting' || current.step === 'waiting_for_challenge')) {
            message.error('Request timed out. Please try again.');
            return {
              step: 'idle',
              peerId: null,
              myChallengeText: null,
              peerChallengeText: null,
              mySolutionToPeerChallenge: null,
              peerSolutionCommitment: null,
              challengeStartTime: null,
              showCaptchaModal: false
            };
          }
          return current;
        });
      }, 10000); // 10 second timeout
    } else {
      const status = socketRef.current ? 
        `Connection state: ${socketRef.current.readyState}` : 
        'No WebSocket connection';
      message.error(`WebSocket connection not ready. ${status}. Please wait and try again.`);
      console.error('WebSocket not ready:', socketRef.current);
    }
  };
  
  const handleCaptchaSolve = (solution) => {
    const timeTaken = Date.now() - ppeStateRef.current.challengeStartTime;
    const timeLimit = 30000; // 30 seconds time bound
    
    if (timeTaken > timeLimit) {
      message.error('You took too long to solve the CAPTCHA');
      setPpeState(prev => ({ ...prev, step: 'idle', showCaptchaModal: false }));
      return;
    }
    
    const commitment = sha256(solution);
    setPpeState(prev => {
      socketRef.current.send(JSON.stringify({ 
        type: 'commitment', 
        target: prev.peerId, 
        commitment: commitment,
        timeTaken
      }));

      if (prev.peerSolutionCommitment) {
        // If we already have their commitment, we can reveal
        socketRef.current.send(JSON.stringify({ 
          type: 'reveal', 
          target: prev.peerId, 
          solution: solution,
          timeTaken
        }));
        return { 
          ...prev, 
          step: 'revealing',
          mySolutionToPeerChallenge: solution,
          showCaptchaModal: false
        };
      } else {
        // Wait for their commitment
        return { 
          ...prev, 
          mySolutionToPeerChallenge: solution,
          showCaptchaModal: false
        };
      }
    });
  };

  const handleCaptchaModalClose = () => {
    setPpeState(prev => ({ ...prev, showCaptchaModal: false, step: 'idle' }));
    message.info('CAPTCHA challenge cancelled');
  };

  const handleVote = async (option) => {
    // Double-check PPE completion before allowing vote
    if (!hasRequiredCertifications || !checkPPECompletion()) {
      message.error('You must complete the PPE process before voting');
      return;
    }

    try {
      const keyPair = await cryptoService.loadKeys();
      if (!keyPair) throw new Error("Keys not loaded.");
      const messageToSign = `${poll.id}:${option}`;
      const signature = await cryptoService.signMessage(keyPair.privateKey, messageToSign);
      const voteData = { publicKey: userPublicKey, option: option, signature: signature };
      await pollApi.submitVote(poll.id, voteData);
      message.success(`Successfully voted for: ${option}`);
      fetchPoll();
    } catch (err) {
      message.error(`Error: ${err.message}`);
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

  const [canVote, setCanVote] = useState(false);
  const [hasRequiredCertifications, setHasRequiredCertifications] = useState(false);

  const checkPPECompletion = () => {
    if (!currentUserId || !poll) return false;
    
    const myNeighbors = calculateNeighbors(
      currentUserId,
      Object.keys(poll.registrants).filter(id => id !== currentUserId).sort()
    );
    
    return myNeighbors.length > 0 && myNeighbors.every(neighborId => certifiedPeers.has(neighborId));
  };

  const fetchUserData = async () => {
    try {
        const verifications = await pollApi.getUserVerifications(pollId, userPublicKey);
        
        const ppeCompleted = checkPPECompletion();
        setHasRequiredCertifications(ppeCompleted);
        
        // Only allow voting if both verifications and PPE are complete
        const canVoteNow = verifications.can_vote && ppeCompleted;
        setCanVote(canVoteNow);
    } catch (error) {
        if (!error.message?.includes('User not registered')) {
            console.error('Failed to check voting eligibility:', error);
        }
        setCanVote(false);
        setHasRequiredCertifications(false);
    }
  };

  // Update eligibility whenever certifiedPeers changes
  useEffect(() => {
    const updateEligibility = async () => {
      if (poll && currentUserId) {
        const ppeCompleted = checkPPECompletion();
        setHasRequiredCertifications(ppeCompleted);
        if (canVote && !ppeCompleted) {
          setCanVote(false);
        }
      }
    };
    updateEligibility();
  }, [certifiedPeers, poll, currentUserId]);

  // Fetch user data when poll or user changes
  useEffect(() => {
    if (poll) {
      fetchUserData();
    }
  }, [poll, pollId, userPublicKey]);

  if (isLoading) return <Spin size="large" />;
  if (!poll) return <Alert message="Poll not found" type="error" />;

  const hasVoted = currentUserId && poll.votes[currentUserId];

  const renderRegisteredUsers = () => {
    const myVerificationStatus = poll.verifications[currentUserId] || { verified_by: [] };
    const myVerificationCount = myVerificationStatus.verified_by.length;
    
    return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card title="Your Verification Status">
        <Alert
          message={
            <Space direction="vertical">
              <Text>Your ID: {currentUserId ? currentUserId.substring(0, 12) + '...' : 'Loading...'}</Text>
              <Text>
                You have {myVerificationCount} verification{myVerificationCount !== 1 ? 's' : ''}
                {myVerificationCount >= 2 ? ' (Ready to vote)' : ` (Need ${2 - myVerificationCount} more)`}
              </Text>
              <Text>
                Verified by: {myVerificationStatus.verified_by.length > 0 
                  ? myVerificationStatus.verified_by.map(id => id.substring(0, 8) + '...').join(', ')
                  : 'No verifications yet'}
              </Text>
            </Space>
          }
          type={myVerificationCount >= 2 ? "success" : "warning"}
          showIcon
        />
      </Card>

      <Card title="Verify Other Users">
        <Alert
          message="Quick Verification Guide"
          description="1. Verify each user below 2. Have them verify you back 3. Complete PPE with your neighbors"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <List
          dataSource={Object.entries(poll.registrants)
            .filter(([id]) => id !== currentUserId)
            .map(([id]) => ({
              id,
              hasVerified: poll.verifications[id]?.verified_by.includes(currentUserId),
              verificationCount: poll.verifications[id]?.verified_by.length || 0,
              canVote: poll.verifications[id]?.verified_by.length >= 2,
              verifiedBy: poll.verifications[id]?.verified_by || []
            }))}
          renderItem={(user) => (
            <List.Item
              actions={[
                user.hasVerified ? (
                  <Text type="success">
                    <CheckCircleOutlined /> Verified
                  </Text>
                ) : (
                  <Button
                    type="primary"
                    onClick={() => handleVerifyUser(user.id)}
                    icon={<CheckCircleOutlined />}
                  >
                    Verify User
                  </Button>
                )
              ]}
            >
              <List.Item.Meta
                avatar={<UserOutlined />}
                title={`User: ${user.id.substring(0, 12)}...`}
                description={
                  <Space direction="vertical">
                    <Text>
                      {user.verificationCount} verification{user.verificationCount !== 1 ? 's' : ''} 
                      {user.canVote ? " (Can vote)" : ` (Needs ${2 - user.verificationCount} more)`}
                    </Text>
                    <Text type="secondary">
                      Verified by: {user.verifiedBy.length > 0 
                        ? user.verifiedBy.map(id => id.substring(0, 8) + '...').join(', ')
                        : 'No verifications yet'}
                    </Text>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      </Card>
    </Space>
  );
};

  return (
    <Space direction="vertical" size="large" style={{ width: '100%', maxWidth: 800 }}>
      <Card>
        <Title level={2}>{poll.question}</Title>
      </Card>

      {!hasVoted && (
        <Card title={<Title level={3}>Cast Your Vote</Title>}>
          {!hasRequiredCertifications ? (
            <Alert
              message="Complete PPE Verification"
              description="You must complete the Proof of Private Effort process with your peers before voting."
              type="warning"
              showIcon
            />
          ) : !canVote ? (
            <Alert
              message="Verification Required"
              description="You need to be verified by other users before you can vote."
              type="warning"
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
      )}

      {hasVoted && (
        <Card title={<Title level={3}>Your Vote</Title>}>
          <Alert
            message="Vote Submitted"
            description={`You have voted for: ${poll.votes[currentUserId]?.option}`}
            type="success"
            showIcon
          />
        </Card>
      )}

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

      {!hasVoted && currentUserId && (
        <Card title={<Title level={3}><LockOutlined /> Step 1: Complete PPE with Peers</Title>}>
          <Alert
            message="Peer-to-Peer Effort (PPE) Verification"
            description="You need to complete a CAPTCHA challenge with each of your assigned neighbors. Both you and your neighbor must successfully solve each other's challenges to establish certification."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
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

      {renderRegisteredUsers()}

      <Button 
        icon={<HomeOutlined />}
        onClick={navigateToHome}
        style={{ alignSelf: 'center' }}
      >
        Back to Home
      </Button>

      {ppeState.showCaptchaModal && (
        <CaptchaModal
          challengeText={ppeState.peerChallengeText}
          peerId={ppeState.peerId}
          onSolve={handleCaptchaSolve}
          onClose={handleCaptchaModalClose}
        />
      )}
    </Space>
  );
}

export default PollVotePage;
