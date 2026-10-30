"""Revista resolvida: o que o preview, o hash, a foto, o zip e o painel leem (S07).

Só leitura; quem grava é `foto.fotografar`. Formato de `resolver(revista)`:

    {
      "f1": {
        "etapas": ["5ef", "9ef"],     # ordem das abas: o jsonb da foto não guarda a ordem das chaves
        "dados": {"5ef": {...}},      # exatamente o JSON que o JS do F1 lê (D-130, D-131)
        "cores": {"padrao-1": "#F72628", ...},   # efetivas, até o maior n das etapas (D-060, D-064)
        "secoes": [{"id", "titulo", "corpo"}],   # None sem template
      },
      "f2": {"secoes": [...] ou None, "svg_sha256": ..., "svg_ids": [...]},
      "capa_sha256": ...,
      "lacunas": [{"tipo": "template", "fasciculo": "F1"}, {"tipo": "variavel", "nome": "..."}],
    }

`titulo` e `corpo` são HTML já escapado (o `titulo` pode ter o `<span class="variavel-vazia">`):
quem consome usa `|safe`/innerHTML, nunca como texto.
Linha da tarefa com arquivo: `item: {"id": <nome sem extensão>, "tipo": <extensão>}` (o JS monta
`arquivos/itens/<id>.<tipo>`); sem arquivo, sem a chave.
Fascículo sem template: `secoes` None e `faixa` com o HTML da faixa vermelha (D-116).
Variável vazia: já sai de `texto.renderizar` como `<span class="variavel-vazia">` (D-139).
Os valores das variáveis e o nome do projeto não entram aqui, só os textos renderizados:
assim uma variável usada só no LP não muda o hash do MT (D-125). Exceção: `pd01`..`pdNN`
são os rótulos dos padrões em `dados[etapa]["padroes"]`, então mudam o hash de toda revista
que tem aquele padrão.
"""

import hashlib
import json
from pathlib import PurePosixPath
from typing import NamedTuple

from django.db.models import Prefetch

from nucleo import texto
from nucleo.models import (
    CorPadrao,
    Corte,
    Descritor,
    FotoRevista,
    MatrizEtapaCC,
    ProjetoCor,
    ProjetoPasso,
    Revista,
    RevistaFasciculo,
    RevistaSecao,
    Tarefa,
    TemplateVersao,
)
from nucleo.models.revista import Motivo
from nucleo.servicos.arquivos import ids_faltando
from nucleo.variaveis import VARIAVEIS

VAZIO = "---"  # linha sem habilidade (CONTEUDO_VAZIO do contrato)
FAIXA_SEM_TEMPLATE = '<div class="faixa-vermelha" role="alert">Falta escolher o template do {}.</div>'


def carregar(pk):
    """Revista com projeto, parceiro_ano, parceiro e ano num SELECT só (o resolver lê todos)."""
    return Revista.objects.select_related("projeto__parceiro_ano__parceiro", "projeto__ano").get(pk=pk)


