"""Cria usuários a partir de um CSV local `usuario,grupo` (fora do git) e imprime o link
para cada um definir a própria senha (S17).

Usuário novo nasce com senha inutilizável, `is_staff` e o grupo da linha. Usuário que já
existe não é alterado; se ainda não definiu senha, ganha um link novo (o anterior expirou).
O link vale `PASSWORD_RESET_TIMEOUT` (3 dias) e deixa de valer quando a senha é definida.
"""

import csv

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from nucleo.permissoes import PAPEIS


class Command(BaseCommand):
    help = "Cria usuários de um CSV `usuario,grupo` e imprime o link para definir a senha."

    def add_arguments(self, parser):
        parser.add_argument("arquivo", help="CSV com cabeçalho usuario,grupo")
        parser.add_argument("--url", required=True, help="endereço do sistema, ex.: https://revista.exemplo.org")

    @transaction.atomic
    def handle(self, *args, arquivo, url, **opcoes):
        with open(arquivo, encoding="utf-8-sig", newline="") as f:
            linhas = [(r["usuario"].strip(), r["grupo"].strip()) for r in csv.DictReader(f)]
        ruins = [f"{u or '(vazio)'}: grupo {g!r}" for u, g in linhas if not u or g not in PAPEIS]
        if ruins:  # nada é criado se uma linha estiver errada
            raise CommandError(f"linhas inválidas (grupos: {', '.join(PAPEIS)}): {'; '.join(ruins)}")

        User = get_user_model()
        for usuario, grupo in linhas:
            user, novo = User.objects.get_or_create(username=usuario, defaults={"is_staff": True})
            if novo:
                user.set_unusable_password()
                user.save()
                user.groups.add(Group.objects.get(name=grupo))
            elif user.has_usable_password():
                self.stdout.write(f"já existe, mantido: {usuario}")
                continue
            caminho = reverse(
                "password_reset_confirm",
                args=[urlsafe_base64_encode(force_bytes(user.pk)), default_token_generator.make_token(user)],
            )
            estado = f"criado ({grupo})" if novo else "sem senha ainda (grupos não alterados)"
            self.stdout.write(f"{estado}: {usuario} {url.rstrip('/')}{caminho}")
