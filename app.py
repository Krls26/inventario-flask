from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Usa la URI de Render aquí:
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://inventario_rkd3_user:d8cjHtcGQQvkZCKWP1QhF7FMtiPftGdr@dpg-d2qpctv5r7bs73b23l0g-a.oregon-postgres.render.com/inventario_rkd3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route("/")
def index():
    return "¡Flask está funcionando en mi PC! 🚀"

if __name__ == "__main__":
    app.run(debug=True)