/**
 * Component to visualize the ideal certification graph.
 * Shows which users should perform PPE with each other.
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Spin, Alert, Descriptions, Space, Table, Tag } from 'antd';
import { ReloadOutlined, ShareAltOutlined } from '@ant-design/icons';
import { getFullGraph, generateGraph } from '../services/graphApi';

function IdealGraphVisualization({ pollId, currentUserId }) {
  const [graphData, setGraphData] = useState(null);
  const [properties, setProperties] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadGraph = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get the full graph
      const data = await getFullGraph(pollId);
      
      setGraphData(data.graph);
      setProperties(data.properties);
      setLoading(false);
    } catch (err) {
      console.error('Error loading graph:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    try {
      setLoading(true);
      await generateGraph(pollId, 3);
      await loadGraph();
    } catch (err) {
      console.error('Error regenerating graph:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, [pollId]);

  if (loading) {
    return (
      <Card title="Ideal Certification Graph">
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
          <p style={{ marginTop: '16px' }}>Loading graph...</p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="Ideal Certification Graph">
        <Alert
          message="Error Loading Graph"
          description={error}
          type="error"
          showIcon
        />
        <Button 
          onClick={loadGraph} 
          icon={<ReloadOutlined />}
          style={{ marginTop: '16px' }}
        >
          Retry
        </Button>
      </Card>
    );
  }

  // Prepare table data for adjacency list view
  const tableData = graphData ? Object.entries(graphData).map(([userId, neighbors], index) => ({
    key: index,
    userId: userId,
    neighbors: neighbors,
    isCurrentUser: userId === currentUserId,
    neighborCount: neighbors.length,
  })) : [];

  const columns = [
    {
      title: 'User ID',
      dataIndex: 'userId',
      key: 'userId',
      render: (text, record) => (
        <span style={{ fontWeight: record.isCurrentUser ? 'bold' : 'normal' }}>
          {text.substring(0, 12)}...
          {record.isCurrentUser && <Tag color="blue" style={{ marginLeft: 8 }}>You</Tag>}
        </span>
      ),
    },
    {
      title: 'PPE Partners',
      dataIndex: 'neighbors',
      key: 'neighbors',
      render: (neighbors) => (
        <div>
          {neighbors.map((neighbor, index) => (
            <Tag key={index} color="green" style={{ marginBottom: 4 }}>
              {neighbor.substring(0, 8)}...
            </Tag>
          ))}
        </div>
      ),
    },
    {
      title: 'Partner Count',
      dataIndex: 'neighborCount',
      key: 'neighborCount',
      sorter: (a, b) => a.neighborCount - b.neighborCount,
    },
  ];

  return (
    <Card 
      title={
        <Space>
          <ShareAltOutlined />
          Ideal Certification Graph
        </Space>
      }
      extra={
        <Button 
          onClick={handleRegenerate} 
          icon={<ReloadOutlined />}
          size="small"
        >
          Regenerate
        </Button>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {properties && (
          <Descriptions 
            bordered 
            size="small" 
            column={2}
            title="Graph Properties"
          >
            <Descriptions.Item label="Nodes" span={1}>
              {properties.num_nodes}
            </Descriptions.Item>
            <Descriptions.Item label="Edges" span={1}>
              {properties.num_edges}
            </Descriptions.Item>
            <Descriptions.Item label="Min Degree" span={1}>
              {properties.min_degree}
            </Descriptions.Item>
            <Descriptions.Item label="Max Degree" span={1}>
              {properties.max_degree}
            </Descriptions.Item>
            <Descriptions.Item label="Avg Degree" span={1}>
              {properties.avg_degree.toFixed(2)}
            </Descriptions.Item>
            <Descriptions.Item label="Connected" span={1}>
              <Tag color={properties.is_connected ? 'green' : 'red'}>
                {properties.is_connected ? 'Yes' : 'No'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Symmetric" span={1}>
              <Tag color={properties.is_symmetric ? 'green' : 'red'}>
                {properties.is_symmetric ? 'Yes' : 'No'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Valid" span={1}>
              <Tag color={properties.is_valid ? 'green' : 'red'}>
                {properties.is_valid ? 'Yes' : 'No'}
              </Tag>
            </Descriptions.Item>
          </Descriptions>
        )}

        {tableData.length > 0 && (
          <div>
            <h4>PPE Partner Assignments</h4>
            <Table
              columns={columns}
              dataSource={tableData}
              pagination={false}
              size="middle"
              scroll={{ y: 400 }}
            />
          </div>
        )}

        <Alert
          message="About the Ideal Graph"
          description="This graph shows which participants should perform PPE (Public verification of Private Effort) with each other. Each user is assigned a fixed set of neighbors to ensure uniform effort distribution and good expansion properties for Sybil resistance. The graph is deterministic based on the poll ID and participant list."
          type="info"
          showIcon
        />

        {currentUserId && graphData && graphData[currentUserId] && (
          <Alert
            message="Your PPE Partners"
            description={
              <div>
                You will perform PPE with: {' '}
                {graphData[currentUserId].map((neighbor, index) => (
                  <Tag key={index} color="blue">
                    {neighbor.substring(0, 12)}...
                  </Tag>
                ))}
              </div>
            }
            type="success"
            showIcon
          />
        )}
      </Space>
    </Card>
  );
}

export default IdealGraphVisualization;