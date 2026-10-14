#!/usr/bin/env python3
"""Coletor da Tabela FIPE (motos por padrão) - só biblioteca padrão.

Fluxo: ConsultarTabelaDeReferencia -> ConsultarMarcas -> ConsultarModelos
       -> ConsultarAnoModelo -> ConsultarValorComTodosParametros

Recursos:
  * controle de taxa (padrão 60 req/min, nunca acima), sequencial, sem paralelismo
  * cache em disco de cada resposta válida (chave = endpoint + parâmetros)
  * retomada: ao rodar de novo, tudo que já está no cache não é requisitado
  * CSV com uma linha por modelo/ano, com todas as colunas devolvidas pela API

Exemplos:
  python coletor_fipe.py --marca "Royal Enfield" --saida amostra_royal_enfield.csv
  python coletor_fipe.py --saida motos_completo.csv            # coleta completa
  python coletor_fipe.py --estimar 60                           # estima tamanho da coleta
"""
import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://veiculos.fipe.org.br/api/veiculos/"
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (coletor_fipe.py)",
    "Referer": "https://veiculos.fipe.org.br/",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}
TIPOS = {"carro": 1, "moto": 2, "caminhao": 3}
MAX_RPM = 60


class ErroFipe(Exception):
    pass


class ClienteFipe:
    def __init__(self, cache_dir, rpm=MAX_RPM, verbose=True):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.intervalo_base = 60.0 / min(rpm, MAX_RPM)
        self.intervalo = self.intervalo_base
        self.ok_seguidos = 0
        self.n_429 = 0
        self.ultimo = 0.0
        self.verbose = verbose
        self.n_rede = 0
        self.n_cache = 0

    def _arquivo(self, endpoint, params):
        chave = endpoint + "?" + urllib.parse.urlencode(sorted(params.items()))
        h = hashlib.sha1(chave.encode()).hexdigest()[:16]
        return os.path.join(self.cache_dir, f"{endpoint}_{h}.json"), chave

    def _esperar(self):
        falta = self.intervalo - (time.monotonic() - self.ultimo)
        if falta > 0:
            time.sleep(falta)
        self.ultimo = time.monotonic()

    def post(self, endpoint, params, usar_cache=True):
        arq, chave = self._arquivo(endpoint, params)
        if usar_cache and os.path.exists(arq):
            with open(arq, encoding="utf-8") as f:
                self.n_cache += 1
                return json.load(f)["resposta"]
        corpo = urllib.parse.urlencode(params).encode()
        for tentativa in range(6):
            self._esperar()
            self.n_rede += 1
            try:
                req = urllib.request.Request(BASE + endpoint, data=corpo, headers=HEADERS, method="POST")
                with urllib.request.urlopen(req, timeout=60) as r:
                    bruto = r.read()
                try:
                    texto = bruto.decode("utf-8")
                except UnicodeDecodeError:  # mensagens de erro vêm em latin-1
                    texto = bruto.decode("latin-1")
                dados = json.loads(texto)
            except urllib.error.HTTPError as e:
                espera = 2 ** tentativa * 5
                if e.code == 429 or e.code >= 500:
                    ra = e.headers.get("Retry-After")
                    espera = max(espera, int(ra) if ra and ra.isdigit() else 0)
                    if e.code == 429:  # desacelera 20% (volta ao normal aos poucos)
                        self.n_429 += 1
                        self.intervalo = min(self.intervalo * 1.2, 10.0)
                        self.ok_seguidos = 0
                    self._log(f"  HTTP {e.code} em {endpoint} (Retry-After={ra}); aguardando {espera}s; "
                              f"intervalo agora {self.intervalo:.2f}s")
                    time.sleep(espera)
                    continue
                raise ErroFipe(f"HTTP {e.code} em {chave}")
            except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
                espera = 2 ** tentativa * 5
                self._log(f"  falha de rede/parse em {endpoint} ({e}); aguardando {espera}s")
                time.sleep(espera)
                continue
            # A API devolve erro com HTTP 200: {"codigo":"2","erro":"Parâmetros inválidos"}
            if isinstance(dados, dict) and "erro" in dados:
                raise ErroFipe(f"{dados.get('erro')} (codigo {dados.get('codigo')}) em {chave}")
            self.ok_seguidos += 1
            if self.ok_seguidos >= 50 and self.intervalo > self.intervalo_base:
                self.intervalo = max(self.intervalo_base, self.intervalo / 1.1)
                self.ok_seguidos = 0
            tmp = arq + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"chave": chave, "resposta": dados}, f, ensure_ascii=False)
            os.replace(tmp, arq)  # gravação atômica: retomada segura
            return dados
        raise ErroFipe(f"desisti após várias tentativas: {chave}")

    def _log(self, msg):
        if self.verbose:
            print(msg, file=sys.stderr, flush=True)

    # --- endpoints ---------------------------------------------------------
    def tabelas(self):
        # sem cache: é o que diz qual é o mês vigente (1 requisição por execução)
        return self.post("ConsultarTabelaDeReferencia", {}, usar_cache=False)

    def marcas(self, tab, tipo):
        return self.post("ConsultarMarcas", {"codigoTabelaReferencia": tab, "codigoTipoVeiculo": tipo})

    def modelos(self, tab, tipo, marca):
        return self.post("ConsultarModelos", {"codigoTipoVeiculo": tipo, "codigoTabelaReferencia": tab,
                                              "codigoMarca": marca})["Modelos"]

    def anos(self, tab, tipo, marca, modelo):
        return self.post("ConsultarAnoModelo", {"codigoTipoVeiculo": tipo, "codigoTabelaReferencia": tab,
                                                "codigoMarca": marca, "codigoModelo": modelo})

    def valor(self, tab, tipo, marca, modelo, ano_comb):
        ano, comb = ano_comb.split("-")
        nome_tipo = {v: k for k, v in TIPOS.items()}[tipo]
        return self.post("ConsultarValorComTodosParametros", {
            "codigoTabelaReferencia": tab, "codigoMarca": marca, "codigoModelo": modelo,
            "codigoTipoVeiculo": tipo, "anoModelo": ano, "codigoTipoCombustivel": comb,
            "tipoVeiculo": nome_tipo, "tipoConsulta": "tradicional"})


