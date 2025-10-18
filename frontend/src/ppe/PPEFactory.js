/**
 * Factory for creating PPE handler instances on the client.
 */

import { SymmetricCaptchaHandler } from './SymmetricCaptchaHandler';

class PPEFactory {
  constructor() {
    this.registry = new Map();
    
    // Register built-in handlers
    this.register('symmetric_captcha', SymmetricCaptchaHandler);
  }

  /**
   * Register a PPE handler.
   * 
   * @param {string} ppeType - PPE type identifier
   * @param {class} handlerClass - Handler class
   */
  register(ppeType, handlerClass) {
    this.registry.set(ppeType, handlerClass);
    console.log(`Registered PPE handler: ${ppeType}`);
  }

  /**
   * Create a PPE handler instance.
   * 
   * @param {string} ppeType - PPE type
   * @param {string} difficulty - Difficulty level
   * @returns {BasePPEHandler}
   */
  create(ppeType, difficulty = 'medium') {
    const HandlerClass = this.registry.get(ppeType);
    
    if (!HandlerClass) {
      throw new Error(`PPE type '${ppeType}' not registered`);
    }
    
    return new HandlerClass(difficulty);
  }

  /**
   * Check if a PPE type is registered.
   * 
   * @param {string} ppeType - PPE type
   * @returns {boolean}
   */
  isRegistered(ppeType) {
    return this.registry.has(ppeType);
  }

  /**
   * Get all registered PPE types.
   * 
   * @returns {string[]}
   */
  getRegisteredTypes() {
    return Array.from(this.registry.keys());
  }
}

// Singleton instance
export const ppeFactory = new PPEFactory();