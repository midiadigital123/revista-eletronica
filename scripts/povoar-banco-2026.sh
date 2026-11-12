#!/usr/bin/env bash
# Povoa um banco VAZIO com a carga de 2026 (D-265): ano e cadastros, 33 parceiros, 148 cortes (com projetos e
# revistas pela cascata), matriz Comunitária (198 descritores, 1093 tarefas), 4 templates e o usuário `admin`.
# Tudo vem do repositório (docs/fontes, templates_seed); não há dump nem senha versionados.
#
# Uso (raiz do repositório, com Docker):
#   ADMIN_SENHA='...' ./scripts/povoar-banco-2026.sh     # sem ADMIN_SENHA, pergunta
# Recomeçar do zero antes: docker compose down -v
set -euo pipefail
cd "$(dirname "$0")/.."

FONTES="$PWD/docs/fontes"
CORTES="2025/planilhas importantes/Cortes dos Padrões por Etapa e Parceiro.xlsx"  # a mesma de 2026 (sha256 igual)
SOMATIVAS="2026/Somativas 2026.xlsx"
MATRIZ="2025/PDFs Matriz Comunitária"
dj() { docker compose run --rm -T -v "$FONTES:/fontes:ro" app python manage.py "$@"; }

if [ -z "${ADMIN_SENHA:-}" ]; then
  read -r -s -p "Senha do usuário admin: " ADMIN_SENHA
  echo
fi

docker compose up -d --wait db
dj migrate

# Só banco vazio: reimportar duplicaria a matriz e a cascata pularia parceiros que já têm corte.
if ! dj shell -c "import sys; from nucleo.models import Parceiro, Ano; sys.exit(int(Parceiro.objects.exists() or Ano.objects.exists()))"; then
  echo "O banco já tem dados. Para recomeçar do zero: docker compose down -v" >&2
  exit 1
fi

dj carregar_cadastros --ano 2026
docker compose run --rm -T -e DJANGO_SUPERUSER_PASSWORD="$ADMIN_SENHA" app \
  python manage.py createsuperuser --noinput --username admin --email admin@example.com
dj importar_cortes "/fontes/$SOMATIVAS" "/fontes/$CORTES" --ano 2026 --usuario admin
dj carregar_templates --ano 2026
for pdf in "SAEGO_2025_RE_Alfa_2EF_5EF Web.pdf" "SAEGO_2025_RE_LP Web.pdf" "SAEGO_2025_RE_MT Web.pdf"; do
  dj importar_matriz --ano 2026 --nome Comunitária "/fontes/$MATRIZ/$pdf"
done

docker compose up -d --wait app
echo "Pronto: http://localhost:${APP_PORT:-8000} (usuário admin)."
