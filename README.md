# IMATEC S.A.S. — Sitio web + Portal de clientes + Panel de gestión

Sistema completo para IMATEC S.A.S. (Cali, Valle del Cauca), **ferretería industrial**
y taller de fabricación y montajes en acero:

- **Sitio web público** con catálogo de productos y solicitud de cotización en línea.
- **Portal de clientes**: cada cliente entra con su usuario y ve sus cotizaciones,
  remisiones y facturas.
- **Panel de gestión (dashboard)**: inventario, despachos, cotizaciones, remisiones,
  facturas y clientes.
- **Respaldo en Excel**: dos archivos que se regeneran solos.

Los colores y el logo se tomaron del logo oficial que está en https://imatecsas.com:
amarillo `#FCEA0B`, negro `#1B1B1A`, grafito `#292F33` y gris acero `#9B9B9B`.
Las tipografías son Montserrat y Roboto, las mismas del archivo de Excel de la empresa.

---

## 1. Cómo arrancarlo

Doble clic en **`run.sh`**, o desde la Terminal:

```bash
./run.sh
```

La primera vez se instala solo (tarda un par de minutos). Después abre el navegador en:

| Qué | Dirección |
|---|---|
| Sitio web | http://localhost:8000 |
| Panel de gestión | http://localhost:8000/admin |
| Portal de clientes | http://localhost:8000/portal |

Para apagarlo: `Control + C` en la Terminal.

### Usuario inicial

| Correo | Contraseña | Rol |
|---|---|---|
| `admin@imatecsas.com` | `Imatec2026*` | Administrador |

> **Cámbiela apenas entre**, en *Usuarios → editar → Contraseña*.

---

## 2. El día a día

### Inventario (lo que ya llevaban en Excel)

*Panel → Inventario*. Tiene **exactamente las mismas columnas** de su archivo
«Inventario Imatec»: ID Artículo, Categoría, Material, Diametro, Descripción, Cantidad,
Unidad, Estado y Notas. El **Estado** se calcula solo a partir de la cantidad, igual que
la fórmula del Excel.

- **`+ Agregar ítem`** — agrega uno nuevo. Las listas de Categoría, Material, Diámetro y
  Unidad son las mismas de su Excel, y si escribe un valor nuevo queda agregado a la lista.
- **`⇅`** (en cada fila) — registra una **entrada** (compra), una **salida** (consumo en
  obra) o un **ajuste** (dejar la cantidad exacta que hay en bodega). Todo queda en el
  **Kardex**.
- **`✎`** — corrige los datos de un ítem.
- **`Importar Excel`** — sube un archivo con el formato de ustedes y carga todo de una vez.
  Los ítems que ya existen se actualizan, los nuevos se agregan; **nada se borra**.
- **Stock mínimo** — si lo llena, el sistema avisa en el dashboard cuando el material baje
  de ese nivel.

### El proceso comercial

```
Solicitud web  →  Cotización  →  Remisión  →  Despacho  →  Factura  →  Pago
   (cliente)      (IMATEC)      (IMATEC)     (entrega)    (IMATEC)
```

1. **Solicitud web** — el cliente arma su pedido en el catálogo y lo envía.
   Llega a *Panel → Solicitudes web*. Con un botón se convierte en cotización.
2. **Cotización** — se le pone precio a cada ítem, tiempo de entrega y forma de pago.
   Se imprime o se guarda como PDF. El cliente la ve en su portal y **la aprueba desde ahí**.
3. **Remisión** — desde la cotización aprobada, un botón genera la remisión con los mismos
   ítems, precios y descuentos.
4. **Despacho** — en *Panel → Despachos* hay un tablero de tres columnas:
   Por despachar → En ruta → Entregadas. Se anota transportador, placa y quién recibió.
5. **Factura** — desde la remisión entregada (o desde la cotización), un botón genera la
   factura conservando todo lo pactado.
6. **Pago** — se registran pagos totales o parciales; el saldo se actualiza solo y la
   factura pasa a «Pagada» cuando queda en cero.

En cualquier punto, el botón **Imprimir / PDF** produce el documento formal con el logo,
los datos de la empresa, el total en letras y los espacios de firma.

### Clientes y su portal

*Panel → Clientes*. Al registrar un cliente puede marcar **«Crear acceso al portal»** y el
sistema le crea el usuario con el correo del cliente. Desde ese momento el cliente entra a
`localhost:8000/portal` y ve **solo sus propios documentos**: cotizaciones (que puede
aprobar), remisiones, facturas con su saldo, y sus solicitudes.

### Las líneas de ferretería industrial

El catálogo cubre las dos caras del negocio:

**Ferretería industrial** — lo que se vende de bodega:

