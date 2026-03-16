import { CuratedZoneService } from '../src/services/curated-zone';

describe('CuratedZoneService', () => {
    let curatedZoneService: CuratedZoneService;

    beforeEach(() => {
        curatedZoneService = new CuratedZoneService();
    });

    test('should save curated data', async () => {
        const data = { id: '1', name: 'Test Document', curatedData: { key: 'value' } };
        await curatedZoneService.saveCuratedData(data);
        const result = await curatedZoneService.getCuratedData(data.id);
        expect(result).toEqual(data);
    });

    test('should retrieve curated data', async () => {
        const data = { id: '2', name: 'Another Document', curatedData: { key: 'anotherValue' } };
        await curatedZoneService.saveCuratedData(data);
        const result = await curatedZoneService.getCuratedData(data.id);
        expect(result).toEqual(data);
    });

    test('should return null for non-existent curated data', async () => {
        const result = await curatedZoneService.getCuratedData('non-existent-id');
        expect(result).toBeNull();
    });
});