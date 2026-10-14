#!/usr/bin/env bash
# Roda a Rodada 4 num processo separado do Claude Code, com contexto limpo e enxuto:
# só Bash, Read e Write, nenhum servidor MCP, prompt de sistema curto.
#
#   bash rodar_enxuto.sh claude-opus-5-5   rodada4a-enxuto-opus
#   bash rodar_enxuto.sh claude-sonnet-5-5 rodada4b-enxuto-sonnet
set -euo pipefail

MODELO="$1"
PASTA="$2"
AQUI="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$AQUI/.." && pwd)"

AGENTE='{"coletor-enxuto":{"description":"Executa coletas de API a partir de instrucoes prontas","tools":["Bash","Read","Write"],"prompt":"Voce executa coletas de dados em APIs HTTP seguindo o conhecimento que vem no pedido. Trabalhe com economia de voltas: escreva cada arquivo completo de uma vez; rode comandos demorados numa unica chamada que espera o fim (timeout de ate 600000 ms), sem processos em segundo plano para acompanhar; imprima resumos e contagens, nao respostas inteiras; nao explore alem do necessario. Ao terminar, responda com um resumo curto."}}'

cd "$RAIZ"
sed "s/{{PASTA}}/$PASTA/" "$AQUI/prompt-rodada4.md" | claude -p \
  --agents "$AGENTE" --agent coletor-enxuto \
  --tools "Bash,Read,Write" --allowedTools "Bash,Read,Write" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --disable-slash-commands --no-chrome \
  --model "$MODELO" --output-format json \
  > "$AQUI/headless-$PASTA.json"

echo "ok: $AQUI/headless-$PASTA.json"
