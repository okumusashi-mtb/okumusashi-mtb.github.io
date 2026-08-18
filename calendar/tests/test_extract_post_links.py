import sys, os, importlib.util

_bin = os.path.join(os.path.dirname(__file__), "..", "bin")
sys.path.insert(0, _bin)
_spec = importlib.util.spec_from_loader(
    "extract_post_links",
    importlib.machinery.SourceFileLoader("extract_post_links",
                                         os.path.join(_bin, "extract-post-links")))
epl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(epl)


HTML = """<html><body>
<a href="https://example.com/outside">本文の外なので拾わない</a>
<div data-hook="post-description">
  <p>集合場所は<a href="http://www.google.co.jp/maps/place/名栗庁舎">名栗庁舎（クリックで地図）</a>です。</p>
  <p>署名は<a href="http://chng.it/abc">http://chng.it/abc</a>から。</p>
  <p>重複: <a href="http://chng.it/abc">同じ URL</a></p>
  <p>連絡は<a href="mailto:okumusashi.mtb@gmail.com">メール</a>で。</p>
  <iframe src="https://www.google.com/maps/embed?pb=!1m14"></iframe>
  <a href="http://wix.com">wix.com</a>
  <a href="https://siteassets.parastorage.com/pages/x">thunderbolt</a>
  <a href="https://static.wixstatic.com/media/c3395c_x~mv2.jpg">写真</a>
</div>
&copy; 2019 Proudly created with Wix.com
<a href="https://www.facebook.com/okumusashi.mtb">フッタ</a>
</body></html>"""


def test_extracts_body_links_with_anchor_text():
    got = epl.extract_links(HTML)
    urls = [l["url"] for l in got["links"]]
    assert urls == ["http://www.google.co.jp/maps/place/名栗庁舎",
                    "http://chng.it/abc",
                    "mailto:okumusashi.mtb@gmail.com"]
    assert got["links"][0]["text"] == "名栗庁舎（クリックで地図）"


def test_excludes_wix_boilerplate_and_outside_body():
    got = epl.extract_links(HTML)
    joined = " ".join(l["url"] for l in got["links"])
    for host in ("wix.com", "parastorage", "wixstatic", "example.com", "facebook"):
        assert host not in joined


def test_extracts_iframe_embeds():
    assert epl.extract_links(HTML)["embeds"] == ["https://www.google.com/maps/embed?pb=!1m14"]


def test_no_body_region_yields_nothing():
    assert epl.extract_links("<html><body>本文なし</body></html>") == {"links": [], "embeds": []}
