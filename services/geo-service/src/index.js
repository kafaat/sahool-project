const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'geo-service',
    version: '5.5.0',
    timestamp: new Date().toISOString()
  });
});

// Get all fields
app.get('/fields', async (req, res) => {
  try {
    const { tenantId } = req.query;
    // TODO: Implement database query
    res.json({
      success: true,
      data: [],
      message: 'Fields retrieved successfully'
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Get field by ID
app.get('/fields/:id', async (req, res) => {
  try {
    const { id } = req.params;
    // TODO: Implement database query
    res.json({
      success: true,
      data: null,
      message: 'Field retrieved successfully'
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Get equipment location
app.get('/equipment/:id/location', async (req, res) => {
  try {
    const { id } = req.params;
    res.json({
      success: true,
      data: {
        id,
        location: { latitude: 24.7136, longitude: 46.6753 },
        lastUpdate: new Date().toISOString()
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// API Info
app.get('/', (req, res) => {
  res.json({
    service: 'geo-service',
    version: '5.5.0',
    description: 'Geographic data and field management service',
    endpoints: [
      'GET /health',
      'GET /fields',
      'GET /fields/:id',
      'GET /equipment/:id/location'
    ]
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`geo-service running on port ${PORT}`);
});
