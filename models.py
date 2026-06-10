from database import db
from datetime import datetime


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id       = db.Column(db.Integer, primary_key=True)
    nombre   = db.Column(db.String(120), nullable=False)
    usuario  = db.Column(db.String(60),  nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    rol      = db.Column(db.String(40),  nullable=False, default="Operador")
    estado   = db.Column(db.String(20),  nullable=False, default="Activo")
    creado   = db.Column(db.DateTime,    default=datetime.utcnow)


class Producto(db.Model):
    __tablename__ = "productos"

    id         = db.Column(db.Integer, primary_key=True)
    nombre     = db.Column(db.String(120), nullable=False)
    categoria  = db.Column(db.String(80),  nullable=False)
    precio     = db.Column(db.Float,       nullable=False)
    stock      = db.Column(db.Integer,     nullable=False, default=0)
    estado     = db.Column(db.String(20),  nullable=False, default="Activo")
    creado     = db.Column(db.DateTime,    default=datetime.utcnow)


class Servicio(db.Model):
    __tablename__ = "servicios"

    id              = db.Column(db.Integer, primary_key=True)
    nombre          = db.Column(db.String(120), nullable=False)
    tipo            = db.Column(db.String(80),  nullable=False)
    precio          = db.Column(db.Float,       nullable=False, default=0.0)
    disponibilidad  = db.Column(db.String(120), nullable=False)
    estado          = db.Column(db.String(20),  nullable=False, default="Activo")
    creado          = db.Column(db.DateTime,    default=datetime.utcnow)


class Cliente(db.Model):
    __tablename__ = "clientes"

    id       = db.Column(db.Integer, primary_key=True)
    nombre   = db.Column(db.String(120), nullable=False)
    dni      = db.Column(db.String(12),  nullable=False, unique=True)
    telefono = db.Column(db.String(20),  nullable=True)
    email    = db.Column(db.String(120), nullable=True)
    visitas  = db.Column(db.Integer,     nullable=False, default=0)
    creado   = db.Column(db.DateTime,    default=datetime.utcnow)
