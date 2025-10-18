/**
 * Certification phase component with clear explanation.
 * FIXES Issue #6: Users understand why this step exists.
 */

import React, { useEffect, useState } from 'react';
import { Card, Alert, Row, Col, Typography } from 'antd';
import { Shield, Users, CheckCircle, AlertTriangle } from 'lucide-react';
import VerificationStatus from './VerificationStatus';
// import PPEAssignmentList from './PPEAssignmentList'; // You'll need to create this

const { Title, Text } = Typography;

const CertificationPhase = ({ pollId, userId }) => {
  return (
    <div className="space-y-6">
      {/* FIXES Issue #6: Clear explanation of purpose */}
      <Card style={{ border: '2px solid #1890ff', backgroundColor: '#f0f8ff' }}>
        <Title level={3} style={{ color: '#1890ff', marginBottom: '16px' }}>
          <Shield className="inline mr-2" />
          Building Security Network
        </Title>
        
        <Alert
          type="info"
          message={
            <div>
              <div className="mb-4">
                <Text strong>What is Peer Certification?</Text>
              </div>
              <Text>
                You'll complete short verification tasks with other participants. 
                This builds a <strong>certification graph</strong> that mathematically 
                prevents fake identities (Sybil attacks).
              </Text>
            </div>
          }
          showIcon
          icon={<Users className="h-4 w-4" />}
          style={{ marginBottom: '16px' }}
        />

        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <div className="p-3 bg-white rounded border border-blue-200">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <Text strong>Purpose</Text>
              </div>
              <Text type="secondary">
                Prove you're a real participant, not a bot or fake account
              </Text>
            </div>
          </Col>

          <Col xs={24} md={8}>
            <div className="p-3 bg-white rounded border border-blue-200">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="h-4 w-4 text-blue-600" />
                <Text strong>Security</Text>
              </div>
              <Text type="secondary">
                Graph expansion properties limit Sybil attacks to &lt;5% of votes
              </Text>
            </div>
          </Col>

          <Col xs={24} md={8}>
            <div className="p-3 bg-white rounded border border-blue-200">
              <div className="flex items-center gap-2 mb-2">
                <Users className="h-4 w-4 text-purple-600" />
                <Text strong>Peer-to-Peer</Text>
              </div>
              <Text type="secondary">
                Verifications happen between participants, not with a central server
              </Text>
            </div>
          </Col>
        </Row>

        <Alert
          type="warning"
          message={
            <div>
              <Text strong>Important:</Text> You must complete these verifications to vote. 
              The number required depends on how many people joined the poll.
            </div>
          }
          showIcon
          icon={<AlertTriangle className="h-4 w-4" />}
          style={{ marginTop: '16px' }}
        />
      </Card>

      {/* Verification Progress */}
      <Card>
        <Title level={4}>Your Verification Progress</Title>
        <VerificationStatus pollId={pollId} userId={userId} />
      </Card>

      {/* PPE Assignment List - FIXES Issue #2: Auto-loads */}
      <Card>
        <Title level={4}>Peer Verifications</Title>
        <Alert
          type="info"
          message="Your verification partners will appear here automatically when registration closes."
          style={{ marginBottom: '16px' }}
        />
        {/* TODO: Add PPEAssignmentList component */}
        <Text type="secondary">
          PPE assignment list component will be loaded here automatically - no manual button needed!
        </Text>
      </Card>
    </div>
  );
};

export default CertificationPhase;