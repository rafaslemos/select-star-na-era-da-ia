# Diário: coleta FIPE de motos (rodada 4a)

Data: 05/10/2026

1. Escrevi o `coletor_fipe.py` de uma vez, usando só o conhecimento fornecido e só a biblioteca padrão. Ele faz POST form-urlencoded, espera 1 s entre requisições e trata como erro o HTTP 200 com `erro` ou `nadaencontrado`, sem gravar no cache. No 429, espera de 5 a 10 s e repete. O cache fica em disco com gravação atômica. Tem `--marca`, `--estimar` e `--tabela`.
2. Amostra Royal Enfield (tabela 338, outubro/2026), numa única execução: 59 modelos, 206 linhas, 0 falhas, 8 respostas 429 recuperadas, 330 s. Conferi o CSV: BOM, as 18 colunas na ordem pedida, `valor_numerico` correto (`R$ 20.684,00` vira `20684.00`), anos de 2013 a 2027 e 40 linhas Zero KM (ano 32000).
3. Estimativa, numa única execução: 103 marcas, 2.037 modelos e média de 4,75 anos por modelo (n=60). Resultado: ~9.676 combinações, ~11.800 requisições e ~3,4 h a 60 req/min. Foram 164 requisições HTTP, 6 vindas do cache e 5 respostas 429, em 193 s.
4. Não rodei a coleta completa, como pedido.

Observação: o 429 apareceu em cerca de 3% das chamadas, como previsto, e nenhuma chamada falhou de vez.
