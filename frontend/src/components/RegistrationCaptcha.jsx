/**
 * Component for displaying and solving registration CAPTCHA.
 * 
 * FIXES Issue #3: Updated terminology.
 * FIXES Issue #4: Clearly labeled as one-sided PPE (server-verified).
 */

import React, { useState, useEffect } from 'react';
import { Card, Input, Button, Alert, Space, Typography, Spin } from 'antd';
import { ReloadOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { requestChallenge } from '../services/registrationApi';
import './RegistrationCaptcha.css';

const { Title, Text } = Typography;

function RegistrationCaptcha({ pollId, onSolved, onCancel }) {
  const [challenge, setChallenge] = useState(null);
  const [solution, setSolution] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadChallenge = async () => {
    try {
      setLoading(true);
      setError(null);
      setSolution('');
      
      const challengeData = await requestChallenge(pollId, 'medium');
      setChallenge(challengeData);
      setLoading(false);
    } catch (err) {
      console.error('Error loading challenge:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadChallenge();
  }, [pollId]);

  const handleSubmit = () => {
    if (!solution.trim()) {
      setError('Please enter your solution');
      return;
    }

    // Pass the solution back to parent component
    onSolved({
      challenge_id: challenge.challenge_id,
      solution: solution.trim(),
    });
  };

  const handleRefresh = () => {
    loadChallenge();
  };

  if (loading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
          <p style={{ marginTop: '16px' }}>Loading challenge...</p>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Title level={4}>
            <CheckCircleOutlined style={{ color: '#1890ff', marginRight: '8px' }} />
            Registration Challenge
          </Title>
          <Text type="secondary">
            Complete this anti-bot verification to join the poll. This is a one-time server-verified challenge (one-sided PPE).
          </Text>
        </div>

        {error && (
          <Alert
            message="Error"
            description={error}
            type="error"
            closable
            onClose={() => setError(null)}
          />
        )}

        {challenge && (
          <div>
            <div className="registration-captcha-container">
              <div className="registration-captcha-text">
                {challenge.challenge_text}
              </div>
            </div>

            <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginTop: '8px' }}>
              Type the text shown above (not case-sensitive)
            </Text>
          </div>
        )}

        <Input
          size="large"
          placeholder="Enter the text you see"
          value={solution}
          onChange={(e) => setSolution(e.target.value)}
          onPressEnter={handleSubmit}
          disabled={!challenge}
        />

        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            {onCancel && (
              <Button onClick={onCancel}>
                Cancel
              </Button>
            )}
            <Button 
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              disabled={loading}
            >
              New Challenge
            </Button>
          </Space>
          
          <Button 
            type="primary" 
            size="large"
            onClick={handleSubmit}
            disabled={!challenge || !solution.trim()}
          >
            Verify & Continue
          </Button>
        </Space>

        <Alert
          message="Anti-Bot Verification"
          description="This is a one-sided Proof of Private Effort (PPE) verified by the server to prevent fake registrations. Later, you'll complete peer-to-peer verifications (two-sided PPE) with other participants."
          type="info"
          showIcon
        />
      </Space>
    </Card>
  );
}

export default RegistrationCaptcha;