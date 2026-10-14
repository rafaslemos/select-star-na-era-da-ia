#!/usr/bin/env python3
"""
Coletor da Tabela FIPE (motos por padrao) - so biblioteca padrao.

Fluxo de chamadas (todas POST form-urlencoded em https://veiculos.fipe.org.br/api/veiculos/):
  1. ConsultarTabelaDeReferencia                     -> meses de referencia (Codigo, Mes)
  2. ConsultarMarcas      (tabela, tipo)             -> marcas (Label, Value)
  3. ConsultarModelos     (tabela, tipo, marca)      -> {"Modelos": [...], "Anos": [...]}
  4. ConsultarAnoModelo   (tabela, tipo, marca, modelo) -> anos do modelo ("2026-1", "32000-1"...)
  5. ConsultarValorComTodosParametros (tabela, tipo, marca, modelo, anoModelo,
                                       codigoTipoCombustivel, tipoConsulta=tradicional) -> valor

Recursos:
  - controle de taxa (intervalo minimo entre requisicoes; nunca menor que 0,5 s = 2 req/s)
  - cache em disco de cada resposta (chave = endpoint + parametros); re-execucoes nao
    repetem requisicoes ja feitas -> retomada automatica apos interrupcao
  - CSV gravado incrementalmente em <saida>.parcial e renomeado ao final
  - filtro de marca (--marca, por codigo ou nome, pode repetir)
  - modo --estimar: conta marcas/modelos e projeta o tamanho da coleta completa

Exemplos:
  python coletor_fipe.py --marca "Royal Enfield" --saida amostra_royal_enfield.csv
  python coletor_fipe.py --estimar
  python coletor_fipe.py --saida motos_completo.csv           # coleta completa
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://veiculos.fipe.org.br/api/veiculos/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (coletor_fipe.py; uso educacional)",
    "Referer": "https://veiculos.fipe.org.br/",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept": "application/json",
}
TIPOS = {1: "carro", 2: "moto", 3: "caminhao"}
INTERVALO_MINIMO = 0.5  # 2 req/s, limite combinado
CAMPOS_VALOR = ["Valor", "Marca", "Modelo", "AnoModelo", "Combustivel", "CodigoFipe",
                "MesReferencia", "Autenticacao", "TipoVeiculo", "SiglaCombustivel", "DataConsulta"]
COLUNAS_CSV = (["codigoTabelaReferencia", "mesTabelaReferencia", "codigoTipoVeiculo",
                "codigoMarca", "codigoModelo", "anoCodigo", "codigoTipoCombustivel"]
               + CAMPOS_VALOR + ["ValorNumerico"])


class ErroApi(Exception):
    pass


class ClienteFipe:
    def __init__(self, cache_dir, intervalo=0.6, verbose=True):
        self.cache_dir = cache_dir
        self.intervalo = max(intervalo, INTERVALO_MINIMO)
        self.verbose = verbose
        self._ultima = 0.0
        self.stats = {"rede": 0, "cache": 0, "retentativas": 0}
        os.makedirs(cache_dir, exist_ok=True)

    # ---------- cache ----------
    def _caminho_cache(self, endpoint, params):
        chave = json.dumps(params, sort_keys=True, ensure_ascii=False)
        h = hashlib.sha1(chave.encode("utf-8")).hexdigest()[:16]
        pasta = os.path.join(self.cache_dir, endpoint)
        os.makedirs(pasta, exist_ok=True)
        return os.path.join(pasta, h + ".json")

    # ---------- rede ----------
    def _esperar_vez(self):
        falta = self.intervalo - (time.monotonic() - self._ultima)
        if falta > 0:
            time.sleep(falta)
        self._ultima = time.monotonic()

    def _post(self, endpoint, params):
        corpo = urllib.parse.urlencode(params).encode("utf-8")
        espera = 5
        for tentativa in range(1, 7):
            self._esperar_vez()
            self.stats["rede"] += 1
            req = urllib.request.Request(BASE_URL + endpoint, data=corpo, headers=HEADERS, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=40) as r:
                    texto = r.read().decode("utf-8")
                dados = json.loads(texto)
            except urllib.error.HTTPError as e:
                motivo = f"HTTP {e.code}"
                if e.code not in (429, 500, 502, 503, 504, 520, 521, 522, 524):
                    raise ErroApi(f"{endpoint} {params}: {motivo}")
                if e.code == 429:
                    self.stats["http429"] = self.stats.get("http429", 0) + 1
                    # freio adaptativo: cada 429 deixa o ritmo 15% mais lento (teto 3 s)
                    self.intervalo = min(self.intervalo * 1.15, 3.0)
                    ra = e.headers.get("Retry-After")
                    if ra and ra.isdigit():
                        espera = max(espera, int(ra))
                        motivo += f" Retry-After={ra}"
            except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
                motivo = repr(e)
            else:
                # A API responde HTTP 200 mesmo em erro, com {"codigo": "...", "erro": "..."}
                if isinstance(dados, dict) and "erro" in dados:
                    cod = str(dados.get("codigo"))
                    if cod == "0":          # "nadaencontrado": resposta legitima e vazia
                        return dados
                    if cod == "99":         # limite de pesquisas da sessao
                        motivo = "codigo 99 (limite de pesquisas)"
                        espera = max(espera, 60)
                    else:                   # 2 = parametros invalidos, 3 = codigo fipe invalido
                        raise ErroApi(f"{endpoint} {params}: {dados}")
                else:
                    return dados
            self.stats["retentativas"] += 1
            self._log(f"  ! {endpoint} falhou ({motivo}); tentativa {tentativa}, aguardando {espera}s")
            time.sleep(espera)
            espera = min(espera * 2, 300)
        raise ErroApi(f"{endpoint} {params}: falhou apos varias tentativas")

    def chamar(self, endpoint, **params):
        caminho = self._caminho_cache(endpoint, params)
        if os.path.exists(caminho):
            self.stats["cache"] += 1
            with open(caminho, encoding="utf-8") as f:
                return json.load(f)["resposta"]
        dados = self._post(endpoint, params)
        tmp = caminho + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"endpoint": endpoint, "params": params, "resposta": dados,
                       "obtido_em": time.strftime("%Y-%m-%dT%H:%M:%S")}, f, ensure_ascii=False)
        os.replace(tmp, caminho)
        return dados

    def _log(self, msg):
        if self.verbose:
            print(msg, file=sys.stderr, flush=True)

    # ---------- endpoints ----------
    def tabelas(self):
        return self.chamar("ConsultarTabelaDeReferencia")

    def marcas(self, tabela, tipo):
        return self.chamar("ConsultarMarcas", codigoTabelaReferencia=tabela, codigoTipoVeiculo=tipo)

    def modelos(self, tabela, tipo, marca):
        r = self.chamar("ConsultarModelos", codigoTabelaReferencia=tabela, codigoTipoVeiculo=tipo,
                        codigoMarca=marca)
        return r if isinstance(r, dict) and "Modelos" in r else {"Modelos": [], "Anos": []}

    def anos(self, tabela, tipo, marca, modelo):
        r = self.chamar("ConsultarAnoModelo", codigoTabelaReferencia=tabela, codigoTipoVeiculo=tipo,
                        codigoMarca=marca, codigoModelo=modelo)
        return r if isinstance(r, list) else []

    def valor(self, tabela, tipo, marca, modelo, ano_modelo, combustivel):
        r = self.chamar("ConsultarValorComTodosParametros", codigoTabelaReferencia=tabela,
                        codigoTipoVeiculo=tipo, codigoMarca=marca, codigoModelo=modelo,
                        anoModelo=ano_modelo, codigoTipoCombustivel=combustivel,
                        tipoConsulta="tradicional")
        return r if isinstance(r, dict) and "Valor" in r else None


def normalizar(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.strip().lower()


def valor_numerico(txt):
    # "R$ 58.860,00" -> 58860.00
    try:
        return f"{float(txt.replace('R$', '').strip().replace('.', '').replace(',', '.')):.2f}"
    except (AttributeError, ValueError):
        return ""


def escolher_tabela(cli, codigo):
    tabs = cli.tabelas()
    if codigo is None:
        t = tabs[0]  # a API devolve do mais recente para o mais antigo
    else:
        t = next((x for x in tabs if x["Codigo"] == codigo), None)
        if t is None:
            sys.exit(f"Tabela de referencia {codigo} nao existe.")
    return t["Codigo"], t["Mes"].strip()


def filtrar_marcas(marcas, filtros):
    if not filtros:
        return marcas
    alvo = {normalizar(f) for f in filtros}
    sel = [m for m in marcas if normalizar(m["Value"]) in alvo or normalizar(m["Label"]) in alvo]
    if not sel:
        sys.exit(f"Nenhuma marca corresponde a {filtros}.")
    return sel


def coletar(cli, tabela, mes, tipo, marcas, saida):
    parcial = saida + ".parcial"
    total_linhas = 0
    with open(parcial, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS_CSV)
        w.writeheader()
        for i, m in enumerate(marcas, 1):
            cod_marca = m["Value"]
            mods = cli.modelos(tabela, tipo, cod_marca)["Modelos"]
            cli._log(f"[{i}/{len(marcas)}] {m['Label']} ({cod_marca}): {len(mods)} modelos")
            for j, mod in enumerate(mods, 1):
                cod_modelo = mod["Value"]
                for ano in cli.anos(tabela, tipo, cod_marca, cod_modelo):
                    ano_modelo, comb = ano["Value"].split("-")
                    v = cli.valor(tabela, tipo, cod_marca, cod_modelo, ano_modelo, comb)
                    if v is None:
                        cli._log(f"    sem valor: modelo {cod_modelo} ano {ano['Value']}")
                        continue
                    linha = {"codigoTabelaReferencia": tabela, "mesTabelaReferencia": mes,
                             "codigoTipoVeiculo": tipo, "codigoMarca": cod_marca,
                             "codigoModelo": cod_modelo, "anoCodigo": ano["Value"],
                             "codigoTipoCombustivel": comb}
                    linha.update({k: (v.get(k).strip() if isinstance(v.get(k), str) else v.get(k))
                                  for k in CAMPOS_VALOR})
                    linha["ValorNumerico"] = valor_numerico(v.get("Valor"))
                    w.writerow(linha)
                    total_linhas += 1
                f.flush()
                if j % 10 == 0:
                    cli._log(f"    {j}/{len(mods)} modelos | linhas={total_linhas} | {cli.stats}")
    os.replace(parcial, saida)
    return total_linhas


def estimar(cli, tabela, tipo, marcas, combos_por_modelo, intervalo, amostra_anos=0):
    total_modelos = 0
    todos = []  # (marca, modelo)
    for i, m in enumerate(marcas, 1):
        mods = cli.modelos(tabela, tipo, m["Value"])["Modelos"]
        total_modelos += len(mods)
        todos += [(m["Value"], x["Value"]) for x in mods]
        if i % 20 == 0:
            cli._log(f"  {i}/{len(marcas)} marcas, {total_modelos} modelos ate agora")
    if amostra_anos:
        # amostra aleatoria (semente fixa) de modelos de todas as marcas -> fator anos/modelo
        import random
        sel = random.Random(42).sample(todos, min(amostra_anos, len(todos)))
        qtds = []
        for k, (mc, md) in enumerate(sel, 1):
            qtds.append(len(cli.anos(tabela, tipo, mc, md)))
            if k % 25 == 0:
                cli._log(f"  amostra de anos: {k}/{len(sel)}")
        combos_por_modelo = sum(qtds) / len(qtds)
        cli._log(f"fator anos/modelo na amostra aleatoria de {len(qtds)} modelos: {combos_por_modelo:.2f}")
    combos = round(total_modelos * combos_por_modelo)
    req = 1 + 1 + len(marcas) + total_modelos + combos
    print(f"marcas={len(marcas)} modelos={total_modelos} "
          f"combinacoes_estimadas={combos} (fator {combos_por_modelo:.2f} por modelo)")
    for rotulo, seg_req in ((f"taxa nominal ({1/intervalo:.2f} req/s)", intervalo),
                            ("taxa teto 2 req/s", 0.5),
                            ("taxa efetiva observada ~0,9 req/s (com 429)", 1.11)):
        print(f"requisicoes_estimadas={req} tempo={req*seg_req/3600:.1f} h  [{rotulo}]")


def main():
    ap = argparse.ArgumentParser(description="Coletor da Tabela FIPE (motos por padrao).")
    ap.add_argument("--tipo", type=int, default=2, choices=TIPOS,
                    help="1=carro, 2=moto (padrao), 3=caminhao")
    ap.add_argument("--tabela", type=int, default=None,
                    help="codigo da tabela de referencia (padrao: a mais recente)")
    ap.add_argument("--marca", action="append", default=[],
                    help="filtra por marca (codigo ou nome); pode repetir")
    ap.add_argument("--saida", default=None, help="arquivo CSV de saida")
    ap.add_argument("--cache-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache"))
    ap.add_argument("--intervalo", type=float, default=0.6,
                    help=f"segundos entre requisicoes (minimo {INTERVALO_MINIMO})")
    ap.add_argument("--estimar", action="store_true",
                    help="so conta marcas/modelos e projeta o tamanho da coleta completa")
    ap.add_argument("--combos-por-modelo", type=float, default=None,
                    help="fator ano/modelo para a estimativa (padrao: medido no cache da amostra)")
    ap.add_argument("--amostra-anos", type=int, default=0,
                    help="no --estimar, consulta os anos de N modelos aleatorios para medir o fator")
    ap.add_argument("--quieto", action="store_true")
    a = ap.parse_args()

    cli = ClienteFipe(a.cache_dir, a.intervalo, verbose=not a.quieto)
    tabela, mes = escolher_tabela(cli, a.tabela)
    marcas = filtrar_marcas(cli.marcas(tabela, a.tipo), a.marca)
    cli._log(f"Tabela {tabela} ({mes}), tipo {a.tipo}={TIPOS[a.tipo]}, {len(marcas)} marca(s)")

    t0 = time.time()
    if a.estimar:
        fator = a.combos_por_modelo
        if fator is None:
            # mede o fator anos/modelo nas respostas ja cacheadas para esta tabela/tipo
            pasta = os.path.join(a.cache_dir, "ConsultarAnoModelo")
            qtds = []
            for nome in (os.listdir(pasta) if os.path.isdir(pasta) else []):
                with open(os.path.join(pasta, nome), encoding="utf-8") as f:
                    d = json.load(f)
                if (str(d["params"]["codigoTabelaReferencia"]) == str(tabela)
                        and str(d["params"]["codigoTipoVeiculo"]) == str(a.tipo)
                        and isinstance(d["resposta"], list)):
                    qtds.append(len(d["resposta"]))
            fator = (sum(qtds) / len(qtds)) if qtds else 5.0
            cli._log(f"fator anos/modelo medido em {len(qtds)} modelos do cache: {fator:.2f}")
        estimar(cli, tabela, a.tipo, marcas, fator, cli.intervalo, a.amostra_anos)
    else:
        saida = a.saida or f"fipe_{TIPOS[a.tipo]}_{tabela}.csv"
        n = coletar(cli, tabela, mes, a.tipo, marcas, saida)
        print(f"OK: {n} linhas em {saida}")
    print(f"requisicoes: rede={cli.stats['rede']} cache={cli.stats['cache']} "
          f"retentativas={cli.stats['retentativas']} | tempo {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
