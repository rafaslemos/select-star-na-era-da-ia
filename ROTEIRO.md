# Roteiro de ensaio: SELECT * na era da IA

SQL Saturday Florianópolis 2026 · 45 minutos · 29 slides

Deck: `slides/index.html` (o link publicado no Apps Script não vai no repositório público)
(para abrir: `python -m http.server 8765 --directory slides`)

---

## A tese em uma frase

> A IA não substitui quem entende a fonte de dados: ela multiplica o valor dessa pessoa.
> Conhecer a API e entregar esse conhecimento do jeito certo derrubou o custo de US$ 1,82 para US$ 0,17, com o mesmo resultado.

## A história que o deck conta

1. **Gancho:** pedimos para a IA descobrir sozinha a API da Tabela FIPE. Funcionou, mas custou 2,5 milhões de tokens para aprender a buscar 206 linhas.
2. **Mecânica:** o modelo não tem memória; a cada volta do loop ele relê tudo. O custo mora no contexto.
3. **Ponte com SQL:** SELECT *, WHERE, JOIN, estatísticas e plano de execução têm equivalentes diretos no mundo das APIs com IA.
4. **Experimento:** a mesma tarefa em cinco rodadas, mudando só o que a IA recebe e onde ela roda. Placar real, medido.
5. **Por que caiu:** custo ≈ contexto × voltas + o que a IA escreve. O trabalho útil custa sempre ~US$ 0,21; o resto era desperdício.
6. **Para levar:** anatomia do prompt, caixa de ferramentas do tamanho da tarefa, meça antes de otimizar, checklist.

---

## Antes do evento

**Uma semana antes**
- [ ] Ensaiar com cronômetro pelo menos duas vezes inteiras.
- [ ] Ensaiar a demo ao vivo (slide 21) na rede de casa e numa rede de celular.
- [ ] Testar os dois QR codes do último slide com o celular, de longe, na tela do evento.
- [ ] Os números foram medidos em 5 e 6 de outubro de 2026, com a tabela de outubro/2026. Se alguém consultar a FIPE no dia, os valores podem ter mudado; diga "medido em outubro".

**No dia**
- [ ] Abrir o link publicado logado na conta Google (ele exige login) e testar `F` (tela cheia).
- [ ] Ter a versão local aberta como plano B, caso a internet do evento falhe.
- [ ] **Notas do apresentador:** a tecla `N` mostra as notas na própria tela projetada. Não use no palco; leve este roteiro impresso ou aberto no celular ou tablet.
- [ ] Terminal pronto para a demo, já na pasta certa, fonte grande (ver slide 21).
- [ ] Ter `fipe/rodada4a-enxuto-opus/amostra_royal_enfield.csv` à mão para mostrar se a demo falhar.

**Teclas do deck:** `→` ou espaço avança (inclusive os itens que aparecem por etapas), `←` volta, `F` tela cheia, `O` visão geral (clique num slide para ir até ele), `Home` / `End` início e fim.

---

## Cronograma

| Bloco | Slides | Início | Duração |
|---|---|---|---|
| Abertura e gancho | 1–4 | 0:00 | 6 min |
| Parte 1 · Como a IA conversa com uma API | 5–7 | 6:00 | 5 min |
| Parte 2 · Você já viu esse filme | 8–11 | 11:00 | 7 min |
| Parte 3 · O experimento (rodadas 1 a 3) | 12–17 | 18:00 | 9 min |
| Rodada 4 e placar final | 18–20 | 27:00 | 5 min |
| A coleta (demo) e Para levar | 21–24 | 32:00 | 6 min |
| Fechamento | 25–28 | 38:00 | 3 min |
| Obrigado e perguntas | 29 | 41:00 | 4 min |

**Se atrasar:** encurte o slide 7 (vá direto à caixa de números), passe rápido pelo 13 (os cards se explicam) e pule a demo ao vivo (mostre o CSV pronto). Não corte os slides 19 e 20: são o clímax.

---

## Slide a slide

Cada bloco traz: o que está na tela, o que falar (sugestão, não decore palavra por palavra), os números que você precisa saber e a transição para o próximo slide.

