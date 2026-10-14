# API FIPE (motos) - veiculos.fipe.org.br

Todos os endpoints: `POST https://veiculos.fipe.org.br/api/veiculos/<Endpoint>`, header `Content-Type: application/x-www-form-urlencoded; charset=UTF-8`. GET devolve 404; cookies desnecessarios.

## Sequencia
1. `ConsultarTabelaDeReferencia` (body vazio) -> lista `{Codigo, Mes}`; usar o maior `Codigo` (338 = outubro/2026).
2. `ConsultarMarcas`: `codigoTabelaReferencia=338&codigoTipoVeiculo=2` -> `[{Label, Value}]` (Value = codigoMarca). Royal Enfield = 192.
3. `ConsultarModelos`: `codigoTipoVeiculo=2&codigoTabelaReferencia=338&codigoMarca=192` -> `{Modelos:[{Label,Value}], Anos:[...]}`. `Anos` e da marca toda: ignorar.
4. `ConsultarAnoModelo`: acrescenta `codigoModelo` -> `[{Label, Value}]`, Value = `ano-combustivel` (ex. `2008-1`; `32000-x` = Zero KM).
5. `ConsultarValorComTodosParametros`: `codigoTabelaReferencia, codigoMarca, codigoModelo, codigoTipoVeiculo=2, anoModelo, codigoTipoCombustivel, tipoVeiculo=moto, tipoConsulta=tradicional` -> `Valor, Marca, Modelo, AnoModelo, Combustivel, CodigoFipe, MesReferencia, Autenticacao, TipoVeiculo, SiglaCombustivel, DataConsulta`.

## Armadilhas
- Erros chegam com HTTP 200 (`{"codigo":"2","erro":"Parâmetros inválidos"}` ou `nadaencontrado`): tratar como erro, nunca cachear.
- Cloudflare responde 429 (sem Retry-After) em ~3% das chamadas: esperar 5-10 s e repetir (o coletor faz ate 8 tentativas).
- Usar o combustivel que vem no ano (`2020-1` -> 1). 1 Gasolina, 2 Alcool, 3 Diesel, 4 Eletrico, 5 Flex, 6 Hibrido.
- Textos com espaco no final (ex. `MesReferencia`, "outubro de 2026 "): aplicar strip.
- Valor vem como "R$ 20.684,00"; o CSV traz tambem `valor_numerico`.

## Coletor
`python coletor_fipe.py --marca "Royal Enfield" --saida amostra_royal_enfield.csv` | `--estimar` | sem filtro = coleta completa (retomavel via cache em `cache_fipe/` e CSV incremental). 1 req/s, sequencial.

## Amostra Royal Enfield (tabela 338, outubro/2026)
59 modelos, 206 linhas modelo/ano com valor, 0 erros, 277 requisicoes (~5,5 min).

## Estimativa da coleta completa (tabela 338)
| Item | Valor |
|---|---|
| Marcas | 103 |
| Modelos | 2.037 |
| Anos/modelo (amostra de 60 modelos: 285 anos) | 4,75 |
| Combinacoes modelo/ano | ~9.676 |
| Requisicoes (1 + 1 + 103 + 2.037 + 9.676) | ~11.818 |
| Tempo a 60 req/min | ~197 min (~3,3 h), mais ~3% de repeticoes por 429 |

Obs.: a Royal Enfield tem 3,5 anos/modelo (206/59), abaixo da media estimada de 4,75; o total real pode variar.
