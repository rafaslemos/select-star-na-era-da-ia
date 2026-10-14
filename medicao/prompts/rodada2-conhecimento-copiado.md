<!-- Prompt enviado ao subagente da Rodada 2, extraído do transcript. Tamanho original: 31,950 caracteres. Os valores de 6 cabeçalhos de cookie foram omitidos. -->

Você vai coletar os dados da consulta de MOTOS da Tabela FIPE (marcas, modelos, anos e o valor FIPE de cada combinação) e deixar pronto um jeito automatizado de coletar todos esses dados, usando o conhecimento passado abaixo por quem já conhece a API.

Regras:
- Trabalhe a partir do conhecimento abaixo. Não leia nenhum outro arquivo do repositório nem pastas temporárias, e não consulte memórias ou buscas de sessões anteriores (por exemplo, ferramentas ctx_search). Em especial, não abra nada em fipe\rodada1-exploracao.
- Limite de taxa: no máximo 60 requisições por minuto ao servidor da FIPE, sem paralelismo, reaproveitando respostas já obtidas.
- Não grave os cookies dos exemplos em nenhum arquivo.
- NÃO rode a coleta completa de todas as motos. Valide o coletor numa amostra: a marca Royal Enfield inteira (todos os modelos, todos os anos, com valores) no mês de referência mais recente.

Entregáveis, todos em fipe\rodada2-conhecimento\ :
1. API.md: documentação da API. Endpoints, método HTTP, parâmetros, cabeçalhos necessários, formato e exemplo das respostas, a sequência de chamadas para chegar ao valor de uma moto, códigos de tipo de veículo, e armadilhas encontradas (erros, limites, parâmetros obrigatórios, etc.).
2. coletor_fipe.py: script Python (só biblioteca padrão) que coleta todas as marcas, modelos, anos e valores de motos para um mês de referência, com controle de taxa, cache em disco das respostas e retomada se for interrompido. Saída em CSV com uma linha por moto/ano e todas as colunas que a API devolve. Deve aceitar um filtro de marca, para rodar a amostra.
3. amostra_royal_enfield.csv: o resultado da validação na Royal Enfield.
4. Uma estimativa do tamanho da coleta completa (quantas marcas, modelos e combinações modelo/ano, quantas requisições e quanto tempo levaria na taxa permitida).
5. diario.md: um diário curto do seu processo (o que tentou, o que deu errado, como resolveu cada coisa), útil para uma palestra sobre o custo da IA trabalhar com uma API.

Ao terminar, responda com um resumo curto: endpoints usados, sequência de chamadas, números da amostra e a estimativa da coleta completa.

===== CONHECIMENTO PASSADO PELO ESPECIALISTA (texto original) =====

Pra pesquisar os períodos podemos trabalhar com a seguinte requisição:

curl --url 'https://veiculos.fipe.org.br/api/veiculos/ConsultarTabelaDeReferencia' \
  -X 'POST' \
  -H 'accept: application/json, text/javascript, */*; q=0.01' \
  -H 'accept-language: pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7' \
  -H 'content-length: 0' \
  -b '<cookies do navegador omitidos na versão pública>' \
  -H 'origin: https://veiculos.fipe.org.br' \
  -H 'priority: u=0, i' \
  -H 'referer: https://veiculos.fipe.org.br/' \
  -H 'sec-ch-ua: "Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36' \
  -H 'x-requested-with: XMLHttpRequest'

