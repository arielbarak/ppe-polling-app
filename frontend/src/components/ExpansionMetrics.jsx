/**
 * Graph Expansion Metrics Display Component
 * Shows all expansion properties and THE KEY METRIC: Sybil resistance bound
 */

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle, AlertTriangle, Shield, TrendingUp } from 'lucide-react';
import { expansionService } from '../services/expansionService';

const ExpansionMetrics = ({ pollId }) => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const data = await expansionService.getExpansionMetrics(pollId);
        setMetrics(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, [pollId]);

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Computing expansion properties...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Failed to compute expansion metrics: {error}
        </AlertDescription>
      </Alert>
    );
  }

  if (!metrics) return null;

  const getResistanceBadge = (level) => {
    const variants = {
      HIGH: 'bg-green-100 text-green-800',
      MEDIUM: 'bg-yellow-100 text-yellow-800',
      LOW: 'bg-red-100 text-red-800',
    };
    return (
      <Badge className={variants[level] || 'bg-gray-100 text-gray-800'}>
        {level}
      </Badge>
    );
  };

  const StatusIcon = ({ passes }) => {
    return passes ? (
      <CheckCircle className="h-5 w-5 text-green-600" />
    ) : (
      <XCircle className="h-5 w-5 text-red-600" />
    );
  };

  return (
    <div className="space-y-6">
      {/* Overall Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-6 w-6" />
            Graph Expansion Verification
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3 mb-4">
            <StatusIcon passes={metrics.verification_passed} />
            <span className="text-lg font-semibold">
              {metrics.verification_passed ? 'All Checks Passed' : 'Verification Failed'}
            </span>
          </div>

          {!metrics.verification_passed && metrics.failure_reasons.length > 0 && (
            <Alert variant="warning">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <div className="font-semibold mb-2">Issues detected:</div>
                <ul className="list-disc list-inside space-y-1">
                  {metrics.failure_reasons.map((reason, idx) => (
                    <li key={idx}>{reason}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div className="text-center p-4 bg-gray-50 rounded">
              <div className="text-2xl font-bold text-gray-900">{metrics.num_nodes}</div>
              <div className="text-sm text-gray-600">Total Nodes</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded">
              <div className="text-2xl font-bold text-green-600">{metrics.num_honest_nodes}</div>
              <div className="text-sm text-gray-600">Honest Nodes</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded">
              <div className="text-2xl font-bold text-gray-900">{metrics.num_edges}</div>
              <div className="text-sm text-gray-600">Edges (PPEs)</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded">
              <div className="text-2xl font-bold text-blue-600">{metrics.average_degree.toFixed(1)}</div>
              <div className="text-sm text-gray-600">Avg Degree</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* THE KEY METRIC: Sybil Resistance Bound */}
      <Card className="border-2 border-blue-500">
        <CardHeader className="bg-blue-50">
          <CardTitle className="flex items-center gap-2 text-blue-900">
            <Shield className="h-6 w-6" />
            Sybil Resistance Bound
            <span className="ml-auto text-sm font-normal">
              {getResistanceBadge(metrics.sybil_bound.resistance_level)}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="mb-6">
            <Alert className="bg-blue-50 border-blue-200">
              <TrendingUp className="h-4 w-4" />
              <AlertDescription>
                <strong>Security Guarantee:</strong> Even if an adversary successfully completes{' '}
                <strong>{metrics.sybil_bound.attack_edges}</strong> PPEs with honest participants,
                they can control at most <strong>{metrics.sybil_bound.max_sybil_nodes}</strong> fake identities
                ({metrics.sybil_bound.sybil_percentage.toFixed(1)}% of total).
              </AlertDescription>
            </Alert>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-3">Sybil Bound Details</h4>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-600">Max Sybil Nodes:</dt>
                  <dd className="font-semibold">{metrics.sybil_bound.max_sybil_nodes}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Percentage:</dt>
                  <dd className="font-semibold">{metrics.sybil_bound.sybil_percentage.toFixed(1)}%</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Attack Edges (a):</dt>
                  <dd className="font-semibold">{metrics.sybil_bound.attack_edges}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Avg Degree (d):</dt>
                  <dd className="font-semibold">{metrics.sybil_bound.average_degree.toFixed(1)}</dd>
                </div>
              </dl>
            </div>

            <div>
              <h4 className="font-semibold mb-3">Adversary Advantage</h4>
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-3xl font-bold text-center mb-2">
                  {metrics.sybil_bound.multiplicative_advantage.toFixed(1)}x
                </div>
                <div className="text-sm text-center text-gray-600">
                  Adversary's advantage over honest user
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-3">
                An adversary investing the same effort as one honest user can influence{' '}
                {metrics.sybil_bound.multiplicative_advantage.toFixed(1)} votes instead of 1.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Expansion Properties */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Vertex Expansion */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <StatusIcon passes={metrics.vertex_expansion.satisfies_threshold} />
              Vertex Expansion
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Expansion Ratio:</span>
                <span className="font-semibold text-lg">
                  {metrics.vertex_expansion.expansion_ratio.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Required:</span>
                <span className="text-sm">≥ {metrics.vertex_expansion.threshold}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    metrics.vertex_expansion.satisfies_threshold ? 'bg-green-600' : 'bg-red-600'
                  }`}
                  style={{
                    width: `${Math.min(
                      (metrics.vertex_expansion.expansion_ratio / metrics.vertex_expansion.threshold) * 100,
                      100
                    )}%`,
                  }}
                ></div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Edge Expansion */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <StatusIcon passes={metrics.edge_expansion.satisfies_threshold} />
              Edge Expansion
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Conductance:</span>
                <span className="font-semibold text-lg">
                  {metrics.edge_expansion.conductance.toFixed(3)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Required:</span>
                <span className="text-sm">≥ {metrics.edge_expansion.threshold}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    metrics.edge_expansion.satisfies_threshold ? 'bg-green-600' : 'bg-red-600'
                  }`}
                  style={{
                    width: `${Math.min(
                      (metrics.edge_expansion.conductance / metrics.edge_expansion.threshold) * 100,
                      100
                    )}%`,
                  }}
                ></div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Spectral Gap */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <StatusIcon passes={metrics.spectral_gap.satisfies_threshold} />
              Spectral Gap
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">λ₂ (Algebraic Connectivity):</span>
                <span className="font-semibold text-lg">
                  {metrics.spectral_gap.lambda_2.toFixed(4)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Required:</span>
                <span className="text-sm">≥ {metrics.spectral_gap.threshold}</span>
              </div>
              <div className="text-xs text-gray-500">
                Computed in {metrics.spectral_gap.computation_time_ms.toFixed(1)}ms
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Minimum Degree */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <StatusIcon passes={metrics.minimum_degree.satisfies_requirement} />
              Minimum Degree
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Minimum:</span>
                <span className="font-semibold text-lg">{metrics.minimum_degree.minimum_degree}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Required:</span>
                <span className="text-sm">≥ {metrics.minimum_degree.required_minimum}</span>
              </div>
              {metrics.minimum_degree.nodes_below_threshold.length > 0 && (
                <Alert variant="warning" className="mt-2">
                  <AlertDescription className="text-xs">
                    {metrics.minimum_degree.nodes_below_threshold.length} nodes below threshold
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* LSE Property */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <StatusIcon passes={metrics.is_lse} />
            LSE Property: (K={metrics.lse_parameters.K}, ρ={metrics.lse_parameters.rho}, q=
            {metrics.lse_parameters.q.toFixed(3)})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600">
            {metrics.is_lse
              ? 'Graph satisfies Large-Set Expanding property with specified parameters.'
              : 'Graph does not satisfy LSE property. Expansion may be insufficient for security guarantees.'}
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default ExpansionMetrics;