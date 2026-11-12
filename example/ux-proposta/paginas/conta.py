"""Conta e cadastros sensíveis: entrar, senha, usuários, exclusão de parceiro e galeria de estados (demo, dados fictícios)."""
import dados as D
from paginas import shell as S

esc = S.esc

CSS = """
/* ── Conta: entrar, senha, usuários, exclusão, estados ─────────────── */
.pilha > *{min-width:0}
.entrar-marca h1{font-size:40px;max-width:16ch}
.co-wm{display:flex;align-items:center;gap:10px;color:#fff;font-weight:650;font-size:16px;letter-spacing:-.01em}
.co-txt{display:grid;gap:16px}
.co-bloco{width:100%;max-width:340px;display:grid;gap:16px}
.co-bloco h2{font-size:22px;letter-spacing:-.02em}
.co-bloco .btn{height:40px;width:100%}
.co-ajuda{font-size:13px;color:var(--txt-2);line-height:1.5}
.co-ajuda b{color:var(--txt)}
.co-erro{display:flex;gap:8px;align-items:flex-start;color:var(--erro);background:var(--erro-fundo);border-radius:8px;padding:9px 11px;font-size:13px}
.co-erro .ic{margin-top:1px}
.input[aria-invalid="true"]{border-color:var(--erro);box-shadow:0 0 0 3px var(--erro-fundo)}
.co-regras{background:var(--tela);border-radius:10px;padding:10px 12px}
.co-regras p{font-weight:600;font-size:13px;margin-bottom:2px}
.co-regras li{padding:5px 0;font-size:13px;color:var(--txt-2)}
.co-regras li[data-ok="true"]{color:var(--txt)}
.co-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.co-selo{display:grid;place-items:center;width:44px;height:44px;border-radius:50%}
.co-selo .ic{width:24px;height:24px;vertical-align:0}
.co-selo-ok{background:var(--ok-fundo);color:var(--ok)}
.co-selo-alerta{background:var(--alerta-fundo);color:var(--alerta)}
.co-pessoa{display:flex;align-items:center;gap:10px}
.co-pessoa > div{display:grid;line-height:1.3}
.co-pessoa b{font-weight:600}
.co-pessoa .mudo{font-size:12px}
.co-sel{width:168px;height:30px;font-size:13px}
.co-filtros{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:12px}
.co-filtros .input{width:260px}
.co-filtros .select{width:190px}
.co-filtros .mudo{margin-left:auto}
.co-pag{max-width:700px;display:grid;gap:16px}
.co-opcoes{display:grid;border:1px solid var(--fio-2);border-radius:var(--raio);overflow:hidden}
.co-opcoes label{display:flex;gap:12px;align-items:flex-start;padding:10px 12px;border-bottom:1px solid var(--fio);cursor:pointer}
.co-opcoes label:last-child{border-bottom:0}
.co-opcoes label:hover{background:var(--tela)}
.co-opcoes label:has(input:checked){background:var(--cobalto-fundo)}
.co-opcoes input{margin-top:3px}
.co-opcoes span{display:grid;gap:1px}
.co-opcoes small{color:var(--txt-2);font-size:13px}
fieldset.campo{border:0;padding:0;margin:0;min-width:0}
fieldset.campo legend{padding:0;margin-bottom:6px}
.co-check{display:flex;gap:10px;align-items:flex-start;font-size:13px;cursor:pointer}
.co-check input{margin-top:2px}
.co-rodape{display:flex;gap:8px;justify-content:flex-end;padding-top:14px;border-top:1px solid var(--fio)}
.co-copia{display:flex;gap:8px}
.co-copia .input{flex:1;min-width:0}
.co-sub{display:grid;gap:6px}
.co-acao-topo{padding:18px 20px;display:grid;gap:12px;justify-items:start}
.co-acao-topo p{max-width:68ch;color:var(--txt-2)}
.co-conf{display:grid;gap:12px;max-width:420px}
.co-conf .linha{gap:8px}
.es-indice{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px}
.es-indice a{display:inline-flex;align-items:center;height:30px;padding:0 12px;border-radius:99px;background:var(--papel);border:1px solid var(--fio);color:var(--txt);text-decoration:none;font-weight:550;font-size:13px}
.es-indice a:hover{border-color:var(--cobalto-fio);color:var(--cobalto)}
.es-grade{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;align-items:start}
.es-sec{display:grid;gap:12px;align-content:start}
.es-sec h2{font-size:16px}
.es-sec > p.quando{color:var(--txt-2);max-width:60ch}
.es-sec .es-demo{display:grid;gap:10px}
.es-larga{grid-column:1 / -1}
@media (max-width: 960px){
  .es-grade{grid-template-columns:1fr}
  .co-filtros .input,.co-filtros .select{width:100%}
  .co-filtros .mudo{margin-left:0}
}
"""

