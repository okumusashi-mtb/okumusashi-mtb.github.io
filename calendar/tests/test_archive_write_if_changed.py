import os, sys, importlib.util, importlib.machinery
import yaml

HERE = os.path.dirname(__file__)
BIN = os.path.join(HERE, "..", "bin", "cal-omc-archive-fetch")


def _load_cli():
    loader = importlib.machinery.SourceFileLoader("cal_omc_archive_fetch", BIN)
    spec = importlib.util.spec_from_loader("cal_omc_archive_fetch", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.join(HERE, "..", "bin"))
    spec.loader.exec_module(mod)
    return mod


def _doc(fetched="2026-06-22", body="早朝より作業しました。"):
    return {
        "summary": "名栗定期作業",
        "date": "2026-06-07",
        "all_day": True,
        "category": "定期作業",
        "description": "出典: https://x/r",
        "source": {
            "type": "omc-blog",
            "crawler": "cal-omc-archive-fetch",
            "fetched": fetched,
            "posts": [
                {"kind": "report", "url": "https://x/r", "title": "6/7 名栗定期作業の報告",
                 "published": "2026-06-07", "body": body},
            ],
        },
    }


def test_write_event_if_changed_skips_when_only_fetched_differs(tmp_path):
    cli = _load_cli()
    path = str(tmp_path / "ev.yaml")

    wrote1 = cli.write_event_if_changed(path, _doc(fetched="2026-06-22"))
    assert wrote1 is True
    before = open(path, encoding="utf-8").read()

    wrote2 = cli.write_event_if_changed(path, _doc(fetched="2026-06-29"))
    assert wrote2 is False
    after = open(path, encoding="utf-8").read()

    assert before == after
    assert yaml.safe_load(after)["source"]["fetched"] == "2026-06-22"


def test_write_event_if_changed_rewrites_when_content_changes(tmp_path):
    cli = _load_cli()
    path = str(tmp_path / "ev.yaml")

    cli.write_event_if_changed(path, _doc(fetched="2026-06-22", body="早朝より作業しました。"))
    wrote = cli.write_event_if_changed(
        path, _doc(fetched="2026-06-29", body="早朝より作業しました。橋の補修も行った。"))

    assert wrote is True
    d = yaml.safe_load(open(path, encoding="utf-8"))
    assert d["source"]["fetched"] == "2026-06-29"
    assert "橋の補修" in d["source"]["posts"][0]["body"]


def test_write_event_if_changed_writes_new_file(tmp_path):
    cli = _load_cli()
    path = str(tmp_path / "sub" / "ev.yaml")

    wrote = cli.write_event_if_changed(path, _doc())
    assert wrote is True
    assert os.path.exists(path)


def test_write_event_if_changed_overwrites_broken_yaml(tmp_path):
    cli = _load_cli()
    path = tmp_path / "ev.yaml"
    path.write_text("not: [valid: yaml: ::", encoding="utf-8")

    wrote = cli.write_event_if_changed(str(path), _doc(fetched="2026-06-29"))
    assert wrote is True
    d = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert d["source"]["fetched"] == "2026-06-29"


