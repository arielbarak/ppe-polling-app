/**
 * Component for displaying advanced verification results.
 * 
 * Shows graph analysis, Sybil detection, and statistical metrics.
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Spin, Alert, Descriptions, Space, Statistic, Row, Col, Typography, Collapse, Tag, Progress } from 'antd';
import { CheckCircleOutlined, WarningOutlined, CloseCircleOutlined, ReloadOutlined, SafetyOutlined } from '@ant-design/icons';
import { verifyPollComprehensive, getGraphProperties, detectSybilAttacks } from '../services/verificationApi';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

function AdvancedVerificationPanel({ pollId }) {
  const [verification, setVerification] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadVerification = async () => {
    try {
      setLoading(true);
      setError(null);

      const result = await verifyPollComprehensive(pollId);
      setVerification(result);
      setLoading(false);
    } catch (err) {
      console.error('Verification error:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVerification();
  }, [pollId]);

  if (loading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
          <p style={{ marginTop: '16px' }}>Running verification algorithms...</p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <Alert
          message="Verification Error"
          description={error}
          type="error"
          showIcon
        />
        <Button 
          onClick={loadVerification} 
          icon={<ReloadOutlined />}
          style={{ marginTop: '16px' }}
        >
          Retry
        </Button>
      </Card>
    );
  }

  const getStatusIcon = () => {
    if (verification.is_valid && verification.errors.length === 0) {
      return <CheckCircleOutlined style={{ fontSize: '48px', color: '#52c41a' }} />;
    } else if (verification.errors.length > 0) {
      return <CloseCircleOutlined style={{ fontSize: '48px', color: '#f5222d' }} />;
    } else {
      return <WarningOutlined style={{ fontSize: '48px', color: '#faad14' }} />;
    }
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      {/* Status Summary */}
      <Card>
        <div style={{ textAlign: 'center' }}>
          {getStatusIcon()}
          <Title level={3} style={{ marginTop: '16px' }}>
            {verification.is_valid ? 'Poll Verified ✅' : 'Verification Failed ❌'}
          </Title>
          <Paragraph type="secondary">{verification.summary}</Paragraph>
        </div>
      </Card>

      {/* Key Metrics */}
      <Card title="Key Metrics">
        <Row gutter={16}>
          <Col span={6}>
            <Statistic 
              title="Participants" 
              value={verification.metrics.total_participants}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Certifications" 
              value={verification.metrics.total_certifications}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Valid Votes" 
              value={verification.metrics.valid_votes}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Participation" 
              value={(verification.metrics.participation_rate * 100).toFixed(1)}
              suffix="%"
            />
          </Col>
        </Row>
      </Card>

      {/* Errors */}
      {verification.errors.length > 0 && (
        <Card title={<><CloseCircleOutlined style={{ color: '#f5222d' }} /> Critical Errors</>}>
          {verification.errors.map((error, idx) => (
            <Alert
              key={idx}
              message={error}
              type="error"
              showIcon
              style={{ marginBottom: '8px' }}
            />
          ))}
        </Card>
      )}

      {/* Warnings */}
      {verification.warnings.length > 0 && (
        <Card title={<><WarningOutlined style={{ color: '#faad14' }} /> Warnings</>}>
          {verification.warnings.map((warning, idx) => (
            <Alert
              key={idx}
              message={warning}
              type="warning"
              showIcon
              style={{ marginBottom: '8px' }}
            />
          ))}
        </Card>
      )}

      {/* Detailed Analysis */}
      <Card title="Detailed Analysis">
        <Collapse>
          {/* Graph Properties */}
          {verification.analysis.connectivity && (
            <Panel header="Graph Connectivity & Structure" key="connectivity">
              <Descriptions bordered size="small" column={2}>
                <Descriptions.Item label="Connected">
                  {verification.analysis.connectivity.is_connected ? '✅ Yes' : '❌ No'}
                </Descriptions.Item>
                <Descriptions.Item label="Components">
                  {verification.analysis.connectivity.num_components}
                </Descriptions.Item>
                <Descriptions.Item label="Nodes">
                  {verification.analysis.connectivity.nodes}
                </Descriptions.Item>
                <Descriptions.Item label="Edges">
                  {verification.analysis.connectivity.edges}
                </Descriptions.Item>
                {verification.analysis.connectivity.diameter && (
                  <>
                    <Descriptions.Item label="Diameter">
                      {verification.analysis.connectivity.diameter}
                    </Descriptions.Item>
                    <Descriptions.Item label="Avg Shortest Path">
                      {verification.analysis.connectivity.avg_shortest_path?.toFixed(2)}
                    </Descriptions.Item>
                  </>
                )}
              </Descriptions>
            </Panel>
          )}

          {/* Degree Distribution */}
          {verification.analysis.degree_distribution && (
            <Panel header="Degree Distribution" key="degrees">
              <Descriptions bordered size="small" column={2}>
                <Descriptions.Item label="Min Degree">
                  {verification.analysis.degree_distribution.min}
                </Descriptions.Item>
                <Descriptions.Item label="Max Degree">
                  {verification.analysis.degree_distribution.max}
                </Descriptions.Item>
                <Descriptions.Item label="Mean Degree">
                  {verification.analysis.degree_distribution.mean?.toFixed(2)}
                </Descriptions.Item>
                <Descriptions.Item label="Std Deviation">
                  {verification.analysis.degree_distribution.std?.toFixed(2)}
                </Descriptions.Item>
              </Descriptions>
            </Panel>
          )}

          {/* Expansion Properties */}
          {verification.metrics.spectral_gap !== undefined && (
            <Panel header="Expansion Properties" key="expansion">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text strong>Spectral Gap: </Text>
                  <Text>{verification.metrics.spectral_gap?.toFixed(4)}</Text>
                  <Paragraph type="secondary" style={{ marginTop: '8px' }}>
                    Larger spectral gap indicates better expansion properties.
                  </Paragraph>
                </div>
                
                {verification.metrics.clustering_coefficient !== undefined && (
                  <div>
                    <Text strong>Clustering Coefficient: </Text>
                    <Text>{verification.metrics.clustering_coefficient?.toFixed(4)}</Text>
                    <Paragraph type="secondary" style={{ marginTop: '8px' }}>
                      High clustering may indicate tightly-knit groups.
                    </Paragraph>
                  </div>
                )}
                
                {verification.analysis.expansion_ratios && (
                  <div>
                    <Text strong>Expansion Ratios: </Text>
                    {verification.analysis.expansion_ratios.map((ratio, idx) => (
                      <Tag key={idx} color={ratio > 0.3 ? 'green' : 'orange'}>
                        {ratio.toFixed(3)}
                      </Tag>
                    ))}
                  </div>
                )}
              </Space>
            </Panel>
          )}

          {/* Sybil Detection */}
          {verification.analysis.suspicious_clusters && verification.analysis.suspicious_clusters.length > 0 && (
            <Panel header="⚠️ Suspicious Clusters Detected" key="sybil">
              <Alert
                message="Low-Conductance Clusters Found"
                description="These clusters have low connectivity to the rest of the graph, which may indicate Sybil attacks."
                type="warning"
                showIcon
                style={{ marginBottom: '16px' }}
              />
              {verification.analysis.suspicious_clusters.map((cluster, idx) => (
                <Card key={idx} size="small" style={{ marginBottom: '8px' }}>
                  <Text strong>Cluster {idx + 1}: </Text>
                  <Text>{cluster.size} nodes</Text>
                  <br />
                  <Text type="secondary">Conductance: {cluster.conductance?.toFixed(4)}</Text>
                </Card>
              ))}
            </Panel>
          )}

          {/* Statistical Analysis */}
          <Panel header="Statistical Analysis" key="stats">
            <Descriptions bordered size="small" column={1}>
              <Descriptions.Item label="Certification Coverage">
                <Progress 
                  percent={(verification.metrics.certification_coverage * 100).toFixed(1)} 
                  status={verification.metrics.certification_coverage > 0.1 ? 'success' : 'exception'}
                />
              </Descriptions.Item>
              <Descriptions.Item label="Avg Certifications Per User">
                {verification.metrics.avg_certifications_per_user?.toFixed(2)}
              </Descriptions.Item>
              <Descriptions.Item label="Std Certifications Per User">
                {verification.metrics.std_certifications_per_user?.toFixed(2)}
              </Descriptions.Item>
            </Descriptions>
          </Panel>
        </Collapse>
      </Card>

      {/* Refresh Button */}
      <Card>
        <Button 
          icon={<ReloadOutlined />}
          onClick={loadVerification}
          type="primary"
        >
          Re-run Verification
        </Button>
      </Card>
    </Space>
  );
}

export default AdvancedVerificationPanel;