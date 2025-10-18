/**
 * Symmetric CAPTCHA PPE component.
 * Both users solve CAPTCHAs.
 */

import React, { useState, useEffect } from 'react';
import { Card, Input, Button, Alert, Typography, Space } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import './ppe-components.css';

const { Title, Text } = Typography;

const SymmetricCaptchaPPE = ({ execution, onSubmit, onComplete }) => {
  const [answer, setAnswer] = useState('');
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    // Calculate time remaining
    const timeout = execution.challenge_data.timeout || 300; // 5 min default
    const startTime = new Date(execution.started_at);
    const endTime = new Date(startTime.getTime() + timeout * 1000);
    
    const updateTimer = () => {
      const now = new Date();
      const remaining = Math.max(0, Math.floor((endTime - now) / 1000));
      setTimeRemaining(remaining);
      
      if (remaining === 0 && !submitted) {
        onComplete(false, 'Timeout');
      }
    };
    
    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    
    return () => clearInterval(interval);
  }, [execution, submitted, onComplete]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitted(true);
    
    const response = {
      answer: answer,
      mac: execution.challenge_data.mac // Include MAC for binding
    };
    
    try {
      const result = await onSubmit(response);
      onComplete(result.success, result.failure_reason);
    } catch (error) {
      onComplete(false, error.message);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Card className="ppe-card">
      <div className="ppe-header">
        <Title level={4}>
          Symmetric CAPTCHA Verification
        </Title>
        {timeRemaining !== null && (
          <Space align="center">
            <ClockCircleOutlined />
            <Text>{formatTime(timeRemaining)}</Text>
          </Space>
        )}
      </div>

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Alert
          message="Type the characters shown below. This is case-insensitive."
          type="info"
          showIcon
        />

        {/* CAPTCHA Display */}
        <div className="captcha-display">
          <div className="captcha-text">
            {execution.challenge_data.text}
          </div>
        </div>

        {/* Answer Input */}
        <form onSubmit={handleSubmit}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text>
              Enter the characters ({execution.challenge_data.length} characters)
            </Text>
            <Input
              size="large"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              disabled={submitted}
              placeholder="Type here..."
              style={{ 
                fontFamily: 'monospace', 
                fontSize: '20px', 
                textAlign: 'center' 
              }}
              autoComplete="off"
              autoFocus
            />

            <Button
              type="primary"
              htmlType="submit"
              disabled={submitted || !answer.trim() || timeRemaining === 0}
              size="large"
              block
              loading={submitted}
            >
              {submitted ? 'Verifying...' : 'Submit Answer'}
            </Button>
          </Space>
        </form>

        <Text type="secondary" style={{ textAlign: 'center', display: 'block' }}>
          Both you and your partner are solving similar challenges to verify each other.
        </Text>
      </Space>
    </Card>
  );
};

export default SymmetricCaptchaPPE;