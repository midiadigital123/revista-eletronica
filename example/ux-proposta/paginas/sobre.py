"""Sobre esta proposta: a análise das telas atuais e o que a demo muda (demo de UI/UX, tudo fictício)."""
import dados as D
from paginas import shell as S

CSS = """
/* ── Sobre esta proposta ───────────────────────────────────────────── */
.so-lay{display:grid;grid-template-columns:190px minmax(0,1fr);gap:40px;align-items:start}
.so-toc{position:sticky;top:76px;display:grid;gap:2px;font-size:13px}
.so-toc p{font-weight:650;margin-bottom:6px}
.so-toc a{color:var(--txt-2);text-decoration:none;padding:5px 10px;border-radius:7px}
.so-toc a:hover{background:var(--tela-2);color:var(--txt)}
.so-doc{display:grid;gap:48px;min-width:0}
.so-sec{display:grid;gap:14px;scroll-margin-top:72px;min-width:0}
.so-sec > h2{font-size:21px;letter-spacing:-.02em;line-height:1.25}
.so-sec h3{font-size:15px}
.so-txt{max-width:72ch;font-size:15px;line-height:1.6}
.so-txt + .so-txt{margin-top:-4px}
.so-tese{font-size:16px;line-height:1.6;max-width:72ch}
.so-regua{display:flex;gap:3px;max-width:72ch}
.so-regua div{flex:1;min-width:0;padding:10px 10px 9px;border-radius:6px;background:var(--c);color:var(--ct);display:grid;gap:1px}
.so-regua b{font-size:14px;font-weight:650}
.so-regua span{font-size:12px;opacity:.85}
.so-regua div[data-f="1"]{--c:var(--r1);--ct:var(--r1t)}.so-regua div[data-f="2"]{--c:var(--r2);--ct:var(--r2t)}
.so-regua div[data-f="3"]{--c:var(--r3);--ct:var(--r3t)}.so-regua div[data-f="4"]{--c:var(--r4);--ct:var(--r4t)}
.so-regua div[data-f="5"]{--c:var(--r5);--ct:var(--r5t)}
.so-tab td{white-space:normal;vertical-align:top;height:auto;padding:14px 14px;line-height:1.55;font-size:13.5px}
.so-tab th{position:static}
.so-n td:first-child{color:var(--txt-2);font-weight:650;width:44px}
.so-tab code{font:inherit;font-size:12.5px;background:var(--tela-2);border-radius:4px;padding:1px 5px;white-space:nowrap}
.so-tab b{font-weight:650}
.so-tab .ev{color:var(--txt-2)}
.so-tab .ev code{display:inline-block;margin:0 2px 3px 0}
.so-tab a{font-weight:550}
.so-tab ul{margin:6px 0 0;padding-left:18px}
.so-par{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px;align-items:stretch}
.so-par > div{border-radius:var(--raio-g);padding:18px;display:grid;gap:14px;align-content:start}
.so-antes{background:var(--papel);border:1px solid var(--fio)}
.so-depois{background:var(--tinta);color:var(--tinta-txt)}
.so-par h3{font-size:15px}
.so-depois h3{color:#fff}
.so-topo{display:flex;gap:2px;flex-wrap:wrap;background:var(--tela-2);border-radius:8px;padding:4px}
.so-topo span{padding:6px 9px;border-radius:6px;font-weight:550;color:var(--txt-2)}
.so-topo span.on{background:var(--papel);color:var(--txt);box-shadow:var(--sombra-p)}
.so-nota{display:grid;gap:8px;font-size:13.5px;color:var(--txt-2);line-height:1.5}
.so-nota b{color:var(--txt);font-weight:600}
.so-lat{display:grid;gap:2px}
.so-lat > a{display:flex;align-items:center;gap:10px;padding:7px 10px;border-radius:8px;color:inherit;text-decoration:none;font-weight:550}
.so-lat > a:hover{background:var(--tinta-2)}
.so-lat > p{margin:10px 10px 2px;font-size:12px;color:var(--tinta-mudo);font-weight:600}
.so-lat .sub{display:flex;gap:6px;flex-wrap:wrap;padding:0 10px 4px 38px;font-size:13px;color:var(--tinta-mudo)}
.so-lat .sub a{color:var(--tinta-txt);text-decoration:none;background:var(--tinta-2);border-radius:6px;padding:2px 8px}
.so-lat .sub a:hover{background:var(--tinta-3)}
.so-dec{list-style:none;margin:0;padding:0;display:grid;gap:0;max-width:78ch;border-top:1px solid var(--fio)}
.so-dec li{display:grid;gap:2px;padding:13px 0;border-bottom:1px solid var(--fio);line-height:1.55}
.so-dec b{font-weight:650;font-size:15px}
.so-dec span{color:var(--txt-2);font-size:14px}
.so-pas{list-style:none;margin:0;padding:0;display:grid;gap:10px;counter-reset:p;max-width:78ch}
.so-pas li{counter-increment:p;display:flex;gap:14px;align-items:flex-start;line-height:1.55}
.so-pas li::before{content:counter(p);flex:none;display:grid;place-items:center;width:26px;height:26px;border-radius:50%;background:var(--cobalto-fundo);color:var(--cobalto-2);font-weight:650;font-size:13px}
.so-pas b{font-weight:650}
.so-lim{margin:0;padding-left:20px;display:grid;gap:8px;max-width:72ch;line-height:1.6}
@media (max-width: 1100px){
  .so-lay{grid-template-columns:1fr;gap:20px}
  .so-toc{position:static;display:flex;flex-wrap:wrap;gap:6px}
  .so-toc p{display:none}
  .so-toc a{border:1px solid var(--fio);background:var(--papel);border-radius:99px;padding:4px 12px}
}
@media (max-width: 760px){
  .so-par{grid-template-columns:1fr}
  .so-regua b{font-size:12px}.so-regua span{display:none}
  .so-sec > h2{font-size:19px}
  .so-n td:first-child{width:auto}
}
"""

