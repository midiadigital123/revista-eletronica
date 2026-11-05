"""Abrir ano (S16): copia os cadastros do ano anterior, sem cortes nem projetos (D-119)."""
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, TransactionTestCase

from nucleo.models import (
    Ano, Componente, CorPadrao, Corte, Descritor, Etapa, Matriz, MatrizEtapaCC, Parceiro,
    ParceiroAno, Projeto, Tarefa, Template, TemplateVersao,
)
from nucleo.servicos.abrir_ano import AnoRecusado, abrir_ano

COPIADOS = [Etapa, Componente, CorPadrao, Matriz, MatrizEtapaCC, Descritor, Tarefa, Template]
NAO_COPIADOS = [ParceiroAno, Corte, Projeto]
FILTRO_ANO = {
    MatrizEtapaCC: "ano__ano", Descritor: "matriz_etapa_cc__ano__ano",
    Tarefa: "descritor__matriz_etapa_cc__ano__ano", TemplateVersao: "template__ano__ano",
}  # fmt: skip
MOTIVO = "abrir ano 2027 a partir de 2026"


def do_ano(modelo, ano):
    return modelo.objects.filter(**{FILTRO_ANO.get(modelo, "ano__ano"): ano})


def contagens(ano):
    """{modelo: nº de linhas do ano} para os modelos copiados e os que não podem ser."""
    return {m.__name__: do_ano(m, ano).count() for m in COPIADOS + NAO_COPIADOS + [TemplateVersao]}


def mecs(ano):
    return set(
        do_ano(MatrizEtapaCC, ano).values_list(
            "matriz__nome", "etapa__codigo", "componente__codigo", "passo"
        )
    )


def templates(ano):
    return set(do_ano(Template, ano).values_list("componente__codigo", "fasciculo", "nome"))


class AbrirAnoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("carregar_cadastros", "--ano", "2026", stdout=StringIO())
        call_command("carregar_templates", "--ano", "2026", stdout=StringIO())
        a26 = Ano.objects.get(ano=2026)
        cls.usuario = get_user_model().objects.create_user("pedagogica")
        etapa = {e.codigo: e for e in Etapa.objects.filter(ano=a26)}
        cc = {c.codigo: c for c in Componente.objects.filter(ano=a26)}
        comunitaria = Matriz.objects.create(ano=a26, nome="Comunitária")
        excecao = Matriz.objects.create(ano=a26, nome="Exceção", duplicada_de=comunitaria)
        for matriz, e, c, passo in (
            (comunitaria, "5EF", "LP", 25), (comunitaria, "9EF", "MT", 50),
            (comunitaria, "5EF", "MT", None), (excecao, "9EF", "LP", 30),
        ):  # fmt: skip
            mec = MatrizEtapaCC.objects.create(
                matriz=matriz, etapa=etapa[e], componente=cc[c], ano=a26, passo=passo
            )
            for i in (1, 2):
                d = Descritor.objects.create(
                    matriz_etapa_cc=mec, codigo=f"D0{i}", descricao="lê", ordem=i,
                    prerequisitos=["x"],
                )  # fmt: skip
                Tarefa.objects.create(descritor=d, inicio=100, fim=125, texto="t", ordem=1)
                Tarefa.objects.create(descritor=d, inicio=125, fim=150, texto="u", ordem=2)
        cls.template = Template.objects.get(ano=a26, componente=cc["LP"], fasciculo="F1")
        TemplateVersao.objects.create(
            template=cls.template, numero=2, texto="versão 2", criada_por=cls.usuario
        )
        pa = ParceiroAno.objects.create(parceiro=Parceiro.objects.create(nome="GOIÁS"), ano=a26)
        Corte.objects.create(parceiro_ano=pa, etapa=etapa["5EF"], componente=cc["LP"], ano=a26, valores=[200])
        Projeto.objects.create(parceiro_ano=pa, ano=a26, nome="GOIÁS - NOME DO PROJETO")

    def test_copia_cadastros_com_mesmas_contagens(self):
        antes = contagens(2026)
        novo, origem = abrir_ano(2027, usuario=self.usuario)
        self.assertEqual((novo.ano, origem.ano), (2027, 2026))
        depois = contagens(2027)
        for m in COPIADOS:
            self.assertEqual(depois[m.__name__], antes[m.__name__], m.__name__)
        self.assertEqual(depois["TemplateVersao"], antes["Template"])  # só a última vira a 1
        self.assertEqual(contagens(2026), antes)  # origem intacta
        self.assertEqual(depois["Tarefa"], 16)

    def test_copia_nome_e_cor_dos_padroes(self):  # D-175
        CorPadrao.objects.filter(ano__ano=2026, padrao=1).update(nome="Abaixo do básico")
        abrir_ano(2027, usuario=self.usuario)
        self.assertEqual(
            list(do_ano(CorPadrao, 2027).order_by("padrao").values_list("cor", "nome")),
            list(do_ano(CorPadrao, 2026).order_by("padrao").values_list("cor", "nome")),
        )
        self.assertEqual(do_ano(CorPadrao, 2027).get(padrao=1).nome, "Abaixo do básico")

    def test_mapa_de_ids_preserva_mec_e_templates(self):
        abrir_ano(2027)
        self.assertEqual(len(mecs(2026)), 4)
        self.assertEqual(mecs(2027), mecs(2026))
        self.assertEqual(templates(2027), templates(2026))
        self.assertEqual({c for c, _, _ in templates(2027)}, {"LP", "MT"})
        # Cada MEC de 2026 continua com os seus descritores e tarefas (nada migrou para 2027).
        for m in COPIADOS[4:7]:
            self.assertEqual(do_ano(m, 2026).count(), do_ano(m, 2027).count(), m.__name__)
        self.assertEqual(do_ano(Descritor, 2026).count(), 8)
        self.assertEqual(do_ano(Tarefa, 2026).count(), 16)

    def test_nao_copia_cortes_parceiros_nem_projetos(self):
        abrir_ano(2027)
        depois = contagens(2027)
        for m in NAO_COPIADOS:
            self.assertEqual(depois[m.__name__], 0, m.__name__)

    def test_matriz_aponta_para_a_origem_e_preserva_conteudo(self):
        abrir_ano(2027)
        for m in Matriz.objects.filter(ano__ano=2027):
            self.assertEqual((m.duplicada_de.ano.ano, m.duplicada_de.nome), (2026, m.nome))
        mec = MatrizEtapaCC.objects.get(ano__ano=2027, matriz__nome="Comunitária", etapa__codigo="5EF",
                                        componente__codigo="LP")
        self.assertEqual(
            list(Tarefa.objects.filter(descritor__matriz_etapa_cc=mec)
                 .order_by("descritor__ordem", "ordem")
                 .values_list("descritor__codigo", "descritor__prerequisitos", "inicio", "texto")),
            [("D01", ["x"], 100, "t"), ("D01", ["x"], 125, "u"),
             ("D02", ["x"], 100, "t"), ("D02", ["x"], 125, "u")],
        )  # fmt: skip

    def test_template_nasce_com_a_ultima_versao_como_1(self):
        abrir_ano(2027, usuario=self.usuario)
        t = Template.objects.get(ano__ano=2027, componente__codigo="LP", fasciculo="F1")
        (v,) = t.templateversao_set.all()
        self.assertEqual((v.numero, v.texto, v.criada_por), (1, "versão 2", self.usuario))
        self.assertEqual(t.origem, self.template.origem)

    def test_fks_compostas_de_ano_validas(self):
        novo, _ = abrir_ano(2027)
        for mec in MatrizEtapaCC.objects.filter(ano=novo).select_related("matriz", "etapa", "componente"):
            self.assertEqual({mec.matriz.ano_id, mec.etapa.ano_id, mec.componente.ano_id}, {novo.pk})
        for t in Template.objects.filter(ano=novo).select_related("componente"):
            self.assertEqual(t.componente.ano_id, novo.pk)

    def test_historico_uma_linha_por_copia_com_usuario(self):
        abrir_ano(2027, usuario=self.usuario)
        for modelo in COPIADOS:
            hist = modelo.history.filter(history_change_reason=MOTIVO)
            self.assertEqual(hist.count(), do_ano(modelo, 2027).count(), modelo.__name__)
            self.assertFalse(hist.exclude(history_user=self.usuario).exists(), modelo.__name__)
        self.assertEqual(Ano.history.get(history_change_reason=MOTIVO).history_user, self.usuario)

    def test_historico_sem_usuario(self):
        abrir_ano(2027)
        for modelo in COPIADOS + [Ano]:
            hist = modelo.history.filter(history_change_reason=MOTIVO)
            self.assertTrue(hist.exists(), modelo.__name__)
            self.assertFalse(hist.filter(history_user__isnull=False).exists(), modelo.__name__)
        self.assertFalse(do_ano(TemplateVersao, 2027).filter(criada_por__isnull=False).exists())

    def test_falha_no_meio_nao_deixa_nada(self):
        with mock.patch.object(TemplateVersao.objects, "bulk_create", side_effect=RuntimeError("falhou")):
            with self.assertRaisesMessage(RuntimeError, "falhou"):
                abrir_ano(2027, usuario=self.usuario)
        self.assertFalse(Ano.objects.filter(ano=2027).exists())
        self.assertEqual(set(contagens(2027).values()), {0})
        for modelo in COPIADOS + [Ano]:
            self.assertFalse(modelo.history.filter(history_change_reason=MOTIVO).exists(), modelo.__name__)

    def test_segunda_execucao_falha_sem_efeito(self):
        abrir_ano(2027)
        antes = contagens(2027)
        with self.assertRaisesMessage(AnoRecusado, "2027 já está aberto"):
            abrir_ano(2027)
        self.assertEqual(contagens(2027), antes)

    def test_ano_existente_mesmo_que_antigo(self):
        with self.assertRaisesMessage(AnoRecusado, "2026 já está aberto"):
            abrir_ano(2026)

    def test_ano_pulado_ou_no_passado_recusado(self):
        for ano in (2028, 20277, 2020):
            with self.assertRaisesMessage(AnoRecusado, "o próximo ano que pode ser aberto é 2027"):
                abrir_ano(ano)
            self.assertFalse(Ano.objects.filter(ano=ano).exists())

    def test_encadeia_anos(self):
        abrir_ano(2027)
        Matriz.objects.create(ano=Ano.objects.get(ano=2027), nome="Só 2027")
        abrir_ano(2028)
        self.assertTrue(Matriz.objects.filter(ano__ano=2028, nome="Só 2027").exists())


class SemAnoTest(TestCase):
    def test_sem_ano_nenhum_recusa_sem_criar(self):
        with self.assertRaisesMessage(AnoRecusado, "nenhum ano anterior a 2027"):
            abrir_ano(2027)
        self.assertFalse(Ano.objects.exists())


class ComandoAbrirAnoTest(TransactionTestCase):
    """Fora de atomic: exercita o caminho com SET TRANSACTION ISOLATION LEVEL REPEATABLE READ."""

    def test_comando_abre_e_recusa_repeticao(self):
        call_command("carregar_cadastros", "--ano", "2026", stdout=StringIO())
        saida = StringIO()
        call_command("abrir_ano", "2027", stdout=saida)
        self.assertIn("2027 aberto a partir de 2026", saida.getvalue())
        self.assertEqual(Etapa.objects.filter(ano__ano=2027).count(), 4)
        with self.assertRaisesMessage(CommandError, "2027 já está aberto"):
            call_command("abrir_ano", "2027", stdout=StringIO())
