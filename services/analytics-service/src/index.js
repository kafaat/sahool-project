const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');

const app = express();
const PORT = process.env.PORT || 3006;

// Middleware
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'analytics-service',
    version: '5.5.0',
    timestamp: new Date().toISOString()
  });
});

// Track event
app.post('/events', async (req, res) => {
  try {
    const { eventType, eventName, properties } = req.body;
    res.json({
      success: true,
      message: 'Event tracked successfully'
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Get analytics summary
app.get('/summary', async (req, res) => {
  try {
    const { tenantId, startDate, endDate } = req.query;
    res.json({
      success: true,
      data: {
        totalFields: 0,
        totalArea: 0,
        avgHealth: 0,
        alertsCount: 0
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// API Info
app.get('/', (req, res) => {
  res.json({
    service: 'analytics-service',
    version: '5.5.0',
    description: 'Analytics and reporting service',
    endpoints: [
      'GET /health',
      'POST /events',
      'GET /summary'
    ]
  });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`analytics-service running on port ${PORT}`);
});
