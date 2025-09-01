from flask import Flask, render_template, request, redirect, url_for
from models import db, Producto, Categoria
import os

app = Flask(__name__)

# Configuración Render / PostgreSQL
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    # Insertar categorías iniciales si no existen
    categorias_iniciales = [
        "Papelería", "Piñatería", "Juguetería", "Detalles",
        "Cajas", "Arreglos de bombas", "Stickers para bombas", "Libros"
    ]
    for nombre in categorias_iniciales:
        if not Categoria.query.filter_by(nombre=nombre).first():
            db.session.add(Categoria(nombre=nombre))
    db.session.commit()


# Página principal: lista productos
@app.route("/")
def index():
    categorias = Categoria.query.all()
    categoria_id = request.args.get("categoria_id", type=int)
    productos = (
        Producto.query.filter_by(categoria_id=categoria_id).all()
        if categoria_id else Producto.query.all()
    )
    return render_template("index.html", categorias=categorias, productos=productos, categoria_id=categoria_id)


# Formulario para agregar producto
@app.route("/form_agregar_producto")
def form_agregar_producto():
    categorias = Categoria.query.all()
    return render_template("agregar_producto.html", categorias=categorias)


# Agregar producto
@app.route("/agregar_producto", methods=["POST"])
def agregar_producto():
    nombre = request.form["nombre"]
    precio = float(request.form["precio"])
    stock = int(request.form["stock"])
    categoria_id = int(request.form["categoria_id"])
    nuevo = Producto(nombre=nombre, precio=precio, stock=stock, categoria_id=categoria_id)
    db.session.add(nuevo)
    db.session.commit()
    return redirect(url_for("index"))


# Formulario para agregar categoría
@app.route("/form_agregar_categoria")
def form_agregar_categoria():
    return render_template("agregar_categoria.html")


# Agregar categoría
@app.route("/agregar_categoria", methods=["POST"])
def agregar_categoria():
    nombre = request.form["nombre_categoria"]
    if not Categoria.query.filter_by(nombre=nombre).first():
        db.session.add(Categoria(nombre=nombre))
        db.session.commit()
    return redirect(url_for("index"))


# Consultar inventario
@app.route("/consultar", methods=["GET", "POST"])
def consultar():
    productos = []
    if request.method == "POST":
        busqueda = request.form["busqueda"]
        productos = Producto.query.filter(Producto.nombre.ilike(f"%{busqueda}%")).all()
    return render_template("consultar.html", productos=productos)


# Eliminar producto
@app.route("/eliminar_producto/<int:id>")
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    return redirect(url_for("index"))


# Actualizar stock
@app.route("/actualizar_stock/<int:id>", methods=["GET", "POST"])
def actualizar_stock(id):
    producto = Producto.query.get_or_404(id)
    if request.method == "POST":
        cantidad = int(request.form["cantidad"])
        producto.stock += cantidad  # puede ser positivo o negativo
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("actualizar_stock.html", producto=producto)


if __name__ == "__main__":
    app.run(debug=True)