[{"Codigo":338,"Mes":"outubro/2026 "},{"Codigo":337,"Mes":"setembro/2026 "},{"Codigo":336,"Mes":"agosto/2026 "},{"Codigo":335,"Mes":"julho/2026 "},{"Codigo":334,"Mes":"junho/2026 "},{"Codigo":333,"Mes":"maio/2026 "},{"Codigo":332,"Mes":"abril/2026 "},{"Codigo":331,"Mes":"março/2026 "},{"Codigo":330,"Mes":"fevereiro/2026 "},{"Codigo":329,"Mes":"janeiro/2026 "},{"Codigo":328,"Mes":"dezembro/2025 "},{"Codigo":327,"Mes":"novembro/2025 "},{"Codigo":326,"Mes":"outubro/2025 "},{"Codigo":325,"Mes":"setembro/2025 "},{"Codigo":324,"Mes":"agosto/2025 "},{"Codigo":323,"Mes":"julho/2025 "},{"Codigo":322,"Mes":"junho/2025 "},{"Codigo":321,"Mes":"maio/2025 "},{"Codigo":320,"Mes":"abril/2025 "},{"Codigo":319,"Mes":"março/2025 "},{"Codigo":318,"Mes":"fevereiro/2025 "},{"Codigo":317,"Mes":"janeiro/2025 "},{"Codigo":316,"Mes":"dezembro/2024 "},{"Codigo":315,"Mes":"novembro/2024 "},{"Codigo":314,"Mes":"outubro/2024 "},{"Codigo":313,"Mes":"setembro/2024 "},{"Codigo":312,"Mes":"agosto/2024 "},{"Codigo":311,"Mes":"julho/2024 "},{"Codigo":310,"Mes":"junho/2024 "},{"Codigo":309,"Mes":"maio/2024 "},{"Codigo":308,"Mes":"abril/2024 "},{"Codigo":307,"Mes":"março/2024 "},{"Codigo":306,"Mes":"fevereiro/2024 "},{"Codigo":305,"Mes":"janeiro/2024 "},{"Codigo":304,"Mes":"dezembro/2023 "},{"Codigo":303,"Mes":"novembro/2023 "},{"Codigo":302,"Mes":"outubro/2023 "},{"Codigo":301,"Mes":"setembro/2023 "},{"Codigo":300,"Mes":"agosto/2023 "},{"Codigo":299,"Mes":"julho/2023 "},{"Codigo":298,"Mes":"junho/2023 "},{"Codigo":297,"Mes":"maio/2023 "},{"Codigo":296,"Mes":"abril/2023 "},{"Codigo":295,"Mes":"março/2023 "},{"Codigo":294,"Mes":"fevereiro/2023 "},{"Codigo":293,"Mes":"janeiro/2023 "},{"Codigo":292,"Mes":"dezembro/2022 "},{"Codigo":291,"Mes":"novembro/2022 "},{"Codigo":290,"Mes":"outubro/2022 "},{"Codigo":289,"Mes":"setembro/2022 "},{"Codigo":288,"Mes":"agosto/2022 "},{"Codigo":287,"Mes":"julho/2022 "},{"Codigo":286,"Mes":"junho/2022 "},{"Codigo":285,"Mes":"maio/2022 "},{"Codigo":284,"Mes":"abril/2022 "},{"Codigo":283,"Mes":"março/2022 "},{"Codigo":282,"Mes":"fevereiro/2022 "},{"Codigo":281,"Mes":"janeiro/2022 "},{"Codigo":280,"Mes":"dezembro/2021 "},{"Codigo":279,"Mes":"novembro/2021 "},{"Codigo":278,"Mes":"outubro/2021 "},{"Codigo":274,"Mes":"setembro/2021 "},{"Codigo":273,"Mes":"agosto/2021 "},{"Codigo":272,"Mes":"julho/2021 "},{"Codigo":271,"Mes":"junho/2021 "},{"Codigo":270,"Mes":"maio/2021 "},{"Codigo":267,"Mes":"abril/2021 "},{"Codigo":266,"Mes":"março/2021 "},{"Codigo":265,"Mes":"fevereiro/2021 "},{"Codigo":264,"Mes":"janeiro/2021 "},{"Codigo":263,"Mes":"dezembro/2020 "},{"Codigo":262,"Mes":"novembro/2020 "},{"Codigo":261,"Mes":"outubro/2020 "},{"Codigo":260,"Mes":"setembro/2020 "},{"Codigo":259,"Mes":"agosto/2020 "},{"Codigo":258,"Mes":"julho/2020 "},{"Codigo":256,"Mes":"junho/2020 "},{"Codigo":255,"Mes":"maio/2020 "},{"Codigo":253,"Mes":"abril/2020 "},{"Codigo":252,"Mes":"março/2020 "},{"Codigo":251,"Mes":"fevereiro/2020 "},{"Codigo":250,"Mes":"janeiro/2020 "},{"Codigo":249,"Mes":"dezembro/2019 "},{"Codigo":248,"Mes":"novembro/2019 "},{"Codigo":247,"Mes":"outubro/2019 "},{"Codigo":246,"Mes":"setembro/2019 "},{"Codigo":245,"Mes":"agosto/2019 "},{"Codigo":244,"Mes":"julho/2019 "},{"Codigo":243,"Mes":"junho/2019 "},{"Codigo":242,"Mes":"maio/2019 "},{"Codigo":241,"Mes":"abril/2019 "},{"Codigo":239,"Mes":"março/2019 "},{"Codigo":238,"Mes":"fevereiro/2019 "},{"Codigo":237,"Mes":"janeiro/2019 "},{"Codigo":236,"Mes":"dezembro/2018 "},{"Codigo":235,"Mes":"novembro/2018 "},{"Codigo":234,"Mes":"outubro/2018 "},{"Codigo":233,"Mes":"setembro/2018 "},{"Codigo":232,"Mes":"agosto/2018 "},{"Codigo":231,"Mes":"julho/2018 "},{"Codigo":230,"Mes":"junho/2018 "},{"Codigo":229,"Mes":"maio/2018 "},{"Codigo":228,"Mes":"abril/2018 "},{"Codigo":227,"Mes":"março/2018 "},{"Codigo":226,"Mes":"fevereiro/2018 "},{"Codigo":225,"Mes":"janeiro/2018 "},{"Codigo":224,"Mes":"dezembro/2017 "},{"Codigo":219,"Mes":"novembro/2017 "},{"Codigo":218,"Mes":"outubro/2017 "},{"Codigo":217,"Mes":"setembro/2017 "},{"Codigo":216,"Mes":"agosto/2017 "},{"Codigo":215,"Mes":"julho/2017 "},{"Codigo":214,"Mes":"junho/2017 "},{"Codigo":212,"Mes":"maio/2017 "},{"Codigo":211,"Mes":"abril/2017 "},{"Codigo":207,"Mes":"março/2017 "},{"Codigo":205,"Mes":"fevereiro/2017 "},{"Codigo":202,"Mes":"janeiro/2017 "},{"Codigo":200,"Mes":"dezembro/2016 "},{"Codigo":198,"Mes":"novembro/2016 "},{"Codigo":197,"Mes":"outubro/2016 "},{"Codigo":196,"Mes":"setembro/2016 "},{"Codigo":194,"Mes":"agosto/2016 "},{"Codigo":193,"Mes":"julho/2016 "},{"Codigo":192,"Mes":"junho/2016 "},{"Codigo":191,"Mes":"maio/2016 "},{"Codigo":190,"Mes":"abril/2016 "},{"Codigo":189,"Mes":"março/2016 "},{"Codigo":188,"Mes":"fevereiro/2016 "},{"Codigo":187,"Mes":"janeiro/2016 "},{"Codigo":186,"Mes":"dezembro/2015 "},{"Codigo":185,"Mes":"novembro/2015 "},{"Codigo":184,"Mes":"outubro/2015 "},{"Codigo":183,"Mes":"setembro/2015 "},{"Codigo":182,"Mes":"agosto/2015 "},{"Codigo":181,"Mes":"julho/2015 "},{"Codigo":180,"Mes":"junho/2015 "},{"Codigo":179,"Mes":"maio/2015 "},{"Codigo":178,"Mes":"abril/2015 "},{"Codigo":176,"Mes":"março/2015 "},{"Codigo":175,"Mes":"fevereiro/2015 "},{"Codigo":174,"Mes":"janeiro/2015 "},{"Codigo":173,"Mes":"dezembro/2014 "},{"Codigo":172,"Mes":"novembro/2014 "},{"Codigo":171,"Mes":"outubro/2014 "},{"Codigo":170,"Mes":"setembro/2014 "},{"Codigo":169,"Mes":"agosto/2014 "},{"Codigo":168,"Mes":"julho/2014 "},{"Codigo":167,"Mes":"junho/2014 "},{"Codigo":166,"Mes":"maio/2014 "},{"Codigo":165,"Mes":"abril/2014 "},{"Codigo":164,"Mes":"março/2014 "},{"Codigo":163,"Mes":"fevereiro/2014 "},{"Codigo":162,"Mes":"janeiro/2014 "},{"Codigo":161,"Mes":"dezembro/2013 "},{"Codigo":160,"Mes":"novembro/2013 "},{"Codigo":159,"Mes":"outubro/2013 "},{"Codigo":158,"Mes":"setembro/2013 "},{"Codigo":157,"Mes":"agosto/2013 "},{"Codigo":156,"Mes":"julho/2013 "},{"Codigo":155,"Mes":"junho/2013 "},{"Codigo":154,"Mes":"maio/2013 "},{"Codigo":153,"Mes":"abril/2013 "},{"Codigo":152,"Mes":"março/2013 "},{"Codigo":151,"Mes":"fevereiro/2013 "},{"Codigo":150,"Mes":"janeiro/2013 "},{"Codigo":149,"Mes":"dezembro/2012 "},{"Codigo":148,"Mes":"novembro/2012 "},{"Codigo":147,"Mes":"outubro/2012 "},{"Codigo":146,"Mes":"setembro/2012 "},{"Codigo":145,"Mes":"agosto/2012 "},{"Codigo":144,"Mes":"julho/2012 "},{"Codigo":143,"Mes":"junho/2012 "},{"Codigo":142,"Mes":"maio/2012 "},{"Codigo":141,"Mes":"abril/2012 "},{"Codigo":140,"Mes":"março/2012 "},{"Codigo":139,"Mes":"fevereiro/2012 "},{"Codigo":138,"Mes":"janeiro/2012 "},{"Codigo":137,"Mes":"dezembro/2011 "},{"Codigo":136,"Mes":"novembro/2011 "},{"Codigo":135,"Mes":"outubro/2011 "},{"Codigo":134,"Mes":"setembro/2011 "},{"Codigo":133,"Mes":"agosto/2011 "},{"Codigo":132,"Mes":"julho/2011 "},{"Codigo":131,"Mes":"junho/2011 "},{"Codigo":130,"Mes":"maio/2011 "},{"Codigo":129,"Mes":"abril/2011 "},{"Codigo":128,"Mes":"março/2011 "},{"Codigo":127,"Mes":"fevereiro/2011 "},{"Codigo":126,"Mes":"janeiro/2011 "},{"Codigo":125,"Mes":"dezembro/2010 "},{"Codigo":124,"Mes":"novembro/2010 "},{"Codigo":123,"Mes":"outubro/2010 "},{"Codigo":122,"Mes":"setembro/2010 "},{"Codigo":121,"Mes":"agosto/2010 "},{"Codigo":120,"Mes":"julho/2010 "},{"Codigo":119,"Mes":"junho/2010 "},{"Codigo":118,"Mes":"maio/2010 "},{"Codigo":117,"Mes":"abril/2010 "},{"Codigo":61,"Mes":"março/2010 "},{"Codigo":60,"Mes":"fevereiro/2010 "},{"Codigo":59,"Mes":"janeiro/2010 "},{"Codigo":58,"Mes":"dezembro/2009 "},{"Codigo":57,"Mes":"novembro/2009 "},{"Codigo":56,"Mes":"outubro/2009 "},{"Codigo":55,"Mes":"setembro/2009 "},{"Codigo":54,"Mes":"agosto/2009 "},{"Codigo":53,"Mes":"julho/2009 "},{"Codigo":52,"Mes":"junho/2009 "},{"Codigo":51,"Mes":"maio/2009 "},{"Codigo":50,"Mes":"abril/2009 "},{"Codigo":49,"Mes":"março/2009 "},{"Codigo":48,"Mes":"fevereiro/2009 "},{"Codigo":47,"Mes":"janeiro/2009 "},{"Codigo":46,"Mes":"dezembro/2008 "},{"Codigo":45,"Mes":"novembro/2008 "},{"Codigo":44,"Mes":"outubro/2008 "},{"Codigo":43,"Mes":"setembro/2008 "},{"Codigo":42,"Mes":"agosto/2008 "},{"Codigo":41,"Mes":"julho/2008 "},{"Codigo":40,"Mes":"junho/2008 "},{"Codigo":38,"Mes":"maio/2008 "},{"Codigo":37,"Mes":"abril/2008 "},{"Codigo":36,"Mes":"março/2008 "},{"Codigo":35,"Mes":"fevereiro/2008 "},{"Codigo":34,"Mes":"janeiro/2008 "},{"Codigo":33,"Mes":"dezembro/2007 "},{"Codigo":32,"Mes":"novembro/2007 "},{"Codigo":31,"Mes":"outubro/2007 "},{"Codigo":30,"Mes":"setembro/2007 "},{"Codigo":29,"Mes":"agosto/2007 "},{"Codigo":28,"Mes":"julho/2007 "},{"Codigo":27,"Mes":"junho/2007 "},{"Codigo":26,"Mes":"maio/2007 "},{"Codigo":24,"Mes":"abril/2007 "},{"Codigo":23,"Mes":"março/2007 "},{"Codigo":21,"Mes":"fevereiro/2007 "},{"Codigo":20,"Mes":"janeiro/2007 "},{"Codigo":19,"Mes":"dezembro/2006 "},{"Codigo":18,"Mes":"novembro/2006 "},{"Codigo":17,"Mes":"outubro/2006 "},{"Codigo":16,"Mes":"setembro/2006 "},{"Codigo":15,"Mes":"agosto/2006 "},{"Codigo":14,"Mes":"julho/2006 "},{"Codigo":13,"Mes":"junho/2006 "},{"Codigo":12,"Mes":"maio/2006 "},{"Codigo":11,"Mes":"abril/2006 "},{"Codigo":10,"Mes":"março/2006 "},{"Codigo":9,"Mes":"fevereiro/2006 "},{"Codigo":8,"Mes":"janeiro/2006 "},{"Codigo":111,"Mes":"dezembro/2005 "},{"Codigo":6,"Mes":"novembro/2005 "},{"Codigo":2,"Mes":"outubro/2005 "},{"Codigo":1,"Mes":"setembro/2005 "},{"Codigo":7,"Mes":"agosto/2005 "},{"Codigo":25,"Mes":"julho/2005 "},{"Codigo":116,"Mes":"junho/2005 "},{"Codigo":115,"Mes":"maio/2005 "},{"Codigo":114,"Mes":"abril/2005 "},{"Codigo":113,"Mes":"março/2005 "},{"Codigo":112,"Mes":"fevereiro/2005 "},{"Codigo":110,"Mes":"janeiro/2005 "},{"Codigo":101,"Mes":"dezembro/2004 "},{"Codigo":100,"Mes":"novembro/2004 "},{"Codigo":99,"Mes":"outubro/2004 "},{"Codigo":109,"Mes":"setembro/2004 "},{"Codigo":108,"Mes":"agosto/2004 "},{"Codigo":107,"Mes":"julho/2004 "},{"Codigo":106,"Mes":"junho/2004 "},{"Codigo":105,"Mes":"maio/2004 "},{"Codigo":104,"Mes":"abril/2004 "},{"Codigo":103,"Mes":"março/2004 "},{"Codigo":102,"Mes":"fevereiro/2004 "},{"Codigo":98,"Mes":"janeiro/2004 "},{"Codigo":89,"Mes":"dezembro/2003 "},{"Codigo":88,"Mes":"novembro/2003 "},{"Codigo":87,"Mes":"outubro/2003 "},{"Codigo":97,"Mes":"setembro/2003 "},{"Codigo":96,"Mes":"agosto/2003 "},{"Codigo":95,"Mes":"julho/2003 "},{"Codigo":94,"Mes":"junho/2003 "},{"Codigo":93,"Mes":"maio/2003 "},{"Codigo":92,"Mes":"abril/2003 "},{"Codigo":91,"Mes":"março/2003 "},{"Codigo":90,"Mes":"fevereiro/2003 "},{"Codigo":86,"Mes":"janeiro/2003 "},{"Codigo":77,"Mes":"dezembro/2002 "},{"Codigo":76,"Mes":"novembro/2002 "},{"Codigo":75,"Mes":"outubro/2002 "},{"Codigo":85,"Mes":"setembro/2002 "},{"Codigo":84,"Mes":"agosto/2002 "},{"Codigo":83,"Mes":"julho/2002 "},{"Codigo":82,"Mes":"junho/2002 "},{"Codigo":81,"Mes":"maio/2002 "},{"Codigo":80,"Mes":"abril/2002 "},{"Codigo":79,"Mes":"março/2002 "},{"Codigo":78,"Mes":"fevereiro/2002 "},{"Codigo":74,"Mes":"janeiro/2002 "},{"Codigo":66,"Mes":"dezembro/2001 "},{"Codigo":65,"Mes":"novembro/2001 "},{"Codigo":64,"Mes":"outubro/2001 "},{"Codigo":73,"Mes":"setembro/2001 "},{"Codigo":72,"Mes":"agosto/2001 "},{"Codigo":71,"Mes":"julho/2001 "},{"Codigo":70,"Mes":"junho/2001 "},{"Codigo":69,"Mes":"maio/2001 "},{"Codigo":68,"Mes":"abril/2001 "},{"Codigo":67,"Mes":"março/2001 "},{"Codigo":63,"Mes":"fevereiro/2001 "},{"Codigo":62,"Mes":"janeiro/2001 "}]

