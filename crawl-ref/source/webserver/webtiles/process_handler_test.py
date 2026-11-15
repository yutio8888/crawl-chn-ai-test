import os

from webtiles.process_handler import _static_fingerprint


def test_static_fingerprint_changes_when_assets_change(tmp_path):
    atlas = tmp_path / "main.png"
    atlas.write_bytes(b"old atlas")
    info = tmp_path / "tileinfo-main.js"
    info.write_text("old index")
    (tmp_path / "subdir").mkdir()

    before = _static_fingerprint(str(tmp_path))
    assert before == _static_fingerprint(str(tmp_path))
    assert "subdir" not in before

    # A rebuilt atlas (new size and mtime) must change the /gamedata/ key.
    atlas.write_bytes(b"rebuilt atlas, one more tile")
    st = os.stat(atlas)
    os.utime(atlas, ns=(st.st_atime_ns, st.st_mtime_ns + 1000000000))
    assert _static_fingerprint(str(tmp_path)) != before


def test_static_fingerprint_missing_dir(tmp_path):
    assert _static_fingerprint(str(tmp_path / "missing")) == ""
