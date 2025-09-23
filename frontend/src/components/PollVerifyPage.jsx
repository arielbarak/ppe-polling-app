import React, { useState, useEffect, useRef } from 'react';
import { Card, Typography, Button, Space, Spin, Alert, Divider, Statistic, Row, Col, Input, message } from 'antd';
import { HomeOutlined, SearchOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons';
import ForceGraph2D from 'react-force-graph-2d';
import { pollApi } from '../api/pollApi';

const { Title, Text, Paragraph } = Typography;

function PollVerifyPage({ pollId, navigateToHome }) {
  const [poll, setPoll] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [verificationStatus, setVerificationStatus] = useState(null);
  const [inputPollId, setInputPollId] = useState(pollId || '');
  const graphRef = useRef();

  const fetchVerificationData = async (id) => {
    try {
      setIsLoading(true);
      const data = await pollApi.getVerificationData(id);
      
      setPoll(data);
      
      // Transform the data for the graph visualization
      const graphNodes = data.certification_graph.nodes.map(node => ({
        id: node.id,
        name: node.id.substring(0, 8) + '...',
        voted: node.voted,
        vote: node.vote,
        color: node.voted ? '#52c41a' : '#1890ff'
      }));
      
      const graphLinks = data.certification_graph.edges.map(edge => ({
        source: edge.source,
        target: edge.target,
        type: edge.type,
        color: edge.type === 'ppe_certification' ? '#faad14' : '#1890ff'
      }));
      
      setGraphData({
        nodes: graphNodes,
        links: graphLinks
      });
      
      setVerificationStatus(data.verification);
    } catch (error) {
      console.error('Failed to fetch verification data:', error);
      message.error('Failed to load poll verification data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (pollId) {
      fetchVerificationData(pollId);
    }
  }, [pollId]);

  const handleVerify = () => {
    if (inputPollId.trim()) {
      fetchVerificationData(inputPollId.trim());
    } else {
      message.warning('Please enter a Poll ID');
    }
  };

  const renderVerificationStatus = () => {
    if (!verificationStatus) return null;

    const { is_valid, verification_message, total_participants, total_votes, 
            ppe_coverage, min_certifications_per_user, avg_certifications_per_user } = verificationStatus;

    return (
      <Card 
        title={
          <Space>
            {is_valid ? 
              <CheckCircleOutlined style={{ color: '#52c41a' }} /> : 
              <WarningOutlined style={{ color: '#faad14' }} />
            }
            <span>Verification Status</span>
          </Space>
        }
        style={{ marginBottom: 16, borderColor: is_valid ? '#52c41a' : '#faad14' }}
      >
        <Alert
          message={verification_message}
          type={is_valid ? 'success' : 'warning'}
          showIcon
          style={{ marginBottom: 16 }}
        />
        
        <Row gutter={16}>
          <Col span={8}>
            <Statistic 
              title="Participants" 
              value={total_participants} 
            />
          </Col>
          <Col span={8}>
            <Statistic 
              title="Votes Cast" 
              value={total_votes} 
            />
          </Col>
          <Col span={8}>
            <Statistic 
              title="PPE Coverage" 
              value={Math.round(ppe_coverage * 100)} 
              suffix="%" 
              valueStyle={{ color: ppe_coverage > 0.3 ? '#52c41a' : '#faad14' }}
            />
          </Col>
        </Row>
        
        <Divider />
        
        <Row gutter={16}>
          <Col span={12}>
            <Statistic 
              title="Min Certifications/User" 
              value={min_certifications_per_user} 
              valueStyle={{ color: min_certifications_per_user >= 2 ? '#52c41a' : '#faad14' }}
            />
          </Col>
          <Col span={12}>
            <Statistic 
              title="Avg Certifications/User" 
              value={avg_certifications_per_user.toFixed(2)} 
            />
          </Col>
        </Row>
      </Card>
    );
  };

  const renderPollResults = () => {
    if (!poll) return null;

    // Count votes per option
    const voteCount = {};
    poll.options.forEach(option => { voteCount[option] = 0; });
    
    poll.certification_graph.nodes.forEach(node => {
      if (node.voted && node.vote) {
        voteCount[node.vote] = (voteCount[node.vote] || 0) + 1;
      }
    });

    return (
      <Card title="Poll Results" style={{ marginBottom: 16 }}>
        <Title level={3}>{poll.question}</Title>
        
        <Row gutter={16}>
          {poll.options.map(option => (
            <Col span={8} key={option}>
              <Statistic 
                title={option} 
                value={voteCount[option] || 0} 
                suffix={`/ ${poll.total_votes}`} 
              />
            </Col>
          ))}
        </Row>
      </Card>
    );
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Title level={2}>Public Poll Verification</Title>
        <Paragraph>
          Verify the integrity of a poll using the PPE (Public Verification of Private Effort) protocol.
          This tool allows anyone to independently verify that a poll's results are legitimate without trusting the pollster.
        </Paragraph>
        
        <Space direction="horizontal">
          <Input 
            placeholder="Enter Poll ID to verify" 
            value={inputPollId} 
            onChange={e => setInputPollId(e.target.value)}
            style={{ width: 300 }}
            onPressEnter={handleVerify}
          />
          <Button 
            type="primary" 
            icon={<SearchOutlined />} 
            onClick={handleVerify}
            loading={isLoading}
          >
            Verify Poll
          </Button>
        </Space>
      </Card>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>Loading verification data...</div>
        </div>
      ) : poll ? (
        <>
          {renderVerificationStatus()}
          {renderPollResults()}
          
          <Card title="Certification Graph" style={{ marginBottom: 16 }}>
            <Paragraph>
              This graph shows the certification relationships between participants:
              <ul>
                <li><Text strong>Nodes:</Text> Participants (blue = registered, green = voted)</li>
                <li><Text strong>Yellow lines:</Text> PPE certifications between peers</li>
                <li><Text strong>Blue lines:</Text> User verifications</li>
              </ul>
            </Paragraph>
            
            <div style={{ height: '500px', border: '1px solid #eee', borderRadius: '2px' }}>
              <ForceGraph2D
                ref={graphRef}
                graphData={graphData}
                nodeLabel="name"
                nodeColor="color"
                linkColor="color"
                width={800}
                height={500}
                linkDirectionalArrowLength={3}
                linkDirectionalArrowRelPos={1}
                cooldownTicks={100}
                onEngineStop={() => graphRef.current?.zoomToFit(400)}
              />
            </div>
          </Card>
        </>
      ) : (
        <Alert
          message="No Verification Data"
          description="Enter a Poll ID above to verify a poll."
          type="info"
          showIcon
        />
      )}

      <div style={{ display: 'flex', justifyContent: 'center', marginTop: '16px' }}>
        <Button 
          icon={<HomeOutlined />}
          onClick={navigateToHome}
          size="large"
        >
          Back to Home
        </Button>
      </div>
    </Space>
  );
}

export default PollVerifyPage;