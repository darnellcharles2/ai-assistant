const FOLDER_ID = process.env.GOOGLE_DRIVE_FOLDER_ID || null;

function isConfigured() {
  return Boolean(FOLDER_ID);
}

async function uploadFile(fileName, content, mimeType) {
  if (!isConfigured()) {
    return {
      success: false,
      error: 'Google Drive is not configured. Set GOOGLE_DRIVE_FOLDER_ID in .env'
    };
  }

  // Stub: In production, use Google Drive API to upload
  console.log(`[Google Drive Stub] Would upload "${fileName}" (${mimeType}) to folder ${FOLDER_ID}`);
  return {
    success: true,
    stub: true,
    fileName,
    mimeType,
    folderId: FOLDER_ID,
    message: 'File upload is a stub. Integrate with Google Drive API for real uploads.'
  };
}

async function listFiles() {
  if (!isConfigured()) {
    return { success: false, error: 'Google Drive is not configured.' };
  }

  // Stub
  console.log('[Google Drive Stub] Would list files in folder', FOLDER_ID);
  return {
    success: true,
    stub: true,
    files: [],
    message: 'File listing is a stub. Integrate with Google Drive API for real listings.'
  };
}

module.exports = { isConfigured, uploadFile, listFiles };
