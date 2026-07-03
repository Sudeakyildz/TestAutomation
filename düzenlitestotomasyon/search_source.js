const fs = require('fs');
const path = require('path');

const sourcePath = path.join(__dirname, '..', 'latest_logs', 'düzenlitestotomasyon.tests.test_5_github_include_exclude.test_github_repositories_include_all_then_exclude_all', 'page_source.html');

if (!fs.existsSync(sourcePath)) {
  console.log('Page source file not found at:', sourcePath);
  process.exit(1);
}

const html = fs.readFileSync(sourcePath, 'utf8');

// Search for toasts, alerts, or dialogs
console.log('--- HTML Length:', html.length);

const keywords = ['fail', 'error', 'limit', 'threshold', 'licensed', 'toast', 'dialog', 'notification', 'hata', 'lisans', 'uyari'];
keywords.forEach(kw => {
  const regex = new RegExp(`.{0,100}${kw}.{0,100}`, 'gi');
  const matches = html.match(regex);
  if (matches) {
    console.log(`\nMatches for keyword "${kw}": (${matches.length} found)`);
    matches.slice(0, 5).forEach((m, i) => {
      console.log(`  ${i+1}: ${m.trim().replace(/\s+/g, ' ')}`);
    });
  } else {
    console.log(`No matches for keyword "${kw}"`);
  }
});
