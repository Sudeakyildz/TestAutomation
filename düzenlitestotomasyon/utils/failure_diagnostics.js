/**
 * Pytest çıktısından teşhis + kaynak sınıflandırması (GitSec / Test / Ortam).
 */

const TEST_META = {
  'test_0_api_staging.py': {
    category: 'API',
    label: 'Staging API Smoke Testleri',
    gitsecArea: 'API',
    phase: 'API',
    phaseOrder: 0,
  },
  'test_1_login.py': { category: 'E2E', label: 'Giriş Akışı', gitsecArea: 'Auth', phase: 'Auth & Oturum', phaseOrder: 1 },
  'test_2_dashboard_navigation.py': { category: 'E2E', label: 'Dashboard Navigasyon', gitsecArea: 'Dashboard', phase: 'Dashboard', phaseOrder: 2 },
  'test_3_dashboard_controls.py': { category: 'E2E', label: 'Dashboard UI Kontrolleri', gitsecArea: 'Dashboard', phase: 'Dashboard', phaseOrder: 2 },
  'test_4_github_repositories.py': { category: 'E2E', label: 'GitHub Bağlantısı', gitsecArea: 'Integrations', phase: 'Repository & Provider', phaseOrder: 4 },
  'test_5_github_include_exclude.py': {
    category: 'E2E',
    label: 'Include / Exclude',
    gitsecArea: 'Repositories / License Inclusion',
    phase: 'Repository & Provider',
    phaseOrder: 4,
  },
  'test_6_github_backup_combinations.py': { category: 'E2E', label: 'Backup Kombinasyonları', gitsecArea: 'Backup', phase: 'Backup', phaseOrder: 5 },
  'test_7_backups_restore.py': { category: 'E2E', label: 'Backup & Restore', gitsecArea: 'Restore Wizard', phase: 'Restore', phaseOrder: 6 },
  'test_8_schedulers.py': { category: 'E2E', label: 'Zamanlayıcılar', gitsecArea: 'Schedulers', phase: 'Scheduler', phaseOrder: 7 },
  'test_9_auth_extended.py': { category: 'E2E', label: 'Auth Genişletilmiş', gitsecArea: 'Auth', phase: 'Auth & Oturum', phaseOrder: 1 },
  'test_10_workspace.py': { category: 'E2E', label: 'Workspace Yönetimi', gitsecArea: 'Workspace', phase: 'Workspace', phaseOrder: 3 },
  'test_11_activity.py': { category: 'E2E', label: 'Activity & Bildirimler', gitsecArea: 'Activity', phase: 'Activity', phaseOrder: 8 },
  'test_12_storage.py': { category: 'E2E', label: 'Storage', gitsecArea: 'Storage', phase: 'Storage', phaseOrder: 9 },
  'test_13_licence_billing.py': { category: 'E2E', label: 'Lisans & Billing', gitsecArea: 'Licence', phase: 'Lisans & Billing', phaseOrder: 10 },
  'test_14_settings.py': { category: 'E2E', label: 'Kullanıcı Ayarları', gitsecArea: 'Settings', phase: 'Ayarlar', phaseOrder: 11 },
  'test_15_repo_advanced.py': { category: 'E2E', label: 'Repository Gelişmiş', gitsecArea: 'Repositories', phase: 'Repository & Provider', phaseOrder: 4 },
  'test_16_backup_advanced.py': { category: 'E2E', label: 'Backup Gelişmiş', gitsecArea: 'Backup', phase: 'Backup', phaseOrder: 5 },
  'test_17_restore_advanced.py': { category: 'E2E', label: 'Restore Gelişmiş', gitsecArea: 'Restore', phase: 'Restore', phaseOrder: 6 },
  'test_18_scheduler_advanced.py': { category: 'E2E', label: 'Scheduler Gelişmiş', gitsecArea: 'Schedulers', phase: 'Scheduler', phaseOrder: 7 },
  'test_19_negative_edge.py': { category: 'E2E', label: 'Negatif & Edge Case', gitsecArea: 'Cross-cutting', phase: 'Negatif & Edge', phaseOrder: 12 },
  'test_20_api_comprehensive.py': { category: 'API', label: 'Kapsamlı API Testleri', gitsecArea: 'API', phase: 'API', phaseOrder: 0 },
  'test_21_integrations_providers.py': { category: 'E2E', label: 'Bitbucket & GitLab', gitsecArea: 'Integrations', phase: 'Entegrasyonlar', phaseOrder: 4 },
  'test_22_workspace_team_actions.py': { category: 'E2E', label: 'Workspace & Ekip', gitsecArea: 'Workspace', phase: 'Workspace & Ekip', phaseOrder: 3 },
  'test_23_repo_actions.py': { category: 'E2E', label: 'Repo Aksiyonları', gitsecArea: 'Repositories', phase: 'Repository & Provider', phaseOrder: 4 },
  'test_24_backup_functional.py': { category: 'API', label: 'Backup Fonksiyonel', gitsecArea: 'Backup', phase: 'Backup', phaseOrder: 5 },
  'test_25_restore_functional.py': { category: 'E2E', label: 'Restore Fonksiyonel', gitsecArea: 'Restore', phase: 'Restore', phaseOrder: 6 },
  'test_26_scheduler_crud.py': { category: 'E2E', label: 'Scheduler CRUD', gitsecArea: 'Schedulers', phase: 'Scheduler', phaseOrder: 7 },
  'test_27_storage_functional.py': { category: 'E2E', label: 'Storage Fonksiyonel', gitsecArea: 'Storage', phase: 'Storage', phaseOrder: 9 },
  'test_28_account_billing.py': { category: 'E2E', label: 'Hesap & Billing', gitsecArea: 'Settings / Licence', phase: 'Ayarlar & Billing', phaseOrder: 11 },
  'test_29_sandbox_writes.py': { category: 'API', label: 'Sandbox Write Testleri', gitsecArea: 'Sandbox / Functional', phase: 'Sandbox Write', phaseOrder: 13 },
  'test_api_helpers_unit.py': { category: 'Unit', label: 'API Helper Unit Testleri', gitsecArea: 'Test Altyapısı', phase: 'Unit', phaseOrder: 14 },
};

