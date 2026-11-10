# Ficha: Lotes (Atribuir matriz · Atribuir template F1/F2)

Desde o U7a, os lotes não são mais uma tela: são a barra de ações em massa da aba Lista do hub Projetos (`/ui/projeto/ano/<ano>/`, ficha [`projeto.md`](projeto.md)). O GET de `/ui/lotes/<ano>/matriz/` e `/ui/lotes/<ano>/template/` (e de `/ui/lotes/`) redireciona (302) para a Lista; o POST antigo continua gravando.

## Objetivo

Atribuir, de uma vez, a mesma matriz a vários parceiros do ano, ou o mesmo template F1/F2 às revistas de um componente desses parceiros. Nada é atribuído sozinho: alguém marca e aplica. Quem está com o projeto aberto não perde trabalho: o projeto dele é pulado e listado.

## Quem usa

| Perfil | O que faz |
|---|---|
| Pedagógica, Mídias Digitais, Admin | Marcam parceiros e aplicam (permissão de alterar parceiro do ano / fascículo da revista) |
| Impresso | Vê a Lista com a matriz e a situação de cada revista; sem caixas de marcar e sem barra |
| Sem permissão de ver projeto | Não entra (403) |

## Na jornada

- **Antes:** a aba Cortes cria os projetos e as revistas do ano; as matrizes e os templates do ano já existem.
- **Atribuir matriz → Atribuir template:** primeiro a matriz de cada parceiro, depois os templates das revistas.
- **Depois:** a revista (textos por seção, "Validar revista") e o Painel, onde a falta de matriz ou template aparece.
- Um projeto só: a aba Matriz da página do projeto grava pelo mesmo serviço (`servicos.matriz.atribuir_matriz`).

## Dados mostrados (na Lista)

- Uma caixa de marcar por parceiro, na primeira linha dele (o alvo é o parceiro do ano); "Marcar todos os parceiros" no cabeçalho.
- Matriz atual de cada parceiro (ou "sem matriz"). Ao escolher a matriz no modal, as linhas marcadas mostram a nova ao lado da atual.
- Selos: "Em edição por <nome>: será pulado" (o bloqueio do próprio usuário não conta: o lote o toma, D-191/D-221) e "Sem projeto ativo" (a matriz grava assim mesmo).
- Barra fixa: "N selecionado(s)", "Atribuir matriz…" e "Atribuir template…".

## Dados gravados

- **Matriz:** a matriz do parceiro no ano.
- **Template:** o template F1 e/ou F2 das revistas ativas do componente escolhido nos parceiros marcados. Fascículo em "Não mudar" fica como está. Fascículo com texto próprio (cópia de seção) é pulado: troca-se pela página da revista, com a frase de descarte.
- Cada parceiro/revista grava sozinho, com o bloqueio do projeto só durante a escrita; um erro num não desfaz os outros.
- Revista validada que mudaria passa pelo modal de impacto antes de gravar (nada grava até confirmar).

## Ações

| Ação | Quem | Resultado |
|---|---|---|
| Marcar / desmarcar; "Marcar todos" | quem aplica | contador "N selecionado(s)"; com zero, os botões da barra ficam desligados ("Marque ao menos um parceiro") |
| Atribuir matriz… | `change_parceiroano` | modal com o select "Matriz"; "Atribuir matriz" grava e volta à Lista |
| Atribuir template… | `change_revistafasciculo` | modal com "Componente", "Template F1" e "Template F2"; "Atribuir template" grava e volta à Lista |
| Confirmar no modal de impacto | quem aplica | reenvia com a confirmação e grava |

## Estados

