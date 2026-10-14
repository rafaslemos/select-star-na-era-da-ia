#!/usr/bin/env python3
"""Coletor da Tabela FIPE - motos (codigoTipoVeiculo=2).

Sequencia de chamadas (todas POST, form-urlencoded):
  1. ConsultarTabelaDeReferencia        -> meses (Codigo / Mes)
  2. ConsultarMarcas                    -> marcas (Label / Value)
  3. ConsultarModelos (por marca)       -> {"Modelos": [...], "Anos": [...]}
  4. ConsultarAnoModelo (por modelo)    -> anos do modelo ("2008-1" = ano-combustivel)
  5. ConsultarValorComTodosParametros   -> valor FIPE de modelo/ano

Recursos:
  * so biblioteca padrao;
  * controle de taxa (padrao 60 req/min, sem paralelismo);
  * cache em disco de cada resposta (JSON) -> reexecutar retoma de onde parou
    sem repetir requisicoes;
  * filtro de marca (--marca "Royal Enfield" ou --marca 192);
  * --estimar: so conta marcas/modelos/anos (passos 1-4), sem buscar valores.

Uso:
  python coletor_fipe.py --marca "Royal Enfield" --saida amostra_royal_enfield.csv
  python coletor_fipe.py                       # todas as marcas, mes mais recente
  python coletor_fipe.py --tabela 337          # mes de referencia especifico
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://veiculos.fipe.org.br/api/veiculos/"
TIPO_VEICULO = 2          # 1 = carros, 2 = motos, 3 = caminhoes
TIPO_VEICULO_NOME = "moto"  # usado em ConsultarValorComTodosParametros

HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://veiculos.fipe.org.br",
    "referer": "https://veiculos.fipe.org.br/",
    "user-agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"),
    "x-requested-with": "XMLHttpRequest",
}

# Colunas do CSV: contexto da consulta + todos os campos de ConsultarValorComTodosParametros
COLUNAS = [
    "CodigoTabelaReferencia", "CodigoMarca", "CodigoModelo", "AnoCombustivelCodigo",
    "CodigoTipoCombustivel",
    "ZeroKm", "Valor", "ValorNumerico", "Marca", "Modelo", "AnoModelo", "Combustivel", "CodigoFipe",
    "MesReferencia", "Autenticacao", "TipoVeiculo", "SiglaCombustivel", "DataConsulta",
]


class ErroAPI(Exception):
    pass


class ClienteFipe:
    def __init__(self, cache_dir, req_por_min=60, max_tentativas=6, verbose=True):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.intervalo = 60.0 / req_por_min
        self.max_tentativas = max_tentativas
        self.verbose = verbose
        self._ultima = 0.0
        self.n_rede = 0
        self.n_cache = 0
        self.n_429 = 0

    # ---------- cache ----------
    def _caminho_cache(self, endpoint, params):
        chave = endpoint + "?" + urllib.parse.urlencode(sorted(params.items()))
        h = hashlib.sha1(chave.encode("utf-8")).hexdigest()[:16]
        d = os.path.join(self.cache_dir, endpoint)
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, h + ".json")

    # ---------- rede ----------
    def _esperar_vez(self):
        agora = time.monotonic()
        falta = self._ultima + self.intervalo - agora
        if falta > 0:
            time.sleep(falta)
        self._ultima = time.monotonic()

    def post(self, endpoint, params, usar_cache=True):
        caminho = self._caminho_cache(endpoint, params)
        if usar_cache and os.path.exists(caminho):
            with open(caminho, encoding="utf-8") as f:
                self.n_cache += 1
                return json.load(f)["resposta"]

        corpo = urllib.parse.urlencode(params).encode("utf-8")
        espera = 5.0
        retry_after = None
        for tentativa in range(1, self.max_tentativas + 1):
            self._esperar_vez()
            self.n_rede += 1
            req = urllib.request.Request(BASE + endpoint, data=corpo, headers=HEADERS, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    texto = r.read().decode("utf-8")
                dados = json.loads(texto)
            except urllib.error.HTTPError as e:
                msg = f"HTTP {e.code}"
                ra = e.headers.get("Retry-After") if e.headers else None
                if ra and ra.isdigit():
                    retry_after = float(ra)
                    msg += f" (Retry-After={ra})"
                if e.code == 429:
                    self.n_429 += 1
                if e.code in (400, 404):
                    raise ErroAPI(f"{endpoint} {params}: {msg}")
            except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
                msg = f"{type(e).__name__}: {e}"
            else:
                # A API devolve HTTP 200 com {"codigo": "...", "erro": "..."} em caso de erro
                if isinstance(dados, dict) and "erro" in dados:
                    msg = f"erro da API: {dados}"
                    # {"codigo":"2","erro":"Parametros invalidos"} e
                    # {"codigo":"0","erro":"nadaencontrado"} nao se resolvem tentando de novo
                    erro = str(dados.get("erro", "")).lower()
                    if "inv" in erro or "nadaencontrado" in erro:
                        raise ErroAPI(f"{endpoint} {params}: {msg}")
                else:
                    tmp = caminho + ".tmp"
                    with open(tmp, "w", encoding="utf-8") as f:
                        json.dump({"endpoint": endpoint, "params": params, "resposta": dados},
                                  f, ensure_ascii=False)
                    os.replace(tmp, caminho)  # gravacao atomica: retomada segura
                    return dados
            pausa = max(espera, retry_after or 0)
            self._log(f"  ! {endpoint} tentativa {tentativa}/{self.max_tentativas}: {msg}; "
                      f"aguardando {pausa:.0f}s")
            time.sleep(pausa)
            espera = min(espera * 2, 300)
            retry_after = None
        raise ErroAPI(f"{endpoint} {params}: falhou apos {self.max_tentativas} tentativas")

    def _log(self, s):
        if self.verbose:
            print(s, file=sys.stderr, flush=True)

    # ---------- endpoints ----------
    def tabelas_referencia(self):
        # lista muda todo mes: sempre busca na rede (mas grava para registro)
        return self.post("ConsultarTabelaDeReferencia", {}, usar_cache=False)

    def marcas(self, tabela):
        return self.post("ConsultarMarcas", {
            "codigoTabelaReferencia": tabela, "codigoTipoVeiculo": TIPO_VEICULO})

    def modelos(self, tabela, marca):
        return self.post("ConsultarModelos", {
            "codigoTipoVeiculo": TIPO_VEICULO, "codigoTabelaReferencia": tabela,
            "codigoModelo": "", "codigoMarca": marca, "ano": "", "codigoTipoCombustivel": "",
            "anoModelo": "", "modeloCodigoExterno": ""})

    def anos_modelo(self, tabela, marca, modelo):
        return self.post("ConsultarAnoModelo", {
            "codigoTipoVeiculo": TIPO_VEICULO, "codigoTabelaReferencia": tabela,
            "codigoModelo": modelo, "codigoMarca": marca, "ano": "", "codigoTipoCombustivel": "",
            "anoModelo": "", "modeloCodigoExterno": ""})

    def valor(self, tabela, marca, modelo, ano_modelo, combustivel):
        return self.post("ConsultarValorComTodosParametros", {
            "codigoTabelaReferencia": tabela, "codigoMarca": marca, "codigoModelo": modelo,
            "codigoTipoVeiculo": TIPO_VEICULO, "anoModelo": ano_modelo,
            "codigoTipoCombustivel": combustivel, "tipoVeiculo": TIPO_VEICULO_NOME,
            "modeloCodigoExterno": "", "tipoConsulta": "tradicional"})


def valor_numerico(v):
    # "R$ 3.022,00" -> "3022.00"
    s = (v or "").replace("R$", "").strip().replace(".", "").replace(",", ".")
    return s


def filtrar_marcas(marcas, filtro):
    if not filtro:
        return marcas
    f = filtro.strip().lower()
    sel = [m for m in marcas if str(m["Value"]) == f or m["Label"].strip().lower() == f]
    if not sel:
        raise SystemExit(f"Marca '{filtro}' nao encontrada. Opcoes: "
                         + ", ".join(m["Label"] for m in marcas))
    return sel


def estimar_por_amostra(cli, tabela, marcas, n, rpm):
    """Busca modelos de todas as marcas e anos de N modelos sorteados (semente fixa)."""
    import random
    todos = []
    por_marca = {}
    for m in marcas:
        resp = cli.modelos(tabela, m["Value"])
        mods = resp.get("Modelos", []) if isinstance(resp, dict) else []
        por_marca[m["Label"]] = len(mods)
        todos += [(m["Value"], x["Value"]) for x in mods]
    rnd = random.Random(42)
    amostra = rnd.sample(todos, min(n, len(todos)))
    anos = [len(cli.anos_modelo(tabela, mc, md)) for mc, md in amostra]
    media = sum(anos) / len(anos)
    combos = media * len(todos)
    total = 2 + len(marcas) + len(todos) + combos
    top = sorted(por_marca.items(), key=lambda kv: -kv[1])[:10]
    print("---", file=sys.stderr)
    print(f"marcas={len(marcas)} modelos={len(todos)} amostra_modelos={len(amostra)} "
          f"anos_por_modelo_medio={media:.2f}", file=sys.stderr)
    print(f"marcas com mais modelos: {top}", file=sys.stderr)
    print(f"combinacoes modelo/ano estimadas ~ {combos:.0f}", file=sys.stderr)
    print(f"requisicoes estimadas ~ {total:.0f} (2 + {len(marcas)} marcas + {len(todos)} modelos "
          f"+ {combos:.0f} valores) -> ~ {total / rpm / 60:.1f} h a {rpm:.0f} req/min",
          file=sys.stderr)
    print(f"requisicoes nesta estimativa: rede={cli.n_rede} (HTTP 429: {cli.n_429}) "
          f"cache={cli.n_cache}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="Coleta valores FIPE de motos.")
    ap.add_argument("--tabela", type=int, help="codigoTabelaReferencia (padrao: mais recente)")
    ap.add_argument("--marca", action="append",
                    help="filtro de marca (nome ou codigo); pode repetir")
    ap.add_argument("--saida", default="fipe_motos.csv")
    ap.add_argument("--cache", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    "cache_fipe"))
    ap.add_argument("--rpm", type=float, default=60, help="requisicoes por minuto (max 60)")
    ap.add_argument("--estimar", action="store_true",
                    help="nao busca valores: conta marcas e modelos e estima o tamanho da coleta")
    ap.add_argument("--amostra-modelos", type=int, default=0,
                    help="com --estimar: consulta anos so de N modelos sorteados (0 = todos)")
    args = ap.parse_args()
    if args.rpm > 60:
        raise SystemExit("Limite acordado: no maximo 60 requisicoes por minuto.")

    cli = ClienteFipe(args.cache, req_por_min=args.rpm)

    if args.tabela:
        tabela = args.tabela
    else:
        tabelas = cli.tabelas_referencia()
        tabela = max(t["Codigo"] for t in tabelas)  # mais recente (lista nao e ordenada por codigo em anos antigos)
    print(f"Tabela de referencia: {tabela}", file=sys.stderr)

    marcas = cli.marcas(tabela)
    if args.marca:
        sel = []
        for f in args.marca:
            sel += filtrar_marcas(marcas, f)
        marcas = sel
    print(f"Marcas selecionadas: {len(marcas)}", file=sys.stderr)

    n_modelos = n_anos = n_linhas = n_falhas = 0
    escrever = not args.estimar
    if args.estimar and args.amostra_modelos:
        return estimar_por_amostra(cli, tabela, marcas, args.amostra_modelos, args.rpm)
    if escrever:
        fout = open(args.saida, "w", newline="", encoding="utf-8-sig")
        w = csv.DictWriter(fout, fieldnames=COLUNAS)
        w.writeheader()
    try:
        for im, m in enumerate(marcas, 1):
            cod_marca = m["Value"]
            resp = cli.modelos(tabela, cod_marca)
            modelos = resp.get("Modelos", []) if isinstance(resp, dict) else []
            n_modelos += len(modelos)
            print(f"[{im}/{len(marcas)}] {m['Label']} ({cod_marca}): {len(modelos)} modelos",
                  file=sys.stderr, flush=True)
            for mod in modelos:
                cod_modelo = mod["Value"]
                anos = cli.anos_modelo(tabela, cod_marca, cod_modelo)
                n_anos += len(anos)
                if not escrever:
                    continue
                for a in anos:
                    # Value = "<anoModelo>-<codigoTipoCombustivel>", ex. "2008-1", "32000-1" (0 km)
                    ano_modelo, combustivel = a["Value"].split("-", 1)
                    try:
                        v = cli.valor(tabela, cod_marca, cod_modelo, ano_modelo, combustivel)
                    except ErroAPI as e:
                        n_falhas += 1
                        print(f"  ! sem valor: {e}", file=sys.stderr)
                        continue
                    linha = {k: v.get(k, "") for k in COLUNAS}
                    linha.update({
                        "CodigoTabelaReferencia": tabela, "CodigoMarca": cod_marca,
                        "CodigoModelo": cod_modelo, "AnoCombustivelCodigo": a["Value"],
                        "CodigoTipoCombustivel": combustivel,
                        "ValorNumerico": valor_numerico(v.get("Valor")),
                        # anoModelo 32000 e o codigo da FIPE para veiculo 0 km
                        "ZeroKm": "S" if str(ano_modelo) == "32000" else "N",
                    })
                    w.writerow(linha)
                    n_linhas += 1
                    if n_linhas % 50 == 0:
                        fout.flush()
    finally:
        if escrever:
            fout.close()

    print("---", file=sys.stderr)
    print(f"marcas={len(marcas)} modelos={n_modelos} combinacoes_modelo_ano={n_anos} "
          f"linhas_csv={n_linhas} falhas={n_falhas}", file=sys.stderr)
    print(f"requisicoes: rede={cli.n_rede} (HTTP 429: {cli.n_429}) cache={cli.n_cache}",
          file=sys.stderr)
    if args.estimar:
        total = 1 + 1 + len(marcas) + n_modelos + n_anos
        print(f"estimativa coleta completa: {total} requisicoes "
              f"~ {total / args.rpm / 60:.1f} h a {args.rpm:.0f} req/min", file=sys.stderr)


if __name__ == "__main__":
    main()
