import json
import os
import shutil
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection
from django.test import TestCase, TransactionTestCase, override_settings
from django.test.utils import CaptureQueriesContext

from nucleo.models import (
    Ano,
    Componente,
    CorPadrao,
    Corte,
    Descritor,
    Etapa,
    FotoRevista,
    Matriz,
    MatrizEtapaCC,
    Parceiro,
    ParceiroAno,
    Projeto,
    ProjetoCor,
    ProjetoPasso,
    Revista,
    RevistaFasciculo,
    RevistaSecao,
    Tarefa,
    Template,
    TemplateVersao,
)
from nucleo.models.revista import Motivo
from nucleo.servicos.cascata import gravar_cortes
from nucleo.servicos.foto import fotografar
from nucleo.servicos.resolver import (
    FAIXA_SEM_TEMPLATE,
    conteudo_impresso,
    carregar,
    escala,
    hash_validado,
    niveis_do_passo,
    pendencias,
    resolver,
    secoes_desatualizadas,
    sha256,
    valores_das_variaveis,
)
from nucleo.texto import renderizar

# JSON do F1 que o Playwright f1-fixture carrega (gabarito). Regerar: REGERAR_FIXTURES=1.
GABARITO = Path(__file__).parent / "fixtures" / "resolver-4cortes.json"

F1 = "## introducao\nAnálise de {{nome_parceiro}}\n\nTexto **{{nome_projeto}}**.\n\n## fechamento\nUtilização\n\nFim.\n"
F2_LP = (
    "## abertura\nAbertura\n\nBem-vindo.\n\n## passo1\nPasso um\n\nPara os {{adjetivo_patrio_plural_masculino}}.\n\n"
    "## dlg-p2\nItens\n\nDetalhe.\n"
)
F2_MT = "## abertura\nAbertura\n\nBem-vindo.\n\n## passo1\nPasso um\n\nSem variável.\n"


def usuario(nome, papel=None, is_staff=True, **campos):
    """Usuário staff (senha "x"), no grupo `papel` se houver."""
    u = get_user_model().objects.create_user(nome, password="x", is_staff=is_staff, **campos)
    if papel:
        u.groups.add(Group.objects.get(name=papel))
    return u


class MediaTemporaria:
    """MEDIA_ROOT num diretório temporário por teste, apagado no fim."""

    def setUp(self):
        super().setUp()
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media)
        ctx = override_settings(MEDIA_ROOT=media)
        ctx.enable()
        self.addCleanup(ctx.disable)


