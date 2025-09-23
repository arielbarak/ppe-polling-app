import React, { useState } from 'react';
import { Modal, Input, Button, Typography, Space } from 'antd';
import './CaptchaModal.css';

const { Title, Text } = Typography;

function CaptchaModal({ peerId, challengeText, onSolve, onClose }) {
  const [userInput, setUserInput] = useState('');

  const handleSubmit = () => {
    // The modal's only job is to get the user's input and pass it up.
    // The parent component will handle validation.
    onSolve(userInput);
  };

  return (
    <Modal
      open={true}
      onCancel={onClose}
      footer={null}
      closable={true}
      maskClosable={false}
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        <Title level={4}>Peer Certification Challenge</Title>
        <Text>Solve the challenge from peer: <strong>{peerId ? peerId.substring(0, 8) + '...' : 'Unknown'}</strong></Text>
        
        <div className="custom-captcha-container">
          <div className="captcha-text">{challengeText}</div>
        </div>

        <Input
          placeholder="Enter the text shown above"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onPressEnter={handleSubmit}
        />

        <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="primary" onClick={handleSubmit}>
            Submit Solution
          </Button>
        </Space>
      </Space>
    </Modal>
  );
}

export default CaptchaModal;