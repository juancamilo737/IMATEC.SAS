# IMATEC S.A.S. — Estado del proyecto

Documento único de referencia. Última actualización: **1 de septiembre de 2026**.

Si abre esto después de un tiempo y no recuerda nada, lea las secciones
1, 2 y 8: con eso sabe dónde está todo y qué falta.

---

## 1. Qué es esto

Sistema completo para IMATEC S.A.S. (Cali, Valle del Cauca), que es a la vez
**ferretería industrial** y **taller de fabricación y montajes en acero**.

Tiene tres partes en una sola aplicación:

| Parte | Para quién | Qué hace |
|---|---|---|
| **Sitio público** | cualquiera | Inicio, servicios, nosotros, contacto |
| **Portal de clientes** | clientes con usuario | Catálogo, solicitudes, cotizaciones, remisiones, facturas y estado de cartera |
| **Panel de gestión** | equipo IMATEC | Inventario, despachos, facturación, clientes, respaldos |

**El catálogo es privado**: precios y existencias sólo los ven clientes
registrados. El público ve un botón «Acceder al panel».

---

## 2. Dónde vive cada cosa

| Qué | Dónde |
|---|---|
| **Aplicación** | `catalogo.imatecsas.com` — Railway, proyecto `blissful-bravery`, servicio `IMATEC.SAS`, región EU West (Amsterdam) |
| **Datos** | Volumen `imatec.sas-volume` montado en `/datos` — ahí viven la base, los Excel y las fotos subidas |
| **Código** | `~/Desktop/IMATEC.SAS` y github.com/juancamilo737/IMATEC.SAS (**público**) |
| **Página «Nos mudamos»** | `imatecsas.com` — hosting cPanel de bienvenidohosting |
| **WordPress viejo** | Sigue intacto debajo de esa página. No se borró nada |
| **Correo de la empresa** | Mismo servidor cPanel (MX → `mail.imatecsas.com`). **Nunca se tocó** |

### Accesos

- **Panel del sistema**: `catalogo.imatecsas.com/acceso` — usuario
  `admin@imatecsas.com`. La contraseña está en Railway → servicio → pestaña
  **Variables** → `IMATEC_ADMIN_PASSWORD` (clic en el ojito para verla).
- **cPanel**: `imatecsas.com:2083`
- **Railway**: railway.com
- **GitHub**: github.com/juancamilo737/IMATEC.SAS

> **Pendiente:** cambiar la contraseña de administrador. La que se usó pasó
> por el chat, así que conviene reemplazarla (*Usuarios → editar → Contraseña*).

---

## 3. Cómo se opera

### Arrancar en el computador

```bash
cd ~/Desktop/IMATEC.SAS && ./run.sh
```

Abre en `localhost:8000`. La contraseña local es distinta a la de internet:
en local es `Imatec2026*`.

### Publicar cambios

```bash
git add -A && git commit -m "descripción" && git push
```

Railway reconstruye y publica solo en 2–3 minutos. **El Auto Deploy ya está
encendido** (venía apagado de fábrica, por eso al principio los cambios no
subían).

### El flujo de trabajo

```
Solicitud web → Cotización → Remisión → Despacho → Factura → Pago
```

Cada paso genera el siguiente con un botón, arrastrando precios y descuentos.

### Impresión y PDF

- **Todo se imprime en A5**, que es el papel que usa el papá: documentos de
  venta, estado de cuenta y listados del panel. Cada pantalla se reescala
  para que quepa completa, sin barra lateral, filtros ni botones.
- En el listado de inventario se ocultan al imprimir las columnas
  secundarias (categoría, material, diámetro, costo, margen y notas): con las
  13 columnas el papel quedaba ilegible. En pantalla se siguen viendo todas.
- El PDF se guarda con la nomenclatura de la empresa, automáticamente:
  `FEV-688 PARQUES ACUATICOS S.A.S.`, `COT 1 GAS PIPE SOLUTIONS SAS`.
- Botón **⬇ Descargar PDF** en cotización, remisión y factura.

### Respaldos

*Panel → Excel y respaldo*:

- **`CONTROL_IMATEC.xlsx`** — réplica del Excel que la empresa ya maneja,
  con la hoja «Inventario Imatec» idéntica (fuentes, colores, listas y la
  fórmula de Estado).