JS = ""


CURTO = {1: "Matriz, cortes, dados", 2: "Templates e textos", 3: "Pronta para validar", 4: "Falta o impresso", 5: "Em dia"}


def _c(t):
    return f"<code>{t}</code>"


ACHADOS = [
    (
        "O menu é por tipo de objeto, o trabalho é uma esteira",
        "O menu organiza por Painel, Projetos, Matrizes, Templates e Impresso, mas o trabalho segue ano → cortes → matriz → template → variáveis → revista → validar → impresso. Nada diz em que etapa você está.",
        [_c("ui/base.html:33-42"), _c("docs/telas/telas-b.md") + " §1"],
        'Barra lateral que segue a esteira e a tela <a href="index.html">Hoje</a>, que diz o próximo clique.',
    ),
    (
        "A mesma revista tem 4 portas",
        "Linha do Painel, linha da Lista de Projetos, aba Revistas do Projeto e a ficha. Painel e Lista mostram as mesmas revistas, agrupadas igual, com colunas diferentes.",
        [_c("painel_corpo.html"), _c("projeto/lista.html"), _c("ui_projeto.py:102")],
        'Uma só tela, <a href="revistas.html">Revistas</a>, com a esteira e a tabela.',
    ),
    (
        "Três vocabulários para o mesmo estado",
        "“Completa” no Painel; “Em preparo / Pronta / Validada / Impressa” na Lista; “N de 6 prontos” na Revista.",
        [_c("painel.py:107"), _c("ui_projeto.py:102"), _c("revista_situacao.html")],
        'Cinco fases e a régua em todo lugar, como na <a href="revistas.html#esteira">esteira de Revistas</a>.',
    ),
    (
        "O hub Projetos mistura grades do ano com cadastro",
        "Lista, Cortes e Variáveis são três grades do ano; “Adicionar parceiro” só existe na aba Cortes; Cortes e Variáveis reaparecem dentro do Projeto.",
        [_c("cortes.html:20-34"), _c("projeto.html:57,167")],
        '<a href="parceiros.html">Parceiros</a> reúne cadastro e grades; o <a href="parceiro-vale-verde.html">Parceiro</a> vira um dossiê.',
    ),
    (
        "A configuração do ano está escondida",
        "Etapas, componentes, Padrões e Abrir ano só se acham num popover do seletor de ano. As colunas “Abrir” e “Cadastros” têm rótulo enganoso.",
        [_c("_componentes/anos.html:11-12"), _c("anos/anos.html:20-31")],
        'Tela própria: <a href="ano.html">Configurar o ano</a>.',
    ),
    (
        "A ficha da revista é longa e se contradiz",
        "Passos numerados de 1 a 4, mas a checklist da Situação tem 6 itens. Quatro botões de estilos diferentes no cabeçalho, zip sempre habilitado e links duplicados.",
        [_c("revista.html:25,59"), _c("ui_revista.py:135"), _c("revista_situacao.html:47")],
        'Stepper de 6 passos e uma ação primária. Exemplo: <a href="revista-vale-verde-lp.html">Vale Verde · LP</a>.',
    ),
    (
        "Validar está fora do menu e é pobre",
        "Sem link para a revista nem para o preview. O diff é um json.dumps comparado por difflib. Há dois caminhos de validar que não se referenciam.",
        [_c("ui_validar.py:51"), _c("painel.py:157"), _c("validar_cartao.html:33-34")],
        '<a href="entrega-validar.html">Entrega › Validar</a>: fila, conferência, mudanças em linguagem humana e “Validar e ir para a próxima”.',
    ),
    (
        "Profundidade e coisas escondidas",
        "Matriz → Etapa × CC → Descritor são 3 níveis. O “Intervalo mínimo” mora num popover. O histórico de versões de template é prometido e não existe. O impacto do template ocupa página inteira; nas outras telas é modal.",
        [_c("matriz/mec.html:20-33"), _c("templates/lista.html:9"), _c("templates/impacto.html")],
        '<a href="matriz-etapa.html">Matriz por etapa</a> numa tela e <a href="template-lp-f1.html">Template com versões</a>, com impacto sempre em modal.',
    ),
    (
        "O shell é pobre",
        "Sem busca global, sem trilha padronizada, ano sem rótulo, cabeçalho que mistura marca, ano, menu, usuário, Admin e Usuários. Sem menu no celular. Login e senha repetem o head.",
        [_c("base.html"), _c("ui.css:86-91,309"), _c("contexto.py")],
        'Barra lateral, <b>Ctrl K</b>, trilha em toda página e gaveta no celular (veja <a href="index.html">Hoje</a>).',
    ),
    (
        "A ordem das abas do Projeto não segue o fluxo",
        "Revistas, o objeto de trabalho, vem por último. A aba Matriz tem um select só e repete passos de outra aba.",
        [_c("ui_projeto.py:47"), _c("projeto.html:140")],
        'O <a href="parceiro-vale-verde.html">Parceiro</a> abre no Resumo, com as revistas à vista.',
    ),
]


