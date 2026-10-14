#!/usr/bin/env python3
"""Coletor da Tabela FIPE (motos). Somente biblioteca padrao.

Uso:
  python coletor_fipe.py --marca "Royal Enfield" --saida amostra_royal_enfield.csv
  python coletor_fipe.py --estimar
  python coletor_fipe.py --saida fipe_motos.csv          # coleta completa (retomavel)
"""
import argparse, csv, hashlib, json, os, random, re, sys, time
import urllib.request, urllib.error, urllib.parse

BASE = "https://veiculos.fipe.org.br/api/veiculos/"
TIPO_COD, TIPO_STR = 2, "moto"
MIN_INTERVALO = 1.0  # 60 req/min, sequencial
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://veiculos.fipe.org.br/",
    "Origin": "https://veiculos.fipe.org.br",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}
CAMPOS = ["codigo_tabela_referencia", "mes_referencia", "tipo_veiculo", "codigo_marca", "marca",
          "codigo_modelo", "modelo", "ano_codigo", "ano_modelo", "zero_km", "codigo_combustivel",
          "combustivel", "sigla_combustivel", "codigo_fipe", "valor", "valor_numerico",
          "autenticacao", "data_consulta"]


class Cliente:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.ultimo = 0.0
        self.reqs = 0      # requisicoes reais
        self.hits = 0      # acertos de cache

    def _arq(self, endpoint, corpo):
        h = hashlib.sha1((endpoint + "?" + corpo).encode()).hexdigest()
        return os.path.join(self.cache_dir, h + ".json")

    def post(self, endpoint, params):
        corpo = urllib.parse.urlencode(params)
        arq = self._arq(endpoint, corpo)
        if os.path.exists(arq):
            try:
                with open(arq, encoding="utf-8") as f:
                    self.hits += 1
                    return json.load(f)
            except Exception:
                os.remove(arq)
        tentativas = 0
        while True:
            espera = MIN_INTERVALO - (time.monotonic() - self.ultimo)
            if espera > 0:
                time.sleep(espera)
            self.ultimo = time.monotonic()
            self.reqs += 1
            req = urllib.request.Request(BASE + endpoint, data=corpo.encode(), headers=HEADERS, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    txt = r.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                tentativas += 1
                if e.code in (429, 500, 502, 503, 504) and tentativas <= 8:
                    time.sleep(random.uniform(5, 10))
                    continue
                raise
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                tentativas += 1
                if tentativas <= 8:
                    time.sleep(random.uniform(5, 10))
                    continue
                raise
            try:
                dados = json.loads(txt)
            except ValueError:
                tentativas += 1
                if tentativas <= 4:
                    time.sleep(random.uniform(5, 10))
                    continue
                return {"erro": "resposta nao JSON: " + txt[:100]}
            if erro_corpo(dados):
                return dados  # nunca vai para o cache
            tmp = arq + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False)
            os.replace(tmp, arq)
            return dados


def erro_corpo(d):
    if isinstance(d, dict):
        if "erro" in d or ("codigo" in d and "Valor" not in d and "Modelos" not in d):
            return True
    if isinstance(d, str) and "nadaencontrado" in d.lower():
        return True
    return False


def limpa(s):
    return s.strip() if isinstance(s, str) else s


def valor_num(v):
    m = re.sub(r"[^\d,]", "", v or "")
    return "%.2f" % float(m.replace(",", ".")) if m else ""


def tabela(cli, codigo=None):
    t = cli.post("ConsultarTabelaDeReferencia", {})
    if not isinstance(t, list) or not t:
        sys.exit("Falha na tabela de referencia: %r" % (t,))
    if codigo:
        return int(codigo), next((limpa(x["Mes"]) for x in t if int(x["Codigo"]) == int(codigo)), "")
    x = max(t, key=lambda i: int(i["Codigo"]))
    return int(x["Codigo"]), limpa(x["Mes"])


def marcas(cli, tab):
    r = cli.post("ConsultarMarcas", {"codigoTabelaReferencia": tab, "codigoTipoVeiculo": TIPO_COD})
    if not isinstance(r, list):
        sys.exit("Falha em marcas: %r" % (r,))
    return [(int(m["Value"]), limpa(m["Label"])) for m in r]


def modelos(cli, tab, marca):
    r = cli.post("ConsultarModelos", {"codigoTipoVeiculo": TIPO_COD, "codigoTabelaReferencia": tab, "codigoMarca": marca})
    if not isinstance(r, dict) or "Modelos" not in r:
        print("  ! erro modelos marca %s: %r" % (marca, r), file=sys.stderr)
        return None
    return [(int(m["Value"]), limpa(m["Label"])) for m in r["Modelos"]]


def anos(cli, tab, marca, modelo):
    r = cli.post("ConsultarAnoModelo", {"codigoTipoVeiculo": TIPO_COD, "codigoTabelaReferencia": tab,
                                        "codigoMarca": marca, "codigoModelo": modelo})
    if not isinstance(r, list):
        print("  ! erro anos modelo %s: %r" % (modelo, r), file=sys.stderr)
        return None
    return [(limpa(a["Value"]), limpa(a["Label"])) for a in r]