const ERROR_PATTERNS = [
  {
    match: /\[GITSEC BUG\]/i,
    type: 'gitsec_product',
    bugSource: 'gitsec_product',
    reason: 'GitSec staging ortamında olası ürün hatası tespit edildi.',
    solution: 'Bu kayıt bilinçli olarak ürün ekibine iletilmeli. Test beklentisi doğru; UI/API beklenen davranışı göstermiyor.',
  },
  {
    match: /Exclude confirmation dialog did not appear|Exclude confirm not clicked|Could not exclude repository|Repository should remain excluded|licenseInclusionStatus/i,
    type: 'gitsec_exclude',
    bugSource: 'gitsec_product',
    reason: 'Repository exclude (hariç tutma) akışı tamamlanmıyor veya kalıcı olmuyor.',
    solution: 'GitSec bug: Switch/bulk exclude sonrası onay modalı açılmıyor veya API durumu persist etmiyor. Repositories / license-inclusion-status akışını inceleyin.',
  },
  {
    match: /element click intercepted|ElementClickInterceptedException|alert-dialog-overlay|data-title/i,
    type: 'gitsec_overlay',
    bugSource: 'gitsec_product',
    reason: 'UI overlay/modal buton tıklamasını engelliyor.',
    solution: 'GitSec bug: Restore/Scheduler ekranında görünmez overlay veya kapanmayan dialog tıklamayı bloke ediyor. UX/modal z-index kontrol edilmeli.',
  },
  {
    match: /licen[cs]e limit|threshold has been reached|lisans limit/i,
    type: 'license',
    bugSource: 'environment',
    reason: 'Lisans limiti veya eşik değeri aşıldı.',
    solution: 'Test ortamı limiti dolmuş olabilir; aktif repo sayısını azaltın veya lisans planını kontrol edin.',
  },
  {
    match: /TimeoutError|Condition not met within/i,
    type: 'timeout',
    bugSource: 'gitsec_product',
    reason: 'Beklenen UI/API durumu belirlenen süre içinde gerçekleşmedi.',
    solution: 'Staging yavaşlığı veya GitSec tarafında işlem tamamlanmıyor olabilir. Log adımını ve Network/API yanıtını kontrol edin.',
  },
  {
    match: /E2E_USER_EMAIL|environment variable is not defined|assert email/i,
    type: 'env',
    bugSource: 'environment',
    reason: 'Gerekli ortam değişkeni tanımlı değil.',
    solution: 'Panelden .env dosyasını doldurup kaydedin.',
  },
  {
    match: /GITHUB_TEST_USER|GITHUB_TEST_PASSWORD/i,
    type: 'github',
    bugSource: 'environment',
    reason: 'GitHub test hesabı bilgileri eksik veya hatalı.',
    solution: '.env dosyasına GitHub test hesabı bilgilerini ekleyin.',
  },
  {
    match: /ElementNotFound|NoSuchElement|not visible|wait_for_element/i,
    type: 'selector',
    bugSource: 'test_automation',
    reason: 'Sayfada beklenen element bulunamadı — UI değişmiş olabilir.',
    solution: 'Önce GitSec UI değişikliği mi kontrol edin; selector güncellenmesi gerekebilir.',
  },
  {
    match: /AssertionError/i,
    type: 'assertion',
    bugSource: 'unknown',
    reason: 'Test beklentisi karşılanmadı.',
    solution: 'Logdaki assertion satırını inceleyin; GitSec mi test mi kaynaklı olduğunu adımlara göre ayırın.',
  },
];

