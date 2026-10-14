# API da Tabela FIPE (veiculos.fipe.org.br): consulta de motos

Levantamento feito em 05/10/2026 a partir de https://veiculos.fipe.org.br/. A API não tem
documentação pública; tudo aqui veio do JavaScript do site e de chamadas de teste.

## Onde está no site

- A página carrega `content/js/modulos/veiculos_function.js?v=20160805`.
- Nesse arquivo: `var surl = 'https://veiculos.fipe.org.br/api/veiculos/'`.
- O nome de cada endpoint fica em atributos HTML dos formulários (`urlConsulta`, `urlPesquisa`),
  junto com o tipo do veículo (`codTipoVeiculo`, `tipoveiculo`).
- Todas as chamadas passam por `crossDomainAjax()`, que faz um `$.ajax` com `type: 'POST'`,
  `dataType: 'json'` e `data: {...}`. Ou seja, os parâmetros vão no corpo como
  **`application/x-www-form-urlencoded`**, não como JSON.

## Regras gerais

| Item | Valor |
|---|---|
| Base | `https://veiculos.fipe.org.br/api/veiculos/` |
| Método | **POST** sempre. GET devolve 404 com HTML |
| Corpo | form-urlencoded (`chave=valor&...`) |
| Cabeçalhos | nenhum obrigatório: funcionou sem User-Agent, Referer, cookie ou token. Por cortesia, mande `User-Agent` e `Referer: https://veiculos.fipe.org.br/` |
| Autenticação | nenhuma. Os `__RequestVerificationToken` do HTML e o script do reCAPTCHA (`render=explicit`, sem callback `onScriptLoad` definido) não são usados pela API |
| Resposta | `application/json; charset=utf-8` (UTF-8 correto: `março`) |
| Infra | atrás do Cloudflare |

### Códigos de tipo de veículo (`codigoTipoVeiculo`)

| Código | Tipo (`tipoveiculo` no HTML) |
|---|---|
| 1 | carro |
| 2 | **moto** |
| 3 | caminhão |

### Erros (HTTP 200 com corpo de erro)

A API responde **HTTP 200 mesmo quando dá erro**. O erro vem no corpo:

| Corpo | Significado |
|---|---|
| `{"codigo":"0","erro":"nadaencontrado"}` | combinação inexistente (por exemplo, ano que o modelo não tem, ou marca de moto consultada como carro) |
| `{"codigo":"2","erro":"Parâmetros inválidos"}` | faltou parâmetro obrigatório |
| `{"codigo":"3", ...}` | código FIPE em formato inválido (o padrão é `000000-0`) |
| `{"codigo":"99", ...}` | "Você realizou a quantidade máxima de pesquisas. Para continuar, recarregue a página." Esse limite está previsto no JS do site; não chegou a disparar nos testes |

## Endpoints

### 1. `ConsultarTabelaDeReferencia`: meses de referência
Sem parâmetros.
```json
[{"Codigo":338,"Mes":"outubro/2026 "},{"Codigo":337,"Mes":"setembro/2026 "}, ...,
 {"Codigo":62,"Mes":"janeiro/2001 "}]
```
São 310 tabelas, do mês mais recente para o mais antigo. `Mes` vem com espaço no final.

### 2. `ConsultarMarcas`
| Parâmetro | Ex. |
|---|---|
| `codigoTabelaReferencia` | 338 |
| `codigoTipoVeiculo` | 2 |

Os dois são obrigatórios; sem eles a resposta é o código 2.
```json
[{"Label":"ADLY","Value":"60"},{"Label":"AGRALE","Value":"61"}, ... ]
```
Em 10/2026 são 103 marcas de moto. `Value` é string.

### 3. `ConsultarModelos`
| Parâmetro | Ex. |
|---|---|
| `codigoTabelaReferencia` | 338 |
| `codigoTipoVeiculo` | 2 |
| `codigoMarca` | 67 (BMW) |
```json
{"Modelos":[{"Label":"C 400 X","Value":10895}, ...],
 "Anos":[{"Label":"32000","Value":"32000-1"},{"Label":"2027","Value":"2027-1"}, ...]}
```
`Modelos[].Value` é número. `Anos` é a união dos anos de todos os modelos da marca e não diz
qual modelo tem qual ano.

