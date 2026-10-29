"""Admin de usuários (D-142): sem `is_superuser`, `is_staff` e `user_permissions` no
formulário. Usuário novo nasce `is_staff` (todo perfil usa o admin). Ninguém exclui
(desativa com `is_active`).

Quem não é superusuário (o perfil Admin):
- não vê superusuários (trocaria a senha de um e entraria como ele);
- só dá os grupos Pedagógica e Mídias Digitais: Impresso daria `marcar_impressa`, o que
  anularia ADMIN_MARCA_IMPRESSA = False, e Admin multiplicaria quem gerencia usuários;
  esses dois ficam com o superusuário;
- não muda os próprios grupos nem se desativa;
- não altera outro usuário do grupo Admin (só vê);
- não mexe nos grupos de quem já tem um grupo fora dos permitidos (ex.: Impresso).
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User

from nucleo.permissoes import PAPEIS

admin.site.unregister(User)

GRUPOS_DO_ADMIN = ("Pedagógica", "Mídias Digitais")  # o que um não superusuário pode atribuir


def grupos_permitidos(request):
    return PAPEIS if request.user.is_superuser else GRUPOS_DO_ADMIN


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
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(is_superuser=False)

    def get_readonly_fields(self, request, obj=None):
        campos = ("last_login", "date_joined")
        if obj is None or request.user.is_superuser:
            return campos
        if obj == request.user:
            return (*campos, "is_active", "groups")
        if obj.groups.exclude(name__in=grupos_permitidos(request)).exists():
            return (*campos, "groups")
        return campos

    def has_change_permission(self, request, obj=None):
        if (
            obj is not None
            and not request.user.is_superuser
            and obj != request.user
            and obj.groups.filter(name="Admin").exists()
        ):
            return False
        return super().has_change_permission(request, obj)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "groups":
            kwargs["queryset"] = Group.objects.filter(name__in=grupos_permitidos(request)).order_by("name")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.is_staff = True
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False
