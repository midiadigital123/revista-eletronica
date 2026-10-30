# Ficha da tela: Impresso (o que mudou, Revista Impressa Atualizada, planilhas)

Endereço: `/ui/impresso/<ano>/` (sem ano: vai ao ano mais recente).

## Objetivo

Mostrar à equipe do impresso, revista por revista, o que mudou no texto desde a última entrega ao InDesign, deixar copiar o texto novo e baixar as planilhas, e registrar "Revista Impressa Atualizada" quando o InDesign recebeu tudo. Depois do registro, o aviso de impresso daquela revista some do painel.

## Quem usa

| Perfil | O que faz aqui |
|---|---|
| Impresso | Vê, copia, baixa planilhas e marca "Revista Impressa Atualizada". É o único que marca. |
| Pedagógica, Mídias Digitais, Admin | Veem o que mudou e baixam planilhas; não marcam (só leitura). |
| Sem permissão de ver revistas | Recebe "acesso negado". |
| Sem login | Vai para o login do admin e volta depois de entrar. |

## Jornada

- **Antes:** a pedagógica edita a revista e dá o "Validado" (tela da revista ou validação em lote). O painel do ano mostra "falta" na coluna Impresso.
- **Aqui:** o impresso abre a tela pelo menu "Impresso" (ou pela coluna Impresso do painel), escolhe uma revista "Para atualizar", leva o texto novo ao InDesign e marca.
- **Depois:** a revista fica "Em dia"; o painel mostra ✓ na coluna Impresso até a próxima mudança de texto.

## Dados mostrados

- Seletor de ano.
- Resumo: quantas revistas estão para atualizar, quantas aguardam "Validado", total de revistas ativas do ano.
- Lista das revistas ativas do ano (parceiro e componente), cada uma com a situação: **Para atualizar** (mudou e está validada), **Aguardando "Validado"** (mudou, sem validação nesta versão) ou **Em dia** (nada mudou).
- Detalhe da revista escolhida:
  - de quando e de quem é a última "Revista Impressa Atualizada" (e se a foto foi herdada de um projeto arquivado), ou "Primeira entrega";
  - por fascículo (F1, F2) e grupo (seção, cores, escala e descritores de cada etapa): cada item que mudou, marcado como **novo**, **alterado** ou **removido**, com a comparação antes/depois e o texto novo inteiro para copiar.

## Dados gravados

Só um: a foto "impresso" da revista (o registro da "Revista Impressa Atualizada"), com quem marcou e a versão exata que a tela mostrou. Nada mais muda.

## Ações

| Ação | Quem | Resultado |
|---|---|---|
| Trocar de ano | todos | recarrega a tela no ano escolhido |
| Escolher revista na lista | todos | troca só o detalhe; o endereço muda (dá para voltar e compartilhar o link) |
| Copiar texto novo | todos | copia o texto do item; sem área de transferência, seleciona o texto para Ctrl+C |
| Baixar planilhas | todos | baixa o zip com as planilhas do F1 (etapa × componente) e do F2 |
| Abrir preview | todos | abre a revista como ela sai, em outra aba |
| Revista Impressa Atualizada | Impresso, com a revista validada nesta versão | grava a foto e volta à mesma revista, agora "Em dia" |
| Ver no painel | todos | abre o painel do ano filtrado por "falta Impresso" |

## Estados

- **Ano sem revistas:** estado vazio "Nenhuma revista ativa neste ano" com o botão "Abrir cortes".
- **Primeira entrega:** sem foto anterior; tudo aparece como novo.
- **Aguardando "Validado":** aviso amarelo; sem botão de marcar.
- **Só leitura (perfil sem marcar):** aviso "Só leitura"; sem botão de marcar.
- **Mudou só o que o diff de texto não mostra** (formatação ou arquivo de item): aviso para baixar as planilhas e conferir.
- **Em dia:** estado vazio "Impresso em dia".
- **Arquivada:** não aparece na lista (só revistas ativas). Se for arquivada com a tela aberta, o clique é recusado com mensagem.
- **Projeto em edição por outra pessoa:** a tela abre normalmente (ler não trava o projeto); o clique de marcar é recusado com mensagem e nada é gravado.
- **Sucesso:** mensagem verde e a revista passa a "Em dia".

## Mensagens exatas

- Sucesso: "Revista Impressa Atualizada: os avisos desta revista foram zerados."
- Recusas (prefixo "Impresso não atualizado: …"):
  - "Impresso não atualizado: a revista não está “Validado” na versão que a página mostrou; recarregue."
  - "Impresso não atualizado: a revista mudou depois que a página abriu; confira de novo."
  - "Impresso não atualizado: projeto em edição por <nome>."
  - "Impresso não atualizado: projeto arquivado." / "Impresso não atualizado: revista arquivada."
- Aguardando: "Aguardando o “Validado” da pedagógica nesta versão: só depois dele o impresso pode marcar. Confira o que mudou e volte quando a revista estiver validada."
- Só leitura: "Só leitura: seu perfil vê o que mudou, mas não marca a revista como impressa. Para marcar, peça o perfil Impresso a um administrador."
- Diff invisível: "Mudou algo que o diff de texto não mostra (formatação ou arquivo de item). Baixe as planilhas e confira no InDesign."
- Barra de marcar: "Confirma que o InDesign recebeu as mudanças desta página. Se a revista mudar antes do envio, o clique é recusado."
- Erro de rede/servidor ao trocar de revista: toast padrão da base ("Não feito: …").

