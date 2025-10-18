/**
 * PPE type selector component.
 * Allows users to choose which PPE type to use.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { 
  Image, 
  Cloud, 
  Cpu, 
  Users, 
  CheckCircle,
  Clock,
  Shield
} from 'lucide-react';
import { ppeService } from '../../services/ppeService';
import './ppe-components.css';

const PPETypeSelector = ({ pollId, onSelect, disabled = false }) => {
  const [availableTypes, setAvailableTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTypes = async () => {
      try {
        const response = await ppeService.getAvailableTypes(pollId);
        setAvailableTypes(response.available_types || []);
      } catch (error) {
        console.error('Failed to fetch PPE types:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    if (pollId) {
      fetchTypes();
    }
  }, [pollId]);

  const typeIcons = {
    symmetric_captcha: Image,
    proof_of_storage: Cloud,
    computational: Cpu,
    social_distance: Users
  };

  const typeColors = {
    symmetric_captcha: 'type-card-blue',
    proof_of_storage: 'type-card-green',
    computational: 'type-card-purple',
    social_distance: 'type-card-orange'
  };

  if (loading) {
    return <div className="ppe-loading">Loading PPE options...</div>;
  }

  if (error) {
    return <div className="ppe-error">Error loading PPE types: {error}</div>;
  }

  if (availableTypes.length === 0) {
    return <div className="ppe-no-types">No PPE types available for this poll.</div>;
  }

  return (
    <div className="ppe-type-selector">
      <h3 className="selector-title">Choose Verification Method</h3>
      
      <div className="type-grid">
        {availableTypes.map((type) => {
          const Icon = typeIcons[type.type] || CheckCircle;
          const colorClass = typeColors[type.type] || 'type-card-default';
          
          return (
            <Card
              key={type.type}
              className={`type-card ${colorClass} ${disabled ? 'disabled' : ''}`}
              onClick={() => !disabled && onSelect(type.type)}
            >
              <CardContent className="type-card-content">
                <div className="type-card-layout">
                  <div className="type-icon">
                    <Icon className="icon" />
                  </div>
                  
                  <div className="type-info">
                    <div className="type-header">
                      <h4 className="type-name">{type.name}</h4>
                      <div className="type-badges">
                        <Badge variant="outline" className="effort-badge">
                          {type.effort} effort
                        </Badge>
                        {type.is_default && (
                          <Badge className="default-badge">
                            Default
                          </Badge>
                        )}
                      </div>
                    </div>
                    
                    <p className="type-description">
                      {type.description}
                    </p>
                    
                    <div className="type-metadata">
                      <div className="metadata-item">
                        <Clock className="metadata-icon" />
                        <span>{type.effort}</span>
                      </div>
                      <div className="metadata-item">
                        <Shield className="metadata-icon" />
                        <span>{type.security}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default PPETypeSelector;