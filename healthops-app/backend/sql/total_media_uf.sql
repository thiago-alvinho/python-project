SELECT 
    o.uf,
    SUM(d.valor_despesas) AS despesas_totais,
    COUNT(DISTINCT o.registro_operadora) AS qtd_operadoras,
    ROUND(SUM(d.valor_despesas) / NULLIF(COUNT(DISTINCT o.registro_operadora), 0), 2) AS media_por_operadora
FROM despesas_consolidadas AS d
JOIN operadoras AS o ON d.registro_operadora = o.registro_operadora
GROUP BY o.uf
ORDER BY despesas_totais DESC
LIMIT 5;