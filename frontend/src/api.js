// The base URL for your local FastAPI backend
const BASE_URL = 'http://127.0.0.1:8000/api';

/**
 * Fetches the current configuration variables from the .env file.
 */
export const fetchConfig = async () => {
  try {
    const response = await fetch(`${BASE_URL}/config`);
    if (!response.ok) throw new Error('Network response was not ok');
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch config:", error);
    return null;
  }
};

/**
 * Sends updated configuration variables to overwrite the .env file.
 * @param {Object} configData - The JSON payload containing URL, message, and time.
 */
export const saveConfig = async (configData) => {
  try {
    const response = await fetch(`${BASE_URL}/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(configData),
    });
    if (!response.ok) throw new Error('Network response was not ok');
    return await response.json();
  } catch (error) {
    console.error("Failed to save config:", error);
    return null;
  }
};

/**
 * Triggers the background subprocess to launch the manual Facebook login script.
 */
export const triggerSetupSession = async () => {
  try {
    const response = await fetch(`${BASE_URL}/run-setup`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Network response was not ok');
    return await response.json();
  } catch (error) {
    console.error("Failed to trigger setup session:", error);
    return null;
  }
};