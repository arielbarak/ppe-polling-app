import React, { useState, useEffect } from 'react';
import { Layout, Space, Button, Input, Typography, Form, Card, List, message, Tooltip } from 'antd';
import { PlusOutlined, LoginOutlined, ArrowRightOutlined, CheckCircleOutlined, UserAddOutlined, SafetyOutlined } from '@ant-design/icons';
import { cryptoService } from './services/cryptoService';
import { pollApi } from './services/pollApi';
import CreatePoll from './components/CreatePoll';
import PollRegisterPage from './components/PollRegisterPage';
import PollVotePage from './components/PollVotePage';
import PollVerifyPage from './components/PollVerifyPage';
import './App.css';

const { Header, Content, Footer } = Layout;
const { Title, Paragraph } = Typography;

const HomePage = ({ navigateToCreate, navigateToPoll, navigateToVerify, userPublicKey }) => {
  const [form] = Form.useForm();
  const [availablePolls, setAvailablePolls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checkingPoll, setCheckingPoll] = useState(null);
  const [verifyPollId, setVerifyPollId] = useState('');

  useEffect(() => {
    const fetchPolls = async () => {
      try {
        const polls = await pollApi.getAllPolls();
        setAvailablePolls(polls);
      } catch (error) {
        console.error('Failed to fetch polls:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchPolls();
  }, []);

  const handleJoin = async (values) => {
    if (values.pollId?.trim()) {
      setCheckingPoll(values.pollId.trim());
      await navigateToPoll(values.pollId.trim());
      setCheckingPoll(null);
    }
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%', maxWidth: 600, margin: '0 auto' }}>
      <Card>
        <Title level={2}>Create a Poll</Title>
        <Paragraph>Create a new secure, publicly verifiable poll.</Paragraph>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={navigateToCreate}
          size="large"
        >
          Create New Poll
        </Button>
      </Card>

      <Card>
        <Title level={2}>Join a Poll</Title>
        <Paragraph>Have a poll ID? Enter it here to join.</Paragraph>
        <Form form={form} onFinish={handleJoin}>
          <Form.Item
            name="pollId"
            rules={[{ required: true, message: 'Please enter a Poll ID' }]}
          >
            <Input.Search
              placeholder="Enter Poll ID"
              enterButton={
                <Button 
                  type="primary" 
                  icon={<LoginOutlined />}
                  onClick={async () => {
                    const pollId = form.getFieldValue('pollId');
                    if (pollId?.trim()) {
                      setCheckingPoll(pollId.trim());
                      await navigateToPoll(pollId.trim());
                      setCheckingPoll(null);
                    }
                  }}
                  loading={checkingPoll === form.getFieldValue('pollId')}
                >
                  Join Poll
                </Button>
              }
              size="large"
              onSearch={async (value) => {
                if (value?.trim()) {
                  setCheckingPoll(value.trim());
                  await navigateToPoll(value.trim());
                  setCheckingPoll(null);
                }
              }}
            />
          </Form.Item>
        </Form>
      </Card>

      <Card>
        <Title level={2}>Available Polls</Title>
        <List
          loading={loading}
          dataSource={availablePolls}
          renderItem={poll => {
            // Check if user is already registered in this poll
            const isRegistered = userPublicKey && Object.values(poll.registrants || {}).some(
              registeredKey => JSON.stringify(registeredKey) === JSON.stringify(userPublicKey)
            );
            
            return (
              <List.Item
                key={poll.id}
                actions={[
                  <Tooltip title={isRegistered ? "Go to voting page" : "Register for this poll"}>
                    <Button 
                      type={isRegistered ? "default" : "link"}
                      icon={isRegistered ? <CheckCircleOutlined /> : <UserAddOutlined />}
                      onClick={async () => {
                        setCheckingPoll(poll.id);
                        await navigateToPoll(poll.id);
                        setCheckingPoll(null);
                      }}
                      loading={checkingPoll === poll.id}
                    >
                      {isRegistered ? 'Continue' : 'Join'}
                    </Button>
                  </Tooltip>,
                  <Tooltip title="Verify poll integrity">
                    <Button
                      type="link"
                      icon={<SafetyOutlined />}
                      onClick={() => navigateToVerify(poll.id)}
                    >
                      Verify
                    </Button>
                  </Tooltip>
                ]}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      {poll.question}
                      {isRegistered && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size="small">
                      <span>{`${Object.keys(poll.registrants || {}).length} participants`}</span>
                      {isRegistered && <span style={{ color: '#52c41a', fontSize: '12px' }}>✓ You are registered</span>}
                    </Space>
                  }
                />
              </List.Item>
            );
          }}
          bordered
          style={{ width: '100%' }}
        />
      </Card>
      
      <Card>
        <Title level={2}>Verify a Poll</Title>
        <Paragraph>Publicly verify the integrity of any poll without needing to register.</Paragraph>
        <Form onFinish={() => navigateToVerify(verifyPollId)}>
          <Space direction="horizontal">
            <Input 
              placeholder="Enter Poll ID to verify" 
              value={verifyPollId} 
              onChange={e => setVerifyPollId(e.target.value)}
              style={{ width: 300 }}
            />
            <Button 
              type="primary" 
              icon={<SafetyOutlined />} 
              onClick={() => navigateToVerify(verifyPollId)}
            >
              Verify Poll
            </Button>
          </Space>
        </Form>
      </Card>
    </Space>
  );
};

function App() {
  const [publicKey, setPublicKey] = useState(null);
  const [view, setView] = useState({ page: 'home', pollId: null });

  // --- Navigation Functions ---
  const navigateToHome = () => setView({ page: 'home', pollId: null });
  const navigateToCreate = () => setView({ page: 'create', pollId: null });
  const navigateToVerify = (pollId) => setView({ page: 'verify', pollId: pollId });
  const navigateToPoll = async (pollId) => {
    if (!publicKey) {
      console.warn('Public key not ready yet');
      return;
    }
    
    try {
      // Check if user is already registered in this poll
      console.log('Checking registration status for poll:', pollId);
      const poll = await pollApi.getPoll(pollId);
      
      // Find if user's public key is already registered
      const isRegistered = Object.values(poll.registrants || {}).some(
        registeredKey => JSON.stringify(registeredKey) === JSON.stringify(publicKey)
      );
      
      if (isRegistered) {
        console.log('User already registered, navigating to vote page');
        message.success('Welcome back! Taking you to the voting page...');
        setView({ page: 'vote', pollId: pollId });
      } else {
        console.log('User not registered, navigating to register page');
        message.info('Taking you to the registration page...');
        setView({ page: 'register', pollId: pollId });
      }
    } catch (error) {
      console.error('Failed to check poll registration status:', error);
      message.error('Could not verify registration status. Taking you to registration page.');
      // If there's an error fetching the poll, default to registration page
      setView({ page: 'register', pollId: pollId });
    }
  };
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
        return <CreatePoll navigateToPoll={navigateToPoll} navigateToHome={navigateToHome} />;
      case 'register':
        return <PollRegisterPage pollId={view.pollId} userPublicKey={publicKey} navigateToVote={navigateToVote} navigateToHome={navigateToHome} />;
      case 'vote':
        return <PollVotePage pollId={view.pollId} userPublicKey={publicKey} navigateToHome={navigateToHome} />;
      case 'verify':
        return <PollVerifyPage pollId={view.pollId} navigateToHome={navigateToHome} />;
      case 'home':
      default:
        return <HomePage navigateToCreate={navigateToCreate} navigateToPoll={navigateToPoll} navigateToVerify={navigateToVerify} userPublicKey={publicKey} />;
    }
  };

  return (
    <Layout className="App">
      <Header style={{ 
        background: '#fff', 
        padding: '0 24px',
        position: 'sticky',
        top: 0,
        zIndex: 1,
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <Title justify="center" level={3} style={{ margin: '16px 0' }}>PPE Polling System</Title>
      </Header>
      <Content style={{ 
        padding: '24px 50px',
        minHeight: 'calc(100vh - 134px)'
      }}>
        <div className="site-layout-content">
          {renderView()}
        </div>
      </Content>
      <Footer style={{ textAlign: 'center' }}>
        {publicKey && (
          <Paragraph type="secondary">
            <Space>
              Identity Loaded
            </Space>
          </Paragraph>
        )}
      </Footer>
    </Layout>
  );
}

export default App;
