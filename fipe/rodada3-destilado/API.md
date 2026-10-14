# API da Tabela FIPE (consulta de veículos) — foco em motos

API não documentada oficialmente, usada pelo site `https://veiculos.fipe.org.br/`.
Base: `https://veiculos.fipe.org.br/api/veiculos/`
Validada em 05/10/2026 (tabela de referência 338 = outubro/2026).

## Regras gerais

| Item | Valor |
|---|---|
| Método | **sempre `POST`** (todos os endpoints) |
| Corpo | formulário `application/x-www-form-urlencoded` |
| Cabeçalhos | `Content-Type: application/x-www-form-urlencoded; charset=UTF-8`; recomendados `Referer: https://veiculos.fipe.org.br/` e um `User-Agent` de navegador. Não há autenticação, token nem cookie obrigatório (o servidor manda `Set-Cookie: ROUTEID`, mas não é necessário). |
| Resposta | JSON (`application/json; charset=utf-8`), atrás de Cloudflare |
| Erros | vêm com **HTTP 200** e corpo `{"codigo":"2","erro":"Parâmetros inválidos"}` (texto em latin-1, não UTF-8) |

## Códigos

- `codigoTipoVeiculo`: `1` = carros, `2` = motos, `3` = caminhões.
- `tipoVeiculo` (string, só no endpoint de valor): `carro`, `moto`, `caminhao`.
- `codigoTipoCombustivel`: `1` = Gasolina, `2` = Álcool, `3` = Diesel (há outros, como elétrico/flex, em carros). Motos Royal Enfield: só `1`.
- `anoModelo = 32000` significa **zero km** (aparece como label `32000` / valor `32000-1`).

## Sequência de chamadas para chegar ao valor de uma moto

```
ConsultarTabelaDeReferencia  -> codigoTabelaReferencia (ex.: 338)
  ConsultarMarcas            -> codigoMarca            (ex.: 192 = Royal Enfield)
    ConsultarModelos         -> codigoModelo           (ex.: 7942 = Bullet 500)
      ConsultarAnoModelo     -> "ano-combustivel"      (ex.: "2020-1")
        ConsultarValorComTodosParametros -> Valor, CodigoFipe, ...
```

### 1. ConsultarTabelaDeReferencia
- Corpo: vazio.
- Resposta: lista de meses, do mais recente ao mais antigo (310 meses em out/2026).
```json
[{"Codigo":338,"Mes":"outubro/2026 "},{"Codigo":337,"Mes":"setembro/2026 "}, ...]
```
- Atenção: `Mes` vem com espaço no final.

### 2. ConsultarMarcas
- Corpo: `codigoTabelaReferencia=338&codigoTipoVeiculo=2` (ambos obrigatórios; sem o tipo → erro "Parâmetros inválidos").
- Resposta (103 marcas de moto em out/2026):
```json
[{"Label":"ADLY","Value":"60"},{"Label":"AGRALE","Value":"61"}, ..., {"Label":"Royal Enfield","Value":"192"}]
```
- `Value` é **string**.

### 3. ConsultarModelos
- Corpo: `codigoTipoVeiculo=2&codigoTabelaReferencia=338&codigoMarca=192`
- Resposta: objeto com duas listas:
```json
{"Modelos":[{"Label":"Bullet 500","Value":7942},{"Label":"Classic 350 Chrome ","Value":11668}, ...],
 "Anos":[{"Label":"32000","Value":"32000-1"},{"Label":"2027","Value":"2027-1"}, ...]}
```
- `Modelos[].Value` é **inteiro** (diferente das marcas). Labels podem ter espaço no final.
- `Anos` é a lista de anos da **marca inteira**, não do modelo — não use para montar combinações.

### 4. ConsultarAnoModelo
- Corpo: `codigoTipoVeiculo=2&codigoTabelaReferencia=338&codigoMarca=192&codigoModelo=7942`
- Resposta:
```json
[{"Label":"2020","Value":"2020-1"},{"Label":"2019","Value":"2019-1"}, ...]
```
- `Value` = `anoModelo-codigoTipoCombustivel`; separe no `-` para o passo 5.

