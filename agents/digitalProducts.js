function process(idea) {
  return {
    category: 'digitalProducts',
    idea: idea.raw_input,
    agent: 'Digital Products Agent',
    status: 'stub',
    suggestedActions: [
      'Identify the type of digital product (workbook, ebook, template, journal)',
      'Map content to course framework and spiritual guardrails',
      'Draft product outline with sections and exercises',
      'Design cover and layout using brand templates',
      'Generate PDF using template engine',
      'Upload to Google Drive and update inventory sheet'
    ],
    output: {
      product_type: null,
      title: null,
      outline: [],
      file_url: null,
      notes: 'PDF generation requires template engine integration. This is a stub response.'
    }
  };
}

module.exports = { process };
