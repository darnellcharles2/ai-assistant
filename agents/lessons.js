const courseFramework = require('../data/courseFramework.json');

function process(idea) {
  return {
    category: 'lessons',
    idea: idea.raw_input,
    agent: 'Lessons & Teaching Agent',
    status: 'stub',
    framework: courseFramework,
    suggestedActions: [
      'Identify the core scripture passage for this lesson',
      'Map lesson to course framework modules',
      'Create lesson outline with key points and applications',
      'Design reflection questions for the learner',
      'Review lesson against spiritual guardrails'
    ],
    output: {
      title: null,
      scripture_anchor: null,
      outline: [],
      reflection_questions: [],
      notes: 'Full lesson generation requires template engine and content review. This is a stub response.'
    }
  };
}

module.exports = { process };
