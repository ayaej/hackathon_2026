export interface Document {
    id: string;
    type: string;
    rawData: RawDocument;
    cleanData: CleanDocument;
    curatedData: CuratedDocument;
}

export interface RawDocument {
    id: string;
    content: string;
    createdAt: Date;
}

export interface CleanDocument {
    id: string;
    text: string;
    createdAt: Date;
}

export interface CuratedDocument {
    id: string;
    structuredData: Record<string, any>;
    createdAt: Date;
}