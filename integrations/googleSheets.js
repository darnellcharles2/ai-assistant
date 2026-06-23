const SPREADSHEET_ID = process.env.GOOGLE_SHEETS_SPREADSHEET_ID || null;

function isConfigured() {
  return Boolean(SPREADSHEET_ID);
}

async function appendRow(sheetName, rowData) {
  if (!isConfigured()) {
    return {
      success: false,
      error: 'Google Sheets is not configured. Set GOOGLE_SHEETS_SPREADSHEET_ID in .env'
    };
  }

  // Stub: In production, use Google Sheets API to append
  console.log(`[Google Sheets Stub] Would append row to "${sheetName}" in spreadsheet ${SPREADSHEET_ID}`);
  console.log('[Google Sheets Stub] Row data:', JSON.stringify(rowData));
  return {
    success: true,
    stub: true,
    sheetName,
    spreadsheetId: SPREADSHEET_ID,
    message: 'Row append is a stub. Integrate with Google Sheets API for real writes.'
  };
}

async function readSheet(sheetName, range) {
  if (!isConfigured()) {
    return { success: false, error: 'Google Sheets is not configured.' };
  }

  // Stub
  console.log(`[Google Sheets Stub] Would read "${range}" from "${sheetName}"`);
  return {
    success: true,
    stub: true,
    data: [],
    message: 'Sheet read is a stub. Integrate with Google Sheets API for real reads.'
  };
}

module.exports = { isConfigured, appendRow, readSheet };
