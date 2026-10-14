# API da Tabela FIPE: consulta de motos

Base: `https://veiculos.fipe.org.br/api/veiculos/`. Todos os endpoints aceitam **somente POST**, com corpo
`application/x-www-form-urlencoded; charset=UTF-8`. Cookies não são necessários.

## Endpoints

| # | Endpoint | Corpo | Uso do retorno |
|---|----------|-------|----------------|
| 1 | `ConsultarTabelaDeReferencia` | vazio | lista `[{Codigo, Mes}]`; o maior `Codigo` é o mês mais recente (338 = outubro/2026) |
| 2 | `ConsultarMarcas` | `codigoTabelaReferencia`, `codigoTipoVeiculo=2` | `[{Label, Value}]`; `Value` = `codigoMarca` |
| 3 | `ConsultarModelos` | `codigoTipoVeiculo=2`, `codigoTabelaReferencia`, `codigoMarca` | `{Modelos:[{Label,Value}], Anos:[...]}`; `Value` = `codigoModelo` |
| 4 | `ConsultarAnoModelo` | os de (3) + `codigoModelo` | `[{Label, Value}]`, com `Value` no formato `ano-combustivel` (ex. `2020-1`) |
| 5 | `ConsultarValorComTodosParametros` | `codigoTabelaReferencia`, `codigoMarca`, `codigoModelo`, `codigoTipoVeiculo=2`, `anoModelo`, `codigoTipoCombustivel`, `tipoVeiculo=moto`, `tipoConsulta=tradicional` | `Valor`, `Marca`, `Modelo`, `AnoModelo`, `Combustivel`, `CodigoFipe`, `MesReferencia`, `Autenticacao`, `TipoVeiculo`, `SiglaCombustivel`, `DataConsulta` |

Tipo de veículo: 1 = carro, 2 = moto, 3 = caminhão. No passo 5, `tipoVeiculo` é a string `carro`, `moto` ou `caminhao`.

## Sequência de chamadas

1 × tabela → 1 × marcas → 1 × modelos por marca → 1 × anos por modelo → 1 × valor por combinação modelo/ano.
O `anoModelo` e o `codigoTipoCombustivel` do passo 5 saem do `Value` do passo 4 (`2020-1` vira ano 2020 e combustível 1).

## Armadilhas

- **Só POST.** Com GET a resposta é 404.
- **Os erros vêm com HTTP 200**, com o motivo no corpo: `{"codigo":"2","erro":"Parâmetros inválidos"}` ou `nadaencontrado`. O coletor trata isso como erro e **não grava no cache**.
- **HTTP 429 do Cloudflare** sem `Retry-After`, em cerca de 3% das chamadas mesmo a 1 req/s. Nas medições: 8 em 276 requisições na amostra e 5 em 164 na estimativa. O coletor espera de 5 a 10 s (aleatório) e repete.
- **Combustível:** use sempre o código que vem no ano. Códigos: 1 Gasolina, 2 Álcool, 3 Diesel, 4 Elétrico, 5 Flex, 6 Híbrido.
- **Ano `32000` = Zero KM.** No CSV, `zero_km=S`.
- **A lista `Anos` de `ConsultarModelos` vale para a marca inteira, não para o modelo.** Para saber os anos do modelo, chame `ConsultarAnoModelo`.
- **Espaços no final** de alguns textos (ex. `MesReferencia`, `Mes`): o coletor remove com `strip`.
- O mês mais recente muda com o tempo, por isso a resposta de `ConsultarTabelaDeReferencia` fica no cache só pelo dia.

## Coletor (`coletor_fipe.py`)

```
python coletor_fipe.py                                  # tudo, mês mais recente -> fipe_motos.csv
python coletor_fipe.py --marca "Royal Enfield" --csv amostra_royal_enfield.csv
python coletor_fipe.py --estimar [--amostra 60 --seed 42]
python coletor_fipe.py --tabela 338                     # mês específico
```
- Requisições em sequência, com no mínimo 1,0 s entre elas (até 60 por minuto).
- Cache em `cache/`: um JSON por requisição, com chave = endpoint + parâmetros. O arquivo é gravado de forma atômica e só para respostas válidas.
- Retomada: rodar de novo pula o que já está no cache. O CSV é gerado no fim, a partir das respostas.

## Validação: Royal Enfield (tabela 338, outubro/2026)

- Marca 192: 59 modelos, **206 combinações modelo/ano com valor**, 0 falhas. 40 delas são Zero KM.
- 276 requisições HTTP: 268 úteis (1 + 1 + 1 + 59 + 206) e 8 repetições por 429. Tempo: 330 s.

## Estimativa da coleta completa (motos, tabela 338)

Valores obtidos com `--estimar`: contagem exata de marcas e modelos e sorteio de 60 modelos (seed 42) para medir os anos.

| Item | Valor |
|------|-------|
| Marcas | **103** (exato) |
| Modelos | **2.037** (exato) |
| Anos por modelo (amostra n=60) | média 4,75; desvio-padrão 4,10 |
| Combinações modelo/ano | **~9.676** (IC 95% ±2.111, ou seja, entre ~7.600 e ~11.800) |
| Requisições | 1 + 1 + 103 + 2.037 + 9.676 = **~11.818**; com ~3% de 429, **~12.170** |
| Tempo a 60 req/min | **~203 min (~3,4 h)**, sem contar as esperas de 5 a 10 s após cada 429. Na prática fica entre ~3,5 e ~4 h |

A estimativa e a amostra já deixaram ~440 respostas no cache. A coleta completa reaproveita essas respostas.
