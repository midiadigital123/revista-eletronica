# Etapa do projeto (clone com vínculo à base) — desenho

Data: 2026-11-06 · Decisões: D-229, D-230, D-231 (`state.md`) · Status: aprovado pelo usuário em 06/11

## 1. Intenção e porquê

Alguns parceiros avaliam etapas que a matriz deles não tem, como 4EF, 6EF e 8EF. Para montar essas escalas,
a equipe Pedagógica parte de uma etapa vizinha (3EF → 4EF, 9EF → 7EF), copia, acrescenta e tira itens.
Hoje isso só é possível duplicando a matriz inteira (D-113). Uma cópia inteira não recebe mais as correções
da matriz de origem, e o parceiro perde as correções de todas as outras etapas.

O que se quer:

1. Criar, **dentro do projeto**, uma etapa que só existe nele. Ela nasce em branco ou como clone de
   **qualquer** etapa de **qualquer** matriz cadastrada, de qualquer ano, e não só da matriz que o parceiro usa.
2. O clone **guarda a base** de onde veio. Quando a base muda, a mudança tem que chegar ao clone.
3. A chegada é uma **pendência obrigatória**, que bloqueia o Validado. Ela vem com uma comparação antes × depois.
4. **Nunca se perde o que foi digitado no projeto.** O texto local só muda por escolha explícita de uma pessoa.

**Antiobjetivos.** Se acontecer qualquer um destes, o desenho falhou, mesmo que funcione:

- o conteúdo da etapa do projeto muda sem ninguém ter visto;
- a pendência pode ser ignorada e a revista vai para o Impresso mesmo assim;
- a equipe passa a usar o recurso para criar versões paralelas silenciosas das etapas da Comunitária.

## 2. Objetivos e não-objetivos

**Dentro (1ª versão):** criar a etapa do projeto em branco ou como clone; editá-la com o editor de matriz que
já existe; detectar a mudança da base; tela de revisão em 3 vias; pendência que bloqueia o Validado; aviso no
modal de impacto de quem edita a base.

**Fora:**

| Item | Por quê |
|---|---|
| Juntar dois textos dentro de um mesmo campo | Escolhe-se o campo inteiro, como nos templates (D-115) |
| Clone de clone | A base é sempre etapa de **matriz** (D-230) |
| Etapa do projeto para uma etapa que a matriz já tem | Evita versões paralelas da Comunitária (D-230) |
| Desvincular da base | Seria a cópia solta que a D-229 descartou |
| Levar a etapa sozinha para o ano novo | O ano nasce sem escolhas (D-106). "Trazer do ano anterior" fica para a v2 |
| E-mail ao abrir a pendência | É outro bloco do brainstorming (eventos e e-mail ao validar) |

## 3. Decisões tomadas (pelo usuário, em 06/11)

1. **Comparação em 3 vias.** São comparadas a foto da base de quando clonou (ou da última revisão), a base de
   agora e o conteúdo local do projeto. Só o ancestral comum diz se quem mudou um item foi a base ou o projeto.
2. **O dono é o projeto.** Esta foi a escolha do usuário. A recomendação dos agentes era o parceiro no ano.
3. **Item que o projeto não tocou** vem pré-marcado como "aplicar" na revisão, mas **só grava** quando alguém
   clica em "Concluir revisão". Gravar a base nunca escreve no conteúdo do projeto.
4. **Sem cadeia:** só etapa de matriz serve de base.
5. **Só para etapa que a matriz do parceiro não tem.** A ação nasce da pendência `corte_sem_matriz`
   (`app/nucleo/servicos/resolver.py:335`).
6. **A soma com descarte de duplicatas** foi descartada: ela não propaga remoção nem correção de texto, e o
   texto velho fica ao lado do novo.

## 4. Como funciona

### 4.1 Criar
Na aba Matriz do projeto, a pendência "A matriz não tem a etapa: 4EF" ganha o botão **Criar etapa do projeto**,
com duas opções:

- **Em branco.**
- **A partir de:** seletor de matriz (de qualquer ano), depois etapa × componente. Só aparecem etapas de
  matriz, nunca as de outro projeto.

O clone copia passo, descritores e tarefas, reaproveitando o `clonar` usado em `servicos/matriz.py`. Na mesma
transação, com a base travada, grava a **foto** da base. O componente do clone é sempre o da revista.
Se a `escala_max` da etapa nova for diferente da etapa base (9EF → 7EF), as tarefas fora da escala aparecem
marcadas logo depois do clone. Elas já caem na pendência `corte_invalido`.

### 4.2 Editar
A etapa do projeto é uma `MatrizEtapaCC` comum, editada pela mesma tela do editor de matriz. Bloqueio de 30 s,
histórico, arquivos de tarefa e modal de impacto funcionam como hoje.

### 4.3 A base muda
- **Detecção sem sinal nem trigger.** Existe pendência quando o conteúdo canônico da base atual difere da foto.
  Isso pega edição pela tela, reimportação, admin e exclusão de descritor.
