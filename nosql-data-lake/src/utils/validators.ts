export function validateSIRET(siret: string): boolean {
    const siretRegex = /^\d{14}$/;
    return siretRegex.test(siret);
}

export function validateDate(dateString: string): boolean {
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    return dateRegex.test(dateString);
}