| Línea | Qué incluye |
|---|---|
| Tubería y Materiales | Galvanizada, acero al carbón y acero inoxidable 304/316 (SCH10/40/80) |
| Accesorios en Acero al Carbón | Codos, tees, reducciones, uniones, niples, tapones |
| Accesorios en Acero Inoxidable | Codos, tees, reducciones, uniones, sanitarios clamp |
| Bridas y Empaquetadura | Slip-on, ciega, cuello soldable, roscada, empaques y tornillería |
| Válvulas | Compuerta, bola, mariposa, cheque, de pie |
| Sistema Ranurado | Acoples rígidos y flexibles, codos, tees, reducciones |
| PVC y CPVC | Presión, sanitario y agua caliente |
| Polietileno HDPE | Tubería en rollo, compresión, termofusión y electrofusión |
| Uniones y Acoples de Reparación | Dresser, acoples y abrazaderas |

**Taller y montaje** — lo que se fabrica: equipos industriales y hospitalarios en acero
inoxidable, mobiliario urbano, barandas, estructuras metálicas, puertas, obras civiles
y extracción de núcleos.

> Las líneas de ferretería están cargadas con las descripciones técnicas de cada tipo de
> accesorio, pero **sin diámetros ni referencias específicas**: eso se completa a medida
> que se vaya cargando el inventario real de cada línea (igual que ya se hizo con tubería).

### El inventario en el catálogo de la web

Los 109 materiales del inventario están publicados en la web agrupados en **8 familias de
tubería** (categoría *Tubería y Materiales*):

| Familia | Diámetros |
|---|---|
| Tubería Galvanizada | 11 |
| Tubería Acero al Carbón SCH40 sin costura | 14 |
| Tubería Acero al Carbón SCH80 sin costura | 14 |
| Tubería Inoxidable 304 SCH10 · 316 SCH10 | 14 c/u |
| Tubería Inoxidable 304 SCH40 · 316 SCH40 | 14 c/u |
| Tubería Inoxidable SCH80 | 14 |

Cada familia abre una **tabla de diámetros con la existencia real de bodega**, tomada en
vivo del inventario: si usted registra una salida, la web lo refleja de inmediato. Lo que
está en cero aparece como *«Sobre pedido»* y el cliente igual lo puede solicitar.

Cuando el cliente agrega un diámetro a su solicitud, el pedido llega al panel con el
**ID de artículo exacto** (por ejemplo `TUB-GAL-12`), no con una descripción suelta.

En *Inventario → editar ítem* puede fijar el **precio de venta** por metro y decidir si el
ítem se **muestra u oculta en la web**. Sin precio, la web dice «Precio a cotizar».

Al agregar ítems o importar el Excel, las familias del catálogo se actualizan solas.

### Catálogo de la web

*Panel → Catálogo web*. Los 42 productos vienen cargados desde la página actual, con sus
fotos. Puede editar textos, subir fotos nuevas, marcar destacados y poner precios.

> Los productos **sin precio** aparecen en la web como «Precio a cotizar», que es lo
> correcto para fabricación a la medida. Ponga el precio solo cuando quiera mostrarlo.

**Fotos de la bodega.** Guarde las fotos en la carpeta `fotos-bodega/` y ejecute:

```bash
./.venv/bin/python herramientas/procesar_fotos.py
```

Las deja optimizadas para la web en `static/img/bodega/`. Después se asignan a cada
producto desde *Catálogo web → editar producto → Imagen*. Las fotos propias son siempre
la mejor opción: son del material real que se vende y no obligan a dar crédito a nadie.

**Sobre las fotos de los materiales.** Las de productos fabricados salen de la página actual
de IMATEC. Las de tubería se tomaron de Wikimedia Commons, que es la única fuente con
licencia clara para uso comercial; están acreditadas en `/creditos`, como exigen sus
licencias. Una de ellas es CC0 (sin obligación de atribución) y las otras son Creative
Commons con atribución. **Lo ideal es reemplazarlas por fotos de su propia bodega**: se
suben desde *Catálogo web → editar producto → Imagen* y con eso desaparece cualquier
obligación de crédito. Las cinco familias de inoxidable comparten foto porque Commons no
tiene una distinta para cada calibre.

---

## 3. Respaldo en Excel

*Panel → Excel y respaldo*. Se regeneran **automáticamente** cada vez que se guarda un
documento o se mueve el inventario.

**1. `CONTROL_IMATEC.xlsx` — la imagen a seguir.**
Réplica del Excel que ustedes ya manejan. La hoja *«Inventario Imatec»* conserva el mismo
título, las mismas columnas, las mismas listas desplegables, las fuentes Montserrat y
Roboto, los mismos colores de cabecera y la columna *Estado* calculada por fórmula.
Además trae hojas de Resumen, Clientes, Cotizaciones, Remisiones, Facturas, Despachos,
Kardex y Catálogo Web.

**2. `RESPALDO_IMATEC.xlsx` — la copia de seguridad.**
Volcado completo de la base de datos, una hoja por tabla. Sirve para reconstruir todo si
algo falla. Las contraseñas nunca se exportan.

