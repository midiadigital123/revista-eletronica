"""Admin de usuários (D-142): sem `is_superuser`, `is_staff` e `user_permissions` no
formulário. As regras de quem pode o quê ficam em `nucleo/usuarios.py`, comuns à tela B
(`urls/ui_usuarios.py`). Ninguém exclui (desativa com `is_active`).
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from nucleo import usuarios as regra

admin.site.unregister(User)


@admin.register(User)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "first_name", "last_name", "is_active")
    list_filter = ("is_active", "groups")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Dados pessoais", {"fields": ("first_name", "last_name", "email")}),
        ("Acesso", {"fields": ("is_active", "groups")}),
        ("Datas", {"fields": ("last_login", "date_joined")}),
    )
    filter_horizontal = ()
    actions = None

    def get_queryset(self, request):
        return regra.visiveis(request.user, super().get_queryset(request))

    def get_readonly_fields(self, request, obj=None):
        campos = ("last_login", "date_joined")
        if obj is None:
            return campos
        ativo = () if regra.pode_mudar_ativo(request.user, obj) else ("is_active",)
        grupos = () if regra.pode_mudar_grupos(request.user, obj) else ("groups",)
        return (*campos, *ativo, *grupos)

    def has_change_permission(self, request, obj=None):
        if obj is not None and not regra.pode_editar(request.user, obj):
            return False
        return super().has_change_permission(request, obj)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "groups":
            kwargs["queryset"] = regra.grupos_atribuiveis(request.user)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            regra.preparar_novo(obj)
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False  # D-205: usuário se desativa (is_active), nunca se apaga
