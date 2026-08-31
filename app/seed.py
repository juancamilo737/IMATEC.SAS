"""Carga inicial: catálogo real de IMATEC (tomado de imatecsas.com), usuarios y listas."""
from . import db
from .auth import crear_usuario
from .config import EMPRESA_DEFAULT
from .utils import slugify

CATEGORIAS = [
    ("equipos-industriales", "Equipos Industriales",
     "Equipos y muebles en acero inoxidable para restaurantes, comedores, cafeterías, "
     "panaderías y bares. Todo lo relacionado con la industria del procesamiento de alimentos.", 1),
    ("equipos-hospitalarios", "Equipos Hospitalarios",
     "Soluciones y equipos de grado médico para clínicas y hospitales. Diseñamos, calculamos "
     "y fabricamos con apego a las normas internacionales.", 2),
    ("mobiliario-urbano", "Mobiliario Urbano",
     "Bancas, basureros y racks para bicicleta en acero inoxidable para espacio público.", 3),
    ("barandas-pasamanos", "Barandas y Pasamanos",
     "Pasamanos en acero inoxidable, acero al carbón y vidrio templado.", 4),
    ("estructuras-metalicas", "Estructuras Metálicas",
     "Montajes, bodegas, edificios, mezzanines, escaleras metálicas, pérgolas y "
     "mobiliario urbano en general.", 5),
    ("puertas-metalicas", "Puertas y Divisiones",
     "Puertas para baño, cortinas enrollables, puertas de seguridad y separadores.", 6),
    ("obras-civiles", "Obras Civiles",
     "Losas en concreto, acabados en obra blanca, escaleras, cámaras y trampas de grasa, "
     "UARs, cielos falsos en PVC y fachadas en Alucobond.", 7),
    ("extraccion-nucleos", "Extracción de Núcleos",
     "Pasanúcleos para losas de todo tipo, pantallas en concreto y cimentación. "
     "Perforación desde 1\" hasta 9\".", 8),
    ("otros", "Otros Productos",
     "Tapas de inspección, tapas para tanque y fabricaciones especiales bajo medida.", 9),
]

