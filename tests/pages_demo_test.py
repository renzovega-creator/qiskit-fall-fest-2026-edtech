"""Recorre las cuatro misiones de Pages sin servidor Qiskit ni peticiones /run.

python tests/pages_demo_test.py
"""

import argparse
import json
import re
import sys
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import Route, expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.pages import build  # noqa: E402


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def main(public_url: str | None = None) -> None:
    with tempfile.TemporaryDirectory(prefix="qg-pages-demo-") as temp:
        root = Path(temp)
        build(root / "quantumshot")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(root)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = (
            public_url.rstrip("/")
            if public_url
            else f"http://127.0.0.1:{server.server_port}/quantumshot"
        )
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page(reduced_motion="reduce")
                posts: list[str] = []
                errors: list[str] = []
                page.on(
                    "request", lambda req: posts.append(req.url) if req.method == "POST" else None
                )
                page.on("pageerror", lambda err: errors.append(str(err)))

                def slider(selector: str, value: float) -> None:
                    page.locator(selector).evaluate(
                        "(el, value) => { el.value = value; el.dispatchEvent(new Event('input', { bubbles: true })); }",
                        value,
                    )

                def measure() -> None:
                    page.get_by_role(
                        "button",
                        name=re.compile(
                            "Medir con Qiskit|Ver resultado de ejemplo|Consultar de nuevo"
                        ),
                    ).click()
                    page.wait_for_function(
                        "document.querySelector('.feedback h3') || document.querySelector('.estado-run.error')"
                    )
                    assert not posts, f"Pages intentó ejecutar código: {posts}"
                    expect(page.locator(".estado-run.error")).to_have_count(0)
                    expect(page.get_by_role("button", name="Comprobar el reto")).to_be_enabled()

                def complete() -> None:
                    page.get_by_role("button", name="Comprobar el reto").click()
                    expect(page.locator("dialog.logro")).to_be_visible()
                    page.get_by_role("button", name="Seguir aquí").click()

                page.goto(f"{base}/juego.html#mision=m1")
                page.locator("#pred").fill("50")
                measure()
                page.get_by_role("button", name="Comprobar el reto").click()
                expect(page.locator(".resultado-reto")).to_contain_text("Todavía no")
                slider("#theta", 60)
                measure()
                complete()
                page.screenshot(path=str(ROOT / "shots" / "pages-demo-mission.png"), full_page=True)

                page.goto(f"{base}/juego.html#mision=m2")
                page.locator("#pred").fill("500")
                slider("#shots", 500)
                measure()
                complete()

                page.goto(f"{base}/juego.html#mision=m3")
                page.locator('input[name="pred"][value="1.5"]').check()
                slider("#escala", 1.5)
                measure()
                complete()

                page.goto(f"{base}/juego.html#mision=t1")
                page.locator("#pred").fill("300")
                slider("#shots-t", 300)
                measure()
                complete()

                state = page.evaluate("JSON.parse(localStorage.getItem('qiskit:juego'))")
                assert len(state["evidencias"]) == 4
                assert all(e.get("demo") is True for e in state["evidencias"])
                public = page.evaluate("""async () => {
                    const { datosPublicos, validarPublico } = await import('./juego/estado.js');
                    return validarPublico(datosPublicos(JSON.parse(localStorage.getItem('qiskit:juego'))));
                }""")
                assert all(e.get("demo") is True for e in public["evidencias"])
                page.goto(f"{base}/juego.html#portafolio")
                expect(page.locator("#vista")).to_contain_text("precomputado")
                social = page.evaluate("""async () => {
                    const { textoLinkedIn } = await import('./juego/portafolio.js');
                    return textoLinkedIn(JSON.parse(localStorage.getItem('qiskit:juego')), '');
                }""")
                assert "precomputados" in social
                page.screenshot(
                    path=str(ROOT / "shots" / "pages-demo-portfolio.png"), full_page=True
                )

                page.goto(f"{base}/")
                page.locator("#diario .cap-luego button").click()
                page.locator("#reto-prediccion").fill("200")
                page.locator(".reto-form button").click()
                expect(page.locator(".reto-form .fb")).to_contain_text(
                    "Resultado precomputado de Qiskit"
                )
                assert (
                    json.loads(page.evaluate("localStorage.getItem('qiskit:reto')"))["demo"] is True
                )
                assert not posts, f"La demo envió código: {posts}"
                assert not errors, errors
                page.screenshot(path=str(ROOT / "shots" / "pages-demo-daily.png"), full_page=True)
                fixtures = page.evaluate("""async () => {
                    const { RETOS } = await import('./retos.js');
                    const { resultadoDiario } = await import('./demo.js');
                    const data = await (await fetch('./demo-resultados.json')).json();
                    return { count: Object.keys(data.misiones).length,
                        daily: await Promise.all(RETOS.map(r => resultadoDiario(r.id))) };
                }""")
                assert fixtures["count"] == 471
                assert len(fixtures["daily"]) == 4
                assert all(isinstance(v, (int, float)) for v in fixtures["daily"])

                local = browser.new_page()
                local.route(
                    "**/account.js",
                    lambda route: route.fulfill(
                        content_type="text/javascript",
                        body="window.QG_RUNNER_AVAILABLE=true; window.QGAccount={ready:Promise.resolve(),changed(){}};",
                    ),
                )
                requests: list[dict[str, object]] = []

                def runner(route: Route) -> None:
                    requests.append(route.request.post_data_json)
                    route.fulfill(json={"stdout": json.dumps({"p1": 0.5, "shots": "01" * 100})})

                local.route("**/run", runner)
                local.goto(f"{base}/juego.html#mision=m1")
                local.locator("#pred").fill("100")
                local.get_by_role("button", name="Medir con Qiskit", exact=True).click()
                expect(local.get_by_role("button", name="Comprobar el reto")).to_be_enabled()
                assert len(requests) == 1 and requests[0]["mode"] == "run"
                assert "theta = np.deg2rad(90)" in requests[0]["code"]
                expect(local.locator(".backend")).to_contain_text("StatevectorSampler")
                local.close()
                browser.close()
                print(
                    "Pages demo OK: 4 misiones, portafolio, procedencia compartida, 471 configuraciones y 4 retos diarios; cero POST en demo. Ejecución local conserva /run."
                )
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Comprueba también el recorrido en una publicación de Pages.")
    main(parser.parse_args().url)
