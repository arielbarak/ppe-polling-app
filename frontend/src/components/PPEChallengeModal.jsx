/**
 * Modal for conducting PPE challenge with a peer.
 * 
 * Displays peer's challenge and handles the complete PPE protocol flow.
 */

import React, { useState, useEffect } from 'react';
import { Modal, Input, Button, Alert, Space, Typography, Steps, Spin } from 'antd';
import { CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import './PPEChallengeModal.css';

const { Title, Text } = Typography;
const { Step } = Steps;

function PPEChallengeModal({ 
  peerUserId, 
  peerChallenge,
  onSolutionSubmit,
  onClose,
  currentStep = 0,
  status = 'active'
}) {
  const [solution, setSolution] = useState('');
  const [error, setError] = useState(null);

  const steps = [
    { title: 'Challenge', description: 'Solve peer challenge' },
    { title: 'Commitment', description: 'Exchange commitments' },
    { title: 'Verification', description: 'Verify challenges' },
    { title: 'Complete', description: 'Exchange signatures' }
  ];

  const handleSubmit = () => {
    if (!solution.trim()) {
      setError('Please enter your solution');
      return;
    }
    
    setError(null);
    onSolutionSubmit(solution.trim());
  };

  const getStatusIcon = () => {
    if (status === 'error') {
      return 'X';
    } else if (status === 'success') {
      return 'OK';
    } else if (status === 'waiting') {
      return <Spin size="small" />;
    }
    return null;
  };

  return (
    <Modal
      open={true}
      onCancel={onClose}
      footer={null}
      width={600}
      maskClosable={false}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Title level={4}>
            <CheckCircleOutlined style={{ color: '#1890ff', marginRight: '8px' }} />
            PPE Challenge with Peer
          </Title>
          <Text type="secondary">
            User: {peerUserId.substring(0, 10)}...
          </Text>
        </div>

        <Steps current={currentStep} size="small">
          {steps.map((step, idx) => (
            <Step key={idx} title={step.title} description={step.description} />
          ))}
        </Steps>

        {error && (
          <Alert
            message="Error"
            description={error}
            type="error"
            closable
            onClose={() => setError(null)}
          />
        )}

        {currentStep === 0 && peerChallenge && (
          <>
            <div className="ppe-challenge-container">
              <div className="ppe-challenge-text">
                {peerChallenge}
              </div>
            </div>

            <Text type="secondary" style={{ fontSize: '12px' }}>
              Type the characters shown above (ignore spaces, not case-sensitive)
            </Text>

            <Input
              size="large"
              placeholder="Enter your solution"
              value={solution}
              onChange={(e) => setSolution(e.target.value)}
              onPressEnter={handleSubmit}
              disabled={currentStep !== 0}
            />

            <Button 
              type="primary" 
              size="large"
              onClick={handleSubmit}
              disabled={!solution.trim()}
              style={{ width: '100%' }}
            >
              Submit Solution
            </Button>
          </>
        )}

        {currentStep > 0 && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            {status === 'waiting' && (
              <>
                <Spin size="large" />
                <p style={{ marginTop: '16px' }}>
                  {currentStep === 1 && 'Exchanging commitments...'}
                  {currentStep === 2 && 'Verifying challenges...'}
                  {currentStep === 3 && 'Exchanging signatures...'}
                </p>
              </>
            )}
            {status === 'success' && (
              <>
                <CheckCircleOutlined style={{ fontSize: '48px', color: '#52c41a' }} />
                <p style={{ marginTop: '16px', fontSize: '16px' }}>
                  PPE Completed Successfully!
                </p>
              </>
            )}
            {status === 'error' && (
              <>
                <Text type="danger" style={{ fontSize: '16px' }}>
                  PPE Failed: {error || 'Unknown error'}
                </Text>
              </>
            )}
          </div>
        )}

        <Alert
          message="Secure Protocol"
          description="This is the symmetric CAPTCHA PPE protocol. Both you and your peer solve each other's challenges using a cryptographic commitment scheme."
          type="info"
          showIcon
        />
      </Space>
    </Modal>
  );
}

export default PPEChallengeModal;