class RawZoneService {
    constructor(database) {
        this.database = database;
    }

    async uploadDocument(document) {
        try {
            const result = await this.database.collection('raw_documents').insertOne(document);
            return result.insertedId;
        } catch (error) {
            throw new Error('Error uploading document: ' + error.message);
        }
    }

    async getRawDocuments() {
        try {
            const documents = await this.database.collection('raw_documents').find().toArray();
            return documents;
        } catch (error) {
            throw new Error('Error retrieving raw documents: ' + error.message);
        }
    }
}

export default RawZoneService;