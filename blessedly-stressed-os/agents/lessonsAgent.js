const courseFramework = require('../data/course_framework.json');
const stateCheckDefinitions = require('../data/state_check_definitions.json');
const { createIntegrationStub } = require('../integrations/stubbedIntegrations');

async function createLessonsResponse(rawInput) {
  const integration = await createIntegrationStub('lessons', rawInput);

  return {
    agent: 'lessons',
    output: `A lesson arc was prepared for: "${rawInput}". It includes a teaching objective, a reflection exercise and a home practice plan.`,
    memory: {
      courseFramework,
      stateCheck: stateCheckDefinitions,
      integration
    }
  };
}

module.exports = {
  createLessonsResponse
};