JS = """
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const norm = (s) => (s || "").normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").toLowerCase().trim();

  /* Entrar: mostra o erro junto do campo (hash #erro ou envio incompleto) */
  const fe = $("form[data-entrar]");
  if (fe) {
    const erro = $("#erro"), campos = $$("input", fe);
    const mostra = (on) => { erro.hidden = !on; campos.forEach((c) => c.setAttribute("aria-invalid", on ? "true" : "false")); };
    mostra(location.hash === "#erro");
    window.addEventListener("hashchange", () => mostra(location.hash === "#erro"));
    campos.forEach((c) => c.addEventListener("input", () => mostra(false)));
    fe.addEventListener("submit", (e) => {
      e.preventDefault();
      const [u, s] = campos;
      if (!u.value.trim() || !s.value || s.value === "errada") { mostra(true); (u.value.trim() ? s : u).focus(); return; }
      location.href = fe.dataset.ir;
    });
  }

  /* Definir senha: regras sempre visíveis, marcam ao digitar */
  const fs = $("form[data-senha]");
  if (fs) {
    const [a, b] = $$("input[type=password]", fs), botao = $("[data-definir]", fs), usuario = $("input[name=usuario]", fs).value;
    const regras = {
      min: (v) => v.length >= 10,
      numeros: (v) => v.length > 0 && !/^\\d+$/.test(v),
      usuario: (v) => v.length > 0 && !norm(v).includes(norm(usuario.split(".")[0])),
      igual: (v, w) => v.length > 0 && v === w,
    };
    const confere = () => {
      let todas = true;
      $$("[data-regra]", fs).forEach((li) => {
        const ok = regras[li.dataset.regra](a.value, b.value);
        li.dataset.ok = String(ok);
        const st = $(".st", li); st.classList.toggle("st-ok", ok); st.classList.toggle("st-na", !ok);
        $("use", st).setAttribute("href", ok ? "#i-ok" : "#i-traco");
        $(".co-sr", li).textContent = ok ? "cumprida" : "pendente";
        if (!ok) todas = false;
      });
      botao.disabled = !todas;
    };
    a.addEventListener("input", confere); b.addEventListener("input", confere);
    fs.addEventListener("submit", (e) => { e.preventDefault(); if (!botao.disabled) location.href = fs.dataset.ir; });
    confere();
  }

  /* Novo usuário: sem senha inicial */
  const ss = $("[data-sem-senha]");
  if (ss) ss.addEventListener("change", () => {
    const c = $("input[name=senha_inicial]"); c.disabled = ss.checked; if (ss.checked) c.value = "";
  });

  /* Usuários: estado vazio da busca (o filtro em si vem do app.js) */
  const tu = $("#tab-usuarios");
  if (tu) {
    const vazio = $("#usuarios-vazio");
    const atualiza = () => setTimeout(() => { const n = $$("tr[data-busca]", tu).filter((r) => !r.hidden).length; vazio.hidden = n > 0; tu.closest(".tab-caixa").hidden = n === 0; }, 0);
    document.addEventListener("input", (e) => { if (e.target.matches('[data-filtro="#tab-usuarios"]')) atualiza(); });
    document.addEventListener("change", (e) => { if (e.target.matches('[data-alvo="#tab-usuarios"]')) atualiza(); });
  }

  /* Excluir: o botão perigo só habilita quando o nome digitado bate */
  const cn = $("[data-confirma-nome]");
  if (cn) {
    const botao = $("[data-excluir]");
    cn.addEventListener("input", () => { botao.disabled = norm(cn.value) !== norm(cn.dataset.confirmaNome); });
    botao.addEventListener("click", () => { if (!botao.disabled) location.href = botao.dataset.excluir; });
  }
})();
"""

