from sqlalchemy import Column, String, Integer, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Operadora(Base):
    __tablename__ = "operadoras"

    registro_operadora = Column(String(6), primary_key=True, index=True)
    cnpj = Column(String(14), unique=True, index=True, nullable=False)
    razao_social = Column(String, index=True, nullable=False)
    nome_fantasia = Column(String, nullable=True)
    modalidade = Column(String, nullable=True)
    logradouro = Column(String, nullable=True)
    numero = Column(String, nullable=True)
    complemento = Column(String, nullable=True)
    bairro = Column(String(50), nullable=True)
    cidade = Column(String(50), nullable=True)
    uf = Column(String(2), nullable=True)
    cep = Column(String(8), nullable=True)
    ddd = Column(Integer, nullable=True)
    telefone = Column(String(20), nullable=True)
    fax = Column(String(20), nullable=True)
    endereco_eletronico = Column(String, nullable=True)
    representante = Column(String, nullable=True)
    cargo_representante = Column(String, nullable=True)
    regiao_comercializacao = Column(Integer, nullable=True)
    data_registro_ans = Column(Date, nullable=True)

    despesas = relationship("DespesaConsolidada", back_populates="operadora")


class DespesaConsolidada(Base):
    __tablename__ = "despesas_consolidadas"

    id = Column(Integer, primary_key=True, index=True)
    registro_operadora = Column(String(6), ForeignKey("operadoras.registro_operadora"), nullable=False, index=True)
    trimestre = Column(String(2), nullable=False)
    ano = Column(Integer, nullable=False)
    valor_despesas = Column(Numeric(15, 2), nullable=False)

    operadora = relationship("Operadora", back_populates="despesas")


class DespesaAgregada(Base):
    __tablename__ = "despesas_agregadas"

    razao_social = Column(String, primary_key=True, index=True)
    uf = Column(String(2), nullable=True)
    valor_total = Column(Numeric(20, 2), nullable=True)
    media_trimestral = Column(Numeric(20, 2), nullable=True)
    desvio_padrao = Column(Numeric(20, 2), nullable=True)