- **Erro de formulário:** nada gravado; a Lista volta com a seleção e as escolhas e as mensagens: "Marque ao menos um parceiro." · "Escolha a matriz." · "Escolha o template do F1, do F2 ou dos dois." · "Nada foi gravado: Escolha o componente." · opção fora da lista: "Escolha uma opção da lista; a lista mudou desde que a página abriu."
- **Ano sem matriz:** o modal mostra "Nenhuma matriz em <ano>: cadastre em Matrizes." **Ano sem componente:** "Nenhum componente em <ano>: cadastre os componentes do ano." (link para `ui_ano`, com a permissão).
- **Impacto:** o modal "Atribuir matriz tira o “Validado” de N revista(s)" (ou "Atribuir template…") lista as revistas; Cancelar não grava.
- **Bloqueio:** a Lista não trava nada ao abrir. Projeto aberto por outra pessoa, ou arquivado entre a abertura e o clique, é pulado: "Pulados: GO (projeto em edição por Ana); PE (projeto arquivado)."
- **Sucesso:** "Matriz <nome> escolhida para N parceiro(s)." / "Template escolhido em N revista(s)." Com revistas que perderam o "Validado", o aviso com o link para revalidar no Painel.

## Permissões

- Login obrigatório; anônimo vai ao login das telas B (`/conta/entrar/`).
- Ver a Lista: `view_projeto` ou `change_projeto`.
- Atribuir matriz: `change_parceiroano`. Atribuir template: `change_revistafasciculo`. Sem a permissão, o botão não aparece e o POST dá 403. Ação desconhecida na URL: 404.

## Interações

- Os dois modais ficam dentro do form `massa`; o botão de cada um envia para a sua ação (`formaction` → `POST /ui/projeto/ano/<ano>/massa/<matriz|template>/`, rota `ui_projeto_massa`). Envio normal, volta à Lista (PRG). Depois de uma recusa (erro ou impacto), o form volta com a ação recusada no `action`, e o "Confirmar" do modal de impacto reenvia.
- Marcar todos, contador, prévia da matriz nova e ligar os botões: `static/ui/telas/lotes.js`, por delegação.

## Critérios de aceite

1. Pedagógica marca GO e PE na Lista, "Atribuir matriz…", escolhe Nova e aplica: os dois ficam com Nova e aparece "Matriz Nova escolhida para 2 parceiro(s)."
2. Com o projeto de GO aberto por outra pessoa: a linha mostra "Em edição por …: será pulado" e o envio pula GO ("Pulados: …").
3. Sem nada marcado, os botões da barra ficam desligados; o POST vazio volta com "Marque ao menos um parceiro." e nada muda.
4. Matriz de outro ano é recusada.
5. Template: só templates do ano, componente e fascículo; revista com texto próprio no F1 é pulada no F1; F2 em "Não mudar" não muda.
6. Revista validada que muda: o modal de impacto abre e nada grava até confirmar.
7. Impresso não vê caixas nem barra; POST 403. Anônimo: login das telas B (`/conta/entrar/`).
8. `GET /ui/lotes/2026/matriz/` redireciona (302) para `/ui/projeto/ano/2026/`; o POST antigo continua gravando.
9. O lote do admin segue funcionando (mesma regra).

## Referências técnicas

- Regra: `app/nucleo/lotes.py` (`MatrizLoteForm`, `TemplateLoteForm`, `gravar_matriz`, `gravar_template`, `perdem_matriz`, `perdem_template`, `escrever_travado`, `em_edicao`), usada pelo admin (`admin/lote.py`), pela Lista (`urls/ui_projeto.py`: `massa`) e pelas rotas antigas (`urls/ui_lotes.py`: `aplicar`, `para_a_lista`).
- Templates: `templates/ui/projeto/lista.html` (barra e modais), `_componentes/impacto.html`. As páginas antigas `templates/ui/lotes/*` só aparecem depois de um POST antigo.
- Testes: `app/nucleo/tests/test_ui_projetos.py`, `test_ui_lotes.py`.
- Decisões: D-102 (atribuição em lote), D-104 (troca de template com cópias), D-121 (pular travados), D-164/D-167 (lotes no admin, arquivados), D-183/D-186 (telas B), as do plano de UX (D-195 em diante) e D-221 (selo ignora o próprio usuário).
- Inventário: T18, T19.
