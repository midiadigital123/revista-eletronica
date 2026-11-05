from django.core.management.base import BaseCommand, CommandError

from nucleo.servicos.abrir_ano import AnoRecusado, abrir_ano


class Command(BaseCommand):
    help = "Abre o ano copiando os cadastros do maior ano anterior (sem cortes nem projetos)."

    def add_arguments(self, parser):
        parser.add_argument("ano", type=int)

    def handle(self, *args, ano, **opcoes):
        try:
            novo, origem = abrir_ano(ano)
        except AnoRecusado as e:
            raise CommandError(str(e))
        self.stdout.write(f"{novo} aberto a partir de {origem}.")
