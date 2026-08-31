# Publicar IMATEC en Railway

Guía para poner el sistema en internet. Cálculo: **20 a 30 minutos** la primera vez.

> **Lo más importante de todo:** Railway borra el disco del servidor en cada
> despliegue. Si no se crea un **Volume** (disco persistente) y no se apunta la
> aplicación a él, **se pierden los clientes, las cotizaciones, las facturas y el
> inventario cada vez que se actualice el sistema.** El paso 3 es obligatorio.

---

## 1. Crear la cuenta

Entre a [railway.com](https://railway.com) y cree la cuenta (lo más cómodo es
entrar con GitHub). Railway pide una tarjeta para pasar del plan de prueba;
este sistema cabe holgado en el plan **Hobby (US$5/mes)**.

---

## 2. Subir el código

### Opción A — con GitHub (recomendada)

Es la mejor porque después cada `git push` actualiza la página sola.

1. Cree un repositorio nuevo y **privado** en
   [github.com/new](https://github.com/new). Llámelo `imatec-sistema`.
   No marque ninguna casilla de inicialización.
2. En la Terminal, dentro de la carpeta del proyecto:

```bash
git remote add origin https://github.com/SU-USUARIO/imatec-sistema.git
git push -u origin main
```

3. En Railway: **New Project → Deploy from GitHub repo** y elija el repositorio.

### Opción B — con la línea de comandos de Railway

Instale la herramienta (descarga el instalador oficial de Railway):

```bash
curl -fsSL https://railway.com/install.sh | sh
```

Luego, dentro de la carpeta del proyecto:

```bash
railway login
railway init
railway up
```

---

## 3. Crear el disco persistente ⚠️ OBLIGATORIO

En el servicio recién creado, dentro de Railway:

1. Pestaña **Settings** (o clic derecho sobre el servicio) → **Add Volume**.
2. En **Mount path** escriba exactamente:

```
/datos
```

3. Guarde. Railway reinicia el servicio.

Ahí es donde quedan la base de datos, los archivos de Excel y las fotos que se
suban desde el panel. Es lo único que hay que respaldar.

---

## 4. Configurar las variables

En el servicio → pestaña **Variables** → **New Variable**. Agregue estas cuatro:

| Variable | Valor |
|---|---|
| `IMATEC_DATA_DIR` | `/datos` |
| `IMATEC_SECRET_KEY` | una clave larga y única (ver abajo) |
| `IMATEC_ADMIN_EMAIL` | `admin@imatecsas.com` |
| `IMATEC_ADMIN_PASSWORD` | la contraseña que quiera para el administrador |

Para generar la clave secreta, en la Terminal:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copie el resultado y péguelo en `IMATEC_SECRET_KEY`. Esa clave firma las
sesiones: no la comparta y no la suba al repositorio.

`PORT` y `RAILWAY_ENVIRONMENT` las pone Railway sola. No las toque.

---

## 5. Abrir la página al público

Servicio → **Settings → Networking → Generate Domain**. Railway entrega una
dirección tipo `imatec-sistema-production.up.railway.app`.

Compruebe que quedó bien entrando a:

```
https://SU-DIRECCION.up.railway.app/salud
```

Debe responder `{"estado":"ok", ...}`.

---

## 6. Primer ingreso

Entre a `https://SU-DIRECCION.up.railway.app/acceso` con el correo y la
contraseña que puso en las variables.

Si dejó `IMATEC_ADMIN_PASSWORD` vacía, el sistema genera una contraseña al azar
y la muestra **una sola vez** en los registros (pestaña **Deployments → View
Logs**), en un recuadro que dice `USUARIO ADMINISTRADOR CREADO`. Anótela de
inmediato.

**Cámbiela apenas entre:** Usuarios → editar → Contraseña.

---

## 7. Cargar el inventario

El servidor arranca con el catálogo (77 referencias) pero **sin el inventario**,
porque ese es su dato vivo. Cárguelo una sola vez:

Panel → **Inventario → Importar Excel** → suba `Inventario IMATEC.xlsx`.

Al terminar aparecen los 109 materiales y las 8 familias de tubería se publican
solas en el catálogo.

---

## 8. Dominio propio (opcional)

Para que quede en `tienda.imatecsas.com` en vez de la dirección de Railway:

1. Railway → **Settings → Networking → Custom Domain** → escriba
   `tienda.imatecsas.com`. Railway muestra un valor CNAME.
2. En el panel donde esté administrado el dominio `imatecsas.com`, cree un
   registro:

```
Tipo:   CNAME
Nombre: tienda
Valor:  el que muestre Railway
```

3. Espere entre 10 minutos y 2 horas. El certificado HTTPS lo emite Railway.

El WordPress actual sigue intacto en `imatecsas.com`; sólo hay que agregarle un
enlace en el menú que apunte a `tienda.imatecsas.com`.

---

## 9. Respaldos

Railway respalda el volumen, pero **el respaldo bueno es el suyo**:

Panel → **Excel y respaldo → Descargar copia de la base de datos**, una vez por
semana, guardada en una USB o en la nube. Con ese archivo se reconstruye todo.

---

## 10. Actualizar el sistema después

Con la opción A (GitHub), basta con:

```bash
git add -A
git commit -m "descripción del cambio"
git push
```

Railway reconstruye y publica sola en un par de minutos. Los datos no se tocan
porque viven en el volumen.

---

## Si algo sale mal

| Síntoma | Causa casi siempre | Solución |
|---|---|---|
| Se perdieron los datos tras actualizar | No hay volumen, o `IMATEC_DATA_DIR` no apunta a él | Revise el paso 3 y el paso 4 |
| No deja iniciar sesión | La cookie exige HTTPS | Entre por `https://`, no por `http://` |
| El despliegue falla en el healthcheck | La app no arrancó | **Deployments → View Logs** y lea el error |
| Todos quedaron desconectados | Cambió `IMATEC_SECRET_KEY` | Es normal: vuelvan a entrar |
| No aparece la tubería en el catálogo | Falta importar el inventario | Paso 7 |

Los registros en vivo, desde la Terminal:

```bash
railway logs
```
