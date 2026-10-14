# API da Tabela FIPE (veiculos.fipe.org.br) - consulta de motos

API não oficial/sem documentação pública: é a que o site `https://veiculos.fipe.org.br/` usa via AJAX.
Tudo aqui foi verificado em 05/10/2026 (mês de referência mais recente: `338` = outubro/2026).

## Visão geral

- Base: `https://veiculos.fipe.org.br/api/veiculos/`
- **Todos os endpoints são `POST`**. `GET` devolve HTTP 404 (página HTML "The resource you are looking for has been removed...").
- Corpo: `application/x-www-form-urlencoded; charset=UTF-8` (não é JSON).
- Resposta: JSON (`application/json; charset=utf-8`).
- **Cookies não são necessários.** Os cookies dos exemplos do navegador (`cf_clearance`, `_ga`, `ROUTEID`...) são só do Cloudflare/Google Analytics da sessão do navegador; as chamadas funcionaram sem nenhum cookie.

### Cabeçalhos usados

| Cabeçalho | Valor | Necessário? |
|---|---|---|
| `content-type` | `application/x-www-form-urlencoded; charset=UTF-8` | sim (corpo de formulário) |
| `user-agent` | UA de navegador (Chrome) | recomendado (não testado sem) |
| `referer` / `origin` | `https://veiculos.fipe.org.br/` / `https://veiculos.fipe.org.br` | recomendado |
| `x-requested-with` | `XMLHttpRequest` | recomendado |
| `accept` | `application/json, text/javascript, */*; q=0.01` | recomendado |

Os cabeçalhos `sec-ch-*`, `sec-fetch-*`, `priority` e os cookies foram descartados sem efeito. (Não gastamos requisições
testando um por um quais dos "recomendados" são de fato obrigatórios: com eles funciona.)

### Códigos de tipo de veículo

| `codigoTipoVeiculo` | `tipoVeiculo` (texto, usado só no valor) |
|---|---|
| 1 | carros (`carro`) |
| 2 | motos (`moto`) |
| 3 | caminhões (`caminhao`) |

Só o tipo 2/`moto` foi exercitado; os textos de 1 e 3 são o padrão do site e não foram testados aqui.

## Sequência de chamadas para chegar ao valor de uma moto

```
ConsultarTabelaDeReferencia          -> codigoTabelaReferencia (mês)
  ConsultarMarcas                    -> codigoMarca
    ConsultarModelos                 -> codigoModelo
      ConsultarAnoModelo             -> "anoModelo-codigoTipoCombustivel" (ex. "2020-1")
        ConsultarValorComTodosParametros -> valor FIPE
```

Para coletar tudo de um mês: 1 + 1 + (nº marcas) + (nº modelos) + (nº combinações modelo/ano) requisições.
`ConsultarModelosAtravesDoAno` não é necessário para a coleta (é o filtro inverso "escolhi o ano, quais modelos?").

## Endpoints

### 1. `ConsultarTabelaDeReferencia`
Lista os meses de referência. Corpo vazio (`content-length: 0`).

```json
[{"Codigo":338,"Mes":"outubro/2026 "},{"Codigo":337,"Mes":"setembro/2026 "}, ...]
```
- Vai até `janeiro/2001` (~300 meses).
- O mais recente vem primeiro, mas **os códigos não são cronológicos** nos anos antigos (ex.: dezembro/2005 = 111,
  setembro/2005 = 1). Para o "mais recente", use o primeiro item ou o maior código (hoje coincidem). Há lacunas na numeração.
- `Mes` tem espaço no final.

### 2. `ConsultarMarcas`
Parâmetros: `codigoTabelaReferencia=338&codigoTipoVeiculo=2`

```json
[{"Label":"ADLY","Value":"60"},{"Label":"Royal Enfield","Value":"192"}, ...]
```
- 103 marcas de moto em 338. `Value` é **string** aqui. Nomes com caixa mista (`Royal Enfield`, `byCristo`) e acentos.

### 3. `ConsultarModelos`
Parâmetros (o site manda todos, vazios quando não se aplicam):
`codigoTipoVeiculo=2&codigoTabelaReferencia=338&codigoModelo=&codigoMarca=192&ano=&codigoTipoCombustivel=&anoModelo=&modeloCodigoExterno=`

```json
{"Modelos":[{"Label":"Bullet 500","Value":7942}, ...],
 "Anos":[{"Label":"32000 Gasolina","Value":"32000-1"},{"Label":"2027","Value":"2027-1"}, ...]}
```
- `Value` do modelo é **inteiro** aqui (mas string em `ConsultarModelosAtravesDoAno`).
- `Anos` é a união dos anos de **todos** os modelos da marca - não serve para saber os anos de cada modelo.

