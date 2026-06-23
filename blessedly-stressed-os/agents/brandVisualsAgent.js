const { createIntegrationStub } = require('../integrations/stubbedIntegrations');

async function createBrandVisualsResponse(rawInput) {
  const integration = await createIntegrationStub('brand_assets', rawInput);

  return {
    agent: 'brand_assets',
    output: `A brand asset concept was assembled for: "${rawInput}". It includes a visual direction, a brand voice prompt and a recommendation for a simple design system.`,
    memory: {
      integration
    }
  };
}

module.exports = {
  createBrandVisualsResponse
};
