const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { diagnose, extractCurrentStep, TEST_META } = require('./utils/failure_diagnostics');

const PORT = 3050;
const REPORTS_DIR = path.join(__dirname, 'reports');
const LAST_RESULTS_PATH = path.join(REPORTS_DIR, 'lastResults.json');
const SENSITIVE_ENV_PATTERN = /password|secret|token|api_key|apikey/i;

const clients = new Set();
let activeProcess = null;
let testRunning = false;
let logBuffer = '';
let currentTestFile = null;
let lastResults = {};
let suiteState = { running: false, currentIndex: 0, total: 0 };

if (!fs.existsSync(REPORTS_DIR)) {
  fs.mkdirSync(REPORTS_DIR, { recursive: true });
}

function loadLastResults() {
  try {
    if (fs.existsSync(LAST_RESULTS_PATH)) {
      lastResults = JSON.parse(fs.readFileSync(LAST_RESULTS_PATH, 'utf8'));
    }
  } catch (e) {
    lastResults = {};
  }
}

function saveLastResults() {
  try {
    fs.writeFileSync(LAST_RESULTS_PATH, JSON.stringify(lastResults, null, 2), 'utf8');
  } catch (e) {
    console.warn('[Dashboard] lastResults kaydedilemedi:', e.message);
  }
}

function maskEnvValue(key, value) {
  if (SENSITIVE_ENV_PATTERN.test(key)) {
    return value ? '***' : '';
  }
  return value;
}

loadLastResults();

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

function getTestDescription(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const match = content.match(/\"\"\"([\s\S]*?)\"\"\"/);
    if (match && match[1]) {
      return match[1].trim().split('\n')[0].trim();
    }
  } catch (e) {}
  return 'Açıklama bulunamadı.';
}

function parseJunitFailure(junitPath) {
  try {
    if (!fs.existsSync(junitPath)) return null;
    const xml = fs.readFileSync(junitPath, 'utf8');
    const failureMatch = xml.match(/<failure[^>]*message="([^"]*)"[^>]*>([\s\S]*?)<\/failure>/);
    if (failureMatch) {
      const message = failureMatch[1] || failureMatch[2].trim().split('\n')[0];
      return { message };
    }
    const errorMatch = xml.match(/<error[^>]*message="([^"]*)"[^>]*>([\s\S]*?)<\/error>/);
    if (errorMatch) {
      return { message: errorMatch[1] || errorMatch[2].trim().split('\n')[0] };
    }
  } catch (e) {}
  return null;
}