=====

Para consultar as marcas das motos:

curl --url 'https://veiculos.fipe.org.br/api/veiculos/ConsultarMarcas' \
  -H 'accept: application/json, text/javascript, */*; q=0.01' \
  -H 'accept-language: pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7' \
  -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
  -b '<cookies do navegador omitidos na versão pública>' \
  -H 'origin: https://veiculos.fipe.org.br' \
  -H 'priority: u=0, i' \
  -H 'referer: https://veiculos.fipe.org.br/' \
  -H 'sec-ch-ua: "Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36' \
  -H 'x-requested-with: XMLHttpRequest' \
  --data-raw 'codigoTabelaReferencia=338&codigoTipoVeiculo=2'

[{"Label":"ADLY","Value":"60"},{"Label":"AGRALE","Value":"61"},{"Label":"AMAZONAS","Value":"131"},{"Label":"APRILIA","Value":"62"},{"Label":"ATALA","Value":"63"},{"Label":"AVELLOZ","Value":"216"},{"Label":"BAJAJ","Value":"64"},{"Label":"BEE","Value":"205"},{"Label":"Benelli","Value":"162"},{"Label":"BETA","Value":"65"},{"Label":"BIMOTA","Value":"66"},{"Label":"BMW","Value":"67"},{"Label":"BRANDY","Value":"68"},{"Label":"BRAVA","Value":"130"},{"Label":"BRP","Value":"150"},{"Label":"BUELL","Value":"117"},{"Label":"BUENO","Value":"155"},{"Label":"BULL","Value":"212"},{"Label":"byCristo","Value":"69"},{"Label":"CAGIVA","Value":"70"},{"Label":"CALOI","Value":"71"},{"Label":"CFMOTO","Value":"266"},{"Label":"DAELIM","Value":"72"},{"Label":"DAFRA","Value":"145"},{"Label":"DAYANG","Value":"137"},{"Label":"DAYUN","Value":"142"},{"Label":"DERBI","Value":"73"},{"Label":"DUCATI","Value":"74"},{"Label":"EMME","Value":"75"},{"Label":"FEVER","Value":"248"},{"Label":"FOX","Value":"132"},{"Label":"FUSCO MOTOSEGURA","Value":"209"},{"Label":"FYM","Value":"128"},{"Label":"GARINNI","Value":"143"},{"Label":"GAS GAS","Value":"76"},{"Label":"GREEN","Value":"133"},{"Label":"HAOBAO","Value":"138"},{"Label":"HAOJUE","Value":"203"},{"Label":"HARLEY-DAVIDSON","Value":"77"},{"Label":"HARTFORD","Value":"78"},{"Label":"HERO","Value":"79"},{"Label":"Hisun","Value":"261"},{"Label":"HONDA","Value":"80"},{"Label":"HUSABERG","Value":"81"},{"Label":"HUSQVARNA","Value":"82"},{"Label":"INDIAN","Value":"202"},{"Label":"IROS","Value":"158"},{"Label":"JIAPENG VOLCANO","Value":"141"},{"Label":"JOHNNYPAG","Value":"174"},{"Label":"JONNY","Value":"151"},{"Label":"KAHENA","Value":"129"},{"Label":"KASINSKI","Value":"118"},{"Label":"KAWASAKI","Value":"85"},{"Label":"KTM","Value":"87"},{"Label":"KYMCO","Value":"204"},{"Label":"LANDUM","Value":"159"},{"Label":"L\u0027AQUILA","Value":"88"},{"Label":"LAVRALE","Value":"89"},{"Label":"LERIVO","Value":"139"},{"Label":"LEVA","Value":"258"},{"Label":"LIFAN","Value":"178"},{"Label":"Lon-V","Value":"148"},{"Label":"MAGRÃO TRICICLOS","Value":"175"},{"Label":"Malaguti","Value":"146"},{"Label":"MIZA","Value":"126"},{"Label":"Mobílli","Value":"259"},{"Label":"MOTO GUZZI","Value":"90"},{"Label":"MOTOCAR","Value":"201"},{"Label":"MOTOMORINI","Value":"255"},{"Label":"MOTORINO","Value":"200"},{"Label":"MRX","Value":"160"},{"Label":"MV AGUSTA","Value":"91"},{"Label":"MVK","Value":"92"},{"Label":"NIU","Value":"239"},{"Label":"ORCA","Value":"93"},{"Label":"PEGASSI","Value":"164"},{"Label":"PEUGEOT","Value":"94"},{"Label":"PIAGGIO","Value":"95"},{"Label":"POLARIS","Value":"210"},{"Label":"REGAL RAPTOR","Value":"173"},{"Label":"RIGUETE","Value":"198"},{"Label":"Royal Enfield","Value":"192"},{"Label":"SANYANG","Value":"96"},{"Label":"SBM","Value":"262"},{"Label":"SHINERAY","Value":"134"},{"Label":"SIAMOTO","Value":"97"},{"Label":"SUNDOWN","Value":"98"},{"Label":"SUPER SOCO","Value":"237"},{"Label":"SUZUKI","Value":"99"},{"Label":"SWM","Value":"267"},{"Label":"TARGOS","Value":"176"},{"Label":"TIGER","Value":"187"},{"Label":"TRAXX","Value":"119"},{"Label":"TRIUMPH","Value":"100"},{"Label":"Ventane Motors","Value":"244"},{"Label":"VENTO","Value":"180"},{"Label":"VESPA","Value":"256"},{"Label":"VOGE","Value":"268"},{"Label":"VOLTZ","Value":"215"},{"Label":"WATTS","Value":"243"},{"Label":"WUYANG","Value":"135"},{"Label":"YAMAHA","Value":"101"},{"Label":"ZONTES","Value":"242"}]

