"""Copia o seed dos infográficos (`templates_seed/<ano>/infograficos/*.json`, D-298) para cada infográfico ativo
do componente e tipo do seed, de revista ativa. Só preenche o que está vazio: rodar de novo não muda nada.

Recarga (`--anterior <pasta>`, o seed que a carga anterior usou): o campo ainda igual ao anterior recebe o novo;
o que foi editado na revista fica. Fluxo no README ("Corrigir os infográficos de LP depois da carga")."""

from collections import Counter
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from nucleo.models import Ano, RevistaInfografico
from nucleo.servicos import resolver, seed_infografico
from nucleo.servicos.validacao import validada


class Command(BaseCommand):
    help = "Preenche os infográficos do F2 com o seed do ano (só os campos vazios; --anterior para recarregar)."

    def add_arguments(self, parser):
        parser.add_argument("--ano", type=int, required=True)
        parser.add_argument("--usuario", required=True, help="username do autor no histórico")
        parser.add_argument("--anterior", help="pasta com o seed da carga anterior (relativa a app/ ou absoluta)")

    def handle(self, *args, ano, usuario, anterior, **opcoes):
        if not Ano.objects.filter(ano=ano).exists():
            raise CommandError(f"ano {ano} não cadastrado (rode carregar_cadastros --ano {ano})")
        autor = get_user_model().objects.filter(username=usuario).first()
        if not autor:
            raise CommandError(f"usuário {usuario!r} não existe")
        seeds = seed_infografico.seeds(ano)
        if not seeds:
            raise CommandError(f"nenhum seed em {seed_infografico.pasta(ano)}")
        anteriores = {}
        if anterior:
            pasta = Path(anterior) if Path(anterior).is_absolute() else settings.BASE_DIR / anterior
            anteriores = seed_infografico.seeds(ano, pasta)
            if not anteriores:
                raise CommandError(f"nenhum seed anterior em {pasta}")
        erros = [f"{s['_arquivo']}: {e}" for s in seeds.values() for e in seed_infografico.validar(s)]
        erros += [f"anterior {s['_arquivo']}: {e}" for s in anteriores.values() for e in seed_infografico.validar(s)]
        if erros:
            raise CommandError("seed inválido, nada gravado:\n" + "\n".join(erros))

        with transaction.atomic():
            for chave, seed in seeds.items():
                velho = anteriores.get(chave)
                if anterior and not velho:
                    self.stdout.write(self.style.WARNING(f"aviso: {seed['_arquivo']} sem par no anterior: só preenche o vazio"))
                infs = list(
                    RevistaInfografico.objects.filter(
                        ano__ano=ano, componente__codigo=chave[0], tipo=chave[1],
                        arquivado_em__isnull=True, revista__arquivada_em__isnull=True,
                    ).select_related("revista")
                )  # fmt: skip
                eram = {i.revista_id for i in infs  # só quem tem hash gravado pode estar validada
                        if i.revista.hash_validado and validada(i.revista, resolver.hash_validado(i.revista))}  # fmt: skip
                conta = sum((seed_infografico.preencher(inf, seed, autor, velho) for inf in infs), start=Counter())
                perderam = sum(1 for i in infs if i.revista_id in eram
                               and not validada(i.revista, resolver.hash_validado(i.revista)))  # fmt: skip
                self.stdout.write(
                    f"{seed['_arquivo']}: {len(infs)} infográficos, {conta['preenchidos']} preenchidos, "
                    f"{conta['atualizados']} atualizados, {conta['mantidos']} mantidos (editados na revista); "
                    f"{perderam} revistas perderam o Validado"
                )
