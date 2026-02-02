-- 1. Tabela de Dimensão: Operadoras
CREATE TABLE operadoras (
    registro_operadora CHAR(6) PRIMARY KEY, 
    cnpj CHAR(14) NOT NULL UNIQUE,          
    razao_social TEXT NOT NULL,
    nome_fantasia TEXT,
    modalidade TEXT,
    logradouro TEXT,
    numero TEXT,                          
    complemento TEXT,
    bairro VARCHAR(50),
    cidade VARCHAR(50),
    uf CHAR(2),
    cep VARCHAR(8),
    ddd INT,
    telefone VARCHAR(20),
    fax VARCHAR(20),
    endereco_eletronico TEXT,
    representante TEXT,
    cargo_representante TEXT,
    regiao_comercializacao INT,
    data_registro_ans DATE
);

CREATE INDEX idx_operadoras_razao_social ON operadoras(razao_social);


-- 2. Tabela Fato: Despesas Consolidadas
CREATE TABLE despesas_consolidadas (
    id SERIAL PRIMARY KEY,
    registro_operadora CHAR(6) NOT NULL,
    trimestre CHAR(2) NOT NULL,
    ano INT NOT NULL,
    valor_despesas DECIMAL(15, 2) NOT NULL,
    
    CONSTRAINT fk_operadora_despesa 
        FOREIGN KEY (registro_operadora) 
        REFERENCES operadoras(registro_operadora)
);

CREATE INDEX idx_despesas_reg_operadora ON despesas_consolidadas(registro_operadora);

-- 3. Tabela de Agregação
CREATE TABLE despesas_agregadas (
    razao_social TEXT PRIMARY KEY,
    uf CHAR(2),
    valor_total DECIMAL(20, 2),
    media_trimestral DECIMAL(20, 2),
    desvio_padrao DECIMAL(20, 2)
);

-- 4. Inserção dados operadoras
CREATE TEMP TABLE staging_operadoras (
    registro_operadora TEXT,
    cnpj TEXT,
    razao_social TEXT,
    nome_fantasia TEXT,
    modalidade TEXT,
    logradouro TEXT,
    numero TEXT,
    complemento TEXT,
    bairro TEXT,
    cidade TEXT,
    uf TEXT,
    cep TEXT,
    ddd TEXT,
    telefone TEXT,
    fax TEXT,
    endereco_eletronico TEXT,
    representante TEXT,
    cargo_representante TEXT,
    regiao_comercializacao TEXT,
    data_registro_ans TEXT
);

COPY staging_operadoras FROM '/tmp/csv_data/Relatorio_cadop.csv' 
WITH (FORMAT CSV, HEADER true, DELIMITER ';', QUOTE '"', ENCODING 'UTF8');

INSERT INTO operadoras 
SELECT 
    LPAD(registro_operadora, 6, '0'),
    LPAD(cnpj, 14, '0'),
    razao_social,
    nome_fantasia,
    modalidade,
    logradouro,
    numero,
    complemento,
    bairro,
    cidade,
    uf,
    LPAD(cep, 8, '0'),
    NULLIF(ddd, '')::INT,
    telefone,
    fax,
    endereco_eletronico,
    representante,
    cargo_representante,
    NULLIF(regiao_comercializacao, '')::INT,
    TO_DATE(data_registro_ans, 'YYYY-MM-DD')
FROM staging_operadoras
ON CONFLICT (registro_operadora) DO NOTHING;


-- 5. Inserção dados despesas
CREATE TEMP TABLE staging_despesas (
    reg_ans TEXT,
    trimestre TEXT,
    ano TEXT,
    valor_despesas TEXT,
    despesas_suspeitas TEXT
);

COPY staging_despesas FROM '/tmp/csv_data/consolidado_despesas.csv' 
WITH (FORMAT CSV, HEADER true, DELIMITER ';', ENCODING 'UTF8');

INSERT INTO despesas_consolidadas (registro_operadora, trimestre, ano, valor_despesas)
SELECT 
    LPAD(reg_ans, 6, '0'),
    trimestre,
    ano::INT,
    REPLACE(valor_despesas, ',', '.')::DECIMAL(15,2)
FROM staging_despesas
WHERE 
    EXISTS (
        SELECT 1 FROM operadoras op 
        WHERE op.registro_operadora = LPAD(staging_despesas.reg_ans, 6, '0')
    )

    AND despesas_suspeitas::boolean = false;

CREATE TEMP TABLE staging_agregadas (
    razao_social TEXT,
    uf TEXT,
    valor_total TEXT,
    media_trimestral TEXT,
    desvio_padrao TEXT
);

COPY staging_agregadas FROM '/tmp/csv_data/despesas_agregadas.csv' 
WITH (FORMAT CSV, HEADER true, DELIMITER ';', ENCODING 'UTF8');

INSERT INTO despesas_agregadas
SELECT 
    razao_social,
    uf,
    NULLIF(REPLACE(valor_total, ',', '.'), '')::DECIMAL(20,2),
    NULLIF(REPLACE(media_trimestral, ',', '.'), '')::DECIMAL(20,2),
    NULLIF(REPLACE(desvio_padrao, ',', '.'), '')::DECIMAL(20,2)
FROM staging_agregadas
ON CONFLICT (razao_social) DO NOTHING;