Sendo que codigoTabelaReferencia é conforme a requisição anterior
codigoTipoVeiculo
2 = Moto
1 = Carros
3 = Caminhões

======
Com a reposta das marcas
Consultamos os modelos:

curl --url 'https://veiculos.fipe.org.br/api/veiculos/ConsultarModelos' \
  -H 'accept: application/json, text/javascript, */*; q=0.01' \
  -H 'accept-language: pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7' \
  -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
  -b '<cookies do navegador omitidos na versão pública>' \
  -H 'origin: https://veiculos.fipe.org.br' \
  -H 'priority: u=0, i' \
  -H 'referer: https://veiculos.fipe.org.br/' \
  -H 'sec-ch-ua: "Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36' \
  -H 'x-requested-with: XMLHttpRequest' \
  --data-raw 'codigoTipoVeiculo=2&codigoTabelaReferencia=338&codigoModelo=&codigoMarca=131&ano=&codigoTipoCombustivel=&anoModelo=&modeloCodigoExterno='

{"Modelos":[{"Label":"AME-110 MIX","Value":4360},{"Label":"AME-150 TC/ SC","Value":4361},{"Label":"AME-250 C1","Value":4362},{"Label":"AME-LX 125/26","Value":4363}],"Anos":[{"Label":"2009","Value":"2009-1"},{"Label":"2008","Value":"2008-1"},{"Label":"2007","Value":"2007-1"},{"Label":"2006","Value":"2006-1"}]}

