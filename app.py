from flask import Flask, render_template
import os

app = Flask(__name__)

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

# 5. Ruta para la página de productos
@app.route("/productos")
def productos():
    return render_template("productos.html")

# Configuración especial para que funcione tanto en tu PC como en Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)