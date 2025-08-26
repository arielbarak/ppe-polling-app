import React, { useState, useEffect } from 'react';
import { Card, Typography, Button, Space, Spin, Alert, List, message } from 'antd';
import { UserOutlined, CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import { pollApi } from '../services/pollApi';

const { Title, Text, Paragraph } = Typography;

function PollRegisterPage({ pollId, userPublicKey, navigateToVote }) {
    const [poll, setPoll] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isRegistering, setIsRegistering] = useState(false);
    const [verifications, setVerifications] = useState(null);
    const [socket, setSocket] = useState(null);

    useEffect(() => {
        const ws = new WebSocket(`ws://localhost:8000/ws/${pollId}/${userPublicKey}`);
        setSocket(ws);

        ws.onmessage = async (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'verification_accepted') {
                await fetchVerifications();
            }
        };

        return () => ws.close();
    }, [pollId, userPublicKey]);

    const fetchVerifications = async () => {
        try {
            const data = await pollApi.getUserVerifications(pollId, userPublicKey);
            setVerifications(data);
            if (data.can_vote) {
                message.success('You have been verified and can now vote!');
                setTimeout(() => navigateToVote(pollId), 1000);
            }
        } catch (error) {
            message.error('Failed to fetch verifications');
            console.error('Failed to fetch verifications:', error);
        }
    };

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
        try {
            await pollApi.register(pollId, userPublicKey);
            await fetchVerifications();
        } catch (error) {
            console.error('Registration failed:', error);
        } finally {
            setIsRegistering(false);
        }
    };

    if (isLoading) return <Spin size="large" />;
    if (!poll) return <Alert message="Poll not found" type="error" />;

    return (
        <Space direction="vertical" size="large" style={{ width: '100%', maxWidth: 800 }}>
            <Card>
                <Title level={2}>{poll.question}</Title>
            </Card>

            <Card title={<Title level={3}>Registration Status</Title>}>
                {verifications ? (
                    <>
                        <Alert
                            message={
                                verifications.can_vote
                                    ? "You're verified and ready to vote!"
                                    : `You need ${2 - verifications.verification_count} more verifications to vote`
                            }
                            type={verifications.can_vote ? "success" : "info"}
                            showIcon
                        />
                        <List
                            style={{ marginTop: '20px' }}
                            header={<Text strong>Verified by:</Text>}
                            dataSource={verifications.verified_by}
                            renderItem={verifier => (
                                <List.Item>
                                    <UserOutlined /> Verified User
                                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                                </List.Item>
                            )}
                        />
                    </>
                ) : (
                    <Button
                        type="primary"
                        onClick={handleRegister}
                        loading={isRegistering}
                    >
                        Register for Poll
                    </Button>
                )}
            </Card>

            {verifications && !verifications.can_vote && (
                <Alert
                    message="Waiting for Verification"
                    description="Other participants need to verify you before you can vote. Stay on this page."
                    type="info"
                    showIcon
                />
            )}
        </Space>
    );
}

export default PollRegisterPage;
