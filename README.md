# SELECT * na era da IA

**Como conhecer a API economiza tokens (e dinheiro)**

Material da palestra de Rafael Lemos ([Chora API Revolution](https://www.linkedin.com/in/orafaslemos/)) no SQL Saturday Florianópolis 2026: o deck, os experimentos e as ferramentas de medição.

## O experimento

A mesma tarefa, feita cinco vezes por agentes do Claude Code com contexto limpo:

> Mapear a API da Tabela FIPE (veiculos.fipe.org.br) para motos, escrever um coletor em Python e validá-lo na marca Royal Enfield inteira (59 modelos, 206 combinações modelo/ano).

Entre as rodadas, muda só o que a IA recebe e onde ela roda:

| Rodada | O que a IA recebeu | Chamadas ao modelo | Tokens processados | Custo |
|---|---|---|---|---|
| 1. Explorar | Só o link do site | 28 | 2,53 milhões | US$ 1,82 |
| 2. Conhecimento copiado | Os `curl` copiados do navegador, com cabeçalhos, cookies e exemplos | 18 | 1,75 milhão | US$ 1,85 |
| 3. Conhecimento estruturado | O mesmo conhecimento em 5 passos | 19 | 1,56 milhão | US$ 1,26 |
| 4a. Agente enxuto (Opus 5.5) | Estruturado + armadilhas + formato da saída, com só 3 ferramentas | 5 | 85.817 | US$ 0,38 |
| 4b. Agente enxuto (Sonnet 5.5) | Igual à 4a, com o Sonnet | 6 | 92.241 | US$ 0,17 |

As cinco rodadas chegaram aos mesmos 206 valores. A explicação dos números está em [medicao/EXPERIMENTOS.md](medicao/EXPERIMENTOS.md). O resumo:

> **custo ≈ contexto × voltas + o que a IA escreve**
>
> Escrever o coletor custou ~US$ 0,21 em todas as rodadas. O resto era a IA relendo o contexto a cada volta do loop.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `slides/` | O deck em HTML (`index.html`), os tokens de marca e o projeto do Google Apps Script |
| `fipe/rodada*/` | O que cada rodada entregou: documentação da API, coletor, amostra em CSV e diário do processo |
| `fipe/padronizar_csv.py` | Converte as amostras das rodadas 1 a 3 para um formato único e confere se os dados são iguais |
| `medicao/` | O medidor de tokens, os prompts de cada rodada, os resultados em JSON e o EXPERIMENTOS.md |
| `.claude/agents/coletor-enxuto.md` | O agente enxuto da Rodada 4 (só Bash, Read e Write) |
| `ROTEIRO.md` | Roteiro de apresentação, slide a slide |

## Como reproduzir

Requisitos: Python 3.10+ (só biblioteca padrão) e, para as rodadas com IA, o [Claude Code](https://claude.com/claude-code) com login feito.

**Ver o deck**

```bash
python -m http.server 8765 --directory slides
```

Abra http://localhost:8765. Teclas: `→` avança, `←` volta, `F` tela cheia, `O` visão geral, `N` notas do apresentador.

**Rodar um coletor (sem IA, zero token)**

O coletor da Rodada 4a é um script Python comum: só biblioteca padrão e requisições ao site da FIPE, sem nenhuma chamada a modelo de IA. A IA gastou tokens para escrevê-lo; rodá-lo não gasta nada.

```bash
cd fipe/rodada4a-enxuto-opus
python coletor_fipe.py --marca AMAZONAS --csv amazonas.csv
```

Opções principais:

| Opção | Para quê |
|---|---|
| `--tipo moto\|carro\|caminhao` | Tipo de veículo (padrão: `moto`) |
| `--marca NOME` | Coleta só uma marca (nome ou código) |
| `--tabela CODIGO` | Mês de referência (padrão: o mais recente) |
| `--estimar` | Só estima o tamanho da coleta completa: conta marcas e modelos e sorteia 60 modelos para estimar os anos |
| `--csv ARQUIVO` | Arquivo de saída (padrão: `fipe_<tipo>.csv`) |
| `--cache PASTA` | Onde guardar as respostas (padrão: `cache/`); rodar de novo reaproveita o que já foi baixado |

```bash
python coletor_fipe.py --tipo carro --estimar      # tamanho da coleta de carros
python coletor_fipe.py --tipo caminhao --marca VOLVO
```

Exemplos de execução, com a saída real:

```console
$ python3 coletor_fipe.py --marca AMAZONAS --csv amazonas.csv --cache cache-amazonas
Tipo: moto; tabela 338 (outubro/2026); marcas selecionadas: 1
[1/1] AMAZONAS: 4 modelos
Linhas: 16; modelos: 4; falhas: 0
CSV: amazonas.csv
Requisicoes HTTP: 18; do cache: 5; 429: 0; erros: 0; tempo: 17s
```

```console
$ python3 coletor_fipe.py --marca HONDA --csv honda.csv --cache honda
Tipo: moto; tabela 338 (outubro/2026); marcas selecionadas: 1
[1/1] HONDA: 187 modelos
Linhas: 1154; modelos: 187; falhas: 0
CSV: honda.csv
Requisicoes HTTP: 618; do cache: 746; 429: 20; erros: 0; tempo: 755s
```

O coletor faz no máximo 1 requisição por segundo, espera e tenta de novo quando recebe HTTP 429, e nunca grava erros no cache. Antes de uma coleta completa, rode `--estimar`: dependendo do tipo, ela pode levar muitas horas.

Tamanho estimado da coleta completa (tabela de outubro/2026, estimativas de 5 a 14 de outubro de 2026):

| Tipo | Marcas | Modelos | Combinações modelo/ano | Requisições | Tempo a 60/min |
|---|---|---|---|---|---|
| Motos | 103 | 2.037 | ~9.700 | ~11.800 | ~3,4 h |
| Caminhões | 29 | 2.000 | ~11.600 (±1.600) | ~14.000 | ~3,9 h |
| Carros | 108 | 7.385 | ~30.800 (±5.400) | ~39.400 | ~11 h |

Marcas e modelos são contagens exatas. O número de anos vem de uma amostra de 60 modelos sorteados, por isso as combinações têm margem.

**Repetir a Rodada 4 e medir**

```bash
bash medicao/rodar_enxuto.sh claude-sonnet-5-5 rodada4b-enxuto-sonnet
```

O resultado, com `total_cost_usd`, sai em `medicao/headless-rodada4b-enxuto-sonnet.json`.

**Medir qualquer sessão do Claude Code**

```bash
python medicao/medir_sessao.py marco antes-da-tarefa
# ... rode a tarefa
python medicao/medir_sessao.py relatorio antes-da-tarefa
```

O medidor soma o `usage` gravado no transcript da sessão (`~/.claude/projects/…/*.jsonl`). Use `--apenas-subagentes` para medir só os subagentes. Nos transcripts de subagente, a saída é estimada pelo texto gerado, porque o `output_tokens` gravado é o do início da resposta.

## Avisos

- **API da FIPE:** os coletores usam os endpoints internos que o próprio site da FIPE usa. Não há API oficial documentada. Os experimentos respeitaram um limite de 60 requisições por minuto, usaram cache e não rodaram a coleta completa. Para uso comercial, verifique os termos de uso da FIPE.
- **Dados:** valores da tabela de outubro de 2026, coletados em 5 e 6 de outubro de 2026.
- **Prompts:** os prompts das rodadas 1 a 3 foram extraídos dos transcripts. No da Rodada 2, os valores dos cookies do navegador foram omitidos; a API não precisa deles.
- **Medição:** cada rodada rodou uma vez. Outra execução pode variar alguns centavos.

## Licença

[MIT](LICENSE): pode usar, copiar, modificar e redistribuir, mantendo o aviso de direitos autorais.
