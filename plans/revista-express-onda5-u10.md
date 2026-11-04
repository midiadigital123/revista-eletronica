# Plano: Onda 5 (U10, acabamento visual e documentação)

## Contexto

U0 a U9 estão mergeados em `feat/telas-b-ux` (topo `1b9f32d`; Django 703 OK, Playwright 51/51). Falta o U10 de `plans/revista-express-telas-b-ux.md:330-337`. Ele cobre quatro coisas: tabelas largas com cabeçalho e coluna fixos, os estados visuais, a crítica com o impeccable e a documentação. Só depois dele vêm S6–S9 (decisão d do plano). A execução segue a D-201: um subagente por passo, cada um com worktree, branch `feat/ux-u10<x>-<nome>` e compose próprios. Eu faço o merge na raiz.

O que já existe e deve ser reaproveitado, em vez de recriado:
- Sticky espalhado em três lugares de `app/nucleo/static/ui/ui.css`: `.tabela-padroes` (:180), `.grade` (:291-319) e `.tabela-densa` (:397-398). O U10a junta tudo num componente só.
- Estado vazio: `.vazio` (`ui.css:529-536`) e `_componentes/vazio.html`, já incluído 30 vezes. Vários templates ainda escrevem "Nenhum…" solto.
- Animação `@keyframes entra` (`ui.css:265`) e o `prefers-reduced-motion` global (`ui.css:79`).
- `docs/telas/design-system.md` já documenta Alpine, o autosave (U3), a linha nova (U4), o modal de impacto (U2), o renomear (U5), o seletor de ano e o popover (U9). Faltam a tabela rolável e os estados.
- Fichas: `docs/telas/fichas/` não tem `cortes.md` nem `anos.md`. A tabela de `docs/telas/telas-b.md:28-35` ainda manda Anos, Abrir ano e Padrões do ano para o admin, mas hoje eles estão na tela B.

## Ondas internas

| Etapa | Em paralelo | Branch | Porta | Tempo |
|---|---|---|---|---|
| 5.1 | U10a tabela rolável · U10b estados · U10c fichas | `feat/ux-u10a-tabela-rolavel`, `feat/ux-u10b-estados`, `feat/ux-u10c-docs` | 8021, 8022, sem docker | ~3 h (o mais longo) |
| 5.2 | Integração na raiz: merge a → b → c e testes | `feat/telas-b-ux` | 8000 | ~40 min |
| 5.3 | U10d crítica, correção em lote e Playwright em 2 larguras | `feat/ux-u10d-critica` | 8023 | ~3 h |
| 5.4 | Integração final, limpeza e `state.md` | `feat/telas-b-ux` | 8000 | ~40 min |

Total: cerca de 1 dia corrido, cerca de 7 h de agente.

### Preparo de cada worktree com docker (D-201, vale para U10a, U10b e U10d)

1. Copie o `.env` da raiz e **apague a linha `COMPOSE_PROJECT_NAME`**. Exporte `COMPOSE_PROJECT_NAME=ux-u10<x>` e `APP_PORT=<porta>` em todo comando.
2. Rode `docker compose up -d db app`, depois `migrate`, depois `criar_demo --ano 2026`, e crie um **ano 2025 vazio** (`Ano.objects.get_or_create(ano=2025)`). Sem esse ano, o `ano.spec` falha. Ver a learning de 04/11.
3. Crie os usuários `e2e` (superusuário) e `imp-e2e` (grupo Impresso), com senha aleatória guardada num arquivo do scratchpad, fora do repositório. Rode o Playwright com `E2E_BASE_URL=http://localhost:<porta>` e as quatro `E2E_*`. A regra é **0 pulados**.
4. No fim, rode `docker compose down -v`. O subagente faz o commit na própria branch, sem push e sem tocar no `state.md`.

---

### U10a: Tabela rolável (~3 h)

**É dono de:** bloco "tabelas" do `ui.css` (as linhas do sticky citadas acima), o novo `static/ui/componentes/tabela-rolavel.js`, a ordem dos scripts em `templates/ui/base.html` e **só o invólucro da tabela** nos templates: `parciais/cortes_grade.html`, `variaveis/pagina.html` e `parciais/variaveis_linha.html`, `parciais/painel_corpo.html`, `projeto/lista.html`, `anos/ano.html`. Não mexe em estado vazio nem em docs.

1. Teste antes (Playwright `tabela-rolavel.spec.ts`), na grade de Cortes e na planilha de Variáveis com viewport de 1024px:
   - rolar na horizontal deixa a primeira coluna no mesmo `x`;
   - o `thead` fica no topo ao rolar na vertical;
   - o invólucro ganha `data-rolou-esq` só depois de rolar e perde quando volta ao início; `data-rolou-dir` some no fim da rolagem.
   Rode e confira que **falha**.