EXTRA = {"id": "gabriela", "nome": "Gabriela Torres", "perfil": "ped", "usuario": "gabriela.torres", "acesso": "Nunca acessou", "ativo": True, "rastro": False}

DESC_PERFIL = {
    "ped": "Monta o conteúdo: matriz, cortes, variáveis e textos. Valida as revistas.",
    "mid": "Cuida de capa, imagens e infográficos. Edita, mas não valida.",
    "imp": "Só leitura, mais marcar a revista como impressa e baixar os pacotes.",
    "adm": "Tudo o que os outros fazem, mais usuários, abrir o ano e exclusões.",
}


def _t(msg):
    return f'data-toast="{esc(msg)}"'


# ── Telas sem casca ───────────────────────────────────────────────────────
def _marca():
    return (
        '<section class="entrar-marca"><div class="co-wm">'
        '<span class="regua marca-regua" data-f="5" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></span>Revista Express</div>'
        '<div class="co-txt"><h1>Resultados de avaliação, da matriz ao impresso.</h1>'
        "<p>Monte, confira e entregue as revistas de resultados de cada parceiro, uma fase de cada vez.</p></div>"
        '<div class="regua-grande" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div></section>'
    )


def _solo(arquivo, titulo, bloco):
    corpo = f'<div class="entrar">{_marca()}<section class="entrar-form">{bloco}</section></div>'
    return S.Pagina(arquivo, titulo, "", corpo, solo=True)


def entrar():
    erro = (
        f'<p class="co-erro" id="erro" role="alert" hidden>{S.ic("alerta")}<span>Usuário ou senha incorretos. '
        "Confira e tente de novo, ou peça um link de acesso.</span></p>"
    )
    bloco = (
        '<form class="co-bloco" data-entrar data-ir="index.html" novalidate>'
        '<div><h2>Entrar</h2><p class="mudo">Use o usuário e a senha que você recebeu.</p></div>'
        + S.campo("Usuário", "usuario", attrs='autocomplete="username" autofocus')
        + S.campo("Senha", "senha", tipo="password", attrs='autocomplete="current-password"')
        + erro
        + '<button type="submit" class="btn btn-prim">Entrar</button>'
        '<p class="co-ajuda"><b>Sem acesso?</b> Peça um link de acesso a quem administra os usuários.</p>'
        '<p class="co-ajuda">Na demo: deixe a senha em branco para ver o erro, ou abra <a href="entrar.html#erro">entrar.html#erro</a>.</p>'
        "</form>"
    )
    return _solo("entrar.html", "Entrar", bloco)


def senha():
    regras = [
        ("min", "Pelo menos 10 caracteres"),
        ("numeros", "Não ser só números"),
        ("usuario", "Não conter o seu nome de usuário"),
        ("igual", "As duas senhas iguais"),
    ]
    lis = "".join(
        f'<li data-regra="{k}" data-ok="false"><span class="st st-na" aria-hidden="true">{S.ic("traco")}</span><span class="txt">{t}</span><span class="co-sr">pendente</span></li>'
        for k, t in regras
    )
    bloco = (
        '<form class="co-bloco" data-senha data-ir="senha-pronto.html" novalidate>'
        '<div><h2>Defina sua senha</h2><p class="mudo">Você recebeu um link de acesso. Escolha a senha com que vai entrar.</p></div>'
        + S.campo("Usuário", "usuario", "gabriela.torres", attrs="readonly")
        + S.campo("Nova senha", "nova", tipo="password", attrs='autocomplete="new-password"')
        + S.campo("Repita a senha", "repete", tipo="password", attrs='autocomplete="new-password"')
        + f'<div class="co-regras"><p>Sua senha precisa:</p><ul class="checklist" aria-live="polite">{lis}</ul></div>'
        + '<button type="submit" class="btn btn-prim" data-definir disabled>Definir senha</button></form>'
    )
    return _solo("senha.html", "Definir senha", bloco)


