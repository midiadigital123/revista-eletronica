"""Dados 100% fictícios da demo. Nenhum nome, número ou texto aqui vem do banco real."""
import unicodedata

ANO = 2026
ANO_PROX = 2027


def slug(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return "-".join("".join(c if c.isalnum() else " " for c in t.lower()).split())


# ── Fases da esteira (um só vocabulário em todo o sistema) ────────────────
FASES = [
    (1, "preparar", "Preparar", "Matriz, cortes e dados do parceiro"),
    (2, "montar", "Montar", "Templates, infográficos, capa e textos"),
    (3, "conferir", "Conferir", "Pronta para validar"),
    (4, "validada", "Validada", "Validada; falta atualizar o impresso"),
    (5, "impressa", "Impressa", "Impresso em dia"),
]
FASE_NOME = {n: nome for n, _, nome, _ in FASES}
FASE_SLUG = {n: s for n, s, _, _ in FASES}

# Os 6 passos da ficha da revista, na ordem em que se resolvem.
PASSOS = [
    ("base", "Base", "Matriz, cortes e dados do parceiro"),
    ("templates", "Templates", "Um template para o F1 e outro para o F2"),
    ("infograficos", "Infográficos", "Alfa e Outras Etapas"),
    ("capa", "Capa", "Imagem da capa"),
    ("textos", "Textos", "Texto de cada seção"),
    ("conferir", "Revisão", "Preview, o que mudou e Validado"),
]

ETAPAS = [("2EF", 1000), ("5EF", 500), ("9EF", 500), ("3EM", 500)]
COMPONENTES = [("LP", "Língua Portuguesa"), ("MT", "Matemática")]
COMP_NOME = dict(COMPONENTES)

PADROES = [
    (1, "Baixo", "#f72628"),
    (2, "Básico", "#ff8d43"),
    (3, "Adequado", "#b3ccff"),
    (4, "Avançado", "#0ed3ff"),
]

# ── Pessoas (uma por perfil + extras) ─────────────────────────────────────
PERFIS = {
    "ped": "Pedagógica",
    "mid": "Mídias Digitais",
    "imp": "Impresso",
    "adm": "Admin",
}
PESSOAS = [
    {"id": "ana", "nome": "Ana Souza", "perfil": "ped", "usuario": "ana.souza", "acesso": "hoje, 09:12", "ativo": True},
    {"id": "bruno", "nome": "Bruno Lima", "perfil": "mid", "usuario": "bruno.lima", "acesso": "hoje, 08:40", "ativo": True},
    {"id": "carla", "nome": "Carla Mendes", "perfil": "imp", "usuario": "carla.mendes", "acesso": "ontem, 17:05", "ativo": True},
    {"id": "diego", "nome": "Diego Rocha", "perfil": "adm", "usuario": "diego.rocha", "acesso": "hoje, 07:58", "ativo": True},
    {"id": "elisa", "nome": "Elisa Prado", "perfil": "ped", "usuario": "elisa.prado", "acesso": "hoje, 10:02", "ativo": True},
    {"id": "fabio", "nome": "Fábio Nunes", "perfil": "mid", "usuario": "fabio.nunes", "acesso": "há 12 dias", "ativo": False},
]
# Quem a barra lateral mostra para cada perfil da demo.
EU = {"ped": PESSOAS[0], "mid": PESSOAS[1], "imp": PESSOAS[2], "adm": PESSOAS[3]}

# ── Parceiros: (sigla, nome, tipo, matriz, fase LP, fase MT) ──────────────
_P = [
    ("VV", "Vale Verde", "Estado", "vale-verde-2026", 3, 2),
    ("SA", "Serra Alta", "Estado", "serra-alta-2026", 4, 4),
    ("CD", "Costa Dourada", "Estado", "comunitaria-2026", 2, 2),
    ("PC", "Planalto Central", "Estado", "comunitaria-2026", 5, 5),
    ("AS", "Aurora do Sul", "Estado", "comunitaria-2026", 3, 3),
    ("IB", "Ilha Branca", "Estado", "comunitaria-2026", 2, 1),
    ("RC", "Rio Claro", "Estado", None, 1, 1),
    ("CL", "Campo Largo", "Município", "comunitaria-2026", 3, 2),
    ("PA", "Pedra Azul", "Município", "comunitaria-2026", 2, 2),
    ("MS", "Monte Sereno", "Município", "comunitaria-2026", 4, 3),
    ("FL", "Foz do Lago", "Município", "comunitaria-2026", 2, 3),
    ("BT", "Boa Terra", "Município", None, 1, 1),
    ("TC", "Três Cruzes", "Município", "comunitaria-2026", 5, 4),
    ("NV", "Nova Vitória", "Município", "comunitaria-2026", 3, 2),
    ("OV", "Ouro Velho", "Município", "comunitaria-2026", 2, 1),
    ("PO", "Porto Alvo", "Município", "comunitaria-2026", 5, 3),
]

# Combinações de pendência para quem está em Montar (revistas na fase 2).
_COMBOS = [
    ("infograficos", "capa"),
    ("capa",),
    ("textos",),
    ("templates", "textos"),
    ("infograficos",),
    ("capa", "textos"),
]
_PEND_TXT = {
    "templates": "Falta escolher o template do F2",
    "infograficos": "Infográfico Alfa sem habilidade",
    "capa": "Falta a capa",
    "textos": "3 seções sem texto",
}
_BASE_TXT = [
    "Sem matriz",
    "Cortes de 3EM LP faltando",
    "4 de 24 variáveis vazias",
]
EDITANDO = {"vale-verde-lp": "Elisa Prado", "costa-dourada-mt": "Bruno Lima"}
VALIDADAS = {  # fase >= 4: quem validou e quando
    "serra-alta-lp": ("Ana Souza", "10/11 15:20"),
    "serra-alta-mt": ("Ana Souza", "10/11 15:48"),
    "monte-sereno-lp": ("Elisa Prado", "11/11 09:30"),
    "tres-cruzes-mt": ("Ana Souza", "11/11 16:02"),
    "planalto-central-lp": ("Elisa Prado", "05/11 11:10"),
    "planalto-central-mt": ("Elisa Prado", "05/11 11:42"),
    "tres-cruzes-lp": ("Ana Souza", "06/11 14:15"),
    "porto-alvo-lp": ("Ana Souza", "06/11 14:50"),
}

PARCEIROS = []
REVISTAS = []
_n2 = 0
_n1 = 0
for _sigla, _nome, _tipo, _matriz, _flp, _fmt in _P:
    _pid = slug(_nome)
    PARCEIROS.append({"id": _pid, "sigla": _sigla, "nome": _nome, "tipo": _tipo, "matriz": _matriz})
    for _comp, _f in (("LP", _flp), ("MT", _fmt)):
        _rid = f"{_pid}-{_comp.lower()}"
        passos = {k: "ok" for k, _, _ in PASSOS}
        pend = []
        if _f == 1:
            for k in ("base", "templates", "infograficos", "capa", "textos", "conferir"):
                passos[k] = "pend"
            if _matriz is None:
                pend = ["Sem matriz"]
            else:
                pend = [["Cortes de 3EM %s faltando" % _comp, "4 de 8 variáveis vazias"][_n1 % 2]]
            _n1 += 1
        elif _f == 2:
            for k in _COMBOS[_n2 % len(_COMBOS)]:
                passos[k] = "pend"
                pend.append(_PEND_TXT[k])
            passos["conferir"] = "pend"
            _n2 += 1
        elif _f == 3:
            passos["conferir"] = "pend"
        REVISTAS.append(
            {
                "id": _rid,
                "parceiro": _pid,
                "sigla": _sigla,
                "nome_parceiro": _nome,
                "comp": _comp,
                "fase": _f,
                "passos": passos,
                "pend": pend,
                "editando": EDITANDO.get(_rid),
                "validada": VALIDADAS.get(_rid),
                "matriz": _matriz,
            }
        )
POR_ID = {r["id"]: r for r in REVISTAS}
PARCEIRO_POR_ID = {p["id"]: p for p in PARCEIROS}


def revistas_na_fase(n):
    return [r for r in REVISTAS if r["fase"] == n]


def contagem_fases():
    return {n: len(revistas_na_fase(n)) for n, *_ in FASES}


# ── Cortes fictícios por parceiro × etapa × componente ────────────────────
def cortes(parceiro_id, etapa, comp):
    """Devolve 'a, b, c' (3 cortes) ou '' para célula sem dado."""
    i = [p["id"] for p in PARCEIROS].index(parceiro_id)
    if (i * 3 + len(etapa) + (comp == "MT")) % 17 == 0:
        return ""
    base = {"2EF": 350, "5EF": 150, "9EF": 200, "3EM": 225}[etapa]
    passo = {"2EF": 50, "5EF": 25, "9EF": 25, "3EM": 25}[etapa]
    off = ((i * 7 + (comp == "MT") * 3) % 4) * (passo // 5 or 1)
    a = base + off
    return f"{a}, {a + passo}, {a + 2 * passo + (passo // 2 if comp == 'MT' else 0)}"


# ── Variáveis (24 no sistema real; a demo mostra 8 de 5 grupos) ───────────
VARIAVEIS = [
    ("colecao", "ISSN", "Coleção", "{{issn}}", "Capa e ficha técnica"),
    ("pat_m", "Adjetivo (masc. sing.)", "Adjetivo pátrio", "{{adj_masc_sing}}", "Introdução F1"),
    ("pat_f", "Adjetivo (fem. sing.)", "Adjetivo pátrio", "{{adj_fem_sing}}", "Introdução F1"),
    ("programa", "Nome do programa", "Programa", "{{programa}}", "Introdução F1 e Abertura F2"),
    ("secretaria", "Secretaria", "Regional e secretaria", "{{secretaria}}", "Fechamento F1"),
    ("regional", "Regional", "Regional e secretaria", "{{regional}}", "Passo 2 do F2"),
    ("pd01", "Nome do Padrão 01", "Padrões de desempenho", "{{pd01}}", "Escala do F1"),
    ("pd02", "Nome do Padrão 02", "Padrões de desempenho", "{{pd02}}", "Escala do F1"),
]


def variavel(parceiro_id, chave):
    i = [p["id"] for p in PARCEIROS].index(parceiro_id)
    p = PARCEIRO_POR_ID[parceiro_id]
    if (i + len(chave)) % 6 == 0:
        return ""
    valores = {
        "colecao": f"2596-{1000 + i * 13}",
        "pat_m": p["nome"].split()[0].lower() + "ense",
        "pat_f": p["nome"].split()[0].lower() + "ense",
        "programa": f"Avalia {p['nome']}",
        "secretaria": f"Secretaria de Educação de {p['nome']}",
        "regional": f"Regional {i % 5 + 1}",
        "pd01": "Baixo",
        "pd02": "Básico",
    }
    return valores[chave]


# ── Biblioteca ────────────────────────────────────────────────────────────
MATRIZES = [
    {"id": "comunitaria-2026", "nome": "Comunitária 2026", "origem": None, "mecs": 8, "descritores": 142,
     "parceiros": 12, "revistas": 24, "atualizada": "03/11 14:20"},
    {"id": "vale-verde-2026", "nome": "Vale Verde 2026", "origem": "Comunitária 2026", "mecs": 8, "descritores": 146,
     "parceiros": 1, "revistas": 2, "atualizada": "07/11 10:05"},
    {"id": "serra-alta-2026", "nome": "Serra Alta 2026", "origem": "Comunitária 2026", "mecs": 8, "descritores": 139,
     "parceiros": 1, "revistas": 2, "atualizada": "05/11 16:31"},
]

DESCRITORES_5EF_LP = [
    ("D01", "Localizar informações explícitas em textos de diferentes gêneros.", 100, 175),
    ("D02", "Estabelecer relações entre partes de um texto, identificando repetições ou substituições.", 150, 225),
    ("D03", "Inferir o sentido de palavra ou expressão pelo contexto.", 175, 250),
    ("D04", "Inferir uma informação implícita em um texto.", 200, 275),
    ("D05", "Interpretar texto com auxílio de material gráfico diverso.", 225, 300),
    ("D06", "Identificar o tema de um texto.", 175, 250),
    ("D07", "Distinguir um fato da opinião relativa a esse fato.", 275, 350),
    ("D08", "Reconhecer o efeito de sentido decorrente da pontuação e de outras notações.", 300, 400),
]
CORTES_5EF_LP = (150, 200, 250)
ESCALA_5EF = 500

TEMPLATES = [
    {"id": "lp-f1", "nome": "LP · F1 · Padrão 2026", "comp": "LP", "fasc": "F1", "versao": 4, "usado": 22, "copias": 3, "atualizado": "03/11 11:02"},
    {"id": "mt-f1", "nome": "MT · F1 · Padrão 2026", "comp": "MT", "fasc": "F1", "versao": 3, "usado": 22, "copias": 1, "atualizado": "03/11 11:20"},
    {"id": "lp-f2", "nome": "LP · F2 · Padrão 2026", "comp": "LP", "fasc": "F2", "versao": 2, "usado": 20, "copias": 0, "atualizado": "09/11 15:44"},
    {"id": "mt-f2", "nome": "MT · F2 · Padrão 2026", "comp": "MT", "fasc": "F2", "versao": 2, "usado": 20, "copias": 2, "atualizado": "09/11 16:01"},
    {"id": "lp-f1-municipio", "nome": "LP · F1 · Município", "comp": "LP", "fasc": "F1", "versao": 2, "usado": 10, "copias": 0, "atualizado": "28/10 09:15"},
    {"id": "mt-f1-municipio", "nome": "MT · F1 · Município", "comp": "MT", "fasc": "F1", "versao": 1, "usado": 10, "copias": 0, "atualizado": "28/10 09:40"},
]

SECOES_F1 = [
    ("introducao", "Introdução", "Resultados de {{ano}} em {{nome_parceiro}}",
     "Esta revista apresenta os resultados do {{programa}} para a rede {{adj_fem_sing}}. Cada escala mostra o que os estudantes "
     "são capazes de fazer em cada padrão de desempenho."),
    ("fechamento", "Fechamento", "Próximos passos",
     "A {{secretaria}} e as equipes pedagógicas podem usar estas páginas para planejar a recomposição das aprendizagens."),
]
SECOES_F2 = [
    ("abertura", "Abertura", "Avaliação e Currículo", "Explore o infográfico e descubra como as habilidades se organizam por etapa."),
    ("passo1", "Passo 1", "A habilidade em foco", "Cada descritor ancora uma habilidade na escala de proficiência."),
    ("passo2", "Passo 2", "Referencial por etapa", "Veja como a habilidade evolui da {{regional}} ao 3º ano do Ensino Médio."),
    ("passo3", "Passo 3", "Progressão", "A progressão mostra o que muda entre uma etapa e a seguinte."),
    ("dlg-descritor", "Diálogo do descritor", "Sobre o descritor", "O descritor descreve uma habilidade avaliada pelo teste."),
]

ATIVIDADES = [
    ("Ana Souza", "validou Serra Alta · LP", "há 2 h"),
    ("Elisa Prado", "editou os textos de Vale Verde · LP", "há 3 h"),
    ("Bruno Lima", "enviou a capa de Costa Dourada · MT", "há 5 h"),
    ("Carla Mendes", "marcou Planalto Central · LP como impressa", "ontem"),
]


def indice_busca():
    """Entradas da busca global (Ctrl+K): [rótulo, tipo, href]."""
    itens = []
    for r in REVISTAS:
        itens.append([f"{r['nome_parceiro']} · {r['comp']}", "Revista", f"revista-{r['id']}.html"])
    for p in PARCEIROS:
        itens.append([f"{p['nome']} ({p['sigla']})", "Parceiro", f"parceiro-{p['id']}.html"])
    for m in MATRIZES:
        itens.append([m["nome"], "Matriz", "matriz-" + m["id"] + ".html"])
    for t in TEMPLATES:
        itens.append([t["nome"], "Template", "template-" + ("lp-f1" if t["fasc"] == "F1" else "lp-f2") + ".html"])
    for cod, desc, *_ in DESCRITORES_5EF_LP:
        itens.append([f"{cod} · {desc[:48]}", "Descritor", "matriz-etapa.html"])
    return itens