========

Depois os anos do modelo

curl --url 'https://veiculos.fipe.org.br/api/veiculos/ConsultarAnoModelo' \
  -H 'accept: application/json, text/javascript, */*; q=0.01' \
  -H 'accept-language: pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7' \
  -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
  -b '<cookies do navegador omitidos na versão pública>' \
  -H 'origin: https://veiculos.fipe.org.br' \
  -H 'priority: u=0, i' \
  -H 'referer: https://veiculos.fipe.org.br/' \
  -H 'sec-ch-ua: "Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36' \
  -H 'x-requested-with: XMLHttpRequest' \
  --data-raw 'codigoTipoVeiculo=2&codigoTabelaReferencia=338&codigoModelo=4361&codigoMarca=131&ano=&codigoTipoCombustivel=&anoModelo=&modeloCodigoExterno='

[{"Label":"2009","Value":"2009-1"},{"Label":"2008","Value":"2008-1"},{"Label":"2007","Value":"2007-1"},{"Label":"2006","Value":"2006-1"}]

=====
Depois os anos

curl --url 'https://veiculos.fipe.org.br/api/veiculos/ConsultarModelosAtravesDoAno' \
  -H 'accept: application/json, text/javascript, */*; q=0.01' \
  -H 'accept-language: pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7' \
  -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
  -b '<cookies do navegador omitidos na versão pública>' \
  -H 'origin: https://veiculos.fipe.org.br' \
  -H 'priority: u=0, i' \
  -H 'referer: https://veiculos.fipe.org.br/' \
  -H 'sec-ch-ua: "Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36' \
  -H 'x-requested-with: XMLHttpRequest' \
  --data-raw 'codigoTipoVeiculo=2&codigoTabelaReferencia=338&codigoModelo=4361&codigoMarca=131&ano=2008-1&codigoTipoCombustivel=1&anoModelo=2008&modeloCodigoExterno='

