/**
 * Base interface for client-side PPE handlers.
 * 
 * All PPE implementations must implement this interface.
 */

export class BasePPEHandler {
  /**
   * @param {string} ppeType - PPE type identifier
   * @param {string} difficulty - Difficulty level
   */
  constructor(ppeType, difficulty = 'medium') {
    this.ppeType = ppeType;
    this.difficulty = difficulty;
  }

  /**
   * Generate a challenge with secret.
   * 
   * @param {string} secret - Secret key
   * @param {string} sessionId - Session identifier
   * @returns {Promise<{challengeData: any, solution: string}>}
   */
  async generateChallengeWithSecret(secret, sessionId) {
    throw new Error('generateChallengeWithSecret must be implemented');
  }

  /**
   * Verify challenge generation.
   * 
   * @param {string} secret - Secret key
   * @param {string} sessionId - Session identifier
   * @param {any} challengeData - Challenge data
   * @param {string} solution - Solution
   * @returns {Promise<boolean>}
   */
  async verifyChallengeGeneration(secret, sessionId, challengeData, solution) {
    throw new Error('verifyChallengeGeneration must be implemented');
  }

  /**
   * Verify a solution.
   * 
   * @param {any} challengeData - Challenge data
   * @param {string} solution - Proposed solution
   * @returns {Promise<boolean>}
   */
  async verifySolution(challengeData, solution) {
    throw new Error('verifySolution must be implemented');
  }

  /**
   * Render the challenge UI.
   * 
   * @param {any} challengeData - Challenge to display
   * @param {Function} onSolutionSubmit - Callback for solution submission
   * @returns {React.Component}
   */
  renderChallenge(challengeData, onSolutionSubmit) {
    throw new Error('renderChallenge must be implemented');
  }

  /**
   * Get estimated effort in seconds.
   * 
   * @returns {number}
   */
  getEstimatedEffort() {
    const difficultyTimes = {
      'easy': 5,
      'medium': 10,
      'hard': 20
    };
    return difficultyTimes[this.difficulty] || 10;
  }
}