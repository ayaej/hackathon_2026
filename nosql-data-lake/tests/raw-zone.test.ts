import { RawZoneService } from '../src/services/raw-zone';

describe('RawZoneService', () => {
    let rawZoneService: RawZoneService;

    beforeEach(() => {
        rawZoneService = new RawZoneService();
    });

    test('should upload a document', async () => {
        const document = { id: '1', type: 'test', rawData: 'Sample raw data' };
        const result = await rawZoneService.uploadDocument(document);
        expect(result).toBeTruthy();
    });

    test('should retrieve raw documents', async () => {
        const documents = await rawZoneService.getRawDocuments();
        expect(Array.isArray(documents)).toBe(true);
    });
});