[{"Label":"AME-110 MIX","Value":"4360"},{"Label":"AME-150 TC/ SC","Value":"4361"},{"Label":"AME-250 C1","Value":"4362"},{"Label":"AME-LX 125/26","Value":"4363"}]


==========
E pra finalizar,
o detalhamento do marca, ano, modelo selecionado

curl --url 'https://veiculos.fipe.org.br/api/veiculos/ConsultarValorComTodosParametros' \
  -H 'accept: application/json, text/javascript, */*; q=0.01' \
  -H 'accept-language: pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7' \
  -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
  -b '<cookies do navegador omitidos na versão pública>' \
  -H 'origin: https://veiculos.fipe.org.br' \
  -H 'priority: u=0, i' \
  -H 'referer: https://veiculos.fipe.org.br/' \
  -H 'sec-ch-ua: "Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36' \
  -H 'x-requested-with: XMLHttpRequest' \
  --data-raw 'codigoTabelaReferencia=338&codigoMarca=131&codigoModelo=4361&codigoTipoVeiculo=2&anoModelo=2008&codigoTipoCombustivel=1&tipoVeiculo=moto&modeloCodigoExterno=&tipoConsulta=tradicional'

{"Valor":"R$ 3.022,00","Marca":"AMAZONAS","Modelo":"AME-150 TC/ SC","AnoModelo":2008,"Combustivel":"Gasolina","CodigoFipe":"855002-6","MesReferencia":"outubro de 2026 ","Autenticacao":"prpl2z0j94q","TipoVeiculo":2,"SiglaCombustivel":"G","DataConsulta":"segunda-feira, 5 de outubro de 2026 21:46"}