def senha_invalida():
    bloco = (
        '<div class="co-bloco">'
        f'<span class="co-selo co-selo-alerta">{S.ic("relogio")}</span>'
        "<div><h2>Este link expirou ou já foi usado</h2>"
        '<p class="co-ajuda" style="margin-top:8px">Links de acesso valem por 3 dias e funcionam uma única vez. '
        "Peça outro a quem administra os usuários: o perfil Admin, hoje Diego Rocha.</p></div>"
        + S.btn("Voltar para entrar", "entrar.html", tom="prim")
        + "</div>"
    )
    return _solo("senha-invalida.html", "Link expirado", bloco)


def senha_pronto():
    bloco = (
        '<div class="co-bloco">'
        f'<span class="co-selo co-selo-ok">{S.ic("confirmado")}</span>'
        '<div><h2>Senha definida</h2><p class="co-ajuda" style="margin-top:8px">Agora você entra com o usuário <b>gabriela.torres</b> e a senha que acabou de escolher.</p></div>'
        + S.btn("Entrar", "entrar.html", tom="prim")
        + "</div>"
    )
    return _solo("senha-pronto.html", "Senha definida", bloco)


# ── Usuários ──────────────────────────────────────────────────────────────
def _so_admin(corpo):
    return f'<div data-p="ped mid imp">{S.aviso("Só o perfil Admin gerencia usuários. Para pedir uma mudança, fale com Diego Rocha.", "leitura")}</div><div data-p="adm">{corpo}</div>'


def _linha_usuario(u):
    rastro = u.get("rastro", True)
    nome = u["nome"]
    opcoes = "".join(f'<option value="{k}"{" selected" if k == u["perfil"] else ""}>{esc(v)}</option>' for k, v in D.PERFIS.items())
    perfil = (
        f'<span data-p="adm"><select class="select co-sel" data-edita data-autosave aria-label="Perfil de {esc(nome)}">{opcoes}</select></span>'
        f'<span data-p="ped mid imp">{esc(D.PERFIS[u["perfil"]])}</span>'
    )
    situacao = S.tag("Ativo", "ok") if u["ativo"] else S.tag("Desativado")
    itens = [
        S.item_menu("Link de acesso", "usuario-link.html", "link"),
        S.item_menu("Redefinir senha", icone="cadeado", attrs=_t(f"Senha de {nome} redefinida. Ela define a nova no próximo acesso.")),
    ]
    if u["ativo"]:
        itens.append(S.item_menu("Desativar", icone="x", attrs=_t(f"{nome} desativado. Perde o acesso agora; o histórico fica.")))
    else:
        itens.append(S.item_menu("Reativar", icone="ok", attrs=_t(f"{nome} reativado.")))
    itens.append("<hr>")
    if rastro:
        motivo = "Tem histórico no sistema: desative em vez de excluir"
        itens.append(
            f'<button type="button" class="perigo" aria-disabled="true" title="{motivo}">{S.ic("lixeira")}'
            f"<span>Excluir<small>{motivo}</small></span></button>"
        )
    else:
        itens.append(S.item_menu("Excluir", "excluir-livre.html", "lixeira", perigo=True))
    return (
        f'data-busca="{esc(nome)} {esc(u["usuario"])}" data-perfil="{u["perfil"]}"',
        [
            f'<div class="co-pessoa">{S.avatar(u)}<div><b>{esc(nome)}</b><span class="mudo">{esc(u["usuario"])}</span></div></div>',
            perfil,
            situacao,
            esc(u["acesso"]),
            f'<span data-p="adm">{S.menu_ic(itens, "Ações de " + nome)}</span>',
        ],
    )


