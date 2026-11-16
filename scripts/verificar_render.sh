#!/usr/bin/env bash
# Comprueba si en Render está vivo el stack integrado (frontend del ZIP + backend del ZIP).
# Uso: bash scripts/verificar_render.sh
#      API_URL=https://… WEB_URL=https://… bash scripts/verificar_render.sh
set -u
API_URL="${API_URL:-https://cosplay-chile-api.onrender.com}"
WEB_URL="${WEB_URL:-https://cosplay-chile-web.onrender.com}"
API_URL="${API_URL%/}"
WEB_URL="${WEB_URL%/}"

fallos=0
ok()   { printf '  \033[32mOK\033[0m   %s\n' "$1"; }
mal()  { printf '  \033[31mFALLO\033[0m %s\n' "$1"; fallos=$((fallos + 1)); }

echo "API : $API_URL"
echo "WEB : $WEB_URL"
echo

codigo=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "$API_URL/api/salud" || echo 000)
[ "$codigo" = "200" ] && ok "GET /api/salud → 200" || mal "GET /api/salud → $codigo (el backend nuevo no está desplegado)"

cuerpo=$(curl -s --max-time 30 "$API_URL/api/inicio" || true)
case "$cuerpo" in
  *'"estadisticas"'*) ok "GET /api/inicio → devuelve estadísticas" ;;
  *'"detail":"Not Found"'*) mal "GET /api/inicio → 404 Not Found (sigue la API anterior)" ;;
  *) mal "GET /api/inicio → respuesta inesperada: ${cuerpo:0:80}" ;;
esac

rutas=$(curl -s --max-time 30 "$API_URL/openapi.json" \
  | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('paths', {})))" 2>/dev/null || echo 0)
if [ "$rutas" -ge 55 ]; then
  ok "/openapi.json → $rutas rutas (stack nuevo, ~60)"
else
  mal "/openapi.json → $rutas rutas (stack anterior, 49)"
fi

codigo_web=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "$WEB_URL/" || echo 000)
[ "$codigo_web" = "200" ] && ok "GET / (web) → 200" || mal "GET / (web) → $codigo_web"

echo
if [ "$fallos" -eq 0 ]; then
  echo "Resultado: stack integrado desplegado correctamente."
else
  echo "Resultado: $fallos comprobación(es) fallida(s). Revisa DIAGNOSTICO_RENDER.md y GUIA_DEMO.md."
fi
exit "$fallos"