function extractPytestFailure(logBuffer) {
  if (!logBuffer) return null;
  const gitsec = logBuffer.match(/\[GITSEC BUG\][^\n]+/);
  if (gitsec) return { testId: null, message: gitsec[0].trim() };
  const failedLine = logBuffer.match(/^FAILED\s+([^\s]+)\s+-\s+(.+)$/m);
  if (failedLine) return { testId: failedLine[1], message: failedLine[2].trim() };
  const shortSummary = logBuffer.match(/=+\s*FAILURES\s*=+[\s\S]*?(\w+(?:Error|Exception)):\s*(.+)/);
  if (shortSummary) {
    return { testId: null, message: `${shortSummary[1]}: ${shortSummary[2].trim().split('\n')[0]}` };
  }
  return null;
}

function extractCurrentStep(logBuffer) {
  if (!logBuffer) return null;
  const matches = [...logBuffer.matchAll(/INFO: test step - (.+)/g)];
  return matches.length ? matches[matches.length - 1][1].trim() : null;
}

function bugSourceLabel(source) {
  const map = {
    gitsec_product: 'GitSec Ürün Hatası (Olası)',
    test_automation: 'Test Otomasyonu',
    environment: 'Ortam / Yapılandırma',
    unknown: 'Belirsiz — Log İnceleyin',
  };
  return map[source] || map.unknown;
}

function diagnose(testFile, exitCode, logBuffer, junitFailure) {
  const meta = TEST_META[testFile] || { category: 'E2E', label: testFile, gitsecArea: 'unknown' };

  if (exitCode === 0) {
    return {
      testFile,
      label: meta.label,
      category: meta.category,
      gitsecArea: meta.gitsecArea,
      success: true,
      exitCode,
      bugSource: 'none',
      bugSourceLabel: 'Başarılı',
      reason: null,
      solution: null,
      errorType: 'none',
      rawError: null,
      currentStep: extractCurrentStep(logBuffer),
    };
  }

  const extracted = extractPytestFailure(logBuffer);
  const rawError = junitFailure?.message || extracted?.message || 'Test başarısız oldu.';
  const combinedText = `${rawError || ''}\n${logBuffer || ''}`;

  let matchedPattern = null;
  for (const pattern of ERROR_PATTERNS) {
    if (pattern.match.test(combinedText)) {
      matchedPattern = pattern;
      break;
    }
  }

  const bugSource = matchedPattern?.bugSource || 'unknown';

  return {
    testFile,
    label: meta.label,
    category: meta.category,
    gitsecArea: meta.gitsecArea,
    success: false,
    exitCode,
    bugSource,
    bugSourceLabel: bugSourceLabel(bugSource),
    reason: matchedPattern?.reason || `Hata: ${String(rawError).slice(0, 240)}`,
    solution: matchedPattern?.solution || 'Log çıktısını inceleyin.',
    errorType: matchedPattern?.type || 'unknown',
    rawError: String(rawError).slice(0, 800),
    currentStep: extractCurrentStep(logBuffer),
  };
}

module.exports = {
  TEST_META,
  diagnose,
  extractCurrentStep,
  extractPytestFailure,
  bugSourceLabel,
};
