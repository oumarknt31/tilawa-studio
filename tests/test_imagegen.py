"""Pictures made per verse by OpenAI, against a local stand-in for its API (nothing paid)."""

import base64
import io
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from PIL import Image

from tilawa import imagegen, project
from tilawa.i18n import UserError


def _png() -> str:
    buf = io.BytesIO()
    Image.new("RGB", (64, 96), (40, 80, 120)).save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


@pytest.fixture
def openai(monkeypatch):
    asked = []

    class Fake(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body):
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            ok = self.headers["Authorization"] == "Bearer good"
            self._send(200 if ok else 401, {"data": []} if ok else {"error": {"message": "bad key"}})

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            asked.append(body)
            if "Surah Al-Kawthar, verse 3" in body["prompt"]:
                return self._send(400, {"error": {"code": "moderation_blocked", "message": "refused"}})
            self._send(200, {"data": [{"b64_json": _png()}]})

    srv = HTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setattr(imagegen, "API", f"http://127.0.0.1:{srv.server_port}")
    yield asked
    srv.shutdown()


def test_the_prompt_says_the_meaning_and_the_limits():
    p = imagegen.prompt(103, 2, "16:9", "watercolour")
    assert "horizontal" in p and "Surah Al-'Asr, verse 2" in p
    assert "perdition" not in p and "loss" in p.lower()  # the English meaning
    assert "Never show people" in p and "No text" in p and p.endswith("watercolour")


def test_the_key_stays_in_the_tilawa_folder(tmp_path, openai):
    imagegen.check_key("good")
    with pytest.raises(UserError) as e:
        imagegen.check_key("wrong")
    assert e.value.key == "openai_key"
    imagegen.save_key(tmp_path, "good")
    assert imagegen.load_key(tmp_path) == "good" and oct(imagegen.key_file(tmp_path).stat().st_mode)[-3:] == "600"
    imagegen.save_key(tmp_path, "")
    assert imagegen.load_key(tmp_path) == ""


def test_one_picture_per_verse_added_to_the_project(tmp_path, openai):
    p = project.Project(folder=tmp_path, video="v.mp4", surah=108, first_verse=1, format="9:16")
    p.save()
    r = project.verse_images(tmp_path, [(108, 1), (108, 2), (108, 3)], "good", "", {"108:2": "my own prompt"})
    assert sorted(m["verse"] for m in r["made"]) == [[108, 1], [108, 2]]
    assert r["failed"][0]["verse"] == [108, 3] and "contenu" in r["failed"][0]["error"]
    media = project.Project.load(tmp_path).media
    assert {tuple(m["verse"]) for m in media} == {(108, 1), (108, 2)} and all(m["ai"] and m["kind"] == "image" for m in media)
    assert all((tmp_path / "media" / m["file"]).exists() for m in media)
    assert next(m for m in media if m["verse"] == [108, 2])["prompt"] == "my own prompt"
    assert {b["size"] for b in openai} == {"1024x1536"} and {b["quality"] for b in openai} == {"medium"}
