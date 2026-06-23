const express = require('express');
const bodyParser = require('body-parser');
const intakeRoutes = require('./routes/intake');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(bodyParser.json());

app.get('/', (req, res) => {
  res.json({
    name: 'Blessedly Stressed OS',
    version: '1.0.0',
    status: 'running',
    orderOfOperations: [
      'Jesus',
      'Scripture',
      'Prayer',
      'State Check',
      'SAVIOR Made',
      'Kingdom Flow',
      'DC Flow',
      'Savior Saved',
      'Bible & Beats',
      'Skool/Course',
      'Digital Products',
      'Community Support',
      'Service'
    ]
  });
});

app.use('/intake', intakeRoutes);

app.listen(PORT, () => {
  console.log(`Blessedly Stressed OS running on http://localhost:${PORT}`);
  console.log('Order of operations: Jesus first, always.');
});

module.exports = app;
