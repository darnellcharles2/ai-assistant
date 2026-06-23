const axios = require('axios');

const WEBHOOK_URL = process.env.MAKE_WEBHOOK_URL || null;

function isConfigured() {
  return Boolean(WEBHOOK_URL);
}

async function trigger(eventType, payload) {
  if (!isConfigured()) {
    return {
      success: false,
      error: 'Make.com webhook is not configured. Set MAKE_WEBHOOK_URL in .env'
    };
  }

  const data = {
    event: eventType,
    timestamp: new Date().toISOString(),
    source: 'blessedly-stressed-os',
    payload
  };

  try {
    const response = await axios.post(WEBHOOK_URL, data, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 10000
    });
    return {
      success: true,
      status: response.status,
      data: response.data
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      hint: 'Check your MAKE_WEBHOOK_URL and ensure the Make.com scenario is active.'
    };
  }
}

module.exports = { isConfigured, trigger };
