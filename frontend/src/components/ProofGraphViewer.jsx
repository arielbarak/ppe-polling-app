/**
 * Component for viewing and verifying the proof graph.
 * 
 * Displays the complete proof structure with verification status.
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Spin, Alert, Descriptions, Space, Statistic, Row, Col, Typography, Divider } from 'antd';
import { DownloadOutlined, CheckCircleOutlined, WarningOutlined, ReloadOutlined } from '@ant-design/icons';
import { getProofGraph, getProofSummary, exportProofGraph, verifyProofHash } from '../services/proofGraphApi';

const { Title, Text, Paragraph } = Typography;

function ProofGraphViewer({ pollId }) {
  const [proofGraph, setProofGraph] = useState(null);
  const [summary, setSummary] = useState(null);
  const [hashVerification, setHashVerification] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadProofData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load summary and hash verification in parallel
      const [summaryData, hashData] = await Promise.all([
        getProofSummary(pollId),
        verifyProofHash(pollId)
      ]);

      setSummary(summaryData);
      setHashVerification(hashData);
      setLoading(false);
    } catch (err) {
      console.error('Error loading proof data:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const loadFullGraph = async () => {
    try {
      setLoading(true);
      const graphData = await getProofGraph(pollId);
      setProofGraph(graphData);
      setLoading(false);
    } catch (err) {
      console.error('Error loading proof graph:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      await exportProofGraph(pollId);
    } catch (err) {
      console.error('Error exporting proof graph:', err);
      setError('Failed to export proof graph');
    }
  };

  useEffect(() => {
    loadProofData();
  }, [pollId]);

  if (loading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
          <p style={{ marginTop: '16px' }}>Loading proof graph...</p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <Alert
          message="Error Loading Proof Graph"
          description={error}
          type="error"
          showIcon
        />
        <Button 
          onClick={loadProofData} 
          icon={<ReloadOutlined />}
          style={{ marginTop: '16px' }}
        >
          Retry
        </Button>
      </Card>
    );
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      {/* Header */}
      <Card>
        <Title level={3}>
          {hashVerification?.is_valid ? (
            <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
          ) : (
            <WarningOutlined style={{ color: '#faad14', marginRight: '8px' }} />
          )}
          Proof Graph
        </Title>
        <Paragraph type="secondary">
          This is the complete cryptographic proof of the poll's integrity. 
          Anyone can independently verify this proof without trusting the pollster.
        </Paragraph>
      </Card>

      {/* Summary Statistics */}
      {summary && (
        <Card title="Summary">
          <Row gutter={16}>
            <Col span={6}>
              <Statistic 
                title="Total Participants" 
                value={summary.total_participants}
                prefix={<CheckCircleOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic 
                title="PPE Certifications" 
                value={summary.total_certifications}
              />
            </Col>
            <Col span={6}>
              <Statistic 
                title="Total Votes" 
                value={summary.total_votes}
              />
            </Col>
            <Col span={6}>
              <Statistic 
                title="Status" 
                value={summary.is_valid ? "Valid" : "Invalid"}
                valueStyle={{ color: summary.is_valid ? '#3f8600' : '#cf1322' }}
              />
            </Col>
          </Row>

          <Divider />

          <Title level={5}>Vote Tally</Title>
          {Object.entries(summary.vote_tally).map(([option, count]) => (
            <div key={option} style={{ marginBottom: '8px' }}>
              <Text strong>{option}: </Text>
              <Text>{count} votes</Text>
            </div>
          ))}
        </Card>
      )}

      {/* Hash Verification */}
      {hashVerification && (
        <Card 
          title="Cryptographic Hash Verification"
          extra={
            hashVerification.is_valid ? (
              <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '20px' }} />
            ) : (
              <WarningOutlined style={{ color: '#faad14', fontSize: '20px' }} />
            )
          }
        >
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="Verification Status">
              {hashVerification.is_valid ? (
                <Text type="success">Hash Verified</Text>
              ) : (
                <Text type="warning">Hash Mismatch</Text>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="Stored Hash">
              <Text code style={{ fontSize: '11px' }}>
                {hashVerification.stored_hash}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="Computed Hash">
              <Text code style={{ fontSize: '11px' }}>
                {hashVerification.computed_hash}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="Match">
              {hashVerification.match ? 'Yes' : 'No'}
            </Descriptions.Item>
          </Descriptions>

          <Alert
            style={{ marginTop: '16px' }}
            message="About the Hash"
            description="The hash is a cryptographic fingerprint of the entire proof graph. Any modification to participants, certifications, or votes will change this hash, making tampering detectable."
            type="info"
            showIcon
          />
        </Card>
      )}

      {/* Verification Message */}
      {summary && (
        <Card>
          <Alert
            message={summary.is_valid ? "Poll Verified" : "Verification Issues"}
            description={summary.verification_message}
            type={summary.is_valid ? "success" : "warning"}
            showIcon
          />
        </Card>
      )}

      {/* Actions */}
      <Card>
        <Space>
          <Button 
            type="primary"
            icon={<DownloadOutlined />}
            onClick={handleExport}
          >
            Export Proof Graph
          </Button>
          
          <Button
            onClick={loadFullGraph}
            disabled={proofGraph !== null}
          >
            {proofGraph ? 'Full Graph Loaded' : 'Load Full Graph Details'}
          </Button>

          <Button
            icon={<ReloadOutlined />}
            onClick={loadProofData}
          >
            Refresh
          </Button>
        </Space>
      </Card>

      {/* Full Graph Details (if loaded) */}
      {proofGraph && (
        <Card title="Complete Proof Graph Details">
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="Poll ID">
              {proofGraph.metadata.poll_id}
            </Descriptions.Item>
            <Descriptions.Item label="Question">
              {proofGraph.metadata.question}
            </Descriptions.Item>
            <Descriptions.Item label="Options">
              {proofGraph.metadata.options.join(', ')}
            </Descriptions.Item>
            <Descriptions.Item label="Participants">
              {proofGraph.participants.length}
            </Descriptions.Item>
            <Descriptions.Item label="Certifications">
              {proofGraph.certifications.length}
            </Descriptions.Item>
            <Descriptions.Item label="Votes">
              {proofGraph.votes.length}
            </Descriptions.Item>
            <Descriptions.Item label="Min Certifications Required">
              {proofGraph.metadata.min_certifications_required}
            </Descriptions.Item>
            <Descriptions.Item label="Created At">
              {new Date(proofGraph.metadata.created_at).toLocaleString()}
            </Descriptions.Item>
          </Descriptions>

          <Alert
            style={{ marginTop: '16px' }}
            message="Complete Graph Loaded"
            description="The full proof graph with all participants, certifications, and votes is now available. You can export this for independent verification."
            type="info"
            showIcon
          />
        </Card>
      )}

      {/* Verification Instructions */}
      <Card title="How to Verify This Poll">
        <Paragraph>
          Anyone can independently verify this poll by:
        </Paragraph>
        <ol>
          <li>
            <Text strong>Download the proof graph</Text> using the export button
          </li>
          <li>
            <Text strong>Verify the hash</Text> - Recompute the graph hash and ensure it matches
          </li>
          <li>
            <Text strong>Verify signatures</Text> - Check all vote signatures are valid
          </li>
          <li>
            <Text strong>Verify certifications</Text> - Ensure all voters have sufficient PPE certifications
          </li>
          <li>
            <Text strong>Check graph properties</Text> - Verify the certification graph has good expansion
          </li>
        </ol>
        <Paragraph type="secondary">
          The proof graph is self-contained and requires no trust in the pollster.
        </Paragraph>
      </Card>
    </Space>
  );
}

export default ProofGraphViewer;