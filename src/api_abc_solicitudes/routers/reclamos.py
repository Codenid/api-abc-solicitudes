from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from src.api_abc_solicitudes.db import get_db
from src.api_abc_solicitudes.models import (
    Reclamo, ReclamoMovimiento, CatTipoReclamo, CatEstadoReclamo,
    CatCanalIngreso, CatMoneda
)
from src.api_abc_solicitudes.schemas import (
    Page, ReclamoItem, ReclamoDetail, ReclamoCreate,
    MovimientoOut, DecisionOut
)

router = APIRouter()

def ensure_catalogs_exist(db: Session, *, id_tipo: int, id_estado: int, id_canal: int, id_moneda: int):
    if not db.get(CatTipoReclamo, id_tipo):
        raise HTTPException(status_code=400, detail="id_tipo_reclamo no existe")
    if not db.get(CatEstadoReclamo, id_estado):
        raise HTTPException(status_code=400, detail="id_estado_actual no existe")
    if not db.get(CatCanalIngreso, id_canal):
        raise HTTPException(status_code=400, detail="id_canal_ingreso no existe")
    if not db.get(CatMoneda, id_moneda):
        raise HTTPException(status_code=400, detail="id_moneda no existe")

def build_detail(r: Reclamo) -> ReclamoDetail:
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
                resultado=r.decision.resultado,
                justificacion=r.decision.justificacion,
                monto_reintegrar=float(r.decision.monto_reintegrar) if r.decision.monto_reintegrar is not None else None,
                fecha_decision=r.decision.fecha_decision
            ) if r.decision else None
        )
    )

@router.get("/reclamos", response_model=Page, tags=["Reclamos"])
def list_reclamos(
    page: int = Query(1, ge=1, description="Página (1..N)"),
    page_size: int = Query(20, ge=1, le=100, description="Tamaño de página (1..100)"),
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

    count_q = db.query(func.count(R.id_reclamo))
    if conditions:
        count_q = count_q.filter(and_(*conditions))
    total = count_q.scalar()

    items = (
        base
        .order_by(R.fecha_apertura.desc(), R.id_reclamo.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

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

@router.get("/reclamos/{id_reclamo}", response_model=ReclamoDetail, tags=["Reclamos"])
def get_reclamo_detail(id_reclamo: int, db: Session = Depends(get_db)):
    r: Reclamo = (
        db.query(Reclamo)
        .filter(Reclamo.id_reclamo == id_reclamo)
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="Reclamo no encontrado")
    return build_detail(r)

@router.post("/reclamos", response_model=ReclamoDetail, status_code=201, tags=["Reclamos"])
def create_reclamo(payload: ReclamoCreate, db: Session = Depends(get_db)):
    ensure_catalogs_exist(
        db,
        id_tipo=payload.id_tipo_reclamo,
        id_estado=payload.id_estado_actual,
        id_canal=payload.id_canal_ingreso,
        id_moneda=payload.id_moneda
    )

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
    db.flush()

    if payload.movimientos:
        for mv in payload.movimientos:
            db.add(ReclamoMovimiento(
                id_reclamo=r.id_reclamo,
                id_movimiento=mv.id_movimiento,
                rol=mv.rol or "DISPUTA"
            ))

    db.commit()
    db.refresh(r)
    return build_detail(r)
