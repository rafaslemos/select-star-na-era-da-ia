# Experimentos: explorar x conhecer (Tabela FIPE, motos)

Mesma tarefa, dois subagentes do Claude Code (Claude Opus 5.5) com contexto limpo:
mapear a consulta de motos da Tabela FIPE e entregar um coletor validado numa marca.
A diferença está só no que o prompt traz.

A medição usa `medir_sessao.py` e soma o `usage` do transcript do subagente desde um marco.
Entrada e cache são exatos. A saída é estimada pelo texto gerado (caracteres ÷ 3,5), sem
o raciocínio, porque o transcript de subagente só registra o valor do início do streaming.
Os custos usam os preços do Opus 5.5.

## Rodada 1: explorar do zero

- **Data:** 2026-10-05, marco `inicio-fipe` (21:01:32 UTC)
- **Prompt:** apenas o link https://veiculos.fipe.org.br/ e o objetivo, sem nenhuma dica técnica
- **Entregáveis:** `fipe/rodada1-exploracao/` (API.md, coletor_fipe.py, amostra Royal Enfield, diario.md)
- **Medição completa:** `medicao/exploracao-fipe-subagente.json`

| Métrica | Valor |
|---|---|
| Duração | 14 min 34 s |
| Chamadas ao modelo | 28 |
| Uso de ferramentas | 34 (Bash 22, Edit 7, Write 4, handback 1) |
| Escrita de cache | 111.865 tokens |
| Leitura de cache | 2.405.844 tokens |
| Saída (estimada) | ~14.691 tokens |
| Total processado | ~2.532.456 tokens |
| Custo estimado | ~US$ 1,82 |
| Requisições ao site da FIPE | ~510 (2 de reconhecimento, ~15 de teste, 291 da amostra, 203 da estimativa) |
| Resultado | 206 linhas da Royal Enfield, todas com valor |

O que a exploração teve de descobrir sozinha:

- os endpoints internos `POST /api/veiculos/...` e a ordem das chamadas;
- o código de tipo de veículo (2 = moto) e o formato dos anos (`2026-1`, com 32000 = Zero KM);
- o parâmetro obrigatório `tipoConsulta=tradicional`;
- que os erros vêm com HTTP 200 e, sem o tipo de veículo, a API responde "nadaencontrado" em vez de acusar o erro;
- que o Cloudflare bloqueia (HTTP 429) acima de ~0,9 req/s.

## Rodada 2: executar com conhecimento

- **Data:** 2026-10-06, marco `inicio-fipe-conhecimento` (00:50:46 UTC)
- **Prompt:** a mesma tarefa, mais o conhecimento do Rafael colado na íntegra: os 6 `curl`
  copiados do navegador (com cabeçalhos e cookies) e as respostas de exemplo, incluindo a
  lista completa de 310 meses de referência. Limite pedido: 60 req/min.
- **Entregáveis:** `fipe/rodada2-conhecimento/` (API.md, coletor_fipe.py, amostra, ESTIMATIVA.md, diario.md)
- **Medição completa:** `medicao/execucao-fipe-conhecimento.json`

| Métrica | Rodada 1: explorar | Rodada 2: conhecimento | Diferença |
|---|---|---|---|
| Duração | 14 min 34 s | 16 min 45 s | +15% (taxa de 1 req/s em vez de até 2) |
| Chamadas ao modelo | 28 | 18 | −36% |
| Uso de ferramentas | 34 | 19 | −44% |
| Tamanho do prompt | 6.526 caracteres | 31.950 caracteres | ×4,9 |
| Contexto no 1º turno | 61.503 tokens | 78.178 tokens | +16.675 |
| Escrita de cache | 111.865 | 196.945 | +76% |
| Leitura de cache | 2.405.844 | 1.536.919 | −36% |
| Saída (estimada) | ~14.691 | ~12.333 | −16% |
| Total processado | ~2.532.456 | ~1.746.233 | −31% |
| Custo estimado | ~US$ 1,82 | ~US$ 1,85 | ≈ igual |
| Requisições à FIPE | ~510 | ~543 (18 com 429) | ≈ igual |
| Resultado | 206 linhas | 206 linhas | mesmas 206 combinações e os 206 valores idênticos |

