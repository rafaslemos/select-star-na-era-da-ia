"""Converte as amostras das três rodadas para um formato único e confere se são iguais.

Cada subagente escolheu nomes de coluna, ordem e separador diferentes. Este script lê
qualquer um desses formatos e grava amostra_royal_enfield_padrao.csv em cada pasta:

  - separador vírgula, UTF-8 com BOM (abre direto no Excel);
  - colunas em snake_case, na ordem de FORMATO;
  - linhas ordenadas por modelo, ano e combustível.

    python padronizar_csv.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

AQUI = Path(__file__).parent
RODADAS = ["rodada1-exploracao", "rodada2-conhecimento", "rodada3-destilado"]
ENTRADA = "amostra_royal_enfield.csv"
SAIDA = "amostra_royal_enfield_padrao.csv"

FORMATO = [
    "codigo_tabela_referencia", "mes_referencia", "tipo_veiculo",
    "codigo_marca", "marca", "codigo_modelo", "modelo",
    "ano_codigo", "ano_modelo", "zero_km",
    "codigo_combustivel", "combustivel", "sigla_combustivel",
    "codigo_fipe", "valor", "valor_numerico",
    "autenticacao", "data_consulta",
]
# Mudam a cada consulta à FIPE; ficam fora da comparação entre rodadas.
VOLATEIS = {"autenticacao", "data_consulta"}

# Nomes que cada rodada usou para a mesma informação (comparação sem diferenciar maiúsculas).
SINONIMOS = {
    "codigo_tabela_referencia": ["codigoTabelaReferencia"],
    "tipo_veiculo": ["TipoVeiculo", "codigoTipoVeiculo"],
    "codigo_marca": ["codigoMarca"],
    "codigo_modelo": ["codigoModelo"],
    "ano_codigo": ["anoCodigo", "AnoCombustivelCodigo", "AnoCombustivel"],
    "codigo_combustivel": ["codigoTipoCombustivel"],
    "marca": ["Marca"], "modelo": ["Modelo"], "ano_modelo": ["AnoModelo"],
    "combustivel": ["Combustivel"], "sigla_combustivel": ["SiglaCombustivel"],
    "codigo_fipe": ["CodigoFipe"], "valor": ["Valor"], "mes_referencia": ["MesReferencia"],
    "autenticacao": ["Autenticacao"], "data_consulta": ["DataConsulta"],
}


def ler(arquivo: Path) -> list[dict]:
    texto = arquivo.read_text(encoding="utf-8-sig")
    separador = csv.Sniffer().sniff(texto.splitlines()[0], delimiters=",;").delimiter
    return list(csv.DictReader(texto.splitlines(), delimiter=separador))


def valor_numerico(valor: str) -> str:
    return f"{float(valor.replace('R$', '').replace('.', '').replace(',', '.').strip()):.2f}"


def padronizar(linha: dict) -> dict:
    por_nome = {k.lower(): (v or "").strip() for k, v in linha.items()}
    saida = {}
    for coluna, nomes in SINONIMOS.items():
        saida[coluna] = next((por_nome[n.lower()] for n in nomes if n.lower() in por_nome), "")
    saida["valor_numerico"] = valor_numerico(saida["valor"])
    saida["zero_km"] = "S" if saida["ano_modelo"] == "32000" else "N"
    return {c: saida[c] for c in FORMATO}


def chave(linha: dict):
    return (linha["modelo"], int(linha["codigo_modelo"]), -int(linha["ano_modelo"]), linha["codigo_combustivel"])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    resultados = {}
    for rodada in RODADAS:
        linhas = sorted((padronizar(l) for l in ler(AQUI / rodada / ENTRADA)), key=chave)
        destino = AQUI / rodada / SAIDA
        with destino.open("w", encoding="utf-8-sig", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=FORMATO)
            escritor.writeheader()
            escritor.writerows(linhas)
        resultados[rodada] = [{k: v for k, v in l.items() if k not in VOLATEIS} for l in linhas]
        print(f"{rodada}: {len(linhas)} linhas -> {destino.relative_to(AQUI)}")

    referencia = resultados[RODADAS[0]]
    for rodada in RODADAS[1:]:
        iguais = sum(a == b for a, b in zip(referencia, resultados[rodada]))
        ok = iguais == len(referencia) == len(resultados[rodada])
        print(f"{rodada} x {RODADAS[0]}: {iguais}/{len(referencia)} linhas iguais "
              f"(sem {', '.join(sorted(VOLATEIS))}) {'OK' if ok else 'DIFERENTE'}")
        if not ok:
            for a, b in zip(referencia, resultados[rodada]):
                if a != b:
                    print("  primeira diferença:", {k: (a[k], b[k]) for k in a if a[k] != b[k]})
                    break


if __name__ == "__main__":
    main()
