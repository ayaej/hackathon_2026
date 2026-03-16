# NoSQL Data Lake Project

## Overview
This project implements a NoSQL database or Data Lake that structures data into three distinct zones: Raw, Clean, and Curated. The architecture is designed to efficiently store and manage documents, allowing for seamless data processing and retrieval.

## Project Structure
The project is organized into the following directories and files:

- **src/**: Contains the source code for the application.
  - **index.ts**: Entry point of the application.
  - **config/**: Configuration settings for the database connection.
    - **database.ts**: Database connection setup.
  - **services/**: Contains services for handling different data zones.
    - **raw-zone.ts**: Service for managing raw documents.
    - **clean-zone.ts**: Service for managing cleaned text data.
    - **curated-zone.ts**: Service for managing structured data.
  - **models/**: Defines the data models used in the application.
    - **document.ts**: Document model structure.
  - **utils/**: Utility functions for data validation and transformation.
    - **validators.ts**: Functions for validating document data.
    - **transformers.ts**: Functions for transforming raw data.
  - **types/**: TypeScript interfaces for data structures.
    - **index.ts**: Interfaces for various data types.

- **tests/**: Contains unit tests for the services.
  - **raw-zone.test.ts**: Tests for the RawZoneService.
  - **clean-zone.test.ts**: Tests for the CleanZoneService.
  - **curated-zone.test.ts**: Tests for the CuratedZoneService.

- **package.json**: Configuration file for npm, listing dependencies and scripts.
- **tsconfig.json**: TypeScript configuration file specifying compiler options.
- **README.md**: Documentation for the project.

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd nosql-data-lake
   ```
3. Install the dependencies:
   ```
   npm install
   ```
4. Configure the database connection in `src/config/database.ts`.
5. Start the application:
   ```
   npm start
   ```

## Features
- Supports storing raw documents, cleaned text data, and structured data.
- Provides utility functions for data validation and transformation.
- Includes unit tests for ensuring the reliability of services.

## Usage
- Use the `RawZoneService` to upload and retrieve raw documents.
- Use the `CleanZoneService` to save and get cleaned text data.
- Use the `CuratedZoneService` to save and retrieve structured data.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.