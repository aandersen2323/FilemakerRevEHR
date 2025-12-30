#!/usr/bin/env node
/**
 * FileMaker Export Cleanup Script
 *
 * - Removes sparse/empty rows from FileMaker exports (portal data bloat)
 * - Optionally adds column headers to headerless CSV exports
 * - Supports multiple table types: patients, transactions
 *
 * Usage:
 *   node scripts/cleanup_export.js input.csv output.csv
 *   node scripts/cleanup_export.js input.csv output.csv --add-headers
 *   node scripts/cleanup_export.js input.csv output.csv --add-headers --type=transactions
 *   node scripts/cleanup_export.js input.csv  (creates input_clean.csv)
 */

const fs = require('fs');
const path = require('path');

// Minimum non-empty fields to consider a "real" record
const MIN_FIELDS = 5;

// Column headers for Patients export (14 columns)
// Matches FileMaker "patient export1" layout field order
const PATIENT_HEADERS = [
    'Patient_ID',         // 0 - PRIMARY KEY
    'First_Name',         // 1
    'Last_Name',          // 2
    'Birth_Date',         // 3
    'Gender',             // 4
    'Cell_Phone',         // 5
    'Home_Phone',         // 6
    'Work_Phone',         // 7
    'Email',              // 8
    'Street_Address',     // 9
    'City',               // 10
    'State',              // 11
    'Zip',                // 12
    'Doc_Seen',           // 13
];

// Column headers for Transactions export (40 columns)
// Matches actual FileMaker Transactions export layout
const TRANSACTION_HEADERS = [
    // Core Identity (3)
    'Transaction_Num',    // 0 - PRIMARY KEY
    'Patient_ID',         // 1 - FOREIGN KEY to Patients
    'Transaction_Date',   // 2

    // Provider & Visit (4)
    'Doctor',             // 3
    'Exam_Proc',          // 4
    'CL_Fitting_Proc',    // 5
    'Expiration_Date',    // 6

    // Contact Lens OD - Primary (8)
    'Contact_Lenses_OD',  // 7
    'Base_Curve_OD',      // 8
    'Diameter_OD',        // 9
    'CL_Sph_OD',          // 10
    'CL_Cyl_OD',          // 11
    'CL_Axis_OD',         // 12
    'CL_Add_OD',          // 13
    'Quant_CL_OD',        // 14

    // Contact Lens OS - Primary (8)
    'Contact_Lenses_OS',  // 15
    'Base_Curve_OS',      // 16
    'Diameter_OS',        // 17
    'CL_Sph_OS',          // 18
    'CL_Cyl_OS',          // 19
    'CL_Axis_OS',         // 20
    'CL_Add_OS',          // 21
    'Quant_CL_OS',        // 22

    // Contact Lens OD - Secondary (8)
    'Contact_Lenses_OD1', // 23
    'Base_Curve_OD1',     // 24
    'Diameter_OD1',       // 25
    'CL_Sph_OD1',         // 26
    'CL_Cyl_OD1',         // 27
    'CL_Axis_OD1',        // 28
    'CL_Add_OD1',         // 29
    'Quant_CL_OD1',       // 30

    // Contact Lens OD - Secondary (8)
    'Contact_Lenses_OS1', // 31
    'Base_Curve_OS1',     // 32
    'Diameter_OS1',       // 33
    'CL_Sph_OS1',         // 34
    'CL_Cyl_OS1',         // 35
    'CL_Axis_OS1',        // 36
    'CL_Add_OS1',         // 37
    'Quant_CL_OS1',       // 38

    // Notes & Extra (2)
    'Notes',              // 39
    'Extra_Field',        // 40 - placeholder for extra column in export
];

// Map of table types to their headers
const TABLE_HEADERS = {
    'patients': PATIENT_HEADERS,
    'transactions': TRANSACTION_HEADERS,
};

function detectTableType(colCount) {
    // Try to detect based on column count
    for (const [tableName, headers] of Object.entries(TABLE_HEADERS)) {
        if (colCount === headers.length) {
            return tableName;
        }
    }
    return null;
}

