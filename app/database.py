from sqlmodel import SQLModel, create_engine, Session

# 1. Definimos el nombre del archivo de la base de datos
# Como usaremos SQLite, esto creará un archivo real en tu carpeta.
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# 2. Creamos el "Engine" (El motor de conexión)
# connect_args={"check_same_thread": False} es necesario solo para SQLite en FastAPI
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

# 3. Función para crear las tablas al inicio
def create_db_and_tables():
    # Esto busca todos los modelos que hereden de SQLModel y crea las tablas si no existen
    SQLModel.metadata.create_all(engine)

# 4. Dependencia para obtener la sesión (IMPORTANTE)
# Esta función se usará en cada "ruta" (endpoint) para interactuar con la DB.
# El 'yield' asegura que la conexión se cierre automáticamente después de usarla.
def get_session():
    with Session(engine) as session:
        yield session