"""S11b2: texto por seção na revista (cópia, aviso com diff, descartar, troca de template)."""

from django.urls import reverse

from nucleo.admin.bloqueio import CAMPO_SESSAO
from nucleo.models import Bloqueio, RevistaFasciculo, RevistaSecao, Template, TemplateVersao
from nucleo.servicos.resolver import carregar, hash_validado, resolver, secoes_desatualizadas
from nucleo.tests.test_admin_projeto import Base, mensagens
from nucleo.tests.test_resolver import F1

INTRO = "secao__F1__introducao"


class TextosTest(Base):
    def setUp(self):
        super().setUp()
        self.rev = self.go["LP"]
        self.url = reverse("admin:nucleo_revista_change", args=[self.rev.pk])
        self.rf = RevistaFasciculo.objects.get(revista=self.rev, fasciculo="F1")

    def abrir(self):
        Bloqueio.objects.filter(usuario=self.ped).delete()  # o pagehide da carga anterior
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        return r

    def postar(self, aberta=None, **troca):
        """POST do change form como o navegador o mandaria a partir da página `aberta`, com `troca`."""
        aberta = aberta or self.abrir()
        form = aberta.context["adminform"].form
        dados = {CAMPO_SESSAO: aberta.context["bloqueio"]["sessao"]}
        for n, campo in form.fields.items():
            valor = form.initial.get(n, campo.initial)
            if n.startswith(("secao__", "versao__")):
                dados[n] = valor
                if campo.show_hidden_initial:
                    dados[f"initial-{n}"] = valor
        rfs = RevistaFasciculo.objects.filter(revista=self.rev).order_by("pk")
        dados.update({"revistafasciculo_set-TOTAL_FORMS": len(rfs), "revistafasciculo_set-INITIAL_FORMS": len(rfs)})
        for i, rf in enumerate(rfs):
            dados.update({f"revistafasciculo_set-{i}-id": rf.pk, f"revistafasciculo_set-{i}-template": rf.template_id})
        dados.update(troca)
        return self.client.post(self.url, dados, follow=True)

    def nova_versao(self, texto):
        atual = TemplateVersao.objects.filter(template=self.rf.template).order_by("-numero").first()
        return TemplateVersao.objects.create(template=self.rf.template, numero=atual.numero + 1, texto=texto)

    def secao_resolvida(self, id_):
        return next(s for s in resolver(carregar(self.rev.pk))["f1"]["secoes"] if s["id"] == id_)

    def test_copia_so_na_secao_editada_e_hash_muda(self):
        antes = hash_validado(carregar(self.rev.pk))
        r = self.postar(**{INTRO: "Meu **texto** de {{parceiro}}."})
        self.assertIn("Textos do F1 salvos: introducao.", mensagens(r))
        copia = RevistaSecao.objects.get()
        self.assertEqual((copia.revista_fasciculo, copia.secao), (self.rf, "introducao"))
        self.assertEqual(copia.texto, "Meu **texto** de {{parceiro}}.")
        self.assertEqual(copia.template_versao.numero, 1)
        self.assertIn("<strong>texto</strong> de GO", self.secao_resolvida("introducao")["corpo"])
        self.assertEqual(self.secao_resolvida("introducao")["titulo"], "Análise de GO")  # título do template
        self.assertNotEqual(hash_validado(carregar(self.rev.pk)), antes)  # o Validado cai

    def test_texto_igual_ao_template_nao_cria_copia(self):
        # Corpo de 2 parágrafos: o navegador devolve \r\n; espaço nas pontas some como no template.
        self.nova_versao(F1.replace("Fim.", "A.\n\nB."))
        self.postar(**{"secao__F1__fechamento": "A.\r\n\r\nB.\r\n", INTRO: "  Texto **{{nome_projeto}}**.  "})
        self.assertFalse(RevistaSecao.objects.exists())

    def test_corpo_invalido_nao_grava(self):
        r = self.postar(**{INTRO: "Oi {{x}}.\n\n# Título"})
        erros = str(r.context["adminform"].form.errors[INTRO])
        self.assertIn("{{x}}", erros)
        self.assertIn("título (#)", erros)
        r = self.postar(**{INTRO: ""})
        self.assertIn("corpo vazio", str(r.context["adminform"].form.errors[INTRO]))
        self.assertFalse(RevistaSecao.objects.exists())

    def test_aviso_diff_manter_e_descartar(self):
        self.postar(**{INTRO: "Meu texto."})
        self.nova_versao(F1.replace("Fim.", "Fim novo."))  # só o fechamento mudou: sem aviso
        self.assertNotContains(self.abrir(), "Seções desatualizadas")
        self.nova_versao(F1.replace("Texto **{{nome_projeto}}**.", "Texto novo."))
        aberta = self.abrir()
        self.assertContains(aberta, "Seções desatualizadas: introducao.")
        self.assertContains(aberta, "Template novo")  # diff lado a lado
        self.assertContains(aberta, "novo.</span>")  # o diff marca a troca
        self.assertIn("manter__F1__introducao", aberta.context["adminform"].form.fields)

        # Manter meu texto: a cópia passa a sair da versão mostrada; o aviso some.
        self.postar(aberta, manter__F1__introducao="on")
        self.assertEqual(RevistaSecao.objects.get().template_versao.numero, 3)
        self.assertEqual(secoes_desatualizadas(self.rev), [])
        self.assertEqual(RevistaSecao.objects.get().texto, "Meu texto.")

        # Descartar: volta ao texto do template ao vivo.
        r = self.postar(descartar__F1__introducao="on")
        self.assertFalse(RevistaSecao.objects.exists())
        self.assertIn("Texto novo.", self.secao_resolvida("introducao")["corpo"])
        self.assertNotContains(r, "Seções desatualizadas")

    def test_editar_e_descartar_juntos_e_erro(self):
        self.postar(**{INTRO: "Meu texto."})
        r = self.postar(**{INTRO: "Outro.", "descartar__F1__introducao": "on"})
        self.assertIn("escolha um dos dois", str(r.context["adminform"].form.errors[INTRO]))
        self.assertEqual(RevistaSecao.objects.get().texto, "Meu texto.")

    def test_versao_nova_entre_abrir_e_salvar_continua_avisando(self):
        aberta = self.abrir()
        self.nova_versao(F1.replace("Texto **{{nome_projeto}}**.", "Texto novo."))
        self.postar(aberta, **{INTRO: "Meu texto."})
        self.assertEqual(RevistaSecao.objects.get().template_versao.numero, 1)  # a versão que a pessoa viu
        self.assertEqual([c.secao for c in secoes_desatualizadas(self.rev)], ["introducao"])

    def test_troca_de_template_exige_confirmacao_e_descarta_copias(self):
        self.postar(**{INTRO: "Meu texto."})
        outro = Template.objects.create(ano=self.ano, componente=self.lp, fasciculo="F1", nome="Outro")
        TemplateVersao.objects.create(template=outro, numero=1, texto=F1.replace("Fim.", "Outro fim."))
        i = list(RevistaFasciculo.objects.filter(revista=self.rev).order_by("pk")).index(self.rf)
        campo = f"revistafasciculo_set-{i}-template"

        r = self.postar(**{campo: outro.pk})
        self.assertContains(r, "cópias de seção: introducao")
        self.assertContains(r, "digite “descartar 1 cópia”")
        r = self.postar(**{campo: outro.pk, f"revistafasciculo_set-{i}-confirmacao": "descartar 2 cópias"})
        self.assertContains(r, "Este fascículo tem textos editados")
        self.assertEqual(RevistaFasciculo.objects.get(pk=self.rf.pk).template, self.templates["LP", "F1"])
        self.assertTrue(RevistaSecao.objects.exists())

        # Confirmado: na mesma transação apaga as cópias e troca; o texto editado junto é ignorado.
        r = self.postar(**{campo: outro.pk, f"revistafasciculo_set-{i}-confirmacao": " Descartar  1 cópia", INTRO: "x"})
        self.assertEqual(RevistaFasciculo.objects.get(pk=self.rf.pk).template, outro)
        self.assertFalse(RevistaSecao.objects.exists())
        self.assertIn("Textos do F1 não salvos: o template do F1 foi trocado.", mensagens(r))
        self.assertIn("Outro fim.", self.secao_resolvida("fechamento")["corpo"])

    def test_impresso_so_le_os_textos(self):
        self.postar(**{INTRO: "Meu texto."})
        self.client.force_login(self.imp)
        r = self.client.get(self.url)
        self.assertNotIn(INTRO, r.context["adminform"].form.fields)
        self.assertContains(r, "Meu texto.")
        self.assertEqual(self.client.post(self.url, {INTRO: "y"}).status_code, 403)
        self.assertEqual(RevistaSecao.objects.get().texto, "Meu texto.")
