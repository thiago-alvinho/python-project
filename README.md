# python-project

## Decisões Técnicas

### 1.2. Processamento de Arquivos

A abordagem incremental foi escolhida para garantir a escalabilidade do processamento, mantendo o consumo de memória (RAM) baixo e constante, independente do volume total de dados. Além de evitar o uso de Swap, essa estratégia aumenta a resiliência da aplicação: caso ocorra uma falha durante a execução, os arquivos já processados estarão salvos, não sendo necessário reiniciar todo o fluxo do zero.

### 1.3 Consolidação e Análise de Inconsistências

Tendo em vista que os arquivos contidos em demonstrações contábeis não possuem CNPJ e Razão Social, as operações e decisões que seriam tomadas em relação a esses dois campos nessa etapa será deixada para a próxima etapa, onde realizarei um join das despesas consolidadas com as operadoras de plano de saúde ativa e, dessa forma, terei as informações solicitadas.

### 2.1. Validação de Dados com Estratégias Diferentes

#### Estratégia adotada

Decidi por não excluir despesas que não passassem pelas validações de CNPJ, Razão social e saldo. Isso porque estamos lidando com despesas financeiras e caso haja alguma inconsistência nesses campos, é necessário que haja uma verificação nessa informação. Portanto, irei adicinar 3 colunas ("FLAG_CNPJ_VALIDO", "FLAG_RAZAO_SOCIAL_VALIDA" e "FLAG_VALOR_POSITIVO") no relatório final, cada coluna dessa será uma flag para cada uma dessas verificações e, o valor "FALSO" representa que a despesa não passou na respectiva validação.

##### Os prós
Não perder a informação de uma despesa registrada e marca-lá para uma posterior análise.

##### Os contras
Aumento do tamanho do arquivo final.

### 2.2. Enriquecimento de Dados com Tratamento de Falhas

#### CNPJ com mais de um cadastro

Decidi por considerar apenas um cadastro para um CNPJ que tenha mais de um registro. Isso porque, ao realizar o JOIN, caso tenha mais de um registro para um mesmo CNPJ, essa despesa será repetida para todas essas ocorrências, criando despesas que não existiam para esse CNPJ.

### Despesas sem match no cadastro

Decidi por manter essas despesas sem correspondente, preenchendo o campo que ficaria vazio como "NÃO ENCONTRADO". Escolhi essa decisão pois considero que é importante manter o registro das despesas, mesmo que não se tenha achado a empresa correspondente, visto que a empresa pode ter saído do status de ativa por algum motivo, e portanto não está no cadastro.

### 3 Teste de banco de dados e análise

#### Normalização

##### Escolha
A escolha foi manter as tabelas normalizadas.

##### Motivo
A tabela desnormalizada com todos os dados em uma única tabela teria as seguintes desvantagens:
1. Aumento significativo do espaço de armazenamento utilizado, pois informações particulares de cada operadora, como seu endereço, seria repetido em todas as suas despesas.
2. A operação de UPDATE seria cara, pois para, por exemplo, mudar o representante de uma empresa, teria que atualizar essa informação em todas as ocorrências da empresa.

A vantagem que essa abordagem tem é diminuir a quantidade de joins, que é uma operação cara, porém, dá para diminuir de forma significativa esse custo utilizando os índices.

#### Tipo de dados

##### Escolhas
Decimal e DATE

##### Motivo
Decimal pois é mais preciso para cálculos financeiros. Integer não conseguiríamos ter valores com centavos e float não é preciso para frações exatas.

Date pois string tornaria operações no banco como ORDER BY mais custosas e TIMESTAMP não é necessário porque não usaremos hora.

### 4.2.3 Cache vs Queries diretas

#### Escolha
A solução técnica escolhida é o cache

#### Motivo
Os dados da ANS são históricos e trimestrais. Por esse motivo, não é necessário atualizar o cálculo desses dados a todo momento. A utilização do cache evitará esses cálculos desnecessários.