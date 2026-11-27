"""Upload da capa da revista (S09; D-118, D-125), da imagem do item do infográfico, do arquivo
do item da tarefa (D-180, D-181) e do PDF das atividades do F2 (D-308)."""

import hashlib
import uuid

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from nucleo.models import Atividades, Tarefa

MB = 1024 * 1024
CAPA_MAX = 5 * MB
ITEM_MAX = 5 * MB
ATIVIDADES_MAX = 20 * MB  # PDF editorado, com imagens
ITEM_MIMES = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg"}  # contrato/schemas.ts


def _erro(msg):
    raise ValidationError(msg)


def _ler(arquivo, limite, nome):
    dados = arquivo if isinstance(arquivo, bytes) else arquivo.read(limite + 1)
    if len(dados) > limite:
        _erro(f"{nome} maior que {limite // MB} MB: reduza e envie de novo.")
    return dados


def _gravar(pasta, extensao, dados):
    return default_storage.save(f"{pasta}/{uuid.uuid4().hex}.{extensao}", ContentFile(dados))


def _salvar(obj, campos, novo, antigo):
    """Salva `obj` (revista, item do infográfico…; sem pk, cria); se falhar, apaga o arquivo novo.
    O antigo sai no commit (decisão do S09)."""
    try:
        obj.save(update_fields=campos if obj.pk else None)
    except BaseException:
        default_storage.delete(novo)
        raise
    # ponytail: se a transação de fora falhar depois, o arquivo novo fica órfão; varredura se incomodar.
    if antigo and antigo != novo:
        transaction.on_commit(lambda: default_storage.delete(antigo))


# --- Capa -------------------------------------------------------------------


def tipo_imagem(dados):
    """Extensão pela assinatura mágica (png, jpg, webp) ou None."""
    if dados.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if dados.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if dados[:4] == b"RIFF" and dados[8:12] == b"WEBP":
        return "webp"
    return None


def receber_capa(revista, arquivo):
    """Grava a capa (PNG, JPG ou WebP até 5 MB, tipo pelo conteúdo) e o sha256."""
    dados = _ler(arquivo, CAPA_MAX, "Capa")
    extensao = tipo_imagem(dados) or _erro("Capa precisa ser PNG, JPG ou WebP.")
    antigo = revista.capa
    revista.capa = _gravar("capas", extensao, dados)
    revista.capa_sha256 = hashlib.sha256(dados).hexdigest()
    _salvar(revista, ["capa", "capa_sha256"], revista.capa, antigo)
    return revista


def receber_imagem_item(item, arquivo):
    """Grava a imagem do item do infográfico (PNG, JPG ou WebP até 5 MB, tipo pelo conteúdo) e o
    sha256. Item ainda fora do banco (com infográfico, ano e posição postos) é criado aqui."""
    dados = _ler(arquivo, ITEM_MAX, "Imagem")
    extensao = tipo_imagem(dados) or _erro("A imagem precisa ser PNG, JPG ou WebP.")
    antigo = item.imagem
    item.imagem = _gravar("infograficos", extensao, dados)
    item.imagem_sha256 = hashlib.sha256(dados).hexdigest()
    _salvar(item, ["imagem", "imagem_sha256"], item.imagem, antigo)
    return item


# --- Item da tarefa (D-180, D-181) -----------------------------------------------


def receber_item(tarefa, arquivo, alt=""):
    """Grava o arquivo do item (PDF, PNG ou JPG até 5 MB) com nome uuid e o texto alternativo.
    O tipo (e a extensão gravada) sai dos bytes; nome e mime enviados não contam.
    O arquivo antigo sai se ficou órfão."""
    dados = _ler(arquivo, ITEM_MAX, "Arquivo do item")
    tipo = "pdf" if dados.startswith(b"%PDF-") else tipo_imagem(dados)
    if tipo not in ITEM_MIMES:
        _erro("O arquivo do item precisa ser PDF, PNG ou JPG.")
    antigo = tarefa.arquivo
    tarefa.arquivo, tarefa.texto_alternativo = _gravar("itens", tipo, dados), alt
    try:
        tarefa.save(update_fields=["arquivo", "texto_alternativo"])
    except BaseException:
        default_storage.delete(tarefa.arquivo)
        raise
    apagar_item_orfao(antigo)
    return tarefa


def remover_item(tarefa):
    """Desliga o arquivo da tarefa; o arquivo físico só sai se nenhuma tarefa o usa (D-150)."""
    antigo = tarefa.arquivo
    tarefa.arquivo, tarefa.texto_alternativo = None, ""
    tarefa.save(update_fields=["arquivo", "texto_alternativo"])
    apagar_item_orfao(antigo)


def apagar_item_orfao(caminho):
    """Depois do commit, apaga `caminho` do storage se nenhuma Tarefa (de nenhum ano) aponta
    para ele. O abrir_ano copia o caminho: 2026 e 2027 dividem o mesmo arquivo (D-150)."""
    # ponytail: um abrir_ano/duplicar_matriz em andamento, com a cópia ainda não commitada,
    # não aparece no exists() e o arquivo sai com a cópia apontando para ele. Saída se
    # acontecer: select_for_update em Matriz/Ano aqui e na cópia, serializando as duas.

    def apagar():
        if not Tarefa.objects.filter(arquivo=caminho).exists():
            default_storage.delete(caminho)

    if caminho:
        transaction.on_commit(apagar)


@receiver(post_delete, sender=Tarefa)
def _tarefa_excluida(sender, instance, **kwargs):
    """Qualquer exclusão de tarefa (pela tela, em cascata do descritor, na reimportação)."""
    apagar_item_orfao(instance.arquivo)


# --- PDF das atividades do F2 (D-308) ---------------------------------------------


def receber_atividades(ano, componente, tipo, arquivo):
    """Grava o PDF das atividades de ano × componente × tipo (só PDF, até 20 MB, tipo pelos bytes) e o sha256.
    Já existindo, troca o arquivo; o antigo sai no commit."""
    dados = _ler(arquivo, ATIVIDADES_MAX, "PDF das atividades")
    if not dados.startswith(b"%PDF-"):
        _erro("As atividades precisam ser um arquivo PDF.")
    obj = Atividades.objects.filter(ano=ano, componente=componente, tipo=tipo).first()
    obj = obj or Atividades(ano=ano, componente=componente, tipo=tipo)
    antigo = obj.arquivo
    obj.arquivo = _gravar("atividades", "pdf", dados)
    obj.arquivo_sha256 = hashlib.sha256(dados).hexdigest()
    _salvar(obj, ["arquivo", "arquivo_sha256"], obj.arquivo, antigo)
    return obj


def remover_atividades(obj):
    """Inversa de receber_atividades: apaga o registro; o arquivo sai do storage no commit."""
    caminho = obj.arquivo
    obj.delete()
    transaction.on_commit(lambda: default_storage.delete(caminho))


def atividades_da_revista(revista):
    """{tipo: caminho no storage} dos PDFs de atividades do ano × componente da revista."""
    # ponytail: lê o PDF vigente, também na revista arquivada (fora da foto, D-308); guardar o sha na foto se precisar.
    return dict(
        Atividades.objects.filter(ano_id=revista.ano_id, componente_id=revista.componente_id).values_list(
            "tipo", "arquivo"
        )
    )