# (sku, nombre, categoria, descripcion, especificaciones, material, imagen, destacado)
PRODUCTOS = [
    # --- EQUIPOS INDUSTRIALES ---
    ("EI-001", "Mesa de Trabajo en Acero Inoxidable", "equipos-industriales",
     "Mesa de trabajo en acero inoxidable calibre 304, ideal para cocinas industriales, "
     "restaurantes y plantas de procesamiento de alimentos.",
     "Cubierta en lámina de acero inoxidable AISI 304 cal. 18 · Patas en tubo redondo de 1 1/2\" "
     "· Niveladores plásticos · Refuerzo estructural inferior · Medidas bajo pedido",
     "Acero inoxidable 304", "mesa-de-trabajo.jpg", 1),
    ("EI-002", "Mesa con Doble Entrepaño", "equipos-industriales",
     "Mesa de trabajo con dos entrepaños inferiores para máximo aprovechamiento del espacio "
     "en cocinas y áreas de producción.",
     "Cubierta y entrepaños en acero inoxidable AISI 304 · Estructura en tubo cuadrado "
     "· Entrepaños reforzados · Medidas bajo pedido", "Acero inoxidable 304",
     "mesa-con-doble-entrepanp.jpg", 1),
    ("EI-003", "Mueble Bajo con Cajones", "equipos-industriales",
     "Mueble bajo en acero inoxidable con cajones sobre rieles telescópicos, para almacenamiento "
     "de utensilios en línea caliente y fría.",
     "Cuerpo en acero inoxidable AISI 304 · Cajones con rieles telescópicos de extensión total "
     "· Halador integrado · Configuración de cajones bajo pedido", "Acero inoxidable 304",
     "mueble-bajo-con-cajones.jpg", 0),
    ("EI-004", "Mueble Bajo con Pozuelo de Lavado", "equipos-industriales",
     "Mueble bajo con pozuelo de lavado embutido, entrepaño inferior y espaldar sanitario.",
     "Pozuelo embutido sin soldadura visible · Desagüe de 2\" con rebosadero "
     "· Espaldar sanitario de 10 cm · Entrepaño inferior", "Acero inoxidable 304",
     "mueble-bajo-con-pozuelo-de-lavado.jpg", 0),
    ("EI-005", "Pozuelo de Lavado", "equipos-industriales",
     "Pozuelo de lavado en acero inoxidable, sencillo o múltiple, con o sin escurridero.",
     "Pozuelos embutidos en una sola pieza · Esquinas sanitarias redondeadas "
     "· Desagüe de 2\" · Escurridero opcional a izquierda o derecha", "Acero inoxidable 304",
     "pozuelo-de-lvado.jpg", 0),
    ("EI-006", "Cubierta con Pozuelo de Lavado", "equipos-industriales",
     "Cubierta en acero inoxidable con pozuelo integrado, fabricada a la medida del espacio.",
     "Lámina cal. 18 AISI 304 · Pozuelo embutido integrado · Bordes con doblez sanitario "
     "· Perforaciones para grifería según requerimiento", "Acero inoxidable 304",
     "cubierta-on-pozuelo-de-lavado.jpg", 0),
    ("EI-007", "Cubierta en Acero Inoxidable", "equipos-industriales",
     "Cubiertas y mesones en acero inoxidable a la medida para cocinas, laboratorios y "
     "áreas de proceso.",
     "Lámina AISI 304 cal. 18 o 16 · Refuerzo interno en madera tratada o estructura metálica "
     "· Acabado satinado · Medidas y cortes bajo pedido", "Acero inoxidable 304",
     "cubierta-en-acero-inoxidable.jpg", 0),
    ("EI-008", "Campana de Extracción", "equipos-industriales",
     "Campana de extracción de humos y grasas en acero inoxidable, con filtros tipo bafle "
     "y ducto de descarga.",
     "Cuerpo en acero inoxidable AISI 304 · Filtros tipo bafle desmontables y lavables "
     "· Canal recolector de grasas · Iluminación estanca opcional · Extractor centrífugo "
     "según caudal", "Acero inoxidable 304", "campana-de-extracicon.jpg", 1),
    ("EI-009", "Estantería para Cuartos Fríos", "equipos-industriales",
     "Estantería modular en acero inoxidable para cuartos fríos y congelación, resistente "
     "a la humedad.",
     "Parales en ángulo o tubo de acero inoxidable · Entrepaños lisos o perforados "
     "· Altura y número de niveles configurable · Niveladores en material sanitario",
     "Acero inoxidable 304", "estanteria-para-cuartos-frios.jpg", 0),
    ("EI-010", "Estanterías Lisas", "equipos-industriales",
     "Estanterías lisas en acero inoxidable para almacenamiento de insumos y vajilla.",
     "Entrepaños en lámina lisa AISI 304 · Estructura en tubo cuadrado · 3 a 5 niveles "
     "· Medidas bajo pedido", "Acero inoxidable 304", "estanterias-lisas.jpg", 0),
    ("EI-011", "Estufa 6 Boquillas con Plancha", "equipos-industriales",
     "Estufa industrial de 6 boquillas con plancha asadora integrada y horno inferior opcional.",
     "Quemadores de alta presión en hierro fundido · Plancha en acero al carbón de 3/4\" "
     "· Perillas de control independiente · Estructura y frente en acero inoxidable "
     "· Gas natural o propano", "Acero inoxidable / hierro fundido",
     "estufa-6-q-con-plancha.jpg", 1),

    # --- EQUIPOS HOSPITALARIOS ---
    ("EH-001", "Lavamanos Quirúrgico de Pedal", "equipos-hospitalarios",
     "Lavamanos quirúrgico accionado por pedal, para áreas de lavado de manos prequirúrgico.",
     "Pozuelo embutido profundo en AISI 304 · Accionamiento por pedal sin contacto manual "
     "· Grifería tipo cuello de ganso · Espaldar sanitario · Anclaje a piso o pared",
     "Acero inoxidable 304", "img-20200215-wa0032.jpg", 1),
    ("EH-002", "Lavamanos Quirúrgico Doble", "equipos-hospitalarios",
     "Lavamanos quirúrgico de dos puestos para salas de cirugía, con accionamiento por pedal "
     "o sensor.",
     "Dos pozuelos embutidos en una sola lámina · Accionamiento por pedal o sensor infrarrojo "
     "· Espaldar sanitario alto · Sifones y desagües incluidos", "Acero inoxidable 304",
     "lavamanos-quirurgico-doble.jpg", 1),
    ("EH-003", "Lavamanos Quirúrgico de Empotrar", "equipos-hospitalarios",
     "Lavamanos quirúrgico para empotrar en muro, de fácil limpieza y desinfección.",
     "Empotrable a muro · Pozuelo embutido sin uniones · Esquinas sanitarias "
     "· Grifería y accionamiento según especificación del cliente", "Acero inoxidable 304",
     "lavamanos-quirurgico-de-empotrar.jpg", 0),
    ("EH-004", "Mesa de Trabajo Hospitalaria", "equipos-hospitalarios",
     "Mesa de trabajo en acero inoxidable para centrales de esterilización, laboratorios "
     "y áreas asistenciales.",
     "Cubierta en AISI 304 cal. 18 · Estructura tubular sanitaria · Entrepaño inferior opcional "
     "· Acabado satinado apto para desinfección", "Acero inoxidable 304",
     "mesa-de-trabajo.jpg", 0),
    ("EH-005", "Mueble Bajo Hospitalario con Cajones", "equipos-hospitalarios",
     "Mueble bajo en acero inoxidable con cajones para almacenamiento de insumos médicos.",
     "Cuerpo en AISI 304 · Cajones sobre rieles telescópicos · Superficie continua sin "
     "aristas · Zócalo sanitario", "Acero inoxidable 304", "mueble-bajo-con-cajones.jpg", 0),
    ("EH-006", "Mesa Hospitalaria con Doble Entrepaño", "equipos-hospitalarios",
     "Mesa con doble entrepaño para áreas de apoyo clínico y centrales de esterilización.",
     "Cubierta y dos entrepaños en AISI 304 · Estructura reforzada · Ruedas con freno "
     "opcionales · Medidas bajo pedido", "Acero inoxidable 304",
     "mesa-con-doble-entrpano.jpg", 0),

    # --- MOBILIARIO URBANO ---
    ("MU-001", "Banca en Acero Inoxidable", "mobiliario-urbano",
     "Banca para espacio público y zonas comunes, en acero inoxidable de alta resistencia "
     "a la intemperie.",
     "Estructura en tubo de acero inoxidable AISI 304 · Listones en inoxidable o madera "
     "inmunizada · Anclaje a piso con pernos de expansión · Acabado satinado o pulido espejo",
     "Acero inoxidable 304", "banca-ena-cero-inoxidable.jpg", 1),
    ("MU-002", "Basureros Públicos", "mobiliario-urbano",
     "Basureros para espacio público en acero inoxidable, con canasta interna removible.",
     "Cuerpo en acero inoxidable AISI 304 · Canasta interna removible "
     "· Anclaje a piso o poste · Tapa superior con protección de lluvia",
     "Acero inoxidable 304", "basureros-publicos.jpg", 0),
    ("MU-003", "Basurero Doble Exterior", "mobiliario-urbano",
     "Punto ecológico de dos canecas para separación de residuos en exteriores.",
     "Dos compartimentos con señalización de separación · Estructura en acero inoxidable "
     "· Canastas internas removibles · Techo integrado", "Acero inoxidable 304",
     "basurero-doble-exterior.jpg", 0),
    ("MU-004", "Rack para Bicicleta en Acero Inoxidable", "mobiliario-urbano",
     "Cicloparqueadero en acero inoxidable para instalación en andenes, parques y "
     "conjuntos residenciales.",
     "Tubo de acero inoxidable AISI 304 de 2\" · Capacidad configurable "
     "· Anclaje a piso con platina y pernos · Resistente a la intemperie",
     "Acero inoxidable 304", "rack-bicicleta-acero-inoxidable.jpg", 1),
    ("MU-005", "Rack para Bicicleta", "mobiliario-urbano",
     "Rack para bicicletas en acero al carbón con acabado en pintura electrostática.",
     "Tubo estructural en acero al carbón · Pintura electrostática horneada "
     "· Capacidad configurable · Anclaje a piso", "Acero al carbón",
     "rack-bicicleta.jpg", 0),

    # --- BARANDAS Y PASAMANOS ---
    ("BP-001", "Pasamanos en Acero Inoxidable", "barandas-pasamanos",
     "Pasamanos y barandas en acero inoxidable para escaleras, rampas y balcones.",
     "Tubo de acero inoxidable AISI 304 · Parales y accesorios tipo Inox "
     "· Acabado satinado o pulido espejo · Instalación incluida · Fabricación a la medida",
     "Acero inoxidable 304", "pasamanos-en-acero.jpg", 1),
    ("BP-002", "Pasamanos en Vidrio", "barandas-pasamanos",
     "Baranda en vidrio templado con herrajes y pasamanos en acero inoxidable.",
     "Vidrio templado de 8, 10 o 12 mm · Herrajes tipo araña o pisavidrio en acero inoxidable "
     "· Pasamanos superior en tubo redondo · Cálculo estructural incluido",
     "Vidrio templado / acero inoxidable", "pasamanos-en-vidrio.jpg", 1),
    ("BP-003", "Pasamanos en Acero al Carbón", "barandas-pasamanos",
     "Pasamanos en acero al carbón con acabado en pintura electrostática o esmalte industrial.",
     "Tubo estructural en acero al carbón · Preparación de superficie y anticorrosivo "
     "· Acabado en pintura electrostática · Instalación incluida", "Acero al carbón",
     "pasamanos-en-acero-1.jpg", 0),

    # --- ESTRUCTURAS METÁLICAS ---
    ("EM-001", "Estructura Metálica", "estructuras-metalicas",
     "Diseño, fabricación y montaje de estructura metálica para bodegas, edificios y "
     "cubiertas industriales.",
     "Perfilería estructural según diseño · Soldadura con proceso certificado "
     "· Preparación de superficie y anticorrosivo · Montaje con personal certificado en alturas "
     "· Incluye planos de taller", "Acero estructural ASTM A36 / A572",
     "estructuras-metalicas2.jpg", 1),
    ("EM-002", "Mezzanines y Entrepisos Metálicos", "estructuras-metalicas",
     "Mezzanines y entrepisos metálicos para ampliar el área útil de bodegas y locales.",
     "Vigas y viguetas en perfil estructural · Lámina alfajor o steel deck "
     "· Escalera de acceso y baranda · Cálculo y planos estructurales",
     "Acero estructural ASTM A36", "whatsapp-image-2021-04-12-at-4-12-18-pm.jpg", 0),
    ("EM-003", "Escaleras Metálicas", "estructuras-metalicas",
     "Escaleras metálicas rectas, en U o de caracol, con pasamanos integrado.",
     "Zancas en platina o perfil estructural · Peldaños en lámina alfajor o rejilla "
     "· Pasamanos en acero inoxidable o acero al carbón · Acabado en pintura electrostática",
     "Acero estructural", "whatsapp-image-2021-04-12-at-4-14-37-pm.jpg", 0),
    ("EM-004", "Torres y Estructuras Especiales", "estructuras-metalicas",
     "Torres, soportes y estructuras especiales para equipos industriales y telecomunicaciones.",
     "Diseño y cálculo estructural · Fabricación en taller · Galvanizado en caliente opcional "
     "· Montaje e izaje con equipo propio", "Acero estructural",
     "whatsapp-image-2021-04-12-at-4-20-04-pm.jpg", 0),
    ("EM-005", "Pérgolas y Cubiertas", "estructuras-metalicas",
     "Pérgolas y cubiertas en todo tipo de tejas y en policarbonato.",
     "Estructura en perfil estructural o tubo · Cubierta en teja termoacústica, "
     "traslúcida o policarbonato · Canales y bajantes · Instalación incluida",
     "Acero estructural", "4538f98e75ef558a15d70264bde524d0.jpg", 0),

    # --- PUERTAS Y DIVISIONES ---
    ("PD-001", "Puertas para Baño en Acero Inoxidable", "puertas-metalicas",
     "Divisiones y puertas para baño en acero inoxidable, para uso institucional y comercial.",
     "Paneles en acero inoxidable AISI 304 · Herrajes en inoxidable "
     "· Sistema de cierre con indicador libre/ocupado · Instalación incluida",
     "Acero inoxidable 304",
     "6579f67b2dd33e-divisiones-para-bano-en-acero-inoxidable-284773-4.jpg", 0),
    ("PD-002", "Puertas de Seguridad en Acero Inoxidable", "puertas-metalicas",
     "Puertas de seguridad de servicio pesado en acero inoxidable para accesos industriales "
     "e institucionales.",
     "Hoja en lámina de acero inoxidable con refuerzo interno · Marco estructural "
     "· Bisagras de servicio pesado · Cerradura de alta seguridad",
     "Acero inoxidable 304",
     "double-steel-security-door-heavy-duty-doorset-by-npm-sinoph-154-dv-p.jpg", 0),
    ("PD-003", "Cortinas Enrollables Metálicas", "puertas-metalicas",
     "Cortinas enrollables metálicas manuales o automáticas para locales y bodegas.",
     "Lámina en acero galvanizado o inoxidable · Operación manual o motorizada "
     "· Guías laterales y eje con resortes balanceados · Cerradura de piso",
     "Acero galvanizado",
     "ads-puertas-portones-automaticos-cortina-enrollable-metalica-cortina-enrollable-metalica-1463787.jpg", 0),
    ("PD-004", "Separadores de Orinal", "puertas-metalicas",
     "Separadores de orinal en acero inoxidable para baños institucionales.",
     "Lámina en acero inoxidable AISI 304 · Bordes pulidos "
     "· Anclaje a muro con herrajes en inoxidable · Medidas estándar o bajo pedido",
     "Acero inoxidable 304", "banca-acero.jpg", 0),

    # --- OBRAS CIVILES ---
    ("OC-001", "Losas en Concreto", "obras-civiles",
     "Losas en concreto de todo tipo: aligeradas, bloquelón, velilla y casetón.",
     "Losa aligerada, bloquelón, velilla o casetón · Suministro de acero de refuerzo "
     "· Formaleta y vaciado · Ensayos de resistencia · Personal técnico calificado",
     "Concreto / acero de refuerzo", "whatsapp-image-2021-04-12-at-4-12-18-pm.jpg", 0),
    ("OC-002", "Acabados en Obra Blanca", "obras-civiles",
     "Acabados en obra blanca: enchapes, estucos, pinturas y cielos falsos en PVC.",
     "Enchape de pisos y muros · Estuco y pintura · Cielo falso en PVC o drywall "
     "· Cuadrillas propias · Cronograma y actas de avance", "Varios",
     "whatsapp-image-2021-04-12-at-4-14-37-pm.jpg", 0),
    ("OC-003", "Cámaras y Trampas de Grasa · UARs", "obras-civiles",
     "Construcción de cámaras de inspección, trampas de grasa y unidades de "
     "almacenamiento de residuos.",
     "Diseño según normativa ambiental local · Construcción en concreto impermeabilizado "
     "· Tapas en acero inoxidable o concreto · Entrega con planos récord",
     "Concreto / acero inoxidable", "tapa-insp.jpg", 0),
    ("OC-004", "Fachadas en Alucobond", "obras-civiles",
     "Fachadas ventiladas en lámina compuesta de aluminio tipo Alucobond.",
     "Subestructura en aluminio · Lámina compuesta de 4 mm "
     "· Sistema de junta abierta o sellada · Diseño y despiece incluido",
     "Aluminio compuesto", "estructuras-metalicas2.jpg", 0),

    # --- EXTRACCIÓN DE NÚCLEOS ---
    ("EN-001", "Extracción de Núcleos y Pasanúcleos", "extraccion-nucleos",
     "Perforación y extracción de núcleos en losas, pantallas en concreto y cimentaciones. "
     "Servicio a todo el suroccidente colombiano.",
     "Perforación desde 1\" hasta 9\" de diámetro · Equipo de perforación diamantada "
     "· Corte sin vibración ni daño estructural · Extracción de testigos para ensayo "
     "· Trabajo en losas, pantallas y cimentación", "Servicio",
     "tapas-de-acero-inoxidable-para-tanque-eq0.jpg", 1),

    # --- OTROS ---
    ("OT-001", "Tapas de Inspección", "otros",
     "Tapas de inspección en acero inoxidable o acero al carbón, herméticas o estándar.",
     "Marco y tapa en acero inoxidable o acero al carbón · Sistema hermético opcional "
     "· Acabado para recibir enchape · Medidas bajo pedido", "Acero inoxidable 304",
     "tapa-insp.jpg", 0),
    ("OT-002", "Tapas de Acero Inoxidable para Tanque", "otros",
     "Tapas sanitarias en acero inoxidable para tanques de almacenamiento de agua potable.",
     "Lámina en acero inoxidable AISI 304 · Diseño sanitario con traslapo antiingreso "
     "· Bisagras y portacandado en inoxidable · Ventilación con malla",
     "Acero inoxidable 304", "tapas-de-acero-inoxidable-para-tanque-eq0.jpg", 0),
    ("OT-003", "Fabricación Especial Bajo Medida", "otros",
     "¿No encuentra lo que busca? Fabricamos bajo plano o bajo su necesidad específica.",
     "Envíenos su plano, foto o descripción · Asesoría técnica en materiales y acabados "
     "· Cotización sin costo · 30 años de experiencia en el suroccidente colombiano",
     "Según requerimiento", "cubierta-ena-cero-inoxidable.jpg", 0),
]


