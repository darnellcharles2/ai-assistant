const { createIntegrationStub } = require('../integrations/stubbedIntegrations');
const courseFramework = require('../data/course_framework.json');

async function createSkoolResponse(rawInput) {
  const integration = await createIntegrationStub('skool', rawInput);

  return {
    agent: 'skool',
    output: `A Skool module outline was generated for: "${rawInput}". The blueprint includes a lesson sequence, a community prompt and a launch checklist.`,
    memory: {
      framework: courseFramework,
      integration
    }
  };
}

module.exports = {
  createSkoolResponse
};
