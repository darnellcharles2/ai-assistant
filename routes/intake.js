const express = require('express');
const router = express.Router();
const { classify, route } = require('../agents/router');
const stateCheck = require('../data/stateCheck.json');

router.post('/', (req, res) => {
  const { raw_input, state_check } = req.body;

  if (!raw_input) {
    return res.status(400).json({
      error: 'raw_input is required',
      hint: 'Send a JSON body with at least a "raw_input" field containing your idea.'
    });
  }

  if (state_check) {
    const redStates = Object.entries(state_check).filter(([, val]) => val === 'red');
    if (redStates.length > 0) {
      return res.status(200).json({
        warning: 'State Check detected red states. Consider pausing before creating.',
        redStates: redStates.map(([key]) => key),
        recommendation: stateCheck.actions.red,
        idea_received: true,
        idea_processed: false,
        raw_input
      });
    }
  }

  const idea = {
    id: `idea-${Date.now()}`,
    raw_input,
    state_check: state_check || null,
    created_at: new Date().toISOString(),
    status: 'received'
  };

  const category = classify(raw_input);
  idea.category = category;

  const result = route(idea);

  res.json({
    success: true,
    idea: {
      id: idea.id,
      raw_input: idea.raw_input,
      category: idea.category,
      created_at: idea.created_at,
      status: 'processed'
    },
    agentOutput: result
  });
});

router.get('/categories', (req, res) => {
  res.json({
    categories: [
      { id: 'music', description: 'Songs, beats, lyrics, worship anthems via DC Flow' },
      { id: 'lessons', description: 'Bible studies, devotionals, teachings' },
      { id: 'skool', description: 'Skool community modules, courses, cohorts' },
      { id: 'digitalProducts', description: 'Ebooks, workbooks, templates, journals' },
      { id: 'brand', description: 'Logos, graphics, thumbnails, cover art' },
      { id: 'automation', description: 'Workflows, webhooks, integrations' },
      { id: 'stewardship', description: 'Finance, time, resource management, accountability' },
      { id: 'general', description: 'Catch-all for ideas that do not match a specific agent' }
    ]
  });
});

module.exports = router;
