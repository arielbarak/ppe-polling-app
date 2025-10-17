import React, { useState, useEffect } from 'react';
import { Card, Typography, Button, Space, Spin, Alert, List, message } from 'antd';
import { UserOutlined, CheckCircleOutlined, LoadingOutlined, HomeOutlined } from '@ant-design/icons';
import { pollApi } from '../services/pollApi';
import RegistrationCaptcha from './RegistrationCaptcha';
import { registerWithChallenge } from '../services/registrationApi';

const { Title, Text, Paragraph } = Typography;

function PollRegisterPage({ pollId, userPublicKey, navigateToVote, navigateToHome }) {
    const [poll, setPoll] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isRegistering, setIsRegistering] = useState(false);
    const [verifications, setVerifications] = useState(null);
    const [socket, setSocket] = useState(null);
    
    // CAPTCHA state
    const [showCaptcha, setShowCaptcha] = useState(false);
    const [captchaData, setCaptchaData] = useState(null);

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
                    const wsMessage = JSON.parse(event.data);
                    if (wsMessage.type === 'verification_accepted') {
                        await fetchVerifications();
                        await fetchPoll(); // Refresh poll data to get updated verifications
                    } else if (wsMessage.type === 'user_registered') {
                        console.log('WebSocket: user_registered event received in PollRegisterPage, refreshing poll data');
                        await fetchPoll(); // Refresh poll data to show new registered users
                        // Show notification for new user
                        const userId = wsMessage.userId || wsMessage.from;
                        const currentUserId = await pollApi.getUserId(userPublicKey);
                        if (userId && userId !== currentUserId) {
                            message.info(`New user joined: ${userId.substring(0, 8)}...`, 3);
                        }
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
            console.log('Verification status update:', { 
                can_vote: data.can_vote, 
                verified_by_count: data.verified_by.length,
                verified_by: data.verified_by.map(id => id.substring(0, 8) + '...')
            });
            setVerifications(data);
            if (data.can_vote) {
                console.log('User can now vote! Navigating to vote page...');
                message.success('You have been verified and can now vote!');
                setTimeout(() => navigateToVote(pollId), 1000);
            }
            // Also fetch poll data to ensure we have the latest registrations and verifications
            await fetchPoll();
        } catch (error) {
            // Only show error if it's not about being unregistered
            if (!error.message?.includes('User not registered') && !error.message?.includes('not found')) {
                console.error('Failed to fetch verifications:', error);
                // Don't show error message to user for expected "not registered" errors
            }
        }
    };

    const fetchPoll = async () => {
        try {
            // Try to get poll from local storage first
            const cachedPollData = localStorage.getItem(`poll_${pollId}`);
            let pollData;
            
            try {
                // Try to fetch from backend
                pollData = await pollApi.getPoll(pollId);
                // Cache the poll data
                localStorage.setItem(`poll_${pollId}`, JSON.stringify(pollData));
                console.log('Poll data fetched from server and cached in PollRegisterPage');
            } catch (error) {
                // If backend fetch fails and we have cached data, use it
                if (cachedPollData) {
                    console.log('Using cached poll data in PollRegisterPage');
                    pollData = JSON.parse(cachedPollData);
                    message.warning('Using cached poll data. Some information may be outdated.');
                } else {
                    // No cached data and backend failed
                    throw error;
                }
            }
            
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

    // Add polling mechanism to check verification status every 3 seconds (only if registered)
    useEffect(() => {
        // Only start polling if we have poll data and user is registered
        if (!poll || !pollId || !userPublicKey) return;
        
        const currentUserId = pollApi.getUserId(userPublicKey);
        const isRegistered = poll.registrants && currentUserId && poll.registrants[currentUserId];
        
        if (!isRegistered) {
            console.log('User not registered yet, skipping verification polling');
            return;
        }

        // Initial fetch for registered users
        fetchVerifications();

        // Set up polling every 3 seconds to check verification status
        const verificationInterval = setInterval(() => {
            console.log('Polling for verification status updates...');
            fetchVerifications();
        }, 3000);

        // Cleanup interval on unmount
        return () => {
            clearInterval(verificationInterval);
        };
    }, [poll, pollId, userPublicKey]);

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
        // Show CAPTCHA first
        setShowCaptcha(true);
    };

    // NEW function for handling CAPTCHA solution:
    const handleCaptchaSolved = async (challengeData) => {
        try {
            setIsRegistering(true);
            
            // Store challenge data
            setCaptchaData(challengeData);
            
            // Register with challenge solution
            await registerWithChallenge(
                pollId,
                userPublicKey,
                challengeData.challenge_id,
                challengeData.solution
            );
            
            await fetchVerifications();
            await fetchPoll(); // Refresh poll data to show updated registrations
            message.success('Successfully registered for the poll');
            setShowCaptcha(false);
        } catch (error) {
            console.error('Registration failed:', error);
            message.error(`Registration failed: ${error.message}`);
            setShowCaptcha(false);
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
                                    ? "You're verified! Complete PPE challenges with your neighbors to start voting."
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
                ) : showCaptcha ? (
                    <RegistrationCaptcha
                        pollId={pollId}
                        onSolved={handleCaptchaSolved}
                        onCancel={() => setShowCaptcha(false)}
                    />
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
                <Space direction="vertical" style={{ width: '100%' }}>
                    <Alert
                        message="Waiting for Verification"
                        description={`You have ${verifications.verified_by.length} out of 2 required verifications. Other participants need to verify you before you can vote. Stay on this page.`}
                        type="info"
                        showIcon
                    />
                    <Button 
                        onClick={() => {
                            console.log('Manual verification check triggered');
                            fetchVerifications();
                        }}
                        type="default"
                    >
                        Check Status Now
                    </Button>
                </Space>
            )}

            <Button 
                icon={<HomeOutlined />}
                onClick={navigateToHome}
                style={{ alignSelf: 'center' }}
            >
                Back to Home
            </Button>
        </Space>
    );
}

export default PollRegisterPage;
