from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import pandas as pd
from models import db, Producto, Categoria, Sucursal, ProductoSucursal
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

    # Sucursales iniciales
    sucursales_iniciales = ["Sucursal Centro", "Sucursal Norte", "Sucursal Sur"]
    for nombre in sucursales_iniciales:
        if not Sucursal.query.filter_by(nombre=nombre).first():
            db.session.add(Sucursal(nombre=nombre))

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
                    producto.categoria_id = categoria.id
                else:
                    producto = Producto(
                        nombre=nombre,
                        precio=precio,
                        categoria_id=categoria.id
                    )
                    db.session.add(producto)
                    db.session.commit()

                # Asignar stock en la primera sucursal (ejemplo)
                sucursal = Sucursal.query.first()
                ps = ProductoSucursal.query.filter_by(producto_id=producto.id, sucursal_id=sucursal.id).first()
                if ps:
                    ps.stock = stock
                else:
                    db.session.add(ProductoSucursal(producto_id=producto.id, sucursal_id=sucursal.id, stock=stock))

            db.session.commit()
            flash("Inventario actualizado/importado correctamente.", "success")

    return render_template("base.html")


# ---------- AGREGAR PRODUCTO ----------
@app.route("/agregar_producto", methods=["GET", "POST"])
def agregar_producto():
    categorias = Categoria.query.all()
    sucursales = Sucursal.query.all()
    if request.method == "POST":
        nombre = request.form["nombre"]
        precio = float(request.form["precio"])
        stock = int(request.form["stock"])
        categoria_id = int(request.form["categoria_id"])
        sucursal_id = int(request.form["sucursal_id"])

        nuevo = Producto(nombre=nombre, precio=precio, categoria_id=categoria_id)
        db.session.add(nuevo)
        db.session.commit()

        # Stock en la sucursal elegida
        db.session.add(ProductoSucursal(producto_id=nuevo.id, sucursal_id=sucursal_id, stock=stock))
        db.session.commit()

        return redirect(url_for("agregar_producto"))
    return render_template("agregar_producto.html", categorias=categorias, sucursales=sucursales)


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
    sucursal_id = request.form.get("sucursal_id", type=int) if request.method == "POST" else None

    query = db.session.query(Producto, Categoria, Sucursal, ProductoSucursal).\
        join(Categoria, Producto.categoria_id == Categoria.id).\
        join(ProductoSucursal, Producto.id == ProductoSucursal.producto_id).\
        join(Sucursal, ProductoSucursal.sucursal_id == Sucursal.id)

    if nombre:
        query = query.filter(Producto.nombre.ilike(f"%{nombre}%"))
    if categoria_id:
        query = query.filter(Producto.categoria_id == categoria_id)
    if sucursal_id:
        query = query.filter(Sucursal.id == sucursal_id)

    resultados = query.all()
    categorias = Categoria.query.all()
    sucursales = Sucursal.query.all()

    return render_template(
        "consultar.html",
        resultados=resultados,
        categorias=categorias,
        sucursales=sucursales,
        categoria_id=categoria_id,
        sucursal_id=sucursal_id,
        nombre=nombre
    )


# ---------- EXPORTAR INVENTARIO ----------
@app.route("/exportar_excel", methods=["POST"])
def exportar_excel():
    nombre = request.form.get("nombre", "").strip()
    categoria_id = request.form.get("categoria_id", type=int)
    sucursal_id = request.form.get("sucursal_id", type=int)

    query = db.session.query(Producto, Categoria, Sucursal, ProductoSucursal).\
        join(Categoria, Producto.categoria_id == Categoria.id).\
        join(ProductoSucursal, Producto.id == ProductoSucursal.producto_id).\
        join(Sucursal, ProductoSucursal.sucursal_id == Sucursal.id)

    if nombre:
        query = query.filter(Producto.nombre.ilike(f"%{nombre}%"))
    if categoria_id:
        query = query.filter(Producto.categoria_id == categoria_id)
    if sucursal_id:
        query = query.filter(Sucursal.id == sucursal_id)

    resultados = query.all()

    data = [{
        "Nombre": p.nombre,
        "Categoría": c.nombre,
        "Sucursal": s.nombre,
        "Stock": ps.stock,
        "Precio": p.precio
    } for p, c, s, ps in resultados]

    columnas = ["Nombre", "Categoría", "Sucursal", "Stock", "Precio"]
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


if __name__ == "__main__":
    app.run(debug=True)