- **`RESPALDO_IMATEC.xlsx`** — volcado completo de la base.
- **Copia de la base de datos** — descárguela una vez por semana a una USB
  o a la nube. Es el respaldo que de verdad importa.

---

## 4. Los datos de la empresa

Los archivos originales están en `~/Desktop/IMATEC.SAS/Archivos/`
(fuera del control de versiones: son datos de la empresa y el repo es público).

Listos para subir, ya numerados, en **`~/Desktop/SUBIR A IMATEC/`**.

### Orden de subida — importa

Panel → **Excel y respaldo** → *«Cargar los archivos de la empresa»*

| # | Archivo | Qué carga |
|---|---|---|
| 1 | `1 - CLIENTES.xlsx` | 174 clientes |
| 2 | `2 - LISTADO DE PRECIOS.xlsx` | 427 productos con su costo |
| 3 | `3 - HISTORICO DE COTIZACIONES.json` | 2.696 productos con precio real |
| 4 | `4 - CARTERA.xlsx` | ⚠️ **no subir todavía** — ver sección 5 |

El orden importa: la cartera necesita los clientes ya cargados, y el
histórico va después del listado para que el costo quede emparejado.

Ninguna importación borra: actualiza lo que existe y agrega lo nuevo.

### Estado esperado al terminar

| | |
|---|---|
| Clientes | 174 |
| Inventario | 3.200 productos (714 publicados) |
| Cartera | ver sección 5 |

---

## 5. La cartera — resuelta

**El papá revisó la primera carga y dijo que no se debía todo eso. Tenía
razón, y el propio archivo lo demostró.** Quedó en **$29.743.442**, que es
exactamente la cifra que ellos mismos escribieron al pie de su hoja.

### Qué estaba mal

El archivo `RELACION DE CARTERA IMATEC S.A.S..xlsx` tiene dos hojas, y el
importador cometía dos errores a la vez:

| | Facturas | Valor |
|---|---|---|
| Se cargaba de más — **Hoja2**, un estado de cuenta suelto | +15 | +$16.420.071 |
| Se botaba de menos — las filas que dicen **«PDTE PAGO»** | −9 | −$7.151.775 |
| **Cargado antes** | 53 | **$39.011.738** |
| **Cargado ahora** | 47 | **$29.743.442** |

**1. Se leían las dos hojas.** La Hoja1 es la relación de cartera y trae su
total al pie: $29.743.442. La Hoja2 es otra cosa —un `ESTADO DE CUENTA` de un
solo cliente, FERRETERIA SU PROVEEDOR, con 15 facturas viejas (FEV-453 a
FEV-560)— y **no está sumada dentro de ese total**. Ese mismo cliente sí
aparece en la Hoja1 con sus 4 facturas nuevas (FEV-628 en adelante). O sea:
la empresa no considera esa hoja cartera vigente. Ahora sólo se lee la hoja
cuyo título dice «relación de cartera»; cualquier otra se reporta como
omitida. **Ese era el grueso del error: $16,4 millones.**

**2. Se botaban las filas sin fecha de vencimiento.** Nueve facturas dicen
«PDTE PAGO» donde va el día, y el importador las descartaba. Sí se deben, y
la prueba es aritmética: las 47 filas de la Hoja1, incluidas esas nueve,
suman **exactamente** el total escrito al pie. Ahora entran con el
vencimiento vacío y caen en su propia franja de cobranza, **sin inventarles
un plazo**.

### Cómo quedó repartida

| | Facturas | Valor |
|---|---|---|
| Vencidas | 18 | $5.470.516 |
| Por vencer | 20 | $17.121.151 |
| **Sin plazo acordado** («PDTE PAGO») | 9 | $7.151.775 |
| **Total** | **47** | **$29.743.442** |

El cambio más visible: **FERRETERIA SU PROVEEDOR pasó de $25.656.431 a
$9.236.360.**

### Defectos que salieron de paso

Al meter facturas con la fecha en blanco aparecieron tres sitios donde una
cadena vacía se comparaba como si fuera una fecha —y `''` es menor que
cualquier fecha, así que las nueve se pintaban de rojo como vencidas:

- el KPI «facturas vencidas» del tablero,
- el filtro `/admin/facturas?estado=vencidas`,
- los listados de facturas del panel y del portal.