### Abertura e gancho (0:00 – 6:00)

**1. Capa · "SELECT * na era da IA"** · 1 min
- **Falar:** apresentação rápida (nome, Chora API). Pergunta para a plateia: "Quem aqui já levou bronca por um SELECT * em produção?"
- **Por quê:** a plateia de banco reconhece a dor na hora. Toda a palestra vai traduzir essa dor para a IA.
- **Transição:** "Hoje a gente vai ver o SELECT * acontecendo de um jeito novo: dentro da IA."

**2. A pergunta · "Quanto vale, na Tabela FIPE, cada moto da Royal Enfield?"** · 2 min
- **Tela:** a pergunta; depois aparecem "206 linhas" e "o site da FIPE não tem API documentada".
- **Falar:** "Todo mundo aqui já consultou a FIPE no navegador. Alguém sabe como o site busca esses dados?" (ninguém sabe). "A IA também não sabia. Então pedimos para ela descobrir sozinha, só com o link do site."
- **Saber:** 59 modelos, 206 combinações modelo/ano, tabela de outubro/2026.

**3. No escuro · "No escuro, a IA investiga por tentativa e erro."** · 2 min
- **Tela:** cinco linhas de terminal, aparecendo uma a uma. Leia em voz alta, com calma:
  1. Baixou o HTML e o JavaScript do site e achou os endpoints `/api/veiculos/...`. "Dois downloads, nenhum palpite: foi esperta."
  2. GET deu 404: "o endpoint só aceita POST. Quem testa no navegador acha que ele nem existe."
  3. POST sem parâmetros: HTTP 200 com "Parâmetros inválidos". "O status diz que deu certo. Não deu."
  4. Sem o tipo de veículo, a API assume carro e responde "nada encontrado". "Armadilha silenciosa."
  5. A 1,7 requisição por segundo, o Cloudflare bloqueou (429). "Isso não está escrito em lugar nenhum."
- **Transição:** "E quanto custou essa investigação?"

**4. O tamanho do estrago · "2.532.456 tokens"** · 1 min
- **Tela:** o número conta até 2.532.456; depois "14 min 34 s · 28 chamadas ao modelo · ~US$ 1,82 · ~510 requisições ao site da FIPE".
- **Falar:** pausa. "Dois milhões e meio de tokens para aprender a buscar 206 linhas."
- **Saber:** medido de verdade, num subagente do Claude Code (Claude Opus 5.5) com contexto limpo, somando o `usage` do transcript.
- **Transição:** "Para entender de onde vem esse número, precisamos ver como a IA conversa com uma API."

### Parte 1 · Como a IA conversa com uma API (6:00 – 11:00)

**5. Seção · "Como a IA conversa com uma API"** · 15 s
- Só leia o título e avance.

**6. O loop do agente · "Cada volta do loop reenvia tudo."** · 2 min
- **Tela:** Pergunta → Modelo → Ferramenta → Resposta, e a seta de volta.
- **Falar:** "O modelo não tem memória. A cada volta, o programa reenvia tudo: instruções, ferramentas, histórico e a resposta nova. O que entrou na volta 2 é pago de novo na 3, na 4, na 5…"
- **Se perguntarem sobre MCP:** "É só um jeito padronizado de expor ferramentas para a IA. O custo não está no protocolo, está no que entra no contexto."

**7. Onde vão os tokens · "Onde os tokens foram gastos"** · 2 min 30 s
- **Tela:** à esquerda, quatro itens; à direita, a caixa com os números do subagente da Rodada 1.
- **Falar:** "Antes da primeira pergunta sobre a FIPE, o agente já carregava 61 mil tokens: instruções e ferramentas. A cada descoberta, o contexto cresce, e tudo é relido em cada volta."
- **Saber:**
  - 1º turno: 61.503 tokens; último turno: 111.867.
  - 28 voltas = 2.405.844 tokens relidos do cache.
  - Saída (o que a IA escreveu): ~14.700 tokens, menos de 1% do total.
- **Frase de efeito:** "O que a IA escreve é barato. O caro é ela reler."

### Parte 2 · Você já viu esse filme (11:00 – 18:00)