### 4. `ConsultarAnoModelo`: anos de um modelo
| Parâmetro | Ex. |
|---|---|
| `codigoTabelaReferencia` | 338 |
| `codigoTipoVeiculo` | 2 |
| `codigoMarca` | 67 |
| `codigoModelo` | 10895 |
```json
[{"Label":"32000","Value":"32000-1"},{"Label":"2026","Value":"2026-1"},{"Label":"2025","Value":"2025-1"}]
```
`Value` = `<anoModelo>-<codigoTipoCombustivel>`. **32000 significa "Zero KM".**

### 5. `ConsultarValorComTodosParametros`: preço
| Parâmetro | Ex. | Obs. |
|---|---|---|
| `codigoTabelaReferencia` | 338 | |
| `codigoTipoVeiculo` | 2 | |
| `codigoMarca` | 67 | |
| `codigoModelo` | 10895 | |
| `anoModelo` | 2026 | parte antes do `-` |
| `codigoTipoCombustivel` | 1 | parte depois do `-` |
| `tipoConsulta` | `tradicional` | **obrigatório**; sem ele dá código 2 |
| `modeloCodigoExterno` | (vazio) | só na consulta por código FIPE (`tipoConsulta=codigo`) |
```json
{"Valor":"R$ 58.860,00","Marca":"BMW","Modelo":"C 400 X","AnoModelo":2026,
 "Combustivel":"Gasolina","CodigoFipe":"803101-0","MesReferencia":"outubro de 2026 ",
 "Autenticacao":"1lf8nf39lrd1l","TipoVeiculo":2,"SiglaCombustivel":"G",
 "DataConsulta":"segunda-feira, 5 de outubro de 2026 18:03"}
```
`Valor` é texto em formato brasileiro. `Autenticacao` muda a cada chamada, e `DataConsulta` é a
hora da consulta, não um dado do veículo.

### Endpoints auxiliares (não são necessários para a coleta)
- `ConsultarModelosAtravesDoAno` (tabela, tipo, marca, `ano`=`2026-1`, `anoModelo`, `codigoTipoCombustivel`):
  modelos de uma marca que têm aquele ano. Aqui `Value` vem como **string**, ao contrário do
  `ConsultarModelos`.
- `ConsultarAnoModeloPeloCodigoFipe` (tabela, tipo, `modeloCodigoExterno`=`803101-0`): anos a
  partir do código FIPE.
- `ConsultarValor`: aparece no JS, mas só em código antigo; o site não usa.

## Sequência para chegar ao valor de uma moto

```
ConsultarTabelaDeReferencia            -> pega Codigo do mês (ex.: 338)
ConsultarMarcas(338, 2)                -> escolhe Value da marca (ex.: "67")
ConsultarModelos(338, 2, 67)           -> escolhe Modelos[].Value (ex.: 10895)
ConsultarAnoModelo(338, 2, 67, 10895)  -> escolhe Value (ex.: "2026-1")
ConsultarValorComTodosParametros(338, 2, 67, 10895, anoModelo=2026,
                                 codigoTipoCombustivel=1, tipoConsulta=tradicional)
```
Exemplo com curl:
```bash
curl -X POST https://veiculos.fipe.org.br/api/veiculos/ConsultarValorComTodosParametros \
  -H "Referer: https://veiculos.fipe.org.br/" \
  -d "codigoTabelaReferencia=338&codigoTipoVeiculo=2&codigoMarca=67&codigoModelo=10895&anoModelo=2026&codigoTipoCombustivel=1&tipoConsulta=tradicional"
```
Para a coleta completa: 1 + 1 + M (marcas) + N (modelos) + C (combinações modelo/ano) requisições.

## Armadilhas encontradas