def sembrar_catalogo() -> None:
    for slug, nombre, desc, orden in CATEGORIAS:
        db.ex("INSERT OR IGNORE INTO categorias(slug,nombre,descripcion,orden) VALUES(?,?,?,?)",
              (slug, nombre, desc, orden))
    cats = {c["slug"]: c["id"] for c in db.q("SELECT id,slug FROM categorias")}
    for sku, nombre, cat, desc, espec, material, imagen, destacado in PRODUCTOS:
        db.ex("""INSERT OR IGNORE INTO productos
                 (sku,slug,nombre,categoria_id,descripcion,especificaciones,material,
                  imagen,destacado,precio,a_pedido)
                 VALUES(?,?,?,?,?,?,?,?,?,0,1)""",
              (sku, slugify(nombre), nombre, cats[cat], desc, espec, material,
               f"productos/{imagen}", destacado))


def sembrar_config() -> None:
    for k, v in EMPRESA_DEFAULT.items():
        if not db.q1("SELECT 1 FROM config WHERE clave=?", (f"empresa.{k}",)):
            db.set_config(f"empresa.{k}", v)


def sembrar_usuarios() -> None:
    if not db.q1("SELECT 1 FROM usuarios WHERE rol='admin'"):
        crear_usuario("admin@imatecsas.com", "Imatec2026*", "Administrador IMATEC", "admin")


