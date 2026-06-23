const schemaDefinitions = require('../data/schema_definitions.json');
const { createIntegrationStub } = require('../integrations/stubbedIntegrations');

async function createDigitalProductResponse(rawInput) {
  const integration = await createIntegrationStub('digital_products', rawInput);

  return {
    agent: 'digital_products',
    output: `A digital product concept was drafted for: "${rawInput}". It proposes a workbook structure, an outline and a delivery plan.`,
    memory: {
      schema: schemaDefinitions,
      integration
    }
  };
}

module.exports = {
  createDigitalProductResponse
};
