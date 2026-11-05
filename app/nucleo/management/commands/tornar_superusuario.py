"""Torna usuários existentes superusuários (D-219).

Nenhuma tela faz isto de propósito (D-142): o form de usuário do admin e a tela Usuários não têm
`is_superuser`. Só quem tem acesso ao servidor promove alguém. Se um nome não existir, nada muda.
Usuário novo como superusuário: `createsuperuser`.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Torna superusuários os usuários informados (já cadastrados)."

    def add_arguments(self, parser):
        parser.add_argument("usuarios", nargs="+", help="nomes de usuário, ex.: fabiano.santana")

    @transaction.atomic
    def handle(self, *args, usuarios, **opcoes):
        encontrados = {u.username: u for u in get_user_model().objects.filter(username__in=usuarios)}
        faltam = [u for u in usuarios if u not in encontrados]
        if faltam:  # nada muda se um nome estiver errado
            raise CommandError(f"usuário não encontrado: {', '.join(faltam)}. Nada foi alterado.")
        for nome in usuarios:
            u = encontrados[nome]
            if u.is_superuser:
                self.stdout.write(f"já era superusuário: {nome}")
                continue
            u.is_superuser = u.is_staff = True
            u.save(update_fields=["is_superuser", "is_staff"])
            aviso = "" if u.is_active else " (está desativado: só entra depois de ativado)"
            self.stdout.write(f"agora é superusuário: {nome}{aviso}")