===== FIM DO CONHECIMENTO =====
<context_window_protection>
  <priority_instructions>
    Every byte a tool returns enters your conversation memory and costs reasoning capacity for the rest of the session. The context-mode tools let you do the work in a sandbox and surface only the derived answer — the raw bytes stay out. Think-in-Code: program the analysis, do not compute it by reading raw data into your conversation.
  </priority_instructions>

  <deferred_tool_bootstrap>
    The context-mode tools below may be DEFERRED in your harness — their schemas are not loaded yet, so calling them directly fails (e.g. "tool not found" / InputValidationError). Load them ONCE before your first ctx_* call:
    ToolSearch(query: "select:mcp__plugin_context-mode_context-mode__ctx_batch_execute,mcp__plugin_context-mode_context-mode__ctx_search,mcp__plugin_context-mode_context-mode__ctx_execute,mcp__plugin_context-mode_context-mode__ctx_execute_file,mcp__plugin_context-mode_context-mode__ctx_fetch_and_index")
    After that they are callable. If any ctx_* call fails as not-found, ToolSearch it and retry — do NOT fall back to Bash/Read just because the schema was not loaded yet.
  </deferred_tool_bootstrap>

  <tool_selection_hierarchy>
    0. MEMORY: mcp__plugin_context-mode_context-mode__ctx_search(sort: "timeline")
       - On resume or compaction, query prior decisions, errors, plans, user prompts before asking the user — auto-captured session memory is searchable.
    1. GATHER: mcp__plugin_context-mode_context-mode__ctx_batch_execute(commands, queries)
       - Primary research tool. Runs commands in parallel, auto-indexes each output, and (when queries are passed) returns matching sections in the same round trip — no follow-up search call.
       - Each command: {label: "section header", command: "shell command"}; the label becomes the FTS5 chunk title — descriptive labels improve search.
    2. FOLLOW-UP: mcp__plugin_context-mode_context-mode__ctx_search(queries: ["q1", "q2", ...])
       - Multiple related questions about anything already indexed (your captures + session memory). Batch every question in one array; the ranking pipeline runs per-query and the round-trip cost is paid once.
    3. PROCESSING: mcp__plugin_context-mode_context-mode__ctx_execute(language, code) | mcp__plugin_context-mode_context-mode__ctx_execute_file(path, language, code)
       - Derive answers FROM data: filter, count, aggregate, parse, transform. Only what you console.log() enters your conversation; the raw bytes stay in the sandbox.
  </tool_selection_hierarchy>

  <when_not_to_use>
    - You intend to PROCESS the output (filter, count, parse, aggregate) → use mcp__plugin_context-mode_context-mode__ctx_batch_execute or mcp__plugin_context-mode_context-mode__ctx_execute. Bash stays correct when you intend to OBSERVE a short fixed output (git status on a clean tree, whoami, pwd) or when you are mutating state (git, mkdir, rm, mv, navigation).
    - You want to analyze, summarize, or extract from a file → use mcp__plugin_context-mode_context-mode__ctx_execute_file. Read stays correct when you intend to Edit the file (Edit needs the exact bytes in your conversation to match against).
    - WebFetch → use mcp__plugin_context-mode_context-mode__ctx_fetch_and_index; full network access, results indexed for mcp__plugin_context-mode_context-mode__ctx_search, raw page bytes never enter your conversation.
    - mcp__plugin_context-mode_context-mode__ctx_execute and mcp__plugin_context-mode_context-mode__ctx_execute_file for file writes → these run code in a subprocess and discard the sandbox FS; they are for analysis, processing, and computation only.
  </when_not_to_use>

  <file_writing_policy>
    File writes use the native Write or Edit tool — mcp__plugin_context-mode_context-mode__ctx_execute, mcp__plugin_context-mode_context-mode__ctx_execute_file, and Bash subprocesses do not persist edits to the host filesystem.
    Applies to all file types: code, configs, plans, specs, YAML, JSON, markdown.
  </file_writing_policy>

  <output_constraints>
    <artifact_policy>
      Write artifacts (code, configs, PRDs) to files. Return only: file path + 1-line description.
    </artifact_policy>
  </output_constraints>
  <session_continuity>
    Skills, roles, and decisions set during this session remain active until the user revokes them.
    Do not drop behavioral directives as context grows.
  </session_continuity>

</context_window_protection>