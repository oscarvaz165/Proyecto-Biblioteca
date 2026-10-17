"""
Sistema de biblioteca
Funciones: inicio con resumen, alta, edición y baja de libros,
consulta del catálogo y reportes en Excel. Con login para el personal.

Cómo correrlo:
1. pip install -r requirements.txt
2. Tener .streamlit/secrets.toml con SUPABASE_URL y SUPABASE_KEY
3. streamlit run app.py
"""

import os
from datetime import datetime, timezone
from io import BytesIO

import pandas as pd
import streamlit as st
from supabase import create_client, Client

st.set_page_config(
    page_title="Biblioteca - Servicio Social",
    page_icon="📚",
    layout="wide",
)

# ------------------------------------------------------------------
# Estilos
# ------------------------------------------------------------------
st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    .hero {
        background: linear-gradient(120deg, #1F6F5C 0%, #2E8B73 100%);
        padding: 1.5rem 1.8rem;
        border-radius: 16px;
        margin-bottom: 1.4rem;
    }
    .hero h1, .hero p { color: #FFFFFF !important; margin: 0; padding: 0; }
    .hero p { opacity: 0.9; margin-top: 0.3rem; }
    [data-testid="stMetric"] {
        background: #F4F8F6;
        border: 1px solid #D5E2DC;
        border-left: 6px solid #1F6F5C;
        border-radius: 12px;
        padding: 14px 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Conexión a Supabase
# ------------------------------------------------------------------
@st.cache_resource
def get_client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


supabase = get_client()

# ------------------------------------------------------------------
# Login (usuarios creados en Supabase -> Authentication -> Users)
# ------------------------------------------------------------------
def pantalla_login():
    _, centro, _ = st.columns([1, 1.3, 1])
    with centro:
        st.markdown(
            "<div class='hero'><h1>📚 Sistema de Biblioteca</h1>"
            "<p>Inicia sesión para continuar</p></div>",
            unsafe_allow_html=True,
        )
        with st.form("login"):
            correo = st.text_input("Correo")
            clave = st.text_input("Contraseña", type="password")
            entrar = st.form_submit_button("Entrar")

        if entrar:
            usuario = None
            try:
                # Cliente temporal, para no mezclar sesiones entre usuarios
                temporal = create_client(
                    st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
                )
                r = temporal.auth.sign_in_with_password(
                    {"email": correo.strip(), "password": clave}
                )
                if r.user:
                    usuario = r.user.email
            except Exception:
                usuario = None

            if usuario:
                st.session_state["usuario"] = usuario
                st.rerun()
            else:
                st.error("Correo o contraseña incorrectos.")


if "usuario" not in st.session_state:
    pantalla_login()
    st.stop()

# ------------------------------------------------------------------
# Funciones auxiliares
# ------------------------------------------------------------------
COLUMNAS_VISTA = {
    "no_adquisicion": "No. de adquisición",
    "titulo": "Título",
    "subtitulo_volumen": "Subtítulo / volumen",
    "autor": "Autor",
    "editorial": "Editorial / pie de imprenta",
    "anio_publicacion": "Año",
    "signatura_topografica": "Signatura",
    "estado": "Estado",
}


def ahora():
    return datetime.now(timezone.utc).isoformat()


def vacio_a_none(texto):
    texto = (texto or "").strip()
    return texto or None


def traer_libros(estado=None):
    """Trae todos los libros (de 1000 en 1000, que es el límite de Supabase)."""
    todos, inicio, paso = [], 0, 1000
    while True:
        q = supabase.table("books").select("*")
        if estado and estado != "Todos":
            q = q.eq("estado", estado)
        res = q.order("no_adquisicion").range(inicio, inicio + paso - 1).execute()
        todos.extend(res.data)
        if len(res.data) < paso:
            break
        inicio += paso
    return todos


def contar(estado=None):
    q = supabase.table("books").select("id", count="exact")
    if estado:
        q = q.eq("estado", estado)
    return q.limit(1).execute().count or 0


def buscar_por_folio(folio):
    """Busca un libro por No. de adquisición, sin importar mayúsculas."""
    res = (
        supabase.table("books")
        .select("*")
        .ilike("no_adquisicion", folio.strip())
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def mostrar_flash():
    mensaje = st.session_state.pop("flash", None)
    if mensaje:
        st.success(mensaje)


# ------------------------------------------------------------------
# Menú lateral
# ------------------------------------------------------------------
INICIO = "🏠 Inicio"
ALTA = "➕ Alta de libro"
EDITAR = "✏️ Editar libro"
BAJA = "📤 Baja de libro"
CATALOGO = "🔎 Consultar catálogo"
REPORTE = "📄 Generar reporte"

with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=160)
    st.markdown("### 📚 Biblioteca")
    opcion = st.radio(
        "Menú",
        [INICIO, ALTA, EDITAR, BAJA, CATALOGO, REPORTE],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(f"Sesión: {st.session_state['usuario']}")
    if st.button("Cerrar sesión"):
        st.session_state.pop("usuario", None)
        st.rerun()

# ------------------------------------------------------------------
# INICIO
# ------------------------------------------------------------------
if opcion == INICIO:
    st.markdown(
        "<div class='hero'><h1>📚 Sistema de Biblioteca</h1>"
        "<p>Control del acervo: altas, bajas, consultas y reportes</p></div>",
        unsafe_allow_html=True,
    )
    mostrar_flash()

    total = contar()
    disponibles = contar("disponible")
    prestados = contar("prestado")
    bajas = contar("baja")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de ejemplares", total)
    c2.metric("Disponibles", disponibles)
    c3.metric("Prestados", prestados)
    c4.metric("Dados de baja", bajas)

    st.write("")
    izq, der = st.columns(2)
    with izq:
        st.markdown("#### Ejemplares por estado")
        datos = pd.DataFrame(
            {
                "Estado": ["Disponibles", "Prestados", "Baja"],
                "Ejemplares": [disponibles, prestados, bajas],
            }
        ).set_index("Estado")
        st.bar_chart(datos)
    with der:
        st.markdown("#### Últimos registrados")
        res = (
            supabase.table("books")
            .select("no_adquisicion,titulo,estado")
            .order("fecha_alta", desc=True)
            .limit(5)
            .execute()
        )
        if res.data:
            tabla = pd.DataFrame(res.data).rename(
                columns={
                    "no_adquisicion": "No. de adquisición",
                    "titulo": "Título",
                    "estado": "Estado",
                }
            )
            st.dataframe(tabla, hide_index=True)
        else:
            st.info("Todavía no hay libros registrados.")

# ------------------------------------------------------------------
# ALTA DE LIBRO
# ------------------------------------------------------------------
elif opcion == ALTA:
    st.subheader("➕ Registrar libro")
    mostrar_flash()
    st.caption(
        "Cada ejemplar (copia física) se registra con su propio No. de adquisición. "
        "Si el libro se está dando de baja al mismo tiempo, marca la casilla del final."
    )

    # Este contador cambia al guardar, para que el formulario quede vacío
    n = st.session_state.get("alta_n", 0)

    with st.form(f"form_alta_{n}"):
        no_adq = st.text_input(
            "No. de adquisición * (ej: A-400)",
            key=f"alta_no_{n}",
            help="Usa el mismo número que ya tiene el libro en su tarjeta física.",
        )
        titulo = st.text_input("Título *", key=f"alta_titulo_{n}")
        subtitulo = st.text_input("Subtítulo y/o número de volumen", key=f"alta_sub_{n}")
        autor = st.text_input(
            "Autor * (apellido paterno, apellido materno, nombre(s))",
            key=f"alta_autor_{n}",
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            lugar = st.text_input("Lugar de publicación", key=f"alta_lugar_{n}")
        with col2:
            editorial = st.text_input("Editorial", key=f"alta_edit_{n}")
        with col3:
            anio = st.text_input("Año", key=f"alta_anio_{n}")

        col4, col5 = st.columns(2)
        with col4:
            tarjeta = st.text_input("Número de tarjeta (si aplica)", key=f"alta_tarj_{n}")
        with col5:
            signatura = st.text_input("Signatura topográfica", key=f"alta_sig_{n}")

        st.divider()
        marcar_baja = st.checkbox(
            "Este libro se está dando de baja al mismo tiempo que se registra",
            key=f"alta_baja_{n}",
        )
        motivo = st.text_input(
            "Motivo de la baja (solo si marcaste la casilla de arriba)",
            key=f"alta_motivo_{n}",
        )

        enviado = st.form_submit_button("Guardar libro")

    if enviado:
        folio = no_adq.strip().upper()
        if not folio or not titulo.strip() or not autor.strip():
            st.error("No. de adquisición, título y autor son obligatorios.")
        else:
            datos = {
                "no_adquisicion": folio,
                "titulo": titulo.strip(),
                "subtitulo_volumen": vacio_a_none(subtitulo),
                "autor": autor.strip(),
                "lugar_publicacion": vacio_a_none(lugar),
                "editorial": vacio_a_none(editorial),
                "anio_publicacion": vacio_a_none(anio),
                "num_tarjeta": vacio_a_none(tarjeta),
                "signatura_topografica": vacio_a_none(signatura),
            }
            if marcar_baja:
                datos["estado"] = "baja"
                datos["fecha_baja"] = ahora()
                datos["motivo_baja"] = vacio_a_none(motivo) or "No especificado"

            try:
                supabase.table("books").insert(datos).execute()
            except Exception as e:
                if "duplicate" in str(e).lower() or "23505" in str(e):
                    st.error(f"Ya existe un libro con el No. de adquisición {folio}.")
                else:
                    st.error(f"No se pudo guardar: {e}")
            else:
                st.session_state["alta_n"] = n + 1
                st.session_state["flash"] = f"Libro {folio} guardado correctamente."
                st.rerun()

# ------------------------------------------------------------------
# EDITAR LIBRO
# ------------------------------------------------------------------
elif opcion == EDITAR:
    st.subheader("✏️ Editar libro")
    mostrar_flash()
    st.caption(
        "Corrige los datos de un libro ya registrado. "
        "El No. de adquisición no se puede cambiar desde aquí."
    )

    folio_buscar = st.text_input("No. de adquisición del libro (ej: A-400)")

    if folio_buscar.strip():
        libro = buscar_por_folio(folio_buscar)

        if not libro:
            st.warning("No se encontró ningún libro con ese número de adquisición.")
        else:
            k = libro["id"]
            st.info(f"**{libro['no_adquisicion']}** · Estado actual: **{libro['estado']}**")

            with st.form(f"form_editar_{k}"):
                titulo = st.text_input("Título *", value=libro["titulo"] or "", key=f"e_titulo_{k}")
                subtitulo = st.text_input(
                    "Subtítulo y/o número de volumen",
                    value=libro["subtitulo_volumen"] or "",
                    key=f"e_sub_{k}",
                )
                autor = st.text_input("Autor *", value=libro["autor"] or "", key=f"e_autor_{k}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    lugar = st.text_input(
                        "Lugar de publicación",
                        value=libro["lugar_publicacion"] or "",
                        key=f"e_lugar_{k}",
                    )
                with col2:
                    editorial = st.text_input(
                        "Editorial / pie de imprenta",
                        value=libro["editorial"] or "",
                        key=f"e_edit_{k}",
                    )
                with col3:
                    anio = st.text_input(
                        "Año", value=libro["anio_publicacion"] or "", key=f"e_anio_{k}"
                    )

                col4, col5 = st.columns(2)
                with col4:
                    tarjeta = st.text_input(
                        "Número de tarjeta",
                        value=libro["num_tarjeta"] or "",
                        key=f"e_tarj_{k}",
                    )
                with col5:
                    signatura = st.text_input(
                        "Signatura topográfica",
                        value=libro["signatura_topografica"] or "",
                        key=f"e_sig_{k}",
                    )

                guardar = st.form_submit_button("Guardar cambios")

            if guardar:
                if not titulo.strip() or not autor.strip():
                    st.error("Título y autor son obligatorios.")
                else:
                    try:
                        supabase.table("books").update(
                            {
                                "titulo": titulo.strip(),
                                "subtitulo_volumen": vacio_a_none(subtitulo),
                                "autor": autor.strip(),
                                "lugar_publicacion": vacio_a_none(lugar),
                                "editorial": vacio_a_none(editorial),
                                "anio_publicacion": vacio_a_none(anio),
                                "num_tarjeta": vacio_a_none(tarjeta),
                                "signatura_topografica": vacio_a_none(signatura),
                            }
                        ).eq("id", k).execute()
                    except Exception as e:
                        st.error(f"No se pudo guardar: {e}")
                    else:
                        st.session_state["flash"] = (
                            f"Cambios guardados en {libro['no_adquisicion']}."
                        )
                        st.rerun()

# ------------------------------------------------------------------
# BAJA DE LIBRO
# ------------------------------------------------------------------
elif opcion == BAJA:
    st.subheader("📤 Dar de baja un libro ya registrado")
    mostrar_flash()

    folio_buscar = st.text_input("No. de adquisición del libro (ej: A-400)")

    if folio_buscar.strip():
        libro = buscar_por_folio(folio_buscar)

        if not libro:
            st.warning("No se encontró ningún libro con ese número de adquisición.")
        elif libro["estado"] == "baja":
            st.info("Este libro ya está dado de baja.")
        elif libro["estado"] == "prestado":
            st.error(
                "Este libro está prestado actualmente. "
                "No se puede dar de baja hasta que se devuelva."
            )
        else:
            st.write(f"**No. de adquisición:** {libro['no_adquisicion']}")
            st.write(f"**Título:** {libro['titulo']}")
            st.write(f"**Autor:** {libro['autor']}")

            motivo = st.text_input("Motivo de la baja (ej: extraviado, dañado)")
            if st.button("Confirmar baja"):
                supabase.table("books").update(
                    {
                        "estado": "baja",
                        "fecha_baja": ahora(),
                        "motivo_baja": vacio_a_none(motivo) or "No especificado",
                    }
                ).eq("id", libro["id"]).execute()
                st.session_state["flash"] = (
                    f"Libro {libro['no_adquisicion']} dado de baja correctamente."
                )
                st.rerun()

# ------------------------------------------------------------------
# CONSULTAR CATÁLOGO
# ------------------------------------------------------------------
elif opcion == CATALOGO:
    st.subheader("🔎 Catálogo de libros")

    col1, col2 = st.columns([2, 1])
    with col1:
        busqueda = st.text_input("Buscar por título, autor o No. de adquisición")
    with col2:
        filtro_estado = st.selectbox(
            "Filtrar por estado", ["Todos", "disponible", "prestado", "baja"]
        )

    libros = traer_libros(filtro_estado)

    if not libros:
        st.info("No hay libros con ese filtro todavía.")
    else:
        df = pd.DataFrame(libros)
        if busqueda.strip():
            b = busqueda.strip()
            mascara = (
                df["titulo"].str.contains(b, case=False, na=False, regex=False)
                | df["autor"].str.contains(b, case=False, na=False, regex=False)
                | df["no_adquisicion"].str.contains(b, case=False, na=False, regex=False)
            )
            df = df[mascara]

        st.write(f"{len(df)} libro(s) encontrado(s)")
        tabla = df[list(COLUMNAS_VISTA)].rename(columns=COLUMNAS_VISTA)
        st.dataframe(tabla, hide_index=True)

# ------------------------------------------------------------------
# GENERAR REPORTE
# ------------------------------------------------------------------
elif opcion == REPORTE:
    st.subheader("📄 Generar reporte de libros")
    st.caption(
        "Agrupa los ejemplares del mismo título (como en el documento original) "
        "y arma un Excel descargable."
    )

    estado_reporte = st.selectbox(
        "¿Qué libros quieres incluir?",
        ["baja", "disponible", "prestado", "Todos"],
    )

    if st.button("Generar reporte"):
        libros = traer_libros(estado_reporte)
        if not libros:
            st.session_state.pop("reporte", None)
            st.warning("No hay libros con ese filtro todavía.")
        else:
            df = pd.DataFrame(libros)

            # "Pie de imprenta" = lugar, editorial y año (los que tengan datos)
            df["pie_imprenta"] = df.apply(
                lambda f: ", ".join(
                    p
                    for p in [f["lugar_publicacion"], f["editorial"], f["anio_publicacion"]]
                    if isinstance(p, str) and p.strip()
                ),
                axis=1,
            )
            claves = ["autor", "titulo", "pie_imprenta", "signatura_topografica"]
            df[claves] = df[claves].fillna("")

            agrupado = (
                df.groupby(claves)
                .agg(
                    ejemplares=("no_adquisicion", "count"),
                    tarjeta=("num_tarjeta", "first"),
                    adquisiciones=("no_adquisicion", lambda x: " ".join(x)),
                )
                .reset_index()
            )
            agrupado.insert(0, "No.", range(1, len(agrupado) + 1))
            agrupado = agrupado.rename(
                columns={
                    "autor": "Descripción del Bien (Autor)",
                    "titulo": "Título",
                    "pie_imprenta": "Pie de Imprenta",
                    "ejemplares": "Núm. de Ej.",
                    "tarjeta": "Núm. de tarjeta",
                    "signatura_topografica": "Signatura topográfica",
                    "adquisiciones": "No. de adquisición",
                }
            )[
                [
                    "No.",
                    "Descripción del Bien (Autor)",
                    "Título",
                    "Pie de Imprenta",
                    "Núm. de Ej.",
                    "Núm. de tarjeta",
                    "Signatura topográfica",
                    "No. de adquisición",
                ]
            ]

            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                agrupado.to_excel(writer, index=False, sheet_name="Reporte")
                hoja = writer.sheets["Reporte"]
                from openpyxl.styles import Alignment, Font

                anchos = [6, 40, 40, 45, 12, 16, 24, 26]
                for i, ancho in enumerate(anchos):
                    letra = chr(ord("A") + i)
                    hoja.column_dimensions[letra].width = ancho
                for celda in hoja[1]:
                    celda.font = Font(bold=True)
                for fila in hoja.iter_rows(min_row=1):
                    for celda in fila:
                        celda.alignment = Alignment(wrap_text=True, vertical="top")

            st.session_state["reporte"] = (
                agrupado,
                buffer.getvalue(),
                f"reporte_libros_{estado_reporte}.xlsx",
            )

    if "reporte" in st.session_state:
        agrupado, datos_excel, nombre_archivo = st.session_state["reporte"]
        st.write(f"{len(agrupado)} título(s) en el reporte")
        st.dataframe(agrupado, hide_index=True)
        st.download_button(
            label="⬇️ Descargar Excel",
            data=datos_excel,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
