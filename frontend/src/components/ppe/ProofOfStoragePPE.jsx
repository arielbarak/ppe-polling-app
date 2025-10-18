/**
 * Proof-of-Storage PPE component.
 * User proves access to cloud storage.
 */

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { Download, Hash, ExternalLink } from 'lucide-react';
import './ppe-components.css';

const ProofOfStoragePPE = ({ execution, onSubmit, onComplete }) => {
  const [fileHash, setFileHash] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [downloadStarted, setDownloadStarted] = useState(false);

  const challengeData = execution.challenge_data;

  const handleDownload = () => {
    setDownloadStarted(true);
    window.open(challengeData.share_link, '_blank');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitted(true);
    
    const response = {
      file_hash: fileHash.trim()
    };
    
    try {
      const result = await onSubmit(response);
      onComplete(result.success, result.failure_reason);
    } catch (error) {
      onComplete(false, error.message);
    }
  };

  return (
    <Card className="ppe-card">
      <CardHeader>
        <CardTitle>Proof of Storage Verification</CardTitle>
      </CardHeader>
      <CardContent className="ppe-content">
        <Alert className="ppe-info">
          <AlertDescription>
            <strong>How it works:</strong> Download a challenge file from cloud storage,
            compute its hash, and submit the hash to prove you have access.
          </AlertDescription>
        </Alert>

        {/* Instructions */}
        <div className="instructions">
          <h4 className="instructions-title">Instructions:</h4>
          {Object.entries(challengeData.instructions).map(([key, value]) => (
            <div key={key} className="instruction-step">
              <span className="step-number">{key.replace('step_', '')}.</span>
              <span className="step-text">{value}</span>
            </div>
          ))}
        </div>

        {/* File Info */}
        <div className="file-info">
          <div className="file-info-row">
            <span className="file-info-label">Filename:</span>
            <span className="file-info-value">{challengeData.filename}</span>
          </div>
          <div className="file-info-row">
            <span className="file-info-label">Size:</span>
            <span className="file-info-value">{(challengeData.file_size / 1024).toFixed(1)} KB</span>
          </div>
          <div className="file-info-row">
            <span className="file-info-label">Storage:</span>
            <span className="file-info-value storage-provider">
              {challengeData.storage_provider.replace('_', ' ')}
            </span>
          </div>
        </div>

        {/* Download Button */}
        <Button
          onClick={handleDownload}
          disabled={downloadStarted}
          className="download-button"
          variant="outline"
        >
          <Download className="button-icon" />
          {downloadStarted ? 'Link Opened' : 'Download Challenge File'}
          <ExternalLink className="button-icon" />
        </Button>

        {/* Hash Input */}
        <form onSubmit={handleSubmit} className="ppe-form">
          <div>
            <label className="input-label hash-label">
              <Hash className="label-icon" />
              File SHA-256 Hash
            </label>
            <Input
              type="text"
              value={fileHash}
              onChange={(e) => setFileHash(e.target.value)}
              disabled={submitted}
              placeholder="Paste the SHA-256 hash here..."
              className="hash-input"
            />
            <p className="hash-help">
              Use: <code>sha256sum {challengeData.filename}</code>
            </p>
          </div>

          <Button
            type="submit"
            disabled={submitted || !fileHash.trim() || fileHash.length !== 64}
            className="submit-button"
          >
            {submitted ? 'Verifying Hash...' : 'Submit Hash'}
          </Button>
        </form>

        <div className="ppe-description">
          This proves you have access to {challengeData.storage_provider} without sharing credentials.
        </div>
      </CardContent>
    </Card>
  );
};

export default ProofOfStoragePPE;