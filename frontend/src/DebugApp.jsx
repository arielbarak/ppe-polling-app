import React, { useState, useEffect } from 'react';
import { Layout, Space, Button, Typography, Card } from 'antd';
import { cryptoService } from './services/cryptoService';
import { pollApi } from './api/pollApi';
import PollVotePageSimple from './components/PollVotePageSimple';

const { Header, Content, Footer } = Layout;
const { Title, Paragraph } = Typography;

function DebugApp() {
  const [view, setView] = useState('home');
  const [userPublicKey, setUserPublicKey] = useState(null);
  const [pollId, setPollId] = useState(null);
  
  // Load keys on startup
  useEffect(() => {
    const loadKeys = async () => {
      try {
        const keyPair = await cryptoService.loadKeys();
        if (keyPair) {
          console.log('Keys loaded successfully');
          setUserPublicKey(keyPair.publicKey);
        } else {
          // Generate new keys if none exist
          const newKeyPair = await cryptoService.generateAndStoreKeys();
          setUserPublicKey(newKeyPair.publicKey);
          console.log('New keys generated');
        }
      } catch (error) {
        console.error('Failed to load/generate keys:', error);
      }
    };
    
    loadKeys();
  }, []);
  
  // Load latest poll
  useEffect(() => {
    const getLatestPoll = async () => {
      try {
        const polls = await pollApi.getAllPolls();
        if (polls.length > 0) {
          // Get the latest poll
          const latestPoll = polls[polls.length - 1];
          setPollId(latestPoll.id);
          console.log('Latest poll ID:', latestPoll.id);
        }
      } catch (error) {
        console.error('Failed to load polls:', error);
      }
    };
    
    getLatestPoll();
  }, []);
  
  const navigateToHome = () => {
    setView('home');
  };
  
  const navigateToPoll = () => {
    setView('poll');
  };
  
  const renderContent = () => {
    if (view === 'home') {
      return (
        <Card>
          <Title level={2}>PPE Debugging Tool</Title>
          <Paragraph>
            This simplified version lets us test the PPE functionality directly.
          </Paragraph>
          
          {pollId && (
            <Button type="primary" onClick={navigateToPoll}>
              Go to Latest Poll
            </Button>
          )}
        </Card>
      );
    }
    
    if (view === 'poll' && pollId) {
      return (
        <PollVotePageSimple
          pollId={pollId}
          userPublicKey={userPublicKey}
          navigateToHome={navigateToHome}
        />
      );
    }
    
    return <p>Loading...</p>;
  };
  
  return (
    <Layout className="layout">
      <Header style={{ display: 'flex', alignItems: 'center' }}>
        <div className="logo" />
        <Title level={3} style={{ color: 'white', margin: 0 }}>
          PPE Debug Mode
        </Title>
      </Header>
      
      <Content style={{ padding: '0 50px', marginTop: 40 }}>
        <div className="site-layout-content">
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {renderContent()}
          </Space>
        </div>
      </Content>
      
      <Footer style={{ textAlign: 'center' }}>
        PPE Debugging Tool
      </Footer>
    </Layout>
  );
}

export default DebugApp;