function cleanupExport(inputPath, outputPath, addHeaders = false, tableType = null) {
    console.log(`Reading: ${inputPath}`);

    const data = fs.readFileSync(inputPath, 'utf8');
    const lines = data.split('\n');

    console.log(`Total lines: ${lines.length}`);

    // Filter to only lines with significant data
    const significantLines = lines.filter(line => {
        const fields = line.split(',');
        const nonEmptyCount = fields.filter(f =>
            f && f !== '""' && f.trim() !== ''
        ).length;
        return nonEmptyCount >= MIN_FIELDS;
    });

    console.log(`Records with data: ${significantLines.length}`);
    console.log(`Removed ${lines.length - significantLines.length} sparse/empty lines`);

    // Build output
    let output = '';

    // Add headers if requested
    if (addHeaders) {
        const firstLine = significantLines[0] || '';
        const colCount = firstLine.split(',').length;

        let headers;
        let detectedType = tableType;

        // If no type specified, try to detect
        if (!detectedType) {
            detectedType = detectTableType(colCount);
        }

        if (detectedType && TABLE_HEADERS[detectedType]) {
            headers = TABLE_HEADERS[detectedType];
            if (colCount !== headers.length) {
                console.log(`\nWarning: Found ${colCount} columns, but ${detectedType} expects ${headers.length}`);
                console.log('Using generic column headers instead.');
                headers = Array.from({length: colCount}, (_, i) => `Column_${i}`);
            } else {
                console.log(`\nDetected table type: ${detectedType}`);
            }
        } else {
            headers = Array.from({length: colCount}, (_, i) => `Column_${i}`);
            console.log(`\nNote: Found ${colCount} columns, no matching table type.`);
            console.log('Using generic column headers.');
            console.log(`Known types: ${Object.keys(TABLE_HEADERS).join(', ')}`);
        }

        output = headers.join(',') + '\n';
        console.log(`Added ${headers.length} column headers`);
    }

    output += significantLines.join('\n');

    // Write cleaned file
    fs.writeFileSync(outputPath, output, 'utf8');

    const originalSize = fs.statSync(inputPath).size;
    const newSize = fs.statSync(outputPath).size;
    const reduction = ((1 - newSize/originalSize) * 100).toFixed(1);

    if (reduction > 1) {
        console.log(`\nFile size: ${(originalSize/1024/1024).toFixed(2)}MB -> ${(newSize/1024).toFixed(2)}KB`);
        console.log(`Reduction: ${reduction}%`);
    } else {
        console.log(`\nFile size: ${(originalSize/1024/1024).toFixed(2)}MB`);
    }
    console.log(`Saved to: ${outputPath}`);
}

// Main
const args = process.argv.slice(2);

// Check for flags
const addHeadersFlag = args.includes('--add-headers');

// Check for --type=XXX flag
let tableType = null;
const typeArg = args.find(a => a.startsWith('--type='));
if (typeArg) {
    tableType = typeArg.split('=')[1].toLowerCase();
    if (!TABLE_HEADERS[tableType]) {
        console.error(`Unknown table type: ${tableType}`);
        console.error(`Known types: ${Object.keys(TABLE_HEADERS).join(', ')}`);
        process.exit(1);
    }
}

const fileArgs = args.filter(a => !a.startsWith('--'));

if (fileArgs.length < 1) {
    console.log('FileMaker Export Cleanup Script');
    console.log('');
    console.log('Usage: node cleanup_export.js <input.csv> [output.csv] [options]');
    console.log('');
    console.log('Options:');
    console.log('  --add-headers       Add column headers to output CSV');
    console.log('  --type=<type>       Specify table type for headers');
    console.log('');
    console.log('Supported table types:');
    for (const [name, headers] of Object.entries(TABLE_HEADERS)) {
        console.log(`  ${name.padEnd(15)} (${headers.length} columns)`);
    }
    console.log('');
    console.log('Examples:');
    console.log('  node cleanup_export.js patients.csv patients_clean.csv --add-headers');
    console.log('  node cleanup_export.js transactions.csv tx_clean.csv --add-headers --type=transactions');
    console.log('');
    console.log('If output not specified, creates input_clean.csv');
    process.exit(1);
}

const inputPath = fileArgs[0];
const outputPath = fileArgs[1] || inputPath.replace('.csv', '_clean.csv');

if (!fs.existsSync(inputPath)) {
    console.error(`File not found: ${inputPath}`);
    process.exit(1);
}

cleanupExport(inputPath, outputPath, addHeadersFlag, tableType);
