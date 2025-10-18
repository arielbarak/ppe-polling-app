/**
 * Client-side parameter validation utilities.
 */

/**
 * Validate basic parameter bounds on the client side.
 */
export const validateParameterBounds = (params) => {
  const errors = [];
  const warnings = [];

  if (!params) {
    errors.push("Parameters are required");
    return { valid: false, errors, warnings };
  }

  // Basic bounds checking
  if (!params.m || params.m < 10) {
    errors.push("Participant count (m) must be at least 10");
  }

  if (!params.d || params.d <= 0) {
    errors.push("Degree (d) must be positive");
  }

  if (params.kappa && (params.kappa < 20 || params.kappa > 128)) {
    errors.push("Security parameter (κ) must be between 20 and 128");
  }

  if (params.eta_v && (params.eta_v <= 0 || params.eta_v >= 0.5)) {
    errors.push("Max deleted nodes (ηV) must be between 0 and 0.5");
  }

  if (params.eta_e && (params.eta_e <= 0 || params.eta_e >= 0.5)) {
    errors.push("Max failed PPEs (ηE) must be between 0 and 0.5");
  }

  // Check if degree exceeds participants
  if (params.d && params.m && params.d > params.m) {
    errors.push("Degree (d) cannot exceed participant count (m)");
  }

  // Warning for high effort
  if (params.d && params.d > 80) {
    warnings.push(`High user effort required: ${params.d.toFixed(0)} verifications per user`);
  }

  // Warning for very dense graph
  const p = params.d / params.m;
  if (p > 0.5) {
    warnings.push(`Very dense graph: ${(p * 100).toFixed(1)}% edge probability`);
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
};

/**
 * Estimate user effort in minutes.
 */
export const estimateUserEffort = (degree) => {
  // Assume ~30 seconds per verification
  return Math.round((degree * 0.5) * 10) / 10;
};

/**
 * Get security level description.
 */
export const getSecurityLevelDescription = (resistance) => {
  if (resistance >= 98) return { level: "Excellent", color: "green" };
  if (resistance >= 95) return { level: "Very Good", color: "green" };
  if (resistance >= 90) return { level: "Good", color: "blue" };
  if (resistance >= 80) return { level: "Fair", color: "yellow" };
  return { level: "Poor", color: "red" };
};

/**
 * Get effort level description.
 */
export const getEffortLevelDescription = (degree) => {
  if (degree >= 100) return { level: "Very High", color: "red" };
  if (degree >= 80) return { level: "High", color: "orange" };
  if (degree >= 60) return { level: "Medium", color: "yellow" };
  if (degree >= 40) return { level: "Low", color: "green" };
  return { level: "Very Low", color: "green" };
};

/**
 * Format parameter values for display.
 */
export const formatParameterValue = (key, value) => {
  switch (key) {
    case 'eta_v':
    case 'eta_e':
      return `${(value * 100).toFixed(1)}%`;
    case 'p':
      return value.toFixed(4);
    case 'd':
    case 'b':
      return value.toFixed(1);
    case 'm':
    case 'kappa':
      return value.toString();
    default:
      return typeof value === 'number' ? value.toFixed(3) : value;
  }
};

/**
 * Get parameter description for UI.
 */
export const getParameterDescription = (key) => {
  const descriptions = {
    m: "Total number of participants in the poll",
    d: "Number of verifications each user must complete",
    kappa: "Security parameter (higher = more secure)",
    eta_v: "Maximum percentage of users that can be deleted/inactive",
    eta_e: "Maximum percentage of verifications that can fail",
    p: "Probability that any two users are connected",
    b: "Graph expansion parameter (must be ≥ 1)"
  };
  
  return descriptions[key] || "Parameter description not available";
};

/**
 * Calculate approximate poll completion time.
 */
export const estimatePollDuration = (participants, degree) => {
  // Assume users complete verifications over time
  // Peak participation in first few hours
  const avgVerificationTime = 30; // seconds
  const totalVerifications = participants * degree;
  const parallelFactor = Math.min(participants / 10, 100); // How many work in parallel
  
  const totalTimeSeconds = (totalVerifications * avgVerificationTime) / parallelFactor;
  const hours = Math.round(totalTimeSeconds / 3600);
  
  if (hours < 1) return "< 1 hour";
  if (hours < 24) return `~${hours} hours`;
  const days = Math.round(hours / 24);
  return `~${days} days`;
};