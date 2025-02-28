const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process')
const path = require('path');

function runPythonScript() {
    //const pythonProcess = spawn("/usr/local/bin/python3.10", ["scraper.py"]);
    const pythonProcess = spawn("./scraper.bin")

    pythonProcess.stdout.on("data", (data) => {
        console.log(`Output from Python: ${data.toString()}`);
    });

    pythonProcess.stderr.on("data", (data) => {
        console.error(`Error from Python: ${data.toString()}`);
    });

    pythonProcess.on("close", (code) => {
        console.log(`Python script exited with code ${code}`);
    });
}

function createWindow() {
  // Create a new browser window
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,  // Allow renderer process to use Node.js
    },
  });

  // Load the HTML file
  win.loadFile('index.html');

  runPythonScript();
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