def usuarios():
    pessoas = [dict(p) for p in D.PESSOAS] + [EXTRA]
    total = len(pessoas)
    filtros = (
        '<div class="co-filtros">'
        '<input class="input" type="search" data-filtro="#tab-usuarios" placeholder="Buscar por nome ou usuário" aria-label="Buscar usuário" autocomplete="off">'
        '<select class="select" data-alvo="#tab-usuarios" data-filtra="perfil" aria-label="Filtrar por perfil"><option value="">Todos os perfis</option>'
        + "".join(f'<option value="{k}">{esc(v)}</option>' for k, v in D.PERFIS.items())
        + f'</select><span class="mudo">Mostrando <span data-contagem="#tab-usuarios">{total}</span> de {total}</span></div>'
    )
    tab = S.tabela(
        ["Pessoa", "Perfil", "Situação", "Último acesso", ('<span data-p="adm">Ações</span>', "acoes")],
        [_linha_usuario(u) for u in pessoas],
        id_="tab-usuarios",
    )
    vazio = '<div id="usuarios-vazio" hidden>' + S.vazio("Nenhum usuário encontrado", "Tente outro nome ou escolha Todos os perfis.") + "</div>"
    acoes = f'<span data-p="adm">{S.btn("Novo usuário", "usuario-novo.html", tom="prim", icone="mais")}</span>'
    corpo = (
        S.cab("Usuários", "Quem acessa o sistema e com qual perfil.", acoes)
        + f'<div class="pilha"><div data-p="ped mid imp">{S.aviso("Só o perfil Admin gerencia usuários. Você vê a lista, mas não altera. Para pedir uma mudança, fale com Diego Rocha.", "leitura")}</div>'
        + f"<div>{filtros}{tab}{vazio}</div></div>"
    )
    return S.Pagina("usuarios.html", "Usuários", "usuarios", corpo, trilha=[("Usuários", None)], status=True)


def usuario_novo():
    perfis = "".join(
        f'<label><input type="radio" name="perfil" value="{k}"{" checked" if k == "ped" else ""}><span><b>{esc(v)}</b><small>{esc(DESC_PERFIL[k])}</small></span></label>'
        for k, v in D.PERFIS.items()
    )
    form = (
        '<form class="card card-p campos" onsubmit="return false">'
        + '<div class="campos-2">'
        + S.campo("Nome completo", "nome", attrs='autocomplete="off"')
        + S.campo("Usuário", "usuario", ajuda="Sem espaços. Exemplo: nome.sobrenome", attrs='autocomplete="off"')
        + "</div>"
        + f'<fieldset class="campo"><legend class="rot">Perfil</legend><div class="co-opcoes" role="radiogroup">{perfis}</div></fieldset>'
        + S.campo("Senha inicial", "senha_inicial", tipo="password", ajuda="Pelo menos 10 caracteres. A pessoa pode trocá-la depois.", attrs='autocomplete="new-password"')
        + '<label class="co-check"><input type="checkbox" data-sem-senha><span><b>Prefere não definir senha?</b> Gere um link de acesso depois.'
        '<br><span class="mudo">O usuário é criado sem senha e entra pelo link, em Usuários › Link de acesso.</span></span></label>'
        + f'<div class="co-rodape">{S.btn("Cancelar", "usuarios.html", tom="fan")}{S.btn("Criar usuário", "usuarios.html", tom="prim")}</div></form>'
    )
    corpo = S.cab("Novo usuário", "Crie o acesso e escolha o que a pessoa pode fazer.") + _so_admin(f'<div class="co-pag">{form}</div>')
    return S.Pagina("usuario-novo.html", "Novo usuário", "usuarios", corpo, trilha=[("Usuários", "usuarios.html"), ("Novo usuário", None)])


def usuario_link():
    url = "https://revista.exemplo.invalid/acesso/k3Fq9vX2mLpT8wZd"
    msg = (
        "Olá, Gabriela! Seu acesso à Revista Express está pronto. Use este link para escolher sua senha: "
        f"{url}\nO link vale por 3 dias e só funciona uma vez. Se ele expirar, peça outro ao Diego."
    )
    corpo_p = (
        '<div class="card card-p campos">'
        '<div class="co-sub"><h2>Link</h2><div class="co-copia">'
        f'<input class="input" type="text" readonly value="{esc(url)}" aria-label="Link de acesso">'
        + S.btn("Copiar link", tom="prim", icone="copiar", attrs=f'data-copiar="{esc(url)}"')
        + "</div>"
        + f'<p class="linha">{S.tag("Vale por 3 dias", "", "relogio")}<span class="mudo">Expira em 15/11 às 10:02 e funciona uma vez.</span></p></div>'
        + '<div class="co-sub"><h2>Mensagem pronta para colar</h2>'
        + f'<label class="campo"><span class="rot co-sr">Mensagem</span><textarea class="textarea" readonly style="min-height:120px">{esc(msg)}</textarea></label>'
        + f'<div>{S.btn("Copiar mensagem", icone="copiar", attrs=f"data-copiar=" + chr(34) + esc(msg) + chr(34))}</div></div>'
        + S.aviso('O link continua disponível aqui: <b>Usuários › Link de acesso</b>. Você pode voltar e copiá-lo de novo até ele vencer.', "info")
        + f'<div class="co-rodape">{S.btn("Gerar novo link", tom="fan", attrs=_t("Novo link gerado. O anterior deixou de valer."))}{S.btn("Voltar para Usuários", "usuarios.html")}</div></div>'
    )
    corpo = S.cab("Link de acesso", "Para <b>Gabriela Torres</b> (gabriela.torres). Ela define a própria senha pelo link.") + _so_admin(f'<div class="co-pag">{corpo_p}</div>')
    return S.Pagina("usuario-link.html", "Link de acesso", "usuarios", corpo, trilha=[("Usuários", "usuarios.html"), ("Link de acesso", None)])


