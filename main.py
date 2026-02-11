# --- UI: Tkinter para crear ventanas en Windows ---
import tkinter as tk                 # Módulo base de Tkinter (ventanas, widgets)
from tkinter import ttk, messagebox  # ttk = widgets modernos; messagebox = alertas/popup

# --- Drivers DB ---
import psycopg          # Driver PostgreSQL (psycopg3)
import mysql.connector  # Driver MySQL (Oracle)

# ============================================================
# CONFIGURACIÓN
# ============================================================

# Parámetros para conectarse a PostgreSQL (host local, puerto 5432)
PG_CONFIG = {
    "host": "localhost",   # Servidor donde corre PostgreSQL (localhost = esta PC)
    "port": 5432,          # Puerto por defecto de PostgreSQL
    "database": "testdb",  # Nombre de la base de datos en PostgreSQL
    "user": "postgres",    # Usuario
    "password": "postgres" # Contraseña
}

# Parámetros para conectarse a MySQL (host local, puerto 3306)
MY_CONFIG = {
    "host": "localhost",        # Servidor MySQL
    "port": 3306,               # Puerto por defecto de MySQL
    "database": "testdb",       # Nombre de la base de datos en MySQL
    "user": "root",             # Usuario
    "password": "Asdefsdfg$20"  # Contraseña
}

TABLE_NAME = "clientes"  # Nombre de la tabla que usará el CRUD en ambos motores

# ============================================================
# CONEXIÓN (selección de motor)
# ============================================================

def get_connection(db_choice: str):
    """
    Retorna una conexión viva según el motor seleccionado en la UI.
    Concepto DB-API: la conexión es el objeto principal; de ella salen cursores. [web:1]
    """
    if db_choice == "PostgreSQL":
        # psycopg.connect() abre la conexión hacia Postgres.
        # dbname: psycopg/libpq espera el nombre de la base como "dbname".
        # options: mandamos un parámetro de sesión para asegurar client_encoding=UTF8.
        return psycopg.connect(
            host=PG_CONFIG["host"],
            port=PG_CONFIG["port"],
            dbname=PG_CONFIG["database"],
            user=PG_CONFIG["user"],
            password=PG_CONFIG["password"],
            options="-c client_encoding=UTF8",
        )
    elif db_choice == "MySQL":
        # mysql.connector.connect() abre conexión a MySQL con el diccionario MY_CONFIG.
        return mysql.connector.connect(**MY_CONFIG)
    else:
        # Si el usuario elige algo no contemplado
        raise ValueError("Motor no soportado")

# ============================================================
# ESQUEMA (crear tabla si no existe)
# ============================================================

def ensure_schema(conn, db_choice: str):
    """
    Crea la tabla si no existe (en el motor elegido).
    DB-API: se crea un cursor, se ejecuta SQL y se confirma con commit. [web:1]
    """
    cur = conn.cursor()  # cursor = objeto para enviar SQL al motor [web:1]

    if db_choice == "PostgreSQL":
        # En Postgres: SERIAL autoincrementa
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL
            );
        """)
    else:
        # En MySQL: AUTO_INCREMENT autoincrementa
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL
            );
        """)

    conn.commit()  # commit = guardar cambios de DDL/DML en la transacción [web:1]
    cur.close()    # liberar el cursor

# ============================================================
# CRUD (Create, Read, Update, Delete)
# ============================================================

def insert_cliente(conn, nombre, email):
    # Inserta un registro usando query parametrizada (%s) para evitar inyección SQL. [web:1]
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO {TABLE_NAME} (nombre, email) VALUES (%s, %s)",
        (nombre, email),
    )
    conn.commit()  # confirmamos inserción
    cur.close()

def list_clientes(conn):
    # Consulta (SELECT) y devuelve una lista de filas.
    cur = conn.cursor()
    cur.execute(f"SELECT id, nombre, email FROM {TABLE_NAME} ORDER BY id")
    rows = cur.fetchall()  # trae todas las filas
    cur.close()
    return rows

def update_cliente(conn, cliente_id, nombre, email):
    # Actualiza por ID.
    cur = conn.cursor()
    cur.execute(
        f"UPDATE {TABLE_NAME} SET nombre=%s, email=%s WHERE id=%s",
        (nombre, email, cliente_id),
    )
    conn.commit()
    cur.close()

def delete_cliente(conn, cliente_id):
    # Borra por ID.
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {TABLE_NAME} WHERE id=%s", (cliente_id,))
    conn.commit()
    cur.close()

# ============================================================
# APLICACIÓN (UI + lógica)
# ============================================================

