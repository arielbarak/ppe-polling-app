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
  const certifiedPeersRef = useRef(certifiedPeers);
  certifiedPeersRef.current = certifiedPeers;
  
  const [recentlyJoinedUsers, setRecentlyJoinedUsers] = useState(new Set());
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const previousPollRef = useRef(null);

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
      
      // Check for new users by comparing with previous poll data
      if (previousPollRef.current) {
        const previousUsers = new Set(Object.keys(previousPollRef.current.registrants));
        const currentUsers = new Set(Object.keys(pollData.registrants));
        
        // Find newly joined users
        const newUsers = [...currentUsers].filter(userId => !previousUsers.has(userId));
        
        // Show notifications for new users (except current user)
        newUsers.forEach(userId => {
          if (userId !== currentUserId) {
            console.log('New user detected:', userId.substring(0, 8));
            message.info(`New user joined: ${userId.substring(0, 8)}...`, 3);
            
            // Add to recently joined users for visual highlight
            setRecentlyJoinedUsers(prev => new Set(prev).add(userId));
            // Remove from recently joined after 5 seconds
            setTimeout(() => {
              setRecentlyJoinedUsers(prev => {
                const newSet = new Set(prev);
                newSet.delete(userId);
                return newSet;
              });
            }, 5000);
          }
        });
        
        // Check for new votes
        const previousVotes = Object.keys(previousPollRef.current.votes).length;
        const currentVotes = Object.keys(pollData.votes).length;
        if (currentVotes > previousVotes) {
          console.log('New vote detected');
          message.info(`New vote cast! Total votes: ${currentVotes}`, 2);
        }
      }
      
      // Store current poll data for next comparison
      previousPollRef.current = pollData;
      setPoll(pollData);
      setLastUpdated(new Date());
      
      // Also refresh PPE certifications if user is available
      if (userPublicKey && pollData) {
        loadPPECertifications();
      }
    } catch (error) {
      console.error('Failed to fetch poll:', error);
      // Don't show error message for network issues during background fetching
    } finally {
      setIsLoading(false);
    }
  };

  const loadPPECertifications = async () => {
    if (!userPublicKey || !pollId) return;
    
    try {
      const certifications = await pollApi.getPPECertifications(pollId, userPublicKey);
      console.log('Loaded PPE certifications from backend:', certifications.certified_peers);
      setCertifiedPeers(new Set(certifications.certified_peers));
    } catch (error) {
      console.error('Failed to load PPE certifications:', error);
      // Don't show error for unregistered users
      if (!error.message?.includes('not registered')) {
        // Keep existing state on error
      }
    }
  };
  
  // Initial fetch and setup polling
  useEffect(() => {
    fetchPoll();
    
    // Set up polling every 5 seconds as backup (WebSocket handles most real-time updates)
    const pollInterval = setInterval(() => {
      fetchPoll();
    }, 5000);
    
    // Cleanup interval on unmount
    return () => {
      clearInterval(pollInterval);
    };
  }, [pollId]);

  // Initial PPE certifications load - subsequent loads happen via polling
  useEffect(() => {
    if (poll && userPublicKey && currentUserId) {
      loadPPECertifications();
    }
  }, [currentUserId]); // Only run when currentUserId changes, not on every poll update

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

      // Handle real-time updates for registration and verification stages
      if (msg.type === 'user_registered') { 
        console.log('WebSocket: user_registered event received, triggering fetchPoll()');
        fetchPoll();
        // Show notification for new user
        const userId = msg.userId || msg.from;
        if (userId && userId !== currentUserId) {
          message.info(`New user joined: ${userId.substring(0, 8)}...`, 3);
        }
      }

      if (msg.type === 'user_verified') { 
        fetchPoll(); 
        message.success('User verification updated!', 2);
      }

      if (msg.type === 'vote_cast') {
        fetchPoll();
        message.info(`New vote cast for: ${msg.option}`, 2);
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
          content: (
            <div>
              <p>Peer {msg.from.substring(0,8)}... wants to complete Proof of Private Effort (PPE) verification with you.</p>
              <p><strong>Both participants will solve CAPTCHA challenges to prove they are human.</strong></p>
              <p>Accept this request?</p>
            </div>
          ),
          onOk() {
            message.info('PPE certification accepted! Preparing challenges...');
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

        message.success(`Peer ${msg.from.substring(0,8)}... accepted your PPE request! Starting challenges...`);
        
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
            message.success('Peer completed their challenge! Verifying solutions...');
            return { 
              ...prev, 
              step: 'revealing',
              peerSolutionCommitment: msg.commitment 
            };
          } else {
            // Still need to solve it - peer finished first, waiting for us
            message.info(`Peer ${msg.from.substring(0,8)}... completed their challenge. Please complete yours!`);
            return { 
              ...prev,
              peerSolutionCommitment: msg.commitment 
            };
          }
        });
      }

      if (msg.type === 'reveal') {
        console.log('Reveal message received from:', msg.from.substring(0,8));
        
        // Check if this peer is already certified to avoid duplicate processing
        if (certifiedPeersRef.current.has(msg.from)) {
          return;
        }
        
        if (msg.solution === null) {
          message.error(`Peer ${msg.from.substring(0,8)} failed to provide a solution`);
          return;
        }
        
        // Store the commitment temporarily in case state is reset
        const currentState = ppeStateRef.current;
        let peerCommitment = currentState.peerSolutionCommitment;
        
        // If no commitment in current state, but we're expecting this peer, it might be a race condition
        if (!peerCommitment && (currentState.peerId === msg.from || currentState.step !== 'idle')) {
          // Give it a moment for the commitment to be processed
          setTimeout(() => {
            // Retry processing this reveal message
            const retryState = ppeStateRef.current;
            if (retryState.peerSolutionCommitment && !certifiedPeersRef.current.has(msg.from)) {
              processRevealMessage(msg, retryState.peerSolutionCommitment);
            }
          }, 50);
          return;
        }
        
        if (!peerCommitment) {
          return;
        }
        
        processRevealMessage(msg, peerCommitment);
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
        message.success('CAPTCHA completed! Verifying with peer...');
        return { 
          ...prev, 
          step: 'revealing',
          mySolutionToPeerChallenge: solution,
          showCaptchaModal: false
        };
      } else {
        // Wait for their commitment
        message.info(`CAPTCHA completed! Waiting for peer ${prev.peerId.substring(0,8)}... to finish their challenge.`);
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

  // Helper function to process reveal messages
  const processRevealMessage = (msg, peerCommitment) => {
    const computedCommitment = sha256(msg.solution);
    console.log('Verifying commitment match...');
    
    const commitmentCheck = computedCommitment === peerCommitment;
    if (commitmentCheck) {
      // Show a prominent success message for certification
      message.success({
        content: `Certification Complete! Peer ${msg.from.substring(0,8)}... has been verified and certified.`,
        duration: 4,
        style: {
          marginTop: '20vh',
        },
      });
      console.log('Adding peer to certified list:', msg.from.substring(0,8));
      setCertifiedPeers(prevCertified => {
        const newSet = new Set(prevCertified).add(msg.from);
        console.log('Updated certified peers:', Array.from(newSet).map(id => id.substring(0,8)));
        return newSet;
      });

      // Save PPE certification to backend
      if (poll && userPublicKey) {
        const peerPublicKey = poll.registrants[msg.from];
        if (peerPublicKey) {
          pollApi.recordPPECertification(poll.id, userPublicKey, peerPublicKey)
            .then(() => {
              console.log('PPE certification saved to backend');
            })
            .catch((error) => {
              console.error('Failed to save PPE certification:', error);
            });
        }
      }
      
      // Reset PPE state after successful certification
      setPpeState(prev => {
        if (prev.peerId === msg.from || prev.step === 'revealing') {
          return { step: 'idle', peerId: null, myChallengeText: null, peerChallengeText: null, mySolutionToPeerChallenge: null, peerSolutionCommitment: null, showCaptchaModal: false };
        }
        return prev;
      });
    } else {
      message.error(`Peer ${msg.from.substring(0,8)} provided an invalid solution.`);
    }
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
  const [userVerificationComplete, setUserVerificationComplete] = useState(false);

  const checkPPECompletion = () => {
    if (!currentUserId || !poll) return false;
    
    const myNeighbors = calculateNeighbors(
      currentUserId,
      Object.keys(poll.registrants).filter(id => id !== currentUserId).sort()
    );
    
    const isComplete = myNeighbors.length > 0 && myNeighbors.every(neighborId => certifiedPeers.has(neighborId));
    console.log('PPE Completion Check:', { 
      myNeighbors, 
      certifiedPeers: Array.from(certifiedPeers), 
      isComplete 
    });
    return isComplete;
  };

  const fetchUserData = async () => {
    try {
        const verifications = await pollApi.getUserVerifications(pollId, userPublicKey);
        
        const ppeCompleted = checkPPECompletion();
        setHasRequiredCertifications(ppeCompleted);
        
        // Check if verification just became complete
        const wasVerificationComplete = userVerificationComplete;
        const isVerificationComplete = verifications.can_vote;
        setUserVerificationComplete(isVerificationComplete);
        
        // Show success message when verification completes (but don't auto-start PPE)
        if (!wasVerificationComplete && isVerificationComplete && !ppeCompleted) {
            console.log('Verification completed! User can now start PPE manually.');
            message.success({
                content: 'Congratulations! You are now verified and can start the PPE process with your neighbors.',
                duration: 5,
            });
        }
        
        // Only allow voting if both verifications and PPE are complete
        const canVoteNow = verifications.can_vote && ppeCompleted;
        setCanVote(canVoteNow);
    } catch (error) {
        if (!error.message?.includes('User not registered')) {
            console.error('Failed to check voting eligibility:', error);
        }
        setCanVote(false);
        setHasRequiredCertifications(false);
        setUserVerificationComplete(false);
    }
  };

  // Update eligibility whenever certifiedPeers changes
  useEffect(() => {
    const updateEligibility = async () => {
      if (poll && currentUserId) {
        const ppeCompleted = checkPPECompletion();
        setHasRequiredCertifications(ppeCompleted);
        
        // If PPE is now complete, check full voting eligibility
        if (ppeCompleted) {
          await fetchUserData();
        } else if (canVote && !ppeCompleted) {
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

  // Auto-highlight voting section when user becomes eligible to vote
  useEffect(() => {
    console.log('Auto-highlight check:', { poll: !!poll, currentUserId: !!currentUserId, canVote, hasVoted: poll?.votes[currentUserId] });
    if (poll && currentUserId && canVote && !poll.votes[currentUserId]) {
      console.log('Triggering auto-highlight for voting section!');
      // Show prominent success message
      message.success({
        content: 'Congratulations! You have completed all PPE verifications and can now vote!',
        duration: 6,
        style: {
          marginTop: '20vh',
        },
      });
      
      // Scroll to voting section after a brief delay
      setTimeout(() => {
        const votingSection = document.querySelector('[data-section="voting"]');
        if (votingSection) {
          votingSection.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
          });
        }
      }, 1000);
    }
  }, [canVote, poll, currentUserId]);

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
                {myVerificationCount >= 2 ? ' (Verified)' : ` (Need ${2 - myVerificationCount} more)`}
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

      <Card title={`Verify Other Users (${Object.keys(poll.registrants).length - 1} others online)`}>
        <Alert
          message="Live User List - Updates Automatically"
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
              style={recentlyJoinedUsers.has(user.id) ? {
                backgroundColor: '#f6ffed',
                border: '1px solid #b7eb8f',
                borderRadius: '6px',
                transition: 'all 0.3s ease'
              } : {}}
              actions={[
                recentlyJoinedUsers.has(user.id) && (
                  <Text type="success" style={{ marginRight: 8 }}>
                    🆕 New!
                  </Text>
                ),
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
              ].filter(Boolean)}
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
        <Text type="secondary">
          {Object.keys(poll.registrants).length} users registered • 
          {Object.keys(poll.votes).length} votes cast • 
          Auto-refresh every 3s • 
          Last updated: {lastUpdated.toLocaleTimeString()}
        </Text>
      </Card>      {!hasVoted && (
        <Card 
          title={<Title level={3}>Cast Your Vote</Title>} 
          data-section="voting"
          style={canVote ? { 
            border: '2px solid #52c41a', 
            boxShadow: '0 4px 12px rgba(82, 196, 26, 0.15)' 
          } : {}}
        >
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