Y en `portal_datos._dias_vencido`, una fecha ilegible devolvía `0`, que se lee
como «vence hoy»: esas facturas se colaban en la franja corriente como si
estuvieran al día. Ahora devuelve `None` y hay una franja **«sin plazo»**
aparte, más un filtro `/admin/facturas?estado=sin_plazo`.

### Salvaguardas para que no se repita

- El importador **compara lo cargado contra el total escrito en la hoja** y
  reporta la diferencia. Si no cuadra, es que el archivo cambió.
- Ya no sólo inserta: **reconcilia**. Al recargar actualiza lo que cambió y
  retira lo que ya no está en la hoja —así fue como salieron las 15 de la
  Hoja2 sin tener que borrar la base.
- Sólo toca las facturas que él mismo creó (las marcadas «Saldo trasladado de
  la relación de cartera»). Una factura hecha desde el panel, o una a la que
  ya se le registró un abono, no se pisa nunca.

### Lo único que queda por revisar a mano

- **FEV-927, GRUPO ACERO Y CONFORT ($1.857.200)** trae escrito «ABONÓ» en el
  archivo, pero no dice de cuánto fue el abono. Se cargó por el valor
  completo —que es como está sumada en el total de ellos— y la anotación
  quedó copiada en las observaciones de la factura. Cuando él diga el monto,
  se registra el pago desde el panel y el saldo se ajusta solo.
- Las **9 facturas «PDTE PAGO»** necesitan que alguien les acuerde una fecha
  de vencimiento. Están en `/admin/facturas?estado=sin_plazo`.


## 6. Hallazgo importante sobre los precios

**La columna «COSTO» del listado de precios NO es el precio de venta.**

Se comprobó cruzando los productos que están en el listado **y** fueron
cotizados de verdad (87 coincidencias):

| | |
|---|---|
| Ratio mediano cotizado / listado | **1,33x** |
| Cotizado por encima del listado | 66 de 87 |
| Iguales (±2%) | 1 de 87 |

Publicar esa columna como precio de venta habría hecho que **vendieran sin
margen**. Por eso:

- El **precio de venta** sale del último valor realmente cotizado a un cliente.
- El **costo** se guarda aparte y **nunca se borra**, aunque el cruce por
  descripción haya dejado alguno mal emparejado: los precios se negocian y
  ese valor es una referencia que la empresa corrige a mano.
- El inventario muestra **Costo · Venta · Margen** en columnas, con el margen
  en color: verde si es normal, rojo si vende bajo costo, naranja si es
  desproporcionado. Los 16 dudosos quedan anotados «revisar costo».

Se publican los productos cotizados **dos veces o más** (605): son los
recurrentes, validados por el uso. Los de una sola vez quedan cargados sin
publicar, porque suelen ser fabricaciones puntuales o erratas.

---

## 7. Facturación electrónica DIAN

El sistema **sí** hace hoy: arma la factura con todos los campos del Anexo
Técnico 1.9, la numera, calcula el **CUFE** (SHA-384) y genera el **XML UBL
2.1** descargable.

**No** hace todavía: firmar y transmitir a la DIAN. Eso exige habilitación y
un proveedor tecnológico.

**El papá ya usa Xubio**, que está habilitado ante la DIAN — eso salta el
trámite lento. El punto de conexión está aislado en
`app/dian.py → enviar_a_dian()`; se toca una sola función.

**Falta averiguar** si Xubio expone API para emitir desde fuera, o si sólo se
factura dentro de su plataforma. Si es lo segundo, la integración sería
exportar los documentos hacia Xubio en vez de transmitir a la DIAN.

Para avanzar hace falta: acceso a la cuenta de Xubio, ver si hay sección de
API o integraciones, y la resolución de numeración DIAN (número, rango y
fechas).

---

## 8. Lo que falta

Por orden de importancia:

1. ~~Resolver la cartera~~ — hecho, ver sección 5. Falta el monto del
   abono de GRUPO ACERO Y CONFORT y ponerle plazo a las 9 «PDTE PAGO».
2. **Subir los archivos 1, 2 y 3** desde `~/Desktop/SUBIR A IMATEC/`. Hoy
   producción está vacía: todo lo importado está sólo en la copia local.