def sembrar_todo() -> None:
    db.init_db()
    db.init_materiales()
    sembrar_config()
    sembrar_catalogo()
    sembrar_materiales_en_catalogo()
    sembrar_ferreteria()
    sembrar_usuarios()


# =====================================================================
#  Publicar el inventario de materiales en el catálogo de la web.
#  Cada "familia" es un producto del catálogo; sus diámetros salen en
#  vivo del inventario, con la existencia real de bodega.
# =====================================================================
CATEGORIA_MATERIALES = ("tuberia-y-materiales", "Tubería y Materiales",
                        "Tubería en acero galvanizado, acero al carbón y acero inoxidable 304 y "
                        "316, en calibres SCH10, SCH40 y SCH80, desde 1/4\" hasta 10\". "
                        "Venta por metro con despacho desde nuestra bodega en Cali.", 10)

# (sku, nombre, prefijo_sku_inventario, descripción, especificaciones, material, imagen)
FAMILIAS_MATERIAL = [
    ("TUB-GAL", "Tubería Galvanizada", "TUB-GAL-",
     "Tubería en acero galvanizado por inmersión en caliente, para conducción de agua, "
     "estructuras livianas, barandas y redes contra incendio. Disponible de 1/4\" a 6\".",
     "Acero galvanizado por inmersión en caliente · Recubrimiento de zinc resistente a la "
     "corrosión · Roscable · Venta por metro o por tubo de 6 m · Diámetros de 1/4\" a 6\" "
     "· Existencia real consultable en la tabla",
     "Acero galvanizado", "materiales/galvanizada.jpg"),

    ("TUB-AC40", "Tubería Acero al Carbón SCH40 sin costura", "TUB-AC-",
     "Tubería de acero al carbón sin costura, cédula 40. La más usada en conducción de "
     "fluidos, vapor de baja presión y estructuras. Disponible de 1/4\" a 10\".",
     "Acero al carbón sin costura (S/C) · Cédula SCH40 · Apta para soldadura y roscado "
     "· Norma ASTM A106 / A53 · Venta por metro · Diámetros de 1/4\" a 10\"",
     "Acero al carbón", "materiales/acero-carbon.jpg"),

    ("TUB-AC80", "Tubería Acero al Carbón SCH80 sin costura", "TUB-AC80-",
     "Tubería de acero al carbón sin costura, cédula 80: pared más gruesa que la SCH40, "
     "para mayor presión de trabajo. Disponible de 1/4\" a 10\".",
     "Acero al carbón sin costura (S/C) · Cédula SCH80 (pared reforzada) · Mayor presión "
     "de trabajo que la SCH40 · Norma ASTM A106 / A53 · Venta por metro "
     "· Diámetros de 1/4\" a 10\"",
     "Acero al carbón", "materiales/acero-carbon-2.jpg"),

    ("TUB-IN10-304", "Tubería Inoxidable 304 SCH10", "TUB-IN10-304-",
     "Tubería en acero inoxidable AISI 304, cédula 10 (pared delgada). Ideal para "
     "industria de alimentos, cocinas industriales y estructuras sanitarias.",
     "Acero inoxidable AISI 304 · Cédula SCH10 (pared delgada) · Acabado sanitario "
     "· Apta para industria de alimentos y bebidas · Venta por metro "
     "· Diámetros de 1/4\" a 10\"",
     "Acero inoxidable 304", "materiales/inoxidable.jpg"),

    ("TUB-IN10-316", "Tubería Inoxidable 316 SCH10", "TUB-IN10-316-",
     "Tubería en acero inoxidable AISI 316, cédula 10. El 316 resiste mejor los cloruros "
     "y ambientes químicos que el 304.",
     "Acero inoxidable AISI 316 (con molibdeno) · Cédula SCH10 · Mayor resistencia a "
     "cloruros y ambientes salinos o químicos · Venta por metro "
     "· Diámetros de 1/4\" a 10\"",
     "Acero inoxidable 316", "materiales/inoxidable.jpg"),

    ("TUB-IN40-304", "Tubería Inoxidable 304 SCH40", "TUB-IN40-304-",
     "Tubería en acero inoxidable AISI 304, cédula 40. Pared estándar, para conducción "
     "y estructuras que exigen resistencia a la corrosión.",
     "Acero inoxidable AISI 304 · Cédula SCH40 (pared estándar) · Soldable "
     "· Resistente a la corrosión · Venta por metro · Diámetros de 1/4\" a 10\"",
     "Acero inoxidable 304", "materiales/inoxidable.jpg"),

    ("TUB-IN40-316", "Tubería Inoxidable 316 SCH40", "TUB-IN40-316-",
     "Tubería en acero inoxidable AISI 316, cédula 40. Para procesos químicos, "
     "farmacéuticos y ambientes marinos.",
     "Acero inoxidable AISI 316 (con molibdeno) · Cédula SCH40 · Para procesos químicos "
     "y ambientes agresivos · Venta por metro · Diámetros de 1/4\" a 10\"",
     "Acero inoxidable 316", "materiales/inoxidable.jpg"),

    ("TUB-IN80", "Tubería Inoxidable SCH80", "TUB-IN80-",
     "Tubería en acero inoxidable cédula 80, de pared reforzada, para las aplicaciones "
     "de mayor exigencia mecánica y de presión.",
     "Acero inoxidable · Cédula SCH80 (pared reforzada) · Mayor presión de trabajo "
     "· Venta por metro · Diámetros de 1/4\" a 10\"",
     "Acero inoxidable", "materiales/inoxidable.jpg"),
]


