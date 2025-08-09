import { sha256 } from 'js-sha256';

/**
 * Calculates the ideal neighbors for a given user in the certification graph.
 * This is a simplified implementation of the paper's graph generation.
 * @param {string} currentUserId - The ID of the user for whom to find neighbors.
 * @param {string[]} allUserIds - A sorted list of all registered user IDs.
 * @param {number} degree - The number of neighbors each node should have (k).
 * @returns {string[]} A list of neighbor user IDs.
 */
export const calculateNeighbors = (currentUserId, allUserIds, degree = 2) => {
  if (allUserIds.length <= degree) {
    // In a small poll, everyone connects to everyone else (excluding self)
    return allUserIds.filter(id => id !== currentUserId);
  }

  const currentIndex = allUserIds.indexOf(currentUserId);
  if (currentIndex === -1) return [];

  const neighbors = new Set();
  const n = allUserIds.length;

  // Connect to 'degree / 2' nodes before and after in the sorted list
  for (let i = 1; i <= degree / 2; i++) {
    const prevIndex = (currentIndex - i + n) % n;
    const nextIndex = (currentIndex + i) % n;
    neighbors.add(allUserIds[prevIndex]);
    neighbors.add(allUserIds[nextIndex]);
  }

  return Array.from(neighbors);
};