2. Componente `.tabela-rolavel` em `ui.css`: o invólucro com `overflow:auto`, `thead th` e `.fixa` com sticky, e a sombra da borda por `::after` ligada aos atributos `data-rolou-*`. As regras de `.grade`, `.tabela-densa` e `.tabela-padroes` passam a usar o componente. As que sobrarem iguais são apagadas.
3. `tabela-rolavel.js`: um componente Alpine `tabelaRolavel` (build CSP, **todas as propriedades declaradas no objeto**, conforme a learning do Alpine CSP). Ele observa `scroll` e `ResizeObserver` e liga os atributos. Sem rolagem, não liga nada. Carregue o arquivo em `base.html` antes do Alpine, no mesmo padrão de `componentes/autosave.js`. Atualize `test_ui_base`, que confere os `<script>`.
4. Aplique nas cinco telas. Confira que continua **sem rolagem lateral da página** em 1440, 1024, 768 e 390px. A rolagem é só dentro do invólucro, como na correção de ontem (`4c41607`).
5. Suíte Django, `makemigrations --check` e Playwright completo no worktree. Commit `feat(ui-b): tabela rolável com cabeçalho e coluna fixos (U10a)`.
6. **Relatório final:** inclua o texto da linha `Tabela rolável` para a seção 4 do `design-system.md`. O U10d cola esse texto.

### U10b: Estados (~3 h)

**É dono de:** blocos "estado vazio", "animação" e "status" do `ui.css`, `_componentes/vazio.html`, `_componentes/status_salvo.html`, `componentes/autosave.js` (só as classes de estado) e **só o bloco vazio** dos templates. Não mexe no invólucro das tabelas.

1. Inventário: `grep -rn "Nenhum\|nenhum" templates/ui`. A lista começa por `projeto/lista.html`, `matriz/lista.html`, `templates/lista.html`, `parciais/matriz_lista.html` e `anos/anos.html`. Todo vazio solto vira `{% include "ui/_componentes/vazio.html" %}`, com título, uma frase "causa + o que fazer" e o botão da ação, quando o perfil puder executá-la. Exemplo: "Nenhum projeto em 2026 · + Novo projeto". Para o Impresso, a tela mostra só o texto, sem botão.
2. Testes Django, um por tela com vazio: o perfil que grava vê o botão e o Impresso não vê. Esses testes vêm antes da implementação.
3. Estados dos controles novos (`btn-icone`, `nome_inline`, linha nova, alça `.alca`, `popover-config`, área de soltar, botões do modal de impacto):
   - foco de 2px visível;
   - hover;
   - `:disabled` / `[aria-disabled]` com cursor e cor;
   - carregando com `aria-busy`, usando o `_componentes/girando.html` que já existe.
   O movimento fica em 120/180 ms com `--ease-saida`.
4. Linha nova entra com `animation: entra 120ms var(--ease-saida)`, reaproveitando o `@keyframes entra`. A troca de texto do `status_salvo` tem transição de 180 ms. As duas respeitam o `prefers-reduced-motion` global.
5. Playwright: a linha nova tem a animação `entra`, e o status muda com `transition-duration` de 180 ms. Suíte Django, `makemigrations --check` e Playwright completo. Commit `feat(ui-b): estados vazios que ensinam e estados dos controles novos (U10b)`.
6. **Relatório final:** inclua o texto para o `design-system.md` (estado vazio com ação; tabela de estados).

### U10c: Fichas e telas-b (~1,5 h, sem docker)

**É dono de:** `docs/telas/fichas/*` e `docs/telas/telas-b.md`. Não mexe no `design-system.md`, para não conflitar com o U10d.

1. Crie `fichas/cortes.md` (grade de Cortes dentro de Projetos, autosave por célula, 409 otimista, renomear inline, "+ Adicionar parceiro", planilha de grupos) e `fichas/anos.md` (seletor de ano, "Configurar <ano>", "Abrir novo ano", etapas na ordem escolar, componentes, Padrões do ano com Salvar por padrão). Siga o modelo de `fichas/projeto.md`.
2. Corrija a tabela de `telas-b.md:28-35`: Anos, Abrir ano, etapas, componentes, Padrões do ano e renomear parceiro já têm tela B. No admin ficam só o que ainda não tem tela (criar template, que é S7, e o que S6–S9 vão cobrir).
3. Revise as fichas que já existem contra U4 a U9b: lotes dentro de Projetos, painel agrupado, revista em duas colunas, template com seção travada. Corrija o que estiver desatualizado. Para conferir o comportamento real, leia o código: views em `app/nucleo/urls/` e templates em `templates/ui/`.
4. Commit `docs(telas): fichas de Cortes e Anos e telas-b em dia (U10c)`.

---

### 5.2 Integração (eu, na raiz)

1. `git merge --no-ff` de U10a, depois U10b, depois U10c. Conflito provável: o mesmo template mexido pelos dois (por exemplo, `projeto/lista.html`, invólucro × bloco vazio). Eu resolvo e registro na mensagem de merge.
2. Rodo a suíte Django com `--parallel 1` (sem outro agente rodando testes ao mesmo tempo), depois `makemigrations --check --dry-run`. Depois o Playwright completo no banco de dev, com a demo, o ano 2025 e o login E2E temporário.
3. Registro no `state.md` as decisões que aparecerem, por exemplo "tabela rolável substitui `.grade`/`.tabela-densa`".