### 5. ConsultarValorComTodosParametros
- Corpo:
  `codigoTabelaReferencia=338&codigoMarca=192&codigoModelo=7942&codigoTipoVeiculo=2&anoModelo=2020&codigoTipoCombustivel=1&tipoVeiculo=moto&tipoConsulta=tradicional`
- Resposta:
```json
{"Valor":"R$ 20.684,00","Marca":"Royal Enfield","Modelo":"Bullet 500","AnoModelo":2020,
 "Combustivel":"Gasolina","CodigoFipe":"879008-6","MesReferencia":"outubro de 2026 ",
 "Autenticacao":"k4vgbhsjwlq","TipoVeiculo":2,"SiglaCombustivel":"G",
 "DataConsulta":"segunda-feira, 5 de outubro de 2026 22:13"}
```
- `Valor` é texto em formato brasileiro (`R$ 20.684,00`) — converter para número.
- `MesReferencia` vem por extenso e com espaço final; `DataConsulta` e `Autenticacao` mudam a cada consulta (não são dados da moto).

## Armadilhas

1. **Erro com HTTP 200.** Parâmetro faltando ou inválido não gera 4xx: vem `{"codigo":"2","erro":"Parâmetros inválidos"}`. Tem que checar a chave `erro` no corpo — e não gravar isso no cache.
2. **Encoding misto.** Respostas normais são UTF-8; a mensagem de erro vem em latin-1 (`Par\xe2metros`). Decodifique com fallback.
3. **Tipos inconsistentes.** `Value` de marca é string, de modelo é inteiro, de ano é `"2020-1"`.
4. **Ano 32000 = zero km.** Não é erro de dado.
5. **`Anos` em ConsultarModelos é da marca**, não do modelo. As combinações reais vêm de ConsultarAnoModelo, um modelo por vez.
6. **`anoModelo` e `codigoTipoCombustivel` separados** no passo 5, mas juntos (`2020-1`) no passo 4.
7. **`tipoVeiculo` (string)** foi aceito também quando omitido nos testes, mas o site manda — mantenha. `codigoTipoVeiculo` (número) é obrigatório nos endpoints de marcas/modelos/anos.
8. **Espaços no fim** de `Mes`, `MesReferencia` e de alguns `Label` de modelo — use `strip()`.
9. **Sem endpoint em lote:** é uma requisição por modelo (anos) e uma por combinação modelo/ano (valor). O custo da coleta é dominado pelo passo 5.
10. **Limite de taxa — 429 mesmo a 60 req/min.** A API está atrás de Cloudflare e não publica limite. Rodando sequencial a exatamente 1 req/s, recebemos **HTTP 429 em 10 de 278 requisições** na amostra (todas na primeira metade da coleta) e 2 de 162 na estimativa. Não veio `Retry-After` útil. Solução no coletor: esperar (5 s, 10 s, ... com backoff exponencial), desacelerar 20 % a cada 429 e voltar ao ritmo base aos poucos. Nunca gravar o 429 no cache.
11. **Mês de referência muda** (normalmente no início do mês). Os códigos de marca/modelo são estáveis entre meses, mas a lista de modelos/anos e os valores mudam — o cache é por `codigoTabelaReferencia`.

## Estimativa da coleta completa (motos, outubro/2026, tabela 338)

Medida com `python coletor_fipe.py --estimar 60` (lista os modelos de todas as marcas e consulta os anos de 60 modelos sorteados):

| Item | Valor |
|---|---|
| Marcas | **103** (medido) |
| Modelos | **2.037** (medido) |
| Anos por modelo | média 4,75 na amostra aleatória (desvio-padrão ~4,2; Royal Enfield: 3,49) |
| Combinações modelo/ano | **~9.700** (IC 95 % aproximado: 7.500 a 12.000) |
| Requisições | 1 (meses) + 1 (marcas) + 103 (modelos) + 2.037 (anos) + ~9.700 (valores) ≈ **11.800** |
| Tempo a 60 req/min | ≈ **3 h 17 min** de relógio; com ~4 % de 429 e backoff, contar **~3,5 h** (faixa 2,7 a 4 h) |

Mais de 80 % das requisições são do último passo (uma por moto/ano). Uma segunda rodada no mesmo mês sai quase de graça pelo cache; num mês novo, tudo é refeito (os códigos de marca/modelo se mantêm, mas valores e combinações mudam).