def sembrar_materiales_en_catalogo() -> None:
    slug, nombre, desc, orden = CATEGORIA_MATERIALES
    db.ex("INSERT OR IGNORE INTO categorias(slug,nombre,descripcion,orden) VALUES(?,?,?,?)",
          (slug, nombre, desc, orden))
    cat_id = db.q1("SELECT id FROM categorias WHERE slug=?", (slug,))["id"]

    for sku, nom, grupo, descripcion, espec, material, imagen in FAMILIAS_MATERIAL:
        # sólo se publica la familia si hay ítems de ese grupo en el inventario
        if not db.scalar("SELECT COUNT(*) FROM materiales WHERE sku LIKE ? AND activo=1",
                         (grupo + "%",)):
            continue
        existente = db.q1("SELECT id FROM productos WHERE sku=?", (sku,))
        if existente:
            db.ex("""UPDATE productos SET nombre=?,categoria_id=?,descripcion=?,
                     especificaciones=?,material=?,grupo_sku=?,unidad='Metros' WHERE id=?""",
                  (nom, cat_id, descripcion, espec, material, grupo, existente["id"]))
        else:
            db.ex("""INSERT INTO productos
                     (sku,slug,nombre,categoria_id,descripcion,especificaciones,material,
                      unidad,precio,iva_pct,a_pedido,dias_entrega,imagen,grupo_sku,destacado)
                     VALUES(?,?,?,?,?,?,?,'Metros',0,19,0,3,?,?,0)""",
                  (sku, slugify(nom), nom, cat_id, descripcion, espec, material, imagen, grupo))


