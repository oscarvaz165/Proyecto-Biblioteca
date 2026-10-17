-- ============================================================
-- Esquema de la tabla de libros (biblioteca)
-- Ajustado al formato real del catálogo físico de la biblioteca
-- Ejecutar esto en Supabase -> SQL Editor -> New snippet -> Run
-- ============================================================

create table if not exists books (
    id uuid primary key default gen_random_uuid(),

    no_adquisicion text unique not null,   -- folio por COPIA física, formato real: "A-400"
    titulo text not null,
    subtitulo_volumen text,
    autor text not null,                   -- formato: "apellido paterno, apellido materno, nombre(s)"

    lugar_publicacion text,
    editorial text,
    anio_publicacion text,

    num_tarjeta text,                      -- número de tarjeta del catálogo físico anterior
    signatura_topografica text,            -- código de ubicación en el estante

    estado text not null default 'disponible'
        check (estado in ('disponible', 'prestado', 'baja')),

    fecha_alta timestamp with time zone default now(),
    fecha_baja timestamp with time zone,
    motivo_baja text
);

create index if not exists idx_books_no_adquisicion on books (no_adquisicion);
create index if not exists idx_books_titulo on books (titulo);
create index if not exists idx_books_autor on books (autor);
create index if not exists idx_books_estado on books (estado);

-- Nota:
-- Si un libro tiene varios ejemplares, cada ejemplar es UNA fila distinta
-- (mismo título/autor, distinto no_adquisicion). Así cada copia física
-- se puede rastrear por separado en préstamos y bajas.