**3. Copia de la base de datos.** Toda la información vive en un solo archivo:
`data/imatec.db`. Descárguelo una vez por semana y guárdelo en una USB o en la nube: es el
respaldo más completo que existe.

---

## 4. Facturación electrónica DIAN — léase con atención

El sistema **sí** hace hoy:

- Genera la factura completa con todos los campos que exige el Anexo Técnico DIAN 1.9.
- La numera según la resolución que se configure.
- Calcula el **CUFE** con el algoritmo oficial (SHA-384).
- Produce el **XML UBL 2.1** descargable.
- Imprime la representación gráfica con el CUFE.

El sistema **no** hace todavía:

- **Firmar digitalmente el XML y transmitirlo a la DIAN.**

Eso no es una limitación del programa: una factura electrónica sólo tiene validez legal
cuando se transmite firmada, y para eso la DIAN debe **habilitar a IMATEC S.A.S.** y la
empresa debe contratar un **Proveedor Tecnológico** autorizado (Factus, Alegra, Siigo,
Facture, etc.). Sin eso, ningún programa puede emitir facturas electrónicas válidas.

**Qué hay que hacer:**

1. Habilitarse en el portal de la DIAN (Factura Electrónica → Habilitación).
2. Obtener la **resolución de numeración**, el **rango** y la **clave técnica**.
3. Contratar el proveedor tecnológico y pedirle sus credenciales de API.
4. Cargar los datos en *Panel → Configuración → Facturación electrónica DIAN*.
5. Conectar el proveedor en un solo punto del código:
   `app/dian.py` → función `enviar_a_dian()`. Todo lo demás ya está listo.

Mientras tanto, el módulo queda avisando en pantalla que la factura **no** se transmitió,
para que nadie la dé por radicada.

---

## 5. Publicarlo en internet

Hoy corre en el computador. Para que los clientes entren desde afuera hay dos caminos:

- **Subdominio junto al sitio actual** (recomendado): dejar el WordPress en
  `imatecsas.com` y publicar esto en `tienda.imatecsas.com` o `app.imatecsas.com`.
  El sitio actual solo necesita un enlace nuevo en su menú.
- **Reemplazar el sitio actual**: apuntar `imatecsas.com` a esta aplicación. El sitio
  público de aquí ya trae el mismo contenido (servicios, nosotros, proyectos, contacto).

Para producción hay que cambiar dos cosas:

```bash
export IMATEC_SECRET_KEY="una-clave-larga-y-secreta"   # firma las sesiones
```

y servir detrás de HTTPS. La base SQLite aguanta bien esta operación; si en el futuro
crece mucho, se migra a PostgreSQL sin cambiar la lógica.

---

## 6. Estructura del proyecto

```
IMATEC.SAS/
├── run.sh                  Arrancar el sistema
├── requirements.txt
├── app/
│   ├── main.py             Aplicación web
│   ├── config.py           Colores de marca y datos de la empresa
│   ├── db.py               Base de datos (SQLite)
│   ├── auth.py             Usuarios, contraseñas y sesiones
│   ├── documentos.py       Cotización → remisión → factura
│   ├── excel_sync.py       Los dos archivos de Excel
│   ├── dian.py             Facturación electrónica (CUFE, XML UBL)
│   ├── numbering.py        Consecutivos
│   ├── seed.py             Catálogo inicial
│   ├── utils.py            Formatos ($ y total en letras)
│   └── routers/            publico.py · portal.py · admin.py
├── templates/              Pantallas (HTML)
├── static/                 Estilos, logo e imágenes de productos
└── data/
    ├── imatec.db           ← toda la información
    └── excel/              CONTROL_IMATEC.xlsx y RESPALDO_IMATEC.xlsx
```

---

## 7. Preguntas frecuentes

**¿Se pierde algo si apago el computador?**
No. Todo queda guardado en `data/imatec.db`. Al volver a arrancar está igual.

**¿Puedo seguir usando mi Excel a mano?**
Sí. Trabaje en el que quiera y use *Importar Excel* para subir los cambios, o
*Descargar Excel* para bajar lo que está en el sistema.

**¿Cuántas personas pueden usarlo al tiempo?**
Varias. Cree un usuario por persona en *Usuarios* (rol **Vendedor** para el equipo
comercial, **Administrador** para quien maneja todo).

**¿Los clientes ven la información de otros clientes?**
No. Cada cliente ve únicamente los documentos asociados a su perfil.

**Olvidé la contraseña del administrador.**
Con acceso al computador se puede restablecer:

```bash
./.venv/bin/python -c "import sys; sys.path.insert(0,'.'); from app.auth import hash_password; from app import db; db.ex('UPDATE usuarios SET password_hash=? WHERE rol=\"admin\"', (hash_password('NuevaClave123*'),)); print('listo')"
```