# =====================================================================
#  FERRETERÍA INDUSTRIAL
#  IMATEC ya no es sólo taller de fabricación: hoy vende accesorios,
#  bridas, válvulas, sistema ranurado, PVC/CPVC y polietileno.
#  Estas son las líneas que se ven en su bodega.
# =====================================================================
CATEGORIAS_FERRETERIA = [
    ("accesorios-acero-carbon", "Accesorios en Acero al Carbón",
     "Codos, tees, reducciones, uniones, niples y tapones en acero al carbón, roscados y "
     "para soldar, en cédula 40 y 80.", 11),
    ("accesorios-inoxidable", "Accesorios en Acero Inoxidable",
     "Codos, tees, reducciones, uniones y niples en acero inoxidable AISI 304 y 316, "
     "para industria de alimentos, farmacéutica y química.", 12),
    ("bridas", "Bridas y Empaquetadura",
     "Bridas slip-on, ciegas, de cuello soldable y roscadas, con su empaquetadura y "
     "tornillería. Diferentes librajes.", 13),
    ("valvulas", "Válvulas",
     "Válvulas de compuerta, bola, mariposa y cheque, en bronce, hierro dúctil y acero "
     "inoxidable, roscadas, bridadas y ranuradas.", 14),
    ("sistema-ranurado", "Sistema Ranurado",
     "Acoples rígidos y flexibles, codos, tees y reducciones ranuradas para redes contra "
     "incendio y conducción, con montaje rápido y sin soldadura.", 15),
    ("pvc-cpvc", "PVC y CPVC",
     "Tubería y accesorios en PVC presión, PVC sanitario y CPVC para agua caliente.", 16),
    ("polietileno", "Polietileno HDPE",
     "Tubería HDPE en rollo y accesorios de compresión y electrofusión para acueducto, "
     "riego y conducción enterrada.", 17),
    ("uniones-reparacion", "Uniones y Acoples de Reparación",
     "Uniones tipo Dresser, acoples y abrazaderas de reparación para intervenir redes "
     "sin cortar el tramo completo.", 18),
]