- O resolver acrescenta `{"tipo": "base", "etapa": "4ef"}` às `lacunas`. Como as lacunas entram no hash
  (`resolver.py:293`), três coisas acontecem com pouco código: `pendencias()` precisa de um ramo novo para a
  lacuna "base", e o resto vem de graça:
  1. a revista derivada perde o Validado;
  2. `pendencias()` passa a listar **"A etapa 4EF tem mudanças da base para revisar"**;
  3. `perdem_validado` passa a listar a revista no modal de quem edita a base, desde que `_afetadas`
     (`servicos/matriz.py:146`) inclua as revistas cujo projeto tem uma etapa com essa base.
- **Modal de quem edita a base:** às listas atuais soma-se "Abre revisão em: Minas Gerais LP · 4EF".
  Na reimportação de uma matriz, o modal informa quantos projetos derivados ganharão pendência.

### 4.4 Revisar (tela)
Abre a partir da pendência, na aba Matriz do projeto. Cada item é um campo do descritor ou uma tarefa,
classificado comparando a foto (A), a base de agora (B) e o local (L):

| Caso | Classificação | Na tela |
|---|---|---|
| L = A (o projeto não mexeu) | entra | pré-marcado "Usar o da base" |
| B = A (só o projeto mexeu) | fica o local | não aparece |
| L = B | igual | não aparece |
| os três diferentes (inclui apagar de um lado e editar do outro) | **conflito** | exige escolha |

- **Cabeçalho:** "3EF da Matriz Comunitária mudou em 06/11 (por Fulana). Faltam N decisões."
- **Grupo "Precisa da sua decisão"** (aberto e primeiro): um cartão por item, com "No seu projeto" de um lado e
  "Na base" do outro. A mudança da base aparece marcada como no controle de alterações do Word: riscado = saiu,
  sublinhado = entrou. A marca não depende só de cor. Botões: **Manter o meu** · **Usar o da base** ·
  **Editar…** (abre o campo com o texto local e mostra a base ao lado).
- **Grupo "Vem da base, confira"** (fechado): os itens pré-marcados. Cada um pode ser trocado para "Manter o meu".
- **Concluir revisão:** fica ativo quando todos os conflitos têm escolha. Abre o modal de impacto e, numa
  transação só, faz três coisas:
  1. aplica as escolhas no local;
  2. grava a nova foto = base de agora;
  3. confere o hash da base que a tela mostrou. Se a base mudou no meio, recusa com "recarregue", no mesmo
     padrão de `validacao.py`.

  O histórico registra o motivo, por exemplo "revisão da base: aplicou 7, manteve 2".
- **Recusa ("Manter o meu")** avança a foto daquele item. Ele só volta a aparecer se a base mexer nele de novo.

## 5. Regras de negócio

1. O sistema compara 3 versões porque só assim sabe quem mudou cada item: a base ou o projeto.
2. O sistema não altera texto do projeto sem uma pessoa escolher, porque o que foi digitado não pode se perder.
3. Enquanto a base tiver mudanças não revisadas, a revista derivada não pode ser validada e perde o Validado
   que tinha. Edição, prévia e zip continuam funcionando.
4. Quem pode criar, editar e revisar a etapa do projeto: Pedagógica, Mídias Digitais e Admin. É a ação
   `editar_projeto` de `app/nucleo/permissoes.py`, que os três já têm. O Impresso só vê.
5. Só existe etapa do projeto para etapa × componente que tem corte no parceiro e que a matriz do parceiro
   não tem.
6. Base com etapa de projeto derivada ativa não é excluída pela tela. A tela de exclusão lista os projetos
   derivados (D-205). Se a base sumir por fora, por exemplo no apagar ano, o vínculo vira nulo, a etapa vira
   cópia solta e a pendência some.
7. Projeto arquivado congela a etapa junto (D-093).
8. A base tem o mesmo componente da revista: um clone de LP só nasce de etapa LP. *(Decisão do Claude: clonar
   MT a partir de LP não tem uso pedagógico; o seletor escolhe matriz → etapa, e o componente vem da revista.)*
9. Se a revisão termina com o conteúdo igual ao que estava validado (por exemplo, tudo em "Manter o meu"), o
   hash volta a bater e o Validado reaparece sem novo clique. É a regra que já vale no sistema (D-094): o
   Validado é do conteúdo, não do clique.
10. Entram na revisão em 3 vias todos os campos que a revista mostra: os campos do descritor, a ordem dos
    descritores, o `passo` da etapa e, em cada tarefa, faixa, texto, `arquivo` e `texto_alternativo`. Para o
    `arquivo`, a tela mostra a imagem antes × depois. Trocar a imagem pela da base passa pelo
    `servicos.arquivos` que já existe, incluindo apagar o órfão (D-150, D-181). *(Decisão do Claude: deixar a
    imagem de fora quebraria a promessa de que a mudança da base chega ao clone.)*

## 6. Restrições do projeto (valem para o builder)

- Ano em toda tabela, com FK composta via `nucleo/db.py::fk_composta` e `reverse_sql`. O teste de
  `pg_constraint` muda junto.
