/**
 * Real-time parameter validation component.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react';
import { parameterService } from '../services/parameterService';

const ParameterValidator = ({ parameters, onValidationChange }) => {
  const [validation, setValidation] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!parameters) return;

    const validateParams = async () => {
      setLoading(true);
      try {
        const result = await parameterService.validateParameters(parameters);
        setValidation(result);
        if (onValidationChange) {
          onValidationChange(result);
        }
      } catch (error) {
        console.error('Validation failed:', error);
        setValidation({
          valid: false,
          errors: [`Validation error: ${error.message}`],
          warnings: []
        });
      } finally {
        setLoading(false);
      }
    };

    const debounceTimer = setTimeout(validateParams, 500);
    return () => clearTimeout(debounceTimer);
  }, [parameters, onValidationChange]);

  if (!parameters) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-gray-500">
            No parameters to validate
          </div>
        </CardContent>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center">
            <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
            <div className="text-sm text-gray-600">Validating parameters...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!validation) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-gray-500">
            Validation pending...
          </div>
        </CardContent>
      </Card>
    );
  }

  const getConstraintIcon = (satisfied) => {
    return satisfied ? (
      <CheckCircle className="h-4 w-4 text-green-600" />
    ) : (
      <XCircle className="h-4 w-4 text-red-600" />
    );
  };

  const constraintDescriptions = {
    1: "Minimum participants for expansion",
    2: "Edge probability bounds (d/m ≤ p ≤ 1)",
    3: "Expansion parameter (b ≥ 1)",
    4: "Failed PPE threshold",
    5: "Minimum degree requirement",
    6: "Sybil bound validity"
  };

  return (
    <div className="space-y-4">
      {/* Overall Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {validation.valid ? (
              <>
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span className="text-green-600">Parameters Valid</span>
              </>
            ) : (
              <>
                <XCircle className="h-5 w-5 text-red-600" />
                <span className="text-red-600">Validation Failed</span>
              </>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium mb-2">Parameter Values</h4>
              <div className="space-y-1 text-sm">
                <div>Participants (m): <strong>{parameters.m}</strong></div>
                <div>Degree (d): <strong>{parameters.d.toFixed(1)}</strong></div>
                <div>Security (κ): <strong>{parameters.kappa}</strong></div>
                <div>Max Deleted (ηV): <strong>{(parameters.eta_v * 100).toFixed(1)}%</strong></div>
                <div>Max Failed (ηE): <strong>{(parameters.eta_e * 100).toFixed(1)}%</strong></div>
                {parameters.p && (
                  <div>Edge Prob (p): <strong>{parameters.p.toFixed(4)}</strong></div>
                )}
              </div>
            </div>
            
            {validation.valid && (
              <div>
                <h4 className="font-medium mb-2">Security Metrics</h4>
                <div className="space-y-1 text-sm">
                  {validation.estimated_sybil_resistance && (
                    <div>Sybil Resistance: <strong className="text-green-600">
                      {validation.estimated_sybil_resistance.toFixed(1)}%
                    </strong></div>
                  )}
                  {validation.estimated_completion_rate && (
                    <div>Completion Rate: <strong className="text-blue-600">
                      {validation.estimated_completion_rate.toFixed(1)}%
                    </strong></div>
                  )}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Constraint Details */}
      <Card>
        <CardHeader>
          <CardTitle>Constraint Validation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5, 6].map(i => {
              const satisfied = validation[`constraint_${i}_satisfied`];
              return (
                <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-gray-50">
                  {getConstraintIcon(satisfied)}
                  <div className="flex-1">
                    <div className="font-medium text-sm">
                      Constraint {i}: {constraintDescriptions[i]}
                    </div>
                  </div>
                  <Badge variant={satisfied ? "success" : "destructive"}>
                    {satisfied ? "Pass" : "Fail"}
                  </Badge>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Errors */}
      {validation.errors && validation.errors.length > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <div className="font-semibold mb-2">Validation Errors:</div>
            <ul className="list-disc list-inside space-y-1">
              {validation.errors.map((error, idx) => (
                <li key={idx} className="text-sm">{error}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* Warnings */}
      {validation.warnings && validation.warnings.length > 0 && (
        <Alert className="bg-yellow-50 border-yellow-300">
          <AlertTriangle className="h-4 w-4 text-yellow-700" />
          <AlertDescription>
            <div className="font-semibold mb-2 text-yellow-800">Warnings:</div>
            <ul className="list-disc list-inside space-y-1">
              {validation.warnings.map((warning, idx) => (
                <li key={idx} className="text-sm text-yellow-800">{warning}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* Calculated Values */}
      {validation.calculated_values && Object.keys(validation.calculated_values).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-4 w-4" />
              Calculated Values
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-2 text-sm">
              {Object.entries(validation.calculated_values).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-gray-600">{key.replace(/_/g, ' ')}:</span>
                  <span className="font-mono">
                    {typeof value === 'number' ? value.toFixed(3) : value}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ParameterValidator;