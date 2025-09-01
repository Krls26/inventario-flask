from flask import Flask, render_template, request, redirect, url_for
from models import db, Producto, Categoria
import os

app = Flask(__name__)

# Configuración de Render / PostgreSQL
db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Crear tablas y cargar categorías iniciales
with app.app_context():
    db.create_all()

    categorias_iniciales = [
        "Papelería", "Piñatería", "Juguetería", "Detalles",
        "Cajas", "Arreglos de bombas", "Stickers para bombas", "Libros"
    ]

    for nombre in categorias_iniciales:
        if not Categoria.query.filter_by(nombre=nombre).first():
            db.session.add(Categoria(nombre=nombre))

    db.session.commit()


@app.route("/")
def index():
    categorias = Categoria.query.all()
    categoria_id = request.args.get("categoria_id", type=int)

    if categoria_id:
        productos = Producto.query.filter_by(categoria_id=categoria_id).all()
    else:
        productos = Producto.query.all()

    return render_template(
        "index.html",
        categorias=categorias,
        productos=productos,
        categoria_id=categoria_id
    )


@app.route("/agregar_producto", methods=["POST"])
def agregar_producto():
    nombre = request.form["nombre"]
    precio = float(request.form["precio"])
    stock = int(request.form["stock"])
    categoria_id = int(request.form["categoria_id"])

    nuevo = Producto(
        nombre=nombre,
        precio=precio,
        stock=stock,
        categoria_id=categoria_id
    )

    db.session.add(nuevo)
    db.session.commit()

    return redirect(url_for("index"))


@app.route("/agregar_categoria", methods=["POST"])
def agregar_categoria():
    nombre = request.form["nombre_categoria"].strip()

    if nombre and not Categoria.query.filter_by(nombre=nombre).first():
        db.session.add(Categoria(nombre=nombre))
        db.session.commit()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
