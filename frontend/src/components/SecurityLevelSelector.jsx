/**
 * Security level selection component.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Shield, Users, Clock, CheckCircle } from 'lucide-react';
import { parameterService } from '../services/parameterService';

const SecurityLevelSelector = ({ selectedLevel, onSelect, participantCount }) => {
  const [presets, setPresets] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPresets = async () => {
      try {
        const data = await parameterService.getPresets();
        setPresets(data.presets);
      } catch (error) {
        console.error('Failed to fetch presets:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchPresets();
  }, []);

  if (loading) {
    return <div className="text-center py-8">Loading security levels...</div>;
  }

  if (!presets) {
    return <div className="text-center py-8 text-red-600">Failed to load security levels</div>;
  }

  const levels = ['high', 'medium', 'low'];

  return (
    <div className="grid md:grid-cols-3 gap-4">
      {levels.map((level) => {
        const preset = presets[level];
        const isSelected = selectedLevel === level;
        
        const getSecurityColor = (level) => {
          switch (level) {
            case 'high': return 'text-green-600';
            case 'medium': return 'text-blue-600';
            case 'low': return 'text-gray-600';
            default: return 'text-gray-600';
          }
        };

        const getBadgeVariant = (level) => {
          switch (level) {
            case 'high': return 'default';
            case 'medium': return 'secondary';
            case 'low': return 'outline';
            default: return 'outline';
          }
        };

        const getBadgeText = (level) => {
          switch (level) {
            case 'high': return 'Recommended for Elections';
            case 'medium': return 'Recommended for Polls';
            case 'low': return 'For Casual Surveys';
            default: return '';
          }
        };
        
        return (
          <Card
            key={level}
            className={`cursor-pointer transition-all hover:shadow-md ${
              isSelected
                ? 'ring-2 ring-blue-500 bg-blue-50'
                : 'hover:shadow-md'
            }`}
            onClick={() => onSelect(level)}
          >
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Shield className={`h-5 w-5 ${getSecurityColor(level)}`} />
                    <h4 className="font-semibold capitalize">{level} Security</h4>
                  </div>
                  {isSelected && (
                    <CheckCircle className="h-5 w-5 text-blue-600" />
                  )}
                </div>

                <p className="text-sm text-gray-600">
                  {preset.description}
                </p>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-gray-400" />
                    <span>{preset.recommended_d} verifications/user</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Shield className="h-4 w-4 text-gray-400" />
                    <span>{preset.sybil_resistance_percentage}% Sybil resistant</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-gray-400" />
                    <span>~{Math.round(preset.recommended_d * 0.5)} min effort</span>
                  </div>
                </div>

                <div className="pt-3 border-t">
                  <Badge 
                    variant={getBadgeVariant(level)}
                    className="w-full justify-center"
                  >
                    {getBadgeText(level)}
                  </Badge>
                </div>

                {participantCount && (
                  <div className="pt-2 border-t text-xs text-gray-500">
                    <div>For {participantCount} participants:</div>
                    <div>• Security parameter: κ = {preset.recommended_kappa}</div>
                    <div>• Max deleted nodes: {(preset.recommended_eta_v * 100).toFixed(1)}%</div>
                    <div>• Max failed PPEs: {(preset.recommended_eta_e * 100).toFixed(1)}%</div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

export default SecurityLevelSelector;