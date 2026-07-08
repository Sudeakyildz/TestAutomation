"""
GitSec ürün hatası raporlama yardımcıları.

Test başarısız olduğunda hata kaynağını ayırt etmek için kullanılır:
- gitsec_product: Staging/GitSec uygulama hatası (test doğru, ürün yanlış)
- test_automation: Selector/akış güncellenmeli
- environment: .env, oturum, ağ vb.
"""


class GitsecProductBug(Exception):
    """GitSec staging ortamında tespit edilen olası ürün hatası."""

    def __init__(self, title, details, area="unknown", evidence=None):
        self.title = title
        self.details = details
        self.area = area
        self.evidence = evidence or []
        message = f"[GITSEC BUG] {title} — {details}"
        super().__init__(message)


def fail_gitsec_bug(title, details, area="unknown", evidence=None):
    """GitSec ürün hatası olarak pytest fail."""
    import pytest

    lines = [f"[GITSEC BUG] {title}", details, f"Alan: {area}"]
    if evidence:
        lines.append("Kanıt:")
        lines.extend(f"  - {item}" for item in evidence)
    pytest.fail("\n".join(lines))