- Regra que o banco precisa garantir fica em SQL (CHECK, unique parcial, trigger), não só no ORM.
- Escrita concorrente passa pelo bloqueio (`servicos/bloqueio.py`). O teste de concorrência usa `TransactionTestCase`.
- Toda função tem controle na tela B, nunca só no admin (D-189, D-210). A confirmação que afeta vários lugares
  é um modal, não um checkbox.
- O E2E cria o próprio parceiro "E2E …" e edita só ele (D-225).
- Esta funcionalidade substitui em parte a D-051 ("projeto não tem conteúdo próprio"). O builder registra uma
  decisão nova no `state.md`.

## 7. Modelo de dados (direção; detalhes ficam com o builder)

Sem tabela nova. Muda só `MatrizEtapaCC` (`app/nucleo/models/matriz.py:42`):

| Coluna | Regra |
|---|---|
| `projeto_id` | Nula. Dona da etapa local. FK composta `(projeto_id, ano_id)` |
| `matriz_id` | Passa a aceitar nulo. `CHECK num_nonnulls(matriz_id, projeto_id) = 1` |
| `base_id` | FK para a própria `MatrizEtapaCC`, `ON DELETE SET NULL` criado por SQL (padrão de `duplicada_de`). `CHECK base_id <> id`. Trigger recusa base que não seja de matriz |
| `base_foto` | jsonb. Conteúdo canônico da base, chaveado por **código** (descritor pelo `codigo`, tarefa pela faixa), nunca por id |

Mais um unique parcial `(projeto, etapa, componente) WHERE projeto_id IS NOT NULL`.

**Por que a foto e não o histórico:** a reimportação apaga e recria descritores e tarefas com ids novos
(`servicos/importar_matriz.py`). Por isso o django-simple-history não consegue remontar a base antiga.

**Normalização:** o conteúdo canônico normaliza espaços e quebras de linha. Sem isso, uma reimportação
cosmética gera uma pendência enorme.

**Encaixes:**
- `_f1_escalas` (`resolver.py:130`): lê também a MEC do projeto.
- `pendencias` (`resolver.py:335`): o `corte_sem_matriz` passa a considerar a MEC do projeto.
- `_afetadas` (`servicos/matriz.py:146`): inclui os derivados.
- `abrir_ano` e `apagar_ano` não podem quebrar com `matriz_id` nulo.
- `limpar_e2e`: também apaga as MECs de projeto.

O agente de dados contou cerca de 35 referências que assumem que a MEC tem matriz. A mais grave é
`abrir_ano.py:89-95`.

## 8. Fica com o builder

- Formato exato da foto e identidade da tarefa. Sugestão: `inicio-fim#n`. Na v1, uma tarefa com a faixa
  corrigida aparece como "removida + nova" (`ponytail:`, ~0,5 dia para parear por faixa depois).
- Onde a lógica de 3 vias vive (sugestão: `servicos/` novo ou estender `servicos/matriz.py::diferencas`).
- Como o editor de matriz é aberto para uma MEC sem matriz: rota e permissão `editar_projeto`.
- Testes: classificação das 3 vias (unitário, com os 4 casos da tabela + apagar × editar), concorrência
  da conclusão, constraints no `pg_constraint`, um spec E2E de ponta a ponta com parceiro próprio.

## 9. Custo estimado

6 a 11 dias para a 1ª versão. As estimativas dos agentes foram 6 dias (versionamento) e 9 a 11 dias (dados).

| Parte | Dias |
|---|---|
| Migração, CHECKs, trigger, testes de catálogo | 1 |
| Resolver, pendências, impacto, `abrir_ano` e `apagar_ano` com matriz nula | 1,5 |
| Criar etapa (em branco ou clone) e tela | 1,5 |
| Motor de 3 vias e testes | 1,5 |
| Tela de revisão | 2 a 2,5 |
| Modal, E2E e docs | 1 a 1,5 |

## 10. Decididos após a revisão (usuário, 06/11)

- **Projeto recriado pela cascata herda a etapa.** Quando todos os cortes saem, o projeto é arquivado, e quando
  voltam nasce um projeto novo (D-068, `servicos/cascata.py:87`). Nesse caso, a cascata transfere as etapas do
  projeto, com a foto e o `base_id`, para o projeto novo do mesmo parceiro no ano. A exceção à regra 7
  ("arquivado congela") vale só para essa transferência. Cumpre o "nunca se perde o que foi digitado".
  Custo: ~0,5 dia.
- **A matriz ganha a etapa depois.** Por troca de matriz ou porque a Comunitária passa a ter 4EF, abre a
  pendência "A matriz agora tem 4EF: escolha qual usar", que bloqueia o Validado. São dois botões, sem
  comparação:
  - **Manter a do projeto:** a escolha fica gravada e não volta a perguntar.
  - **Usar a da matriz:** a etapa do projeto deixa de valer, fica guardada e não é apagada.

  Enquanto ninguém escolhe, a revista mostra a do projeto. A regra 5 vale só na criação. Ela não cabe em
  CHECK, porque a matriz fica em `parceiro_ano`. Custo: ~1 dia. Com isso, o total da v1 fica entre 7,5 e
  12,5 dias.
