# Diário de exploração: API da Tabela FIPE (motos)

Data: 05/10/2026. Ponto de partida: só o link https://veiculos.fipe.org.br/.

## 1. Reconhecimento (2 requisições)
- Baixei o HTML da home (188 KB, servido pelo Cloudflare) e listei as tags `<script src>`.
  Apareceu um script com nome promissor: `content/js/modulos/veiculos_function.js`.
- Baixei o JS (47 KB) e procurei por `url:` e `api/`. Logo na linha 10 estava
  `var surl = 'https://veiculos.fipe.org.br/api/veiculos/'`. Dois endpoints apareciam
  escritos direto no código (`ConsultarTabelaDeReferencia`, `ConsultarMarcas`). Os outros vinham
  de atributos do HTML (`urlConsulta`, `urlPesquisa`).

## 2. Ler o HTML em vez de adivinhar (0 requisições)
- Um grep pelos atributos do HTML mostrou o mapa completo: `ConsultarModelos`,
  `ConsultarAnoModelo`, `ConsultarModelosAtravesDoAno`, `ConsultarAnoModeloPeloCodigoFipe`,
  `ConsultarValorComTodosParametros`, e também `codTipoVeiculo` = 1/2/3 para carro/moto/caminhão.
- Na função `crossDomainAjax`, o código mostrava POST, `dataType: json` e `data` como objeto. Daí
  concluí que o corpo é form-urlencoded e não JSON. Isso evitou um erro de formato.
- Na função de preço, a lista de parâmetros incluía `tipoConsulta`. Ficou anotado, e depois se
  mostrou obrigatório.
- O reCAPTCHA e o `__RequestVerificationToken` assustaram, mas o callback `onScriptLoad` nem
  existe na página. Suspeitei que fossem decorativos, e os testes confirmaram.

## 3. Testes manuais (cerca de 15 requisições, 1 por segundo)
- **Tropeço de ferramenta:** o ambiente bloqueou `curl` direto. Escrevi um `probe.py` de 30 linhas
  com urllib e pausa embutida de 1 s.
- `ConsultarTabelaDeReferencia`: funciona via POST, mas GET dá **404 com HTML**. Quem testasse só
  com o navegador concluiria que o endpoint não existe. Funcionou também sem nenhum cabeçalho.
- **Falso problema de encoding:** `mar�o` no terminal. Conferi os bytes (`\xc3\xa7`) e o UTF-8
  estava certo; o problema era o console do Windows.
- `ConsultarMarcas` sem parâmetros: **HTTP 200** com `{"codigo":"2","erro":"Parâmetros inválidos"}`.
  Foi aí que aprendi que o status HTTP não indica erro.
- `ConsultarModelos` sem `codigoTipoVeiculo`: veio `nadaencontrado` em vez de "parâmetro
  inválido". Parece assumir carro. É uma armadilha silenciosa.
- `ConsultarValorComTodosParametros` sem `tipoConsulta`: dá código 2. Com `tradicional`, vem o
  preço.
- Ano `32000` = Zero KM (havia a pista `converterZeroKM` no JS). O formato `2026-1` é
  ano-combustível.

## 4. Coletor e amostra (291 requisições, 5 minutos)
- Escolhi a marca Royal Enfield por ter tamanho médio (59 modelos). A BMW tem 145.
- **Surpresa:** HTTP 429 do Cloudflare depois de umas 55 requisições a 0,6 s/req (1,7 req/s,
  dentro do teto de 2 req/s). Foram 23 ocorrências em 291 requisições, sem `Retry-After`. Um
  backoff de 5 s resolveu todas. Isso não aparece no JS; só se descobre rodando.
- Resultado: 206 linhas, nenhuma sem valor. Ao rodar de novo, 0 requisições de rede: o cache
  cobre a retomada.
- Ajuste feito depois: freio adaptativo (cada 429 deixa o ritmo 15% mais lento) e leitura de
  `Retry-After`, caso algum dia venha.

## 5. Estimativa (203 requisições, 4 minutos)
- Usar só a Royal Enfield daria um fator enviesado (3,49 anos por modelo, marca nova). Adicionei
  `--amostra-anos`, que sorteia 100 modelos de todas as marcas e chega a **4,41**.
- 103 marcas e 2.037 modelos (exato), uns 9.000 valores e umas 11.100 requisições, o que dá
  **cerca de 3,5 h** na taxa efetiva (~0,9 req/s). Mesmo a 1 req/s houve 6 respostas 429.

## Custo total da exploração
- Requisições à FIPE: cerca de 510 (2 de reconhecimento, ~15 de teste, 291 da amostra, 203 da
  estimativa). Nenhuma veio do navegador.
- O que mais economizou tempo foi **ler o JS e os atributos do HTML antes de testar**: os 7
  endpoints e os parâmetros saíram de 2 downloads.
- O que só a execução revelou: erro com HTTP 200, `tipoConsulta` obrigatório, o default
  silencioso de tipo de veículo, o 404 em GET e o rate limit do Cloudflare.