Leitura dos números:

- **O conhecimento cortou o trabalho da IA.** Foram 36% menos chamadas ao modelo, 44% menos
  uso de ferramentas e 31% menos tokens processados. A IA não precisou investigar o site.
- **O custo não caiu, porque o conhecimento chegou em estado copiado.** Os `curl` copiados do
  navegador trazem cabeçalhos e cookies repetidos seis vezes, e a lista de 310 meses é
  desnecessária para a tarefa. São ~16,7 mil tokens a mais, relidos em todos os turnos.
  Os cookies nem eram necessários: a API responde sem eles.
- **O tempo é dominado pela taxa de requisições, não pela IA.** A amostra exige 268
  requisições de qualquer jeito.
- **O resultado é o mesmo; o formato do CSV, não.** Os nomes e a ordem das colunas de
  contexto diferem entre as rodadas (a Rodada 2 não tem `mesTabelaReferencia` e acrescenta
  `ZeroKm`).

## Rodada 3: executar com conhecimento estruturado

- **Data:** 2026-10-06, marco `inicio-fipe-destilado` (01:12:53 UTC)
- **Prompt:** a mesma tarefa, mais o conhecimento do Rafael reescrito em 5 passos: endpoint,
  corpo e o que extrair de cada resposta. Sem cookies, cabeçalhos de navegador ou listas.
  Não menciona o HTTP 429 nem os códigos de combustível de elétrico, flex e híbrido.
  Limite: 60 req/min.
- **Entregáveis:** `fipe/rodada3-destilado/`
- **Medição completa:** `medicao/execucao-fipe-destilado.json`

## As três rodadas lado a lado

| Métrica | 1. Explorar | 2. Conhecimento copiado | 3. Conhecimento estruturado |
|---|---|---|---|
| Duração | 14 min 34 s | 16 min 45 s | **12 min 36 s** |
| Chamadas ao modelo | 28 | 18 | 19 |
| Uso de ferramentas | 34 | 19 | 20 |
| Tamanho do prompt | 6.526 caracteres | 31.950 caracteres | 9.179 caracteres |
| Contexto no 1º turno | 61.503 tokens | 78.178 tokens | 62.936 tokens |
| Escrita de cache | 111.865 | 196.945 | **94.292** |
| Leitura de cache | 2.405.844 | 1.536.919 | **1.456.238** |
| Saída (estimada) | ~14.691 | ~12.333 | **~10.462** |
| Total processado | ~2.532.456 | ~1.746.233 | **~1.561.030** |
| Custo estimado | ~US$ 1,82 | ~US$ 1,85 | **~US$ 1,26** |
| Requisições à FIPE | ~510 | ~543 | ~440 (12 com 429) |
| Resultado | 206 linhas | 206 linhas, valores idênticos | 206 linhas, valores idênticos |

Leitura dos números:

- **Conhecimento estruturado foi o mais barato e o mais rápido:** 31% mais barato que explorar
  do zero e 32% mais barato que o conhecimento copiado, com 38% menos tokens processados que a
  exploração.
- **Copiado x estruturado:** o mesmo conhecimento, com o mesmo número de chamadas (18 x 19).
  A diferença de custo vem do peso do prompt (~15 mil tokens a menos, relidos em cada turno).
- **O que o especialista não escreveu, a IA ainda teve de descobrir:** o HTTP 429 do
  Cloudflare, erros que vêm com HTTP 200 e os códigos de combustível 4, 5 e 6. Cada lacuna
  no conhecimento vira tentativa e erro, e tentativa e erro vira token.
## Rodada 4: processo enxuto (4a Opus, 4b Sonnet)

