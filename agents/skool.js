function process(idea) {
  return {
    category: 'skool',
    idea: idea.raw_input,
    agent: 'Skool Community Builder Agent',
    status: 'stub',
    suggestedActions: [
      'Determine which Skool community this content belongs to',
      'Map idea to a module or post within the community',
      'Draft module content with scripture anchors',
      'Create engagement prompts for community discussion',
      'Schedule content using automation pipeline',
      'Review against spiritual guardrails before publishing'
    ],
    output: {
      community: null,
      module_title: null,
      post_draft: null,
      engagement_prompts: [],
      notes: 'Skool integration requires API access or Make.com automation. This is a stub response.'
    }
  };
}

module.exports = { process };