class Mundo:
    """Ano 2026, LP e MT, 5EF e 9EF, Comunitária com passo 25, templates e GO + PE com 4 cortes."""

    @classmethod
    def montar(cls, alvo):
        alvo.usuario = get_user_model().objects.create(username="admin")
        ano = alvo.ano = Ano.objects.create(ano=2026)
        alvo.lp = Componente.objects.create(ano=ano, codigo="LP", nome="Língua Portuguesa")
        alvo.mt = Componente.objects.create(ano=ano, codigo="MT", nome="Matemática")
        alvo.e5 = Etapa.objects.create(ano=ano, codigo="5EF", escala_max=500, ordem=2)
        alvo.e9 = Etapa.objects.create(ano=ano, codigo="9EF", escala_max=500, ordem=3)
        for k, cor in enumerate(["#F72628", "#FF8D43", "#B3CCFF", "#0ED3FF", "#FFFFFF"], 1):
            # Nomes do ano (D-175): o gabarito continua com "Padrão 0k"; os projetos não sobrescrevem.
            CorPadrao.objects.create(ano=ano, padrao=k, cor=cor, nome=f"Padrão {k:02d}")
        alvo.matriz = Matriz.objects.create(ano=ano, nome="Comunitária")
        alvo.tarefa = None
        for comp in (alvo.lp, alvo.mt):
            for etapa in (alvo.e5, alvo.e9):
                mec = MatrizEtapaCC.objects.create(
                    matriz=alvo.matriz, etapa=etapa, componente=comp, ano=ano, passo=25
                )
                d1 = Descritor.objects.create(
                    matriz_etapa_cc=mec, codigo="D01", descricao=f"Descritor 1 {comp.codigo}",
                    prerequisitos=["Pré 1;", "Pré 2."], praticas="Leitura", conhecimento="Estratégia",
                    habilidades_relacionadas="EF15LP02", habilidade_correspondente="", ordem=1,
                )
                d2 = Descritor.objects.create(
                    matriz_etapa_cc=mec, codigo="D02", descricao="Descritor 2", ordem=2
                )
                t = Tarefa.objects.create(descritor=d1, inicio=100, fim=150, texto="Localiza.", ordem=2)
                Tarefa.objects.create(descritor=d1, inicio=225, fim=275, texto="Cruza o corte 250.", ordem=1)
                Tarefa.objects.create(descritor=d2, inicio=300, fim=350, texto="Infere.", ordem=1)
                if alvo.tarefa is None:
                    alvo.tarefa = t  # LP 5EF D01
        alvo.templates = {}
        for comp, f2 in ((alvo.lp, F2_LP), (alvo.mt, F2_MT)):
            for fasc, txt in (("F1", F1), ("F2", f2)):
                t = Template.objects.create(ano=ano, componente=comp, fasciculo=fasc, nome="Padrão")
                TemplateVersao.objects.create(template=t, numero=1, texto=txt)
                alvo.templates[comp.codigo, fasc] = t
        alvo.go = cls.parceiro(alvo, "GO", [100, 200, 250, 300])
        alvo.pe = cls.parceiro(alvo, "PE", [150, 200, 250, 350])

    @staticmethod
    def parceiro(alvo, nome, cortes):
        pa = ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome=nome), ano=alvo.ano, matriz=alvo.matriz)
        gravar_cortes(
            pa,
            [(alvo.e5, alvo.lp, cortes), (alvo.e9, alvo.lp, cortes), (alvo.e5, alvo.mt, cortes)],
            alvo.usuario,
        )
        projeto = Projeto.objects.get(parceiro_ano=pa, arquivado_em__isnull=True)
        projeto.nome = f"Projeto {nome}"
        projeto.adjetivo_patrio_plural_masculino = "goianos"
        projeto.save()
        for rf in RevistaFasciculo.objects.filter(revista__projeto=projeto).select_related("revista"):
            rf.template = alvo.templates[rf.revista.componente.codigo, rf.fasciculo]
            rf.save()
        return {r.componente.codigo: r for r in Revista.objects.filter(projeto=projeto)}


def recarregar(revista):
    return Revista.objects.get(pk=revista.pk)


class EscalaTest(TestCase):
    """Casos de contrato/schemas.ts (api/test/contrato.test.ts), generalizados para N padrões."""

    def test_niveis_do_passo_25(self):
        n = niveis_do_passo(0, 500, 25)
        self.assertEqual((len(n), n[0], n[-1]), (20, 0, 475))

    def test_passo_25_linhas_vazias(self):
        # contrato: nível 150 já ocupado. Aqui por uma tarefa 150→175 (fim = próximo nível).
        r = escala([(150, 175, "manual", None)], [150, 200, 250], 0, 500, 25)
        vazias = {p: [linha["level"] for linha in linhas if linha["content"] == "---"] for p, linhas in r.items()}
        self.assertEqual(vazias["padrao-1"], [125, 100, 75, 50, 25, 0])
        self.assertEqual(vazias["padrao-2"], [175])  # 150 já existe
        self.assertEqual(vazias["padrao-3"], [225, 200])
        self.assertEqual(len(vazias["padrao-4"]), 10)
        self.assertEqual(r["padrao-4"][0], {"level": 475, "fim": 500, "content": "---"})
        self.assertEqual(r["padrao-2"][1], {"level": 150, "fim": 175, "content": "manual"})

    def test_linha_vazia_mesmo_dentro_de_tarefa_larga(self):  # D-155: fiel ao TS, só o início conta
        r = escala([(100, 200, "longa", None)], [300], 0, 500, 25)
        vazias = [linha["level"] for linha in r["padrao-1"] if linha["content"] == "---"]
        self.assertTrue({125, 150, 175}.issubset(vazias))
        self.assertNotIn(100, vazias)

    def test_item_da_tarefa(self):
        r = escala([(100, 150, "com", "itens/abc.pdf"), (200, 250, "sem", None)], [300], 0, 500, None)
        com, sem = sorted(r["padrao-1"], key=lambda linha: linha["level"])
        self.assertEqual(com["item"], {"id": "abc", "tipo": "pdf"})
        self.assertNotIn("item", sem)

    def test_n_padroes_e_ancora_maior(self):
        r = escala([(190, 260, "cruza dois cortes", None), (150, 200, "topo no corte", None)], [200, 250], 0, 500, None)
        self.assertEqual(list(r), ["padrao-1", "padrao-2", "padrao-3"])
        self.assertEqual([linha["content"] for linha in r["padrao-3"]], ["cruza dois cortes"])
        self.assertEqual([linha["content"] for linha in r["padrao-1"]], ["topo no corte"])  # topo aberto
        self.assertEqual(r["padrao-2"], [])  # sem passo, sem linhas vazias


class ResolverTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Mundo.montar(cls)

    def test_f1_no_formato_do_js(self):
        r = resolver(self.go["LP"])
        self.assertEqual(r["f1"]["etapas"], ["5ef", "9ef"])
        e5 = r["f1"]["dados"]["5ef"]
        self.assertEqual(e5["scaleRange"], {"min": 0, "max": 500})
        self.assertEqual(e5["cortes"], {"padrao-1": 100, "padrao-2": 200, "padrao-3": 250, "padrao-4": 300})
        self.assertEqual([p["chave"] for p in e5["padroes"]], [f"padrao-{k}" for k in range(1, 6)])
        self.assertEqual(e5["padroes"][4]["rotulo"], "Padrão 05")
        d01 = e5["D01"]
        self.assertEqual(d01["bncc"]["skills"], ["EF15LP02"])
        self.assertIn({"level": 225, "fim": 275, "content": "Cruza o corte 250."}, d01["scale"]["padrao-4"])
        self.assertIn({"level": 100, "fim": 150, "content": "Localiza."}, d01["scale"]["padrao-2"])
        self.assertEqual(r["f1"]["cores"]["padrao-5"], "#FFFFFF")
        self.assertEqual(r["lacunas"], [])
        # Gabarito do Playwright (f1-fixture.spec.ts): o mesmo JSON que o JS lê.
        dados = r["f1"]["dados"]
        if os.environ.get("REGERAR_FIXTURES"):
            GABARITO.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        self.assertEqual(json.loads(GABARITO.read_text(encoding="utf-8")), dados)

    def test_textos_renderizados(self):
        r = resolver(self.go["LP"])
        intro = r["f1"]["secoes"][0]
        self.assertEqual((intro["id"], intro["titulo"]), ("introducao", "Análise de GO"))
        self.assertEqual(intro["corpo"], "<p>Texto <strong>Projeto GO</strong>.</p>\n")
        self.assertEqual([s["id"] for s in r["f2"]["secoes"]], ["abertura", "passo1", "dlg-p2"])

    def test_variaveis_oficiais_renderizam_o_valor_do_projeto(self):
        Projeto.objects.filter(pk=self.go["LP"].projeto_id).update(pd05="Avançado")
        valores = valores_das_variaveis(recarregar(self.go["LP"]).projeto)
        corpo = renderizar("Estudantes de {{nome_parceiro}}: {{pd05}}.", valores)
        self.assertEqual(corpo, "<p>Estudantes de GO: Avançado.</p>\n")  # nome_parceiro = Parceiro.nome

    def test_pdnn_vazio_usa_o_nome_do_ano(self):  # D-175
        CorPadrao.objects.filter(ano=self.ano, padrao=2).update(nome="Abaixo do básico")
        lp = recarregar(self.go["LP"])
        padroes = resolver(lp)["f1"]["dados"]["5ef"]["padroes"]
        self.assertEqual(padroes[1], {"chave": "padrao-2", "rotulo": "Abaixo do básico"})
        valores = valores_das_variaveis(lp.projeto)
        self.assertEqual(renderizar("{{pd02}}", valores), "<p>Abaixo do básico</p>\n")

    def test_rotulo_do_padrao_sai_do_pdnn(self):  # o projeto sobrescreve o nome do ano
        CorPadrao.objects.filter(ano=self.ano, padrao=2).update(nome="Abaixo do básico")
        Projeto.objects.filter(pk=self.go["LP"].projeto_id).update(pd02="Básico")
        lp = recarregar(self.go["LP"])
        padroes = resolver(lp)["f1"]["dados"]["5ef"]["padroes"]
        self.assertEqual(padroes[1], {"chave": "padrao-2", "rotulo": "Básico"})
        self.assertEqual(renderizar("{{pd02}}", valores_das_variaveis(lp.projeto)), "<p>Básico</p>\n")

    def com_cortes(self, valores, **pd):
        """LP do GO com `valores` em todas as etapas e os pdNN dados; devolve a revista recarregada."""
        Corte.objects.filter(parceiro_ano=self.go["LP"].projeto.parceiro_ano, componente=self.lp).update(valores=valores)
        Projeto.objects.filter(pk=self.go["LP"].projeto_id).update(**pd)
        return recarregar(self.go["LP"])

    def test_pdnn_e_nome_do_ano_vazios_de_padrao_existente_e_pendencia(self):
        CorPadrao.objects.filter(ano=self.ano, padrao=3).update(nome="")
        lp = self.com_cortes([200, 300], pd03=" ")  # 3 padrões
        r = resolver(lp)
        self.assertEqual(r["f1"]["dados"]["5ef"]["padroes"][2]["rotulo"], "{{pd03}}")  # o JS destaca
        self.assertEqual(r["lacunas"], [{"tipo": "variavel", "nome": "pd03"}])
        self.assertIn(("variaveis", "Variáveis sem valor: pd03."), [(p.codigo, p.mensagem) for p in pendencias(lp)])

    def test_pdnn_vazio_de_padrao_que_nao_existe_nao_e_pendencia(self):
        CorPadrao.objects.filter(ano=self.ano, padrao=5).update(nome="")
        lp = self.com_cortes([200, 250, 300], pd05="")  # 4 padrões
        self.assertEqual(resolver(lp)["lacunas"], [])
        self.assertNotIn("variaveis", [p.codigo for p in pendencias(lp)])

    def test_rotulo_muda_o_hash_e_o_impresso(self):  # o rótulo é texto impresso
        antes = hash_validado(self.go["LP"]), conteudo_impresso(self.go["LP"])
        lp = self.com_cortes([100, 200, 250, 300], pd01="Abaixo do básico")
        self.assertNotEqual(antes[0], hash_validado(lp))
        self.assertNotEqual(antes[1], conteudo_impresso(lp))

    def test_nome_do_ano_muda_o_hash_so_de_quem_nao_sobrescreve(self):
        Projeto.objects.filter(pk=self.go["LP"].projeto_id).update(pd02="Básico")
        go, pe = recarregar(self.go["LP"]), recarregar(self.pe["LP"])
        antes = hash_validado(go), hash_validado(pe)
        CorPadrao.objects.filter(ano=self.ano, padrao=2).update(nome="Abaixo do básico")
        self.assertEqual(hash_validado(go), antes[0])
        self.assertNotEqual(hash_validado(pe), antes[1])

    def test_passo_do_projeto_sobrescreve_e_cor_do_projeto(self):
        projeto = self.go["LP"].projeto
        ProjetoPasso.objects.create(projeto=projeto, etapa=self.e5, componente=self.lp, ano=self.ano, passo=None)
        ProjetoCor.objects.create(projeto=projeto, padrao=5, cor="#123456")
        r = resolver(self.go["LP"])
        linhas = [linha for ls in r["f1"]["dados"]["5ef"]["D01"]["scale"].values() for linha in ls]
        self.assertNotIn("---", [linha["content"] for linha in linhas])  # passo nulo = sem linhas vazias
        self.assertIn("---", [linha["content"] for linha in r["f1"]["dados"]["9ef"]["D01"]["scale"]["padrao-1"]])
        self.assertEqual(r["f1"]["cores"]["padrao-5"], "#123456")

    def test_variavel_so_no_f2_da_lp_muda_so_o_hash_da_lp(self):
        antes = hash_validado(self.go["LP"]), hash_validado(self.go["MT"])
        Projeto.objects.filter(pk=self.go["LP"].projeto_id).update(adjetivo_patrio_plural_masculino="goianas")
        depois = hash_validado(recarregar(self.go["LP"])), hash_validado(recarregar(self.go["MT"]))
        self.assertNotEqual(antes[0], depois[0])
        self.assertEqual(antes[1], depois[1])

    def test_trocar_svg_muda_o_hash_e_nao_o_impresso(self):
        lp = self.go["LP"]
        hash_antes, impresso_antes = hash_validado(lp), conteudo_impresso(lp)
        Revista.objects.filter(pk=lp.pk).update(svg_f2="f2/novo.svg", svg_sha256="b" * 64, svg_ids=["passo1"])
        lp = recarregar(lp)
        self.assertNotEqual(hash_validado(lp), hash_antes)
        self.assertEqual(conteudo_impresso(lp), impresso_antes)

    def test_corte_do_pe_muda_so_o_pe(self):
        go, pe = conteudo_impresso(self.go["LP"]), conteudo_impresso(self.pe["LP"])
        Corte.objects.filter(
            parceiro_ano=self.pe["LP"].projeto.parceiro_ano, etapa=self.e5, componente=self.lp
        ).update(valores=[150, 200, 260, 350])
        pe_depois = conteudo_impresso(self.pe["LP"])
        self.assertEqual(conteudo_impresso(self.go["LP"]), go)
        self.assertNotEqual(pe_depois, pe)
        self.assertEqual(pe_depois["f1"]["dados"]["9ef"], pe["f1"]["dados"]["9ef"])  # só a etapa mudou

    def test_tarefa_da_comunitaria_muda_todas_as_revistas_que_a_usam(self):
        revistas = [self.go["LP"], self.pe["LP"], self.go["MT"]]
        antes = [conteudo_impresso(r) for r in revistas]
        Tarefa.objects.filter(pk=self.tarefa.pk).update(texto="Localiza e descreve.")
        depois = [conteudo_impresso(r) for r in revistas]
        self.assertNotEqual(depois[0], antes[0])
        self.assertNotEqual(depois[1], antes[1])
        self.assertEqual(depois[2], antes[2])  # MT usa outra MEC

    def test_sem_template_marcador_e_pendencia(self):
        RevistaFasciculo.objects.filter(revista=self.go["LP"], fasciculo="F2").update(template=None)
        r = resolver(self.go["LP"])
        self.assertEqual(r["f2"]["secoes"], None)
        self.assertEqual(r["f2"]["faixa"], FAIXA_SEM_TEMPLATE.format("F2"))
        self.assertIn({"tipo": "template", "fasciculo": "F2"}, r["lacunas"])
        self.assertIn("template_f2", [p.codigo for p in pendencias(self.go["LP"])])
        self.assertNotIn("variaveis", [p.codigo for p in pendencias(self.go["LP"])])  # gentílico só no F2

    def test_variavel_vazia_lacuna_e_pendencia(self):
        Projeto.objects.filter(pk=self.go["LP"].projeto_id).update(adjetivo_patrio_plural_masculino=" ")
        lp = recarregar(self.go["LP"])
        r = resolver(lp)
        self.assertIn('<span class="variavel-vazia">{{adjetivo_patrio_plural_masculino}}</span>', r["f2"]["secoes"][1]["corpo"])
        self.assertEqual(r["lacunas"], [{"tipo": "variavel", "nome": "adjetivo_patrio_plural_masculino"}])
        self.assertIn("variaveis", [p.codigo for p in pendencias(lp)])

    def test_pendencias(self):
        lp = self.go["LP"]
        self.assertEqual([p.codigo for p in pendencias(lp)], ["svg", "capa"])
        Revista.objects.filter(pk=lp.pk).update(
            svg_f2="f2/x.svg", svg_sha256="a" * 64, svg_ids=["passo1"], capa="capas/x.png", capa_sha256="c" * 64
        )
        lp = recarregar(lp)
        ids = [p for p in pendencias(lp) if p.codigo == "ids_svg"]
        self.assertEqual(ids[0].mensagem, "Ids que faltam no SVG: btn-action-p2.")
        Revista.objects.filter(pk=lp.pk).update(svg_ids=["passo1", "btn-action-p2"])
        self.assertEqual(pendencias(recarregar(lp)), [])

        pa = lp.projeto.parceiro_ano
        Projeto.objects.filter(pk=lp.projeto_id).update(nome="GO - NOME DO PROJETO")
        MatrizEtapaCC.objects.filter(matriz=self.matriz, etapa=self.e9, componente=self.lp).delete()
        self.assertEqual(
            [(p.codigo, p.mensagem) for p in pendencias(recarregar(lp))],
            [("corte_sem_matriz", "A matriz não tem a etapa: 9EF."), ("nome_projeto", "Troque o nome padrão do projeto.")],
        )
        ParceiroAno.objects.filter(pk=pa.pk).update(matriz=None)
        self.assertEqual(pendencias(recarregar(lp))[0].codigo, "matriz")

    def test_copia_de_secao_e_desatualizada(self):
        lp = self.go["LP"]
        rf = RevistaFasciculo.objects.get(revista=lp, fasciculo="F1")
        t = self.templates["LP", "F1"]
        v1 = TemplateVersao.objects.get(template=t)
        RevistaSecao.objects.create(revista_fasciculo=rf, template=t, secao="fechamento", texto="Meu fim.", template_versao=v1)
        r = resolver(lp)
        self.assertEqual(r["f1"]["secoes"][1], {"id": "fechamento", "titulo": "Utilização", "corpo": "<p>Meu fim.</p>\n"})
        self.assertEqual(secoes_desatualizadas(lp), [])
        # Versão nova mexendo só na introdução: a cópia do fechamento continua em dia.
        TemplateVersao.objects.create(template=t, numero=2, texto=F1.replace("Texto", "Novo texto"))
        self.assertEqual(secoes_desatualizadas(lp), [])
        TemplateVersao.objects.create(template=t, numero=3, texto=F1.replace("Fim.", "Fim novo."))
        self.assertEqual([c.secao for c in secoes_desatualizadas(lp)], ["fechamento"])
        self.assertEqual(resolver(lp)["f1"]["secoes"][1]["corpo"], "<p>Meu fim.</p>\n")  # a cópia vale

    def test_corte_invalido_vira_pendencia(self):  # gravado por outro caminho que não a cascata
        Corte.objects.filter(
            parceiro_ano=self.go["LP"].projeto.parceiro_ano, etapa=self.e9, componente=self.lp
        ).update(valores=[200, 500])
        p = [x for x in pendencias(recarregar(self.go["LP"])) if x.codigo == "corte_invalido"]
        self.assertEqual(p[0].mensagem, "Cortes fora de ordem ou da escala: 9EF.")
        Corte.objects.filter(componente=self.lp).update(valores=[300, 200])
        self.assertIn("5EF, 9EF", [x for x in pendencias(recarregar(self.go["LP"])) if x.codigo == "corte_invalido"][0].mensagem)

    def test_teto_de_consultas(self):
        lp = carregar(self.go["LP"].pk)
        with CaptureQueriesContext(connection) as so_resolver:
            resolvido = resolver(lp)
        with CaptureQueriesContext(connection) as resto:
            pendencias(lp, resolvido)
            hash_validado(lp, resolvido)
        self.assertLessEqual(len(so_resolver), 13, "\n".join(q["sql"][:120] for q in so_resolver))  # +1: nomes do ano (D-175)
        self.assertLessEqual(len(resto), 2)  # só a conferência de MEC por etapa
        self.assertEqual(hash_validado(lp, resolvido), hash_validado(lp))

    def test_copias_orfas_em_ordem(self):
        t = self.templates["LP", "F2"]
        rf = RevistaFasciculo.objects.get(revista=self.go["LP"], fasciculo="F2")
        v1 = TemplateVersao.objects.get(template=t)
        for secao in ("dlg-zz", "dlg-aa"):  # fora do template: órfãs
            RevistaSecao.objects.create(revista_fasciculo=rf, template=t, secao=secao, texto=secao, template_versao=v1)
        ids = [s["id"] for s in resolver(self.go["LP"])["f2"]["secoes"]]
        self.assertEqual(ids, ["abertura", "passo1", "dlg-p2", "dlg-aa", "dlg-zz"])

    def test_arquivada_devolve_a_foto_de_arquivamento(self):
        mt = self.go["MT"]
        foto = fotografar(mt, Motivo.ARQUIVAMENTO, self.usuario)
        self.assertEqual(foto.hash, hash_validado(mt))
        Revista.objects.filter(pk=mt.pk).update(arquivada_em="2026-10-29T12:00:00Z")
        Tarefa.objects.update(texto="mudou")
        self.assertEqual(resolver(recarregar(mt)), foto.conteudo)
        self.assertEqual(hash_validado(recarregar(mt)), foto.hash)


class FotoRepeatableReadTest(TransactionTestCase):
    def setUp(self):
        Mundo.montar(self)

    def test_fora_de_atomic_usa_repeatable_read(self):
        with CaptureQueriesContext(connection) as consultas:
            foto = fotografar(self.go["LP"], Motivo.IMPRESSO, self.usuario)
        sqls = [q["sql"] for q in consultas.captured_queries]
        self.assertEqual(sqls[:2], ["BEGIN", "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"])
        self.assertEqual(foto.hash, hash_validado(self.go["LP"]))
        self.assertEqual(FotoRevista.objects.get().conteudo, resolver(self.go["LP"]))

    def test_fora_de_atomic_relê_a_revista(self):
        velha = self.go["LP"]  # instância de antes da troca do SVG
        Revista.objects.filter(pk=velha.pk).update(svg_f2="f2/x.svg", svg_sha256="d" * 64)
        foto = fotografar(velha, Motivo.IMPRESSO, self.usuario)
        self.assertEqual(foto.conteudo["f2"]["svg_sha256"], "d" * 64)