def test_review_file_written_in_sorted_order(tmp_path):
    import subprocess

    # 2つの投稿を用意し、どちらも日付が抽出できない(review行き)ようにする。
    # sitemap の記載順と review の書き出し順が一致しない(URL 逆順)ことを確認する。
    url_z = "https://okumusashimtb.wixsite.com/omcweb/post/z-post"
    url_a = "https://okumusashimtb.wixsite.com/omcweb/post/a-post"
    sitemap = tmp_path / "sitemap.xml"
    sitemap.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'<url><loc>{url_z}</loc></url>\n'
        f'<url><loc>{url_a}</loc></url>\n'
        '</urlset>\n', encoding="utf-8")

    cache = tmp_path / "cache"
    cache.mkdir()
    cli = _load_cli()
    for url in (url_z, url_a):
        rec = {"url": url, "title": "日付なし記事", "published": "日付不明",
               "body": "本文"}
        (cache / f"{cli.omc_parse.slugify_post_url(url)}.yaml").write_text(
            yaml.safe_dump(rec, allow_unicode=True, sort_keys=False), encoding="utf-8")

    out = tmp_path / "events"
    review = tmp_path / "rev.txt"
    r = subprocess.run(
        [sys.executable, BIN, "--sitemap-file", str(sitemap),
         "--cache-dir", str(cache), "--out-dir", str(out),
         "--review-file", str(review), "--fetched", "2026-06-22"],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert review.exists()
    lines = review.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines == sorted(lines)
    # sitemap 順 (z, a) とは異なりソート順 (a, z) で書かれていること
    assert lines[0].startswith(url_a)
    assert lines[1].startswith(url_z)


def test_same_date_multi_post_event_is_deterministic_regardless_of_sitemap_order(tmp_path):
    """sitemap の列挙順が実行ごとに変わっても、同一日に複数記事がある
    イベントの出力 (posts の順・description・summary) が揺れないこと。
    (sitemap は site 側の都合で順序が安定しない実例が確認されたため。
    並び替えの基準は公開日時 (pub_date) が主、同日同時刻は url でタイブレークする。)"""
    import subprocess

    cli = _load_cli()
    url_a = "https://okumusashimtb.wixsite.com/omcweb/post/2026/07/01/7-7-イベントa"
    url_b = "https://okumusashimtb.wixsite.com/omcweb/post/2026/07/02/7-7-イベントb"
    recs = {
        url_a: {"url": url_a, "title": "7月7日イベントA", "published": "2026-07-01", "body": "本文A"},
        url_b: {"url": url_b, "title": "7月7日イベントB", "published": "2026-07-02", "body": "本文B"},
    }

    def _run(order):
        d = tmp_path / ("run_" + "_".join(order))
        cache = d / "cache"
        cache.mkdir(parents=True)
        for key in order:
            url = url_a if key == "a" else url_b
            (cache / f"{cli.omc_parse.slugify_post_url(url)}.yaml").write_text(
                yaml.safe_dump(recs[url], allow_unicode=True, sort_keys=False), encoding="utf-8")
        urls_in_order = [url_a if k == "a" else url_b for k in order]
        sitemap = d / "sitemap.xml"
        locs = "\n".join(f"<url><loc>{u}</loc></url>" for u in urls_in_order)
        sitemap.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{locs}\n</urlset>\n',
            encoding="utf-8")
        out = d / "events"
        r = subprocess.run(
            [sys.executable, BIN, "--sitemap-file", str(sitemap), "--cache-dir", str(cache),
             "--out-dir", str(out), "--review-file", str(d / "rev.txt"), "--fetched", "2026-07-20"],
            capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        files = list(out.glob("2026/07-07_*.yaml"))
        assert len(files) == 1
        return files[0].read_text(encoding="utf-8")

    content_ab = _run(["a", "b"])
    content_ba = _run(["b", "a"])
    assert content_ab == content_ba


def test_cancellation_notice_wins_summary_regardless_of_order(tmp_path):
    """同日に (案内, 後日の中止告知) の2 post があるとき、summary と
    description(出典 URL) はともに『中止』を含む告知を優先する
    (入力順に依存しない回帰テスト)。
    2022-09-18 の実イベントで中止告知が summary/description から落ちる
    退行が見つかったことに対する回帰テスト。"""
    import subprocess

    cli = _load_cli()
    url_announce = "https://okumusashimtb.wixsite.com/omcweb/post/2022/09/01/9-18-annouce"
    url_cancel = "https://okumusashimtb.wixsite.com/omcweb/post/2022/09/15/9-18-cancel"
    recs = {
        url_announce: {"url": url_announce, "title": "9/18 名栗定期作業のお知らせ",
                       "published": "2022-09-01", "body": "9時集合です。"},
        url_cancel: {"url": url_cancel, "title": "9/18 名栗定期作業中止のお知らせ",
                     "published": "2022-09-15", "body": "雨天のため中止します。"},
    }

    def _run(order):
        d = tmp_path / ("cancel_run_" + "_".join(order))
        cache = d / "cache"
        cache.mkdir(parents=True)
        urls_in_order = [url_announce if k == "announce" else url_cancel for k in order]
        for url in urls_in_order:
            (cache / f"{cli.omc_parse.slugify_post_url(url)}.yaml").write_text(
                yaml.safe_dump(recs[url], allow_unicode=True, sort_keys=False), encoding="utf-8")
        sitemap = d / "sitemap.xml"
        locs = "\n".join(f"<url><loc>{u}</loc></url>" for u in urls_in_order)
        sitemap.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{locs}\n</urlset>\n',
            encoding="utf-8")
        out = d / "events"
        r = subprocess.run(
            [sys.executable, BIN, "--sitemap-file", str(sitemap), "--cache-dir", str(cache),
             "--out-dir", str(out), "--review-file", str(d / "rev.txt"), "--fetched", "2026-07-20"],
            capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        files = list(out.glob("2022/09-18_*.yaml"))
        assert len(files) == 1
        return yaml.safe_load(files[0].read_text(encoding="utf-8"))

    d1 = _run(["announce", "cancel"])
    d2 = _run(["cancel", "announce"])
    assert "中止" in d1["summary"]
    assert "中止" in d2["summary"]
    assert d1["summary"] == d2["summary"]

    # description (出典 URL) も中止記事を指すこと (入力順に依存しない)
    assert d1["description"] == f"出典: {url_cancel}"
    assert d2["description"] == f"出典: {url_cancel}"
    assert d1["description"] == d2["description"]


def test_report_after_cancellation_wins_over_cancellation(tmp_path):
    """『最後の意思表示が勝つ』回帰テスト (2025/08-03 型)。
    (案内, 中止告知, 中止よりさらに後日の report) の3 post があるとき、
    実際には活動が行われたことを report が示しているので、
    summary/description は中止ではなく report を採用すること
    (入力順に依存しない)。
    2025-08-03 の実イベントで、中止告知の後に写真付きの報告記事が
    投稿されていたにもかかわらず summary が「活動中止」になっていた
    誤りに対する回帰テスト (Google カレンダーの実績「名栗定期作業」とも矛盾していた)。"""
    import subprocess

    cli = _load_cli()
    url_announce = "https://okumusashimtb.wixsite.com/omcweb/post/2025/07/18/8-3-announce"
    url_cancel = "https://okumusashimtb.wixsite.com/omcweb/post/2025/08/02/8-3-cancel"
    url_report = "https://okumusashimtb.wixsite.com/omcweb/post/2025/08/07/8-3-report"
    recs = {
        url_announce: {"url": url_announce, "title": "8/3 名栗定期作業のお知らせ",
                       "published": "2025-07-18", "body": "9時集合です。"},
        url_cancel: {"url": url_cancel, "title": "8/3活動中止のお知らせ",
                     "published": "2025-08-02", "body": "気温が高いため中止します。"},
        url_report: {"url": url_report, "title": "8/3名栗定期作業の報告",
                     "published": "2025-08-07",
                     "images": ["https://static.wixstatic.com/media/c3395c_dummy.jpg"]},
    }

    def _run(order):
        d = tmp_path / ("report_wins_run_" + "_".join(order))
        cache = d / "cache"
        cache.mkdir(parents=True)
        key_to_url = {"announce": url_announce, "cancel": url_cancel, "report": url_report}
        urls_in_order = [key_to_url[k] for k in order]
        for url in urls_in_order:
            (cache / f"{cli.omc_parse.slugify_post_url(url)}.yaml").write_text(
                yaml.safe_dump(recs[url], allow_unicode=True, sort_keys=False), encoding="utf-8")
        sitemap = d / "sitemap.xml"
        locs = "\n".join(f"<url><loc>{u}</loc></url>" for u in urls_in_order)
        sitemap.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{locs}\n</urlset>\n',
            encoding="utf-8")
        out = d / "events"
        r = subprocess.run(
            [sys.executable, BIN, "--sitemap-file", str(sitemap), "--cache-dir", str(cache),
             "--out-dir", str(out), "--review-file", str(d / "rev.txt"), "--fetched", "2026-07-27"],
            capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        files = list(out.glob("2025/08-03_*.yaml"))
        assert len(files) == 1
        return yaml.safe_load(files[0].read_text(encoding="utf-8"))

    d1 = _run(["announce", "cancel", "report"])
    d2 = _run(["report", "cancel", "announce"])

    assert "中止" not in d1["summary"]
    assert "中止" not in d2["summary"]
    assert d1["summary"] == d2["summary"] == "名栗定期作業"

    assert d1["description"] == f"出典: {url_report}"
    assert d2["description"] == f"出典: {url_report}"


def test_cancellation_still_wins_when_no_later_report(tmp_path):
    """report が存在しない (中止告知のみで終わる) 既存ケースでは、
    引き続き中止告知が summary/description を勝ち取ること
    (『最後の意思表示が勝つ』ルールの退行防止)。"""
    import subprocess

    cli = _load_cli()
    url_announce = "https://okumusashimtb.wixsite.com/omcweb/post/2022/09/01/9-18-annouce2"
    url_cancel = "https://okumusashimtb.wixsite.com/omcweb/post/2022/09/15/9-18-cancel2"
    recs = {
        url_announce: {"url": url_announce, "title": "9/18 名栗定期作業のお知らせ",
                       "published": "2022-09-01", "body": "9時集合です。"},
        url_cancel: {"url": url_cancel, "title": "9/18 名栗定期作業中止のお知らせ",
                     "published": "2022-09-15", "body": "雨天のため中止します。"},
    }

    def _run(order):
        d = tmp_path / ("still_cancel_run_" + "_".join(order))
        cache = d / "cache"
        cache.mkdir(parents=True)
        key_to_url = {"announce": url_announce, "cancel": url_cancel}
        urls_in_order = [key_to_url[k] for k in order]
        for url in urls_in_order:
            (cache / f"{cli.omc_parse.slugify_post_url(url)}.yaml").write_text(
                yaml.safe_dump(recs[url], allow_unicode=True, sort_keys=False), encoding="utf-8")
        sitemap = d / "sitemap.xml"
        locs = "\n".join(f"<url><loc>{u}</loc></url>" for u in urls_in_order)
        sitemap.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{locs}\n</urlset>\n',
            encoding="utf-8")
        out = d / "events"
        r = subprocess.run(
            [sys.executable, BIN, "--sitemap-file", str(sitemap), "--cache-dir", str(cache),
             "--out-dir", str(out), "--review-file", str(d / "rev.txt"), "--fetched", "2026-07-27"],
            capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        files = list(out.glob("2022/09-18_*.yaml"))
        assert len(files) == 1
        return yaml.safe_load(files[0].read_text(encoding="utf-8"))

    d1 = _run(["announce", "cancel"])
    d2 = _run(["cancel", "announce"])
    assert "中止" in d1["summary"]
    assert "中止" in d2["summary"]
    assert d1["description"] == f"出典: {url_cancel}"
    assert d2["description"] == f"出典: {url_cancel}"


def test_cancellation_notice_classified_as_other_still_wins_summary(tmp_path):
    """中止告知のタイトルがキーワード分類で『その他』になるケース
    (例:「7-20活動中止のお知らせ」) でも、案内記事のカテゴリ (例: 里山整備)
    で絞り込む前に中止を検出し、summary に反映されること。
    category != "その他" 分岐でカテゴリ絞り込みが先に行われていたため
    中止候補が落ちてしまい、description (_pick_primary, 絞り込み無し) と
    食い違う退行があったことに対する回帰テスト。"""
    import subprocess

    cli = _load_cli()
    url_announce = "https://okumusashimtb.wixsite.com/omcweb/post/2026/07/10/7-20-satoyama-annouce"
    url_cancel = "https://okumusashimtb.wixsite.com/omcweb/post/2026/07/19/7-20-satoyama-cancel"
    recs = {
        url_announce: {"url": url_announce, "title": "7/20 里山整備活動のお知らせ",
                       "published": "2026-07-10", "body": "9時集合です。"},
        url_cancel: {"url": url_cancel, "title": "7-20活動中止のお知らせ",
                     "published": "2026-07-19", "body": "雨天のため中止します。"},
    }

    def _run(order):
        d = tmp_path / ("other_cancel_run_" + "_".join(order))
        cache = d / "cache"
        cache.mkdir(parents=True)
        urls_in_order = [url_announce if k == "announce" else url_cancel for k in order]
        for url in urls_in_order:
            (cache / f"{cli.omc_parse.slugify_post_url(url)}.yaml").write_text(
                yaml.safe_dump(recs[url], allow_unicode=True, sort_keys=False), encoding="utf-8")
        sitemap = d / "sitemap.xml"
        locs = "\n".join(f"<url><loc>{u}</loc></url>" for u in urls_in_order)
        sitemap.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{locs}\n</urlset>\n',
            encoding="utf-8")
        out = d / "events"
        r = subprocess.run(
            [sys.executable, BIN, "--sitemap-file", str(sitemap), "--cache-dir", str(cache),
             "--out-dir", str(out), "--review-file", str(d / "rev.txt"), "--fetched", "2026-07-20"],
            capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        files = list(out.glob("2026/07-20_*.yaml"))
        assert len(files) == 1
        return yaml.safe_load(files[0].read_text(encoding="utf-8"))

    d1 = _run(["announce", "cancel"])
    d2 = _run(["cancel", "announce"])

    # category はカテゴリ判定可能な案内記事 (里山整備) 由来のまま変わらない
    assert d1["category"] == "里山整備"
    assert d2["category"] == "里山整備"

    # summary はカテゴリで絞り込まれず、その他分類の中止告知を拾うこと
    assert "中止" in d1["summary"]
    assert "中止" in d2["summary"]
    assert d1["summary"] == d2["summary"]

    # description (出典 URL) も同じ中止記事を指し、summary と食い違わないこと
    assert d1["description"] == f"出典: {url_cancel}"
    assert d2["description"] == f"出典: {url_cancel}"
    assert d1["description"] == d2["description"]
