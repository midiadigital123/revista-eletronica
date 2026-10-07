# state.md — revista-express

## Estado atual
Passo 3 de 4: script e teste prontos; falta confirmar cortes do 5º ano
Funcionando: `python3 scripts/extrair_descritores.py <pdf> <pasta>` gera lingua-portuguesa.json (2ef: 8, 5ef: 15) e matematica.json (2ef: 33, 5ef: 28); `python3 scripts/test_extrair_descritores.py` → 4 OK
Quebrado/pendente: cortes do 5º ano são suposição (Saeb); contrato não aceita 2ef

## Próxima ação
Confirmar os cortes do 5º ano (LP 150/200/250, MT 175/225/275) em `CORTES_SEM_NUMERO`.

## Plano
1. [x] Parser `scripts/extrair_descritores.py`
2. [x] Teste `scripts/test_extrair_descritores.py`
3. [ ] Confirmar cortes do 5º ano  ← agora
4. [ ] Contrato aceitar `2ef` (se o usuário quiser)

## Decisões

### D-001 — Um JSON por disciplina (2026-10-07)
- **Contexto:** a revista tem LP e MT (2º e 5º EF); descritores.json só tem nível de ano.
- **Decisão:** gerar `lingua-portuguesa.json` e `matematica.json`, cada um `{ "2ef": ..., "5ef": ... }`.
- **Motivo:** mantém o formato do descritores.json; um projeto do editor por disciplina.
- **Descartadas:** JSON único com disciplina no topo — foge do formato.
- **Arquivos afetados:** `scripts/extrair-descritores.mjs`
- **Status:** ativa

### D-002 — topic vazio (2026-10-07)
- **Contexto:** o PDF não tem "TÓPICO".
- **Decisão:** `topic = ""`.
- **Motivo:** schema aceita; não inventar dado.
- **Descartadas:** unidade temática/objeto — duplicaria bncc.knowledge.
- **Arquivos afetados:** `scripts/extrair-descritores.mjs`
- **Status:** ativa

### D-003 — Coordenadas (pdftotext -bbox) em vez de texto -layout (2026-10-07)
- **Contexto:** prerrequisitos em 2 colunas, ticks × cortes em colunas diferentes, rótulos BNCC centralizados (MT D06 sai trocado no -layout).
- **Decisão:** ler palavras com x/y via `pdftotext -bbox` (poppler), Node sem dependências.
- **Motivo:** posição resolve colunas e associação rótulo↔valor.
- **Descartadas:** `-layout` + regex — frágil; pdfplumber/pdfjs — dependência nova.
- **Arquivos afetados:** `scripts/extrair-descritores.mjs`
- **Status:** ativa

### D-004 — Script em Python, stdlib + pdftotext (2026-10-07)
- **Contexto:** usuário pediu Python em vez de JS.
- **Decisão:** `scripts/extrair_descritores.py`, só stdlib, chamando `pdftotext -bbox` via subprocess; teste em unittest.
- **Motivo:** pedido do usuário; pypdf/pdfplumber não instalados.
- **Descartadas:** versão .mjs (removida); pdfplumber — dependência nova.
- **Arquivos afetados:** `scripts/extrair_descritores.py`, `scripts/test_extrair_descritores.py`
- **Status:** ativa

### D-005 — Texto da régua pertence ao tick logo abaixo (2026-10-07)
- **Contexto:** posição do texto em relação aos ticks varia por página (ex.: LP 2ef D04).
- **Decisão:** cada linha de texto vai para o primeiro tick abaixo dela (= base da faixa, como `montarFaixasRegua`); abaixo do último tick vai para o mínimo; "–" vira "---".
- **Motivo:** confere com as linhas cinzas da página renderizada.
- **Descartadas:** tick acima — erra D01.
- **Arquivos afetados:** `scripts/extrair_descritores.py`
- **Status:** ativa

### D-006 — Cortes do 5º ano por tabela (2026-10-07)
- **Contexto:** páginas do 5º ano não imprimem números de corte; 2º ano imprime (LP 350/400/500, MT 400/500/625).
- **Decisão:** `CORTES_SEM_NUMERO` com valores Saeb (LP 150/200/250, MT 175/225/275), usada só quando o PDF não traz os 3 cortes.
- **Motivo:** rótulos Básico/Proficiente da página ficam nesses ticks.
- **Descartadas:** ler linhas vetoriais (pdftocairo -svg) — linhas de corte não são caminhos consistentes.
- **Arquivos afetados:** `scripts/extrair_descritores.py`
- **Status:** ativa, aguardando confirmação

## Perguntas em aberto
- [ ] Cortes do 5º ano corretos? — depende de: usuário
- [ ] Contrato (`contrato/schemas.ts:14`) não aceita `2ef` — depende de: usuário decidir se o contrato ganha o ano.

## Sessões
### 2026-10-07
- PDF base trocado para SAEGO_2025_RE_Alfa_2EF_5EF Web.pdf; plano aprovado.
- Script reescrito em Python; 84 descritores extraídos; 4 testes OK.
