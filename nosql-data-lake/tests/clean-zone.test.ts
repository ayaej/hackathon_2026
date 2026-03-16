import { CleanZoneService } from '../src/services/clean-zone';

describe('CleanZoneService', () => {
    let cleanZoneService: CleanZoneService;

    beforeEach(() => {
        cleanZoneService = new CleanZoneService();
    });

    test('should save clean text', async () => {
        const cleanText = 'This is a clean text.';
        const result = await cleanZoneService.saveCleanText(cleanText);
        expect(result).toBeTruthy();
    });

    test('should retrieve clean texts', async () => {
        const cleanTexts = await cleanZoneService.getCleanTexts();
        expect(Array.isArray(cleanTexts)).toBe(true);
    });
});