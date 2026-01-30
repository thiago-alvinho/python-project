from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class OperadoraBase(BaseModel):
    registro_operadora: str
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    modalidade: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    cep: Optional[str] = None
    ddd: Optional[int] = None
    telefone: Optional[str] = None
    fax: Optional[str] = None
    endereco_eletronico: Optional[str] = None
    representante: Optional[str] = None
    cargo_representante: Optional[str] = None
    regiao_comercializacao: Optional[int] = None
    data_registro_ans: Optional[date] = None

    class Config:
        from_attributes = True

class DespesaResponse(BaseModel):
    trimestre: str
    ano: int
    valor_despesas: float

    class Config:
        from_attributes = True

class EstatisticaResponse(BaseModel):
    razao_social: str
    uf: Optional[str]
    valor_total: float
    media_trimestral: float
    desvio_padrao: float

    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    data: List[OperadoraBase]
    total: int
    page: int
    limit: int