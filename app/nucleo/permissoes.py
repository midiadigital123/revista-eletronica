"""Perfis e permissões: tabela papel × ação (D-073, D-079, D-083, D-102).

Fonte única para código e testes. A migração 0007 congela uma cópia literal
desta tabela (migração não importa código que muda depois). Mudou aqui?
Crie uma migração de dados nova que sincronize os grupos; o teste
`test_permissoes.GruposNoBancoTest` falha até isso acontecer.

Nenhum papel tem `delete_*`: nada pede exclusão e revista nunca é apagada
(D-117, arquiva). Usuário se desativa, não se apaga (histórico usa SET_NULL).
"""

# Pergunta em aberto: admin pode clicar "Revista Impressa Atualizada"?
# Padrão: não. Mudar só aqui (e sincronizar os grupos numa migração nova).
ADMIN_MARCA_IMPRESSA = False

EDITA = ("add", "change", "view")


def _perms(app, modelos):
    """modelos: {modelo: ações} → conjunto de 'app.ação_modelo'."""
    return frozenset(f"{app}.{acao}_{modelo}" for modelo, acoes in modelos.items() for acao in acoes)


# Todos os modelos de nucleo (nomes em minúsculas, como no codename).
# O teste compara com o registro de apps: modelo novo sem entrada aqui falha.
MODELOS_NUCLEO = (
    "ano", "parceiro", "etapa", "componente", "corpadrao",
    "matriz", "matrizetapacc", "descritor", "tarefa",
    "parceiroano", "corte", "projeto", "projetopasso", "projetocor",
    "template", "templateversao",
    "revista", "revistafasciculo", "revistasecao", "fotorevista",
    "bloqueio",
)  # fmt: skip

# Ação de negócio → permissões Django que ela exige.
# Fora de propósito: ano só nasce por `abrir_ano` (S16); template_versao é só
# INSERT (D-115); FotoRevista nasce do clique do impresso; Bloqueio é do serviço.
ACOES = {
    "ver_tudo": _perms("nucleo", dict.fromkeys(MODELOS_NUCLEO, ("view",))),
    "abrir_ano": frozenset({"nucleo.abrir_ano"}),
    "editar_cadastros": _perms("nucleo", dict.fromkeys(("parceiro", "etapa", "componente", "parceiroano"), EDITA)),
    "editar_matriz": _perms("nucleo", dict.fromkeys(("matriz", "matrizetapacc", "descritor", "tarefa"), EDITA)),
    "preencher_cortes": _perms("nucleo", {"corte": EDITA}),
    "editar_templates": _perms("nucleo", {"template": EDITA, "templateversao": ("add", "view")}),
    "editar_paleta": _perms("nucleo", {"corpadrao": EDITA}),
    # Variáveis são colunas de Projeto (D-100). Revista e fascículo nascem por
    # serviço (só `change`); a seção copiada nasce ao salvar (`add`).
    # S11: `hash_validado`, `validado_em`, `validado_por` e `arquivada_em` são
    # readonly_fields no admin; só os serviços escrevem esses campos.
    "editar_projeto": _perms(
        "nucleo",
        {
            "projeto": EDITA,
            "projetopasso": EDITA,
            "projetocor": EDITA,
            "revista": ("change", "view"),
            "revistafasciculo": ("change", "view"),
            "revistasecao": EDITA,
        },
    ),
    "validar": frozenset({"nucleo.validar_revista"}),
    "marcar_impressa": frozenset({"nucleo.marcar_impressa"}),
    # Grupos são fixos (migração): admin só os vê. Usuário: sem delete (desativar).
    # S11 OBRIGATÓRIO: registrar User no admin com form/readonly_fields SEM
    # is_superuser, is_staff e user_permissions, e com `groups` limitado aos 4
    # grupos fixos. Sem isso, change_user deixa o admin se dar qualquer
    # permissão, e "Admin não marca impressa" (ADMIN_MARCA_IMPRESSA) vira enfeite.
    "gerenciar_usuarios": _perms("auth", {"user": EDITA, "group": ("view",)}),
}

PEDAGOGICA = (
    "ver_tudo", "abrir_ano", "editar_cadastros", "editar_matriz", "preencher_cortes",
    "editar_templates", "editar_paleta", "editar_projeto", "validar",
)  # fmt: skip

PAPEIS = {
    # D-083: admin = Pedagógica + usuários.
    "Admin": (*PEDAGOGICA, "gerenciar_usuarios", *(("marcar_impressa",) if ADMIN_MARCA_IMPRESSA else ())),
    "Pedagógica": PEDAGOGICA,
    "Mídias Digitais": PEDAGOGICA,  # D-073: mesmo que a Pedagógica
    "Impresso": ("ver_tudo", "marcar_impressa"),  # D-074: vê tudo e marca impressa
}


def permissoes(papel):
    """Conjunto de 'app.codename' do papel."""
    return frozenset().union(*(ACOES[acao] for acao in PAPEIS[papel]))
