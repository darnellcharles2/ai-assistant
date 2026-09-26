const express = require('express');
const bodyParser = require('body-parser');
const intakeRoutes = require('./routes/intake');

const app = express();
const PORT = Number(process.env.PORT) || 3000;

app.disable('x-powered-by');
app.use(bodyParser.json({ limit: '1mb' }));
app.use(bodyParser.urlencoded({ extended: false, limit: '1mb' }));

app.get('/health', (req, res) => res.json({ status: 'ok' }));
app.get('/', (req, res) => res.json({ name: 'Blessedly Stressed OS', version: '1.0.0', status: 'running' }));
app.use('/intake', intakeRoutes);

app.use((err, req, res, next) => {
  if (err instanceof SyntaxError && err.status === 400 && err.type === 'entity.parse.failed') {
    return res.status(400).json({ error: 'Invalid JSON request body' });
  }
  if (err.type === 'entity.too.large') return res.status(413).json({ error: 'Request body too large' });
  return next(err);
});

if (require.main === module) {
  app.listen(PORT, () => console.log(`Blessedly Stressed OS running on http://localhost:${PORT}`));
}

module.exports = app;
