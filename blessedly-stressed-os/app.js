const express = require('express');
const bodyParser = require('body-parser');
const { classifyIdea, routeIdea } = require('./agents/router');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'blessedly-stressed-os-mvp' });
});

app.post('/intake', async (req, res) => {
  const rawInput = req.body && req.body.raw_input;

  if (!rawInput || typeof rawInput !== 'string' || !rawInput.trim()) {
    return res.status(400).json({ error: 'raw_input is required' });
  }

  const classification = classifyIdea(rawInput);
  const result = await routeIdea(rawInput, classification);

  res.json({
    status: 'received',
    classification,
    raw_input: rawInput,
    agent: result.agent,
    output: result.output,
    memory: result.memory
  });
});

app.get('/', (req, res) => {
  res.send('Blessedly Stressed OS MVP is running. POST to /intake with a raw_input field.');
});

app.listen(PORT, () => {
  console.log(`Blessedly Stressed OS MVP running on http://localhost:${PORT}`);
});
