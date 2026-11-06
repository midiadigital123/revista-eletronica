"""limpar_e2e (D-224): apaga só os "E2E …" que o usuário de teste criou, com o que a cascata gerou."""

from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from nucleo.models import Etapa, Matriz, MatrizEtapaCC, Parceiro, Projeto, Revista, Template, TemplateVersao
from nucleo.servicos.etapa_projeto import criar
from nucleo.tests.test_resolver import Mundo


def criado_por(obj, usuario):
    type(obj).history.filter(id=obj.pk, history_type="+").update(history_user=usuario)


@override_settings(DEBUG=True)
class LimparE2ETest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Mundo.montar(cls)
        User = get_user_model()
        cls.e2e, cls.gente = User.objects.create(username="e2e"), User.objects.create(username="gente")
        Mundo.parceiro(cls, "E2E Lixo X1", [100, 200, 250, 300])
        Mundo.parceiro(cls, "E2E De gente", [100, 200, 250, 300])
        cls.lixo, cls.alheio = Parceiro.objects.get(nome="E2E Lixo X1"), Parceiro.objects.get(nome="E2E De gente")
        criado_por(cls.lixo, cls.e2e)
        criado_por(cls.alheio, cls.gente)
        cls.tpl = Template.objects.create(ano=cls.ano, componente=cls.lp, fasciculo="F1", nome="E2E textos X1")
        TemplateVersao.objects.create(template=cls.tpl, numero=1, texto="## a\nA\n\nx\n")
        criado_por(cls.tpl, cls.e2e)
        cls.mat = Matriz.objects.create(ano=cls.ano, nome="E2E MEC X1")
        criado_por(cls.mat, cls.e2e)

    def rodar(self, *args):
        saida = StringIO()
        call_command("limpar_e2e", *args, stdout=saida, stderr=saida)
        return saida.getvalue()

    def test_apaga_so_o_do_usuario_de_teste_com_a_cascata(self):
        projetos = Projeto.objects.filter(parceiro_ano__parceiro=self.lixo)
        self.assertTrue(Revista.objects.filter(projeto__in=projetos).exists())
        self.assertIn("E2E Lixo X1", self.rodar("--simular"))
        self.assertTrue(Parceiro.objects.filter(pk=self.lixo.pk).exists())  # simular não apaga

        self.assertIn("Apagados: E2E Lixo X1, E2E MEC X1, E2E textos X1", self.rodar())
        self.assertFalse(Matriz.objects.filter(pk=self.mat.pk).exists())
        self.assertFalse(Parceiro.objects.filter(pk=self.lixo.pk).exists())
        self.assertFalse(Template.objects.filter(pk=self.tpl.pk).exists())
        self.assertFalse(TemplateVersao.objects.filter(template_id=self.tpl.pk).exists())
        self.assertTrue(Parceiro.objects.filter(pk=self.alheio.pk).exists())  # "E2E" de outra pessoa fica
        self.assertTrue(Parceiro.objects.filter(nome="GO").exists())

    def test_apaga_etapa_do_projeto_do_parceiro_e2e(self):
        e4 = Etapa.objects.create(ano=self.ano, codigo="4EF", escala_max=500, ordem=4)
        base = MatrizEtapaCC.objects.get(matriz=self.matriz, etapa=self.e9, componente=self.lp)
        mec = criar(Projeto.objects.get(parceiro_ano__parceiro=self.lixo), e4, self.lp, self.e2e, base=base)
        self.assertIn("Apagados: E2E Lixo X1", self.rodar())
        self.assertFalse(MatrizEtapaCC.objects.filter(pk=mec.pk).exists())
        self.assertFalse(Parceiro.objects.filter(pk=self.lixo.pk).exists())
        self.assertTrue(MatrizEtapaCC.objects.filter(pk=base.pk).exists())  # a base é da matriz real

    @override_settings(DEBUG=False)
    def test_recusa_sem_debug(self):
        with self.assertRaises(CommandError):
            self.rodar()
