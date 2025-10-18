/**
 * Parameter Configuration Wizard.
 * Guides users through parameter selection.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { 
  Shield, 
  Users, 
  Activity,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  Info
} from 'lucide-react';
import SecurityLevelSelector from './SecurityLevelSelector';
import ParameterValidator from './ParameterValidator';
import ParameterImpactChart from './ParameterImpactChart';
import { parameterService } from '../services/parameterService';

const ParameterWizard = ({ onComplete, initialParams = null }) => {
  const [step, setStep] = useState(1);
  const [expectedParticipants, setExpectedParticipants] = useState(initialParams?.m || 100);
  const [securityLevel, setSecurityLevel] = useState('medium');
  const [calculatedParams, setCalculatedParams] = useState(null);
  const [validation, setValidation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const totalSteps = 3;

  // Initialize with existing parameters if provided
  useEffect(() => {
    if (initialParams) {
      setExpectedParticipants(initialParams.m);
      setCalculatedParams(initialParams);
      setStep(3);
    }
  }, [initialParams]);

  // Step 1: Participant count
  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2">How many participants do you expect?</h3>
        <p className="text-sm text-gray-600 mb-4">
          This determines the security and effort requirements for your poll.
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">
            Expected Participants
          </label>
          <input
            type="number"
            value={expectedParticipants}
            onChange={(e) => {
              const value = Math.max(10, parseInt(e.target.value) || 10);
              setExpectedParticipants(value);
              setError(null);
            }}
            className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            min="10"
            max="100000"
            placeholder="Enter number of participants"
          />
          <p className="text-xs text-gray-500 mt-1">
            Minimum: 10 participants. Higher participant counts require more verifications per user.
          </p>
        </div>

        {/* Participant impact preview */}
        <div className="grid md:grid-cols-3 gap-4">
          {[
            { threshold: 100, effort: "40-60", security: "Medium", desc: "Small polls" },
            { threshold: 1000, effort: "60-80", security: "High", desc: "Medium polls" },
            { threshold: 10000, effort: "80-100", security: "Very High", desc: "Large polls" }
          ].map((range) => (
            <Card 
              key={range.threshold} 
              className={`${expectedParticipants <= range.threshold ? 'ring-2 ring-blue-200 bg-blue-50' : ''}`}
            >
              <CardContent className="pt-4">
                <div className="text-center">
                  <div className="text-lg font-semibold">≤ {range.threshold}</div>
                  <div className="text-sm text-gray-600 mb-2">{range.desc}</div>
                  <div className="text-xs space-y-1">
                    <div>Effort: {range.effort} PPEs</div>
                    <div>Security: {range.security}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Alert className="bg-blue-50 border-blue-200">
          <Users className="h-4 w-4" />
          <AlertDescription className="text-sm">
            <strong>Note:</strong> More participants require more verifications per user 
            to maintain security guarantees from the PPE paper. We'll calculate optimal 
            parameters based on your choice.
          </AlertDescription>
        </Alert>
      </div>

      <Button 
        onClick={() => setStep(2)} 
        className="w-full"
        disabled={expectedParticipants < 10}
      >
        Next: Choose Security Level
        <ArrowRight className="h-4 w-4 ml-2" />
      </Button>
    </div>
  );

  // Step 2: Security level
  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <Button
          variant="ghost"
          onClick={() => setStep(1)}
          className="mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        
        <h3 className="text-lg font-semibold mb-2">Choose Security Level</h3>
        <p className="text-sm text-gray-600 mb-4">
          Higher security requires more effort from users but provides stronger protection against attacks.
        </p>
      </div>

      <SecurityLevelSelector
        selectedLevel={securityLevel}
        onSelect={setSecurityLevel}
        participantCount={expectedParticipants}
      />

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Button 
        onClick={async () => {
          setLoading(true);
          setError(null);
          try {
            const result = await parameterService.calculateParameters(
              expectedParticipants,
              securityLevel
            );
            setCalculatedParams(result.parameters);
            setValidation(result.validation);
            setStep(3);
          } catch (error) {
            console.error('Failed to calculate parameters:', error);
            setError(`Failed to calculate parameters: ${error.message}`);
          } finally {
            setLoading(false);
          }
        }}
        disabled={loading}
        className="w-full"
      >
        {loading ? (
          <>
            <div className="animate-spin h-4 w-4 mr-2 border-2 border-white border-t-transparent rounded-full"></div>
            Calculating Parameters...
          </>
        ) : (
          <>
            Calculate Parameters
            <ArrowRight className="h-4 w-4 ml-2" />
          </>
        )}
      </Button>
    </div>
  );

  // Step 3: Review and confirm
  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <Button
          variant="ghost"
          onClick={() => setStep(2)}
          className="mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        
        <h3 className="text-lg font-semibold mb-2">Review Parameters</h3>
        <p className="text-sm text-gray-600 mb-4">
          These parameters have been calculated to satisfy all security constraints from Appendix C.
        </p>
      </div>

      {calculatedParams && (
        <>
          {/* Parameter Summary */}
          <div className="grid md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Core Parameters</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Participants (m):</span>
                    <span className="font-semibold">{calculatedParams.m}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Degree (d):</span>
                    <span className="font-semibold">{calculatedParams.d.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Security (κ):</span>
                    <span className="font-semibold">{calculatedParams.kappa}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Tolerance Parameters</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Max Deleted (ηV):</span>
                    <span className="font-semibold">{(calculatedParams.eta_v * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Max Failed (ηE):</span>
                    <span className="font-semibold">{(calculatedParams.eta_e * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Edge Prob (p):</span>
                    <span className="font-semibold">{calculatedParams.p.toFixed(4)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Validation Status */}
          <ParameterValidator 
            parameters={calculatedParams}
            onValidationChange={setValidation}
          />

          {/* Impact Analysis */}
          {validation && (
            <ParameterImpactChart 
              parameters={calculatedParams} 
              validation={validation} 
            />
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <Button
              onClick={() => setStep(2)}
              variant="outline"
              className="flex-1"
            >
              Adjust Security Level
            </Button>
            <Button
              onClick={() => onComplete(calculatedParams, validation)}
              disabled={!validation || !validation.valid}
              className="flex-1"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Use These Parameters
            </Button>
          </div>
        </>
      )}
    </div>
  );

  return (
    <Card className="max-w-6xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Poll Parameter Configuration
          </span>
          <Badge variant="outline">
            Step {step} of {totalSteps}
          </Badge>
        </CardTitle>
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${(step / totalSteps) * 100}%` }}
          />
        </div>
      </CardHeader>
      
      <CardContent>
        {step === 1 && renderStep1()}
        {step === 2 && renderStep2()}
        {step === 3 && renderStep3()}
      </CardContent>
    </Card>
  );
};

export default ParameterWizard;