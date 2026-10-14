# Diário — rodada 3 (com o conhecimento destilado do especialista)

Ponto de partida: um texto curto do especialista com os 5 endpoints, os corpos de exemplo e os códigos de tipo de veículo e combustível. Nenhuma exploração às cegas foi necessária.

## Linha do tempo

1. **Sondagem do passo 1 (1 requisição).** `ConsultarTabelaDeReferencia` com corpo vazio funcionou de primeira: 310 meses, o mais recente é 338 = outubro/2026. Confirmou o que o especialista disse.
2. **Marcas + teste de erro (3 requisições).** 103 marcas de moto; Royal Enfield = 192. Testei de propósito sem `codigoTipoVeiculo`: **a API responde HTTP 200** com `{"codigo":"2","erro":"Parâmetros inválidos"}` — e a mensagem vem em latin-1. Isso não estava no texto do especialista: quem confiar no status HTTP grava erro no cache achando que é dado.
3. **Modelos, anos e valor (5 requisições).** Tudo como descrito. Detalhes que o texto não dizia: `ConsultarModelos` devolve também uma lista `Anos` (da marca, não do modelo — armadilha); `Value` do modelo é inteiro e o da marca é string; `32000` é o código de zero km; o valor vem como texto `R$ 20.684,00`; a resposta final traz mais campos do que os listados (`Autenticacao`, `TipoVeiculo`, `SiglaCombustivel`, `DataConsulta`). Também vi que `tipoVeiculo=moto` pode ser omitido, mas mantive.
4. **Coletor escrito de uma vez** (só stdlib): limitador de 1 req/s, cache em disco por endpoint+parâmetros com gravação atômica, retomada via cache, filtro de marca, CSV com todas as colunas da API + códigos usados + valor numérico.
5. **Amostra Royal Enfield (278 requisições, 5 min 22 s).** 59 modelos, 206 linhas, 0 erros. **Surpresa: 10 respostas HTTP 429** mesmo respeitando 60 req/min, sequencial. O backoff que eu tinha colocado "por precaução" segurou a coleta. Lição: o limite de 60/min que nos foi dado é o nosso teto, não a garantia de que o servidor aceite esse ritmo.
6. **Ajuste:** desaceleração adaptativa (+20 % de intervalo a cada 429, volta aos poucos) e log do `Retry-After`.
7. **Teste de retomada.** Rodar de novo: 1 requisição de rede (só a lista de meses), CSV idêntico byte a byte. Apaguei 5 respostas do cache para simular interrupção: o coletor refez só essas 5 (+1), dados idênticos.
8. **Estimativa (162 requisições, 3,5 min).** Modelos de todas as 103 marcas (2.037) + anos de 60 modelos sorteados (média 4,75). ~9.700 combinações, ~11.800 requisições, ~3,3 a 3,5 h. Mais 2 respostas 429.

## Custo desta rodada

- Requisições à FIPE: ~456 no total (9 de sondagem, 278 da amostra, 7 dos testes de retomada, 162 da estimativa).
- Nenhum tropeço de "descobrir a API": o conhecimento do especialista eliminou a fase de tentativa e erro. O que sobrou para descobrir foram as **armadilhas operacionais** — erro com HTTP 200, encoding misto, tipos inconsistentes, ano 32000 e o 429 abaixo do limite combinado.
- Moral para a palestra: o texto do especialista economiza a exploração, mas não substitui rodar uma amostra real. As duas coisas que mais mudariam o resultado (erro disfarçado de 200 e 429 a 60 req/min) só apareceram executando.
