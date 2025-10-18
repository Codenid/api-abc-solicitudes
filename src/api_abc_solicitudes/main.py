# app.py
from datetime import datetime
from typing import List, Optional, Literal

import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import (
    create_engine, Column, Integer, String, SmallInteger, BigInteger, Numeric,
    Text, TIMESTAMP, ForeignKey, UniqueConstraint, func, and_, or_, select
)
from sqlalchemy.orm import declarative_base, relationship, Session, sessionmaker

# -----------------------------------------------------------------------------
# Configuración
# -----------------------------------------------------------------------------

load_dotenv()

DB_URL = os.getenv("DATABASE_URL","")

engine = create_engine(DB_URL, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()

# -----------------------------------------------------------------------------
# Modelos ORM (respetan el esquema dado)
# -----------------------------------------------------------------------------
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
    resultado = Column(String(16), nullable=False)  # CHECK en BD
    justificacion = Column(Text)
    monto_reintegrar = Column(Numeric(12, 2))
    fecha_decision = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())

    reclamo = relationship("Reclamo", back_populates="decision")

# -----------------------------------------------------------------------------
# Schemas (Pydantic)
# -----------------------------------------------------------------------------
class MovimientoIn(BaseModel):
    id_movimiento: int = Field(..., description="ID numérico del movimiento externo")
    rol: Optional[str] = Field(default="DISPUTA", description="Rol del movimiento en el reclamo")

class ReclamoCreate(BaseModel):
    id_cliente: int
    id_tarjeta: int
    id_tipo_reclamo: int
    id_estado_actual: int
    id_canal_ingreso: int
    descripcion: Optional[str] = None
    monto: Optional[float] = None
    id_moneda: int
    fecha_apertura: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None
    sla_dias: Optional[int] = 30
    referencia_externa: Optional[str] = None
    movimientos: Optional[List[MovimientoIn]] = Field(default=None, description="Lista opcional de movimientos asociados")

class ReclamoItem(BaseModel):
    id_reclamo: int
    id_cliente: int
    id_tarjeta: int
    descripcion: Optional[str]
    monto: Optional[float]
    fecha_apertura: datetime
    fecha_cierre: Optional[datetime]
    sla_dias: Optional[int]
    referencia_externa: Optional[str]
    tipo_codigo: str
    estado_codigo: str
    canal_codigo: str
    moneda_codigo: str

class MovimientoOut(BaseModel):
    id_reclamo_mov: int
    id_movimiento: int
    rol: str

class DecisionOut(BaseModel):
    id_decision: int
    resultado: Literal["PROCEDENTE","IMPROCEDENTE","PARCIAL"]
    justificacion: Optional[str]
    monto_reintegrar: Optional[float]
    fecha_decision: datetime

class ReclamoDetail(BaseModel):
    id_reclamo: int
    id_cliente: int
    id_tarjeta: int
    descripcion: Optional[str]
    monto: Optional[float]
    fecha_apertura: datetime
    fecha_cierre: Optional[datetime]
    sla_dias: Optional[int]
    referencia_externa: Optional[str]

    tipo: dict   # {id, codigo, nombre, criticidad}
    estado: dict # {id, codigo, nombre}
    canal: dict  # {id, codigo, nombre}
    moneda: dict # {id, codigo, nombre}

    movimientos: List[MovimientoOut]
    decision: Optional[DecisionOut]

