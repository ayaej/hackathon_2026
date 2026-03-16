import express from 'express';
import { connectToDatabase } from './config/database';
import { RawZoneService } from './services/raw-zone';
import { CleanZoneService } from './services/clean-zone';
import { CuratedZoneService } from './services/curated-zone';

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

connectToDatabase()
  .then(() => {
    console.log('Database connected successfully');

    const rawZoneService = new RawZoneService();
    const cleanZoneService = new CleanZoneService();
    const curatedZoneService = new CuratedZoneService();

    // Define routes here
    // Example: app.post('/raw', (req, res) => rawZoneService.uploadDocument(req.body));

    app.listen(PORT, () => {
      console.log(`Server is running on port ${PORT}`);
    });
  })
  .catch((error) => {
    console.error('Database connection error:', error);
  });