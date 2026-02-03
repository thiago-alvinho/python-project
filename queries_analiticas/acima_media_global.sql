WITH despesas_por_operadora AS (
    -- Cálculo do total de gastos de cada operadora em cada trimestre
    SELECT 
        ano, 
        trimestre,
        registro_operadora,
        SUM(valor_despesas) AS total_operadora
    FROM despesas_consolidadas
    GROUP BY ano, trimestre, registro_operadora
),
media_mercado_trimestral AS (
    -- Calcula a média do mercado usando os totais do passo 1
    SELECT 
        ano,
        trimestre,
        AVG(total_operadora) AS media_geral
    FROM despesas_por_operadora
    GROUP BY ano, trimestre
),
operadoras_acima_media AS (
    -- Cruza os dados e verifica quem ficou acima da média
    SELECT 
        dpo.registro_operadora
    FROM despesas_por_operadora AS dpo
    JOIN media_mercado_trimestral AS mmt 
        ON dpo.ano = mmt.ano AND dpo.trimestre = mmt.trimestre
    WHERE dpo.total_operadora > mmt.media_geral
    GROUP BY dpo.registro_operadora
    -- Filtra apenas quem bateu a meta em 2 ou mais trimestres
    HAVING COUNT(*) >= 2
)
-- Contagem simples de quantas operadoras atenderam aos critérios
SELECT COUNT(*) AS qtd_operadoras_acima FROM operadoras_acima_media;