def _tabela_achados():
    linhas = ""
    for n, (titulo, texto, evid, resolve) in enumerate(ACHADOS, 1):
        linhas += (
            f"<tr><td>{n}</td><td><b>{titulo}.</b> {texto}</td>"
            f'<td class="ev">{" ".join(evid)}</td><td>{resolve}</td></tr>'
        )
    return (
        '<div class="tab-caixa"><table class="tabela so-tab so-n"><thead><tr><th>#</th><th>Achado</th>'
        "<th>Evidência no código</th><th>Como a proposta resolve</th></tr></thead>"
        f"<tbody>{linhas}</tbody></table></div>"
    )


MUDANCAS = [
    ("Painel + Projetos › Lista + Projeto › Revistas", ("Revistas", "revistas.html"), "Uma tela, um vocabulário: as 5 fases."),
    ("Revista (ficha longa)", ("Revista com stepper", "revista-vale-verde-lp.html"), "6 passos, um por vez, e uma ação primária."),
    ("Projetos › Cortes e Variáveis", ("Parceiros", "parceiros.html"), "As grades do ano ficam junto do cadastro."),
    ("Projeto (5 abas)", ("Parceiro", "parceiro-vale-verde.html"), "Resumo primeiro; Cortes, Matriz e Variáveis depois."),
    ("Validar (só por URL)", ("Entrega › Validar", "entrega-validar.html"), "No menu, com link para a revista e o preview."),
    ("Impresso, zip e planilhas", ("Entrega › Impresso e Pacotes", "entrega-impresso.html"), "Zip só habilitado para revista validada."),
    ("Matrizes", ("Matrizes", "matrizes.html"), "Menos níveis até chegar ao descritor."),
    ("Templates", ("Templates com versões", "templates.html"), "Histórico de versões e impacto em modal."),
    ("Seletor de ano › Configurar e Abrir", ("Configurar o ano", "ano.html"), "Tela própria, achável pela barra."),
    ("Usuários, Entrar, Senha, Excluir", ("Mesmas funções, refeitas", "usuarios.html"), "Explicam o que fazer quando algo impede a ação."),
]

