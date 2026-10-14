# Estimativa da coleta completa de motos (tabela 338 = outubro/2026)

Medido com `python coletor_fipe.py --estimar --amostra-modelos 150`:
lista real de marcas e modelos de todas as marcas + anos de 150 modelos sorteados (semente 42).

| Item | Valor | Como |
|---|---|---|
| Marcas | **103** | contado (exato) |
| Modelos | **2.037** | contado (exato) |
| Anos por modelo (média) | 4,49 | amostra de 150 modelos |
| Combinações modelo/ano | **~9.150** | 2.037 x 4,49 (estimado; Royal Enfield deu 3,49) |
| Requisições | **~11.300** | 2 + 103 + 2.037 + ~9.150 |
| Tempo a 60 req/min | **~3,1 h** | 11.300 / 60 / 60 |
| Tempo com 429 | **~3,3-3,4 h** | ~3% das chamadas tomam 429 + 5 s de espera e a nova tentativa também conta |

Marcas com mais modelos: HONDA 187, YAMAHA 148, BMW 145, HARLEY-DAVIDSON 121, TRIUMPH 121,
KAWASAKI 102, DUCATI 94, SUZUKI 87, BRP 64, Royal Enfield 59.

Faixa de incerteza: a média de anos por modelo vem de 150 modelos (de 2.037); a coleta real deve ficar
entre ~8.000 e ~10.500 combinações. Os 105 pedidos de marcas/modelos e ~210 de anos já estão no cache,
então a coleta completa reaproveita essa parte.

Para um histórico (todos os ~300 meses), multiplicar por ~300 (menos nos meses antigos, com menos modelos):
ordem de grandeza de **meses de coleta** a 60 req/min - inviável sem negociar com a FIPE ou restringir o período.

Custo desta validação: amostra Royal Enfield = 268 requisições úteis + 9 repetições por 429 (~5 min);
estimativa = 255 requisições de rede (~5 min).