# (sku, nombre, categoría, descripción, especificaciones, material)
PRODUCTOS_FERRETERIA = [
    # --- ACCESORIOS ACERO AL CARBÓN ---
    ("AC-COD90", "Codo 90° Acero al Carbón", "accesorios-acero-carbon",
     "Codo de 90 grados en acero al carbón para cambio de dirección en redes de conducción.",
     "Radio largo y radio corto · Cédula 40 y 80 · Para soldar a tope, socket weld o roscado "
     "· Diámetros de 1/2\" a 10\" · Norma ASTM A234 WPB",
     "Acero al carbón"),
    ("AC-COD45", "Codo 45° Acero al Carbón", "accesorios-acero-carbon",
     "Codo de 45 grados en acero al carbón, para desvíos suaves que reducen la pérdida de carga.",
     "Cédula 40 y 80 · Para soldar a tope, socket weld o roscado · Diámetros de 1/2\" a 10\" "
     "· Norma ASTM A234 WPB", "Acero al carbón"),
    ("AC-TEE", "Tee Acero al Carbón", "accesorios-acero-carbon",
     "Tee en acero al carbón para derivación de la línea, recta o reducida.",
     "Tee recta y tee reducida · Cédula 40 y 80 · Para soldar o roscada "
     "· Diámetros de 1/2\" a 10\"", "Acero al carbón"),
    ("AC-RED", "Reducción Acero al Carbón", "accesorios-acero-carbon",
     "Reducción concéntrica y excéntrica para el cambio de diámetro de la tubería.",
     "Concéntrica y excéntrica · Cédula 40 y 80 · Para soldar o roscada (bushing) "
     "· Combinaciones de 1/2\" a 10\"", "Acero al carbón"),
    ("AC-UNI", "Unión y Copla Acero al Carbón", "accesorios-acero-carbon",
     "Uniones, coplas y uniones universales para empalmar tramos de tubería.",
     "Copla roscada y para soldar · Unión universal de asiento cónico y plano "
     "· Media unión · Diámetros de 1/2\" a 6\"", "Acero al carbón"),
    ("AC-NIP", "Niple y Tapón Acero al Carbón", "accesorios-acero-carbon",
     "Niples roscados a la medida y tapones macho y hembra para cierre de línea.",
     "Niple corrido y niple a la medida · Tapón macho y hembra · Casquete (cap) para soldar "
     "· Diámetros de 1/2\" a 6\"", "Acero al carbón"),

    # --- ACCESORIOS INOXIDABLE ---
    ("IN-COD", "Codos Acero Inoxidable 304 y 316", "accesorios-inoxidable",
     "Codos de 90° y 45° en acero inoxidable, para líneas sanitarias y de proceso.",
     "AISI 304 y 316 · 90° y 45° · Cédula 10, 40 y 80 · Para soldar, roscado o sanitario "
     "clamp · Diámetros de 1/2\" a 10\"", "Acero inoxidable 304 / 316"),
    ("IN-TEE", "Tee Acero Inoxidable 304 y 316", "accesorios-inoxidable",
     "Tees en acero inoxidable para derivación en líneas de alimentos y proceso químico.",
     "AISI 304 y 316 · Tee recta y reducida · Cédula 10, 40 y 80 "
     "· Acabado sanitario disponible · Diámetros de 1/2\" a 10\"",
     "Acero inoxidable 304 / 316"),
    ("IN-RED", "Reducción Acero Inoxidable", "accesorios-inoxidable",
     "Reducciones concéntricas y excéntricas en acero inoxidable.",
     "AISI 304 y 316 · Concéntrica y excéntrica · Cédula 10, 40 y 80 "
     "· Combinaciones de 1/2\" a 10\"", "Acero inoxidable 304 / 316"),
    ("IN-UNI", "Unión, Copla y Niple Inoxidable", "accesorios-inoxidable",
     "Uniones, coplas, niples y tapones en acero inoxidable.",
     "AISI 304 y 316 · Copla roscada y para soldar · Unión universal · Niple a la medida "
     "· Tapón macho y hembra · Diámetros de 1/2\" a 6\"", "Acero inoxidable 304 / 316"),
    ("IN-CLAMP", "Accesorios Sanitarios Clamp", "accesorios-inoxidable",
     "Accesorios sanitarios tipo clamp (abrazadera) para industria de alimentos, bebidas "
     "y farmacéutica: desmontaje rápido y limpieza total.",
     "AISI 304 y 316 · Ferrule, abrazadera y empaque · Acabado sanitario pulido "
     "· Codos, tees y reducciones clamp · Diámetros de 1/2\" a 4\"",
     "Acero inoxidable 304 / 316"),

    # --- BRIDAS ---
    ("BR-SO", "Brida Slip-On", "bridas",
     "Brida deslizante (slip-on) que se monta sobre la tubería y se suelda por dentro y "
     "por fuera. La más usada por su facilidad de alineación.",
     "Acero al carbón e inoxidable · Libraje 150, 300 y superiores "
     "· Cara realzada (RF) y cara plana (FF) · Norma ANSI/ASME B16.5 "
     "· Diámetros de 1/2\" a 24\"", "Acero al carbón / inoxidable"),
    ("BR-CIEGA", "Brida Ciega", "bridas",
     "Brida ciega para cerrar el extremo de una línea o dejar un punto de inspección.",
     "Acero al carbón e inoxidable · Libraje 150, 300 y superiores · RF y FF "
     "· Norma ANSI/ASME B16.5 · Diámetros de 1/2\" a 24\"",
     "Acero al carbón / inoxidable"),
    ("BR-WN", "Brida Cuello Soldable (Weld Neck)", "bridas",
     "Brida de cuello soldable, para servicio de alta presión y temperatura: transmite el "
     "esfuerzo a la tubería sin concentrarlo en la soldadura.",
     "Acero al carbón e inoxidable · Libraje 150, 300 y superiores · Cara realzada (RF) "
     "· Norma ANSI/ASME B16.5 · Diámetros de 1/2\" a 24\"",
     "Acero al carbón / inoxidable"),
    ("BR-ROSC", "Brida Roscada", "bridas",
     "Brida roscada para líneas donde no se puede soldar.",
     "Acero al carbón e inoxidable · Rosca NPT · Libraje 150 y 300 "
     "· Norma ANSI/ASME B16.5 · Diámetros de 1/2\" a 6\"",
     "Acero al carbón / inoxidable"),
    ("BR-EMP", "Empaquetadura y Tornillería para Brida", "bridas",
     "Empaques y juegos de tornillería del librage y diámetro que necesite su brida.",
     "Empaque en caucho, asbesto-free, teflón y grafito · Espiro-metálico "
     "· Juego de espárragos con tuercas · Todos los librajes y diámetros",
     "Varios"),

    # --- VÁLVULAS ---
    ("VA-COMP", "Válvula de Compuerta", "valvulas",
     "Válvula de compuerta para servicio de apertura y cierre total en redes de agua "
     "y conducción.",
     "Bronce, hierro dúctil y acero inoxidable · Roscada y bridada "
     "· Vástago fijo y ascendente · Recubrimiento epóxico en hierro dúctil "
     "· Diámetros de 1/2\" a 12\"", "Bronce / hierro dúctil / inoxidable"),
    ("VA-BOLA", "Válvula de Bola", "valvulas",
     "Válvula de bola de cuarto de vuelta, para corte rápido de la línea.",
     "Bronce, acero inoxidable y PVC · Roscada, bridada y clamp "
     "· Paso total y paso reducido · Una, dos y tres piezas "
     "· Diámetros de 1/2\" a 6\"", "Bronce / inoxidable / PVC"),
    ("VA-MAR", "Válvula Mariposa", "valvulas",
     "Válvula mariposa tipo wafer y lug, liviana y de operación rápida, para diámetros "
     "grandes.",
     "Cuerpo en hierro dúctil · Disco en inoxidable · Asiento en EPDM o Buna-N "
     "· Wafer y lug · Palanca, reductor o actuador "
     "· Diámetros de 2\" a 12\"", "Hierro dúctil / inoxidable"),
    ("VA-CHEQ", "Válvula Cheque", "valvulas",
     "Válvula de retención (cheque) que impide el retorno del fluido.",
     "Cheque de columpio, de disco y de bola · Bronce, hierro dúctil e inoxidable "
     "· Roscada, bridada y ranurada · Diámetros de 1/2\" a 12\"",
     "Bronce / hierro dúctil / inoxidable"),
    ("VA-PIE", "Válvula de Pie y Accesorios de Succión", "valvulas",
     "Válvula de pie con canastilla para succión de bombas.",
     "Bronce y hierro dúctil · Con canastilla de filtro · Roscada y bridada "
     "· Diámetros de 1\" a 8\"", "Bronce / hierro dúctil"),

    # --- SISTEMA RANURADO ---
    ("RA-ACOP", "Acople Ranurado Rígido y Flexible", "sistema-ranurado",
     "Acople ranurado para unir tubería sin soldar: montaje rápido, desmontable y con "
     "tolerancia a movimiento.",
     "Rígido y flexible · Cuerpo en hierro dúctil con pintura epóxica "
     "· Empaque en EPDM (agua) o Nitrilo (aceite) · Apto para red contra incendio "
     "· Diámetros de 1\" a 12\"", "Hierro dúctil"),
    ("RA-COD", "Codo Ranurado 90° y 45°", "sistema-ranurado",
     "Codos ranurados para cambio de dirección en sistemas de montaje rápido.",
     "90° y 45° · Hierro dúctil con pintura epóxica · Extremos ranurados "
     "· Diámetros de 1\" a 12\"", "Hierro dúctil"),
    ("RA-TEE", "Tee y Reducción Ranurada", "sistema-ranurado",
     "Tees, cruces y reducciones ranuradas para derivar la línea sin soldadura.",
     "Tee recta, tee reducida y cruz · Reducción concéntrica "
     "· Hierro dúctil con pintura epóxica · Diámetros de 1\" a 12\"", "Hierro dúctil"),
    ("RA-ACCS", "Accesorios Ranurados Especiales", "sistema-ranurado",
     "Tapas, niples, adaptadores brida-ranura y ranuradoras para completar el sistema.",
     "Tapa ranurada · Adaptador de brida a ranura · Niple ranurado "
     "· Servicio de ranurado de tubería en nuestro taller", "Hierro dúctil"),

    # --- PVC Y CPVC ---
    ("PV-TUB", "Tubería PVC Presión", "pvc-cpvc",
     "Tubería en PVC para conducción de agua a presión, en distintos RDE.",
     "RDE 21, 26, 32.5 y 41 · Unión mecánica y soldadura líquida "
     "· Norma NTC 382 · Diámetros de 1/2\" a 12\"", "PVC"),
    ("PV-ACC", "Accesorios PVC Presión", "pvc-cpvc",
     "Codos, tees, uniones, reducciones, adaptadores y tapones en PVC presión.",
     "Codo 90° y 45° · Tee y tee reducida · Unión y unión de reparación "
     "· Adaptador macho y hembra · Buje de reducción "
     "· Diámetros de 1/2\" a 12\"", "PVC"),
    ("PV-SAN", "Tubería y Accesorios PVC Sanitario", "pvc-cpvc",
     "Línea sanitaria en PVC para aguas residuales y ventilación.",
     "Tubería sanitaria y de ventilación · Codos, yees, tees sanitarias "
     "· Sifones y registros · Diámetros de 1 1/2\" a 8\"", "PVC sanitario"),
    ("PV-CPVC", "CPVC Agua Caliente", "pvc-cpvc",
     "Tubería y accesorios en CPVC para redes de agua caliente.",
     "Resistente hasta 82 °C · Tubería y accesorios completos "
     "· Soldadura líquida específica para CPVC · Diámetros de 1/2\" a 2\"", "CPVC"),

    # --- POLIETILENO ---
    ("PE-TUB", "Tubería HDPE en Rollo", "polietileno",
     "Tubería en polietileno de alta densidad, en rollo, para acueducto, riego y "
     "conducción enterrada. Resiste el movimiento del terreno sin fracturarse.",
     "PE100 y PE80 · RDE 9, 11, 13.6, 17, 21 y 26 · Presentación en rollo "
     "· Norma NTC 1747 · Diámetros de 1/2\" a 12\"", "Polietileno HDPE"),
    ("PE-ACC", "Accesorios HDPE de Compresión", "polietileno",
     "Accesorios de compresión para unir tubería HDPE sin equipo especial.",
     "Unión, codo, tee y adaptador de compresión · Adaptador macho y hembra "
     "· No requiere termofusión · Diámetros de 1/2\" a 4\"", "Polipropileno / HDPE"),
    ("PE-FUS", "Accesorios HDPE de Termofusión y Electrofusión", "polietileno",
     "Accesorios para unión soldada de tubería HDPE, la más confiable en redes enterradas.",
     "Codos, tees, reducciones y uniones a tope · Accesorios de electrofusión "
     "· Stub end y brida de respaldo · Servicio de termofusión disponible",
     "Polietileno HDPE"),

    # --- UNIONES DE REPARACIÓN ---
    ("UR-DRES", "Unión Dresser", "uniones-reparacion",
     "Unión tipo Dresser para empalmar dos tramos de tubería sin soldadura ni rosca, "
     "absorbiendo desalineación y dilatación.",
     "Cuerpo en acero o hierro dúctil con recubrimiento epóxico "
     "· Empaques y tornillería incluidos · Para tubería de acero, PVC y HDPE "
     "· Diámetros de 2\" a 12\"", "Acero / hierro dúctil"),
    ("UR-ACOP", "Acople de Reparación", "uniones-reparacion",
     "Acople de reparación para intervenir una fuga sin cortar el tramo completo.",
     "Cuerpo en hierro dúctil con pintura epóxica · Empaque de sello total "
     "· Tornillería en acero inoxidable · Diámetros de 2\" a 12\"",
     "Hierro dúctil / inoxidable"),
    ("UR-ABRA", "Abrazadera de Reparación", "uniones-reparacion",
     "Abrazadera de reparación que sella una perforación o fisura puntual en la tubería.",
     "Cuerpo y tornillería en acero inoxidable · Empaque en EPDM "
     "· Una y dos bandas · Diámetros de 1/2\" a 12\"", "Acero inoxidable"),
]


