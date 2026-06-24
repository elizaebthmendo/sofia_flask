from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # <-- 1. Agregamos la importación
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# ==========================================
# CONFIGURACIÓN DE SEGURIDAD Y BASE DE DATOS
# ==========================================
app.secret_key = os.environ.get('SECRET_KEY', 'clave_secreta_sofia_tienda_123')

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///sofia_store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # <-- 2. Inicializamos Flask-Migrate aquí


# ==========================================
# MODELOS (Tablas de la Base de Datos)
# ==========================================

# Tabla para guardar a los usuarios administradores
class Administrador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

# Tabla para guardar los productos con descripción y estrellas
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    imagen_url = db.Column(db.String(300), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)     
    estrellas = db.Column(db.Float, nullable=True)      

# 3. ¡ELIMINAMOS EL BLOQUE db.create_all() QUE ESTABA AQUÍ!
# Ya no es necesario porque Alembic manejará la estructura.

# ... (El resto de tus rutas se mantiene exactamente igual)

# ==========================================
# RUTAS PÚBLICAS 
# ==========================================
@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/contacto")
def contacto():
    return render_template("contacto.html")

@app.route("/clientes")
def clientes():
    return render_template("clientes.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/productos")
def productos():
    todos_los_productos = Producto.query.all()
    return render_template("productos.html", productos=todos_los_productos)


# ==========================================
# RUTAS DE AUTENTICACIÓN
# ==========================================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        password = request.form.get("password")
        
        existe = Administrador.query.filter_by(email=email).first()
        if existe:
            flash("Este correo electrónico ya está registrado.", "danger")
            return redirect(url_for("register"))
        
        password_encriptada = generate_password_hash(password)
        nuevo_admin = Administrador(nombre=nombre, email=email, password=password_encriptada)
        db.session.add(nuevo_admin)
        db.session.commit()
        
        flash("Administrador registrado correctamente.", "success")
        return redirect(url_for("login"))
        
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        admin = Administrador.query.filter_by(email=email).first()
        
        if admin and check_password_hash(admin.password, password):
            session["admin_id"] = admin.id
            session["admin_nombre"] = admin.nombre
            flash(f"¡Bienvenida de vuelta, {admin.nombre}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Credenciales incorrectas.", "danger")
            return redirect(url_for("login"))
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin_id", None)
    session.pop("admin_nombre", None)
    flash("Has cerrado sesión.", "success")
    return redirect(url_for("login"))


# ==========================================
# GESTIÓN DEL DASHBOARD ADMINISTRATIVO
# ==========================================
@app.route("/dashboard")
def dashboard():
    if "admin_id" not in session:
        flash("Acceso denegado.", "warning")
        return redirect(url_for("login"))
        
    return render_template("dashboard.html")

@app.route("/dashboard/productos")
def dashboard_productos():
    if "admin_id" not in session:
        flash("Acceso denegado.", "warning")
        return redirect(url_for("login"))
        
    todos_los_productos = Producto.query.all()
    return render_template("dashboard_productos.html", productos=todos_los_productos)

@app.route("/dashboard/productos/agregar", methods=["POST"])
def agregar_producto():
    if "admin_id" not in session:
        return redirect(url_for("login"))
        
    nombre = request.form.get("nombre")
    precio = request.form.get("precio")
    imagen_url = request.form.get("imagen_url")
    descripcion = request.form.get("descripcion")
    estrellas = request.form.get("estrellas")
    
    nuevo_prod = Producto(
        nombre=nombre, 
        precio=float(precio), 
        imagen_url=imagen_url,
        descripcion=descripcion,
        estrellas=float(estrellas) if estrellas else 5.0
    )
    db.session.add(nuevo_prod)
    db.session.commit()
    
    flash("Producto añadido exitosamente al catálogo.", "success")
    return redirect(url_for("dashboard_productos"))

