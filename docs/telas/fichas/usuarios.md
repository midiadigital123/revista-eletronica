# Ficha: Usuários (e Entrar, Criar senha)

Endereço: `/ui/usuarios/` (rota `ui_usuarios`). Entra pelo link "Usuários" do cabeçalho, ao lado de "Sair", só com `auth.change_user`; fora do menu de 5 itens (D-210). Login e criar senha são páginas soltas, sem menu (D-212, D-216).

## Objetivo

Dar e tirar acesso sem abrir o admin: criar usuário, mudar o grupo, gerar o link para a pessoa criar a própria senha, redefinir a senha, desativar e excluir quem nunca registrou nada. Regra completa: [`docs/regras-de-negocio.md`](../../regras-de-negocio.md), seção 8.2 "Regras de usuários".

## Quem usa

| Perfil | O que faz aqui |
|---|---|
| Superusuário | Vê e altera todos, inclusive outros Admins; dá qualquer grupo, Admin incluso. |
| Admin | Não vê superusuários. Dá Pedagógica, Mídias Digitais e Impresso (D-220) e altera quem está nesses grupos. Outro Admin: só vê ("Só o superusuário altera"). Não muda o próprio grupo nem se desativa ou se exclui. |
| Pedagógica, Mídias Digitais, Impresso | Não veem o link "Usuários"; a URL dá 403. |
| Sem login | Vai ao login (`/conta/entrar/`) e volta depois de entrar. |

## Na jornada

- **Antes:** a pessoa pede acesso a quem gerencia usuários.
- **Aqui:** "Novo usuário" (com senha) ou, para não mandar senha, "Link de acesso" na linha: copia a mensagem pronta e envia.
- **Depois:** a pessoa abre o link, cria a senha em `/conta/senha/<uid>/<token>/` e entra por `/conta/entrar/`. Quem sai da equipe é desativado; o histórico dele fica.

## Dados mostrados

- Tabela: Usuário (selo "você" na própria linha), Nome, Grupo, Situação ("Ativo" / "Desativado", linha desativada esmaecida), Último acesso ("Nunca entrou"), Ações. Ativos primeiro, por usuário.
- Grupo: seletor com os grupos que o ator pode dar, onde ele pode mudar; senão, o nome do grupo em texto ("Sem grupo").

## Dados gravados

- Usuário novo: usuário, nome, sobrenome, e-mail, senha (validadores do Django) e um grupo. Nasce `is_staff`. Nenhum campo de privilégio (`is_superuser`, `is_staff`, `user_permissions`) entra pelo POST.
- Grupo (troca o grupo inteiro por um só), `is_active`, senha.
- Excluir apaga o usuário só sem rastro (D-218).

## Ações

| Ação | Onde | Quem | Resultado |
|---|---|---|---|
| Novo usuário | cabeçalho | `auth.add_user` | `/ui/usuarios/novo/` (`ui_usuarios_novo`): form; cria e volta à lista com "Usuário <u> criado no grupo <g>." |
| Mudar (grupo) | coluna Grupo | `pode_mudar_grupos` | botão aparece só quando o seletor sai do grupo atual (CSS `:has`, D-217); POST `ui_usuarios_grupo` |
| Link de acesso (ícone `link`) | Ações | `pode_editar`, só usuário ativo | POST `ui_usuarios_link`: página com o link e a mensagem pronta, cada um com "Copiar" (D-216) |
| Redefinir senha (ícone `key-round`) | Ações | `pode_editar` | `/ui/usuarios/<pk>/senha/` (`ui_usuarios_senha`): nova senha duas vezes |
| Desativar / Ativar (ícone `user-x` / `user-check`) | Ações | `pode_mudar_ativo` | POST `ui_usuarios_ativo` com `acao` |
| Excluir (lixeira) | Ações | `pode_mudar_ativo` | `/ui/usuarios/<pk>/excluir/` (`ui_usuarios_excluir`), página comum `ui/excluir.html`: com rastro, lista o que impede e manda desativar; sem rastro, digitar o usuário |

As ações da linha são botões-ícone com `aria-label` e `data-dica` (D-217). Sem nenhuma ação permitida, a célula diz "Só o superusuário altera".

