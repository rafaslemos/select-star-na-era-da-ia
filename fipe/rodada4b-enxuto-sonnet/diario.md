# Diario
- Escrevi o coletor (urllib, 1 req/s, cache sha1 em disco, erros fora do cache, retry em 429/5xx, CSV incremental com retomada).
- Amostra Royal Enfield (marca 192, tabela 338 outubro/2026): 59 modelos, 206 linhas, 0 erros, 277 req, ~5,5 min.
- `--estimar`: 103 marcas, 2.037 modelos, 60 modelos sorteados (seed 42) -> 4,75 anos/modelo -> ~9.676 combinacoes, ~11.818 req, ~3,3 h.
- Corrigi a unidade do tempo impresso (minutos = req/60 e horas = req/3600).
