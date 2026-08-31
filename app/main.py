"""Aplicación web de IMATEC S.A.S. — sitio público, portal de clientes y panel de gestión."""
import json
from datetime import date

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db
from .auth import current_user, es_staff
from .config import STATIC_DIR, TEMPLATES_DIR
from .seed import sembrar_todo
from .utils import cop, fecha_larga, num, numero_a_letras

app = FastAPI(title="IMATEC S.A.S.", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

plantillas = Jinja2Templates(directory=str(TEMPLATES_DIR))
plantillas.env.filters["cop"] = cop
plantillas.env.filters["num"] = num
plantillas.env.filters["fecha_larga"] = fecha_larga
plantillas.env.filters["letras"] = numero_a_letras
plantillas.env.filters["tarjeta_json"] = lambda p: json.dumps({
    "id": p["id"], "sku": p["sku"], "nombre": p["nombre"],
    "categoria": p.get("categoria", ""), "precio": p.get("precio") or 0,
    "unidad": p.get("unidad", "UND"),
})

ESTADOS_TAG = {
    "borrador": "", "nuevo": "tag-info", "enviada": "tag-info", "en_cotizacion": "tag-alerta",
    "cotizado": "tag-ok", "aprobada": "tag-ok", "rechazada": "tag-error", "vencida": "tag-alerta",
    "pendiente": "tag-alerta", "despachada": "tag-info", "entregada": "tag-ok",
    "emitida": "tag-info", "enviada_dian": "tag-info", "aceptada": "tag-ok",
    "pagada": "tag-ok", "anulada": "tag-error", "cerrado": "tag-ok",
}
plantillas.env.filters["tag"] = lambda e: ESTADOS_TAG.get(e, "")
plantillas.env.filters["bonito"] = lambda e: str(e or "").replace("_", " ").capitalize()


def render(request: Request, plantilla: str, **ctx) -> HTMLResponse:
    """Renderiza añadiendo el contexto común a todas las páginas."""
    usuario = ctx.pop("usuario", None) or current_user(request)
    base = {
        "request": request,
        "usuario": usuario,
        "es_staff": es_staff(usuario),
        "empresa": db.empresa(),
        "anio": date.today().year,
        "hoy": date.today().isoformat(),
    }
    if es_staff(usuario):
        base["nuevos_pedidos"] = db.scalar("SELECT COUNT(*) FROM pedidos WHERE estado='nuevo'")
        base["bajo_minimo"] = db.scalar(
            "SELECT COUNT(*) FROM materiales WHERE activo=1 AND cantidad<=stock_minimo")
    base.update(ctx)
    return plantillas.TemplateResponse(request, plantilla, base)


@app.on_event("startup")
def arrancar():
    sembrar_todo()


@app.exception_handler(404)
async def no_encontrado(request: Request, exc):
    if request.url.path.startswith(("/admin", "/portal")):
        return RedirectResponse("/", status_code=303)
    return plantillas.TemplateResponse(
        request, "public/404.html",
        {"usuario": current_user(request), "es_staff": False,
         "empresa": db.empresa(), "anio": date.today().year},
        status_code=404)


from .routers import admin, portal, publico  # noqa: E402

app.include_router(publico.router)
app.include_router(portal.router)
app.include_router(admin.router)
