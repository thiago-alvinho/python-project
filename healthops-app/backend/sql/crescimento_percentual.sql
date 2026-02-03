-- Obtendo qual é o primeiro trimestre e o último trimestre analisado
WITH limites_temporais AS (
	SELECT 
		MIN(ano || trimestre) as periodo_inicial,
		MAX(ano || trimestre) as periodo_final
	FROM despesas_consolidadas
),
somas_trimestres_analisados AS (
    -- Soma as despesas dos trimestres analisados
	SELECT
	d.registro_operadora,
	COALESCE(SUM(d.valor_despesas) FILTER(WHERE (d.ano || d.trimestre) = (SELECT periodo_inicial FROM limites_temporais)), 0)AS valor_inicial,
	COALESCE(SUM(d.valor_despesas) FILTER(WHERE (d.ano || d.trimestre) = (SELECT periodo_final FROM limites_temporais)), 0) AS valor_final
	FROM despesas_consolidadas AS d
	GROUP BY d.registro_operadora
)
SELECT 
    -- Faz o cálculo do crescimento percentual
	o.razao_social,
	soma.valor_inicial,
	soma.valor_final,
    ROUND(((soma.valor_final - soma.valor_inicial)/soma.valor_inicial) * 100, 2) AS crescimento_percentual
FROM somas_trimestres_analisados AS soma
JOIN operadoras AS o ON soma.registro_operadora = o.registro_operadora
WHERE soma.valor_inicial > 0 AND soma.valor_final > 0
ORDER BY 
	crescimento_percentual DESC
LIMIT 5;