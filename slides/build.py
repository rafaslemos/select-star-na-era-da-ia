"""Gera apps-script/Index.html: o deck num arquivo único para o Google Apps Script.

O HtmlService do Apps Script não serve arquivos estáticos, então o tokens.css
entra inline e as imagens viram data URI. Rode depois de editar index.html:

    python build.py
"""

import base64
import re
from pathlib import Path

AQUI = Path(__file__).parent


def main():
    html = (AQUI / "index.html").read_text(encoding="utf-8")

    tokens = (AQUI / "assets" / "tokens.css").read_text(encoding="utf-8")
    html, n = re.subn(r"<!-- build:tokens -->.*?<!-- /build:tokens -->",
                      lambda _: f"<style>\n{tokens}</style>", html, flags=re.S)
    assert n == 1, "marcador build:tokens não encontrado em index.html"

    def embutir(m):
        arquivo = AQUI / m.group(1)
        dados = base64.b64encode(arquivo.read_bytes()).decode("ascii")
        return f'src="data:image/png;base64,{dados}"'

    html = re.sub(r'src="(assets/[^"]+\.png)"', embutir, html)

    destino = AQUI / "apps-script" / "Index.html"
    destino.write_text(html, encoding="utf-8")
    print(f"{destino.relative_to(AQUI)}: {len(html) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
