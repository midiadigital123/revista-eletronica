"""T07: aviso de impacto ao mudar nome ou cor do padrão do ano (D-076, D-175)."""

from django.urls import reverse

from nucleo.models import CorPadrao, ProjetoCor, Revista
from nucleo.servicos import resolver, validacao
from nucleo.servicos.resolver import carregar
from nucleo.tests.test_admin_projeto import Base, mensagens


def validar(revista):
    Revista.objects.filter(pk=revista.pk).update(hash_validado=resolver.hash_validado(carregar(revista.pk)))


def esta_validada(revista):
    r = carregar(revista.pk)
    return validacao.validada(r, resolver.hash_validado(r))


class PadraoImpactoTest(Base):
    def setUp(self):
        super().setUp()
        self.cp = CorPadrao.objects.get(ano=self.ano, padrao=3)
        self.url = reverse("admin:nucleo_corpadrao_change", args=[self.cp.pk])
        # Só GO LP fica fora pelo nome: os outros 3 não sobrescrevem pd03.
        self.projeto_pe.pd03 = "Adequado PE"
        self.projeto_pe.save()
        validar(self.go["LP"])

    def post(self, follow=False, **troca):
        dados = {"nome": self.cp.nome, "cor": self.cp.cor, **troca}
        return self.client.post(self.url, dados, follow=follow)

    def test_nome_pede_confirmacao_e_lista_validada(self):
        r = self.post(nome="Adequado")
        self.assertEqual(r.status_code, 200)
        form = r.context["adminform"].form
        self.assertEqual(form.afetadas, 2)  # GO LP e GO MT; PE sobrescreve pd03
        self.assertEqual(form.resultado[1], [self.go["LP"]])
        self.assertContains(r, "Confirmo: afeta 2 revista(s) ativa(s); 1 perdem o “Validado”")
        self.assertContains(r, f"Perdem o “Validado”: {self.go['LP']}.")
        self.assertContains(r, "Não salvo: mudar o nome ou a cor do Padrão 3 de 2026 afeta 2 revista(s)")
        self.assertContains(r, 'value="Adequado"')  # o digitado é mantido

    def test_pd_proprio_fora_da_lista(self):
        validar(self.pe["LP"])
        r = self.post(nome="Adequado")
        afetadas, perdem = r.context["adminform"].form.resultado
        self.assertNotIn(self.pe["LP"], afetadas)
        self.assertNotIn(self.pe["LP"], perdem)

    def test_sem_confirmar_nao_grava(self):
        self.post(nome="Adequado")
        self.assertEqual(CorPadrao.objects.get(pk=self.cp.pk).nome, "Padrão 03")
        self.assertTrue(esta_validada(self.go["LP"]))

    def test_confirmado_grava_e_avisa(self):
        r = self.post(follow=True, nome="Adequado", confirmar_impacto="on")
        self.assertEqual(CorPadrao.objects.get(pk=self.cp.pk).nome, "Adequado")
        self.assertFalse(esta_validada(self.go["LP"]))
        aviso = next(m for m in mensagens(r) if "perderam" in m)
        self.assertIn(f"1 revista(s) perderam o “Validado”: {self.go['LP']}.", aviso)
        self.assertIn('href="/painel/2026/?falta=validado"', aviso)

    def test_cor_conta_so_quem_nao_tem_projeto_cor(self):
        ProjetoCor.objects.create(projeto=self.projeto_go, padrao=3, cor="#000000")
        r = self.post(cor="#123456")
        self.assertEqual(set(r.context["adminform"].form.resultado[0]), {self.pe["LP"], self.pe["MT"]})

    def test_n_zero_salva_direto(self):
        self.projeto_go.pd03 = "Adequado GO"
        self.projeto_go.save()
        r = self.post(nome="Adequado")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(CorPadrao.objects.get(pk=self.cp.pk).nome, "Adequado")

    def test_mesmo_valor_nao_pede_confirmacao(self):
        r = self.post()
        self.assertEqual(r.status_code, 302)
        self.assertTrue(esta_validada(self.go["LP"]))

    def test_get_mostra_pior_caso(self):
        r = self.client.get(self.url)
        self.assertContains(r, "Confirmo: afeta 4 revista(s) ativa(s); 1 perdem o “Validado”")

    def test_impresso_ve_sem_checkbox(self):
        self.client.force_login(self.imp)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'name="confirmar_impacto"')