### 4. `ConsultarAnoModelo`
Parâmetros: os mesmos de `ConsultarModelos` com `codigoModelo` preenchido.

```json
[{"Label":"2020","Value":"2020-1"},{"Label":"2019","Value":"2019-1"}]
```
- `Value` = `"<anoModelo>-<codigoTipoCombustivel>"`. Precisa ser quebrado no `-` para a chamada de valor.
- **`32000` = 0 km** (modelo novo; o label vem só "32000"). Não é um ano de verdade.
- Códigos de combustível vistos em motos (verificados pelo campo `Combustivel` da resposta de valor):

  | código | Combustivel | Sigla | exemplo |
  |---|---|---|---|
  | 1 | Gasolina | G | quase tudo (828 de 847 anos na amostra de estimativa) |
  | 4 | Elétrico | E | KASINSKI PRIMA ELECTRA 2000W |
  | 5 | Flex | F | HONDA CG 160 FAN Flex |
  | 6 | Híbrido | H | YAMAHA FLUO 125 CONNECTED |

  (2 = álcool e 3 = diesel existem no site para carros/caminhões; não apareceram em motos.)
- Não presuma `-1`: use sempre o sufixo que veio no `Value`.

### 5. `ConsultarModelosAtravesDoAno` (opcional)
Parâmetros: os de `ConsultarAnoModelo` + `ano=2008-1&codigoTipoCombustivel=1&anoModelo=2008`.
Devolve `[{"Label":"AME-110 MIX","Value":"4360"}, ...]` (modelos da marca que existem naquele ano). Não usado no coletor.

### 6. `ConsultarValorComTodosParametros`
Parâmetros:
`codigoTabelaReferencia=338&codigoMarca=192&codigoModelo=7942&codigoTipoVeiculo=2&anoModelo=2020&codigoTipoCombustivel=1&tipoVeiculo=moto&modeloCodigoExterno=&tipoConsulta=tradicional`

```json
{"Valor":"R$ 20.684,00","Marca":"Royal Enfield","Modelo":"Bullet 500","AnoModelo":2020,
 "Combustivel":"Gasolina","CodigoFipe":"879008-6","MesReferencia":"outubro de 2026 ",
 "Autenticacao":"k4vgbhsjwlq","TipoVeiculo":2,"SiglaCombustivel":"G",
 "DataConsulta":"segunda-feira, 5 de outubro de 2026 21:54"}
```
- `Valor` é texto em formato brasileiro (`R$ 20.684,00`) - converter para número.
- `Autenticacao` e `DataConsulta` mudam a cada consulta (não são dados da moto).
- **Obrigatórios** (testado): `tipoConsulta=tradicional` e `codigoTipoCombustivel`. Sem eles: `Parâmetros inválidos`.
- **Dispensáveis** (testado): `tipoVeiculo` e `modeloCodigoExterno` - sem eles a resposta é a mesma.

## Erros e armadilhas

| Situação | Resposta |
|---|---|
| Parâmetro obrigatório faltando | **HTTP 200** com `{"codigo":"2","erro":"Parâmetros inválidos"}` |
| Combinação inexistente (ex. ano que o modelo não tem) | **HTTP 200** com `{"codigo":"0","erro":"nadaencontrado"}` |
| Método GET | HTTP 404 (HTML) |
| Excesso de requisições | **HTTP 429**, sem cabeçalho `Retry-After` |

- **Erros vêm com HTTP 200**: é preciso olhar o corpo (`"erro"` presente) antes de aceitar/cachear a resposta.
  Esses dois erros não adianta repetir.
- **Limite de taxa**: mesmo a 1 requisição/segundo cravada (60/min, sem paralelismo), ~3% das chamadas tomaram 429
  (9 de 277 na amostra; 9 de 264 na estimativa). Esperar 5 s e repetir resolveu sempre na 1ª nova tentativa.
  O limite exato não é publicado; parece ser em rajadas/janela curta, não "60 por minuto" redondo.
- Tipos inconsistentes: `Value` de marca é string, de modelo é inteiro (em `ConsultarModelos`) e string em outros endpoints.
- Espaços sobrando no fim de textos (`"outubro/2026 "`, `"Classic 350 Chrome "`, `"outubro de 2026 "`).
- O mesmo `CodigoFipe` aparece em vários anos do mesmo modelo (é o código do modelo, não da combinação modelo/ano).
