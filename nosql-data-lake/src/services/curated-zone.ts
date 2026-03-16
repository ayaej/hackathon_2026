class CuratedZoneService {
    constructor(database) {
        this.database = database;
    }

    async saveCuratedData(documentId, curatedData) {
        try {
            const result = await this.database.collection('curatedZone').insertOne({
                documentId,
                curatedData,
                createdAt: new Date(),
            });
            return result.insertedId;
        } catch (error) {
            throw new Error('Error saving curated data: ' + error.message);
        }
    }

    async getCuratedData(documentId) {
        try {
            const result = await this.database.collection('curatedZone').findOne({ documentId });
            return result ? result.curatedData : null;
        } catch (error) {
            throw new Error('Error retrieving curated data: ' + error.message);
        }
    }
}

export default CuratedZoneService;