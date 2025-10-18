from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

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