1. **Erro com HTTP 200.** É preciso olhar o campo `erro` no corpo. Não dá para confiar no
   status HTTP.
2. **Sem `codigoTipoVeiculo` a resposta não é "parâmetro inválido".** Em `ConsultarModelos`, sem
   o tipo vem `nadaencontrado`: a API parece assumir carro, e a marca 67 não existe como carro.
   Esse erro passa despercebido com facilidade.
3. **`tipoConsulta=tradicional` é obrigatório** no endpoint de valor, embora não pareça
   necessário.
4. **Ano 32000 = Zero KM**; o site converte com `converterZeroKM`.
5. **O ano vem como `ano-combustível`** (`2026-1`) e precisa ser separado em `anoModelo` e
   `codigoTipoCombustivel`.
6. **Os tipos variam:** `Value` de marca é string, de modelo é número em `ConsultarModelos` e
   string em `ConsultarModelosAtravesDoAno`.
7. **GET devolve 404** (HTML genérico do IIS), o que dá a impressão de que o endpoint não existe.
8. **`Mes`/`MesReferencia` vêm com espaço no final.**
9. **O site faz `async:false` e `cache:false`.** O jQuery acrescenta `_=timestamp` em GET, mas
   como é POST isso não se aplica.
10. **Limite de pesquisas (código 99)** por sessão, segundo o JS. O coletor trata isso esperando
    60 s ou mais e tentando de novo.
11. O console do Windows mostra `mar�o`, mas o problema é de exibição; o JSON está em UTF-8
    correto.
12. **Rate limit do Cloudflare (HTTP 429), sem `Retry-After`.** Isso não está no JS; só apareceu
    na prática. A 0,6 s/req (cerca de 1,7 req/s), o primeiro 429 veio depois de umas 55
    requisições, e foram 23 em 291 (8%). A 1 req/s ainda houve 6 em 203. Esperar 5 s sempre
    resolveu. Na prática, a taxa sustentável fica em **~0,9 req/s**, abaixo do teto de 2 req/s
    que combinamos. O coletor espera e tenta de novo, e a cada 429 aumenta o intervalo em 15%.

## Amostra validada (Royal Enfield, tabela 338 = outubro/2026)

- Arquivo: `amostra_royal_enfield.csv`, com 206 linhas (modelo/ano), 59 modelos, 40 delas Zero KM,
  nenhuma sem valor.
- Valores entre R$ 15.781 e R$ 37.686. Todas a gasolina, anos de 2013 a Zero KM.
- Requisições: 268 úteis (1 tabela + 1 marcas + 1 modelos + 59 anos + 206 valores) e 23
  repetidas por causa de 429. Tempo total: 298 s.
- Ao rodar de novo, tudo veio do cache: 0 requisições de rede, 268 do cache, 0 s.

## Estimativa da coleta completa de motos (tabela 338)

Fonte: `python coletor_fipe.py --estimar --amostra-anos 100 --intervalo 1`. Foram 103 chamadas a
`ConsultarModelos` (contagem exata) e 100 chamadas a `ConsultarAnoModelo` em modelos sorteados
(semente 42) de todas as marcas.

| Item | Quantidade |
|---|---|
| Marcas | **103** (exato) |
| Modelos | **2.037** (exato) |
| Anos por modelo (amostra aleatória de 100) | 4,41 (na Royal Enfield foram 3,49) |
| Combinações modelo/ano (valores) | **~9.000** (2.037 × 4,41 ≈ 8.983) |
| Requisições | 1 + 1 + 103 + 2.037 + ~8.983 ≈ **11.100** |
| Tempo a 2 req/s (teto teórico) | ~1,5 h, mas haverá 429 |
| Tempo a ~0,9 req/s (taxa efetiva observada) | **~3,5 h** |
| Cache em disco | cerca de 11 mil arquivos JSON pequenos: uns 7 MB de conteúdo, mais espaço em disco por causa do tamanho de cluster |

As respostas da estimativa já estão em `cache/` e serão reaproveitadas pela coleta completa.

