from django.apps import AppConfig


class NucleoConfig(AppConfig):
    name = "nucleo"

    def ready(self):
        from nucleo.servicos import arquivos  # noqa: F401  (conecta o post_delete da Tarefa)
