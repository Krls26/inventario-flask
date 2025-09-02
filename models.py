from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ============================================================
# TABLA DE USUARIOS
# ============================================================
class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # admin, bodega, consulta


# ============================================================
# TABLA DE CATEGORÍAS
# ============================================================
class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text)


# ============================================================
# TABLA DE PRODUCTOS
# ============================================================
class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id", ondelete="SET NULL"))
    proveedor = db.Column(db.String(100))
    # 👇 simplificado a un solo precio porque tu app.py lo usa así
    precio = db.Column(db.Numeric(12, 2))
    estado = db.Column(db.String(20), default="activo")

    categoria = db.relationship("Categoria", backref="productos")


# ============================================================
# TABLA DE SUCURSALES
# ============================================================
class Sucursal(db.Model):
    __tablename__ = "sucursales"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.Text)


# ============================================================
# TABLA PRODUCTOS_SUCURSALES
# ============================================================
class ProductoSucursal(db.Model):
    __tablename__ = "productos_sucursales"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    sucursal_id = db.Column(db.Integer, db.ForeignKey("sucursales.id", ondelete="CASCADE"), nullable=False)
    # 👇 cambiado a "stock" porque tu app.py lo usa así
    stock = db.Column(db.Integer, default=0)

    producto = db.relationship("Producto", backref="productos_sucursales")
    sucursal = db.relationship("Sucursal", backref="productos_sucursales")


# ============================================================
# TABLA DE MOVIMIENTOS
# ============================================================
class Movimiento(db.Model):
    __tablename__ = "movimientos"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    sucursal_id = db.Column(db.Integer, db.ForeignKey("sucursales.id", ondelete="CASCADE"), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # entrada, salida
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, server_default=db.func.now())
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="SET NULL"))