### U10d: Crítica, correção em lote e 2 larguras (~4 h)

Roda num worktree novo, criado do topo da integração depois da 5.2.

0. **Correções da planilha de Variáveis e textos velhos (achados do U10c, decisão do usuário em 04/11), em TDD:**
   - Célula travada não desliga a planilha: o 409 de bloqueio de um projeto (`urls/ui_projeto.py` `campo`, sem `atual`) deixa só aquela linha/célula em só leitura com o nome de quem edita; o resto da planilha continua editável (`static/ui/componentes/autosave.js` ~:156-159). Teste Django do 409 + Playwright com dois contextos.
   - Sobrescrita na planilha: a rota passa a comparar o `original` enviado com o valor gravado; se diferente, responde 409 com `atual`, como a grade de Cortes, sem gravar. Teste Django (duas abas) e Playwright.
   - Mensagem de parceiro novo (`urls/cortes.py` `novo_parceiro`) sem "salve"; `templates/ui/lotes/template.html:11` sem link para o admin.

1. Adicione um segundo projeto ao `app/e2e/playwright.config.ts`: `desktop-1440` com `viewport 1440×900`, ao lado do `chromium` padrão (1280×720). Assim, todo `npx playwright test` passa nas duas larguras (102 execuções, cerca de 3 min).
2. Rode a skill `impeccable:impeccable` em modo **critique** e depois em modo **audit** nas telas alteradas pela reforma: Painel, Projetos (Lista, Cortes, Variáveis), Projeto, Revista, Matrizes/MEC, Templates/editor, Ano, Impresso. Use screenshots em 1440 e 1280. Junte tudo numa lista só, ordenada por gravidade.
3. Corrija **tudo num lote só**, dentro do mundo do `DESIGN.md` (Bancada Neutra; sem cor nova fora dos Padrões, do âmbar de aviso e do destructive). O que mudar comportamento ou exigir decisão do usuário não entra no lote: vai para o relatório como pergunta.
4. Rode o `detect --json` do impeccable uma vez sobre os templates e o CSS alterados. O resultado precisa vir sem achados abertos, ou com cada um justificado no relatório.
5. Atualize o `docs/telas/design-system.md`: cole os textos de U10a e U10b, registre o projeto de 1440 do Playwright e confira as linhas de libs e sha384.
6. Suíte Django, `makemigrations --check` e Playwright nas duas larguras. Commit `fix(ui-b): acabamento da crítica do impeccable e Playwright em 1440 e 1280 (U10d)`.

### 5.4 Integração final (eu, na raiz)

1. Faço o merge de U10d e rodo de novo a suíte Django, o `makemigrations --check` e o Playwright nas duas larguras, com 0 pulados.
2. Marco as caixas do U10 em `plans/revista-express-telas-b-ux.md:336-337`.
3. **Limpeza do banco de dev**, que estava autorizada para o fim do U10 (pergunta em aberto do `state.md`). Primeiro **listo** o que vou apagar: usuários `e2e`, `imp-e2e`, `demo-preview`; parceiro `DEMONSTRAÇÃO` e matriz `Demonstração`; parceiros `E2E …`; ano 2025 vazio. Só apago depois da sua confirmação. SAESE, SAEGO, PAEBES, TESTE, `otavio`, `midias`, `impresso` e `pedagogica` não entram. Aviso: depois disso, o Playwright no dev volta a pedir a demo e o ano 2025.
4. `trail check`, depois a anotação do trail, se houver algo novo, depois o commit final **só do `state.md`**.

## Verificação

- `docker compose exec -T app python manage.py test nucleo --parallel 1`: tudo OK (hoje são 703, mais os novos).
- `docker compose exec -T app python manage.py makemigrations --check --dry-run`: nenhuma migração.
- `cd app/e2e && E2E_* npx playwright test`: projetos `chromium` (1280) e `desktop-1440` verdes, **0 pulados**.
- Manual: na grade de Cortes e em Variáveis, rolar mostra a coluna fixa e a sombra; não há rolagem lateral da página em 390px; Projetos vazio em 2025 mostra "Nenhum projeto em 2025 · + Novo projeto" para o admin e só o texto para o Impresso.

## Arquivos críticos

- `app/nucleo/static/ui/ui.css` (U10a: bloco de tabelas; U10b: vazio, animação e status)
- `app/nucleo/static/ui/componentes/tabela-rolavel.js` (novo) e `templates/ui/base.html`
- `app/nucleo/templates/ui/_componentes/vazio.html`, `status_salvo.html`
- `app/e2e/playwright.config.ts`, `app/e2e/tests/tabela-rolavel.spec.ts` (novo)
- `docs/telas/design-system.md`, `docs/telas/telas-b.md`, `docs/telas/fichas/{cortes,anos}.md` (novos)
