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
  const [modal, contextHolder] = Modal.useModal();
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
    challengeStartTime: null,
    showCaptchaModal: false
  });
  const ppeStateRef = useRef(ppeState);
  ppeStateRef.current = ppeState;

  // Monitor PPE state changes
  useEffect(() => {
    // Just monitor state changes, no need for debug logs
  }, [ppeState]);

  const currentUserId = useMemo(() => {
    if (!poll || !userPublicKey) return null;
    const entry = Object.entries(poll.registrants).find(
      ([userId, key]) => JSON.stringify(key) === JSON.stringify(userPublicKey)
    );
    return entry ? entry[0] : null;
  }, [poll, userPublicKey]);

  const neighbors = useMemo(() => {
    if (!poll || !currentUserId) return [];
    const allUserIds = Object.keys(poll.registrants).filter(id => id !== currentUserId).sort();
    const neighborsList = calculateNeighbors(currentUserId, allUserIds);
    console.log('Calculated neighbors:', neighborsList);
    return neighborsList;
  }, [poll, currentUserId]);

  const fetchPoll = async () => {
    try {
      // Only show loading state on initial load
      if (!poll) setIsLoading(true);
      
      // Try to get poll from local storage first
      const cachedPollData = localStorage.getItem(`poll_${pollId}`);
      let pollData;
      
      try {
        // Try to fetch from backend
        pollData = await pollApi.getPoll(pollId);
        // Cache the poll data
        localStorage.setItem(`poll_${pollId}`, JSON.stringify(pollData));
        console.log('Poll data fetched from server and cached');
      } catch (error) {
        // If backend fetch fails and we have cached data, use it
        if (cachedPollData) {
          console.log('Using cached poll data');
          pollData = JSON.parse(cachedPollData);
          message.warning('Using cached poll data. Some information may be outdated.');
        } else {
          // No cached data and backend failed
          throw error;
        }
      }
      
      // Detect newly joined users
      if (previousPollRef.current) {
        const prevRegistrants = Object.keys(previousPollRef.current.registrants);
        const currentRegistrants = Object.keys(pollData.registrants);
        const newUsers = currentRegistrants.filter(id => !prevRegistrants.includes(id));
        
        if (newUsers.length > 0) {
          // Add them to the recently joined list
          const updatedRecentlyJoined = new Set(recentlyJoinedUsers);
          newUsers.forEach(id => updatedRecentlyJoined.add(id));
          setRecentlyJoinedUsers(updatedRecentlyJoined);
          
          // Show notifications for new users (only if not from WebSocket)
          if (!pollData._fromWebSocket) {
            newUsers.forEach(id => {
              if (id !== currentUserId) {
                message.info(`New user joined: ${id.substring(0, 8)}...`, 3);
              }
            });
          }
        }
      }
      
      previousPollRef.current = pollData;
      setPoll(pollData);
      setLastUpdated(new Date());
      
      // Load PPE certifications when poll updates
      if (pollData && userPublicKey && currentUserId) {
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
        message.error('Failed to load PPE certifications');
      }
    }
  };
  
  // Initial fetch and setup polling
  useEffect(() => {
    fetchPoll();
    
    // // Set up polling for updates
    // const pollInterval = setInterval(() => {
    //   fetchPoll();
    // }, 5000); // Poll every 5 seconds
    
    // Cleanup interval on unmount
    // return () => {
    //   clearInterval(pollInterval);
    // };
  }, [pollId]);

  // Initial PPE certifications load - subsequent loads happen via polling
  useEffect(() => {
    if (poll && userPublicKey && currentUserId) {
      loadPPECertifications();
    }
  }, [currentUserId]); // Only run when currentUserId changes, not on every poll update

  useEffect(() => {
    console.log('Setting up WebSocket effect. pollId:', pollId, 'currentUserId:', currentUserId);
    
    if (!pollId || !currentUserId) {
      return;
    }
    
    // Clean currentUserId to remove any quotes that might be in it
    const cleanUserId = currentUserId.replace(/"/g, '');
    const wsUrl = `ws://localhost:8000/ws/${pollId}/${cleanUserId}`;
    
    // Close any existing connection first
    if (socketRef.current && socketRef.current.readyState !== WebSocket.CLOSED) {
      socketRef.current.close();
    }
    
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      console.log('WebSocket connected');
    };

    socket.onclose = (event) => {
      console.log('WebSocket disconnected', event);
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log('WebSocket message received:', msg);
        
        const currentPpeState = ppeStateRef.current;

        // Handle error messages
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
          if (ppeState.step !== 'idle') {
            socketRef.current.send(JSON.stringify({ 
              type: 'reject_ppe', 
              target: msg.from,
              reason: 'busy'
            }));
            return;
          }

          const myChallenge = generateCaptchaText();
          console.log('Received PPE request, showing modal...');

          modal.confirm({
            zIndex: 1500,
            width: 500,
            maskClosable: false,
            centered: true,
            destroyOnClose: true,
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
                ...ppeState,
                step: 'challenging',
                peerId: msg.from,
                myChallengeText: myChallenge,
                challengeStartTime: Date.now()
              });

              // First accept, then immediately send our challenge
              socketRef.current.send(JSON.stringify({
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
                    socketRef.current.send(JSON.stringify({
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
              socketRef.current.send(JSON.stringify({
                type: 'reject_ppe',
                target: msg.from
              }));
              modal.destroy();
            },
            autoFocusButton: 'cancel'
          });
          
          // Force update modal position after a short delay
          setTimeout(() => {
            modal.update({});
          }, 100);
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
              socketRef.current.send(JSON.stringify({
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
          resetPpeState();
        }

        if (msg.type === 'challenge') {
          // Verify we're in a valid state to receive a challenge
          const validStates = ['waiting_for_challenge', 'challenging', 'requesting'];
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
              resetPpeState();
            });
        }

        if (msg.type === 'commitment') {
          setPpeState(prev => {
            if (prev.peerId !== msg.from) {
              console.warn('Received commitment from unexpected peer', msg.from);
              return prev;
            }
            return { ...prev, peerSolutionCommitment: msg.commitment };
          });

          // If we already have our solution, then we can send the reveal
          if (currentPpeState.mySolutionToPeerChallenge) {
            socketRef.current.send(JSON.stringify({ 
              type: 'reveal', 
              target: msg.from, 
              solution: currentPpeState.mySolutionToPeerChallenge 
            }));
          }
        }

        if (msg.type === 'reveal') {
          // Check we have the expected peer commitment
          if (currentPpeState.peerId !== msg.from) {
            console.warn('Received reveal from unexpected peer', msg.from);
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
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
      }
    };

    return () => { 
      console.log('Cleaning up WebSocket connection');
      if (socketRef.current) {
        console.log('Closing WebSocket connection on unmount');
        socketRef.current.close(); 
      }
    };
  }, [pollId, currentUserId]);

  const resetPpeState = () => {
    console.log('Resetting PPE state to idle');
    const initialState = {
      step: 'idle',
      peerId: null,
      myChallengeText: null,
      peerChallengeText: null,
      mySolutionToPeerChallenge: null,
      peerSolutionCommitment: null,
      challengeStartTime: null,
      showCaptchaModal: false
    };
    console.log('New PPE state will be:', initialState);
    setPpeState(initialState);
  };

  const handleStartCertification = (neighborId) => {
    console.log('handleStartCertification called with neighborId:', neighborId);
    if (ppeState.step !== 'idle') {
      message.error("Please wait for the current PPE process to complete");
      return;
    }

    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      console.log('Starting certification with neighbor:', neighborId);
      message.info(`Sending PPE request to peer ${neighborId.substring(0, 8)}...`);
      
      // Clear any existing state first
      resetPpeState();
      
      // Update state
      setPpeState({
        step: 'requesting',
        peerId: neighborId,
        challengeStartTime: Date.now()
      });
      
      // Send the request
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
    console.log('CAPTCHA solved, solution:', solution);
    
    if (!solution || solution.trim() === '') {
      message.error('Please enter a valid solution');
      return;
    }
    
    const timeTaken = Date.now() - ppeStateRef.current.challengeStartTime;
    const timeLimit = 30000; // 30 seconds time bound
    
    if (timeTaken > timeLimit) {
      message.error('Time limit exceeded for CAPTCHA. Please try again.');
      resetPpeState();
      return;
    }
    
    const commitment = sha256(solution);
    console.log('Generated commitment:', commitment);
    
    setPpeState(prev => {
      console.log('Current state in handleCaptchaSolve:', prev);
      
      if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
        message.error('WebSocket connection lost. Please try again.');
        return { ...prev, step: 'idle', showCaptchaModal: false };
      }
      
      try {
        socketRef.current.send(JSON.stringify({ 
          type: 'commitment', 
          target: prev.peerId, 
          commitment: commitment,
          timeTaken
        }));
        console.log('Sent commitment to peer:', prev.peerId.substring(0, 8));
      } catch (error) {
        console.error('Failed to send commitment:', error);
        message.error('Failed to send solution commitment');
        return { ...prev, step: 'idle', showCaptchaModal: false };
      }

      if (prev.peerSolutionCommitment) {
        // If we already have their commitment, we can reveal
        try {
          socketRef.current.send(JSON.stringify({ 
            type: 'reveal', 
            target: prev.peerId, 
            solution: solution,
            timeTaken
          }));
          console.log('Sent reveal to peer:', prev.peerId.substring(0, 8));
          message.success('CAPTCHA completed! Verifying with peer...');
        } catch (error) {
          console.error('Failed to send reveal:', error);
          message.error('Failed to send solution reveal');
          return { ...prev, step: 'idle', showCaptchaModal: false };
        }
        
        return { 
          ...prev, 
          step: 'revealing',
          mySolutionToPeerChallenge: solution,
          showCaptchaModal: false
        };
      } else {
        return {
          ...prev,
          mySolutionToPeerChallenge: solution,
          showCaptchaModal: false
        };
      }
    });
  };

  const handleCaptchaModalClose = () => {
    console.log('CAPTCHA modal closing, current state:', ppeState);
    setPpeState(prev => {
      console.log('Resetting PPE state from:', prev);
      const newState = { 
        ...prev, 
        showCaptchaModal: false, 
        step: 'idle',
        peerChallengeText: null,
        mySolutionToPeerChallenge: null,
        peerSolutionCommitment: null
      };
      console.log('New state after CAPTCHA modal close:', newState);
      return newState;
    });
    message.info('CAPTCHA challenge cancelled');
  };
  

  // Helper function to process reveal messages
  const processRevealMessage = (msg, peerCommitment) => {
    console.log('Processing reveal message from:', msg.from.substring(0, 8));
    console.log('Solution received:', msg.solution);
    console.log('Expected commitment:', peerCommitment);
    
    const computedCommitment = sha256(msg.solution);
    console.log('Computed commitment:', computedCommitment);
    console.log('Verifying commitment match...');
    
    const commitmentCheck = computedCommitment === peerCommitment;
    console.log('Commitment check result:', commitmentCheck);
    
    if (commitmentCheck) {
      // Show a prominent success message for certification
      message.success({
        content: `Peer ${msg.from.substring(0, 8)}... has been certified!`,
        duration: 4,
        style: {
          marginTop: '20vh',
        },
      });
      
      // Add this peer to our certified list
      setCertifiedPeers(prev => {
        const updated = new Set(prev);
        updated.add(msg.from);
        return updated;
      });
      
      // Also check if we're now eligible to vote
      setTimeout(checkPPECompletion, 500);
    } else {
      message.error({
        content: `Peer ${msg.from.substring(0, 8)}... provided an invalid solution!`,
        duration: 4,
        style: {
          marginTop: '20vh',
        },
      });
    }
    
    // Reset PPE state
    resetPpeState();
  };

  const handleVote = async (option) => {
    if (!canVote) {
      message.error('You are not eligible to vote yet');
      return;
    }
    
    try {
      setIsLoading(true);
      message.loading('Submitting your vote...', 1.5);
      
      // Prepare the vote data
      const keyPair = await cryptoService.loadKeys();
      if (!keyPair) throw new Error('No keypair found');
      
      // Create message to sign
      const messageToSign = `${pollId}:${option}`;
      
      // Sign it with our private key
      const signature = await cryptoService.signMessage(keyPair.privateKey, messageToSign);
      
      // Send the vote to the server
      const voteData = {
        publicKey: userPublicKey,
        option: option,
        signature: signature
      };
      
      await pollApi.submitVote(pollId, voteData);
      
      // Show success and refresh
      message.success(`Vote submitted for: ${option}`, 3);
      fetchPoll();
    } catch (error) {
      console.error('Failed to submit vote:', error);
      message.error(`Failed to submit vote: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyUser = async (userId) => {
    try {
      setIsLoading(true);
      message.loading('Verifying user...', 1.5);
      
      // Get keypair
      const keyPair = await cryptoService.loadKeys();
      if (!keyPair) throw new Error('No keypair found');
      
      // Create message to sign
      const messageToSign = `verify:${pollId}:${userId}`;
      
      // Sign it with our private key
      const signature = await cryptoService.signMessage(keyPair.privateKey, messageToSign);
      
      // Send the verification to the server
      const verificationData = {
        publicKey: userPublicKey,
        target: userId,
        signature: signature
      };
      
      await pollApi.verifyUser(pollId, verificationData);
      
      // Show success and refresh
      message.success(`User ${userId.substring(0, 8)}... verified successfully`, 3);
      fetchPoll();
      fetchUserData();
    } catch (error) {
      console.error('Failed to verify user:', error);
      message.error(`Failed to verify user: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const [canVote, setCanVote] = useState(false);
  const [hasRequiredCertifications, setHasRequiredCertifications] = useState(false);
  const [userVerificationComplete, setUserVerificationComplete] = useState(false);

  const checkPPECompletion = () => {
    if (!poll || !currentUserId) return false;
    
    // Calculate our expected neighbors
    const myNeighbors = calculateNeighbors(
      currentUserId, 
      Object.keys(poll.registrants).filter(id => id !== currentUserId)
    );
    
    const isComplete = myNeighbors.length > 0 && myNeighbors.every(neighborId => certifiedPeers.has(neighborId));
    return isComplete;
  };

  const fetchUserData = async () => {
    try {
      if (!pollId || !userPublicKey) return;
      
      const verifications = await pollApi.getUserVerifications(pollId, userPublicKey);
      setUserVerificationComplete(verifications.is_verified);
    } catch (error) {
      console.error('Failed to fetch user status:', error);
    }
  };

  // Update eligibility whenever certifiedPeers changes
  useEffect(() => {
    const hasCompletedPPE = checkPPECompletion();
    setHasRequiredCertifications(hasCompletedPPE);
    
    // Only update can vote if both conditions are met
    setCanVote(hasCompletedPPE && userVerificationComplete);
    
    if (hasCompletedPPE && !userVerificationComplete) {
      console.log('Verification completed! User can now start PPE manually.');
      message.info('PPE verification completed! Now wait for user verification.', 3);
    } else if (hasCompletedPPE && userVerificationComplete && !canVote) {
      message.success('You are now eligible to vote!', 3);
    }
  }, [certifiedPeers, poll, currentUserId]);

  // Fetch user data when poll or user changes
  useEffect(() => {
    if (poll && pollId && userPublicKey) {
      fetchUserData();
    }
  }, [poll, pollId, userPublicKey]);

  // Define hasVoted here, before it's used in the next useEffect
  const hasVoted = poll && currentUserId && poll.votes && poll.votes[currentUserId];

  // Auto-highlight voting section when user becomes eligible to vote
  useEffect(() => {
    console.log('Auto-highlight check:', {poll: !!poll, currentUserId: !!currentUserId, canVote, hasVoted});
    if (poll && currentUserId && canVote && !poll.votes[currentUserId]) {
      const votingSection = document.querySelector('[data-section="voting"]');
      if (votingSection) {
        // Scroll to voting section
        votingSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Add a pulse animation
        votingSection.classList.add('highlight-pulse');
        setTimeout(() => {
          votingSection.classList.remove('highlight-pulse');
        }, 2000);
      }
    }
  }, [canVote, poll, currentUserId]);

  if (isLoading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
      <Spin size="large" />
    </div>
  );

  if (!poll) return (
    <Card>
      <Alert
        message="Poll Not Found"
        description="The requested poll could not be found or has been deleted."
        type="error"
        showIcon
      />
    </Card>
  );

  const renderRegisteredUsers = () => {
    const usersToRender = [];
    
    // First add the current user
    if (currentUserId) {
      usersToRender.push({
        id: currentUserId,
        isCurrentUser: true
      });
    }
    
    // Then add verified users
    Object.keys(poll.verifications || {}).forEach(id => {
      if (id !== currentUserId) {
        usersToRender.push({
          id,
          isVerified: true
        });
      }
    });
    
    // Add remaining unverified users
    Object.keys(poll.registrants).forEach(id => {
      if (id !== currentUserId && !poll.verifications?.[id]) {
        usersToRender.push({ id });
      }
    });
    
    return (
      <Card title={<Title level={3}><LockOutlined /> Step 2: User Verification</Title>}>
        <Alert
          message="User Verification"
          description="For additional security, users need to be verified by at least one other user before voting. This helps prevent Sybil attacks where a single person creates multiple accounts."
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <List
          dataSource={usersToRender}
          renderItem={user => (
            <List.Item
              actions={[
                user.isCurrentUser ? (
                  userVerificationComplete ? (
                    <Text type="success"><CheckCircleOutlined /> Verified</Text>
                  ) : (
                    <Text type="warning">Waiting for verification</Text>
                  )
                ) : (
                  hasRequiredCertifications && !(Array.isArray(poll.verifications?.[user.id]) && poll.verifications?.[user.id]?.includes(currentUserId)) ? (
                    <Button 
                      type="primary"
                      onClick={() => handleVerifyUser(user.id)}
                    >
                      Verify User
                    </Button>
                  ) : (
                    Array.isArray(poll.verifications?.[user.id]) && poll.verifications?.[user.id]?.includes(currentUserId) ? (
                      <Text type="success"><CheckCircleOutlined /> Verified by you</Text>
                    ) : (
                      <Button disabled>
                        Verify User
                      </Button>
                    )
                  )
                )
              ]}
            >
              <List.Item.Meta
                avatar={<UserOutlined />}
                title={
                  <>
                    {user.isCurrentUser ? (
                      <Text strong>You: {user.id.substring(0, 12)}...</Text>
                    ) : (
                      <Text>User: {user.id.substring(0, 12)}...</Text>
                    )}
                    {recentlyJoinedUsers.has(user.id) && (
                      <Text type="success" style={{ marginLeft: 8 }}>
                        New
                      </Text>
                    )}
                  </>
                }
                description={
                  user.isVerified ? (
                    <Text type="success">Verified by {(Array.isArray(poll.verifications?.[user.id]) ? poll.verifications[user.id] : []).length} user(s)</Text>
                  ) : user.isCurrentUser ? (
                    userVerificationComplete ? (
                      <Text type="success">Verified by {(Array.isArray(poll.verifications?.[user.id]) ? poll.verifications[user.id] : []).length} user(s)</Text>
                    ) : (
                      <Text type="warning">Waiting to be verified by other users</Text>
                    )
                  ) : (
                    <Text type="secondary">
                      {(Array.isArray(poll.verifications?.[user.id]) ? poll.verifications[user.id] : []).length} verification(s)
                    </Text>
                  )
                }
              />
            </List.Item>
          )}
        />
      </Card>
    );
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%', maxWidth: 800 }}>
      {contextHolder}
      <Card>
        <Title level={2}>{poll.question}</Title>
        <Text type="secondary">
          {Object.keys(poll.registrants).length} users registered • 
          {Object.keys(poll.votes).length} votes cast • 
          Auto-refresh every 3s • 
          Last updated: {lastUpdated.toLocaleTimeString()}
        </Text>
      </Card>
      
      {!hasVoted && (
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
            // Count votes for this option
            const voteCount = Object.values(poll.votes)
              .filter(vote => vote.option === option)
              .length;
            
            // Calculate percentage
            const totalVotes = Object.keys(poll.votes).length;
            const percentage = totalVotes ? (voteCount / totalVotes) * 100 : 0;
            
            return (
              <List.Item>
                <List.Item.Meta
                  title={option}
                  description={
                    <Progress 
                      percent={percentage} 
                      strokeColor="#1890ff"
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
                  neighbors.length ? (
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
                  ) : null
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

      {/* CAPTCHA Modal - render based on state */}
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