**8. Seção · "Você já viu esse filme."** · 15 s
- "Tudo o que vocês aprenderam otimizando query vale aqui."

**9. SQL x API · "De SQL para API, de API para IA"** · 2 min 30 s
- **Tela:** tabela com cinco linhas, aparecendo uma a uma.

| No banco | Na API | Para a IA | O que falar |
|---|---|---|---|
| SELECT * | sem seleção de campos | resposta gigante no contexto | "Trazer tudo e filtrar depois, só que agora o 'depois' é o contexto do modelo." |
| WHERE | parâmetros da requisição | filtrar na fonte | "Filtre no servidor, não no prompt." |
| JOIN | uma chamada por nível | o loop fica no código | "A API não tem JOIN; vamos ver no próximo slide." |
| Estatísticas | documentação e limites | conhecimento estruturado no prompt | "O otimizador sem estatísticas descobre o custo executando. A IA sem conhecimento também." |
| Plano de execução | log de chamadas | `usage` | "Cada resposta da IA traz o recibo de tokens. É o nosso plano de execução." |

**10. A mesma consulta · SQL x API da FIPE** · 2 min
- **Tela:** à esquerda, um SELECT com três JOINs; à direita, as cinco chamadas da FIPE com a contagem.
- **Falar:** "No banco, uma consulta. Na API da FIPE, 1 + 1 + 1 + 59 + 206 = 268 requisições, a 1 por segundo. O JOIN virou um loop aninhado."
- **Saber:** para todas as motos são 103 marcas, 2.037 modelos, ~9.700 preços e ~11.800 requisições. "Se o modelo fizer esse loop, cada resposta passa pelo contexto."

**11. As armadilhas · "A API da FIPE não avisa quando você erra."** · 2 min
- **Tela:** quatro itens:
  1. erro com HTTP 200;
  2. sem tipo de veículo, ela assume carro;
  3. `tipoConsulta=tradicional` é obrigatório e não aparece em lugar óbvio;
  4. o Cloudflare bloqueia (429) abaixo de 2 req/s.
- **Falar:** "Cada uma dessas custou pelo menos uma volta do loop. Quem conhece a API sabe disso antes de começar. E é exatamente esse conhecimento que vamos testar."

### Parte 3 · O experimento (18:00 – 27:00)

**12. Seção · "Mesma tarefa. Três prompts."** · 30 s
- **Falar:** "Mapear a API e coletar as 206 motos da Royal Enfield. Três subagentes com contexto limpo, um de cada vez. A tarefa e as entregas são iguais; muda só o que vai no prompt."
- **Saber, se perguntarem:**
  - **Entregas pedidas a todos:** documentação da API, coletor em Python (controle de taxa, cache, retomada), amostra da Royal Enfield em CSV, estimativa da coleta completa e um diário do processo.
  - **Regras:** no máximo 60 requisições por minuto (a Rodada 1 podia até 2 por segundo) e nada de coleta completa.

**13. As três rodadas** · 1 min 30 s
- **01 Explorar:** só o link do site.
- **02 Conhecimento copiado:** "Os 6 `curl` que eu copiei do DevTools do navegador, com cabeçalhos, cookies e a lista de 310 meses. Do jeito que a gente faz no dia a dia."
- **03 Conhecimento estruturado:** "O mesmo conhecimento, reescrito em 5 passos: endpoint, corpo e o que extrair."

**14. Copiado x estruturado** · 1 min 30 s
- **Tela:** à esquerda, o `curl` com cookies (31.950 caracteres); à direita, o passo 2 estruturado (9.179 caracteres).
- **Falar:** "É o mesmo conhecimento. Um tem 32 mil caracteres, o outro 9 mil. E os cookies nem eram necessários: a API responde sem eles."

**15. Placar · "Mesmo resultado, contas diferentes"** · 2 min
- **Tela:** três barras.

| Rodada | Tempo | Chamadas | Tokens | Custo |
|---|---|---|---|---|
| 1. Explorar | 14 min 34 s | 28 | 2,53 mi | US$ 1,82 |
| 2. Copiado | 16 min 45 s | 18 | 1,75 mi | US$ 1,85 |
| 3. Estruturado | 12 min 36 s | 19 | 1,56 mi | US$ 1,26 |

