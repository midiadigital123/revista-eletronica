# Ficha: Revistas e revista (T20/T21)

## Objetivo

Reunir numa página o que a equipe precisa para deixar uma revista pronta: o SVG do F2, a capa, o template de cada fascículo, o texto de cada seção e o "Validado". A lista do ano leva a cada revista, ao preview e ao zip.

## Quem usa

| Perfil | O que faz |
|---|---|
| Pedagógica, Admin | tudo: arquivos, templates, textos, "Validado" |
| Mídias Digitais | o mesmo da Pedagógica; usa a lista para baixar o zip |
| Impresso | só vê (textos, arquivos, estado do "Validado"); abre o preview e a tela do impresso |
| Sem ver revista | recebe "acesso negado" |

## Jornada

- **Antes:** Painel (coluna da revista, "falta" de SVG, capa, template ou textos) ou a escolha de template em lote.
- **Depois:** preview da revista, "Validado", tela do impresso, zip para Mídias.

## Telas

### Lista de revistas do ano (`/ui/revista/<ano>/`)

Mostra, por revista do ano: parceiro/projeto, componente, SVG (tem ou falta), capa (tem ou falta), situação (ativa, arquivada) e as ações Abrir, Preview e Zip.

### Revista (`/ui/revista/<ano>/<id>/`)

1. **Cabeçalho:** nome da revista, ano e componente; ações "Abrir preview" (nova aba), "Tela do impresso", "Baixar zip".
2. **Validado:** estado (validado por quem e quando; mudou depois do último "Validado"; ainda não validado), pendências que impedem, seções desatualizadas (só aviso), botão "Validado".
3. **Textos:** lista das seções à esquerda (F1 e F2, com marca "cópia" ou "desatualizada"); à direita, a seção escolhida com o texto e o botão "Salvar seção".
4. **Templates:** um seletor por fascículo; confirmação por texto quando a troca apaga cópias.
5. **Arquivos:** SVG do F2 (conferência de ids, gabarito) e capa (miniatura).

## Dados mostrados

- Revista: projeto, parceiro, componente, ano, SVG (tem/falta, ids conferidos), capa, arquivada.
- Por fascículo: template e versão em uso.
- Por seção: id, título (não edita), texto efetivo (cópia ou o do template), se é cópia, se está desatualizada e o diff "seu texto | template novo".
- Validado: quem e quando, pendências, seções desatualizadas.
- Revista arquivada: as seções da foto congelada.

## Dados gravados

- SVG do F2 (arquivo, hash, ids) e capa (arquivo, hash).
- Template de cada fascículo; ao trocar com cópias, as cópias daquele fascículo são apagadas.
- Cópia do texto de uma seção (cria, atualiza, mantém sobre a versão nova, descarta).
- "Validado" (hash, quando, quem).

## Ações

| Ação | Onde | Resultado |
|---|---|---|
| Abrir revista | lista | página da revista |
| Abrir preview | lista e cabeçalho | preview em nova aba (arquivada: versão arquivada) |
| Baixar zip | lista e cabeçalho | arquivo `.zip`; com pendências volta com a mensagem |
| Escolher seção | lista de seções | troca o painel da direita sem recarregar a página |
| Salvar seção | painel da seção | grava a cópia; a lista e o "Validado" se atualizam |
| Manter meu texto / Descartar cópia | painel da seção | regrava a versão da cópia / apaga a cópia |
| Salvar templates | card Templates | troca o template; com cópias exige a frase |
| Enviar SVG / capa | card Arquivos | grava; ids faltando gravam e avisam |
| Validado | card Validado | grava o "Validado" da versão exibida |

## Estados

- **Vazio:** ano sem revistas: "Nenhuma revista em <ano>. As revistas nascem quando os cortes do parceiro são lançados." com botão "Abrir cortes". Fascículo sem template: faixa vermelha "Falta escolher o template do F1." Sem SVG: "Sem SVG do F2." Sem capa: "Sem capa."
- **Erro:** arquivo inválido, texto inválido, confirmação errada: mensagem no campo e "Nada foi gravado: corrija os erros marcados."
- **Só leitura por perfil:** aviso "Só leitura: seu perfil vê a revista, mas não altera. Para editar, peça a permissão de revista a um administrador." Campos desabilitados, sem botões de gravar.
- **Só leitura por bloqueio:** aviso "Somente leitura: <pessoa> está editando…" (o mesmo do admin).
- **Arquivada:** aviso "Só leitura: revista arquivada. O texto mostrado é a foto do arquivamento." Sem bloqueio, sem formulários.
- **Sucesso:** mensagens verdes: "Textos do F1 salvos: introducao.", "Templates salvos.", "Arquivos salvos.", "Revista validada."

## Mensagens exatas

- Seção sem mudança: "Nada a salvar: o texto está igual ao que abriu."
- Texto editado e descartado juntos: "Editou e marcou “Descartar cópia”: escolha um dos dois."
- Troca com cópias: "Este fascículo tem textos editados (cópias de seção: …). Trocar o template apaga essas cópias: para confirmar, digite “descartar N cópia(s)” em Confirmação."
- Ids faltando: "Ids que faltam no SVG: …. Esperados: …. Baixar gabarito de ids".
- Validado recusado: "Não validada: <motivo>." (mudou, pendências, arquivada).
- Bloqueio perdido: "Não salvo: você perdeu o bloqueio de edição (outra pessoa ou aba abriu esta página). Recarregue e refaça a alteração."
- Zip recusado: "Zip recusado. Pendências: …"

