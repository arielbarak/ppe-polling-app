import React, { useState, useEffect } from 'react';
import { Card, Typography, Button, Space, Spin, Alert, List, Progress, message } from 'antd';
import { CopyOutlined, UserAddOutlined } from '@ant-design/icons';
import { pollApi } from '../api/pollApi';

const { Title, Text, Paragraph } = Typography;

function PollRegisterPage({ pollId, userPublicKey, navigateToVote }) {
  const [poll, setPoll] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRegistering, setIsRegistering] = useState(false);
  const [registrationMessage, setRegistrationMessage] = useState('');

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
      message.success('Registration successful! Redirecting...');
      setTimeout(() => navigateToVote(pollId), 1000);
    } catch (err) {
      message.error(err.message);
    } finally {
      setIsRegistering(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(pollId)
      .then(() => message.success('Poll ID copied to clipboard!'))
      .catch(() => message.error('Failed to copy Poll ID'));
  };

  if (isLoading) return <Spin size="large" />;
  if (!poll) return <Alert message="Poll not found" type="error" />;

  return (
    <Space direction="vertical" size="large" style={{ width: '100%', maxWidth: 800 }}>
      <Card>
        <Title level={2} style={{ textAlign: 'center' }}>{poll.question}</Title>
      </Card>

      <Card title={<Title level={3}>Share this Poll</Title>}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Paragraph>Use this ID to let others join the poll:</Paragraph>
          <Space>
            <Text code copyable>{pollId}</Text>
            <Button 
              icon={<CopyOutlined />} 
              onClick={copyToClipboard}
              type="primary"
            >
              Copy ID
            </Button>
          </Space>
        </Space>
      </Card>

      <Card title={<Title level={3}>Registration</Title>}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Paragraph>You must register to participate in this poll.</Paragraph>
          <Button
            type="primary"
            icon={<UserAddOutlined />}
            loading={isRegistering}
            onClick={handleRegister}
            size="large"
          >
            {isRegistering ? 'Registering...' : 'Register Now'}
          </Button>
          {registrationMessage && (
            <Alert
              message={registrationMessage}
              type={registrationMessage.startsWith('Error') ? 'error' : 'success'}
            />
          )}
        </Space>
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
    </Space>
  );
}

export default PollRegisterPage;