def sembrar_ferreteria() -> None:
    for slug, nombre, desc, orden in CATEGORIAS_FERRETERIA:
        db.ex("INSERT OR IGNORE INTO categorias(slug,nombre,descripcion,orden) VALUES(?,?,?,?)",
              (slug, nombre, desc, orden))
        db.ex("UPDATE categorias SET nombre=?,descripcion=?,orden=? WHERE slug=?",
              (nombre, desc, orden, slug))
    cats = {c["slug"]: c["id"] for c in db.q("SELECT id,slug FROM categorias")}
    for sku, nombre, cat, desc, espec, material in PRODUCTOS_FERRETERIA:
        if db.q1("SELECT 1 FROM productos WHERE sku=?", (sku,)):
            db.ex("""UPDATE productos SET nombre=?,categoria_id=?,descripcion=?,
                     especificaciones=?,material=? WHERE sku=?""",
                  (nombre, cats[cat], desc, espec, material, sku))
        else:
            db.ex("""INSERT INTO productos
                     (sku,slug,nombre,categoria_id,descripcion,especificaciones,material,
                      unidad,precio,iva_pct,a_pedido,dias_entrega,imagen,destacado)
                     VALUES(?,?,?,?,?,?,?,'UND',0,19,0,2,'',0)""",
                  (sku, slugify(nombre), nombre, cats[cat], desc, espec, material))
