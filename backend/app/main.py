from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from typing import List

from . import models, schemas, database

app = FastAPI(title="API ANS")

# 1. Rota de Listagem com Busca e Paginação + Metadados
@app.get("/api/operadoras", response_model=schemas.PaginatedResponse)
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

    stmt = select(models.DespesaConsolidada).where(
        models.DespesaConsolidada.registro_operadora == registro
    ).order_by(models.DespesaConsolidada.ano.desc(), models.DespesaConsolidada.trimestre.desc())
    
    result = await db.execute(stmt)
    return result.scalars().all()

# 4. Estatísticas Agregadas
@app.get("/api/estatisticas", response_model=List[schemas.EstatisticaResponse])
async def ver_estatisticas(db: AsyncSession = Depends(database.get_db)):
    # Retorna o TOP 5 maiores despesas
    stmt = select(models.DespesaAgregada).order_by(models.DespesaAgregada.valor_total.desc()).limit(5)
    
    result = await db.execute(stmt)
    return result.scalars().all()