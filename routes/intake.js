const express = require('express');
const router = express.Router();
const { classify, route } = require('../agents/router');
const stateCheck = require('../data/stateCheck.json');

router.post('/', (req, res, next) => {
  try {
    const { raw_input, state_check } = req.body || {};
    if (typeof raw_input !== 'string' || !raw_input.trim()) {
      return res.status(400).json({ error: 'raw_input is required', hint: 'Send a non-empty string in the raw_input field.' });
    }
    if (state_check !== undefined && (state_check === null || typeof state_check !== 'object' || Array.isArray(state_check))) {
      return res.status(400).json({ error: 'state_check must be an object when provided' });
    }

    if (state_check) {
      const redStates = Object.entries(state_check).filter(([, value]) => value === 'red');
      if (redStates.length) {
        return res.status(200).json({
          warning: 'State Check detected red states. Consider pausing before creating.',
          redStates: redStates.map(([key]) => key),
          recommendation: stateCheck.actions.red,
          idea_received: true,
          idea_processed: false,
          raw_input: raw_input.trim()
        });
      }
    }

    const idea = {
      id: `idea-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      raw_input: raw_input.trim(),
      state_check: state_check || null,
      created_at: new Date().toISOString(),
      status: 'received',
      category: classify(raw_input.trim())
    };
    const result = route(idea);
    return res.json({ success: true, idea: { ...idea, status: 'processed' }, agentOutput: result });
  } catch (error) {
    return next(error);
  }
});

router.get('/categories', (req, res) => res.json({ categories: [
  { id: 'music', description: 'Songs, beats, lyrics, worship anthems via DC Flow' },
  { id: 'lessons', description: 'Bible studies, devotionals, teachings' },
  { id: 'skool', description: 'Skool community modules, courses, cohorts' },
  { id: 'digitalProducts', description: 'Ebooks, workbooks, templates, journals' },
  { id: 'brand', description: 'Logos, graphics, thumbnails, cover art' },
  { id: 'automation', description: 'Workflows, webhooks, integrations' },
  { id: 'stewardship', description: 'Finance, time, resource management, accountability' },
  { id: 'general', description: 'Catch-all for ideas that do not match a specific agent' }
] }));

module.exports = router;
