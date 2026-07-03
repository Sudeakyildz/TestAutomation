const fs = require('fs');
const path = require('path');

const sourcePath = path.join(__dirname, '..', 'latest_logs', 'düzenlitestotomasyon.tests.test_5_github_include_exclude.test_github_repositories_include_all_then_exclude_all', 'page_source.html');

if (!fs.existsSync(sourcePath)) {
  console.log('File not found');
  process.exit(1);
}

const html = fs.readFileSync(sourcePath, 'utf8');

console.log('--- Toasts ---');
const toastRegex = /<li[^>]*data-sonner-toast[^>]*>([\s\S]*?)<\/li>/gi;
let match;
while ((match = toastRegex.exec(html)) !== null) {
  const content = match[1].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
  console.log('Toast:', content);
}

console.log('--- Dialogs ---');
const dialogRegex = /<div[^>]*role="dialog"[^>]*>([\s\S]*?)<\/div>/gi;
while ((match = dialogRegex.exec(html)) !== null) {
  const content = match[1].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
  console.log('Dialog:', content);
}

console.log('--- Body text matching warnings ---');
const bodyRegex = /<body[^>]*>([\s\S]*?)<\/body>/gi;
const bodyMatch = bodyRegex.exec(html);
if (bodyMatch) {
  const text = bodyMatch[1].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
  const searchKws = ['fail', 'limit', 'threshold', 'licensed', 'error', 'hata', 'lisans'];
  searchKws.forEach(kw => {
    const idx = text.toLowerCase().indexOf(kw.toLowerCase());
    if (idx !== -1) {
      console.log(`Keyword "${kw}" found around: "...${text.substring(idx - 60, idx + 100)}..."`);
    }
  });
}