class Page(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[ReclamoItem]

# -----------------------------------------------------------------------------
# FastAPI
# -----------------------------------------------------------------------------
app = FastAPI(
    title="API de Reclamos",
    version="1.0.0",
    description="""
API simple para gestionar **reclamos**.

**Endpoints:**
- `GET /reclamos`: consulta básica con filtros y paginación.
- `GET /reclamos/{id}`: detalle de un reclamo (catálogos, movimientos, decisión).
- `POST /reclamos`: creación de reclamo, opcionalmente con movimientos.
"""
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def ensure_catalogs_exist(db: Session, *, id_tipo: int, id_estado: int, id_canal: int, id_moneda: int):
    if not db.get(CatTipoReclamo, id_tipo):
        raise HTTPException(status_code=400, detail="id_tipo_reclamo no existe")
    if not db.get(CatEstadoReclamo, id_estado):
        raise HTTPException(status_code=400, detail="id_estado_actual no existe")
    if not db.get(CatCanalIngreso, id_canal):
        raise HTTPException(status_code=400, detail="id_canal_ingreso no existe")
    if not db.get(CatMoneda, id_moneda):
        raise HTTPException(status_code=400, detail="id_moneda no existe")

# -----------------------------------------------------------------------------
# 1) GET /reclamos  — filtros + paginación
# -----------------------------------------------------------------------------
@app.get("/reclamos", response_model=Page, tags=["Reclamos"])
def list_reclamos(
    page: int = Query(1, ge=1, description="Página (1..N)"),
    page_size: int = Query(20, ge=1, le=100, description="Tamaño de página (1..100)"),
    # Filtros por columnas de reclamo
    id_reclamo: Optional[int] = None,
    id_cliente: Optional[int] = None,
    id_tarjeta: Optional[int] = None,
    id_tipo_reclamo: Optional[int] = None,
    id_estado_actual: Optional[int] = None,
    id_canal_ingreso: Optional[int] = None,
    id_moneda: Optional[int] = None,
    referencia_externa: Optional[str] = Query(None, description="Coincidencia exacta"),
    search: Optional[str] = Query(None, description="Búsqueda en descripción (ILIKE)"),
    abierto: Optional[bool] = Query(None, description="True: sin fecha_cierre"),
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    monto_min: Optional[float] = None,
    monto_max: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """
    Devuelve una lista *básica* de reclamos con datos esenciales y códigos de catálogos.
    Soporta filtros por cualquier campo de `reclamo` y paginación.
    """
    R = Reclamo
    T = CatTipoReclamo
    E = CatEstadoReclamo
    C = CatCanalIngreso
    M = CatMoneda

    base = (
        db.query(
            R.id_reclamo, R.id_cliente, R.id_tarjeta, R.descripcion, R.monto,
            R.fecha_apertura, R.fecha_cierre, R.sla_dias, R.referencia_externa,
            T.codigo.label("tipo_codigo"),
            E.codigo.label("estado_codigo"),
            C.codigo.label("canal_codigo"),
            M.codigo.label("moneda_codigo"),
        )
        .join(T, R.id_tipo_reclamo == T.id_tipo_reclamo)
        .join(E, R.id_estado_actual == E.id_estado)
        .join(C, R.id_canal_ingreso == C.id_canal)
        .join(M, R.id_moneda == M.id_moneda)
    )

    # Construcción dinámica de filtros
    conditions = []
    if id_reclamo is not None:        conditions.append(R.id_reclamo == id_reclamo)
    if id_cliente is not None:        conditions.append(R.id_cliente == id_cliente)
    if id_tarjeta is not None:        conditions.append(R.id_tarjeta == id_tarjeta)
    if id_tipo_reclamo is not None:   conditions.append(R.id_tipo_reclamo == id_tipo_reclamo)
    if id_estado_actual is not None:  conditions.append(R.id_estado_actual == id_estado_actual)
    if id_canal_ingreso is not None:  conditions.append(R.id_canal_ingreso == id_canal_ingreso)
    if id_moneda is not None:         conditions.append(R.id_moneda == id_moneda)
    if referencia_externa:            conditions.append(R.referencia_externa == referencia_externa)
    if search:                        conditions.append(R.descripcion.ilike(f"%{search}%"))
    if abierto is True:               conditions.append(R.fecha_cierre.is_(None))
    if fecha_desde:                   conditions.append(R.fecha_apertura >= fecha_desde)
    if fecha_hasta:                   conditions.append(R.fecha_apertura <  fecha_hasta)
    if monto_min is not None:         conditions.append(R.monto >= monto_min)
    if monto_max is not None:         conditions.append(R.monto <= monto_max)

    if conditions:
        base = base.filter(and_(*conditions))

    # total
    count_q = db.query(func.count(R.id_reclamo))
    if conditions:
        count_q = count_q.filter(and_(*conditions))
    total = count_q.scalar()

    # página
    items = (
        base
        .order_by(R.fecha_apertura.desc(), R.id_reclamo.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Adaptar a schema
    items_out = [ReclamoItem(
        id_reclamo=i.id_reclamo,
        id_cliente=i.id_cliente,
        id_tarjeta=i.id_tarjeta,
        descripcion=i.descripcion,
        monto=float(i.monto) if i.monto is not None else None,
        fecha_apertura=i.fecha_apertura,
        fecha_cierre=i.fecha_cierre,
        sla_dias=i.sla_dias,
        referencia_externa=i.referencia_externa,
        tipo_codigo=i.tipo_codigo,
        estado_codigo=i.estado_codigo,
        canal_codigo=i.canal_codigo,
        moneda_codigo=i.moneda_codigo,
    ) for i in items]

    return Page(page=page, page_size=page_size, total=total, items=items_out)

# -----------------------------------------------------------------------------
# 2) GET /reclamos/{id}  — detalle con catálogos, movimientos, decisión
# -----------------------------------------------------------------------------
@app.get("/reclamos/{id_reclamo}", response_model=ReclamoDetail, tags=["Reclamos"])
def get_reclamo_detail(id_reclamo: int, db: Session = Depends(get_db)):
    r: Reclamo = (
        db.query(Reclamo)
        .filter(Reclamo.id_reclamo == id_reclamo)
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="Reclamo no encontrado")

    return ReclamoDetail(
        id_reclamo=r.id_reclamo,
        id_cliente=r.id_cliente,
        id_tarjeta=r.id_tarjeta,
        descripcion=r.descripcion,
        monto=float(r.monto) if r.monto is not None else None,
        fecha_apertura=r.fecha_apertura,
        fecha_cierre=r.fecha_cierre,
        sla_dias=r.sla_dias,
        referencia_externa=r.referencia_externa,
        tipo={"id": r.tipo.id_tipo_reclamo, "codigo": r.tipo.codigo, "nombre": r.tipo.nombre, "criticidad": r.tipo.criticidad},
        estado={"id": r.estado.id_estado, "codigo": r.estado.codigo, "nombre": r.estado.nombre},
        canal={"id": r.canal.id_canal, "codigo": r.canal.codigo, "nombre": r.canal.nombre},
        moneda={"id": r.moneda.id_moneda, "codigo": r.moneda.codigo, "nombre": r.moneda.nombre},
        movimientos=[
            MovimientoOut(
                id_reclamo_mov=m.id_reclamo_mov,
                id_movimiento=m.id_movimiento,
                rol=m.rol
            ) for m in r.movimientos
        ],
        decision=(
            DecisionOut(
                id_decision=r.decision.id_decision,
                resultado=r.decision.resultado,  # validado por CHECK en BD
                justificacion=r.decision.justificacion,
                monto_reintegrar=float(r.decision.monto_reintegrar) if r.decision.monto_reintegrar is not None else None,
                fecha_decision=r.decision.fecha_decision
            ) if r.decision else None
        )
    )

# -----------------------------------------------------------------------------
# 3) POST /reclamos  — creación (con movimientos opcionales)
# -----------------------------------------------------------------------------
@app.post("/reclamos", response_model=ReclamoDetail, status_code=201, tags=["Reclamos"])
def create_reclamo(payload: ReclamoCreate, db: Session = Depends(get_db)):
    # Validaciones básicas de catálogos
    ensure_catalogs_exist(
        db,
        id_tipo=payload.id_tipo_reclamo,
        id_estado=payload.id_estado_actual,
        id_canal=payload.id_canal_ingreso,
        id_moneda=payload.id_moneda
    )

    # Crear reclamo
    r = Reclamo(
        id_cliente=payload.id_cliente,
        id_tarjeta=payload.id_tarjeta,
        id_tipo_reclamo=payload.id_tipo_reclamo,
        id_estado_actual=payload.id_estado_actual,
        id_canal_ingreso=payload.id_canal_ingreso,
        descripcion=payload.descripcion,
        monto=payload.monto,
        id_moneda=payload.id_moneda,
        fecha_apertura=payload.fecha_apertura or datetime.utcnow(),
        fecha_cierre=payload.fecha_cierre,
        sla_dias=payload.sla_dias,
        referencia_externa=payload.referencia_externa
    )
    db.add(r)
    db.flush()  # obtiene id_reclamo

    # Movimientos (opcional)
    if payload.movimientos:
        for mv in payload.movimientos:
            db.add(ReclamoMovimiento(
                id_reclamo=r.id_reclamo,
                id_movimiento=mv.id_movimiento,
                rol=mv.rol or "DISPUTA"
            ))

    db.commit()
    db.refresh(r)  # recarga relaciones

    # Responder con detalle
    return get_reclamo_detail(r.id_reclamo, db)