## Permissões

- Ver: login + permissão de ver revistas (mesma da página antiga do impresso).
- Marcar: permissão "marcar impressa" (só o perfil Impresso; o Admin não tem). Sem ela, o envio é recusado com "acesso negado".
- O clique leva a versão que a tela mostrou; o servidor só grava se a revista está validada exatamente nela e se ninguém está com o projeto aberto para edição.

## HTMX

- Clicar numa revista da lista: `hx-get` do mesmo endereço com `?revista=<id>`, troca só o detalhe e põe o endereço no histórico. Sem JavaScript, o link recarrega a página inteira no mesmo estado. O foco vai para o título da revista escolhida (o leitor de tela não lê o diff inteiro). Voltar/avançar do navegador mostra a página inteira, nunca só o detalhe.
- "Copiar texto novo" copia o texto do campo; sem área de transferência, seleciona o texto e avisa "Selecionado: use Ctrl+C" (o rótulo é anunciado ao leitor de tela).
- Marcar é um formulário comum (envia, volta para a mesma revista com a mensagem). O botão é desabilitado no envio para não clicar duas vezes.

## Wireframe (1440 px)

```
┌ Revista Eletrônica   Painel Cortes Variáveis Matrizes Templates Revistas [Impresso]     Nome  Admin  Sair ┐
│                                                                                                          │
│ Impresso                                                                              Ver no painel     │
│ O que mudou em cada revista desde a última “Revista Impressa Atualizada”, para levar ao InDesign.      │
│ [2026|2025]                                                                                              │
│ (2 para atualizar) (1 aguardando “Validado”)  9 revista(s) ativa(s) em 2026                              │
│ ┌ lista ───────────────────────┐  GO · LP                                                                │
│ │▌GO · LP        Para atualizar│  Comparado com a última “Revista Impressa Atualizada”, de 12/03 por Ana. │
│ │ GO · MT   Aguardando Validado│  [⤓ Baixar planilhas]  Abrir preview                                     │
│ │ PE · LP              ✓ Em dia│  F1 ─────────────────────────────────────────────────────────────────    │
│ └──────────────────────────────┘  ┌ 5EF ───────────────────────────────────────────────────────────────┐ │
│                                   │ D01 (alterado)                                                       │ │
│                                   │ ┌ Antes ───────────────────┬ Depois ─────────────────────────────┐   │ │
│                                   │ │ 100–150: Localiza.       │ 100–175: Localiza.                  │   │ │
│                                   │ └──────────────────────────┴─────────────────────────────────────┘   │ │
│                                   │ [texto novo inteiro, só leitura, mono]                               │ │
│                                   │ [⧉ Copiar texto novo]                                                │ │
│                                   └──────────────────────────────────────────────────────────────────────┘ │
│                                   ┌ barra fixa no rodapé ───────────────────────────────────────────────┐ │
│                                   │ Confirma que o InDesign recebeu…      [Revista Impressa Atualizada] │ │
│                                   └──────────────────────────────────────────────────────────────────────┘ │
```

390 px: uma coluna; a lista vira uma caixa rolável de até 16rem acima do detalhe; a comparação rola na horizontal; a barra de marcar fica no fim do detalhe (não fixa, para não cobrir o texto).

## Critérios de aceite

1. Com permissão de ver, `GET /ui/impresso/2026/` responde 200 com a casca B, a lista das revistas ativas e o detalhe da revista pedida (ou da primeira "Para atualizar").
2. `GET` com `HX-Request` devolve só o detalhe; revista inexistente ou de outro ano dá 404.
3. Pedagógica vê a tela com o aviso de só leitura e sem botão; o POST de marcar dá 403. Usuário sem ver revistas recebe 403.
4. Impresso, com a revista validada, vê o botão; o clique grava a foto "impresso" com ele como autor, volta à mesma revista com a mensagem de sucesso e a revista aparece "Impresso em dia".
5. Versão mudou depois que a página abriu: recusa com a mensagem exata e nada é gravado.
6. Projeto aberto por outra pessoa: recusa "projeto em edição por …" e nada é gravado.
7. Anônimo vai ao login do admin (GET e POST).
8. Ano sem revistas mostra o estado vazio com o link para os cortes.
9. O menu "Impresso" da casca aponta para esta tela.
10. A página antiga do impresso e seus testes continuam iguais (mesma regra).

## Referências técnicas

- Regra: `app/nucleo/urls/impresso.py` (`situacao`, `estado`, `gravar`, `pode_marcar`; extraídos da view antiga, que passou a usá-los), `servicos/validacao.py` (`marcar_impressa`), `admin/lote.py` (`escrever_travado`), `servicos/planilhas.py` (`zip_planilhas`, servido pela rota antiga `impresso_planilhas`).
- Tela B: `app/nucleo/urls/ui_impresso.py`, `templates/ui/impresso/impresso.html`, `templates/ui/parciais/impresso_detalhe.html`, `templates/ui/_componentes/impresso_situacao.html`, `static/ui/telas/impresso.css`, `tests/test_ui_impresso.py`.
- Decisões: D-072, D-074, D-077, D-089, D-094, D-118 (impresso só textos e escalas), D-121 (bloqueio no lote), D-178, D-183, D-186.
- Bloqueio: esta tela não usa o bloqueio de edição de página (`com_bloqueio`), como a página antiga: ler não trava o projeto; o clique adquire e libera o bloqueio dentro da transação (`escrever_travado`).