# ── Excluir parceiro ──────────────────────────────────────────────────────
def excluir_em_uso():
    revs = [r for r in D.REVISTAS if r["parceiro"] == "vale-verde"]
    linhas = [
        ["Revistas", f"{len(revs)} (LP e MT)", f'<a href="revistas.html?parceiro=vale-verde#tabela">Ver as revistas</a>'],
        ["Cortes", "8 combinações de etapa e componente", '<a href="parceiro-vale-verde.html#cortes">Ver os cortes</a>'],
        ["Variáveis preenchidas", "19 de 24", '<a href="parceiro-vale-verde.html#variaveis">Ver as variáveis</a>'],
        ["Matriz própria", "Vale Verde 2026, derivada da Comunitária 2026", '<a href="matriz-vale-verde-2026.html">Abrir a matriz</a>'],
        ["Histórico de alterações", "37 registros", '<a href="parceiro-vale-verde.html#resumo">Ver o resumo do parceiro</a>'],
    ]
    corpo = (
        S.cab("Não dá para excluir Vale Verde", "O parceiro tem trabalho registrado e excluir apagaria esse histórico. Desativar resolve sem perder nada.")
        + '<div class="pilha">'
        + '<div class="card co-acao-topo"><h2>Desativar parceiro</h2>'
        "<p>Vale Verde some das listas e do trabalho da temporada 2026, mas nada é apagado: matriz, cortes, variáveis, revistas e histórico continuam guardados. Você reativa quando quiser.</p>"
        + S.btn("Desativar Vale Verde", tom="prim", attrs=_t("Vale Verde desativado. Reative em Parceiros, filtro Desativados.") + " data-edita")
        + "</div>"
        + '<div class="pilha" style="gap:8px"><h2>O que impede a exclusão</h2>'
        + S.tabela(["O quê", "Quantos", "Onde ver"], linhas)
        + '<p class="mudo">Só dá para excluir um parceiro que nada usa, como um cadastro feito por engano.</p></div>'
        + f'<div>{S.btn("Voltar para Vale Verde", "parceiro-vale-verde.html", tom="fan", icone="volta")}</div></div>'
    )
    return S.Pagina(
        "excluir-em-uso.html", "Não dá para excluir Vale Verde", "parceiros", corpo,
        trilha=[("Parceiros", "parceiros.html"), ("Vale Verde", "parceiro-vale-verde.html"), ("Excluir", None)],
    )


def excluir_livre():
    apagar = [
        "O cadastro do parceiro: sigla EX, tipo Município.",
        "As 2 revistas em branco (LP e MT), sem nenhum passo feito.",
        "As 8 linhas de cortes e as 24 variáveis, todas vazias.",
    ]
    lista = '<ul class="checklist">' + "".join(f'<li>{S.st("na", "Será apagado")}<span class="txt">{t}</span></li>' for t in apagar) + "</ul>"
    corpo = (
        S.cab("Excluir o parceiro Exemplo Sem Uso", "Nada usa este parceiro, então ele pode ser excluído de vez.")
        + '<div class="co-pag">'
        + '<div class="card card-p campos">'
        + f"<div><h2>O que será apagado</h2>{lista}</div>"
        + S.aviso("Não dá para desfazer. O registro da exclusão fica no histórico do sistema.", "alerta")
        + '<div class="co-conf">'
        + S.campo("Para confirmar, digite o nome do parceiro: Exemplo Sem Uso", "confirma", attrs='autocomplete="off" data-confirma-nome="Exemplo Sem Uso" data-edita')
        + '<div class="linha">'
        + S.btn("Excluir Exemplo Sem Uso", tom="perigo", icone="lixeira", attrs='data-excluir="parceiros.html" disabled data-edita')
        + S.btn("Voltar sem excluir", "parceiros.html", tom="fan")
        + "</div></div></div></div>"
    )
    return S.Pagina(
        "excluir-livre.html", "Excluir Exemplo Sem Uso", "parceiros", corpo,
        trilha=[("Parceiros", "parceiros.html"), ("Exemplo Sem Uso", None), ("Excluir", None)],
    )


