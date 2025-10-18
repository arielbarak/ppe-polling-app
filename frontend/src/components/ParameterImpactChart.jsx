/**
 * Parameter impact visualization chart.
 */

import React, { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Shield, Users, Activity, Clock } from 'lucide-react';

const ParameterImpactChart = ({ parameters, validation }) => {
  const impactData = useMemo(() => {
    if (!parameters || !validation) return null;

    const sybilResistance = validation.estimated_sybil_resistance || 0;
    const completionRate = validation.estimated_completion_rate || 0;
    const userEffort = parameters.d;
    const graphDensity = (parameters.p || (parameters.d / parameters.m)) * 100;

    return {
      metrics: [
        {
          name: 'Sybil Resistance',
          value: sybilResistance,
          maxValue: 100,
          color: '#10b981',
          icon: Shield,
          unit: '%',
          description: 'Protection against fake accounts'
        },
        {
          name: 'Completion Rate',
          value: completionRate,
          maxValue: 100,
          color: '#3b82f6',
          icon: Activity,
          unit: '%',
          description: 'Expected user completion rate'
        },
        {
          name: 'User Effort',
          value: userEffort,
          maxValue: 100,
          color: '#f59e0b',
          icon: Clock,
          unit: ' PPEs',
          description: 'Verifications required per user'
        },
        {
          name: 'Graph Density',
          value: graphDensity,
          maxValue: 100,
          color: '#8b5cf6',
          icon: Users,
          unit: '%',
          description: 'Network connectivity level'
        }
      ],
      tradeoffs: [
        {
          metric: 'Security vs Usability',
          security: sybilResistance,
          usability: 100 - (userEffort / 100) * 50 // Rough inverse relationship
        }
      ]
    };
  }, [parameters, validation]);

  if (!impactData) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-gray-500">
            No impact data available
          </div>
        </CardContent>
      </Card>
    );
  }

  const getEffortLevel = (effort) => {
    if (effort >= 80) return { level: 'High', color: 'bg-red-100 text-red-800' };
    if (effort >= 50) return { level: 'Medium', color: 'bg-yellow-100 text-yellow-800' };
    return { level: 'Low', color: 'bg-green-100 text-green-800' };
  };

  const getSecurityLevel = (resistance) => {
    if (resistance >= 95) return { level: 'Excellent', color: 'bg-green-100 text-green-800' };
    if (resistance >= 90) return { level: 'Good', color: 'bg-blue-100 text-blue-800' };
    if (resistance >= 80) return { level: 'Fair', color: 'bg-yellow-100 text-yellow-800' };
    return { level: 'Poor', color: 'bg-red-100 text-red-800' };
  };

  const effort = getEffortLevel(parameters.d);
  const security = getSecurityLevel(validation.estimated_sybil_resistance || 0);

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid md:grid-cols-4 gap-4">
        {impactData.metrics.map((metric) => {
          const IconComponent = metric.icon;
          const percentage = (metric.value / metric.maxValue) * 100;
          
          return (
            <Card key={metric.name}>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 mb-2">
                  <IconComponent className="h-4 w-4" style={{ color: metric.color }} />
                  <span className="text-sm font-medium">{metric.name}</span>
                </div>
                
                <div className="space-y-2">
                  <div className="text-2xl font-bold" style={{ color: metric.color }}>
                    {metric.value.toFixed(0)}{metric.unit}
                  </div>
                  
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all duration-300"
                      style={{
                        width: `${Math.min(percentage, 100)}%`,
                        backgroundColor: metric.color
                      }}
                    />
                  </div>
                  
                  <p className="text-xs text-gray-600">{metric.description}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Detailed Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Parameter Impact Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={impactData.metrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis />
                <Tooltip 
                  formatter={(value, name) => [`${value.toFixed(1)}`, name]}
                  labelFormatter={(label) => `Metric: ${label}`}
                />
                <Bar 
                  dataKey="value" 
                  fill="#3b82f6"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Security vs Usability Analysis */}
      <div className="grid md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Security Assessment</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Overall Security Level:</span>
                <Badge className={security.color}>
                  {security.level}
                </Badge>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Sybil Resistance:</span>
                  <span className="font-medium">{(validation.estimated_sybil_resistance || 0).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Security Parameter (κ):</span>
                  <span className="font-medium">{parameters.kappa}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Max Failed PPEs (ηE):</span>
                  <span className="font-medium">{(parameters.eta_e * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Usability Assessment</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">User Effort Level:</span>
                <Badge className={effort.color}>
                  {effort.level}
                </Badge>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>PPEs per User:</span>
                  <span className="font-medium">{parameters.d.toFixed(0)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Est. Time Investment:</span>
                  <span className="font-medium">~{Math.round(parameters.d * 0.5)} minutes</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Expected Completion:</span>
                  <span className="font-medium">{(validation.estimated_completion_rate || 0).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle>Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {validation.estimated_sybil_resistance < 90 && (
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="text-sm font-medium text-yellow-800 mb-1">
                  Consider Higher Security
                </div>
                <div className="text-sm text-yellow-700">
                  Sybil resistance is below 90%. Consider increasing the degree (d) or security parameter (κ).
                </div>
              </div>
            )}
            
            {parameters.d > 80 && (
              <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                <div className="text-sm font-medium text-orange-800 mb-1">
                  High User Effort Required
                </div>
                <div className="text-sm text-orange-700">
                  Users need to complete {parameters.d.toFixed(0)} verifications. Consider if this is acceptable for your use case.
                </div>
              </div>
            )}
            
            {validation.estimated_completion_rate < 80 && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="text-sm font-medium text-red-800 mb-1">
                  Low Completion Rate Expected
                </div>
                <div className="text-sm text-red-700">
                  Only {(validation.estimated_completion_rate || 0).toFixed(1)}% completion expected. Consider reducing user effort.
                </div>
              </div>
            )}
            
            {validation.valid && validation.estimated_sybil_resistance >= 90 && parameters.d <= 60 && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="text-sm font-medium text-green-800 mb-1">
                  Well-Balanced Parameters
                </div>
                <div className="text-sm text-green-700">
                  Good balance between security ({(validation.estimated_sybil_resistance || 0).toFixed(1)}% resistance) and usability ({parameters.d.toFixed(0)} PPEs per user).
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ParameterImpactChart;