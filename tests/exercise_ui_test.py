"""Comprueba en el navegador el editor de los ejercicios con Playwright y tools/serve.py.

    uv run --group tools python tests/exercise_ui_test.py

Abre el paso de misión de p1-quickstart, comprueba que el código inicial falla con un mensaje por
caso, que la solución pasa, que el código y las pistas se conservan y que la consola no registra
errores. Sin corrector (servidor estático) la tarjeta explica cómo ejecutarlo.
"""
import importlib.util
import json
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
LESSON = "p1-quickstart"
EXERCISE = f"{LESSON}/ghz"


def start(handler):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(handler, directory=str(ROOT / "site")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}"


def quiet(base):
    return type("Quiet", (base,), {"log_message": lambda *a: None})


def mission_step():
    beats = json.loads((ROOT / "site" / "lessons" / LESSON / "lesson.json").read_text(encoding="utf-8"))["beats"]
    return next(i for i, b in enumerate(beats) if b["id"] == "mision")


def ghz_card(page):
    return page.locator(".mcard").filter(has=page.locator("textarea.xcode")).nth(1)


def main():
    spec = importlib.util.spec_from_file_location("serve_tool", ROOT / "tools" / "serve.py")
    serve = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(serve)
    solution = (ROOT / "exercises" / LESSON / "ghz" / "solution.py").read_text(encoding="utf-8")
    url = f"/lesson.html?l={LESSON}&beat={mission_step()}"
    fallos = []

    def check(ok, msg):
        if not ok:
            fallos.append(msg)
        print("✓" if ok else "✗", msg)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 1500})
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))

        page.goto(start(quiet(serve.Handler)) + url)
        card = ghz_card(page)
        card.wait_for()
        card.get_by_role("button", name="Comprobar").click()
        card.locator(".xline.bad").first.wait_for(timeout=20_000)
        check("caso oculto 1" in card.locator(".xout").inner_text(), "el código inicial falla y muestra los casos ocultos")
        card.locator("textarea").fill(solution)
        card.get_by_role("button", name="Comprobar").click()
        card.get_by_text("¡Pasa todos los casos!").wait_for(timeout=20_000)
        check(card.locator(".xline.bad").count() == 0, "la solución pasa todos los casos")
        card.get_by_role("button", name="Pista").click()
        check(card.locator(".xhint").count() == 1, "una pista por pulsación")
        page.reload()
        check(ghz_card(page).locator("textarea").input_value() == solution, "el código se conserva al recargar")
        ghz_card(page).get_by_role("button", name="Empezar de nuevo").click()
        check("def ghz(n)" in ghz_card(page).locator("textarea").input_value() and solution not in ghz_card(page).locator("textarea").input_value(),
              "«Empezar de nuevo» restaura el código inicial")

        page.goto(start(quiet(SimpleHTTPRequestHandler)) + url)
        card = ghz_card(page)
        card.get_by_role("button", name="Ejecutar").click()
        card.get_by_text("tools/serve.py").wait_for(timeout=5_000)
        check(True, "sin corrector la tarjeta explica cómo ejecutarlo")
        browser.close()
    check(not [e for e in errors if "501" not in e and "405" not in e], f"sin errores en consola: {errors}")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
