const { createMusicResponse } = require('./musicAgent');
const { createLessonsResponse } = require('./lessonsAgent');
const { createSkoolResponse } = require('./skoolAgent');
const { createDigitalProductResponse } = require('./digitalProductAgent');
const { createBrandVisualsResponse } = require('./brandVisualsAgent');
const { createAutomationResponse } = require('./automationAgent');
const { createStewardshipResponse } = require('./stewardshipAgent');
const { createGeneralResponse } = require('./generalAgent');

function classifyIdea(rawInput) {
  const value = rawInput.toLowerCase();

  if (/(song|lyrics|music|beat|melody|suno)/.test(value)) return 'music';
  if (/(lesson|teach|course|curriculum|workbook|module)/.test(value)) return 'lessons';
  if (/(skool|community|membership|launch|program)/.test(value)) return 'skool';
  if (/(digital product|ebook|template|pdf|guide|download)/.test(value)) return 'digital_products';
  if (/(brand|logo|visual|graphic|design|asset)/.test(value)) return 'brand_assets';
  if (/(automation|workflow|make|zapier|webhook|integrat)/.test(value)) return 'automation';
  if (/(steward|review|guardrail|spirit|prayer|state check)/.test(value)) return 'stewardship';

  return 'general';
}

async function routeIdea(rawInput, classification) {
  const handlers = {
    music: createMusicResponse,
    lessons: createLessonsResponse,
    skool: createSkoolResponse,
    digital_products: createDigitalProductResponse,
    brand_assets: createBrandVisualsResponse,
    automation: createAutomationResponse,
    stewardship: createStewardshipResponse,
    general: createGeneralResponse
  };

  const handler = handlers[classification] || handlers.general;
  return await handler(rawInput);
}

module.exports = {
  classifyIdea,
  routeIdea
};
