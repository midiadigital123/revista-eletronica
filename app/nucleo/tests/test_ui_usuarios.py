"""Usuários na tela B (S9): cada regra de `nucleo/usuarios.py` contra a tela B e contra o admin
(o admin também tem os testes de `test_admin_cadastro.PerfisTest`)."""

from unittest import mock

from django.contrib.auth.models import Group, User
from django.test import Client, override_settings
from django.urls import reverse

from nucleo.tests.test_admin_cadastro import Base
from nucleo.tests.test_resolver import usuario

LISTA = reverse("ui_usuarios")
NOVO = reverse("ui_usuarios_novo")
SENHA_BOA = "outra-senha-longa-123"


def grupo(nome):
    return Group.objects.get(name=nome)


def grupos_de(u):
    return sorted(u.groups.values_list("name", flat=True))


class UsuariosUiTest(Base):
    def setUp(self):
        self.eu = usuario("eu-admin", "Admin")
        self.client.force_login(self.eu)
        self.ped = usuario("ped", "Pedagógica")

    # B
    def mudar_grupo(self, alvo, nome):
        return self.client.post(reverse("ui_usuarios_grupo", args=[alvo.pk]), {"grupo": grupo(nome).pk})

    def ativo(self, alvo, acao):
        return self.client.post(reverse("ui_usuarios_ativo", args=[alvo.pk]), {"acao": acao})

    # admin
    def admin_post(self, alvo, **campos):
        dados = {"username": alvo.username, "is_active": "on", **campos}
        return self.client.post(reverse("admin:auth_user_change", args=[alvo.pk]), dados)

    def admin_form(self, alvo):
        return self.client.get(reverse("admin:auth_user_change", args=[alvo.pk])).context["adminform"].form

    def test_lista_e_entrada_no_cabecalho(self):
        resp = self.client.get(LISTA)
        self.assertContains(resp, ">ped<")
        self.assertContains(resp, f'href="{LISTA}" aria-current="page">Usuários</a>')
        self.assertContains(resp, "Nunca entrou")
        self.assertContains(self.client.get(reverse("ui_anos")), f'href="{LISTA}"')

    def test_so_atribui_pedagogica_e_midias(self):
        resp = self.client.get(LISTA)
        self.assertEqual({g.name for g in resp.context["grupos"]}, {"Pedagógica", "Mídias Digitais"})
        self.assertNotContains(resp, f'<option value="{grupo("Impresso").pk}"')
        for nome in ("Impresso", "Admin"):
            self.mudar_grupo(self.ped, nome)
            self.assertEqual(grupos_de(self.ped), ["Pedagógica"], nome)
        self.assertRedirects(self.mudar_grupo(self.ped, "Mídias Digitais"), LISTA)
        self.assertEqual(grupos_de(self.ped), ["Mídias Digitais"])
        resp = self.client.post(NOVO, self.dados_novo("nova-imp", grupo=grupo("Impresso").pk))
        self.assertEqual(resp.status_code, 200)  # erro no form, nada criado
        self.assertFalse(User.objects.filter(username="nova-imp").exists())
        # admin
        self.assertEqual(set(self.admin_form(self.ped).fields["groups"].queryset.values_list("name", flat=True)),
                         {"Pedagógica", "Mídias Digitais"})  # fmt: skip
        self.admin_post(self.ped, groups=[grupo("Impresso").pk])
        self.assertEqual(grupos_de(self.ped), ["Mídias Digitais"])

    def test_superusuario_fora_da_lista(self):
        self.assertNotContains(self.client.get(LISTA), ">root<")
        for nome in ("ui_usuarios_grupo", "ui_usuarios_ativo", "ui_usuarios_senha", "ui_usuarios_link"):
            self.assertEqual(self.client.post(reverse(nome, args=[self.root.pk]), {"acao": "desativar"}).status_code, 404, nome)
        self.assertEqual(self.client.get(reverse("ui_usuarios_senha", args=[self.root.pk])).status_code, 404)
        self.root.refresh_from_db()
        self.assertTrue(self.root.is_active)
        # admin
        self.assertNotContains(self.client.get(reverse("admin:auth_user_changelist")), ">root<")
        self.assertEqual(self.client.get(reverse("admin:auth_user_change", args=[self.root.pk])).status_code, 302)

    def test_nao_muda_os_proprios_grupos_nem_se_desativa(self):
        resp = self.client.get(LISTA)
        self.assertNotContains(resp, 'aria-label="Desativar eu-admin"')
        self.assertNotContains(resp, f'id="grupo-{self.eu.pk}"')
        self.assertContains(resp, 'aria-label="Redefinir senha de eu-admin"')
        self.assertEqual(self.mudar_grupo(self.eu, "Pedagógica").status_code, 403)
        self.assertEqual(self.ativo(self.eu, "desativar").status_code, 403)
        self.eu.refresh_from_db()
        self.assertEqual(grupos_de(self.eu), ["Admin"])
        self.assertTrue(self.eu.is_active)
        # admin
        form = self.admin_form(self.eu)
        self.assertNotIn("groups", form.fields)
        self.assertNotIn("is_active", form.fields)

    def test_nao_altera_quem_tem_grupo_fora_dos_permitidos(self):
        """Impresso: só vê. Redefinir a senha e entrar como ele daria marcar_impressa ao Admin."""
        imp = usuario("imp", "Impresso")
        resp = self.client.get(LISTA)
        self.assertNotContains(resp, f'id="grupo-{imp.pk}"')
        for rotulo in ("Desativar imp", "Redefinir senha de imp", "Link de acesso de imp"):
            self.assertNotContains(resp, f'aria-label="{rotulo}"')
        senha = reverse("ui_usuarios_senha", args=[imp.pk])
        self.assertEqual(self.mudar_grupo(imp, "Pedagógica").status_code, 403)
        self.assertEqual(self.ativo(imp, "desativar").status_code, 403)
        self.assertEqual(self.client.get(senha).status_code, 403)
        self.assertEqual(self.client.post(senha, {"new_password1": SENHA_BOA, "new_password2": SENHA_BOA}).status_code, 403)
        self.assertEqual(self.client.post(reverse("ui_usuarios_link", args=[imp.pk])).status_code, 403)
        imp.refresh_from_db()
        self.assertEqual(grupos_de(imp), ["Impresso"])
        self.assertTrue(imp.is_active)
        self.assertTrue(imp.check_password("x"))
        # admin
        self.assertEqual(self.admin_post(imp, is_active="").status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:auth_user_password_change", args=[imp.pk])).status_code, 403)

    def test_nao_edita_outro_admin(self):
        outro = usuario("outro-admin", "Admin")
        resp = self.client.get(LISTA)
        self.assertContains(resp, ">outro-admin<")  # só vê
        for rotulo in ("Desativar outro-admin", "Redefinir senha de outro-admin", "Link de acesso de outro-admin"):
            self.assertNotContains(resp, f'aria-label="{rotulo}"')
        self.assertNotContains(resp, f'id="grupo-{outro.pk}"')
        self.assertContains(resp, "Só o superusuário altera")
        senha = reverse("ui_usuarios_senha", args=[outro.pk])
        self.assertEqual(self.mudar_grupo(outro, "Pedagógica").status_code, 403)
        self.assertEqual(self.ativo(outro, "desativar").status_code, 403)
        self.assertEqual(self.client.get(senha).status_code, 403)
        self.assertEqual(self.client.post(senha, {"new_password1": SENHA_BOA, "new_password2": SENHA_BOA}).status_code, 403)
        self.assertEqual(self.client.post(reverse("ui_usuarios_link", args=[outro.pk])).status_code, 403)
        outro.refresh_from_db()
        self.assertTrue(outro.is_active)
        self.assertTrue(outro.check_password("x"))
        # admin
        self.assertEqual(self.admin_post(outro, is_active="").status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:auth_user_password_change", args=[outro.pk])).status_code, 403)

    def dados_novo(self, nome, **extra):
        return {"username": nome, "first_name": "Ana", "last_name": "Lima", "email": "ana@exemplo.org",
                "grupo": grupo("Mídias Digitais").pk, "password1": SENHA_BOA, "password2": SENHA_BOA, **extra}  # fmt: skip

    def test_novo_nasce_staff_e_sem_privilegio_do_post(self):
        self.assertContains(self.client.get(NOVO), 'name="password1"')
        forjado = {"is_superuser": "on", "is_staff": "", "user_permissions": "1", "groups": grupo("Admin").pk}
        resp = self.client.post(NOVO, self.dados_novo("ana", **forjado), follow=True)
        self.assertRedirects(resp, LISTA)
        self.assertContains(resp, "Usuário ana criado no grupo Mídias Digitais.")
        ana = User.objects.get(username="ana")
        self.assertTrue(ana.is_staff)
        self.assertFalse(ana.is_superuser)
        self.assertFalse(ana.user_permissions.exists())
        self.assertEqual(grupos_de(ana), ["Mídias Digitais"])
        self.assertEqual((ana.get_full_name(), ana.email), ("Ana Lima", "ana@exemplo.org"))
        self.assertTrue(ana.check_password(SENHA_BOA))
        # validadores do Django: senha curta e parecida com o nome não passa; nome repetido também não
        resp = self.client.post(NOVO, self.dados_novo("bia", password1="bia", password2="bia"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'class="erro"')
        self.assertEqual(self.client.post(NOVO, self.dados_novo("ana")).status_code, 200)
        self.assertFalse(User.objects.filter(username="bia").exists())
        # admin
        self.client.post(reverse("admin:auth_user_add"), {"username": "nova", "password1": SENHA_BOA, "password2": SENHA_BOA,
                                                          "usable_password": "true"})  # fmt: skip
        self.assertTrue(User.objects.get(username="nova").is_staff)

    def test_mudar_grupo_ignora_campos_de_privilegio(self):
        self.client.post(reverse("ui_usuarios_grupo", args=[self.ped.pk]),
                         {"grupo": grupo("Mídias Digitais").pk, "is_superuser": "on", "is_staff": ""})  # fmt: skip
        self.ped.refresh_from_db()
        self.assertEqual((self.ped.is_superuser, self.ped.is_staff), (False, True))

    def test_desativa_e_o_admin_do_django_nunca_apaga(self):
        self.assertRedirects(self.ativo(self.ped, "desativar"), LISTA)
        self.ped.refresh_from_db()
        self.assertFalse(self.ped.is_active)
        self.assertContains(self.client.get(LISTA), "Desativado")
        self.assertEqual(self.ativo(self.ped, "apagar").status_code, 404)
        self.assertRedirects(self.ativo(self.ped, "ativar"), LISTA)
        self.ped.refresh_from_db()
        self.assertTrue(self.ped.is_active)
        # admin: nem o superusuário apaga
        for quem in (self.eu, self.root):
            self.client.force_login(quem)
            self.assertEqual(self.client.get(reverse("admin:auth_user_delete", args=[self.ped.pk])).status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.ped.pk).exists())

    def excluir(self, alvo, codigo=None):
        return self.client.post(reverse("ui_usuarios_excluir", args=[alvo.pk]), {"confirmacao": codigo or alvo.username}, follow=True)

    def test_exclui_quem_nao_tem_rastro(self):
        """D-218: criado por engano, nunca registrou nada: sai com confirmação forte."""
        novo = usuario("criado-por-engano", "Mídias Digitais")
        self.assertContains(self.client.get(LISTA), 'aria-label="Excluir criado-por-engano"')
        resp = self.client.get(reverse("ui_usuarios_excluir", args=[novo.pk]))
        self.assertContains(resp, "Nada usa isto.")
        self.assertContains(resp, "data-confirmado")
        self.assertContains(self.excluir(novo, "outro-nome"), "o código não confere")
        self.assertTrue(User.objects.filter(pk=novo.pk).exists())
        resp = self.excluir(novo)
        self.assertRedirects(resp, LISTA)
        self.assertContains(resp, "Exclusão feita: o usuário criado-por-engano.")
        self.assertFalse(User.objects.filter(pk=novo.pk).exists())

    def test_com_rastro_so_desativa(self):
        """Quem editou algo fica: excluir apagaria o autor do histórico (history_user é SET_NULL)."""
        from nucleo.models import Ano

        ano = Ano.objects.first() or Ano.objects.create(ano=2099)
        ano._history_user = self.ped
        ano.save()
        resp = self.client.get(reverse("ui_usuarios_excluir", args=[self.ped.pk]))
        self.assertContains(resp, "Edições registradas no histórico")
        self.assertContains(resp, "Para tirar o acesso, desative")
        self.assertNotContains(resp, "data-confirmado")
        self.assertEqual(self.excluir(self.ped).status_code, 200)
        self.assertTrue(User.objects.filter(pk=self.ped.pk).exists())

    def test_excluir_corrida_com_rastro_novo(self):
        """O rastro que surge entre a página e o POST é visto de novo com a linha travada."""
        with mock.patch("nucleo.usuarios.rastros", side_effect=[[], [("revistas que validou", 1)]]):
            resp = self.excluir(self.ped)
        self.assertContains(resp, "Nada foi excluído: ped passou a ter registro")
        self.assertTrue(User.objects.filter(pk=self.ped.pk).exists())

    def test_excluir_segue_a_regra_de_desativar(self):
        url = lambda u: reverse("ui_usuarios_excluir", args=[u.pk])  # noqa: E731
        for alvo in (usuario("imp", "Impresso"), usuario("outro-admin", "Admin"), self.eu):
            self.assertEqual(self.client.get(url(alvo)).status_code, 403, alvo)
            self.assertEqual(self.excluir(alvo).status_code, 403, alvo)
            self.assertNotContains(self.client.get(LISTA), f'aria-label="Excluir {alvo.username}"')
        self.assertEqual(self.client.get(url(self.root)).status_code, 404)
        self.assertEqual(User.objects.filter(username__in=["imp", "outro-admin", "eu-admin", "root"]).count(), 4)

    def test_redefinir_senha(self):
        url = reverse("ui_usuarios_senha", args=[self.ped.pk])
        self.assertContains(self.client.get(url), 'name="new_password1"')
        resp = self.client.post(url, {"new_password1": "123", "new_password2": "123"})
        self.assertEqual(resp.status_code, 200)
        self.ped.refresh_from_db()
        self.assertTrue(self.ped.check_password("x"))
        self.assertRedirects(self.client.post(url, {"new_password1": SENHA_BOA, "new_password2": SENHA_BOA}), LISTA)
        self.ped.refresh_from_db()
        self.assertTrue(self.ped.check_password(SENHA_BOA))
        # a própria senha: segue logado
        meu = reverse("ui_usuarios_senha", args=[self.eu.pk])
        self.assertRedirects(self.client.post(meu, {"new_password1": SENHA_BOA, "new_password2": SENHA_BOA}), LISTA)
        self.assertEqual(self.client.get(LISTA).status_code, 200)

    def test_link_de_acesso_define_a_senha_fora_do_admin(self):
        url = reverse("ui_usuarios_link", args=[self.ped.pk])
        self.assertContains(self.client.get(LISTA), 'aria-label="Link de acesso de ped"')
        self.assertEqual(self.client.get(url).status_code, 405)  # o link só sai na resposta do POST
        resp = self.client.post(url)
        self.assertContains(resp, "vale 3 dias e funciona uma vez")
        self.assertContains(resp, "A senha atual de ped continua valendo")  # `usuario()` cria com senha
        self.assertContains(resp, "Depois, entre por http://testserver/conta/entrar/")
        link = resp.context["link"]
        self.assertTrue(link.startswith("http://testserver/conta/senha/"), link)

        anonimo = Client()
        r = anonimo.get(link, follow=True)  # o Django troca o token por um da sessão
        self.assertContains(r, "Criar senha")
        self.assertNotContains(r, "Administração do Django")
        r = anonimo.post(r.redirect_chain[-1][0], {"new_password1": SENHA_BOA, "new_password2": SENHA_BOA}, follow=True)
        self.assertContains(r, "Senha criada")
        self.assertNotContains(r, "Administração do Django")
        self.ped.refresh_from_db()
        self.assertTrue(self.ped.check_password(SENHA_BOA))
        r = Client().get(link, follow=True)
        self.assertContains(r, "Este link venceu ou já foi usado")
        self.assertNotContains(r, "Administração do Django")

        self.ativo(self.ped, "desativar")  # inativo: o link não serviria
        self.assertNotContains(self.client.get(LISTA), 'aria-label="Link de acesso de ped"')
        self.assertEqual(self.client.post(url).status_code, 403)

    @override_settings(CSRF_TRUSTED_ORIGINS=["https://revista.exemplo.org"], ALLOWED_HOSTS=["revista.exemplo.org"])
    def test_link_usa_a_origem_https_atras_do_proxy(self):
        """O proxy entrega http ao app; o Origin do navegador traz o https verdadeiro."""
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.eu)
        token = c.get(LISTA, HTTP_HOST="revista.exemplo.org").cookies["csrftoken"].value
        resp = c.post(reverse("ui_usuarios_link", args=[self.ped.pk]), {"csrfmiddlewaretoken": token},
                      HTTP_HOST="revista.exemplo.org", HTTP_ORIGIN="https://revista.exemplo.org")  # fmt: skip
        self.assertTrue(resp.context["link"].startswith("https://revista.exemplo.org/conta/senha/"), resp.context["link"])
        self.assertContains(resp, "https://revista.exemplo.org/conta/entrar/")
        # Origin forjado não passa do CSRF
        resp = c.post(reverse("ui_usuarios_link", args=[self.ped.pk]), {"csrfmiddlewaretoken": token},
                      HTTP_HOST="revista.exemplo.org", HTTP_ORIGIN="https://golpe.exemplo.com")  # fmt: skip
        self.assertEqual(resp.status_code, 403)

    def test_superusuario_atribui_impresso_e_admin(self):
        self.client.force_login(self.root)
        resp = self.client.get(LISTA)
        self.assertEqual({g.name for g in resp.context["grupos"]}, {"Admin", "Pedagógica", "Mídias Digitais", "Impresso"})
        self.assertContains(resp, ">root<")
        self.mudar_grupo(self.ped, "Impresso")
        self.assertEqual(grupos_de(self.ped), ["Impresso"])
        self.mudar_grupo(self.eu, "Pedagógica")  # outro Admin: o superusuário mexe
        self.assertEqual(grupos_de(self.eu), ["Pedagógica"])
        self.client.post(NOVO, self.dados_novo("novo-admin", grupo=grupo("Admin").pk))
        self.assertEqual(grupos_de(User.objects.get(username="novo-admin")), ["Admin"])
        # admin
        self.admin_post(self.ped, groups=[grupo("Admin").pk])
        self.assertEqual(grupos_de(self.ped), ["Admin"])

    def test_sem_gerenciar_usuarios_recebe_403(self):
        alvo = self.ped
        rotas = [("get", LISTA), ("get", NOVO), ("post", NOVO), ("get", reverse("ui_usuarios_senha", args=[alvo.pk]))]
        rotas += [("post", reverse(n, args=[alvo.pk])) for n in ("ui_usuarios_grupo", "ui_usuarios_ativo", "ui_usuarios_senha", "ui_usuarios_link", "ui_usuarios_excluir")]
        for papel in ("Pedagógica", "Mídias Digitais", "Impresso"):
            self.client.force_login(usuario(f"x-{papel}", papel))
            self.assertNotContains(self.client.get(reverse("ui_anos")), f'href="{LISTA}"')
            for metodo, url in rotas:
                dados = {**self.dados_novo("intruso"), "acao": "desativar", "new_password1": SENHA_BOA, "new_password2": SENHA_BOA,
                         "confirmacao": alvo.username}  # fmt: skip
                resp = getattr(self.client, metodo)(url, dados if metodo == "post" else None)
                self.assertEqual(resp.status_code, 403, f"{papel} {metodo} {url}")
        alvo.refresh_from_db()
        self.assertTrue(alvo.is_active)
        self.assertEqual(grupos_de(alvo), ["Pedagógica"])
        self.assertFalse(User.objects.filter(username="intruso").exists())
        self.client.logout()
        self.assertEqual(self.client.get(LISTA).status_code, 302)  # anônimo vai ao login

    def test_post_sem_csrf_recusado(self):
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.eu)
        self.assertEqual(c.post(reverse("ui_usuarios_ativo", args=[self.ped.pk]), {"acao": "desativar"}).status_code, 403)
        self.assertEqual(c.post(NOVO, self.dados_novo("sem-csrf")).status_code, 403)
        self.assertEqual(c.post(reverse("ui_usuarios_link", args=[self.ped.pk])).status_code, 403)
        self.ped.refresh_from_db()
        self.assertTrue(self.ped.is_active)
        self.assertFalse(User.objects.filter(username="sem-csrf").exists())
