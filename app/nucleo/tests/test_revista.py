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
    Parceiro,
    ParceiroAno,
    Projeto,
    Revista,
    RevistaFasciculo,
    RevistaSecao,
    Template,
    TemplateVersao,
)
from nucleo.variaveis import VARIAVEIS


class RecusaRevistaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create(username="pedagogica")
        a26 = cls.a26 = Ano.objects.create(ano=2026)
        a27 = Ano.objects.create(ano=2027)
        cls.lp = Componente.objects.create(ano=a26, codigo="LP", nome="Língua Portuguesa")
        cls.mt = Componente.objects.create(ano=a26, codigo="MT", nome="Matemática")
        lp27 = Componente.objects.create(ano=a27, codigo="LP", nome="Língua Portuguesa")
        cls.e5 = Etapa.objects.create(ano=a26, codigo="5EF", escala_max=500, ordem=2)
        cls.pa = ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome="GO"), ano=a26)
        cls.projeto = Projeto.objects.create(parceiro_ano=cls.pa, ano=a26, nome="GO - NOME DO PROJETO")
        revista = Revista.objects.create(projeto=cls.projeto, componente=cls.lp, ano=a26)
        cls.rf = RevistaFasciculo.objects.create(revista=revista, fasciculo="F1", componente=cls.lp, ano=a26)

        def template(ano, comp, nome):
            t = Template.objects.create(ano=ano, componente=comp, fasciculo="F1", nome=nome)
            return t, TemplateVersao.objects.create(template=t, numero=1, texto="## introducao\n")

        cls.t_lp, cls.v_lp = template(a26, cls.lp, "Padrão")
        cls.t_lp_b, _ = template(a26, cls.lp, "Alternativo")
        cls.t_mt, cls.v_mt = template(a26, cls.mt, "Padrão")
        cls.t_lp27, _ = template(a27, lp27, "Padrão")

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

    def test_svg_sem_hash(self):
        r = Revista.objects.get(pk=self.rf.revista_id)
        self.recusa(lambda: Revista.objects.filter(pk=r.pk).update(svg_f2="f2/x.svg"), "revista_svg_f2_com_hash")


class TemplateVersaoTest(TestCase):
    def test_save_recusa_update(self):
        ano = Ano.objects.create(ano=2026)
        comp = Componente.objects.create(ano=ano, codigo="LP", nome="LP")
        t = Template.objects.create(ano=ano, componente=comp, fasciculo="F2", nome="Padrão")
        v = TemplateVersao.objects.create(template=t, numero=1, texto="## passo1\n")
        v.texto = "outro"
        with self.assertRaises(ValueError):
            v.save()


class VariaveisTest(TestCase):
    def test_cada_variavel_nao_automatica_e_coluna_de_projeto(self):
        for v in VARIAVEIS:
            if not v.automatica:
                with self.subTest(v=v.nome):
                    self.assertEqual(Projeto._meta.get_field(v.nome).get_internal_type(), "TextField")
