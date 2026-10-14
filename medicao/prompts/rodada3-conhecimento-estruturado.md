<!-- Prompt enviado ao subagente da Rodada 3, extraído do transcript. Tamanho original: 9,179 caracteres. -->

Você vai coletar os dados da consulta de MOTOS da Tabela FIPE (marcas, modelos, anos e o valor FIPE de cada combinação) e deixar pronto um jeito automatizado de coletar todos esses dados, usando o conhecimento passado abaixo por quem já conhece a API.

Regras:
- Trabalhe a partir do conhecimento abaixo. Não leia nenhum outro arquivo do repositório nem pastas temporárias, e não consulte memórias ou buscas de sessões anteriores (por exemplo, ferramentas ctx_search). Em especial, não abra nada em fipe\rodada1-exploracao nem em fipe\rodada2-conhecimento.
- Limite de taxa: no máximo 60 requisições por minuto ao servidor da FIPE, sem paralelismo, reaproveitando respostas já obtidas.
- NÃO rode a coleta completa de todas as motos. Valide o coletor numa amostra: a marca Royal Enfield inteira (todos os modelos, todos os anos, com valores) no mês de referência mais recente.

Entregáveis, todos em fipe\rodada3-destilado\ :
1. API.md: documentação da API. Endpoints, método HTTP, parâmetros, cabeçalhos necessários, formato e exemplo das respostas, a sequência de chamadas para chegar ao valor de uma moto, códigos de tipo de veículo, e armadilhas encontradas (erros, limites, parâmetros obrigatórios, etc.).
2. coletor_fipe.py: script Python (só biblioteca padrão) que coleta todas as marcas, modelos, anos e valores de motos para um mês de referência, com controle de taxa, cache em disco das respostas e retomada se for interrompido. Saída em CSV com uma linha por moto/ano e todas as colunas que a API devolve. Deve aceitar um filtro de marca, para rodar a amostra.
3. amostra_royal_enfield.csv: o resultado da validação na Royal Enfield.
4. Uma estimativa do tamanho da coleta completa (quantas marcas, modelos e combinações modelo/ano, quantas requisições e quanto tempo levaria na taxa permitida).
5. diario.md: um diário curto do seu processo (o que tentou, o que deu errado, como resolveu cada coisa), útil para uma palestra sobre o custo da IA trabalhar com uma API.

Ao terminar, responda com um resumo curto: endpoints usados, sequência de chamadas, números da amostra e a estimativa da coleta completa.

===== CONHECIMENTO PASSADO PELO ESPECIALISTA (texto original) =====

1. **Consultar Tabela de Referência:** Obtém o código do mês atualizado.
**Endpoint:** `POST [https://veiculos.fipe.org.br/api/veiculos/ConsultarTabelaDeReferencia](https://veiculos.fipe.org.br/api/veiculos/ConsultarTabelaDeReferencia)`
**Headers:** Padrão FIPE (necessário `Content-Type: application/x-www-form-urlencoded; charset=UTF-8` nos próximos)
**Body:** Vazio
**Retorno:** Extraia o `Codigo` do mês desejado (ex: `338` para Outubro/2026). Será o `codigoTabelaReferencia`.


2. **Consultar Marcas:**
**Endpoint:** `POST [https://veiculos.fipe.org.br/api/veiculos/ConsultarMarcas](https://veiculos.fipe.org.br/api/veiculos/ConsultarMarcas)`
**Body:** `codigoTabelaReferencia=338&codigoTipoVeiculo=2`
*(Códigos de tipoVeiculo: 1 = Carros, 2 = Motos, 3 = Caminhões)*
**Retorno:** Extraia o `Value` da marca desejada (ex: `131` para Amazonas). Será o `codigoMarca`.


3. **Consultar Modelos:**
**Endpoint:** `POST [https://veiculos.fipe.org.br/api/veiculos/ConsultarModelos](https://veiculos.fipe.org.br/api/veiculos/ConsultarModelos)`
**Body:** `codigoTipoVeiculo=2&codigoTabelaReferencia=338&codigoMarca=131`
**Retorno:** Extraia o `Value` de dentro do objeto `Modelos` (ex: `4361`). Será o `codigoModelo`.


4. **Consultar Ano e Combustível:** Mapeia as versões disponíveis do modelo.
**Endpoint:** `POST [https://veiculos.fipe.org.br/api/veiculos/ConsultarAnoModelo](https://veiculos.fipe.org.br/api/veiculos/ConsultarAnoModelo)`
**Body:** `codigoTipoVeiculo=2&codigoTabelaReferencia=338&codigoMarca=131&codigoModelo=4361`
**Retorno:** Extraia o `Value`. Ele retorna no formato `anoModelo-codigoTipoCombustivel` (ex: `2008-1`).
*(Códigos de Combustível: 1 = Gasolina, 2 = Álcool, 3 = Diesel)*