## Permissões

- Login obrigatório; anônimo vai ao login do admin.
- Ver: ver ou alterar revista; sem isso, 403.
- Arquivos: alterar revista. Templates: alterar fascículo da revista. Textos: alterar revista e criar/alterar cópia de seção. Trocar template com cópias: também criar/alterar cópia de seção. Validado: permissão de validar.
- Revista ou projeto arquivado: só leitura para todos; POST é 403.
- Bloqueio: abrir a revista trava o projeto dela; quem não consegue o bloqueio vê só leitura; POST sem o bloqueio não grava.

## HTMX

- Escolher seção: `hx-get` no item da lista, alvo `#secao`, `hx-push-url` (o link funciona sem JS e ao recarregar).
- Salvar seção: `hx-post` do formulário da seção, alvo `#secao`; a resposta troca também a lista de seções e o card Validado (`hx-swap-oob`) e as mensagens.
- Templates, arquivos e Validado: formulário comum com recarga (PRG).

## Wireframe (1440 px)

```
Revista Eletrônica  Painel Cortes Variáveis Matrizes Templates [Revistas] Impresso      Ana  Admin  Sair
──────────────────────────────────────────────────────────────────────────────────────────────────────
‹ Revistas 2026
Projeto GO · Língua Portuguesa                          [Abrir preview ↗] [Tela do impresso] [Baixar zip]
GO · 2026

┌ Validado ─────────────────────────────────────────────────────────────────────────────────────────┐
│ Ainda não validado.                                                                  [ Validado ] │
│ ▲ Pendências que impedem: Falta o SVG do F2.                                                       │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘

Textos
┌ Seções ────────────┐ ┌ F1 · introducao ───────────────────────────────────────────────────────┐
│ F1 Padrão v3       │ │ Análise de {{nome_parceiro}}                    [cópia] [desatualizada] │
│ ▸ introducao  cópia│ │ ┌ Seu texto ───────────────┬ Template novo ───────────────┐            │
│   fechamento       │ │ │ …diff…                   │ …                             │            │
│ F2 Padrão v1       │ │ └──────────────────────────┴───────────────────────────────┘            │
│   passo1           │ │ ┌──────────────────────────────────────────────────────────┐            │
│   dlg-p2           │ │ │ texto em markdown (textarea mono)                         │            │
└────────────────────┘ │ └──────────────────────────────────────────────────────────┘            │
                       │ [ ] Manter meu texto   [ ] Descartar cópia                [Salvar seção] │
                       └──────────────────────────────────────────────────────────────────────────┘

┌ Templates ───────────────────────────────┐ ┌ Arquivos ──────────────────────────────────────────┐
│ F1 [Padrão           ▾]                  │ │ SVG do F2  ✓ Todos os 4 ids estão no SVG.          │
│ F2 [Padrão           ▾]                  │ │ [Escolher arquivo]   Baixar gabarito de ids        │
│ Confirmação (só se trocar com cópias)    │ │ Capa  [miniatura]  [Escolher arquivo]              │
│                         [Salvar templates]│ │                                [Salvar arquivos]  │
└──────────────────────────────────────────┘ └────────────────────────────────────────────────────┘
```

Em 390 px: tudo em uma coluna; a lista de seções vira uma faixa acima do painel; botões do cabeçalho quebram em linha.

## Critérios de aceite

1. Com permissão, a lista do ano mostra as revistas com links para abrir, preview e zip; a revista abre com os cinco blocos.
2. Impresso vê tudo sem campos de gravar e com o aviso de só leitura; qualquer POST dele é 403.
3. Salvar uma seção com texto novo cria a cópia só dessa seção pela mesma regra do admin; texto igual ao template não cria; texto inválido mostra o erro no campo e não grava.
4. Seção desatualizada mostra o diff, "Manter meu texto" e "Descartar cópia"; editar e descartar juntos é erro.
5. Trocar o template de fascículo com cópias sem a frase é recusado; com a frase, apaga as cópias e troca.
6. SVG com id faltando grava e avisa com o gabarito; arquivo inválido mostra o erro e não grava.
7. "Validado" grava com o hash da página; com hash velho, recusa com a mensagem.
8. Revista arquivada: só leitura com a foto; sem bloqueio; POST 403.
9. Outra pessoa com o projeto aberto: a página fica só leitura; POST não grava e mostra a mensagem de bloqueio perdido.
10. Anônimo vai ao login do admin.

## Referências técnicas

- Requisitos: `docs/telas/inventario.md` T20, T21; D-074, D-089, D-104, D-108, D-115, D-116, D-117, D-140, D-170, D-171, D-174.
- Regra: `app/nucleo/revista.py` (extraída de `admin/revista.py`), `servicos/validacao.py`, `servicos/arquivos.py`, `servicos/empacotar.py`, `ui_bloqueio.com_bloqueio`.
- Admin equivalente: `admin/revista.py`, `templates/nucleo/revista_change_form.html`.
