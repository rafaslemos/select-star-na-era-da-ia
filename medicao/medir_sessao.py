"""Mede quantos tokens uma sessão do Claude Code gastou, a partir de um marco.

O Claude Code grava cada resposta do modelo (com o `usage`) no transcript
~/.claude/projects/<projeto>/<sessão>.jsonl. Este script soma esse uso.

  python medir_sessao.py marco inicio-fipe       # grava o ponto de partida (agora)
  python medir_sessao.py relatorio inicio-fipe   # tokens gastos desde o marco
  python medir_sessao.py relatorio inicio-fipe --ate fim-fipe
  python medir_sessao.py relatorio --sessao <id> # sessão inteira (outra sessão)

Os marcos ficam em marcos.json, ao lado deste script.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
MARCOS = AQUI / "marcos.json"
PROJETOS = Path.home() / ".claude" / "projects"

# US$ por milhão de tokens. Cache de 1h custa 2x a entrada; de 5 min, 1,25x; leitura, 0,1x.
def _tabela(entrada: float, saida: float) -> dict:
    return {"entrada": entrada, "cache_1h": entrada * 2, "cache_5m": entrada * 1.25,
            "cache_leitura": entrada * 0.1, "saida": saida}


PRECOS = {
    "claude-fable-5-1": _tabela(10.00, 50.00),
    "claude-opus-5-5": _tabela(4.00, 20.00),
    "claude-sonnet-5-5": _tabela(2.00, 10.00),
    "claude-haiku-4-5": _tabela(1.00, 5.00),
}
PRECO_PADRAO = "claude-opus-5-5"


def pasta_do_projeto() -> Path | None:
    """O Claude Code nomeia a pasta do projeto pelo caminho do diretório, trocando símbolos por '-'."""
    atual = Path.cwd().resolve()
    for d in [atual, *atual.parents]:
        nome = "".join(c if c.isalnum() else "-" for c in str(d))
        if (PROJETOS / nome).is_dir():
            return PROJETOS / nome
    return None


def transcript_atual() -> Path:
    """Transcript mais recente do projeto atual (ou de qualquer projeto, se não achar)."""
    pasta = pasta_do_projeto()
    padrao = pasta.glob("*.jsonl") if pasta else PROJETOS.glob("*/*.jsonl")
    arquivos = sorted(padrao, key=lambda p: p.stat().st_mtime)
    if not arquivos:
        sys.exit(f"Nenhum transcript encontrado em {PROJETOS}")
    return arquivos[-1]


def localizar(sessao: str | None) -> Path:
    if not sessao:
        return transcript_atual()
    achados = list(PROJETOS.glob(f"*/{sessao}*.jsonl"))
    if not achados:
        sys.exit(f"Sessão {sessao} não encontrada em {PROJETOS}")
    return achados[0]


def arquivos_da_sessao(principal: Path) -> list[Path]:
    """Transcript principal mais os de subagentes, se houver."""
    pasta = principal.with_suffix("")
    return [principal] + sorted(pasta.glob("**/*.jsonl"))


def ler_marcos() -> dict:
    return json.loads(MARCOS.read_text(encoding="utf-8")) if MARCOS.exists() else {}


def instante(nome: str | None) -> str | None:
    if not nome:
        return None
    marcos = ler_marcos()
    if nome not in marcos:
        sys.exit(f"Marco '{nome}' não existe. Marcos: {', '.join(marcos) or 'nenhum'}")
    return marcos[nome]["timestamp"]


def medir(arquivos: list[Path], desde: str | None, ate: str | None) -> dict:
    respostas: dict[str, dict] = {}   # message.id -> usage (a última entrada tem o uso final)
    saida_max: Counter = Counter()    # message.id -> maior output_tokens visto
    chars_gerados: Counter = Counter()  # message.id -> caracteres de texto + entradas de ferramentas
    modelos: dict[str, str] = {}      # message.id -> modelo que respondeu
    ferramentas = Counter()
    vistos: set[str] = set()
    chars_resultados = 0
    primeiro = ultimo = None

    for arquivo in arquivos:
        for linha in arquivo.open(encoding="utf-8"):
            try:
                o = json.loads(linha)
            except json.JSONDecodeError:
                continue
            ts = o.get("timestamp")
            if not ts or (desde and ts < desde) or (ate and ts > ate):
                continue
            msg = o.get("message") or {}
            if o.get("type") == "assistant" and msg.get("usage"):
                chave = f"{arquivo.name}:{msg.get('id')}"
                respostas[chave] = msg["usage"]
                modelos[chave] = msg.get("model") or PRECO_PADRAO
                saida_max[chave] = max(saida_max[chave], msg["usage"].get("output_tokens", 0))
                for bloco in msg.get("content") or []:
                    if not isinstance(bloco, dict):
                        continue
                    if bloco.get("type") == "tool_use" and bloco.get("id") not in vistos:
                        vistos.add(bloco.get("id"))
                        ferramentas[bloco.get("name")] += 1
                        chars_gerados[chave] += len(json.dumps(bloco.get("input"), ensure_ascii=False))
                    elif bloco.get("type") == "text":
                        chars_gerados[chave] += len(bloco.get("text", ""))
                primeiro = primeiro or ts
                ultimo = ts
            elif o.get("type") == "user" and isinstance(msg.get("content"), list):
                for bloco in msg["content"]:
                    if isinstance(bloco, dict) and bloco.get("type") == "tool_result":
                        conteudo = bloco.get("content")
                        chars_resultados += len(conteudo if isinstance(conteudo, str) else json.dumps(conteudo))

    total = Counter()
    custo = 0.0
    for chave, u in respostas.items():
        criacao = u.get("cache_creation") or {}
        atual = Counter()
        atual["entrada"] = u.get("input_tokens", 0)
        atual["cache_1h"] = criacao.get("ephemeral_1h_input_tokens", 0)
        atual["cache_5m"] = criacao.get("ephemeral_5m_input_tokens", 0)
        if not criacao:
            atual["cache_5m"] += u.get("cache_creation_input_tokens", 0)
        atual["cache_leitura"] = u.get("cache_read_input_tokens", 0)
        atual["saida"] = saida_max[chave]
        atual["raciocinio"] = (u.get("output_tokens_details") or {}).get("thinking_tokens", 0)
        # Transcripts de subagente gravam o output_tokens do início do streaming (8, 16...).
        # Quando isso acontece, estimamos pelo texto gerado: ~3,5 caracteres por token.
        atual["saida_estimada"] = max(saida_max[chave], round(chars_gerados[chave] / 3.5))
        total.update(atual)

        precos = PRECOS.get(modelos[chave], PRECOS[PRECO_PADRAO])
        custo += sum((atual["saida_estimada"] if k == "saida" else atual[k]) * precos[k] for k in precos) / 1_000_000
    duracao = None
    if primeiro and ultimo:
        lerts = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
        inicio = lerts(desde) if desde else lerts(primeiro)
        duracao = round((lerts(ultimo) - inicio).total_seconds())
    return {
        "duracao_segundos": duracao,
        "chamadas_ao_modelo": len(respostas),
        "tokens": dict(total),
        "custo_usd": round(custo, 4),
        "modelos": dict(Counter(modelos.values())),
        "ferramentas": dict(ferramentas.most_common()),
        "chars_resultados_ferramentas": chars_resultados,
        "primeira_resposta": primeiro,
        "ultima_resposta": ultimo,
    }


def imprimir(r: dict, titulo: str):
    t = r["tokens"]
    fmt = lambda n: f"{n:>12,}".replace(",", ".")
    print(f"\n{titulo}\n{'-' * len(titulo)}")
    if r.get("duracao_segundos") is not None:
        m, s = divmod(r["duracao_segundos"], 60)
        print(f"Duração (marco → última resposta)   {m} min {s:02d} s")
    print(f"Chamadas ao modelo     {fmt(r['chamadas_ao_modelo'])}")
    print(f"Entrada (sem cache)    {fmt(t.get('entrada', 0))}")
    print(f"Escrita de cache       {fmt(t.get('cache_1h', 0) + t.get('cache_5m', 0))}")
    print(f"Leitura de cache       {fmt(t.get('cache_leitura', 0))}")
    print(f"Saída registrada       {fmt(t.get('saida', 0))}   (raciocínio: {t.get('raciocinio', 0):,})".replace(",", "."))
    if t.get("saida_estimada", 0) > t.get("saida", 0):
        print(f"Saída estimada         {fmt(t.get('saida_estimada', 0))}   (texto gerado ÷ 3,5; sem raciocínio)")
    total = sum(t.get(k, 0) for k in ("entrada", "cache_1h", "cache_5m", "cache_leitura", "saida_estimada"))
    print(f"Total processado       {fmt(total)}")
    modelos = ", ".join(f"{m} x{n}" for m, n in r.get("modelos", {}).items())
    print(f"Custo estimado (US$)   {r['custo_usd']:>12.4f}   ({modelos or 'sem respostas'})")
    print(f"Resultados de ferramentas: {r['chars_resultados_ferramentas']:,} caracteres".replace(",", "."))
    if r["ferramentas"]:
        print("Ferramentas usadas: " + ", ".join(f"{k} x{v}" for k, v in r["ferramentas"].items()))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("marco", help="Grava um marco com o instante atual")
    m.add_argument("nome")
    m.add_argument("--nota", default="")
    r = sub.add_parser("relatorio", help="Soma o uso desde um marco")
    r.add_argument("desde", nargs="?")
    r.add_argument("--ate")
    r.add_argument("--sessao", help="ID da sessão (padrão: a mais recente)")
    r.add_argument("--salvar", help="Salva o relatório em JSON com este nome")
    r.add_argument("--apenas-subagentes", action="store_true",
                   help="Ignora a conversa principal e soma só os transcripts de subagentes")
    args = p.parse_args()

    if args.cmd == "marco":
        marcos = ler_marcos()
        marcos[args.nome] = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "sessao": transcript_atual().stem,
            "nota": args.nota,
        }
        MARCOS.write_text(json.dumps(marcos, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Marco '{args.nome}' gravado: {marcos[args.nome]['timestamp']}")
        return

    sessao = args.sessao or (ler_marcos().get(args.desde, {}).get("sessao") if args.desde else None)
    principal = localizar(sessao)
    arquivos = arquivos_da_sessao(principal)
    if args.apenas_subagentes:
        arquivos = arquivos[1:]
        if not arquivos:
            sys.exit("Nenhum transcript de subagente encontrado nesta sessão.")
    resultado = medir(arquivos, instante(args.desde), instante(args.ate))
    titulo = f"Sessão {principal.stem[:8]}" + (" · só subagentes" if args.apenas_subagentes else "") \
        + (f" desde '{args.desde}'" if args.desde else " (inteira)")
    imprimir(resultado, titulo)
    if args.salvar:
        destino = AQUI / f"{args.salvar}.json"
        destino.write_text(json.dumps({"desde": args.desde, "ate": args.ate, **resultado},
                                      ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nSalvo em {destino.name}")


if __name__ == "__main__":
    main()
