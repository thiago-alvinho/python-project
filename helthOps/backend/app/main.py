from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from typing import List
from async_lru import alru_cache

from . import models, schemas, database

app = FastAPI(title="API ANS")

origins = [
    "http://localhost:3001", 
    "http://localhost:5173", 
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,   
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Rota de Listagem com Busca e Paginação + Metadados
@app.get("/api/operadoras", response_model=schemas.PaginatedResponse)
@alru_cache(maxsize=1, ttl=3600)
async def listar_operadoras(
    search: str = Query(None, description="Busca por Razão Social ou CNPJ"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(database.get_db)
):
    skip = (page - 1) * limit
    
    query = select(models.Operadora)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                models.Operadora.razao_social.ilike(search_term),
                models.Operadora.cnpj.ilike(search_term)
            )
        )
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    result = await db.execute(query.offset(skip).limit(limit))
    operadoras = result.scalars().all()

    return {
        "data": operadoras,
        "total": total,
        "page": page,
        "limit": limit
    }

# 2. Busca por CNPJ ou Registro
@app.get("/api/operadoras/{identificador}", response_model=schemas.OperadoraBase)
async def detalhar_operadora(identificador: str, db: AsyncSession = Depends(database.get_db)):
    # Tenta buscar por Registro ANS (6 dígitos) OU CNPJ (14 dígitos)
    identificador_limpo = identificador.replace(".", "").replace("/", "").replace("-", "")
    
    stmt = select(models.Operadora).where(
        or_(
            models.Operadora.registro_operadora == identificador_limpo,
            models.Operadora.cnpj == identificador_limpo
        )
    )
    result = await db.execute(stmt)
    op = result.scalars().first()
    
    if not op:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")
    return op

# 3. Histórico de Despesas
@app.get("/api/operadoras/{registro}/despesas", response_model=List[schemas.DespesaResponse])
async def listar_despesas(registro: str, db: AsyncSession = Depends(database.get_db)):

    registro_formatado = registro.strip().zfill(6)
    
    stmt = select(models.DespesaConsolidada).where(
        models.DespesaConsolidada.registro_operadora == registro
    ).order_by(models.DespesaConsolidada.ano.desc(), models.DespesaConsolidada.trimestre.desc())
    
    result = await db.execute(stmt)
    return result.scalars().all()

# 4. Estatísticas Agregadas
@app.get("/api/estatisticas", response_model=schemas.DashboardResponse)
async def ver_estatisticas(db: AsyncSession = Depends(database.get_db)):
    
    # 1. Valor total e média
    query_geral = select(
        func.sum(models.DespesaAgregada.valor_total),
        func.avg(models.DespesaAgregada.valor_total)
    )
    result_geral = await db.execute(query_geral)
    total_geral, media_geral = result_geral.one()

    if total_geral is None:
        total_geral = 0
    if media_geral is None:
        media_geral = 0

    # 2. Top 5 Operadoras
    query_top5 = select(models.DespesaAgregada)\
        .order_by(models.DespesaAgregada.valor_total.desc())\
        .limit(5)
    result_top5 = await db.execute(query_top5)
    top_5 = result_top5.scalars().all()

    # 3. Distribuição por UF
    query_uf = select(
        models.DespesaAgregada.uf,
        func.sum(models.DespesaAgregada.valor_total).label("total")
    )\
    .group_by(models.DespesaAgregada.uf)\
    .order_by(func.sum(models.DespesaAgregada.valor_total).desc())
    
    result_uf = await db.execute(query_uf)

    # Transforma o resultado (que vem como tuplas) em uma lista de dicionários
    lista_uf = [{"uf": row.uf if row.uf else "N/A", "total": row.total} for row in result_uf.all()]

    return {
        "total_despesas": total_geral,
        "media_despesas": media_geral,
        "top_5_operadoras": top_5,
        "despesas_por_uf": lista_uf
    }