- **Falar:** "Nas três: 206 linhas e os mesmos 206 valores. O estruturado saiu 31% mais barato que explorar." Deixe a plateia notar que o copiado custou mais que explorar.
- **Saber:** o tempo é dominado pela taxa de requisições, não pela IA (a amostra exige ~270 requisições de qualquer jeito). A Rodada 2 rodou a 1 por segundo; a Rodada 1, a até 2.

**16. Conhecimento ocupa contexto · "Conhecimento copiado custou o mesmo que não saber nada."** · 1 min 30 s
- **Falar:**
  - "Copiado e estruturado fizeram o mesmo trabalho: 18 e 19 chamadas, contra 28 explorando."
  - "A diferença de custo é só o peso do prompt: uns 15 mil tokens de cabeçalhos e listas, relidos em cada volta."
  - Fechamento: "Conhecer a API corta o trabalho. Estruturar o conhecimento corta a conta."

**17. As lacunas · "Cada lacuna vira tentativa e erro. E tentativa e erro vira token."** · 1 min 30 s
- **Tela:** o que o conhecimento estruturado não citava: o 429, os erros com HTTP 200 e os combustíveis 4, 5 e 6.
- **Falar:** "O 429 e o erro com HTTP 200 foram redescobertos nas três rodadas."
- **Se perguntarem sobre combustível:** "As três rodadas leem o código que vem no ano, como 2020-1, e acertam o valor. Só a Rodada 2 documentou os códigos 4, 5 e 6; a 1 nunca topou com eles, e a 3 achou que eram só de carros, mas existe moto flex. Faltar conhecimento não quebrou o dado: deixou a documentação incompleta."
- **Transição:** "E se a gente fechar essas lacunas e ainda diminuir o contexto?"

### Rodada 4 e placar final (27:00 – 32:00)

**18. Rodada 4 · "O que fizemos para cortar a conta"** · 2 min
- **Tela:** à esquerda, quatro mudanças; à direita, os cartões 4a (Opus, US$ 0,38) e 4b (Sonnet, US$ 0,17).
- **Falar, item a item:**
  1. **Agente enxuto:** só Bash, Read e Write, sem servidores MCP. "Contexto inicial de 61,5 mil para 8,2 mil tokens."
  2. **Menos voltas:** coletor escrito de uma vez, amostra rodada numa única chamada. "De 19 para 5 chamadas."
  3. **Lacunas fechadas:** as 6 armadilhas e o formato do CSV no prompt. "Nada redescoberto, e o CSV veio certo de primeira."
  4. **Modelo certo para a tarefa:** "Com o conhecimento pronto, executar não exige o modelo mais forte."
- **Saber, se perguntarem como rodou:** cada variação foi um processo separado do Claude Code (`claude -p`), com contexto limpo, só três ferramentas, nenhum servidor MCP e um prompt de sistema curto (script `medicao/rodar_enxuto.sh`). Nas duas, os mesmos 206 valores; ~10 minutos, quase tudo esperando o limite de 60 requisições por minuto.

**19. Por que caiu tanto · "O trabalho útil custou o mesmo. O desperdício sumiu."** · 2 min · **o slide mais importante**
- **Tela:** a fórmula `custo ≈ contexto × voltas + o que a IA escreve` e duas barras empilhadas:

| Parte do custo | Rodada 3 | Rodada 4a |
|---|---|---|
| Reler o contexto | US$ 0,58 | US$ 0,02 |
| Guardar contexto novo no cache | US$ 0,47 | US$ 0,14 |
| Escrever código e documentação | US$ 0,21 | US$ 0,22 |
| **Total** | **US$ 1,26** | **US$ 0,38** |

- **Falar:** "Olhem a faixa branca: escrever o coletor custou praticamente o mesmo nas duas. A IA fez o mesmo trabalho. O que sumiu foi o laranja: reler e guardar contexto."
- **A conta, se quiserem detalhe:** na Rodada 3, um contexto de 63 a 94 mil tokens relido 19 vezes = 1,46 milhão de tokens relidos. Na 4a, de 8 a 20 mil relido 5 vezes = 58 mil. Contexto ~7× menor × ~4× menos voltas = ~25× menos releitura.
- **Mesmo modelo:** a comparação é Opus contra Opus. A troca de modelo vem no próximo slide.

