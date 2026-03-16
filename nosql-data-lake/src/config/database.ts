import { MongoClient } from 'mongodb';

const uri = process.env.MONGODB_URI || 'your-default-mongodb-uri';
const options = {
  useNewUrlParser: true,
  useUnifiedTopology: true,
};

let client: MongoClient;

export const connectToDatabase = async () => {
  if (!client) {
    client = new MongoClient(uri, options);
    try {
      await client.connect();
      console.log('Connected to the database');
    } catch (error) {
      console.error('Database connection error:', error);
      throw error;
    }
  }
  return client.db('your-database-name');
};

export const closeDatabaseConnection = async () => {
  if (client) {
    await client.close();
    console.log('Database connection closed');
  }
};