- **Data:** 2026-10-06, marcos `inicio-fipe-4a` e `inicio-fipe-4b`
- **Como rodou:** um processo separado do Claude Code para cada variação (`claude -p`,
  script `medicao/rodar_enxuto.sh`), com contexto limpo e enxuto:
  - só as ferramentas Bash, Read e Write, sem nenhum servidor MCP;
  - prompt de sistema curto (agente `coletor-enxuto`), pedindo para escrever arquivos de uma
    vez e rodar comandos demorados numa única chamada.

  O subagente enxuto não pôde ser usado pela ferramenta de subagentes porque tipos novos só
  carregam no início da sessão. Por isso a medição foi da sessão inteira de cada processo.
  Nessas sessões a saída registrada é exata, e o custo bate com o `total_cost_usd` do próprio
  Claude Code.
- **Prompt:** `medicao/prompt-rodada4.md`. É o conhecimento estruturado do Rafael, mais 6
  armadilhas (429, erro com HTTP 200, combustíveis 1 a 6, só POST, lista `Anos` enganosa,
  espaços no fim) e o formato exato do CSV.
- **Entregáveis:** `fipe/rodada4a-enxuto-opus/` e `fipe/rodada4b-enxuto-sonnet/`
- **Medições:** `medicao/execucao-fipe-4a-enxuto-opus.json` e `medicao/execucao-fipe-4b-enxuto-sonnet.json`

## As cinco rodadas lado a lado

| Métrica | 1. Explorar | 2. Copiado | 3. Estruturado | 4a. Enxuto Opus | 4b. Enxuto Sonnet |
|---|---|---|---|---|---|
| Duração | 14 min 34 s | 16 min 45 s | 12 min 36 s | 10 min 18 s | 9 min 52 s |
| Chamadas ao modelo | 28 | 18 | 19 | **5** | **6** |
| Contexto no 1º turno | 61.503 | 78.178 | 62.936 | **8.183** | **8.193** |
| Contexto no último turno | 111.867 | 108.631 | 94.294 | 19.786 | 17.297 |
| Total processado | ~2.532.456 | ~1.746.233 | ~1.561.030 | **85.817** | **92.241** |
| Custo estimado | ~US$ 1,82 | ~US$ 1,85 | ~US$ 1,26 | **~US$ 0,38** | **~US$ 0,17** |
| Resultado | 206 linhas | 206, iguais | 206, iguais | 206, iguais | 206, iguais |
| CSV no formato pedido | — | — | — | sim | sim |

Leitura dos números:

- **De US$ 1,82 para US$ 0,17: 91% mais barato**, com o mesmo resultado, e o CSV saiu
  exatamente no formato pedido.
- **Com o mesmo Opus, a 4a custou 70% menos que a Rodada 3**, com três mudanças juntas:
  - contexto menor: o processo começa com ~5,6 mil tokens de sistema, contra 61,5 mil do
    subagente padrão; com o prompt, o 1º turno fica em ~8,2 mil, e a sessão termina abaixo
    de 20 mil (as outras terminavam entre 94 e 112 mil);
  - menos voltas: 5 em vez de 19, porque a amostra rodou numa única chamada;
  - conhecimento completo: as armadilhas e o formato do CSV estavam no prompt.

  Com uma rodada só, não dá para separar quanto veio de cada mudança.
- **O Sonnet cortou mais 56%** sobre a 4a, pela metade do preço por token e com o mesmo
  resultado. Com o conhecimento estruturado, a tarefa vira execução e não precisa do modelo
  mais forte.
- **Ressalva da 4b:** no fim, o Sonnet corrigiu a conta de tempo do `--estimar` e não rodou
  a estimativa de novo; só conferiu a sintaxe.

## Observações gerais

- **Os dados são os mesmos nas três primeiras rodadas, mas o formato do CSV não.** A Rodada 3 usa `;`
  como separador. Cada execução escolheu nomes, ordem e separador diferentes. Quem quer
  output padronizado precisa especificar o formato no prompt.