**20. Placar final · "Mesmos 206 valores, cinco contas"** · 1 min
- **Tela:** cinco barras: 1,82 · 1,85 · 1,26 · 0,38 · **0,17**.
- **Falar:** "De explorar no escuro ao agente enxuto: 91% mais barato, com o mesmo resultado."
- **Ser honesto se perguntarem de onde veio cada parte:**
  - Da Rodada 3 para a 4a (mesmo modelo): −70%, com três mudanças juntas (contexto menor, menos voltas e conhecimento completo). Uma rodada só não separa quanto veio de cada uma.
  - Da 4a para a 4b: −56%, só pela troca de modelo, com todo o resto idêntico.

### A coleta e Para levar (32:00 – 38:00)

**21. A coleta · "A coleta completa da FIPE"** · 2 min (com demo)
- **Tela:** tabela com os três tipos, carros em destaque:

| Tipo | Marcas | Modelos | Preços | Requisições | Tempo a 60/min |
|---|---|---|---|---|---|
| Motos | 103 | 2.037 | ~9.700 | ~11.800 | ~3,4 h |
| Caminhões | 29 | 2.000 | ~11.600 | ~14.000 | ~3,9 h |
| Carros | 108 | 7.385 | ~30.800 | ~39.400 | ~11 h |

  Embaixo: "Feito pelo coletor que a IA escreveu, com --tipo moto|carro|caminhao: zero token."
- **Falar:** "Para carros são quase 40 mil requisições e 11 horas. Se a IA fizesse esse loop, cada resposta passaria pelo contexto do modelo. O coletor faz com zero token."
- **Se perguntarem:** são estimativas do próprio coletor (marcas e modelos contados, anos por amostra de 60 modelos). Nenhuma coleta completa foi rodada. Cada tipo foi testado numa marca: Royal Enfield, MAN e Cadillac.
- **Falar:** "A IA aprende a API uma vez. O código coleta para sempre."
- **Demo ao vivo (opcional, ~1 min):** a AMAZONAS tem só 4 modelos, cerca de 20 requisições.
  ```bash
  cd fipe/rodada4a-enxuto-opus
  python coletor_fipe.py --marca AMAZONAS --csv amazonas.csv --cache cache-demo
  ```
  - Antes do evento, apague a pasta `cache-demo` depois de cada ensaio para a demo fazer requisições de verdade. Se quiser uma demo instantânea, deixe o cache: tudo sai do disco.
  - **Plano B:** abra `amostra_royal_enfield.csv` da mesma pasta.
- **Saber:** a coleta completa não foi rodada; os números são a estimativa dos próprios coletores (contagem exata de marcas e modelos, anos estimados por amostra).

**22. Anatomia do prompt · "Anatomia de um prompt estruturado"** · 1 min 30 s
- **Tela:** tabela com cinco blocos (Tarefa, Regras, Conhecimento, Armadilhas, Saída), o que entra em cada um e o que evitar.
- **Falar:** "Isso serve para qualquer API. O que importa é não faltar armadilha nem formato, e não sobrar ruído, porque tudo é relido a cada volta."
- **Saber:** o prompt completo da Rodada 4 está em `medicao/prompt-rodada4.md`.

**23. Caixa de ferramentas · "Caixa de ferramentas do tamanho da tarefa"** · 1 min 30 s
- **Tela:** o arquivo do agente `coletor-enxuto` e "61,5 mil → 5,6 mil" tokens antes da primeira pergunta.
- **Falar:** "Tudo o que está ligado na sessão entra no contexto de toda volta, mesmo sem ser usado. Nosso agente padrão carregava navegador, Figma, Gmail, Drive… para coletar a FIPE." Depois as quatro formas:
  1. um subagente por tipo de trabalho;
  2. um processo separado (`claude -p`) para tarefas repetidas;
  3. conectores e MCP ligados só quando a tarefa pede;
  4. uma conversa por assunto.
