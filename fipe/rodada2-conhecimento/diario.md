# Diário - rodada 2 (com o conhecimento do especialista)

Ponto de partida: os `curl` copiados do navegador pelo especialista (com cookies, cabeçalhos e exemplos de resposta)
para os 6 endpoints. Sem ler nada do repositório nem da rodada 1.

1. **Os cookies são necessários?** Primeira requisição: `ConsultarTabelaDeReferencia` em Python puro, só com
   cabeçalhos "de navegador" e **sem cookie nenhum**. HTTP 200. O `cf_clearance` do exemplo era só do navegador.
   Custo: 1 requisição. Isso eliminou o maior risco (ter que manter sessão Cloudflare).

2. **Escolha da sequência.** O conhecimento lista 6 endpoints; para coletar basta
   Tabela -> Marcas -> Modelos -> AnoModelo -> Valor. `ConsultarModelosAtravesDoAno` é o caminho inverso (filtro do site)
   e foi descartado. O `Anos` que vem em `ConsultarModelos` é a união da marca toda, não serve por modelo.

3. **Coletor escrito de uma vez** (stdlib: urllib, csv, json): limitador de 1 req/s sem paralelismo, cache em disco
   por requisição (hash dos parâmetros, gravação atômica), retomada = rodar de novo (o cache responde),
   filtro `--marca`.

4. **Primeira rodada da amostra (Royal Enfield): HTTP 429.** Mesmo a 60 req/min cravados, 9 de 277 chamadas
   tomaram "Too Many Requests" (sem `Retry-After`). O backoff de 5 s que já estava no código resolveu todas na
   primeira repetição. Lição: "60 por minuto" do nosso lado não garante nada do lado deles; o limite deles parece
   de janela curta. Acrescentei leitura de `Retry-After` (caso apareça) e contador de 429 no resumo.

5. **Retomada testada**: reexecutar a amostra fez 1 requisição de rede (a lista de meses, que de propósito não sai do
   cache) e 267 do cache. CSV idêntico: 206 linhas.

6. **Estimativa sem rodar tudo.** Contar anos de cada um dos 2.037 modelos custaria 2.037 requisições (~35 min).
   Em vez disso: modelos de todas as 103 marcas (exato) + anos de 150 modelos sorteados -> 4,49 anos/modelo ->
   ~9.150 combinações, ~11.300 requisições, ~3,1 h. Custou 255 requisições (~5 min), de novo com 9 x 429.

7. **Armadilhas medidas, não supostas** (5 requisições de teste):
   - sem `tipoConsulta` ou sem `codigoTipoCombustivel` -> HTTP **200** com `{"codigo":"2","erro":"Parâmetros inválidos"}`;
   - ano inexistente -> HTTP 200 com `{"codigo":"0","erro":"nadaencontrado"}`;
   - sem `tipoVeiculo`/`modeloCodigoExterno` -> funciona igual;
   - GET -> 404.
   Bug encontrado no meu código por causa disso: `nadaencontrado` seria repetido 6 vezes (com backoff até minutos).
   Corrigido para falha definitiva sem retry. Erros nunca vão para o cache.

8. **Combustível não é sempre `1`.** O exemplo do especialista só tinha `-1` (gasolina). No cache da estimativa
   apareceram `-4`, `-5`, `-6`; 3 consultas de valor mostraram Elétrico, Flex e Híbrido. O coletor já usava o sufixo
   do `Value`, então nada quebrou - mas a documentação teria ficado errada se eu tivesse presumido.

9. **`32000` = 0 km.** Ano modelo 32000 aparece em 40 das 206 linhas da Royal Enfield. Virou coluna `ZeroKm` no CSV.

10. Tropeço de ferramenta: tentei esperar o processo em background com `sleep 240`, o ambiente bloqueou;
    troquei por um laço que espera o log terminar.

## Custo total desta rodada no servidor da FIPE
~543 requisições (1 teste + 277 amostra + 255 estimativa + 5 testes de erro + 3 combustíveis + 2 reexecuções),
das quais 18 foram 429. Nenhuma requisição desperdiçada em "descobrir" endpoints: o conhecimento do especialista
já dava a sequência, os parâmetros e os formatos - o trabalho foi confirmar, achar as bordas (erros com HTTP 200,
429, combustíveis, 0 km) e medir.
