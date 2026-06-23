const musicAgent = require('./music');
const lessonsAgent = require('./lessons');
const skoolAgent = require('./skool');
const digitalProductsAgent = require('./digitalProducts');
const brandAgent = require('./brand');
const automationAgent = require('./automation');
const stewardshipAgent = require('./stewardship');

const CATEGORY_KEYWORDS = {
  music: ['song', 'beat', 'lyric', 'melody', 'track', 'album', 'chorus', 'verse', 'rap', 'hymn', 'worship', 'anthem', 'bible & beats', 'suno'],
  lessons: ['lesson', 'teach', 'study', 'bible study', 'devotional', 'sermon', 'teaching', 'scripture study', 'word study'],
  skool: ['skool', 'module', 'course', 'classroom', 'cohort', 'community', 'enrollment', 'curriculum'],
  digitalProducts: ['ebook', 'workbook', 'pdf', 'template', 'printable', 'download', 'digital product', 'journal', 'planner'],
  brand: ['logo', 'brand', 'visual', 'design', 'graphic', 'thumbnail', 'cover art', 'aesthetic', 'color palette'],
  automation: ['automate', 'automation', 'webhook', 'zap', 'make.com', 'workflow', 'trigger', 'integration', 'pipeline'],
  stewardship: ['steward', 'stewardship', 'finance', 'budget', 'tithe', 'offering', 'resource', 'time management', 'accountability']
};

const AGENTS = {
  music: musicAgent,
  lessons: lessonsAgent,
  skool: skoolAgent,
  digitalProducts: digitalProductsAgent,
  brand: brandAgent,
  automation: automationAgent,
  stewardship: stewardshipAgent
};

function classify(rawInput) {
  const input = rawInput.toLowerCase();
  let bestCategory = 'general';
  let bestScore = 0;

  for (const [category, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    let score = 0;
    for (const keyword of keywords) {
      if (input.includes(keyword)) {
        score += keyword.split(' ').length;
      }
    }
    if (score > bestScore) {
      bestScore = score;
      bestCategory = category;
    }
  }

  return bestCategory;
}

function route(idea) {
  const category = classify(idea.raw_input);
  idea.category = category;

  const agent = AGENTS[category];
  if (agent) {
    return agent.process(idea);
  }

  return {
    category: 'general',
    idea: idea.raw_input,
    guidance: 'This idea did not match a specific agent. Consider refining it or breaking it into smaller pieces aligned with the order of operations.',
    orderReminder: 'Jesus -> Scripture -> Prayer -> State Check -> SAVIOR Made -> Kingdom Flow -> DC Flow -> Savior Saved -> Bible & Beats -> Skool/Course -> Digital Products -> Community Support -> Service'
  };
}

module.exports = { classify, route };