- **Saber:** tipos novos de subagente só carregam no início da sessão; foi por isso que a Rodada 4 rodou como processo separado.

**24. Meça · "Faça o que eu digo… uma conversa por assunto"** · 1 min
- **Tela:** "~204 mil tokens relidos a cada resposta" (a conversa em que preparei a palestra) contra "~11 mil" (Rodada 4b).
- **Falar, com bom humor:** "A conversa em que eu preparei esta palestra misturou tudo: demo, slides, publicação. Cada resposta relia uns 204 mil tokens. Uma tarefa com contexto limpo relê 11 mil."
- **Cuidado:** não diga que foi a mesma tarefa. A comparação justa é por resposta. Os totais (US$ 11,46 em 76 respostas, contra US$ 0,17 em 6) são de trabalhos diferentes.
- **Frase de baixo:** "Cada resposta traz um recibo, o `usage`. Ele mostra onde está o custo antes de você otimizar. Está no transcript da sessão e no `claude -p --output-format json`."

### Fechamento (38:00 – 41:00)

**25. A lição · "Empurre o trabalho para o lugar mais barato. O mais caro é o contexto do modelo."** · 45 s
- **Falar:** "Você estrutura, a IA escreve o código, o código coleta. Cada um faz o que é mais barato fazer."

**26. Checklist · "Antes de soltar a IA na API"** · 1 min
- **Tela:** seis práticas, cada uma com o número medido:

| Prática | O que medimos |
|---|---|
| Estruture o conhecimento | copiado → estruturado: −32% |
| Escreva armadilhas e formato | nada redescoberto; CSV certo de primeira |
| Caixa do tamanho da tarefa | 61,5 mil → 5,6 mil tokens de partida |
| Menos voltas | 19 → 5 chamadas |
| Modelo certo para a tarefa | Opus → Sonnet: −56% |
| Loop com o código | coleta completa com zero token |

- **Falar:** "Se vocês tirarem uma foto de um slide só, que seja este."

**27. Quem expõe API ou MCP · "Projete ferramentas para quem paga por token"** · 45 s
- **Falar:** "Se vocês publicam APIs ou servidores MCP, pensem nisso. Descrições enxutas, porque vão em toda chamada. Respostas pequenas. Endpoints de agregação. E erros claros: a FIPE devolve erro com HTTP 200, e isso custou voltas nas cinco rodadas."

**28. Cuidado · "Economizar demais também erra."** · 30 s
- **Falar:** "O objetivo não é o contexto mínimo, é o contexto certo. Uma resposta errada é o token mais caro que existe."

### Encerramento (41:00 – 45:00)

**29. Obrigado · "A IA não substitui quem entende a fonte de dados. Ela multiplica o valor dessa pessoa."**
- **Tela:** a frase, o GitHub e o LinkedIn, e dois QR codes lado a lado: o do repositório (github.com/rafaslemos/select-star-na-era-da-ia) e o do LinkedIn (/in/orafaslemos).
- **Falar:** leia a frase e agradeça. "Tudo o que vocês viram está no repositório: o deck, os prompts das cinco rodadas, os coletores e o medidor de tokens. É só apontar o celular para o QR code da esquerda; o da direita é o meu LinkedIn."
- Deixe este slide na tela durante as perguntas.

---

## Os números que você precisa saber de cor

| | 1. Explorar | 2. Copiado | 3. Estruturado | 4a. Enxuto Opus | 4b. Enxuto Sonnet |
|---|---|---|---|---|---|
| Tempo | 14 min 34 s | 16 min 45 s | 12 min 36 s | 10 min 18 s | 9 min 52 s |
| Chamadas ao modelo | 28 | 18 | 19 | 5 | 6 |
| Contexto no 1º turno | 61.503 | 78.178 | 62.936 | 8.183 | 8.193 |
| Tokens processados | 2,53 mi | 1,75 mi | 1,56 mi | 85.817 | 92.241 |
| Custo | US$ 1,82 | US$ 1,85 | US$ 1,26 | US$ 0,38 | US$ 0,17 |
| Requisições à FIPE | ~510 | ~543 | ~440 | ~440 | ~440 |

