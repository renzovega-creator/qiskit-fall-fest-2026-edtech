"""Falla las pruebas de navegador si la página pide una dirección externa.

`new_context` aborta y anota las peticiones que no van a 127.0.0.1 o
localhost. Las rutas específicas de cada prueba se evalúan antes que esta,
así que aquí solo llegan las peticiones que nadie atendió. `verify` hace
fallar la prueba si hubo alguna.
"""

import sys
from typing import Any
from urllib.parse import urlsplit

from playwright.sync_api import Browser, BrowserContext, Route

LOCAL_HOSTS = {"127.0.0.1", "localhost"}

external: list[str] = []


def refuse(route: Route) -> None:
    url = route.request.url
    if urlsplit(url).hostname in LOCAL_HOSTS:
        route.fallback()
        return
    external.append(url)
    print(f"✗ petición fuera del equipo: {url}", file=sys.stderr)
    route.abort()


def new_context(browser: Browser, **options: Any) -> BrowserContext:
    context = browser.new_context(**options)
    context.route("**/*", refuse)
    return context


def verify() -> None:
    """Termina con error si algún navegador pidió una dirección que no es local."""
    if external:
        urls = "\n".join(f"  {url}" for url in sorted(set(external)))
        sys.exit(f"Las pruebas pidieron direcciones fuera del equipo:\n{urls}")