DECISOES = [
    ("Esteira de 5 fases como vocabulário único.", "Preparar, Montar, Conferir, Validada e Impressa substituem os três vocabulários de hoje, em todas as telas."),
    ("A revista é o objeto central.", "Toda tela leva a ela; o parceiro e a matriz são contexto."),
    ("Um passo por vez na ficha da revista.", "O stepper de 6 passos troca a página longa; o passo seguinte é sempre óbvio."),
    ("Impacto mostrado antes do clique.", "Quem vai perder o Validado aparece antes de gravar, sempre em modal."),
    ("Uma ação primária por tela.", "O resto é secundário; botão desabilitado diz o motivo."),
    ("Cores dos Padrões só como dado.", "Aparecem nas escalas e nos cortes, nunca como decoração. A interface usa tinta e um acento cobalto."),
    ("O perfil muda o que aparece.", "Na demo, o seletor “Ver como” no rodapé da barra mostra Pedagógica, Mídias Digitais, Impresso e Admin."),
]

LIMITES = [
    "Os dados são inventados: parceiros, revistas, cortes, textos e pessoas.",
    "A demo não monta a revista; o preview e o zip não existem.",
    "Nada grava. Salvamento automático, toasts e validações são simulados no navegador.",
    "O celular recebe o essencial: barra em gaveta, tabelas roláveis e telas empilhadas.",
]

FASES_IMPL = [
    ("Casca e navegação", "Barra lateral, trilha, busca Ctrl K, seletor de ano e perfil, mais entrar e senha, sem mexer nas telas de dentro."),
    ("Revistas e Revista", "A tela única de revistas com a esteira de 5 fases e a ficha com stepper de 6 passos."),
    ("Parceiros", "Parceiros e o dossiê do Parceiro, com cortes e variáveis, e a tela Configurar o ano."),
    ("Entrega", "Validar, Impresso e Pacotes juntos, com o diff em linguagem humana e o zip só para o validado."),
    ("Biblioteca", "Matrizes e Templates com versões, e o impacto sempre em modal."),
]


def _antes_depois():
    antes = (
        '<div class="so-antes"><h3>Antes</h3>'
        '<div class="so-topo" aria-label="Menu do topo atual"><span>Painel</span><span class="on">Projetos</span><span>Matrizes</span><span>Templates</span><span>Impresso</span></div>'
        '<div class="so-topo" aria-label="Dentro de Projetos"><span>Lista</span><span>Cortes</span><span>Variáveis</span></div>'
        '<div class="so-nota"><p><b>Ano e configuração:</b> num popover do seletor de ano.</p>'
        "<p><b>Validar:</b> só por URL, fora do menu.</p>"
        "<p><b>Usuários e Admin:</b> misturados no cabeçalho com a marca e o ano.</p></div></div>"
    )

    def a(href, ic, txt, n=""):
        return f'<a href="{href}">{S.ic(ic)}<span>{txt}</span></a>'

    depois = (
        '<div class="so-depois"><h3>Depois</h3><nav class="so-lat" aria-label="Barra lateral proposta">'
        + a("index.html", "lista", "Hoje")
        + a("revistas.html", "camadas", "Revistas")
        + a("parceiros.html", "pessoas", "Parceiros")
        + a("entrega-validar.html", "pacote", "Entrega")
        + '<div class="sub"><a href="entrega-validar.html">Validar</a><a href="entrega-impresso.html">Impresso</a><a href="entrega-pacotes.html">Pacotes</a></div>'
        + "<p>Biblioteca</p>"
        + a("matrizes.html", "livro", "Matrizes")
        + a("templates.html", "arquivo", "Templates")
        + "<p>Sistema</p>"
        + a("ano.html", "ajustes", "Configurar o ano")
        + a("usuarios.html", "usuario", "Usuários")
        + "</nav></div>"
    )
    return f'<div class="so-par">{antes}{depois}</div>'


