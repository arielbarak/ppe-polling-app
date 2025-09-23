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

function PollVotePageSimple({ pollId, userPublicKey, navigateToHome }) {
  const [poll, setPoll] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const socketRef = useRef(null);
  const [certifiedPeers, setCertifiedPeers] = useState(new Set());
  const [neighbors, setNeighbors] = useState([]);
  const [currentUserId, setCurrentUserId] = useState(null);

  // Simple PPE state
  const [ppeState, setPpeState] = useState({
    step: 'idle',
    peerId: null,
    myChallengeText: null,
    peerChallengeText: null,
    mySolutionToPeerChallenge: null,
    peerSolutionCommitment: null,
    showCaptchaModal: false
  });

  // Setup WebSocket
  useEffect(() => {
    if (!pollId || !currentUserId) return;
    
    const wsUrl = `ws://localhost:8000/ws/${pollId}/${currentUserId}`;
    console.log('Connecting to WebSocket:', wsUrl);
    
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      console.log('WebSocket connected');
    };

    socket.onmessage = (event) => {
      console.log('Received message:', event.data);
      try {
        const msg = JSON.parse(event.data);
        
        if (msg.type === 'request_ppe') {
          console.log('Received PPE request from:', msg.from);
          // We would handle the request here
        }
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    };

    return () => {
      if (socketRef.current) socketRef.current.close();
    };
  }, [pollId, currentUserId]);

  // Fetch poll data
  useEffect(() => {
    const fetchPoll = async () => {
      try {
        const pollData = await pollApi.getPoll(pollId);
        setPoll(pollData);
        
        // Find current user ID
        if (userPublicKey) {
          const entry = Object.entries(pollData.registrants).find(
            ([id, key]) => JSON.stringify(key) === JSON.stringify(userPublicKey)
          );
          if (entry) {
            setCurrentUserId(entry[0]);
            
            // Calculate neighbors
            const allUserIds = Object.keys(pollData.registrants).filter(id => id !== entry[0]).sort();
            setNeighbors(calculateNeighbors(entry[0], allUserIds));
          }
        }
      } catch (error) {
        console.error('Failed to fetch poll:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPoll();
  }, [pollId, userPublicKey]);

  // Simple implementation of starting PPE
  const handleStartPPE = (neighborId) => {
    console.log('Starting PPE with neighbor:', neighborId);
    
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      // Update state
      setPpeState({
        step: 'requesting',
        peerId: neighborId,
        myChallengeText: null,
        peerChallengeText: null,
        mySolutionToPeerChallenge: null,
        peerSolutionCommitment: null,
        showCaptchaModal: false
      });
      
      // Send request
      const message = {
        type: 'request_ppe',
        target: neighborId
      };
      
      console.log('Sending PPE request:', message);
      socketRef.current.send(JSON.stringify(message));
      message.info(`Sent PPE request to peer ${neighborId.substring(0, 8)}...`);
    } else {
      console.error('WebSocket not connected');
      message.error('WebSocket not connected. Please try again.');
    }
  };

  if (isLoading) return <p>Loading poll...</p>;
  if (!poll) return <p>Poll not found.</p>;

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Title level={2}>Poll: {poll.title}</Title>
      
      {neighbors.length > 0 && (
        <Card title="Certification with Neighbors">
          <List
            dataSource={neighbors}
            renderItem={neighborId => (
              <List.Item
                actions={[
                  certifiedPeers.has(neighborId) ? (
                    <Text type="success"><CheckCircleOutlined /> Certified</Text>
                  ) : (
                    <Button 
                      type="primary" 
                      onClick={() => handleStartPPE(neighborId)}
                    >
                      Start PPE
                    </Button>
                  )
                ]}
              >
                <List.Item.Meta
                  avatar={<UserOutlined />}
                  title={`Peer: ${neighborId.substring(0, 12)}...`}
                />
              </List.Item>
            )}
          />
        </Card>
      )}
      
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

export default PollVotePageSimple;