## Estados

- **Link de acesso:** vale `PASSWORD_RESET_TIMEOUT` (3 dias, o padrão do Django), funciona uma vez e cai quando a senha muda ou a pessoa entra. Se o usuário já tem senha, ela continua valendo até a nova.
- **Link vencido ou usado:** a página de criar senha mostra o erro e "Ir para o login".
- **Excluir com rastro:** a página lista versões de template, validações, fotos, ações no admin e edições no histórico, e não mostra o botão de excluir. Rastro novo enquanto a página estava aberta: nada é excluído.
- **Login errado:** aviso com `aria-invalid` nos dois campos.

## Mensagens exatas

- "Usuário <u> criado no grupo <g>." · "<u> agora está no grupo <g>." · "Grupo de <u> não mudou: escolha um dos grupos da lista."
- "<u> ativado: volta a entrar no sistema." · "<u> desativado: não entra mais. O histórico dele fica."
- "Senha de <u> redefinida. Passe a senha nova a ele por um canal seguro."
- "Exclusão feita: o usuário <u>." · "Nada foi excluído: <u> passou a ter registro no sistema enquanto a página estava aberta."
- Com rastro: "<u> já registrou trabalho no sistema, e excluir apagaria o autor desses registros. Para tirar o acesso, desative na lista de usuários."
- Login: "Usuário ou senha incorretos. Confira os dois e tente de novo. As maiúsculas contam."
- Link vencido: "Este link venceu ou já foi usado. Peça um novo a quem gerencia os usuários."
- Senha criada: "Pronto. Entre com seu usuário e a senha nova."

## Permissões

- Ver e alterar: `auth.change_user` (`gerenciar_usuarios`, só o Admin; `nucleo/permissoes.py`). Criar: também `auth.add_user`. Sem elas, 403.
- Alvo pelo `pk`, filtrado por `visiveis`: superusuário fora da lista de quem não é superusuário (404).
- Cada ação repete a regra no servidor (403), porque o template só esconde o controle. Regra única em `nucleo/usuarios.py`, usada também pelo admin.
- Sem `auth.delete_user` de propósito: a exclusão passa só por esta tela (D-218).

## Interações

- Tudo é form comum com PRG; sem HTMX nem bloqueio de edição.
- "Link de acesso" é POST: o link aparece só na resposta, não fica em URL nem no histórico. O endereço vem do `Origin` do POST (o `https` que o proxy tira do request).
- Login: `LoginView` do Django com `ui/entrar.html`; `/admin/login/` redireciona para cá com o `next` (D-212). "Sair" é POST em `/conta/sair/` e volta ao login.

## Critérios de aceite

1. Admin vê "Usuários" no cabeçalho e a lista sem superusuários; Pedagógica não vê o link e recebe 403 na URL.
2. Admin dá Pedagógica, Mídias Digitais e Impresso, não Admin; o superusuário dá todos.
3. Admin não muda o próprio grupo nem se desativa ou se exclui; outro Admin aparece só para ver.
4. Usuário novo nasce `is_staff`; campos de privilégio no POST são ignorados.
5. "Link de acesso" leva à página de criar senha das telas B; a senha criada vale no login; o link usa a origem `https` atrás do proxy.
6. Excluir: sem rastro, sai digitando o usuário; com rastro, a página lista o que impede e nada sai.

## Referências técnicas

- Regra: `app/nucleo/usuarios.py` (`visiveis`, `grupos_atribuiveis`, `pode_editar`, `pode_mudar_ativo`, `pode_mudar_grupos`, `preparar_novo`, `caminho_definir_senha`, `rastros`, `excluir`).
- Telas: `app/nucleo/urls/ui_usuarios.py`, `app/nucleo/urls/conta.py`; templates `ui/usuarios/{lista,form,link}.html`, `ui/excluir.html`, `ui/entrar.html`, `ui/senha_definir.html`, `ui/senha_pronto.html`; CSS `static/ui/telas/usuarios.css`.
- Testes: `app/nucleo/tests/test_ui_usuarios.py`; `app/e2e/tests/usuarios.spec.ts`.
- Decisões: D-142, D-210 (S9), D-211, D-212, D-216, D-217, D-218, D-220.
