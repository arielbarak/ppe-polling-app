/**
 * Verification status component with DYNAMIC count.
 * FIXES Issue #1: Shows correct verification requirements.
 */

import React, { useEffect, useState } from 'react';
import { Alert, Progress, Card, Typography } from 'antd';
import { CheckCircle, Clock, XCircle, Info } from 'lucide-react';

const { Text, Paragraph } = Typography;

const VerificationStatus = ({ pollId, userId }) => {
  const [requirements, setRequirements] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRequirements = async () => {
      try {
        // This would call your verification service endpoint
        const response = await fetch(`/api/polls/${pollId}/verification/requirements?user_id=${userId}`);
        const data = await response.json();
        setRequirements(data);
      } catch (error) {
        console.error('Failed to fetch verification requirements:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRequirements();
    
    // Refresh every 10 seconds (assignments may be generated)
    const interval = setInterval(fetchRequirements, 10000);
    return () => clearInterval(interval);
  }, [pollId, userId]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-gray-600">
        <Clock className="h-4 w-4 animate-spin" />
        <span>Loading verification status...</span>
      </div>
    );
  }

  if (!requirements) {
    return (
      <Alert
        type="error"
        message="Unable to load verification requirements"
      />
    );
  }

  const { required, completed, remaining } = requirements;
  const percentage = required > 0 ? (completed / required) * 100 : 0;
  const isComplete = completed >= required && required > 0;

  return (
    <div className="space-y-4">
      {/* Status Message - FIXES Issue #1 */}
      <div className="flex items-center gap-3">
        {isComplete ? (
          <>
            <CheckCircle className="h-6 w-6 text-green-600" />
            <div>
              <Text strong className="text-green-700">Certification Complete!</Text>
              <br />
              <Text type="secondary">
                You completed all {required} required verifications
              </Text>
            </div>
          </>
        ) : required === 0 ? (
          <>
            <Clock className="h-6 w-6 text-blue-600" style={{ animation: 'pulse 2s infinite' }} />
            <div>
              <Text strong className="text-blue-700">Waiting for PPE Assignments</Text>
              <br />
              <Text type="secondary">
                Assignments will be generated when registration closes
              </Text>
            </div>
          </>
        ) : (
          <>
            <Clock className="h-6 w-6 text-yellow-600" />
            <div>
              <Text strong>
                You have {completed} out of {required} required verifications
              </Text>
              <br />
              <Text type="secondary">
                {remaining > 0 
                  ? `Complete ${remaining} more verification${remaining > 1 ? 's' : ''} to vote`
                  : 'Processing final verifications...'}
              </Text>
            </div>
          </>
        )}
      </div>

      {/* Progress Bar */}
      {required > 0 && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-600">
            <span>Progress</span>
            <span>{completed} / {required}</span>
          </div>
          <Progress percent={Math.round(percentage)} strokeColor="#1890ff" />
          <Text type="secondary" className="text-xs text-center">
            {percentage.toFixed(1)}% complete
          </Text>
        </div>
      )}

      {/* Explanation Tooltip - FIXES Issue #6 */}
      <Alert
        type="info"
        message={
          <div>
            <Text strong>Why verify?</Text>
            <br />
            <Text>
              These peer-to-peer verifications build a security graph 
              that prevents fake identities (Sybil attacks). The number of verifications depends 
              on how many people joined the poll.
            </Text>
          </div>
        }
        showIcon
        icon={<Info className="h-4 w-4" />}
      />
    </div>
  );
};

export default VerificationStatus;