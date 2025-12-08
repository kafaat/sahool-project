const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');

const app = express();
const PORT = process.env.PORT || 3005;

// Middleware
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'alerts-service',
    version: '5.5.0',
    timestamp: new Date().toISOString()
  });
});

// Get active alerts
app.get('/active', async (req, res) => {
  try {
    const { tenantId } = req.query;
    res.json({
      success: true,
      data: [],
      message: 'Active alerts retrieved successfully'
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Mark alert as read
app.patch('/:id/read', async (req, res) => {
  try {
    const { id } = req.params;
    res.json({
      success: true,
      data: { id, isRead: true },
      message: 'Alert marked as read'
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// API Info
app.get('/', (req, res) => {
  res.json({
    service: 'alerts-service',
    version: '5.5.0',
    description: 'Alerts and notifications service',
    endpoints: [
      'GET /health',
      'GET /active',
      'PATCH /:id/read'
    ]
  });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`alerts-service running on port ${PORT}`);
});
