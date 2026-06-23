const { createIntegrationStub } = require('../integrations/stubbedIntegrations');

async function createAutomationResponse(rawInput) {
  const integration = await createIntegrationStub('automation', rawInput);

  return {
    agent: 'automation',
    output: `An automation scenario was drafted for: "${rawInput}". It recommends a webhook, a trigger path and a handoff plan for downstream tools.`,
    memory: {
      integration
    }
  };
}

module.exports = {
  createAutomationResponse
};