def escolher_tabela(cli, mes):
    tabs = cli.tabelas()
    if mes in (None, "", "atual"):
        t = max(tabs, key=lambda x: x["Codigo"])
    else:
        t = next((x for x in tabs if str(x["Codigo"]) == str(mes) or x["Mes"].strip().lower() == mes.lower()), None)
        if not t:
            raise SystemExit(f"Mês de referência não encontrado: {mes}")
    return t["Codigo"], t["Mes"].strip()


def filtrar_marcas(marcas, filtro):
    if not filtro:
        return marcas
    f = filtro.strip().lower()
    sel = [m for m in marcas if m["Value"] == filtro or m["Label"].strip().lower() == f]
    sel = sel or [m for m in marcas if f in m["Label"].lower()]
    if not sel:
        raise SystemExit(f"Nenhuma marca casa com '{filtro}'")
    return sel


CAMPOS_API = ["Valor", "Marca", "Modelo", "AnoModelo", "Combustivel", "CodigoFipe", "MesReferencia",
              "Autenticacao", "TipoVeiculo", "SiglaCombustivel", "DataConsulta"]
CAMPOS_EXTRA = ["CodigoTabelaReferencia", "CodigoMarca", "CodigoModelo", "AnoCombustivel",
                "CodigoTipoCombustivel", "ZeroKm", "ValorNumerico"]