5. **Consultar Valor Final:** Retorna a avaliação oficial e o Código Fipe.
**Endpoint:** `POST [https://veiculos.fipe.org.br/api/veiculos/ConsultarValorComTodosParametros](https://veiculos.fipe.org.br/api/veiculos/ConsultarValorComTodosParametros)`
**Body:** `codigoTabelaReferencia=338&codigoMarca=131&codigoModelo=4361&codigoTipoVeiculo=2&anoModelo=2008&codigoTipoCombustivel=1&tipoVeiculo=moto&tipoConsulta=tradicional`
*(Nota: `anoModelo` e `codigoTipoCombustivel` são separados aqui. `tipoVeiculo` passa a ser a string literal `carro`, `moto` ou `caminhao`)*
**Retorno:** JSON final contendo `Valor`, `Marca`, `Modelo`, `AnoModelo`, `Combustivel`, `CodigoFipe` e `MesReferencia`.

===== FIM DO CONHECIMENTO =====
<context_window_protection>
  <priority_instructions>
    Every byte a tool returns enters your conversation memory and costs reasoning capacity for the rest of the session. The context-mode tools let you do the work in a sandbox and surface only the derived answer — the raw bytes stay out. Think-in-Code: program the analysis, do not compute it by reading raw data into your conversation.
  </priority_instructions>

  <deferred_tool_bootstrap>
    The context-mode tools below may be DEFERRED in your harness — their schemas are not loaded yet, so calling them directly fails (e.g. "tool not found" / InputValidationError). Load them ONCE before your first ctx_* call:
    ToolSearch(query: "select:mcp__plugin_context-mode_context-mode__ctx_batch_execute,mcp__plugin_context-mode_context-mode__ctx_search,mcp__plugin_context-mode_context-mode__ctx_execute,mcp__plugin_context-mode_context-mode__ctx_execute_file,mcp__plugin_context-mode_context-mode__ctx_fetch_and_index")
    After that they are callable. If any ctx_* call fails as not-found, ToolSearch it and retry — do NOT fall back to Bash/Read just because the schema was not loaded yet.
  </deferred_tool_bootstrap>

  <tool_selection_hierarchy>
    0. MEMORY: mcp__plugin_context-mode_context-mode__ctx_search(sort: "timeline")
       - On resume or compaction, query prior decisions, errors, plans, user prompts before asking the user — auto-captured session memory is searchable.
    1. GATHER: mcp__plugin_context-mode_context-mode__ctx_batch_execute(commands, queries)
       - Primary research tool. Runs commands in parallel, auto-indexes each output, and (when queries are passed) returns matching sections in the same round trip — no follow-up search call.
       - Each command: {label: "section header", command: "shell command"}; the label becomes the FTS5 chunk title — descriptive labels improve search.
    2. FOLLOW-UP: mcp__plugin_context-mode_context-mode__ctx_search(queries: ["q1", "q2", ...])
       - Multiple related questions about anything already indexed (your captures + session memory). Batch every question in one array; the ranking pipeline runs per-query and the round-trip cost is paid once.
    3. PROCESSING: mcp__plugin_context-mode_context-mode__ctx_execute(language, code) | mcp__plugin_context-mode_context-mode__ctx_execute_file(path, language, code)
       - Derive answers FROM data: filter, count, aggregate, parse, transform. Only what you console.log() enters your conversation; the raw bytes stay in the sandbox.
  </tool_selection_hierarchy>

  <when_not_to_use>
    - You intend to PROCESS the output (filter, count, parse, aggregate) → use mcp__plugin_context-mode_context-mode__ctx_batch_execute or mcp__plugin_context-mode_context-mode__ctx_execute. Bash stays correct when you intend to OBSERVE a short fixed output (git status on a clean tree, whoami, pwd) or when you are mutating state (git, mkdir, rm, mv, navigation).
    - You want to analyze, summarize, or extract from a file → use mcp__plugin_context-mode_context-mode__ctx_execute_file. Read stays correct when you intend to Edit the file (Edit needs the exact bytes in your conversation to match against).
    - WebFetch → use mcp__plugin_context-mode_context-mode__ctx_fetch_and_index; full network access, results indexed for mcp__plugin_context-mode_context-mode__ctx_search, raw page bytes never enter your conversation.
    - mcp__plugin_context-mode_context-mode__ctx_execute and mcp__plugin_context-mode_context-mode__ctx_execute_file for file writes → these run code in a subprocess and discard the sandbox FS; they are for analysis, processing, and computation only.
  </when_not_to_use>

  <file_writing_policy>
    File writes use the native Write or Edit tool — mcp__plugin_context-mode_context-mode__ctx_execute, mcp__plugin_context-mode_context-mode__ctx_execute_file, and Bash subprocesses do not persist edits to the host filesystem.
    Applies to all file types: code, configs, plans, specs, YAML, JSON, markdown.
  </file_writing_policy>

  <output_constraints>
    <artifact_policy>
      Write artifacts (code, configs, PRDs) to files. Return only: file path + 1-line description.
    </artifact_policy>
  </output_constraints>
  <session_continuity>
    Skills, roles, and decisions set during this session remain active until the user revokes them.
    Do not drop behavioral directives as context grows.
  </session_continuity>

</context_window_protection>