class App(tk.Tk):
    """
    App hereda de tk.Tk, que representa la ventana principal.
    Guardamos estado: motor seleccionado y conexión activa.
    """
    def __init__(self):
        super().__init__()  # inicializa la ventana base
        self.title("CRUD multi-DB (PostgreSQL / MySQL)")
        self.geometry("760x420")

        self.db_choice = tk.StringVar(value="PostgreSQL")  # variable enlazada al combobox
        self.conn = None  # aquí guardaremos la conexión actual (Postgres o MySQL)

        self._build_ui()  # construye todos los widgets

    def _build_ui(self):
        # ----- Barra superior: selección de motor y botón conectar -----
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Motor:").pack(side="left")

        ttk.Combobox(
            top,
            textvariable=self.db_choice,
            values=["PostgreSQL", "MySQL"],
            state="readonly",
            width=12,
        ).pack(side="left", padx=8)

        ttk.Button(top, text="Conectar", command=self.connect_and_init).pack(side="left")

        # ----- Formulario de datos -----
        form = ttk.LabelFrame(self, text="Datos de cliente")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="ID (para Update/Delete):").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.id_entry = ttk.Entry(form, width=20)
        self.id_entry.grid(row=0, column=1, sticky="w", padx=8, pady=6)

        ttk.Label(form, text="Nombre:").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.nombre_entry = ttk.Entry(form, width=40)
        self.nombre_entry.grid(row=1, column=1, sticky="w", padx=8, pady=6)

        ttk.Label(form, text="Email:").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        self.email_entry = ttk.Entry(form, width=40)
        self.email_entry.grid(row=2, column=1, sticky="w", padx=8, pady=6)

        # ----- Botones CRUD -----
        btns = ttk.Frame(form)
        btns.grid(row=0, column=2, rowspan=3, padx=12)

        ttk.Button(btns, text="Insert", command=self.on_insert).pack(fill="x", pady=3)
        ttk.Button(btns, text="Select/Refresh", command=self.refresh).pack(fill="x", pady=3)
        ttk.Button(btns, text="Update", command=self.on_update).pack(fill="x", pady=3)
        ttk.Button(btns, text="Delete", command=self.on_delete).pack(fill="x", pady=3)

        # ----- Tabla (Treeview) para mostrar resultados -----
        grid = ttk.LabelFrame(self, text="Resultados")
        grid.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(grid, columns=("id", "nombre", "email"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("email", text="Email")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

    def require_conn(self):
        """
        Valida que exista una conexión antes de usar cursor()/CRUD.
        Si no hay conexión, avisa al usuario con un popup.
        """
        if self.conn is None:
            messagebox.showwarning("Sin conexión", "Primero conecta a una base de datos.")
            return False
        return True

    def connect_and_init(self):
        """
        1) Cierra una conexión anterior si existe.
        2) Crea nueva conexión según motor.
        3) Crea la tabla si no existe.
        4) Actualiza la grilla.
        """
        try:
            if self.conn is not None:
                try:
                    self.conn.close()  # cierra conexión anterior
                except Exception:
                    pass

            self.conn = get_connection(self.db_choice.get())
            ensure_schema(self.conn, self.db_choice.get())
            self.refresh()
        except Exception as e:
            self.conn = None
            messagebox.showerror("Error de conexión", str(e))

    def refresh(self):
        """Recarga los datos del SELECT y los pinta en el Treeview."""
        if not self.require_conn():
            return
        try:
            # Limpia la tabla visual
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Carga filas desde DB y las inserta en la vista
            for row in list_clientes(self.conn):
                self.tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_insert(self):
        """Toma inputs (nombre/email) y hace INSERT."""
        if not self.require_conn():
            return

        nombre = self.nombre_entry.get().strip()
        email = self.email_entry.get().strip()

        if not nombre or not email:
            messagebox.showwarning("Validación", "Nombre y Email son obligatorios.")
            return

        try:
            insert_cliente(self.conn, nombre, email)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_update(self):
        """Toma id/nombre/email y hace UPDATE."""
        if not self.require_conn():
            return

        cid = self.id_entry.get().strip()
        nombre = self.nombre_entry.get().strip()
        email = self.email_entry.get().strip()

        if not cid.isdigit():
            messagebox.showwarning("Validación", "ID debe ser numérico para Update.")
            return
        if not nombre or not email:
            messagebox.showwarning("Validación", "Nombre y Email son obligatorios.")
            return

        try:
            update_cliente(self.conn, int(cid), nombre, email)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_delete(self):
        """Toma id y hace DELETE."""
        if not self.require_conn():
            return

        cid = self.id_entry.get().strip()
        if not cid.isdigit():
            messagebox.showwarning("Validación", "ID debe ser numérico para Delete.")
            return

        try:
            delete_cliente(self.conn, int(cid))
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

# Punto de entrada del programa
if __name__ == "__main__":
    app = App()      # crea la ventana
    app.mainloop()   # loop de eventos (la app “vive” aquí)