3. **Cambiar la contraseña** de administrador.
4. **Crear los accesos** de los clientes que vayan a usar el portal
   (*Clientes → nuevo cliente → «Crear acceso al portal»*). Sin usuario nadie
   ve el catálogo.
5. **Vincular Xubio** (sección 7).
6. **Fotos de la bodega** — guardarlas en `fotos-bodega/` y correr
   `./.venv/bin/python herramientas/procesar_fotos.py`. Reemplazan las de
   Wikimedia y con eso desaparece la página de créditos.
7. **Revisar 64 cotizaciones** que no se pudieron leer (6% del total,
   plantilla distinta o archivo dañado).
8. **Limpiar el WordPress** — tiene páginas de demostración del tema en inglés
   (kitchen-remodeling, contemporary-villa, coming-soon). No urge: la página
   de mudanza tapa la entrada y ya hay 301 programados.
9. **Dominio raíz** — poner el sistema en `imatecsas.com` exige mover los
   nameservers a Cloudflare (Railway sólo da CNAME y el DNS actual no soporta
   ALIAS). Se aplazó a propósito: esa operación implica recrear el correo en
   otro panel. Hacerlo cuando el sistema lleve semanas en uso.

---

## 9. Criterios ya acordados

No hace falta volver a discutirlos:

- **El correo no se toca.** Cualquier cambio de DNS se confirma antes y se
  verifica MX, SPF y DKIM después.
- **No borrar nada sin mostrar antes la lista.** Aplica al WordPress y a los
  registros DNS.
- **Nada de contraseñas escritas en el código.** En producción salen de
  variables de entorno o se generan al azar.
- **Precios en cero = «Precio a cotizar».** No inventar precios.
- **El costo siempre se conserva y se puede editar**, porque los precios se
  negocian y a veces se cotiza distinto.

---

## 10. Trampas ya diagnosticadas

Para no volver a perder tiempo con esto:

- **Railway traía Auto Deploy apagado.** Los push a `main` no publicaban nada.
  Ya está encendido.
- **La zona DNS tenía 4 registros SRV rotos** (`_caldav`, `_caldavs`,
  `_carddav`, `_carddavs` apuntando a `%domain%`) que invalidaban el archivo
  completo e impedían crear cualquier registro. Ya corregidos. cPanel valida
  la zona entera al escribir: hay que arreglar todos y usar «Guardar Todos Los
  Registros» de una vez.
- **La página `imatecsas.com` se sirve desde `.htaccess`**, con un bloque
  `# BEGIN IMATEC MUDANZA`. Se revierte borrando esas 6 líneas. El respaldo
  del original está en `.htaccess.respaldo-2026-08-31`.
- **En el Mac no hay `gh`, `node`, `brew` ni CLI de Railway.** Python 3.14 sí.

---

## 11. Estructura del proyecto

```
IMATEC.SAS/
├── ESTADO.md                 este documento
├── README.md                 manual de uso del sistema
├── DESPLIEGUE.md             paso a paso del despliegue en Railway
├── run.sh                    arrancar en local
├── app/
│   ├── main.py               aplicación web
│   ├── config.py             marca y datos de la empresa
│   ├── db.py                 base de datos (SQLite)
│   ├── auth.py               usuarios y sesiones
│   ├── documentos.py         cotización → remisión → factura
│   ├── portal_datos.py       cartera y estado de cuenta del cliente
│   ├── excel_sync.py         los dos archivos de Excel
│   ├── dian.py               CUFE, XML UBL, punto de enganche con Xubio
│   ├── importar_xubio.py     clientes
│   ├── importar_precios.py   listado de precios (costos)
│   ├── importar_items.py     histórico de cotizaciones (precios de venta)
│   ├── importar_cartera.py   facturas pendientes
│   └── routers/              publico.py · portal.py · admin.py
├── herramientas/
│   ├── extraer_items.py      lee las 1.033 cotizaciones
│   └── procesar_fotos.py     optimiza fotos para la web
├── templates/                pantallas
├── static/                   estilos, logo, imágenes
├── Archivos/                 datos de la empresa (fuera de git)
└── data/                     base de datos y Excel generados (fuera de git)
```

**Stack:** Python 3 + FastAPI + SQLite + Jinja2 + openpyxl. Sin paso de build.