def valor(cli, tab, marca, modelo, ano_codigo):
    ano, comb = ano_codigo.split("-")
    return cli.post("ConsultarValorComTodosParametros", {
        "codigoTabelaReferencia": tab, "codigoMarca": marca, "codigoModelo": modelo,
        "codigoTipoVeiculo": TIPO_COD, "anoModelo": ano, "codigoTipoCombustivel": comb,
        "tipoVeiculo": TIPO_STR, "tipoConsulta": "tradicional"})


def estimar(cli, tab, mes, ms, n=60):
    tot_mod, lista = 0, []
    for i, (cm, nm) in enumerate(ms, 1):
        mods = modelos(cli, tab, cm) or []
        tot_mod += len(mods)
        lista += [(cm, c) for c, _ in mods]
        if i % 20 == 0:
            print("  marcas %d/%d, modelos %d" % (i, len(ms), tot_mod), flush=True)
    random.seed(42)
    amostra = random.sample(lista, min(n, len(lista)))
    soma = 0
    for cm, c in amostra:
        soma += len(anos(cli, tab, cm, c) or [])
    media = soma / len(amostra) if amostra else 0
    combos = round(media * tot_mod)
    reqs = 1 + 1 + len(ms) + tot_mod + combos  # tabela + marcas + modelos/marca + anos/modelo + valores
    print("\n== ESTIMATIVA (tabela %s, %s) ==" % (tab, mes))
    print("marcas: %d\nmodelos: %d\namostra: %d modelos, %d anos (media %.2f anos/modelo)"
          % (len(ms), tot_mod, len(amostra), soma, media))
    print("combinacoes modelo/ano: ~%d\nrequisicoes: ~%d\ntempo a 60 req/min: ~%.1f h"
          % (combos, reqs, reqs / 3600))
    print("requisicoes reais nesta estimativa: %d (cache: %d)" % (cli.reqs, cli.hits))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marca", help="filtro por nome da marca (igual, ignorando caixa; senao contem)")
    ap.add_argument("--tabela", help="codigo da tabela de referencia (padrao: mais recente)")
    ap.add_argument("--saida", default="fipe_motos.csv")
    ap.add_argument("--cache", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache_fipe"))
    ap.add_argument("--estimar", action="store_true")
    a = ap.parse_args()

    cli = Cliente(a.cache)
    tab, mes = tabela(cli, a.tabela)
    print("Tabela %s - %s" % (tab, mes))
    ms = marcas(cli, tab)
    if a.marca:
        q = a.marca.lower()
        f = [m for m in ms if m[1].lower() == q] or [m for m in ms if q in m[1].lower()]
        if not f:
            sys.exit("Marca nao encontrada")
        ms = f
    if a.estimar:
        return estimar(cli, tab, mes, ms)

    # retomada: CSV escrito de forma incremental; combinacoes ja gravadas sao puladas (alem do cache)
    feitos = set()
    novo = not os.path.exists(a.saida)
    if not novo:
        with open(a.saida, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if r["codigo_tabela_referencia"] == str(tab):
                    feitos.add((r["codigo_marca"], r["codigo_modelo"], r["ano_codigo"]))
    out = open(a.saida, "a", encoding="utf-8-sig" if novo else "utf-8", newline="")
    w = csv.writer(out)
    if novo:
        w.writerow(CAMPOS)
    n = erros = 0
    for cm, nm in ms:
        mods = modelos(cli, tab, cm)
        if mods is None:
            erros += 1
            continue
        print("Marca %s (%s): %d modelos" % (nm, cm, len(mods)), flush=True)
        for c, nmod in mods:
            ans = anos(cli, tab, cm, c)
            if ans is None:
                erros += 1
                continue
            for cod, _ in ans:
                if (str(cm), str(c), cod) in feitos:
                    continue
                v = valor(cli, tab, cm, c, cod)
                if erro_corpo(v) or "Valor" not in v:
                    erros += 1
                    print("  ! valor %s/%s/%s: %r" % (cm, c, cod, v), file=sys.stderr)
                    continue
                ano, comb = cod.split("-")
                w.writerow([tab, limpa(v.get("MesReferencia")) or mes, limpa(v.get("TipoVeiculo")) or TIPO_COD,
                            cm, nm, c, nmod, cod, ano, "S" if ano == "32000" else "N", comb,
                            limpa(v.get("Combustivel")), limpa(v.get("SiglaCombustivel")),
                            limpa(v.get("CodigoFipe")), limpa(v.get("Valor")), valor_num(v.get("Valor")),
                            limpa(v.get("Autenticacao")), limpa(v.get("DataConsulta"))])
                out.flush()
                n += 1
    out.close()
    print("Linhas novas: %d | erros: %d | requisicoes reais: %d | cache: %d" % (n, erros, cli.reqs, cli.hits))


if __name__ == "__main__":
    main()
