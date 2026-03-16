export function transformToCleanData(rawData: any): any {
    // Implement transformation logic from raw data to clean data
    const cleanData = {
        // Example transformation
        id: rawData.id,
        cleanText: rawData.text.trim(),
        // Add more fields as necessary
    };
    return cleanData;
}

export function transformToCuratedData(cleanData: any): any {
    // Implement transformation logic from clean data to curated data
    const curatedData = {
        // Example transformation
        id: cleanData.id,
        structuredData: {
            // Structure the data as needed
            content: cleanData.cleanText,
            // Add more fields as necessary
        },
    };
    return curatedData;
}