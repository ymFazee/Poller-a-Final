from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import db
from models import Usuario, Producto, Servicio, Cliente
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = "donfuego-secret-2026"

# ─── Base de datos SQLite ───────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "donfuego.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# ─── Crear tablas e insertar datos iniciales ────────────────────────────────
def seed():
    if not Usuario.query.first():
        db.session.add(Usuario(
            nombre="Administrador",
            usuario="admin",
            password=generate_password_hash("admin123"),
            rol="Administrador",
            estado="Activo",
        ))

    if not Producto.query.first():
        productos = [
            Producto(nombre="Pollo a la Brasa (Entero)", categoria="Plato Principal", precio=48.90, stock=30),
            Producto(nombre="Pollo a la Brasa (1/4)",    categoria="Plato Principal", precio=18.90, stock=50),
            Producto(nombre="Hamburguesa Premium",        categoria="Hamburguesas",    precio=24.90, stock=20),
            Producto(nombre="Salchipapas Especial",       categoria="Acompañamientos", precio=19.90, stock=40),
            Producto(nombre="Chicha Morada (1L)",         categoria="Bebidas",         precio=8.00,  stock=60),
        ]
        db.session.add_all(productos)

    if not Servicio.query.first():
        servicios = [
            Servicio(nombre="Delivery a Domicilio", tipo="Entrega",     precio=5.00,   disponibilidad="Todos los días"),
            Servicio(nombre="Reserva de Mesa",       tipo="Restaurante", precio=0.00,   disponibilidad="Lun-Dom"),
            Servicio(nombre="Menú Corporativo",      tipo="Empresarial", precio=35.00,  disponibilidad="Lun-Vie"),
            Servicio(nombre="Catering para Eventos", tipo="Eventos",     precio=500.00, disponibilidad="Previa cita", estado="Inactivo"),
        ]
        db.session.add_all(servicios)

    if not Cliente.query.first():
        clientes = [
            Cliente(nombre="María López",    dni="47821093", telefono="987654321", email="maria@gmail.com",     visitas=12),
            Cliente(nombre="Carlos Quispe",  dni="72103948", telefono="956123789", email="cquispe@outlook.com", visitas=8),
            Cliente(nombre="Ana Rodríguez",  dni="60394812", telefono="912345678", email="ana.rod@gmail.com",   visitas=25),
        ]
        db.session.add_all(clientes)

    db.session.commit()


with app.app_context():
    db.create_all()
    seed()


