#!/usr/bin/env python3
"""Coletor da Tabela FIPE (motos, carros ou caminhoes) - somente biblioteca padrao.

Uso:
  python coletor_fipe.py                       # coleta completa do mes mais recente
  python coletor_fipe.py --marca "Royal Enfield" --csv amostra_royal_enfield.csv
  python coletor_fipe.py --estimar             # conta marcas/modelos e sorteia 60 modelos
  python coletor_fipe.py --tabela 338          # mes de referencia especifico
  python coletor_fipe.py --tipo carro --estimar  # carros (ou --tipo caminhao); padrao: moto

Controle de taxa: no maximo 1 requisicao por segundo (60/min), sequencial.
Cache em disco: uma resposta valida por arquivo JSON; erros nunca sao gravados.
Retomada: basta rodar de novo; o que ja esta no cache nao e requisitado.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import random
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://veiculos.fipe.org.br/api/veiculos/"
# tipo -> (codigoTipoVeiculo, tipoVeiculo usado na consulta de valor)
TIPOS = {"carro": (1, "carro"), "moto": (2, "moto"), "caminhao": (3, "caminhao")}
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://veiculos.fipe.org.br",
    "Referer": "https://veiculos.fipe.org.br/",
    "User-Agent": "Mozilla/5.0 (coletor_fipe.py; estudo)",
}
COLUNAS = ["codigo_tabela_referencia", "mes_referencia", "tipo_veiculo", "codigo_marca", "marca",
           "codigo_modelo", "modelo", "ano_codigo", "ano_modelo", "zero_km", "codigo_combustivel",
           "combustivel", "sigla_combustivel", "codigo_fipe", "valor", "valor_numerico",
           "autenticacao", "data_consulta"]


class ErroFipe(Exception):
    pass


class Cliente:
    def __init__(self, cache_dir, intervalo=1.0, tentativas=8, tipo="moto"):
        self.tipo_cod, self.tipo_str = TIPOS[tipo]
        self.cache_dir = cache_dir
        self.intervalo = intervalo
        self.tentativas = tentativas
        self._ultima = 0.0
        self.stats = {"http": 0, "cache": 0, "429": 0, "erros": 0}
        os.makedirs(cache_dir, exist_ok=True)

    def _arquivo(self, endpoint, params, chave_extra=""):
        corpo = urllib.parse.urlencode(sorted(params.items()))
        h = hashlib.sha1(f"{endpoint}?{corpo}{chave_extra}".encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{endpoint}_{h}.json")

    def _esperar(self):
        falta = self.intervalo - (time.monotonic() - self._ultima)
        if falta > 0:
            time.sleep(falta)
        self._ultima = time.monotonic()

    def post(self, endpoint, params, chave_extra=""):
        arq = self._arquivo(endpoint, params, chave_extra)
        if os.path.exists(arq):
            self.stats["cache"] += 1
            with open(arq, encoding="utf-8") as f:
                return json.load(f)
        dados = urllib.parse.urlencode(params).encode()
        ultimo_erro = None
        for tentativa in range(1, self.tentativas + 1):
            self._esperar()
            self.stats["http"] += 1
            try:
                req = urllib.request.Request(BASE + endpoint, data=dados, headers=HEADERS, method="POST")
                with urllib.request.urlopen(req, timeout=30) as r:
                    texto = r.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    self.stats["429"] += 1
                    time.sleep(random.uniform(5, 10))
                else:
                    time.sleep(min(60, 5 * tentativa))
                ultimo_erro = f"HTTP {e.code}"
                continue
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                ultimo_erro = f"rede: {e}"
                time.sleep(min(60, 5 * tentativa))
                continue
            # Erros chegam com HTTP 200: nao gravar no cache
            if "nadaencontrado" in texto.replace(" ", "").lower():
                self.stats["erros"] += 1
                raise ErroFipe(f"{endpoint}: nadaencontrado {params}")
            try:
                obj = json.loads(texto)
            except ValueError:
                ultimo_erro = "resposta nao-JSON"
                time.sleep(5)
                continue
            if isinstance(obj, dict) and "erro" in obj:
                self.stats["erros"] += 1
                raise ErroFipe(f"{endpoint}: {obj.get('erro')} (codigo {obj.get('codigo')}) {params}")
            tmp = arq + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False)
            os.replace(tmp, arq)
            return obj
        self.stats["erros"] += 1
        raise ErroFipe(f"{endpoint}: falhou apos {self.tentativas} tentativas ({ultimo_erro}) {params}")

    # ---- endpoints ----
    def tabelas(self):
        # cache diario: o mes mais recente muda ao longo do tempo
        return self.post("ConsultarTabelaDeReferencia", {}, chave_extra=dt.date.today().isoformat())

    def marcas(self, tab):
        return self.post("ConsultarMarcas", {"codigoTabelaReferencia": tab, "codigoTipoVeiculo": self.tipo_cod})

    def modelos(self, tab, marca):
        r = self.post("ConsultarModelos", {"codigoTipoVeiculo": self.tipo_cod, "codigoTabelaReferencia": tab,
                                           "codigoMarca": marca})
        return r.get("Modelos", [])  # 'Anos' daqui e da marca inteira: ignorar

    def anos(self, tab, marca, modelo):
        return self.post("ConsultarAnoModelo", {"codigoTipoVeiculo": self.tipo_cod, "codigoTabelaReferencia": tab,
                                                "codigoMarca": marca, "codigoModelo": modelo})

    def valor(self, tab, marca, modelo, ano, comb):
        return self.post("ConsultarValorComTodosParametros", {
            "codigoTabelaReferencia": tab, "codigoMarca": marca, "codigoModelo": modelo,
            "codigoTipoVeiculo": self.tipo_cod, "anoModelo": ano, "codigoTipoCombustivel": comb,
            "tipoVeiculo": self.tipo_str, "tipoConsulta": "tradicional"})


def limpa(s):
    return s.strip() if isinstance(s, str) else s


def normaliza(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.lower().split())


def valor_numerico(v):
    v = (v or "").replace("R$", "").replace(" ", "").replace("\xa0", "").replace(".", "").replace(",", ".")
    try:
        return f"{float(v):.2f}"
    except ValueError:
        return ""


def escolher_tabela(cli, codigo):
    tabs = cli.tabelas()
    if codigo:
        for t in tabs:
            if str(t["Codigo"]) == str(codigo):
                return t["Codigo"], limpa(t["Mes"])
        raise SystemExit(f"Tabela {codigo} nao encontrada")
    t = max(tabs, key=lambda x: int(x["Codigo"]))
    return t["Codigo"], limpa(t["Mes"])


def filtrar_marcas(marcas, filtro):
    if not filtro:
        return marcas
    f = normaliza(filtro)
    sel = [m for m in marcas if str(m["Value"]) == filtro or normaliza(m["Label"]) == f]
    if not sel:
        sel = [m for m in marcas if f in normaliza(m["Label"])]
    if not sel:
        raise SystemExit(f"Marca '{filtro}' nao encontrada")
    return sel


def coletar(cli, tab, mes, marcas, csv_path, log):
    linhas, falhas = [], []
    for i, m in enumerate(marcas, 1):
        cm, nm = m["Value"], limpa(m["Label"])
        try:
            modelos = cli.modelos(tab, cm)
        except ErroFipe as e:
            falhas.append(str(e)); log(f"  ! {e}"); continue
        log(f"[{i}/{len(marcas)}] {nm}: {len(modelos)} modelos")
        for mo in modelos:
            cmo, nmo = mo["Value"], limpa(mo["Label"])
            try:
                anos = cli.anos(tab, cm, cmo)
            except ErroFipe as e:
                falhas.append(str(e)); log(f"  ! {e}"); continue
            for a in anos:
                ano_cod = limpa(a["Value"])
                ano, comb = ano_cod.split("-", 1)
                try:
                    v = cli.valor(tab, cm, cmo, ano, comb)
                except ErroFipe as e:
                    falhas.append(str(e)); log(f"  ! {e}"); continue
                linhas.append({
                    "codigo_tabela_referencia": tab,
                    "mes_referencia": limpa(v.get("MesReferencia")) or mes,
                    "tipo_veiculo": v.get("TipoVeiculo", cli.tipo_cod),
                    "codigo_marca": cm, "marca": limpa(v.get("Marca")) or nm,
                    "codigo_modelo": cmo, "modelo": limpa(v.get("Modelo")) or nmo,
                    "ano_codigo": ano_cod, "ano_modelo": v.get("AnoModelo", ano),
                    "zero_km": "S" if str(ano) == "32000" else "N",
                    "codigo_combustivel": comb, "combustivel": limpa(v.get("Combustivel")),
                    "sigla_combustivel": limpa(v.get("SiglaCombustivel")),
                    "codigo_fipe": limpa(v.get("CodigoFipe")), "valor": limpa(v.get("Valor")),
                    "valor_numerico": valor_numerico(v.get("Valor")),
                    "autenticacao": limpa(v.get("Autenticacao")),
                    "data_consulta": limpa(v.get("DataConsulta")),
                })
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(linhas)
    return linhas, falhas


def estimar(cli, tab, marcas, n_amostra, seed, log):
    todos = []
    for m in marcas:
        try:
            for mo in cli.modelos(tab, m["Value"]):
                todos.append((m["Value"], mo["Value"]))
        except ErroFipe as e:
            log(f"  ! {e}")
    rnd = random.Random(seed)
    amostra = rnd.sample(todos, min(n_amostra, len(todos)))
    qtd = []
    for cm, cmo in amostra:
        try:
            qtd.append(len(cli.anos(tab, cm, cmo)))
        except ErroFipe as e:
            log(f"  ! {e}")
    media = sum(qtd) / len(qtd) if qtd else 0
    n = len(qtd)
    dp = (sum((x - media) ** 2 for x in qtd) / (n - 1)) ** 0.5 if n > 1 else 0
    combos = round(len(todos) * media)
    margem = round(len(todos) * 1.96 * dp / n ** 0.5) if n else 0
    req = 1 + 1 + len(marcas) + len(todos) + combos  # tabela + marcas + modelos + anos + valores
    req_429 = round(req * 1.03)
    return {"marcas": len(marcas), "modelos": len(todos), "amostra": n, "anos_por_modelo_media": round(media, 3),
            "anos_por_modelo_dp": round(dp, 3), "combinacoes_estimadas": combos, "combinacoes_ic95": margem,
            "requisicoes_estimadas": req, "requisicoes_com_429_3pct": req_429,
            "minutos_a_60rpm": round(req_429 / 60, 1), "horas_a_60rpm": round(req_429 / 3600, 2)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    aqui = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description="Coletor FIPE de motos, carros ou caminhoes")
    p.add_argument("--tipo", choices=list(TIPOS), default="moto", help="tipo de veiculo (padrao: moto)")
    p.add_argument("--tabela", help="codigoTabelaReferencia (padrao: mais recente)")
    p.add_argument("--marca", help="nome ou codigo da marca")
    p.add_argument("--csv", help="arquivo de saida (padrao: fipe_<tipo>.csv)")
    p.add_argument("--cache", default=os.path.join(aqui, "cache"))
    p.add_argument("--estimar", action="store_true")
    p.add_argument("--amostra", type=int, default=60)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--intervalo", type=float, default=1.0, help="segundos entre requisicoes (>=1.0)")
    p.add_argument("--quieto", action="store_true")
    a = p.parse_args()

    log = (lambda s: None) if a.quieto else (lambda s: print(s, flush=True))
    a.csv = a.csv or os.path.join(aqui, f"fipe_{a.tipo}.csv")
    cli = Cliente(a.cache, intervalo=max(1.0, a.intervalo), tipo=a.tipo)
    t0 = time.time()
    tab, mes = escolher_tabela(cli, a.tabela)
    marcas = filtrar_marcas(cli.marcas(tab), a.marca)
    print(f"Tipo: {a.tipo}; tabela {tab} ({mes}); marcas selecionadas: {len(marcas)}")
    if a.estimar:
        r = estimar(cli, tab, marcas, a.amostra, a.seed, log)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        linhas, falhas = coletar(cli, tab, mes, marcas, a.csv, log)
        print(f"Linhas: {len(linhas)}; modelos: {len({l['codigo_modelo'] for l in linhas})}; falhas: {len(falhas)}")
        for f in falhas[:20]:
            print("  falha:", f)
        print(f"CSV: {a.csv}")
    print(f"Requisicoes HTTP: {cli.stats['http']}; do cache: {cli.stats['cache']}; "
          f"429: {cli.stats['429']}; erros: {cli.stats['erros']}; tempo: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
