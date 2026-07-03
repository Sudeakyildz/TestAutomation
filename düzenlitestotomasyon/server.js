const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const PORT = 3050;

const clients = new Set();
let activeProcess = null;
let testRunning = false;
let logBuffer = '';

// Helper to broadcast SSE events to all connected clients
function broadcast(event, data) {
  const message = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
  for (const client of clients) {
    try {
      client.write(message);
    } catch (e) {
      clients.delete(client);
    }
  }
}

// Helper to parse docstring from a python file to use as description
function getTestDescription(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const match = content.match(/\"\"\"([\s\S]*?)\"\"\"/);
    if (match && match[1]) {
      return match[1].trim().split('\n')[0].trim();
    }
  } catch (e) {}
  return 'No description available.';
}

// Serve static file helper
function serveStaticFile(res, filePath, contentType) {
  fs.readFile(filePath, (err, content) => {
    if (err) {
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end('500 Server Error');
      return;
    }
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(content);
  });
}

const server = http.createServer((req, res) => {
  // CORS configuration
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // 1. Root / index.html
  if (req.url === '/' || req.url === '/index.html') {
    serveStaticFile(res, path.join(__dirname, 'index.html'), 'text/html');
    return;
  }

  // 2. Fetch list of tests
  if (req.url === '/api/tests' && req.method === 'GET') {
  // Global execution checks
  try {
    const testsDir = path.join(__dirname, 'tests');
    if (fs.existsSync(testsDir)) {
      // Check if pytest is installed and available via python -m
      const pytest = spawn('python', ['-m', 'pytest', '--version']);
      pytest.on('error', (err) => {
        console.error('python or pytest is not installed or not in PATH:', err);
      });
    }
  } catch (e) {}
    try {
      const testsDir = path.join(__dirname, 'tests');
      const files = fs.readdirSync(testsDir);
      const testFiles = files
        .filter(f => /^test_[1-8]_/.test(f) && f.endsWith('.py'))
        .map(f => {
          const fullPath = path.join(testsDir, f);
          return {
            filename: f,
            name: f.replace(/^test_\d+_/, '').replace('.py', '').replace(/_/g, ' ').toUpperCase(),
            description: getTestDescription(fullPath)
          };
        })
        .sort((a, b) => {
          const numA = parseInt(a.filename.split('_')[1]);
          const numB = parseInt(b.filename.split('_')[1]);
          return numA - numB;
        });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(testFiles));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return;
  }

  // 3. Read environment variables
  if (req.url === '/api/env' && req.method === 'GET') {
    try {
      const envPath = path.join(__dirname, '.env');
      let content = '';
      if (fs.existsSync(envPath)) {
        content = fs.readFileSync(envPath, 'utf8');
      }
      const envVars = {};
      const lines = content.split(/\r?\n/);
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        const eqIdx = trimmed.indexOf('=');
        if (eqIdx > 0) {
          const key = trimmed.slice(0, eqIdx).trim();
          const val = trimmed.slice(eqIdx + 1).trim();
          envVars[key] = val;
        }
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(envVars));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return;
  }

  // 4. Save environment variables
  if (req.url === '/api/env' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk.toString(); });
    req.on('end', () => {
      try {
        const newVars = JSON.parse(body || '{}');
        const envPath = path.join(__dirname, '.env');
        let output = '# Gitsec Python Test Automation Environment Variables\n';
        for (const [key, val] of Object.entries(newVars)) {
          if (key && val !== undefined) {
            output += `${key}=${val}\n`;
            process.env[key] = val;
          }
        }
        fs.writeFileSync(envPath, output, 'utf8');
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, message: '.env updated successfully.' }));
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  // 5. SSE Logs stream
  if (req.url === '/api/logs') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    });
    clients.add(res);
    // Send current status and backlog of logs
    res.write(`event: status\ndata: ${JSON.stringify({ running: testRunning })}\n\n`);
    if (logBuffer) {
      res.write(`event: log\ndata: ${JSON.stringify(logBuffer)}\n\n`);
    }
    req.on('close', () => {
      clients.delete(res);
    });
    return;
  }

  // 6. Run E2E Test(s)
  if (req.url === '/api/run' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk.toString(); });
    req.on('end', () => {
      try {
        const { testFile, headed } = JSON.parse(body || '{}');

        if (testRunning) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'A test is already running!' }));
          return;
        }

        testRunning = true;
        logBuffer = '';
        broadcast('status', { running: true });

        // Build command arguments
        const args = [];
        if (testFile) {
          args.push(`tests/${testFile}`);
        } else {
          args.push('tests/');
        }

        if (!headed) {
          args.push('--headless');
        }
        args.push('-s'); // capture stdout

        // Set environment variables
        const runEnv = { ...process.env, FORCE_COLOR: '1' };
        if (headed) {
          runEnv.HEADLESS = 'false';
        } else {
          runEnv.HEADLESS = 'true';
        }

        const runCmd = `python -m pytest ${args.join(' ')}`;
        console.log(`[Dashboard Server] Starting command: ${runCmd}`);
        broadcast('log', `[DASHBOARD] Starting: ${runCmd}\n\n`);
        logBuffer += `[DASHBOARD] Starting: ${runCmd}\n\n`;

        activeProcess = spawn('python', ['-m', 'pytest'].concat(args), {
          shell: true,
          cwd: __dirname,
          env: runEnv
        });

        activeProcess.stdout.on('data', data => {
          const chunk = data.toString();
          logBuffer += chunk;
          broadcast('log', chunk);
        });

        activeProcess.stderr.on('data', data => {
          const chunk = data.toString();
          logBuffer += chunk;
          broadcast('log', chunk);
        });

        activeProcess.on('close', code => {
          console.log(`[Dashboard Server] Pytest finished with code: ${code}`);
          testRunning = false;
          activeProcess = null;
          broadcast('status', { running: false });
          broadcast('done', { success: code === 0, code, testFile });
        });

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, message: 'Test started.' }));
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  // 7. Stop Test
  if (req.url === '/api/stop' && req.method === 'POST') {
    if (activeProcess) {
      console.log(`[Dashboard Server] Terminating pytest process: ${activeProcess.pid}`);
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', activeProcess.pid, '/f', '/t']);
      } else {
        activeProcess.kill('SIGINT');
      }
      broadcast('log', '\n\n[DASHBOARD] Test execution cancelled by user.\n');
      logBuffer += '\n\n[DASHBOARD] Test execution cancelled by user.\n';
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, message: 'Test stopped.' }));
    } else {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'No active test running.' }));
    }
    return;
  }

  // 404 handler
  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('404 Not Found');
});

server.listen(PORT, () => {
  console.log(`========================================================`);
  console.log(`[DASHBOARD] Server is running at http://localhost:${PORT}`);
  console.log(`========================================================`);
});