- Resultado igual em todas: 206 linhas, os mesmos 206 valores.
- Royal Enfield: 59 modelos, 206 combinações, 40 Zero KM, de R$ 15.781 a R$ 37.686.
- Coleta completa a 60 por minuto: motos ~11.800 requisições (~3,4 h), caminhões ~14.000 (~3,9 h), carros ~39.400 (~11 h).
- Contexto de partida: 61,5 mil tokens (subagente padrão) contra 5,6 mil (agente enxuto).
- Custo total do experimento (as cinco rodadas mais o teste do processo enxuto): ~US$ 5,53.

## Como foi medido (se perguntarem)

- Cada resposta do modelo traz o `usage`: tokens de entrada, de escrita de cache, de releitura de cache e de saída.
- O script `medicao/medir_sessao.py` grava um marco com a hora antes da tarefa e depois soma o `usage` do transcript (`~/.claude/projects/…/*.jsonl`).
- O custo usa o preço de cada modelo:
  - **Claude Opus 5.5:** US$ 4 de entrada e US$ 20 de saída por milhão de tokens; releitura de cache a 10% da entrada.
  - **Claude Sonnet 5.5:** metade disso.
- **Precisão por rodada:**
  - **Rodadas 1 a 3 (subagentes):** entrada e cache exatos; a saída é estimada pelo texto gerado, porque o transcript de subagente só registra o valor do início da resposta.
  - **Rodadas 4a e 4b (processos separados):** tudo exato, e o custo bateu com o `total_cost_usd` do próprio Claude Code.
- **Limitações honestas:**
  - cada rodada rodou uma vez só, então outra execução pode variar alguns centavos;
  - as rodadas 1 a 3 rodaram como subagentes e as 4a e 4b como processos separados, então o ambiente não é idêntico.

Os detalhes completos estão em `medicao/EXPERIMENTOS.md`.

---

## Perguntas prováveis e como responder

**"O que é exatamente o `usage`?"**
É o recibo de cada resposta do modelo, com quatro campos:

| Campo | O que é | Preço |
|---|---|---|
| `cache_read_input_tokens` | O histórico relido do cache | Barato: 10% da entrada |
| `cache_creation_input_tokens` | O conteúdo novo desta volta, processado e guardado | 1,25× ou 2× a entrada |
| `input_tokens` | Entrada que não entrou no cache | Preço cheio; costuma ser quase zero (na 4b, 12 tokens) |
| `output_tokens` | Tudo o que o modelo escreveu, inclusive o raciocínio e o código | O mais caro: 5× a entrada |

**"Como uso o `usage` para otimizar?"**
Veja qual campo domina:

| Domina… | Significa… | O que fazer |
|---|---|---|
| `cache_read` | Contexto grande relido muitas vezes | Contexto menor e menos voltas |
| `cache_creation` | Resultados grandes entrando no contexto (o SELECT *) | Filtrar na fonte, imprimir resumos |
| `output` | A IA escrevendo ou pensando demais | Pedir só o necessário, especificar a saída |
| `input_tokens` alto | O cache não está funcionando | Algo muda no começo do contexto a cada chamada |

**Analogia de banco:** `cache_read` é como a leitura lógica (página no buffer pool, barata mas não de graça); `cache_creation` é como a leitura física.

**"Se tem cache, por que a releitura ainda pesa?"**
O cache deixa a releitura 10 vezes mais barata, mas não acaba com ela. Na Rodada 3, 1,46 milhão de tokens relidos a 10% do preço ainda custaram US$ 0,58.

**"Um modelo com janela de contexto maior não resolve?"**
É o contrário. Uma janela maior deixa você acumular mais, e tudo o que se acumula é relido a cada volta. Janela maior é capacidade, não economia.

**"Por que a saída é mais cara que a entrada?"**
O modelo lê a entrada de uma vez, em paralelo; gera a saída um token por vez, cada um dependendo do anterior.

**"Então é só usar o modelo mais barato?"**
Não foi isso que deu o maior ganho. Com o mesmo Opus, a Rodada 4a já custou 70% menos que a 3. O modelo mais barato funcionou porque o conhecimento já estava estruturado: a tarefa virou execução. Para explorar algo desconhecido, o modelo mais forte ainda faz sentido.

