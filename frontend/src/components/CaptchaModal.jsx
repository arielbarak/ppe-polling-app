import React, { useState } from 'react';

function CaptchaModal({ peerId, challengeText, onSolve, onClose }) {
  const [userInput, setUserInput] = useState('');

  const handleSubmit = () => {
    // The modal's only job is to get the user's input and pass it up.
    // The parent component will handle validation.
    onSolve(userInput);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Peer Certification Challenge</h2>
        <p>Solve the challenge from peer: <strong>{peerId.substring(0, 12)}...</strong></p>
        
        <div className="custom-captcha-container">
          <div className="captcha-text">{challengeText}</div>
        </div>

        <input
          type="text"
          placeholder="Enter the text above"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
        />
        
        <div className="modal-buttons">
          <button onClick={handleSubmit}>Submit Solution</button>
          <button onClick={onClose} className="cancel-button">Cancel</button>
        </div>
      </div>
    </div>
  );
}

export default CaptchaModal;
