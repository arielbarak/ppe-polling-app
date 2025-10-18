/**
 * Symmetric CAPTCHA PPE handler implementation.
 */

import { BasePPEHandler } from './BasePPEHandler';
import React from 'react';
import { Input, Typography } from 'antd';

const { Text } = Typography;

export class SymmetricCaptchaHandler extends BasePPEHandler {
  constructor(difficulty = 'medium') {
    super('symmetric_captcha', difficulty);
  }

  async generateChallengeWithSecret(secret, sessionId) {
    // Create deterministic seed
    const seedInput = `${secret}:${sessionId}`;
    const encoder = new TextEncoder();
    const data = encoder.encode(seedInput);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = new Uint8Array(hashBuffer);
    
    // Use hash as seed
    let seed = 0;
    for (let i = 0; i < 8; i++) {
      seed = (seed << 8) | hashArray[i];
    }
    
    // Seeded random generator
    const seededRandom = (function(s) {
      return function() {
        s = (s * 9301 + 49297) % 233280;
        return s / 233280;
      };
    })(seed);
    
    // Generate solution based on difficulty
    const lengthMap = {
      'easy': 4,
      'medium': 6,
      'hard': 8
    };
    const length = lengthMap[this.difficulty] || 6;
    
    const chars = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789';
    let solution = '';
    for (let i = 0; i < length; i++) {
      const index = Math.floor(seededRandom() * chars.length);
      solution += chars[index];
    }
    
    // Challenge with spaces
    const challengeData = solution.split('').join(' ');
    
    return { challengeData, solution };
  }

  async verifyChallengeGeneration(secret, sessionId, challengeData, solution) {
    const { solution: regenerated } = await this.generateChallengeWithSecret(secret, sessionId);
    return regenerated.toLowerCase() === solution.toLowerCase();
  }

  async verifySolution(challengeData, solution) {
    const expected = challengeData.replace(/\s/g, '').toLowerCase().trim();
    const provided = solution.toLowerCase().trim();
    return expected === provided;
  }

  renderChallenge(challengeData, onSolutionSubmit) {
    const [solution, setSolution] = React.useState('');

    const handleSubmit = () => {
      if (solution.trim()) {
        onSolutionSubmit(solution.trim());
      }
    };

    return (
      <div>
        <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: '8px',
          padding: '40px',
          textAlign: 'center',
          margin: '20px 0'
        }}>
          <div style={{
            fontSize: '32px',
            fontWeight: 'bold',
            letterSpacing: '4px',
            color: 'white',
            fontFamily: 'monospace',
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '4px'
          }}>
            {challengeData}
          </div>
        </div>
        
        <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginBottom: '16px' }}>
          Type the characters shown above (ignore spaces, not case-sensitive)
        </Text>
        
        <Input
          size="large"
          placeholder="Enter your solution"
          value={solution}
          onChange={(e) => setSolution(e.target.value)}
          onPressEnter={handleSubmit}
        />
      </div>
    );
  }
}