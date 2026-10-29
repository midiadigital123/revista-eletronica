from pathlib import Path
from subprocess import CalledProcessError, SubprocessError

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from nucleo.models import Ano, Matriz
from nucleo.servicos.importar_matriz import MANTER, gravar_matriz, ler


class Command(BaseCommand):
    help = "Importa descritores e tarefas de um PDF do SAEGO ou de uma planilha (.xlsx) para a matriz."

    def add_arguments(self, parser):
        parser.add_argument("arquivo")
        parser.add_argument("--ano", type=int, required=True)
        parser.add_argument("--nome", required=True, help='nome da matriz, ex.: "Comunitária" (criada se faltar)')
        parser.add_argument("--passo", type=int, help="intervalo mínimo de todas as etapa × CC do arquivo")
        parser.add_argument(
            "--substituir", action="store_true", help="recria descritores e tarefas das etapa × CC que já existem"
        )

    def handle(self, *args, arquivo, ano, nome, passo, substituir, **opcoes):
        ano_obj = Ano.objects.filter(ano=ano).first()
        if not ano_obj:
            raise CommandError(f"ano {ano} não cadastrado (rode carregar_cadastros --ano {ano})")
        try:
            dados = ler(arquivo)  # fora da transação: ler o PDF leva segundos
            with transaction.atomic():  # importação recusada não deixa matriz vazia para trás
                matriz, _ = Matriz.objects.get_or_create(ano=ano_obj, nome=nome)
                resumo = gravar_matriz(
                    matriz, dados, substituir, MANTER if passo is None else passo, origem=Path(arquivo).name
                )
        except CalledProcessError as e:
            raise CommandError(f"pdftotext falhou: {(e.stderr or '').strip() or e}") from e
        except SubprocessError as e:  # inclui o timeout
            raise CommandError(f"pdftotext falhou: {e}") from e
        except IntegrityError as e:
            raise CommandError(f"o banco recusou a importação: {e}") from e
        except (ValueError, OSError) as e:
            raise CommandError(str(e)) from e
        for (cc, etapa), n in resumo.items():
            self.stdout.write(f"{matriz} {cc} {etapa}: {n} descritores")
