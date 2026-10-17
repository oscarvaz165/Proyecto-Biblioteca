# Sistema de Biblioteca - Semana 1

Funciones incluidas: alta de libros, baja de libros (baja lógica), consulta y búsqueda del catálogo.

## Pasos para correrlo

### 1. Crear la tabla en Supabase
1. Entra a tu proyecto en https://supabase.com
2. Ve a **SQL Editor** → **New query**
3. Copia y pega todo el contenido de `schema.sql`
4. Dale a **Run**

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar las credenciales de Supabase
Crea una carpeta `.streamlit` junto a `app.py`, y dentro un archivo llamado `secrets.toml` con este contenido:

```toml
SUPABASE_URL = "https://TU-PROYECTO.supabase.co"
SUPABASE_KEY = "tu-clave-anon-o-service-role"
```

Estos dos valores los encuentras en Supabase: **Project Settings → API**.
- `SUPABASE_URL` = "Project URL"
- `SUPABASE_KEY` = "anon public" key (para empezar, funciona bien; más adelante cuando agreguemos login de bibliotecarios podemos usar reglas de seguridad más finas)

**Importante:** no subas `secrets.toml` a GitHub (agrégalo a tu `.gitignore`).

### 4. Correr la app
```bash
streamlit run app.py
```

Se abrirá en el navegador, normalmente en `http://localhost:8501`

## Cómo funciona el folio
- Cada **copia física** de un libro tiene su propio folio único (B-0001, B-0002, etc.), aunque compartan título.
- Si tienen 3 copias del mismo libro, van a registrar 3 veces el mismo título con 3 folios distintos. Esto es intencional: así, cuando lleguemos a la parte de préstamos (semana 3), cada préstamo se puede ligar a una copia exacta.

## Qué sigue (próximas semanas)
- Tabla de `members` (socios/usuarios de la biblioteca)
- Tabla de `loans` (préstamos) ligada a `books` y `members`
- Pantalla para registrar préstamo y devolución (esto también cambia el `estado` del libro automáticamente a "prestado"/"disponible")
- Login de bibliotecarios con Supabase Auth
