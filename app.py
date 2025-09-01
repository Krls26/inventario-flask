from flask import Flask, render_template, request, redirect, url_for, send_file, flash, Response
import pandas as pd
from models import db, Producto, Categoria
import os
from io import BytesIO

app = Flask(__name__)
app.secret_key = "supersecret"  # Necesario para flash messages

# Configuración DB
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    # Categorías iniciales
    categorias_iniciales = [
        "Papelería", "Piñatería", "Juguetería", "Detalles",
        "Cajas", "Arreglos de bombas", "Stickers para bombas", "Libros"
    ]
    for nombre in categorias_iniciales:
        if not Categoria.query.filter_by(nombre=nombre).first():
            db.session.add(Categoria(nombre=nombre))
    db.session.commit()


# ---------- INICIO ----------
@app.route("/", methods=["GET", "POST"])
def inicio():
    if request.method == "POST":
        file = request.files.get("archivo_excel")
        if file:
            df = pd.read_excel(file)
            for _, row in df.iterrows():
                nombre = row["Nombre"]
                precio = float(row["Precio"])
                stock = int(row["Stock"])
                categoria_nombre = row["Categoría"]

                # Buscar o crear categoría
                categoria = Categoria.query.filter_by(nombre=categoria_nombre).first()
                if not categoria:
                    categoria = Categoria(nombre=categoria_nombre)
                    db.session.add(categoria)
                    db.session.commit()

                # Buscar producto
                producto = Producto.query.filter_by(nombre=nombre).first()
                if producto:
                    producto.precio = precio
                    producto.stock = stock
                    producto.categoria_id = categoria.id
                else:
                    producto = Producto(
                        nombre=nombre,
                        precio=precio,
                        stock=stock,
                        categoria_id=categoria.id
                    )
                    db.session.add(producto)
            
            db.session.commit()
            flash("Inventario actualizado/importado correctamente.", "success")

    return render_template("base.html")


# ---------- AGREGAR PRODUCTO ----------
@app.route("/agregar_producto", methods=["GET", "POST"])
def agregar_producto():
    categorias = Categoria.query.all()
    if request.method == "POST":
        nombre = request.form["nombre"]
        precio = float(request.form["precio"])
        stock = int(request.form["stock"])
        categoria_id = int(request.form["categoria_id"])
        nuevo = Producto(nombre=nombre, precio=precio, stock=stock, categoria_id=categoria_id)
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for("agregar_producto"))
    return render_template("agregar_producto.html", categorias=categorias)


# ---------- AGREGAR CATEGORÍA ----------
@app.route("/agregar_categoria", methods=["GET", "POST"])
def agregar_categoria():
    if request.method == "POST":
        nombre = request.form["nombre_categoria"]
        if not Categoria.query.filter_by(nombre=nombre).first():
            db.session.add(Categoria(nombre=nombre))
            db.session.commit()
        return redirect(url_for("agregar_categoria"))
    return render_template("agregar_categoria.html")


# ---------- CONSULTAR INVENTARIO ----------
@app.route("/consultar", methods=["GET", "POST"])
def consultar():
    nombre = request.form.get("nombre", "").strip() if request.method == "POST" else ""
    categoria_id = request.form.get("categoria_id", type=int) if request.method == "POST" else None

    query = Producto.query
    if nombre:
        query = query.filter(Producto.nombre.ilike(f"%{nombre}%"))
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)

    productos = query.all()
    categorias = Categoria.query.all()  # 🔹 Obtener categorías

    return render_template("consultar.html", productos=productos, categorias=categorias, categoria_id=categoria_id)


# ---------- EXPORTAR INVENTARIO ----------
@app.route("/exportar_excel", methods=["POST"])
def exportar_excel():
    nombre = request.form.get("nombre", "").strip()
    categoria_id = request.form.get("categoria_id", type=int)

    query = Producto.query
    if nombre:
        query = query.filter(Producto.nombre.ilike(f"%{nombre}%"))
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)

    productos = query.all()

    data = [{
        "Nombre": p.nombre,
        "Categoría": p.categoria.nombre if p.categoria else "Sin categoría",
        "Stock": p.stock,
        "Precio": p.precio
    } for p in productos]

    # Definir orden de columnas explícitamente
    columnas = ["Nombre", "Categoría", "Stock", "Precio"]
    df = pd.DataFrame(data, columns=columnas)

    output = BytesIO()
    df.to_excel(output, index=False, sheet_name="Inventario")
    output.seek(0)

    return send_file(
        output,
        download_name="inventario_filtrado.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ---------- ACTUALIZAR Y ELIMINAR STOCK ----------
@app.route("/stock", methods=["GET"])
def stock():
    productos = Producto.query.all()
    return render_template("stock.html", productos=productos)


@app.route("/actualizar_stock/<int:id>", methods=["POST"])
def actualizar_stock(id):
    producto = Producto.query.get_or_404(id)
    nuevo_stock = int(request.form["nuevo_stock"])
    producto.stock = nuevo_stock
    db.session.commit()
    return redirect(url_for("stock"))


@app.route("/eliminar_producto/<int:id>", methods=["POST"])
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    return redirect(url_for("stock"))


if __name__ == "__main__":
    app.run(debug=True)
