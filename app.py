from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# CONFIGURACIÓN DE SEGURIDAD Y BASE DE DATOS
# Clave secreta para manejar las sesiones de forma segura (Login)
app.secret_key = os.environ.get('SECRET_KEY', 'clave_secreta_sofia_tienda_123')

# Detección automática de la Base de Datos (Si estás en Render usa PostgreSQL, en tu PC usa SQLite)
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///sofia_store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==========================================
# MODELOS (Tablas de la Base de Datos)
# ==========================================

# Tabla para guardar a los usuarios administradores
class Administrador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

# Tabla para guardar los productos de la tienda
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    imagen_url = db.Column(db.String(300), nullable=False)

# Crear las tablas automáticamente en la base de datos si no existen al arrancar
with app.app_context():
    db.create_all()


# ==========================================
# RUTAS PÚBLICAS EXISTENTES (Tus avances)
# ==========================================

# 1. Ruta para la página de inicio (index.html)
@app.route("/")
def inicio():
    return render_template("index.html")

# 2. Ruta para la página de contacto
@app.route("/contacto")
def contacto():
    return render_template("contacto.html")

# 3. Ruta para la página de clientes
@app.route("/clientes")
def clientes():
    return render_template("clientes.html")

# 4. Ruta para la página de preguntas frecuentes (FAQ)
@app.route("/faq")
def faq():
    return render_template("faq.html")

# 5. Ruta para la página de productos (PÚBLICA - Ahora trae los datos de la BD)
@app.route("/productos")
def productos():
    # Trae todos los productos guardados para mostrarlos dinámicamente
    todos_los_productos = Producto.query.all()
    return render_template("productos.html", productos=todos_los_productos)


# ==========================================
# NUEVAS RUTAS: AUTENTICACIÓN (LOGIN Y REGISTER)
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Verificar si el correo ya fue registrado por otro admin
        existe = Administrador.query.filter_by(email=email).first()
        if existe:
            flash("Este correo electrónico ya está registrado.", "danger")
            return redirect(url_for("register"))
        
        # Encriptamos la contraseña antes de guardarla por seguridad
        password_encriptada = generate_password_hash(password)
        
        nuevo_admin = Administrador(nombre=nombre, email=email, password=password_encriptada)
        db.session.add(nuevo_admin)
        db.session.commit()
        
        flash("Administrador registrado correctamente. ¡Ya puedes iniciar sesión!", "success")
        return redirect(url_for("login"))
        
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        admin = Administrador.query.filter_by(email=email).first()
        
        # Si el admin existe y la contraseña coincide con el hash encriptado
        if admin and check_password_hash(admin.password, password):
            session["admin_id"] = admin.id  # Guardamos el ID en la sesión del navegador
            session["admin_nombre"] = admin.nombre
            flash(f"¡Bienvenida de vuelta, {admin.nombre}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Credenciales incorrectas. Verifica tu correo o contraseña.", "danger")
            return redirect(url_for("login"))
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    # Eliminamos los datos del usuario de la sesión para cerrar el acceso
    session.pop("admin_id", None)
    session.pop("admin_nombre", None)
    flash("Has cerrado sesión de manera segura.", "success")
    return redirect(url_for("login"))


# ==========================================
# NUEVAS RUTAS: DASHBOARD ADMINISTRATIVO
# ==========================================

# Menú de inicio del Dashboard
@app.route("/dashboard")
def dashboard():
    # Sistema de seguridad: si no ha iniciado sesión, se le bloquea el paso
    if "admin_id" not in session:
        flash("Acceso denegado. Por favor, inicia sesión.", "warning")
        return redirect(url_for("login"))
        
    return render_template("dashboard.html")

# Vista para ver la tabla e inventario de productos
@app.route("/dashboard/productos")
def dashboard_productos():
    if "admin_id" not in session:
        flash("Acceso denegado. Por favor, inicia sesión.", "warning")
        return redirect(url_for("login"))
        
    todos_los_productos = Producto.query.all()
    return render_template("dashboard_productos.html", productos=todos_los_productos)

# Acción para AGREGAR un nuevo producto
@app.route("/dashboard/productos/agregar", methods=["POST"])
def agregar_producto():
    if "admin_id" not in session:
        return redirect(url_for("login"))
        
    nombre = request.form.get("nombre")
    precio = request.form.get("precio")
    imagen_url = request.form.get("imagen_url")
    
    nuevo_prod = Producto(nombre=nombre, precio=float(precio), imagen_url=imagen_url)
    db.session.add(nuevo_prod)
    db.session.commit()
    
    flash("Producto añadido exitosamente al catálogo.", "success")
    return redirect(url_for("dashboard_productos"))

# Acción para ACTUALIZAR/EDITAR un producto existente
@app.route("/dashboard/productos/editar/<int:id>", methods=["POST"])
def editar_producto(id):
    if "admin_id" not in session:
        return redirect(url_for("login"))
        
    producto = Producto.query.get_or_404(id)
    producto.nombre = request.form.get("nombre")
    producto.precio = float(request.form.get('precio'))
    producto.imagen_url = request.form.get("imagen_url")
    
    db.session.commit()
    flash("Producto actualizado correctamente.", "success")
    return redirect(url_for("dashboard_productos"))


# CONFIGURACIÓN ESPECIAL PARA DESPLIEGUE
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

    DATABASE_URL = os.environ.get('DATABASE_URL') # 1. Busca la variable en Render

# 2. Corrige un pequeño estándar visual de Postgres para Python
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Si existe (Render), se conecta a internet. Si no (Tu PC), usa el archivo local.
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///sofia_store.db'