# ─── Decoradores ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesión primero.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesión primero.", "error")
            return redirect(url_for("login"))
        if session.get("rol") != "Administrador":
            flash("No tienes permiso para realizar esta acción.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════════════════════
#   RUTAS PÚBLICAS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def inicio():
    return render_template("index.html")


# ══════════════════════════════════════════════════════════════════════════════
#   AUTH
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usu  = request.form.get("usuario", "").strip()
        pwd  = request.form.get("password", "")
        user = Usuario.query.filter_by(usuario=usu, estado="Activo").first()

        if user and check_password_hash(user.password, pwd):
            session["user_id"]  = user.id
            session["username"] = user.usuario
            session["rol"]      = user.rol
            return redirect(url_for("dashboard"))

        flash("Usuario o contraseña incorrectos.", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("inicio"))


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre  = request.form["nombre"].strip()
        usuario = request.form["usuario"].strip()
        pwd     = request.form["password"]
        pwd2    = request.form["password2"]
        rol     = request.form["rol"]

        if pwd != pwd2:
            flash("Las contraseñas no coinciden.", "error")
            return redirect(url_for("registro"))

        if Usuario.query.filter_by(usuario=usuario).first():
            flash("Ese nombre de usuario ya existe.", "error")
            return redirect(url_for("registro"))

        u = Usuario(
            nombre   = nombre,
            usuario  = usuario,
            password = generate_password_hash(pwd),
            rol      = rol,
            estado   = "Activo",
        )
        db.session.add(u)
        db.session.commit()
        flash("Cuenta creada correctamente. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("login"))

    return render_template("registro.html")


# ══════════════════════════════════════════════════════════════════════════════
#   DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/admin")
@login_required
def dashboard():
    stats = {
        "productos": Producto.query.filter_by(estado="Activo").count(),
        "servicios": Servicio.query.count(),
        "clientes":  Cliente.query.count(),
        "usuarios":  Usuario.query.count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


# ══════════════════════════════════════════════════════════════════════════════
#   PRODUCTOS — CRUD
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/admin/productos")
@login_required
def productos():
    q    = request.args.get("q", "").strip()
    data = Producto.query.filter(Producto.nombre.ilike(f"%{q}%")).all() if q else Producto.query.all()
    return render_template("admin/productos.html", productos=data, q=q)


@app.route("/admin/productos/nuevo", methods=["GET", "POST"])
@admin_required
def producto_nuevo():
    if request.method == "POST":
        p = Producto(
            nombre    = request.form["nombre"].strip(),
            categoria = request.form["categoria"].strip(),
            precio    = float(request.form["precio"]),
            stock     = int(request.form["stock"]),
            estado    = request.form["estado"],
        )
        db.session.add(p)
        db.session.commit()
        flash("Producto creado correctamente.", "success")
        return redirect(url_for("productos"))
    return render_template("admin/producto_form.html", producto=None)


@app.route("/admin/productos/<int:id>/editar", methods=["GET", "POST"])
@admin_required
def producto_editar(id):
    p = Producto.query.get_or_404(id)
    if request.method == "POST":
        p.nombre    = request.form["nombre"].strip()
        p.categoria = request.form["categoria"].strip()
        p.precio    = float(request.form["precio"])
        p.stock     = int(request.form["stock"])
        p.estado    = request.form["estado"]
        db.session.commit()
        flash("Producto actualizado.", "success")
        return redirect(url_for("productos"))
    return render_template("admin/producto_form.html", producto=p)


@app.route("/admin/productos/<int:id>/eliminar", methods=["POST"])
@admin_required
def producto_eliminar(id):
    p = Producto.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    flash("Producto eliminado.", "success")
    return redirect(url_for("productos"))


# ══════════════════════════════════════════════════════════════════════════════
#   SERVICIOS — CRUD
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/admin/servicios")
@login_required
def servicios():
    q    = request.args.get("q", "").strip()
    data = Servicio.query.filter(Servicio.nombre.ilike(f"%{q}%")).all() if q else Servicio.query.all()
    return render_template("admin/servicios.html", servicios=data, q=q)


@app.route("/admin/servicios/nuevo", methods=["GET", "POST"])
@admin_required
def servicio_nuevo():
    if request.method == "POST":
        s = Servicio(
            nombre         = request.form["nombre"].strip(),
            tipo           = request.form["tipo"].strip(),
            precio         = float(request.form["precio"]),
            disponibilidad = request.form["disponibilidad"].strip(),
            estado         = request.form["estado"],
        )
        db.session.add(s)
        db.session.commit()
        flash("Servicio creado correctamente.", "success")
        return redirect(url_for("servicios"))
    return render_template("admin/servicio_form.html", servicio=None)


@app.route("/admin/servicios/<int:id>/editar", methods=["GET", "POST"])
@admin_required
def servicio_editar(id):
    s = Servicio.query.get_or_404(id)
    if request.method == "POST":
        s.nombre         = request.form["nombre"].strip()
        s.tipo           = request.form["tipo"].strip()
        s.precio         = float(request.form["precio"])
        s.disponibilidad = request.form["disponibilidad"].strip()
        s.estado         = request.form["estado"]
        db.session.commit()
        flash("Servicio actualizado.", "success")
        return redirect(url_for("servicios"))
    return render_template("admin/servicio_form.html", servicio=s)


@app.route("/admin/servicios/<int:id>/eliminar", methods=["POST"])
@admin_required
def servicio_eliminar(id):
    s = Servicio.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    flash("Servicio eliminado.", "success")
    return redirect(url_for("servicios"))


# ══════════════════════════════════════════════════════════════════════════════
#   CLIENTES — CRUD
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/admin/clientes")
@login_required
def clientes():
    q    = request.args.get("q", "").strip()
    data = Cliente.query.filter(
        (Cliente.nombre.ilike(f"%{q}%")) | (Cliente.dni.ilike(f"%{q}%"))
    ).all() if q else Cliente.query.all()
    return render_template("admin/clientes.html", clientes=data, q=q)


@app.route("/admin/clientes/nuevo", methods=["GET", "POST"])
@admin_required
def cliente_nuevo():
    if request.method == "POST":
        c = Cliente(
            nombre   = request.form["nombre"].strip(),
            dni      = request.form["dni"].strip(),
            telefono = request.form.get("telefono", "").strip(),
            email    = request.form.get("email", "").strip(),
            visitas  = int(request.form.get("visitas", 0)),
        )
        db.session.add(c)
        db.session.commit()
        flash("Cliente registrado correctamente.", "success")
        return redirect(url_for("clientes"))
    return render_template("admin/cliente_form.html", cliente=None)


@app.route("/admin/clientes/<int:id>/editar", methods=["GET", "POST"])
@admin_required
def cliente_editar(id):
    c = Cliente.query.get_or_404(id)
    if request.method == "POST":
        c.nombre   = request.form["nombre"].strip()
        c.dni      = request.form["dni"].strip()
        c.telefono = request.form.get("telefono", "").strip()
        c.email    = request.form.get("email", "").strip()
        c.visitas  = int(request.form.get("visitas", 0))
        db.session.commit()
        flash("Cliente actualizado.", "success")
        return redirect(url_for("clientes"))
    return render_template("admin/cliente_form.html", cliente=c)


@app.route("/admin/clientes/<int:id>/eliminar", methods=["POST"])
@admin_required
def cliente_eliminar(id):
    c = Cliente.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    flash("Cliente eliminado.", "success")
    return redirect(url_for("clientes"))


# ══════════════════════════════════════════════════════════════════════════════
#   USUARIOS — CRUD
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/admin/usuarios")
@login_required
def usuarios():
    data = Usuario.query.all()
    return render_template("admin/usuarios.html", usuarios=data)


@app.route("/admin/usuarios/nuevo", methods=["GET", "POST"])
@admin_required
def usuario_nuevo():
    if request.method == "POST":
        pwd = request.form["password"].strip()
        u = Usuario(
            nombre   = request.form["nombre"].strip(),
            usuario  = request.form["usuario"].strip(),
            password = generate_password_hash(pwd),
            rol      = request.form["rol"],
            estado   = request.form["estado"],
        )
        db.session.add(u)
        db.session.commit()
        flash("Usuario creado correctamente.", "success")
        return redirect(url_for("usuarios"))
    return render_template("admin/usuario_form.html", usr=None)


@app.route("/admin/usuarios/<int:id>/editar", methods=["GET", "POST"])
@admin_required
def usuario_editar(id):
    u = Usuario.query.get_or_404(id)
    if request.method == "POST":
        u.nombre  = request.form["nombre"].strip()
        u.usuario = request.form["usuario"].strip()
        u.rol     = request.form["rol"]
        u.estado  = request.form["estado"]
        pwd = request.form.get("password", "").strip()
        if pwd:
            u.password = generate_password_hash(pwd)
        db.session.commit()
        flash("Usuario actualizado.", "success")
        return redirect(url_for("usuarios"))
    return render_template("admin/usuario_form.html", usr=u)


@app.route("/admin/usuarios/<int:id>/eliminar", methods=["POST"])
@admin_required
def usuario_eliminar(id):
    if id == session.get("user_id"):
        flash("No puedes eliminar tu propia cuenta.", "error")
        return redirect(url_for("usuarios"))
    u = Usuario.query.get_or_404(id)
    db.session.delete(u)
    db.session.commit()
    flash("Usuario eliminado.", "success")
    return redirect(url_for("usuarios"))


if __name__ == "__main__":
    app.run(debug=True)