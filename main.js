const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const SettingsManager = require('./settings_manager');

const settingsManager = new SettingsManager();
const fs = require('fs');

let mainWindow;
let currentProcess = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    backgroundColor: '#1e1e1e',
    titleBarStyle: 'default'
  });

  mainWindow.loadFile('index.html');
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

ipcMain.handle('select-input-folder', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });
  
  if (!result.canceled && result.filePaths.length > 0) {
    const folderPath = result.filePaths[0];
    const videoExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v'];
    
    const files = fs.readdirSync(folderPath);
    const videoFiles = files.filter(file => {
      const ext = path.extname(file).toLowerCase();
      return videoExtensions.includes(ext);
    }).map(file => path.join(folderPath, file));
    
    return {
      folderPath,
      videoFiles
    };
  }
  
  return null;
});

ipcMain.handle('select-output-folder', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory', 'createDirectory']
  });
  
  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths[0];
  }
  
  return null;
});

ipcMain.handle('process-videos', async (event, { videoFiles, outputFolder, model, llm, format }) => {
  return new Promise((resolve, reject) => {
    const pythonScript = path.join(__dirname, 'batch_processor.py');
    const pythonPath = path.join(__dirname, 'venv', 'bin', 'python3');
    
    // Get MP3 bitrate from settings
    const mp3Bitrate = settingsManager.getSetting('MP3_BITRATE') || '128k';
    
    const args = [
      pythonScript,
      '--videos', JSON.stringify(videoFiles),
      '--output', outputFolder,
      '--model', model || 'medium',
      '--format', format || 'txt',
      '--mp3-bitrate', mp3Bitrate
    ];
    
    if (llm && llm.enabled) {
      args.push('--llm-config', JSON.stringify(llm));
    }
    
    // Send initial message to confirm process is starting
    mainWindow.webContents.send('processing-update', `Starting Python process...\nCommand: ${pythonPath}\nScript: ${pythonScript}\n`);
    
    const pythonProcess = spawn(pythonPath, args, {
      env: { ...process.env, PYTHONUNBUFFERED: '1' }  // Disable Python output buffering
    });
    currentProcess = pythonProcess;
    let stopped = false;
    
    pythonProcess.on('error', (err) => {
      mainWindow.webContents.send('processing-error', `Failed to start Python process: ${err.message}\n`);
      reject({ success: false, error: err.message });
    });
    
    pythonProcess.stdout.on('data', (data) => {
      const message = data.toString();
      mainWindow.webContents.send('processing-update', message);
    });
    
    pythonProcess.stderr.on('data', (data) => {
      const error = data.toString();
      mainWindow.webContents.send('processing-error', error);
    });
    
    pythonProcess.on('close', (code) => {
      currentProcess = null;
      mainWindow.webContents.send('processing-update', `\nPython process exited with code: ${code}\n`);
      if (stopped) {
        resolve({ success: true, stopped: true });
      } else if (code === 0) {
        resolve({ success: true, stopped: false });
      } else {
        reject({ success: false, code });
      }
    });
    
    // Handle stop signal
    pythonProcess.on('SIGTERM', () => {
      stopped = true;
    });
  });
});

ipcMain.handle('stop-processing', async () => {
  if (currentProcess) {
    currentProcess.kill('SIGTERM');
    return { success: true };
  }
  return { success: false };
});

ipcMain.handle('verify-model', async (event, model) => {
  return new Promise((resolve, reject) => {
    const pythonScript = path.join(__dirname, 'verify_model.py');
    const pythonPath = path.join(__dirname, 'venv', 'bin', 'python3');
    
    const args = [pythonScript, '--model', model];
    const pythonProcess = spawn(pythonPath, args);
    
    let output = '';
    let errorOutput = '';
    
    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
      try {
        const result = JSON.parse(output);
        resolve(result);
      } catch (e) {
        reject({ error: 'Failed to parse verification result', details: output + errorOutput });
      }
    });
  });
});

ipcMain.handle('download-model', async (event, model) => {
  return new Promise((resolve, reject) => {
    const pythonScript = path.join(__dirname, 'download_model.py');
    const pythonPath = path.join(__dirname, 'venv', 'bin', 'python3');
    
    const args = [pythonScript, '--model', model];
    const pythonProcess = spawn(pythonPath, args);
    
    let output = '';
    let errorOutput = '';
    let jsonResult = '';
    
    pythonProcess.stdout.on('data', (data) => {
      const message = data.toString();
      output += message;
      
      // Stream progress to terminal in real-time
      mainWindow.webContents.send('processing-update', message);
      
      // Try to extract JSON result (last line)
      const lines = output.trim().split('\n');
      const lastLine = lines[lines.length - 1];
      if (lastLine.startsWith('{')) {
        jsonResult = lastLine;
      }
    });
    
    pythonProcess.stderr.on('data', (data) => {
      const error = data.toString();
      errorOutput += error;
      mainWindow.webContents.send('processing-error', error);
    });
    
    pythonProcess.on('close', (code) => {
      try {
        if (jsonResult) {
          const result = JSON.parse(jsonResult);
          resolve(result);
        } else {
          reject({ error: 'No result from download', details: output + errorOutput });
        }
      } catch (e) {
        reject({ error: 'Failed to parse download result', details: output + errorOutput });
      }
    });
  });
});

ipcMain.handle('search-transcripts', async (event, { action, query, outputFolder, caseSensitive, llmConfig }) => {
  return new Promise((resolve, reject) => {
    const pythonScript = path.join(__dirname, 'search_handler.py');
    const pythonPath = path.join(__dirname, 'venv', 'bin', 'python3');
    
    const args = [
      pythonScript,
      '--action', action,
      '--output-folder', outputFolder
    ];
    
    if (query) {
      args.push('--query', query);
    }
    
    if (caseSensitive) {
      args.push('--case-sensitive');
    }
    
    if (llmConfig) {
      args.push('--llm-config', JSON.stringify(llmConfig));
    }
    
    const pythonProcess = spawn(pythonPath, args);
    let output = '';
    let errorOutput = '';
    
    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(output);
          resolve(result);
        } catch (e) {
          reject({ error: 'Failed to parse search results', details: output });
        }
      } else {
        reject({ error: 'Search failed', details: errorOutput });
      }
    });
  });
});

// Settings IPC handlers
ipcMain.handle('load-settings', async () => {
  return settingsManager.getSettings();
});

ipcMain.handle('save-settings', async (event, settings) => {
  try {
    settingsManager.saveSettings(settings);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});
