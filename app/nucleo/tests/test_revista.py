from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from nucleo.models import (
    Ano,
    Bloqueio,
    Componente,
    Corte,
    Etapa,
    Matriz,
    MatrizEtapaCC,
    Parceiro,
    ParceiroAno,
    Projeto,
    ProjetoPasso,
    Revista,
    RevistaFasciculo,
    RevistaSecao,
    Template,
    TemplateVersao,
)
from nucleo.tests.test_constraints import FKS_COMPOSTAS
from nucleo.variaveis import VARIAVEIS


class RecusaRevistaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create(username="pedagogica")
        a26 = cls.a26 = Ano.objects.create(ano=2026)
        a27 = cls.a27 = Ano.objects.create(ano=2027)
        cls.lp = Componente.objects.create(ano=a26, codigo="LP", nome="Língua Portuguesa")
        cls.mt = Componente.objects.create(ano=a26, codigo="MT", nome="Matemática")
        lp27 = cls.lp27 = Componente.objects.create(ano=a27, codigo="LP", nome="Língua Portuguesa")
        cls.e5 = Etapa.objects.create(ano=a26, codigo="5EF", escala_max=500, ordem=2)
        cls.e5_27 = Etapa.objects.create(ano=a27, codigo="5EF", escala_max=500, ordem=2)
        cls.matriz = Matriz.objects.create(ano=a26, nome="Comunitária")
        cls.matriz27 = Matriz.objects.create(ano=a27, nome="Comunitária")
        go = Parceiro.objects.create(nome="GO")
        cls.sc = Parceiro.objects.create(nome="SC")
        cls.pa = ParceiroAno.objects.create(parceiro=go, ano=a26)
        cls.pa27 = ParceiroAno.objects.create(parceiro=go, ano=a27)
        cls.projeto = Projeto.objects.create(parceiro_ano=cls.pa, ano=a26, nome="GO - NOME DO PROJETO")
        cls.projeto27 = Projeto.objects.create(parceiro_ano=cls.pa27, ano=a27, nome="GO - NOME DO PROJETO")
        cls.revista = Revista.objects.create(projeto=cls.projeto, componente=cls.lp, ano=a26)
        cls.rf = RevistaFasciculo.objects.create(
            revista=cls.revista, fasciculo="F1", componente=cls.lp, ano=a26
        )

        def template(ano, comp, nome, fasciculo="F1"):
            t = Template.objects.create(ano=ano, componente=comp, fasciculo=fasciculo, nome=nome)
            return t, TemplateVersao.objects.create(template=t, numero=1, texto="## introducao\n")

        cls.t_lp, cls.v_lp = template(a26, cls.lp, "Padrão")
        cls.t_lp_b, cls.v_lp_b = template(a26, cls.lp, "Alternativo")
        cls.t_mt, cls.v_mt = template(a26, cls.mt, "Padrão")
        cls.t_lp27, _ = template(a27, lp27, "Padrão")  # mesmo código LP, só o ano muda
        cls.t_lp_f2, _ = template(a26, cls.lp, "Padrão", fasciculo="F2")

    def recusa(self, acao, constraint):
        """O banco recusa, e pela constraint certa."""
        with self.assertRaisesMessage(IntegrityError, constraint), transaction.atomic():
            acao()

    def escolher(self, template):
        return RevistaFasciculo.objects.filter(pk=self.rf.pk).update(template=template)

    def test_template_do_mesmo_componente_e_ano_passa(self):
        self.escolher(self.t_lp)

    def test_template_de_mt_em_revista_de_lp(self):
        self.recusa(lambda: self.escolher(self.t_mt), "fk_revista_fasciculo_template_ano")

    def test_template_de_outro_ano(self):
        self.recusa(lambda: self.escolher(self.t_lp27), "fk_revista_fasciculo_template_ano")

    def test_copia_com_versao_de_outro_template(self):
        self.escolher(self.t_lp)
        self.recusa(lambda: RevistaSecao.objects.create(
            revista_fasciculo=self.rf, template=self.t_lp, secao="introducao", texto="x",
            template_versao=self.v_mt,
        ), "fk_revista_secao_versao_template")

    def test_troca_de_template_com_copias(self):
        self.escolher(self.t_lp)
        self.escolher(self.t_lp_b)  # sem cópias, a troca passa
        self.escolher(self.t_lp)
        RevistaSecao.objects.create(
            revista_fasciculo=self.rf, template=self.t_lp, secao="introducao", texto="x",
            template_versao=self.v_lp,
        )
        self.recusa(lambda: self.escolher(self.t_lp_b), "fk_revista_secao_fasciculo_template")

    def test_bloqueio_com_dois_alvos_ou_nenhum(self):
        expira = timezone.now()
        for alvos in ({"projeto": self.projeto, "template": self.t_lp}, {}):
            with self.subTest(alvos=list(alvos)):
                self.recusa(lambda: Bloqueio.objects.create(
                    usuario=self.usuario, sessao_edicao="aba", expira_em=expira, **alvos
                ), "bloqueio_um_alvo")

    def test_dois_projetos_ativos_no_mesmo_parceiro_ano(self):
        self.recusa(lambda: Projeto.objects.create(parceiro_ano=self.pa, ano=self.a26, nome="Outro"),
                    "projeto_um_ativo_por_parceiro_ano")
        Projeto.objects.filter(pk=self.projeto.pk).update(arquivado_em=timezone.now())
        Projeto.objects.create(parceiro_ano=self.pa, ano=self.a26, nome="Readicionado")  # D-068

    def test_corte_com_valores_invalidos(self):
        for valores, constraint in (
            ([], "corte_valores_1a4"),
            ([1, 2, 3, 4, 5], "corte_valores_1a4"),
            ([100, None], "corte_valores_sem_nulo"),
        ):
            with self.subTest(valores=valores):
                self.recusa(lambda: Corte.objects.create(
                    parceiro_ano=self.pa, etapa=self.e5, componente=self.lp, ano=self.a26,
                    valores=valores,
                ), constraint)

    def test_cada_fk_composta_recusa(self):
        """Um caso de recusa por FK composta; FK nova sem caso aqui falha o teste."""
        a26, a27, lp, lp27, e5, e5_27 = self.a26, self.a27, self.lp, self.lp27, self.e5, self.e5_27

        def mec(**kw):
            return lambda: MatrizEtapaCC.objects.create(
                **{"matriz": self.matriz, "etapa": e5, "componente": lp, "ano": a26, **kw}
            )

        def corte(**kw):
            return lambda: Corte.objects.create(**{
                "parceiro_ano": self.pa, "etapa": e5, "componente": lp, "ano": a26,
                "valores": [100], **kw,
            })

        def passo(**kw):
            return lambda: ProjetoPasso.objects.create(
                **{"projeto": self.projeto, "etapa": e5, "componente": lp, "ano": a26, **kw}
            )

        def fasciculo(**kw):
            return lambda: RevistaFasciculo.objects.create(
                **{"revista": self.revista, "fasciculo": "F2", "componente": lp, "ano": a26, **kw}
            )

        def secao(template, versao):
            return lambda: RevistaSecao.objects.create(
                revista_fasciculo=self.rf, template=template, secao="introducao", texto="x",
                template_versao=versao,
            )

        casos = {
            "fk_matriz_etapa_cc_matriz_ano": [mec(matriz=self.matriz27)],
            "fk_matriz_etapa_cc_etapa_ano": [mec(etapa=e5_27)],
            "fk_matriz_etapa_cc_componente_ano": [mec(componente=lp27)],
            "fk_parceiro_ano_matriz_ano": [
                lambda: ParceiroAno.objects.create(parceiro=self.sc, ano=a26, matriz=self.matriz27)
            ],
            "fk_corte_parceiro_ano_ano": [corte(parceiro_ano=self.pa27)],
            "fk_corte_etapa_ano": [corte(etapa=e5_27)],
            "fk_corte_componente_ano": [corte(componente=lp27)],
            # arquivado: sem isso o UNIQUE de projeto ativo recusaria antes da FK.
            "fk_projeto_parceiro_ano_ano": [lambda: Projeto.objects.create(
                parceiro_ano=self.pa, ano=a27, nome="X", arquivado_em=timezone.now()
            )],
            "fk_projeto_passo_projeto_ano": [passo(projeto=self.projeto27)],
            "fk_projeto_passo_etapa_ano": [passo(etapa=e5_27)],
            "fk_projeto_passo_componente_ano": [passo(componente=lp27)],
            "fk_template_componente_ano": [lambda: Template.objects.create(
                ano=a27, componente=lp, fasciculo="F1", nome="X"
            )],
            "fk_revista_projeto_ano": [
                lambda: Revista.objects.create(projeto=self.projeto27, componente=lp, ano=a26)
            ],
            "fk_revista_componente_ano": [
                lambda: Revista.objects.create(projeto=self.projeto, componente=lp27, ano=a26)
            ],
            "fk_revista_fasciculo_revista_ano": [fasciculo(ano=a27), fasciculo(componente=self.mt)],
            "fk_revista_fasciculo_template_ano": [
                lambda: self.escolher(self.t_mt),  # componente
                lambda: self.escolher(self.t_lp27),  # ano
                lambda: self.escolher(self.t_lp_f2),  # F2 num fascículo F1
            ],
            "fk_revista_secao_fasciculo_template": [secao(self.t_lp_b, self.v_lp_b)],
            "fk_revista_secao_versao_template": [secao(self.t_lp, self.v_mt)],
        }
        self.assertEqual(set(casos), set(FKS_COMPOSTAS))
        self.escolher(self.t_lp)
        for fk, acoes in casos.items():
            for i, acao in enumerate(acoes):
                with self.subTest(fk=fk, caso=i):
                    self.recusa(acao, fk)

    def test_svg_sem_hash(self):
        r = Revista.objects.get(pk=self.rf.revista_id)
        self.recusa(lambda: Revista.objects.filter(pk=r.pk).update(svg_f2="f2/x.svg"), "revista_svg_f2_com_hash")


class TemplateVersaoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        ano = Ano.objects.create(ano=2026)
        comp = Componente.objects.create(ano=ano, codigo="LP", nome="LP")
        cls.t = Template.objects.create(ano=ano, componente=comp, fasciculo="F2", nome="Padrão")
        cls.v = TemplateVersao.objects.create(template=cls.t, numero=1, texto="## passo1\n")

    def test_save_recusa_update(self):
        self.v.texto = "outro"
        with self.assertRaises(ValueError):
            self.v.save()

    def recusa_no_banco(self, acao):
        with self.assertRaisesMessage(IntegrityError, "template_versao_so_insert"), transaction.atomic():
            acao()

    def test_banco_recusa_update_e_delete(self):
        v = self.v
        casos = {
            "update": lambda: TemplateVersao.objects.filter(pk=v.pk).update(texto="outro"),
            "bulk_update": lambda: TemplateVersao.objects.bulk_update(
                [TemplateVersao(pk=v.pk, template=self.t, numero=1, texto="outro")], ["texto"]
            ),
            # _state.adding=True: o save() do modelo deixa passar, o Django tenta UPDATE.
            "save com pk": lambda: TemplateVersao(
                pk=v.pk, template=self.t, numero=1, texto="outro"
            ).save(),
            "delete": lambda: TemplateVersao.objects.filter(pk=v.pk).delete(),
        }
        for nome, acao in casos.items():
            with self.subTest(caso=nome):
                self.recusa_no_banco(acao)
        self.assertEqual(TemplateVersao.objects.get(pk=v.pk).texto, "## passo1\n")


class VariaveisTest(TestCase):
    def test_cada_variavel_nao_automatica_e_coluna_de_projeto(self):
        for v in VARIAVEIS:
            if not v.automatica:
                with self.subTest(v=v.nome):
                    self.assertEqual(Projeto._meta.get_field(v.nome).get_internal_type(), "TextField")