# ── Galeria de estados ────────────────────────────────────────────────────
def estados():
    def sec(id_, titulo, quando, demo, larga=False):
        cls = "card card-p es-sec" + (" es-larga" if larga else "")
        return f'<section class="{cls}" id="{id_}"><h2>{titulo}</h2><p class="quando">{quando}</p><div class="es-demo">{demo}</div></section>'

    indice = [("es-vazio", "Vazio"), ("es-leitura", "Só leitura"), ("es-bloqueio", "Bloqueio"), ("es-impacto", "Impacto"), ("es-nao-salvas", "Não salvas"), ("es-toast", "Aviso passageiro"), ("es-conflito", "Conflito")]
    ind = '<nav class="es-indice" aria-label="Estados">' + "".join(f'<a href="#{i}">{t}</a>' for i, t in indice) + "</nav>"

    vazio = S.vazio("Nenhuma revista em Montar", "Quando uma revista sair de Preparar, ela aparece aqui. Filtre outra fase ou abra um parceiro.", S.btn("Ver todas as revistas", "revistas.html"))
    leitura = (
        S.aviso("Você está no perfil Impresso: vê tudo, mas não altera. Para mudar algo, peça à equipe Pedagógica.", "leitura")
        + '<div class="linha" style="flex-wrap:nowrap"><input class="input" data-edita value="Avalia Vale Verde" aria-label="Nome do programa">'
        + S.btn("Salvar", attrs="data-edita")
        + "</div>"
        + '<p class="mudo">Troque para Impresso em Ver como (rodapé da barra lateral): o campo e o botão acima viram só leitura.</p>'
    )
    bloqueio = (
        S.aviso("<b>Elisa Prado está editando</b> a Introdução de Vale Verde · LP desde 15:32. Você vê o texto, mas só edita quando ela sair. O bloqueio expira depois de 30 s sem atividade.", "alerta", "cadeado")
        + '<label class="campo"><span class="rot">Introdução</span><textarea class="textarea" readonly>Esta revista apresenta os resultados do Avalia Vale Verde para a rede valeverdense.</textarea></label>'
        + f'<div class="linha">{S.btn("Editar", attrs="disabled title=" + chr(34) + "Elisa Prado está editando" + chr(34))}</div>'
    )
    impacto = (
        "<p>Antes de gravar, mostre o que a mudança desfaz. O modal lista cada revista afetada e o que acontece com ela.</p>"
        + f'<div>{S.btn("Mudar o corte 2 de 5EF LP", icone="lapis", attrs="data-abrir=" + chr(34) + "dlg-impacto-ex" + chr(34))}</div>'
    )
    nao_salvas = (
        "<p>Sair de uma edição com mudanças pendentes pede uma decisão explícita, com a saída segura em destaque.</p>"
        + f'<div>{S.btn("Sair da edição com mudanças", icone="sair", attrs="data-abrir=" + chr(34) + "dlg-nao-salvas" + chr(34))}</div>'
    )
    toast = (
        '<div class="linha">'
        + S.btn("Salvo", attrs=_t("Salvo às 15:42") + " data-salva")
        + S.btn("Validada", attrs=_t("Serra Alta · LP validada"))
        + S.btn("Copiado", attrs=_t("Copiado"))
        + "</div><p class=\"mudo\">Some sozinho em poucos segundos. Serve para confirmar o que acabou de acontecer, nunca para pedir uma decisão.</p>"
    )
    conflito = (
        S.aviso("<b>Não salvou.</b> Elisa Prado gravou esta seção às 15:41, depois que você abriu a página. Compare as duas versões e escolha uma; nada foi sobrescrito.", "erro")
        + '<div class="diff"><div><h4>Sua versão (não salva)</h4><p>Esta revista apresenta os resultados do <ins>Avalia Vale Verde</ins> para a rede valeverdense.</p></div>'
        '<div><h4>Versão de Elisa Prado · 15:41</h4><p>Esta revista apresenta os resultados do <del>Programa Avalia</del> para a rede valeverdense, <ins>com dados de 2026</ins>.</p></div></div>'
        + f'<div class="linha">{S.btn("Usar a versão de Elisa", tom="prim", attrs=_t("Versão de Elisa Prado carregada."))}{S.btn("Copiar a minha versão", icone="copiar", attrs="data-copiar=" + chr(34) + "Esta revista apresenta os resultados do Avalia Vale Verde para a rede valeverdense." + chr(34))}</div>'
    )

    d_impacto = S.dialogo(
        "dlg-impacto-ex",
        "Esta mudança tira o Validado de 3 revistas",
        "<p>Mudar o corte 2 de 5EF LP de 195 para 200 altera a escala de:</p>"
        '<ul class="checklist">'
        f'<li>{S.regua_mini(4)}<span class="txt">Serra Alta · LP<br><small>Validada: volta para Conferir</small></span></li>'
        f'<li>{S.regua_mini(4)}<span class="txt">Monte Sereno · LP<br><small>Validada: volta para Conferir</small></span></li>'
        f'<li>{S.regua_mini(5)}<span class="txt">Porto Alvo · LP<br><small>Impressa: o impresso fica desatualizado</small></span></li></ul>'
        '<p class="mudo">Você precisará validar essas revistas de novo.</p>',
        S.btn("Cancelar", attrs="data-fechar") + S.btn("Gravar e tirar o Validado", tom="prim", attrs="data-fechar " + _t("Salvo. 3 revistas perderam o Validado.")),
    )
    d_nao = S.dialogo(
        "dlg-nao-salvas",
        "Alterações não salvas",
        "<p>Você mudou o texto da Introdução de Vale Verde · LP e ainda não salvou. Se sair agora, essas mudanças se perdem.</p>",
        S.btn("Descartar e sair", tom="perigo", attrs="data-fechar " + _t("Alterações descartadas."))
        + S.btn("Continuar editando", attrs="data-fechar")
        + S.btn("Salvar e sair", tom="prim", attrs="data-fechar " + _t("Salvo e fechado.")),
    )
    corpo = (
        S.cab("Estados do sistema", "Como o sistema se comporta quando falta dado, falta permissão, outra pessoa está no mesmo lugar ou algo dá errado. Cada estado tem um jeito só, em todas as telas.")
        + ind
        + '<div class="es-grade">'
        + sec("es-vazio", "Vazio", "Quando uma lista ou fase não tem nada. Diz o motivo e oferece o próximo passo.", vazio)
        + sec("es-leitura", "Só leitura", "Quando o perfil vê, mas não grava (Impresso). O aviso explica e diz a quem pedir.", leitura)
        + sec("es-bloqueio", "Bloqueio por outra pessoa", "Quando alguém está editando o mesmo trecho. Mostra quem, desde quando e quando libera.", bloqueio)
        + sec("es-impacto", "Modal de impacto", "Antes de gravar uma mudança que tira o Validado de outras revistas.", impacto)
        + sec("es-nao-salvas", "Alterações não salvas", "Ao sair de uma edição com mudanças pendentes.", nao_salvas)
        + sec("es-toast", "Aviso passageiro", "Para confirmar uma ação que já aconteceu.", toast)
        + sec("es-conflito", "Erro de salvamento com conflito", "Quando outra pessoa gravou primeiro. Diz a causa e deixa escolher; nunca sobrescreve em silêncio.", conflito, larga=True)
        + "</div>"
        + d_impacto
        + d_nao
    )
    return S.Pagina("estados.html", "Estados do sistema", "sobre", corpo, trilha=[("Sobre esta proposta", "sobre.html"), ("Estados", None)])


def paginas():
    return [entrar(), senha(), senha_invalida(), senha_pronto(), usuarios(), usuario_novo(), usuario_link(), excluir_em_uso(), excluir_livre(), estados()]