@app.route("/dashboard/productos/editar/<int:id>", methods=["POST"])
def editar_producto(id):
    if "admin_id" not in session:
        return redirect(url_for("login"))
        
    producto = Producto.query.get_or_404(id)
    producto.nombre = request.form.get("nombre")
    producto.precio = float(request.form.get('precio'))
    producto.imagen_url = request.form.get("imagen_url")
    producto.descripcion = request.form.get("descripcion")
    producto.estrellas = float(request.form.get("estrellas"))
    
    db.session.commit()
    flash("Producto actualizado correctamente.", "success")
    return redirect(url_for("dashboard_productos"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

@app.route("/dashboard/productos/eliminar/<int:id>", methods=["POST"])
def eliminar_producto(id):
    if "admin_id" not in session:
        return redirect(url_for("login"))
        
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    
    flash("Producto eliminado correctamente del catálogo.", "danger")
    return redirect(url_for("dashboard_productos"))

# ==========================================================================
# RUTAS PARA EL CARRITO DE COMPRAS
# ==========================================================================

@app.route('/dashboard/carrito')
def ver_carrito():
    """Muestra los productos que están actualmente en el carrito."""
    if 'carrito' not in session:
        session['carrito'] = {}
        
    carrito = session['carrito']
    total = 0
    productos_carrito = []
    
    for id_prod, item in carrito.items():
        subtotal = item['precio'] * item['cantidad']
        total += subtotal
        productos_carrito.append({
            'id': id_prod,
            'nombre': item['nombre'],
            'precio': item['precio'],
            'imagen_url': item['imagen_url'],
            'cantidad': item['cantidad'],
            'subtotal': subtotal
        })
        
    return render_template('carrito.html', productos=productos_carrito, total=total)


@app.route('/dashboard/carrito/agregar/<id>', methods=['POST'])
def agregar_al_carrito(id):
    """Añade un producto al carrito o incrementa su cantidad."""
    if 'carrito' not in session:
        session['carrito'] = {}
        
    carrito = session['carrito']
    
    nombre = request.form.get('nombre')
    precio = float(request.form.get('precio'))
    imagen_url = request.form.get('imagen_url')
    
    id_str = str(id)
    
    if id_str in carrito:
        carrito[id_str]['cantidad'] += 1
    else:
        carrito[id_str] = {
            'nombre': nombre,
            'precio': precio,
            'imagen_url': imagen_url,
            'cantidad': 1
        }
        
    session.modified = True
    flash('¡Producto añadido al carrito! 🛒', 'success')
    return redirect(url_for('productos'))


@app.route('/dashboard/carrito/actualizar/<id>/<accion>')
def actualizar_cantidad(id, accion):
    """Incrementa o decrementa la cantidad de un producto en el carrito."""
    id_str = str(id)
    if 'carrito' in session and id_str in session['carrito']:
        carrito = session['carrito']
        
        if accion == 'incrementar':
            carrito[id_str]['cantidad'] += 1
        elif accion == 'decrementar':
            carrito[id_str]['cantidad'] -= 1
            if carrito[id_str]['cantidad'] <= 0:
                carrito.pop(id_str)
                
        session.modified = True
    return redirect(url_for('ver_carrito'))


@app.route('/dashboard/carrito/eliminar/<id>')
def eliminar_del_carrito(id):
    """Elimina por completo un producto del carrito."""
    id_str = str(id)
    if 'carrito' in session and id_str in session['carrito']:
        session['carrito'].pop(id_str)
        session.modified = True
        flash('Producto eliminado del carrito.', 'warning')
    return redirect(url_for('ver_carrito'))


# ==========================================================================
# GESTIÓN DE ELIMINACIÓN DEL CATÁLOGO (UNA SOLA VEZ)
# ==========================================================================
@app.route("/dashboard/productos/eliminar/<int:id>", methods=["POST"])
def eliminar_producto(id):
    if "admin_id" not in session:
        return redirect(url_for("login"))
        
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    
    flash("Producto eliminado correctamente del catálogo.", "danger")
    return redirect(url_for("dashboard_productos"))


# ==========================================
# ENCIENDES EL SERVIDOR (SIEMPRE AL FINAL)
# ==========================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)