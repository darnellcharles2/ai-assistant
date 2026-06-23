const spiritualGuardrails = require('../data/spiritual_guardrails.json');
const dcFlowPrompts = require('../data/dc_flow_prompts.json');
const { createIntegrationStub } = require('../integrations/stubbedIntegrations');

async function createMusicResponse(rawInput) {
  const integration = await createIntegrationStub('music', rawInput);

  return {
    agent: 'music',
    output: `Music concept drafted for: "${rawInput}". The response includes a suggested hook, a verse outline and a prayerful tone that honors the spiritual guardrails.`,
    memory: {
      guardrails: spiritualGuardrails,
      prompt: dcFlowPrompts.prompts[0],
      integration
    }
  };
}

module.exports = {
  createMusicResponse
};
