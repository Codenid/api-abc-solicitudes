from sqlalchemy import (
    Column, Integer, String, SmallInteger, BigInteger, Numeric,
    Text, TIMESTAMP, ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from src.api_abc_solicitudes.db import Base

SCHEMA = "core_reclamos"

class CatEstadoReclamo(Base):
    __tablename__ = "cat_estado_reclamo"
    __table_args__ = {"schema": SCHEMA}
    id_estado = Column(SmallInteger, primary_key=True)
    codigo = Column(String(30), unique=True, nullable=False)
    nombre = Column(String(80), nullable=False)

class CatTipoReclamo(Base):
    __tablename__ = "cat_tipo_reclamo"
    __table_args__ = {"schema": SCHEMA}
    id_tipo_reclamo = Column(SmallInteger, primary_key=True)
    codigo = Column(String(40), unique=True, nullable=False)
    nombre = Column(String(120), nullable=False)
    criticidad = Column(String(12), nullable=False, default="MEDIA")

class CatMoneda(Base):
    __tablename__ = "cat_moneda"
    __table_args__ = {"schema": SCHEMA}
    id_moneda = Column(SmallInteger, primary_key=True)
    codigo = Column(String(3), unique=True, nullable=False)
    nombre = Column(String(32), nullable=False)

class CatCanalIngreso(Base):
    __tablename__ = "cat_canal_ingreso"
    __table_args__ = {"schema": SCHEMA}
    id_canal = Column(SmallInteger, primary_key=True)
    codigo = Column(String(16), unique=True, nullable=False)
    nombre = Column(String(64), nullable=False)

class Reclamo(Base):
    __tablename__ = "reclamo"
    __table_args__ = {"schema": SCHEMA}
    id_reclamo = Column(BigInteger, primary_key=True)
    id_cliente = Column(Integer, nullable=False)
    id_tarjeta = Column(Integer, nullable=False)
    id_tipo_reclamo = Column(SmallInteger, ForeignKey(f"{SCHEMA}.cat_tipo_reclamo.id_tipo_reclamo"), nullable=False)
    id_estado_actual = Column(SmallInteger, ForeignKey(f"{SCHEMA}.cat_estado_reclamo.id_estado"), nullable=False)
    id_canal_ingreso = Column(SmallInteger, ForeignKey(f"{SCHEMA}.cat_canal_ingreso.id_canal"), nullable=False)
    descripcion = Column(Text)
    monto = Column(Numeric(12, 2))
    id_moneda = Column(SmallInteger, ForeignKey(f"{SCHEMA}.cat_moneda.id_moneda"), nullable=False)
    fecha_apertura = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    fecha_cierre = Column(TIMESTAMP)
    sla_dias = Column(SmallInteger, default=30)
    referencia_externa = Column(String(64), unique=True)

    tipo = relationship("CatTipoReclamo")
    estado = relationship("CatEstadoReclamo")
    canal = relationship("CatCanalIngreso")
    moneda = relationship("CatMoneda")

    movimientos = relationship("ReclamoMovimiento", cascade="all, delete-orphan", back_populates="reclamo")
    decision = relationship("ReclamoDecision", cascade="all, delete-orphan", uselist=False, back_populates="reclamo")

class ReclamoMovimiento(Base):
    __tablename__ = "reclamo_movimiento"
    __table_args__ = (
        UniqueConstraint("id_reclamo", "id_movimiento"),
        {"schema": SCHEMA},
    )
    id_reclamo_mov = Column(BigInteger, primary_key=True)
    id_reclamo = Column(BigInteger, ForeignKey(f"{SCHEMA}.reclamo.id_reclamo", ondelete="CASCADE"), nullable=False)
    id_movimiento = Column(BigInteger, nullable=False)
    rol = Column(String(16), nullable=False, default="DISPUTA")

    reclamo = relationship("Reclamo", back_populates="movimientos")

class ReclamoDecision(Base):
    __tablename__ = "reclamo_decision"
    __table_args__ = {"schema": SCHEMA}
    id_decision = Column(BigInteger, primary_key=True)
    id_reclamo = Column(BigInteger, ForeignKey(f"{SCHEMA}.reclamo.id_reclamo", ondelete="CASCADE"), nullable=False, unique=True)
    resultado = Column(String(16), nullable=False)
    justificacion = Column(Text)
    monto_reintegrar = Column(Numeric(12, 2))
    fecha_decision = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())

    reclamo = relationship("Reclamo", back_populates="decision")