function serveFile(res, filePath, contentType) {
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

function listTests() {
  const testsDir = path.join(__dirname, 'tests');
  const files = fs.readdirSync(testsDir);
  return files
    .filter(f => /^test_.*\.py$/.test(f))
    .map(f => {
      const fullPath = path.join(testsDir, f);
      const meta = TEST_META[f] || {};
      const last = lastResults[f] || null;
      return {
        filename: f,
        name: meta.label || f.replace(/^test_\d+_/, '').replace('.py', '').replace(/_/g, ' ').toUpperCase(),
        description: getTestDescription(fullPath),
        category: meta.category || 'E2E',
        phase: meta.phase || 'Diğer',
        phaseOrder: meta.phaseOrder ?? 99,
        gitsecArea: meta.gitsecArea || 'unknown',
        testNumber: parseInt(f.split('_')[1], 10),
        lastResult: last,
      };
    })
    .sort((a, b) => {
      const numA = parseInt(a.filename.split('_')[1]);
      const numB = parseInt(b.filename.split('_')[1]);
      return numA - numB;
    });
}

function finishTestRun(code, testFile) {
  const junitPath = path.join(REPORTS_DIR, testFile ? `junit_${testFile.replace('.py', '')}.xml` : 'junit_all.xml');
  const junitFailure = parseJunitFailure(junitPath);
  const result = diagnose(testFile || 'all_tests', code, logBuffer, junitFailure);

  if (testFile) {
    lastResults[testFile] = {
      ...result,
      finishedAt: new Date().toISOString(),
    };
  }

  saveLastResults();

  testRunning = false;
  activeProcess = null;
  currentTestFile = null;

  broadcast('status', {
    running: false,
    currentTestFile: null,
    currentStep: null,
    suite: suiteState,
  });

  broadcast('done', {
    success: code === 0,
    code,
    testFile,
    result,
  });

  broadcast('step', { step: null, testFile: null });
}

function startPytest(testFile, headed, markers) {
  testRunning = true;
  logBuffer = '';
  currentTestFile = testFile || null;

  const junitName = testFile
    ? `junit_${testFile.replace('.py', '')}.xml`
    : markers
      ? `junit_marker_${String(markers).replace(/[^a-z0-9_-]/gi, '_')}.xml`
      : 'junit_all.xml';
  const junitPath = path.join(REPORTS_DIR, junitName);

  const args = [];
  if (testFile) {
    args.push(`tests/${testFile}`);
  } else {
    args.push('tests/');
  }

  if (markers) {
    args.push('-m', markers);
  }

  if (!headed) {
    args.push('--headless');
  }

  args.push('-s', '--tb=short', `--junitxml=${junitPath}`);

  const runEnv = { ...process.env, FORCE_COLOR: '1', HEADLESS: headed ? 'false' : 'true' };
  const runCmd = `python -m pytest ${args.join(' ')}`;

  broadcast('status', {
    running: true,
    currentTestFile: testFile,
    currentStep: 'Test başlatılıyor...',
    suite: suiteState,
    headed,
  });

  broadcast('log', `[PANEL] Komut: ${runCmd}\n`);
  broadcast('log', headed
    ? '[PANEL] Canlı izleme modu: Tarayıcı penceresi açılacak.\n\n'
    : '[PANEL] Arka plan modu: Tarayıcı görünmez çalışacak.\n\n');
  if (markers) {
    broadcast('log', `[PANEL] Marker filtresi: -m ${markers}\n\n`);
    logBuffer += `[PANEL] Marker filtresi: -m ${markers}\n\n`;
  }

  logBuffer += `[PANEL] Komut: ${runCmd}\n\n`;

  activeProcess = spawn('python', ['-m', 'pytest'].concat(args), {
    shell: true,
    cwd: __dirname,
    env: runEnv,
  });

  activeProcess.stdout.on('data', data => {
    const chunk = data.toString();
    logBuffer += chunk;
    broadcast('log', chunk);

    const step = extractCurrentStep(logBuffer);
    if (step) {
      broadcast('step', { step, testFile: currentTestFile });
      broadcast('status', {
        running: true,
        currentTestFile: currentTestFile,
        currentStep: step,
        suite: suiteState,
      });
    }
  });

  activeProcess.stderr.on('data', data => {
    const chunk = data.toString();
    logBuffer += chunk;
    broadcast('log', chunk);
  });

  activeProcess.on('close', code => {
    console.log(`[Dashboard] Pytest bitti: code=${code}, file=${testFile || 'ALL'}`);
    finishTestRun(code, testFile);
  });
}

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.url === '/' || req.url === '/index.html') {
    fs.readFile(path.join(__dirname, 'index.html'), (err, content) => {
      if (err) {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('500 Server Error');
        return;
      }
      res.writeHead(200, {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
      });
      res.end(content);
    });
    return;
  }

  if (req.url === '/api/tests' && req.method === 'GET') {
    try {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(listTests()));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return;
  }

  if (req.url === '/api/results' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ results: lastResults }));
    return;
  }

  if (req.url === '/api/status' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      running: testRunning,
      currentTestFile,
      currentStep: extractCurrentStep(logBuffer),
      suite: suiteState,
    }));
    return;
  }

  if (req.url === '/api/env' && req.method === 'GET') {
    try {
      const envPath = path.join(__dirname, '.env');
      let content = '';
      if (fs.existsSync(envPath)) {
        content = fs.readFileSync(envPath, 'utf8');
      }
      const envVars = {};
      for (const line of content.split(/\r?\n/)) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        const eqIdx = trimmed.indexOf('=');
        if (eqIdx > 0) {
          const key = trimmed.slice(0, eqIdx).trim();
          const val = trimmed.slice(eqIdx + 1).trim();
          envVars[key] = maskEnvValue(key, val);
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
        res.end(JSON.stringify({ success: true, message: '.env güncellendi.' }));
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  if (req.url === '/api/logs') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    });
    clients.add(res);
    res.write(`event: status\ndata: ${JSON.stringify({
      running: testRunning,
      currentTestFile,
      currentStep: extractCurrentStep(logBuffer),
      suite: suiteState,
    })}\n\n`);
    if (logBuffer) {
      res.write(`event: log\ndata: ${JSON.stringify(logBuffer)}\n\n`);
    }
    req.on('close', () => clients.delete(res));
    return;
  }

  if (req.url === '/api/run' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk.toString(); });
    req.on('end', () => {
      try {
        const { testFile, headed, markers } = JSON.parse(body || '{}');

        if (testRunning) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Şu anda bir test zaten çalışıyor!' }));
          return;
        }

        startPytest(testFile || null, !!headed, markers || null);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          success: true,
          message: 'Test başlatıldı.',
          testFile: testFile || null,
          markers: markers || null,
        }));
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  if (req.url === '/api/stop' && req.method === 'POST') {
    suiteState = { running: false, currentIndex: 0, total: 0 };

    if (activeProcess) {
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', activeProcess.pid, '/f', '/t']);
      } else {
        activeProcess.kill('SIGINT');
      }
      broadcast('log', '\n\n[PANEL] Test çalışması kullanıcı tarafından iptal edildi.\n');
      logBuffer += '\n\n[PANEL] Test çalışması kullanıcı tarafından iptal edildi.\n';
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, message: 'Test durduruldu.' }));
    } else {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Aktif test bulunamadı.' }));
    }
    return;
  }

  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('404 Not Found');
});

server.listen(PORT, () => {
  console.log('========================================================');
  console.log(`[DASHBOARD] Panel çalışıyor: http://localhost:${PORT}`);
  console.log('========================================================');
});
