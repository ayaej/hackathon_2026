export class CleanZoneService {
    private cleanTexts: string[] = [];

    saveCleanText(cleanText: string): void {
        this.cleanTexts.push(cleanText);
    }

    getCleanTexts(): string[] {
        return this.cleanTexts;
    }
}