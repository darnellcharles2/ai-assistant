function process(idea) {
  return {
    category: 'brand',
    idea: idea.raw_input,
    agent: 'Brand & Visual Identity Agent',
    status: 'stub',
    suggestedActions: [
      'Identify the visual asset needed (logo, thumbnail, cover art, graphic)',
      'Pull brand guidelines (colors, fonts, tone) from data memory',
      'Draft design brief aligned with Blessedly Stressed aesthetic',
      'Generate or request visual asset',
      'Review visual against spiritual guardrails and brand consistency',
      'Store final asset in Google Drive'
    ],
    output: {
      asset_type: null,
      design_brief: null,
      file_url: null,
      notes: 'Visual generation requires design API or manual creation. This is a stub response.'
    }
  };
}

module.exports = { process };