**"Isso vale para ChatGPT, Gemini, Copilot, Cursor?"**
O conceito vale: os modelos não guardam estado, e o histórico é reenviado a cada chamada. Nomes de campos, preços e regras de cache mudam de provedor para provedor.

**"Pode usar a API da FIPE assim? É permitido?"**
É a API que o próprio site usa, sem documentação oficial nem autenticação. No experimento, respeitamos um limite de 60 requisições por minuto, usamos cache e não rodamos a coleta completa. Para uso comercial, verifique os termos de uso da FIPE.

**"E se a API mudar?"**
O coletor quebra, e aí a IA volta a trabalhar: com o conhecimento estruturado e o erro na mão, a correção é barata. O que muda é que a IA trabalha só quando precisa, não a cada coleta.

**"Dá para fazer com carros e caminhões?"**
Sim: a API é a mesma, muda só o código do tipo de veículo. O coletor aceita `--tipo carro` ou `--tipo caminhao`. A coleta completa de carros é bem maior: 108 marcas, 7.385 modelos, ~30.800 preços, ~39.400 requisições e ~11 horas a 60 por minuto. Caminhões: 29 marcas, 2.000 modelos, ~11.600 preços, ~3,9 horas.

**"Por que não deixar a IA fazer a coleta inteira?"**
Seriam ~11.800 requisições, e cada resposta passaria pelo contexto do modelo. É o SELECT * levado ao extremo. O coletor faz o mesmo trabalho com zero token.

**"Quanto custou o experimento todo?"**
Cerca de US$ 5,53, somando as cinco rodadas e um teste do processo enxuto. A conversa em que preparei a palestra custou bem mais, e virou o slide 24.

**"Por que a Rodada 2 custou mais que explorar do zero?"**
O conhecimento chegou em estado bruto: cabeçalhos, cookies e a lista de 310 meses, uns 15 mil tokens a mais relidos em cada volta. Ela fez menos trabalho (18 chamadas contra 28), mas cada chamada era mais cara.

**"Os CSVs saíram iguais?"**
Os dados sim, nas cinco rodadas. O formato do arquivo não: nas rodadas 1 a 3, cada subagente escolheu nomes de coluna, ordem e separador diferentes. Na Rodada 4, com o formato no prompt, o CSV veio exatamente como pedido.

---

## Glossário rápido

- **Token:** pedaço de texto que o modelo lê ou escreve; em português, uns 3 a 4 caracteres.
- **Contexto:** tudo o que o modelo recebe numa chamada (instruções, ferramentas, histórico, resultados).
- **Volta (ou turno):** uma chamada ao modelo dentro do loop do agente.
- **Cache de prompt:** o provedor guarda o começo já processado do contexto; se a próxima chamada começa igual, esse trecho sai mais barato.
- **Tool calling:** o modelo pede para executar uma ferramenta (por exemplo, uma requisição HTTP) e recebe o resultado.
- **MCP (Model Context Protocol):** um padrão para expor ferramentas e dados para a IA.
- **Subagente:** um agente separado, com contexto próprio, que recebe uma tarefa e devolve só o resumo.
- **`claude -p`:** o Claude Code rodando sem interface, para tarefas automatizadas; com `--output-format json`, devolve o custo da execução.
- **`usage`:** o recibo de tokens de cada resposta do modelo.

## Arquivos de apoio

| Arquivo | Para quê |
|---|---|
| `slides/index.html` | O deck (editar aqui; `slides/build.py` gera a versão do Apps Script) |
| `medicao/EXPERIMENTOS.md` | Resultados completos e leitura dos números |
| `medicao/prompt-rodada4.md` | O prompt estruturado da Rodada 4 (modelo para a plateia) |
| `medicao/rodar_enxuto.sh` | Como a Rodada 4 rodou |
| `medicao/medir_sessao.py` | O medidor de tokens |
| `fipe/rodada*/` | Coletores, amostras e diários de cada rodada |
| `.claude/agents/coletor-enxuto.md` | O agente enxuto mostrado no slide 23 |
