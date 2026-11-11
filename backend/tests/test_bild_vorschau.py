"""Vorschaubilder für Übersichten (backend/app/bilder/vorschau.py)."""

import io

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.bilder import vorschau as modul

KAMPAGNE = "kampagne-1"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(modul, "UPLOAD_DIR", tmp_path)
    (tmp_path / KAMPAGNE).mkdir()
    app = FastAPI()
    app.include_router(modul.router)
    app.mount("/uploads", modul.CachendeUploads(directory=str(tmp_path)), name="uploads")
    return TestClient(app), tmp_path


def _bild(pfad, groesse, fmt="PNG", **kw):
    Image.new("RGB", groesse, (200, 30, 30)).save(pfad, fmt, **kw)


def test_grosses_bild_wird_verkleinert_und_gecacht(client):
    c, ordner = client
    _bild(ordner / KAMPAGNE / "a.png", (2000, 1000))
    r = c.get(f"/uploads/_vorschau/480/{KAMPAGNE}/a.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/webp"
    assert "immutable" in r.headers["cache-control"]
    # Kürzere Seite = 480, Seitenverhältnis bleibt.
    assert Image.open(io.BytesIO(r.content)).size == (960, 480)
    assert (ordner / "_vorschau" / "480" / KAMPAGNE / "a.png.webp").is_file()


def test_exif_hochformat_wird_gedreht(client):
    c, ordner = client
    exif = Image.Exif()
    exif[0x0112] = 6  # 90° gedreht: gespeichert quer, angezeigt hoch
    _bild(ordner / KAMPAGNE / "h.jpg", (1600, 800), "JPEG", exif=exif)
    r = c.get(f"/uploads/_vorschau/128/{KAMPAGNE}/h.jpg")
    assert Image.open(io.BytesIO(r.content)).size == (128, 256)


def test_kleines_bild_kommt_als_original(client):
    c, ordner = client
    _bild(ordner / KAMPAGNE / "k.png", (100, 100))
    r = c.get(f"/uploads/_vorschau/480/{KAMPAGNE}/k.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"


def test_animiertes_gif_bleibt_animiert(client):
    c, ordner = client
    frames = [Image.new("P", (800, 800), i) for i in range(3)]
    frames[0].save(ordner / KAMPAGNE / "g.gif", save_all=True, append_images=frames[1:])
    r = c.get(f"/uploads/_vorschau/128/{KAMPAGNE}/g.gif")
    assert r.headers["content-type"] == "image/gif"


def test_ungueltige_breite_und_pfade(client):
    c, ordner = client
    _bild(ordner / KAMPAGNE / "a.png", (2000, 1000))
    assert c.get(f"/uploads/_vorschau/999/{KAMPAGNE}/a.png").status_code == 404
    assert c.get(f"/uploads/_vorschau/480/{KAMPAGNE}/fehlt.png").status_code == 404
    assert c.get("/uploads/_vorschau/480/..%2F..%2Fetc/passwd").status_code == 404
    assert c.get(f"/uploads/_vorschau/480/{KAMPAGNE}/.versteckt").status_code == 404


def test_original_hat_langzeit_cache(client):
    c, ordner = client
    _bild(ordner / KAMPAGNE / "a.png", (50, 50))
    r = c.get(f"/uploads/{KAMPAGNE}/a.png")
    assert r.status_code == 200
    assert "immutable" in r.headers["cache-control"]
