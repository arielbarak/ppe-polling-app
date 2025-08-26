import React, { useState, useEffect } from 'react';
import { Layout, Space, Button, Input, Typography, Form, Card, List } from 'antd';
import { PlusOutlined, LoginOutlined, ArrowRightOutlined } from '@ant-design/icons';
import { cryptoService } from './services/cryptoService';
import { pollApi } from './services/pollApi';
import CreatePoll from './components/CreatePoll';
import PollRegisterPage from './components/PollRegisterPage';
import PollVotePage from './components/PollVotePage';
import './App.css';

const { Header, Content, Footer } = Layout;
const { Title, Paragraph } = Typography;

const HomePage = ({ navigateToCreate, navigateToPoll }) => {
  const [form] = Form.useForm();
  const [availablePolls, setAvailablePolls] = useState([]);
  const [loading, setLoading] = useState(true);

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

  const handleJoin = (values) => {
    if (values.pollId?.trim()) {
      navigateToPoll(values.pollId.trim());
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
                  onClick={() => {
                    const pollId = form.getFieldValue('pollId');
                    if (pollId?.trim()) {
                      navigateToPoll(pollId.trim());
                    }
                  }}
                >
                  Join Poll
                </Button>
              }
              size="large"
              onSearch={(value) => {
                if (value?.trim()) {
                  navigateToPoll(value.trim());
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
          renderItem={poll => (
            <List.Item
              key={poll.id}
              actions={[
                <Button 
                  type="link" 
                  icon={<ArrowRightOutlined />}
                  onClick={() => navigateToPoll(poll.id)}
                >
                  Join
                </Button>
              ]}
            >
              <List.Item.Meta
                title={poll.question}
                description={`${Object.keys(poll.registrants || {}).length} participants`}
              />
            </List.Item>
          )}
          bordered
          style={{ width: '100%' }}
        />
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
