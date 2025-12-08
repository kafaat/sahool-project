const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');

const app = express();
const PORT = process.env.PORT || 3003;

// Middleware
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'imagery-service',
    version: '5.5.0',
    timestamp: new Date().toISOString()
  });
});

// Get NDVI timeline
app.get('/ndvi/:fieldId/timeline', async (req, res) => {
  try {
    const { fieldId } = req.params;
    res.json({
      success: true,
      data: [],
      message: 'NDVI timeline retrieved successfully'
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Get latest NDVI
app.get('/ndvi/:fieldId/latest', async (req, res) => {
  try {
    const { fieldId } = req.params;
    res.json({
      success: true,
      data: {
        fieldId,
        value: 0.75,
        date: new Date().toISOString(),
        satellite: 'Sentinel-2'
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// API Info
app.get('/', (req, res) => {
  res.json({
    service: 'imagery-service',
    version: '5.5.0',
    description: 'Satellite imagery processing service',
    endpoints: [
      'GET /health',
      'GET /ndvi/:fieldId/timeline',
      'GET /ndvi/:fieldId/latest'
    ]
  });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`imagery-service running on port ${PORT}`);
});