def _tabela_mudancas():
    linhas = "".join(
        f'<tr><td>{hoje}</td><td><a href="{href}">{prop}</a></td><td>{ganho}</td></tr>' for hoje, (prop, href), ganho in MUDANCAS
    )
    return (
        '<div class="tab-caixa"><table class="tabela so-tab"><thead><tr><th>Hoje</th><th>Proposta</th><th>O que muda</th></tr></thead>'
        f"<tbody>{linhas}</tbody></table></div>"
    )


def corpo():
    toc = [
        ("diagnostico", "Diagnóstico"),
        ("navegacao", "Navegação"),
        ("decisoes", "Decisões de design"),
        ("explorar", "Como explorar"),
        ("limites", "Limites"),
        ("aprovacao", "Se você aprovar"),
    ]
    indice = '<nav class="so-toc" aria-label="Nesta página"><p>Nesta página</p>' + "".join(f'<a href="#{i}">{t}</a>' for i, t in toc) + "</nav>"
    regua = (
        '<div class="so-regua" role="img" aria-label="As 5 fases: Preparar, Montar, Conferir, Validada, Impressa">'
        + "".join(f'<div data-f="{n}"><b>{nome}</b><span>{CURTO[n]}</span></div>' for n, _, nome, _d in D.FASES)
        + "</div>"
    )
    explorar = [
        ('Troque o perfil em <b>Ver como</b>, no rodapé da barra lateral, e veja o que cada um enxerga.', None),
        ("Aperte <b>Ctrl K</b> (ou <b>/</b>) e digite “vale” para buscar parceiro, revista, matriz ou descritor.", None),
        ('Abra uma revista com pendência: <a href="revista-costa-dourada-lp.html">Costa Dourada · LP</a>.', None),
        ('Vá a <a href="entrega-validar.html">Entrega › Validar</a> e use “Validar e ir para a próxima”.', None),
        ('Veja os estados reutilizáveis em <a href="estados.html">Estados</a>: vazio, só leitura, bloqueio, impacto e conflito.', None),
    ]
    sec = lambda i, t, c: f'<section class="so-sec" id="{i}"><h2>{t}</h2>{c}</section>'
    doc = (
        '<div class="so-doc">'
        + '<section class="so-sec"><p class="so-tese">A revista anda numa esteira de cinco fases, e o sistema inteiro passa a falar essa língua: o menu, as listas, a ficha e a entrega mostram a mesma régua e dizem qual é o próximo clique.</p>'
        + regua
        + "</section>"
        + sec(
            "diagnostico",
            "O diagnóstico em 10 achados",
            '<p class="so-txt">Análise das telas atuais, de ponta a ponta. A coluna do meio aponta o arquivo onde cada problema nasce; a da direita leva à página da demo que o resolve.</p>'
            + _tabela_achados(),
        )
        + sec(
            "navegacao",
            "Antes e depois da navegação",
            '<p class="so-txt">Hoje o menu agrupa por tipo de objeto. Na proposta, a barra lateral segue a ordem em que o trabalho acontece.</p>'
            + _antes_depois()
            + "<h3>Hoje → Proposta</h3>"
            + _tabela_mudancas(),
        )
        + sec("decisoes", "Decisões de design", '<ul class="so-dec">' + "".join(f"<li><b>{t}</b><span>{d}</span></li>" for t, d in DECISOES) + "</ul>")
        + sec("explorar", "Como explorar a demo", '<ol class="so-pas">' + "".join(f"<li><span>{t}</span></li>" for t, _ in explorar) + "</ol>")
        + sec("limites", "Limites", '<ul class="so-lim">' + "".join(f"<li>{t}</li>" for t in LIMITES) + "</ul>")
        + sec(
            "aprovacao",
            "Se você aprovar",
            '<p class="so-txt">Cinco rodadas de implementação no Django, nesta ordem. Cada uma entrega algo usável e não depende da seguinte.</p>'
            '<ol class="so-pas">' + "".join(f"<li><span><b>{t}.</b> {d}</span></li>" for t, d in FASES_IMPL) + "</ol>",
        )
        + "</div>"
    )
    return (
        S.cab("Sobre esta proposta", "A análise das telas atuais e o que esta demo muda. Tudo aqui é fictício; nada do sistema real foi alterado.")
        + f'<div class="so-lay">{indice}{doc}</div>'
    )


def paginas():
    return [S.Pagina("sobre.html", "Sobre esta proposta", "sobre", corpo(), trilha=[("Sobre esta proposta", None)])]
