from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
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


# ==========================================
# MODELOS (Solo Administrador por ahora)
# ==========================================
class Administrador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

with app.app_context():
    db.create_all()


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
    # Retorna la vista estática normal que ya tenías armada
    return render_template("productos.html")


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
# GESTIÓN DEL DASHBOARD (Limpio)
# ==========================================
@app.route("/dashboard")
def dashboard():
    if "admin_id" not in session:
        flash("Acceso denegado.", "warning")
        return redirect(url_for("login"))
        
    return render_template("dashboard.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)