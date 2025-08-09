import React, { useState } from 'react';
import { pollApi } from '../api/pollApi';

// The 'navigateToPoll' prop is a function passed down from App.jsx
// to tell it to switch to the poll view.
function CreatePoll({ navigateToPoll }) {
  const [question, setQuestion] = useState('');
  const [options, setOptions] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // Split the options text area by new lines and filter out empty lines.
    const optionsArray = options.split('\n').filter(opt => opt.trim() !== '');

    if (!question || optionsArray.length < 2) {
      setError('Please provide a question and at least two options on separate lines.');
      setIsLoading(false);
      return;
    }

    try {
      const newPoll = await pollApi.createPoll({ question, options: optionsArray });
      // On success, call the navigation function with the new poll's ID
      navigateToPoll(newPoll.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="create-poll-container">
      <h2>Create a New Poll</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="question">Poll Question</label>
          <input
            id="question"
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g., What is your favorite color?"
          />
        </div>
        <div className="form-group">
          <label htmlFor="options">Options (one per line)</label>
          <textarea
            id="options"
            value={options}
            onChange={(e) => setOptions(e.target.value)}
            rows="4"
            placeholder="e.g.,&#10;Red&#10;Green&#10;Blue"
          />
        </div>
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Creating...' : 'Create Poll'}
        </button>
        {error && <p className="error-message">{error}</p>}
      </form>
    </div>
  );
}

export default CreatePoll;
