Colete os dados da consulta de MOTOS da Tabela FIPE (marcas, modelos, anos e o valor FIPE de cada combinação) e deixe pronto um coletor automatizado, usando o conhecimento abaixo.

Regras:
- Use só o conhecimento abaixo. Não leia outros arquivos do repositório nem pastas temporárias, e não consulte memórias de sessões anteriores.
- No máximo 60 requisições por minuto à FIPE, sem paralelismo, reaproveitando respostas já obtidas.
- NÃO rode a coleta completa. Valide o coletor na marca Royal Enfield inteira (todos os modelos, todos os anos, com valores) no mês de referência mais recente.
- Rode a amostra e a estimativa cada uma numa única chamada que espera o fim (timeout 600000 ms).

Entregáveis em fipe/{{PASTA}}/ (relativo à raiz do repositório):
1. API.md: endpoints, parâmetros, sequência de chamadas e armadilhas.
2. coletor_fipe.py: Python só com biblioteca padrão. Coleta todas as marcas, modelos, anos e valores de motos de um mês de referência, com controle de taxa, cache em disco (erros nunca entram no cache) e retomada. Aceita filtro de marca (--marca) e uma opção de estimativa (--estimar) que conta marcas e modelos e sorteia 60 modelos para estimar os anos.
3. amostra_royal_enfield.csv: resultado da Royal Enfield, no formato definido abaixo.
4. A estimativa da coleta completa (marcas, modelos, combinações modelo/ano, requisições e tempo a 60 req/min), numa seção do API.md.
5. diario.md: diário curto do processo.

Ao terminar, responda com um resumo curto: números da amostra e a estimativa.

===== CONHECIMENTO DO ESPECIALISTA =====

1. **Consultar Tabela de Referência:** Obtém o código do mês atualizado.
**Endpoint:** `POST https://veiculos.fipe.org.br/api/veiculos/ConsultarTabelaDeReferencia`
**Headers:** Padrão FIPE (necessário `Content-Type: application/x-www-form-urlencoded; charset=UTF-8` nos próximos)
**Body:** Vazio
**Retorno:** Extraia o `Codigo` do mês desejado (ex: `338` para Outubro/2026). Será o `codigoTabelaReferencia`.

2. **Consultar Marcas:**
**Endpoint:** `POST https://veiculos.fipe.org.br/api/veiculos/ConsultarMarcas`
**Body:** `codigoTabelaReferencia=338&codigoTipoVeiculo=2`
*(Códigos de tipoVeiculo: 1 = Carros, 2 = Motos, 3 = Caminhões)*
**Retorno:** Extraia o `Value` da marca desejada (ex: `131` para Amazonas). Será o `codigoMarca`.

3. **Consultar Modelos:**
**Endpoint:** `POST https://veiculos.fipe.org.br/api/veiculos/ConsultarModelos`
**Body:** `codigoTipoVeiculo=2&codigoTabelaReferencia=338&codigoMarca=131`
**Retorno:** Extraia o `Value` de dentro do objeto `Modelos` (ex: `4361`). Será o `codigoModelo`.

4. **Consultar Ano e Combustível:** Mapeia as versões disponíveis do modelo.
**Endpoint:** `POST https://veiculos.fipe.org.br/api/veiculos/ConsultarAnoModelo`
**Body:** `codigoTipoVeiculo=2&codigoTabelaReferencia=338&codigoMarca=131&codigoModelo=4361`
**Retorno:** Extraia o `Value`. Ele retorna no formato `anoModelo-codigoTipoCombustivel` (ex: `2008-1`).

5. **Consultar Valor Final:** Retorna a avaliação oficial e o Código Fipe.
**Endpoint:** `POST https://veiculos.fipe.org.br/api/veiculos/ConsultarValorComTodosParametros`
**Body:** `codigoTabelaReferencia=338&codigoMarca=131&codigoModelo=4361&codigoTipoVeiculo=2&anoModelo=2008&codigoTipoCombustivel=1&tipoVeiculo=moto&tipoConsulta=tradicional`
*(Nota: `anoModelo` e `codigoTipoCombustivel` são separados aqui. `tipoVeiculo` passa a ser a string literal `carro`, `moto` ou `caminhao`)*
**Retorno:** JSON contendo `Valor`, `Marca`, `Modelo`, `AnoModelo`, `Combustivel`, `CodigoFipe`, `MesReferencia`, `Autenticacao`, `TipoVeiculo`, `SiglaCombustivel` e `DataConsulta`.

Armadilhas:
- Só POST; GET devolve 404. Cookies não são necessários.
- Erros vêm com HTTP 200 e o motivo no corpo, por exemplo `{"codigo":"2","erro":"Parâmetros inválidos"}`, ou `nadaencontrado` quando a combinação não existe. Trate como erro e não grave no cache.
- O Cloudflare responde HTTP 429, sem `Retry-After`, em cerca de 3% das chamadas mesmo a 1 req/s. Espere 5 a 10 s e repita.
- Use sempre o código de combustível que vem no ano (`2020-1` → 1). Códigos: 1 Gasolina, 2 Álcool, 3 Diesel, 4 Elétrico, 5 Flex, 6 Híbrido. Ano `32000` = Zero KM.
- A lista `Anos` que vem em ConsultarModelos é da marca inteira, não do modelo: use ConsultarAnoModelo.
- Alguns textos vêm com espaço no final (ex.: `MesReferencia`); remova.

Formato do CSV (separador vírgula, UTF-8 com BOM, uma linha por modelo/ano, nesta ordem de colunas):
codigo_tabela_referencia, mes_referencia, tipo_veiculo, codigo_marca, marca, codigo_modelo, modelo, ano_codigo, ano_modelo, zero_km (S/N), codigo_combustivel, combustivel, sigla_combustivel, codigo_fipe, valor (como vem, ex. "R$ 20.684,00"), valor_numerico (ex. 20684.00), autenticacao, data_consulta

===== FIM DO CONHECIMENTO =====