def coletar(cli, tab, tipo, marcas, saida):
    linhas, erros = [], []
    for i, mc in enumerate(marcas, 1):
        mods = cli.modelos(tab, tipo, mc["Value"])
        cli._log(f"[{i}/{len(marcas)}] {mc['Label']}: {len(mods)} modelos")
        for j, mo in enumerate(mods, 1):
            try:
                anos = cli.anos(tab, tipo, mc["Value"], mo["Value"])
            except ErroFipe as e:
                erros.append(str(e)); continue
            for a in anos:
                try:
                    v = cli.valor(tab, tipo, mc["Value"], mo["Value"], a["Value"])
                except ErroFipe as e:
                    erros.append(str(e)); continue
                ano, comb = a["Value"].split("-")
                lin = {k: v.get(k) for k in CAMPOS_API}
                for k in v:  # qualquer coluna nova que a API passe a devolver
                    lin.setdefault(k, v[k])
                lin.update({
                    "CodigoTabelaReferencia": tab, "CodigoMarca": mc["Value"], "CodigoModelo": mo["Value"],
                    "AnoCombustivel": a["Value"], "CodigoTipoCombustivel": comb,
                    "ZeroKm": ano == "32000",
                    "ValorNumerico": float(v["Valor"].replace("R$", "").strip().replace(".", "").replace(",", ".")),
                    "MesReferencia": (v.get("MesReferencia") or "").strip(),
                })
                linhas.append(lin)
            cli._log(f"    {j}/{len(mods)} {mo['Label'].strip()}: {len(anos)} anos "
                     f"(rede={cli.n_rede}, cache={cli.n_cache})")
    campos = CAMPOS_API + [k for k in (linhas[0] if linhas else {}) if k not in CAMPOS_API + CAMPOS_EXTRA] + CAMPOS_EXTRA
    with open(saida, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()
        w.writerows(linhas)
    return linhas, erros


def estimar(cli, tab, tipo, marcas, n_amostra, rpm):
    total_mod, todos = 0, []
    for mc in marcas:
        mods = cli.modelos(tab, tipo, mc["Value"])
        total_mod += len(mods)
        todos += [(mc["Value"], m["Value"]) for m in mods]
    random.seed(42)
    amostra = random.sample(todos, min(n_amostra, len(todos)))
    n_anos = [len(cli.anos(tab, tipo, mc, mo)) for mc, mo in amostra]
    media = sum(n_anos) / len(n_anos)
    combos = round(media * total_mod)
    reqs = 1 + 1 + len(marcas) + total_mod + combos
    print(json.dumps({
        "marcas": len(marcas), "modelos": total_mod, "amostra_modelos": len(amostra),
        "media_anos_por_modelo": round(media, 2), "combinacoes_modelo_ano_estimadas": combos,
        "requisicoes_estimadas": reqs, "horas_a_%d_rpm" % rpm: round(reqs / rpm / 60, 2),
    }, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tipo", choices=TIPOS, default="moto")
    ap.add_argument("--mes", default="atual", help="código da tabela (ex: 338), 'outubro/2026' ou 'atual'")
    ap.add_argument("--marca", help="filtro de marca: código ou nome (exato ou parte)")
    ap.add_argument("--saida", default="fipe_motos.csv")
    ap.add_argument("--cache", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache_fipe"))
    ap.add_argument("--rpm", type=int, default=MAX_RPM, help="requisições por minuto (máx 60)")
    ap.add_argument("--estimar", type=int, metavar="N", help="só estima o tamanho, amostrando N modelos")
    a = ap.parse_args()

    tipo = TIPOS[a.tipo]
    cli = ClienteFipe(a.cache, a.rpm)
    tab, mes = escolher_tabela(cli, a.mes)
    cli._log(f"Tabela de referência: {tab} ({mes})")
    marcas = filtrar_marcas(cli.marcas(tab, tipo), a.marca)
    t0 = time.time()
    if a.estimar:
        estimar(cli, tab, tipo, marcas, a.estimar, min(a.rpm, MAX_RPM))
    else:
        linhas, erros = coletar(cli, tab, tipo, marcas, a.saida)
        cli._log(f"OK: {len(linhas)} linhas em {a.saida}; erros={len(erros)}")
        for e in erros:
            cli._log("  ERRO " + e)
    cli._log(f"Requisições: rede={cli.n_rede} (429={cli.n_429}), cache={cli.n_cache}, tempo={time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