def canonico(obj):
    """JSON canônico do hash (D-125): chaves ordenadas, separadores fixos, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256(obj):
    return hashlib.sha256(canonico(obj).encode()).hexdigest()


# --- Escala do F1 (portado de contrato/schemas.ts, generalizado para N padrões) ---------


def padrao_da_tarefa(fim, cortes):
    """Âncora maior (D-044, D-058): o padrão mais alto cujo início é < fim (topo aberto)."""
    return 1 + sum(c < fim for c in cortes)


def padrao_do_nivel(nivel, cortes):
    """padraoDoNivel: nível igual ao corte já é do padrão de cima."""
    return 1 + sum(c <= nivel for c in cortes)


def niveis_do_passo(minimo, maximo, passo):
    """niveisDoPasso: min + k·passo < max, crescentes."""
    return list(range(minimo, maximo, passo))


def escala(tarefas, cortes, minimo, maximo, passo):
    """`scale` de um descritor: {"padrao-1".."padrao-n": linhas de cima para baixo}, n = cortes + 1.

    `tarefas`: [(inicio, fim, texto, arquivo)]. Cada uma vai para o padrão da âncora maior.
    Com passo, cada nível do passo sem tarefa começando nele vira uma linha "---" no padrão
    do nível, mesmo dentro do intervalo de uma tarefa mais larga (linhasVaziasDoPasso, D-155);
    passo nulo = sem linhas vazias (D-091).
    """
    saida = {f"padrao-{k}": [] for k in range(1, len(cortes) + 2)}
    for inicio, fim, conteudo, arquivo in tarefas:
        linha = {"level": inicio, "fim": fim, "content": conteudo}
        if arquivo:
            caminho = PurePosixPath(arquivo)
            linha["item"] = {"id": caminho.stem, "tipo": caminho.suffix.lstrip(".")}
        saida[f"padrao-{padrao_da_tarefa(fim, cortes)}"].append(linha)
    if passo:
        existentes = {inicio for inicio, _, _, _ in tarefas}
        for nivel in niveis_do_passo(minimo, maximo, passo):
            if nivel not in existentes:
                saida[f"padrao-{padrao_do_nivel(nivel, cortes)}"].append(
                    {"level": nivel, "fim": min(nivel + passo, maximo), "content": VAZIO}
                )
    for linhas in saida.values():
        linhas.sort(key=lambda linha: -linha["level"])  # estável: mesmo nível mantém a ordem
    return saida


def rotulo_do_padrao(k, valores):
    """Rótulo do padrão k na escala: `pdNN` do projeto. Vazio: o próprio `{{pdNN}}`, que o JS
    destaca como variável vazia (D-116). Texto puro: o JS escapa."""
    nome = f"pd{k:02d}"
    valor = valores.get(nome)
    return f"{{{{{nome}}}}}" if valor is None or not str(valor).strip() else str(valor)


def _f1_escalas(revista, projeto, variaveis):
    pa = projeto.parceiro_ano
    cortes = list(
        Corte.objects.filter(parceiro_ano=pa, componente_id=revista.componente_id)
        .select_related("etapa")
        .order_by("etapa__ordem", "etapa__codigo")
    )
    mecs = {}
    if pa.matriz_id is not None and cortes:
        mecs = {
            m.etapa_id: m
            for m in MatrizEtapaCC.objects.filter(
                matriz_id=pa.matriz_id,
                componente_id=revista.componente_id,
                etapa_id__in=[c.etapa_id for c in cortes],
            )
        }
    # D-053, D-091: existir a linha é "sobrescrevi"; passo nulo nela é "sem linhas vazias".
    passos = {
        p.etapa_id: p.passo
        for p in ProjetoPasso.objects.filter(projeto=projeto, componente_id=revista.componente_id)
    }
    descritores = {}
    for d in (
        Descritor.objects.filter(matriz_etapa_cc__in=list(mecs.values()))  # lista vazia: sem SELECT
        .prefetch_related(Prefetch("tarefa_set", queryset=Tarefa.objects.order_by("ordem", "pk")))
        .order_by("ordem", "codigo")
    ):
        descritores.setdefault(d.matriz_etapa_cc_id, []).append(d)

    etapas, dados = [], {}
    for corte in cortes:
        etapa, valores = corte.etapa, corte.valores
        mec = mecs.get(etapa.pk)
        passo = passos[etapa.pk] if etapa.pk in passos else (mec.passo if mec else None)
        n = len(valores) + 1
        chave = etapa.codigo.lower()
        etapas.append(chave)
        dados[chave] = {
            "scaleRange": {"min": 0, "max": etapa.escala_max},
            "cortes": {f"padrao-{i}": v for i, v in enumerate(valores, 1)},
            "padroes": [{"chave": f"padrao-{k}", "rotulo": rotulo_do_padrao(k, variaveis)} for k in range(1, n + 1)],
        }
        for d in descritores.get(mec.pk if mec else None, []):
            tarefas = [(t.inicio, t.fim, t.texto, t.arquivo) for t in d.tarefa_set.all()]
            dados[chave][d.codigo] = {
                "description": d.descricao,
                "prerequisites": list(d.prerequisitos),
                "bncc": {
                    "practices": d.praticas,
                    "knowledge": d.conhecimento,
                    "skills": [s for s in (d.habilidades_relacionadas, d.habilidade_correspondente) if s],
                },
                "scale": escala(tarefas, valores, 0, etapa.escala_max, passo),
            }
    return etapas, dados


def _cores(revista, projeto, padroes):
    """Cores 1..padroes: ProjetoCor sobrescreve CorPadrao do ano (D-060, D-064)."""
    cores = dict(CorPadrao.objects.filter(ano_id=revista.ano_id).values_list("padrao", "cor"))
    cores.update(ProjetoCor.objects.filter(projeto=projeto).values_list("padrao", "cor"))
    return {f"padrao-{k}": cores[k] for k in range(1, padroes + 1) if k in cores}


# --- Textos -----------------------------------------------------------------------


def versao_atual(template_id):
    return TemplateVersao.objects.filter(template_id=template_id).order_by("-numero").first()


def secoes_efetivas(fasciculo):
    """[(id, titulo, corpo)] do RevistaFasciculo: última versão do template, com as cópias
    no lugar das seções editadas (D-104, D-115). None sem template.

    `RevistaSecao.texto` é só o corpo: o título não é editável e vem do template.
    Cópia de seção que saiu do template continua, com o título da versão de onde saiu.
    """
    if fasciculo is None or fasciculo.template_id is None:
        return None
    versao = versao_atual(fasciculo.template_id)
    if versao is None:
        return None
    copias = {
        c.secao: c
        for c in RevistaSecao.objects.filter(revista_fasciculo=fasciculo)
        .select_related("template_versao")
        .order_by("secao")  # ordem estável das órfãs: entra no hash
    }
    saida = []
    for id_, (titulo, corpo) in texto.secoes(versao.texto).items():
        copia = copias.pop(id_, None)
        saida.append((id_, titulo, copia.texto if copia else corpo))
    for id_, copia in copias.items():
        saida.append((id_, texto.secoes(copia.template_versao.texto).get(id_, ("", ""))[0], copia.texto))
    return saida


def valores_das_variaveis(projeto):
    pa = projeto.parceiro_ano
    valores = {v.nome: getattr(projeto, v.nome) for v in VARIAVEIS if not v.automatica}
    valores.update(nome_parceiro=pa.parceiro.nome, nome_projeto=projeto.nome, ano=str(projeto.ano.ano))
    return valores


# --- Resolver, hash e impresso ---------------------------------------------------


def resolver(revista):
    """Revista montada (formato no topo do módulo). Arquivada: a foto de arquivamento (D-117).

    Passe a revista de `carregar(pk)`: com outra instância, cada FK do projeto é um SELECT a mais.
    """
    if revista.arquivada_em is not None:
        foto = (
            FotoRevista.objects.filter(revista=revista, motivo=Motivo.ARQUIVAMENTO)
            .order_by("-criada_em", "-pk")
            .first()
        )
        if foto is not None:
            return foto.conteudo

    projeto = revista.projeto
    valores = valores_das_variaveis(projeto)
    fasciculos = {f.fasciculo: f for f in RevistaFasciculo.objects.filter(revista=revista)}
    lacunas, usadas = [], set()

    def textos(fasciculo):
        efetivas = secoes_efetivas(fasciculos.get(fasciculo))
        if efetivas is None:
            lacunas.append({"tipo": "template", "fasciculo": fasciculo})
            return {"secoes": None, "faixa": FAIXA_SEM_TEMPLATE.format(fasciculo)}
        secoes = []
        for id_, titulo, corpo in efetivas:
            usadas.update(texto.variaveis_usadas(titulo), texto.variaveis_usadas(corpo))
            secoes.append(
                {
                    "id": id_,
                    "titulo": texto.renderizar_texto_puro(titulo, valores),
                    "corpo": texto.renderizar(corpo, valores),
                }
            )
        return {"secoes": secoes}

    etapas, dados = _f1_escalas(revista, projeto, valores)
    padroes = max((len(d["padroes"]) for d in dados.values()), default=0)
    usadas.update(f"pd{k:02d}" for k in range(1, padroes + 1))  # rótulos da escala: só os padrões que a revista tem
    f1 = {"etapas": etapas, "dados": dados, "cores": _cores(revista, projeto, padroes), **textos("F1")}
    f2 = {**textos("F2"), "svg_sha256": revista.svg_sha256, "svg_ids": sorted(revista.svg_ids or [])}
    # Mesmo critério de "vazio" de texto._valor.
    lacunas += [
        {"tipo": "variavel", "nome": n}
        for n in sorted(usadas)
        if valores.get(n) is None or not str(valores[n]).strip()
    ]
    return {"f1": f1, "f2": f2, "capa_sha256": revista.capa_sha256, "lacunas": lacunas}


def hash_validado(revista, resolvido=None):
    """sha256 do JSON canônico do resolvido. O resolvido já traz svg_sha256 e capa_sha256,
    então trocar o SVG ou a capa muda o hash (D-118). `resolvido`: reaproveita um já montado."""
    return sha256(resolver(revista) if resolvido is None else resolvido)


def impresso_de(resolvido):
    """Parte do resolvido que o impresso confere: escalas, cores e textos do F1 e textos do F2.
    Sem SVG nem capa (D-066, D-072, D-077, D-112). Serve também para fotos antigas (S13)."""
    f1, f2 = resolvido["f1"], resolvido["f2"]
    return {
        "f1": {k: f1.get(k) for k in ("etapas", "dados", "cores", "secoes")},
        "f2": {"secoes": f2.get("secoes")},
    }


def conteudo_impresso(revista):
    return impresso_de(resolver(revista))


# --- Pendências e seções desatualizadas -------------------------------------------


class Pendencia(NamedTuple):
    codigo: str
    mensagem: str
    # ponytail: link nulo até existirem as telas (S11/S12); o painel monta o link pelo código.
    link: str | None = None


def problema_dos_cortes(dados):
    """Espelho do problemaDaEtapa do JS (D-131): cortes estritamente crescentes em (min, max).
    Defensivo: a cascata já recusa (D-153), mas o dado pode ter entrado por outro caminho."""
    anterior, maximo = dados["scaleRange"]["min"], dados["scaleRange"]["max"]
    for i in range(1, len(dados["cortes"]) + 1):
        v = dados["cortes"].get(f"padrao-{i}")
        if v is None or not anterior < v < maximo:
            return True
        anterior = v
    return False


def pendencias(revista, resolvido=None):
    """O que bloqueia o "Validado" (D-112, D-116, D-125). Lista vazia = pode validar.
    `resolvido`: reaproveita um já montado (o painel monta uma vez para pendências e hash)."""
    projeto = revista.projeto
    pa = projeto.parceiro_ano
    if resolvido is None:
        resolvido = resolver(revista)
    saida = []
    if pa.matriz_id is None:
        saida.append(Pendencia("matriz", "Falta escolher a matriz do parceiro no ano."))
    else:
        com_mec = set(
            MatrizEtapaCC.objects.filter(matriz_id=pa.matriz_id, componente_id=revista.componente_id)
            .values_list("etapa_id", flat=True)
        )
        sem_mec = [
            c.etapa.codigo
            for c in Corte.objects.filter(parceiro_ano=pa, componente_id=revista.componente_id)
            .select_related("etapa")
            .order_by("etapa__ordem")
            if c.etapa_id not in com_mec
        ]
        if sem_mec:
            saida.append(Pendencia("corte_sem_matriz", f"A matriz não tem a etapa: {', '.join(sem_mec)}."))
    dados = resolvido["f1"]["dados"]
    invalidas = [e.upper() for e in resolvido["f1"]["etapas"] if problema_dos_cortes(dados[e])]
    if invalidas:
        saida.append(
            Pendencia("corte_invalido", f"Cortes fora de ordem ou da escala: {', '.join(invalidas)}.")
        )
    for lacuna in resolvido["lacunas"]:
        if lacuna["tipo"] == "template":
            saida.append(
                Pendencia(f"template_{lacuna['fasciculo'].lower()}", f"Falta escolher o template do {lacuna['fasciculo']}.")
            )
    if not revista.svg_f2:
        saida.append(Pendencia("svg", "Falta o SVG do F2."))
    elif resolvido["f2"]["secoes"] is not None:
        faltando = ids_faltando(revista, [s["id"] for s in resolvido["f2"]["secoes"]])
        if faltando:
            saida.append(Pendencia("ids_svg", f"Ids que faltam no SVG: {', '.join(faltando)}."))
    if not revista.capa:
        saida.append(Pendencia("capa", "Falta a imagem de capa."))
    vazias = [lacuna["nome"] for lacuna in resolvido["lacunas"] if lacuna["tipo"] == "variavel"]
    if vazias:
        saida.append(Pendencia("variaveis", f"Variáveis sem valor: {', '.join(vazias)}."))
    if projeto.nome.endswith(" - NOME DO PROJETO"):  # nome inicial da cascata (D-065)
        saida.append(Pendencia("nome_projeto", "Troque o nome padrão do projeto."))
    return saida


def secoes_desatualizadas(revista):
    """Cópias (RevistaSecao) cuja seção mudou no template depois da versão de onde saíram (D-115).

    Só avisa; não bloqueia o "Validado" (D-087). Seção que saiu do template conta como mudada.
    """
    atuais, saida = {}, []
    copias = (
        RevistaSecao.objects.filter(revista_fasciculo__revista=revista)
        .select_related("template_versao", "revista_fasciculo")
        .order_by("revista_fasciculo__fasciculo", "secao")
    )
    for copia in copias:
        if copia.template_id not in atuais:
            atuais[copia.template_id] = texto.secoes(versao_atual(copia.template_id).texto)
        base = texto.secoes(copia.template_versao.texto).get(copia.secao)
        if base != atuais[copia.template_id].get(copia.secao):
            saida.append(copia)
    return saida
