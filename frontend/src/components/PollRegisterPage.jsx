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
        // Use the stable user ID (hash of public key) as the WebSocket client id.
        // Passing the raw publicKey object into the URL becomes "[object Object]" and causes collisions.
        const setupSocket = async () => {
            try {
                const userId = await pollApi.getUserId(userPublicKey);
                const wsUrl = `ws://localhost:8000/ws/${pollId}/${encodeURIComponent(userId)}`;
                const ws = new WebSocket(wsUrl);
                setSocket(ws);

                ws.onmessage = async (event) => {
                    const message = JSON.parse(event.data);
                    if (message.type === 'verification_accepted') {
                        await fetchVerifications();
                        await fetchPoll(); // Refresh poll data to get updated verifications
                    }
                };
            } catch (err) {
                console.error('Failed to establish WebSocket connection:', err);
            }
        };

        setupSocket();

        return () => { if (socket) socket.close(); };
    }, [pollId, userPublicKey]);

    const fetchVerifications = async () => {
        try {
            const data = await pollApi.getUserVerifications(pollId, userPublicKey);
            setVerifications(data);
            if (data.can_vote) {
                message.success('You have been verified and can now vote!');
                setTimeout(() => navigateToVote(pollId), 1000);
            }
            // Also fetch poll data to ensure we have the latest registrations and verifications
            await fetchPoll();
        } catch (error) {
            // If the error is because we're not registered yet, don't show an error
            if (!error.message?.includes('User not registered')) {
                message.error('Failed to fetch verifications');
                console.error('Failed to fetch verifications:', error);
            }
        }
    };

    const fetchPoll = async () => {
        try {
            const pollData = await pollApi.getPoll(pollId);
            setPoll(pollData);
        } catch (error) {
            console.error('Failed to fetch poll:', error);
            message.error('Failed to fetch poll data');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchPoll();
    }, [pollId]);

    const handleVerifyUser = async (userId) => {
        try {
            await pollApi.verifyUser(pollId, userId, userPublicKey);
            if (socket) {
                socket.send(JSON.stringify({
                    type: 'verification_accepted',
                    target: userId
                }));
            }
            await fetchPoll(); // Refresh the poll data to show updated verifications
            message.success('User verified successfully');
        } catch (error) {
            console.error('Failed to verify user:', error);
            message.error('Failed to verify user');
        }
    };

    const handleRegister = async () => {
        setIsRegistering(true);
        try {
            await pollApi.register(pollId, userPublicKey);
            await fetchVerifications();
            await fetchPoll(); // Refresh poll data to show updated registrations
            message.success('Successfully registered for the poll');
        } catch (error) {
            console.error('Registration failed:', error);
            message.error('Failed to register for the poll');
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

            {verifications && (
                <Card title={<Title level={3}>Other Registered Users</Title>}>
                    <List
                        dataSource={Object.entries(poll.registrants)
                            .filter(([_, key]) => JSON.stringify(key) !== JSON.stringify(userPublicKey)) // Don't show self using public key comparison
                            .map(([id]) => ({
                                id,
                                hasVerified: verifications?.has_verified?.includes(id),
                                verificationCount: poll.verifications[id]?.verified_by.length || 0,
                                canVote: poll.verifications[id]?.verified_by.length >= 2
                            }))}
                        renderItem={(user) => (
                            <List.Item
                                actions={[
                                    user.hasVerified ? (
                                        <Text type="success">
                                            <CheckCircleOutlined /> Verified
                                        </Text>
                                    ) : (
                                        <Button
                                            type="primary"
                                            onClick={() => handleVerifyUser(user.id)}
                                            icon={<CheckCircleOutlined />}
                                        >
                                            Verify User
                                        </Button>
                                    )
                                ]}
                            >
                                <List.Item.Meta
                                    avatar={<UserOutlined />}
                                    title={`User: ${user.id.substring(0, 8)}...`}
                                    description={
                                        <>
                                            {user.hasVerified ? (
                                                "You've verified this user"
                                            ) : (
                                                "Needs your verification"
                                            )}
                                            <br />
                                            <Text type={user.canVote ? "success" : "warning"}>
                                                {user.verificationCount} verification{user.verificationCount !== 1 ? 's' : ''} 
                                                {user.canVote ? " (Can vote)" : ` (Needs ${2 - user.verificationCount} more)`}
                                            </Text>
                                        </>
                                    }
                                />
                            </List.Item>
                        )}
                    />
                </Card>
            )}

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
