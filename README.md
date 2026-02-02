# python-project

## Como executar?

### Necessário possuir docker instalado

1. Clone o repositório.
2. No diretório projeto-estagio execute o comando: docker compose up -d --build.
3. A aplicação ficará disponível em localhost:3001.
4. Caso desejado, a api pode ser acessada por localhost:8000/docs, onde poderá ser visto as rotas disponíveis.
5. Caso desejado, há como acessar o banco através do pgAdmin em localhost:15432/
login: thiago_silva.9@hotmail.com senha: PgAdmin2018!
Conecte ao servidor:
Host name/address: db
Maintenance database: ans_db
Username: postgres
senha: Postgres2018!

### Arquivos solicitados

1. Arquivos .zip estão em /data
2. Scripts sql estão em /healthops-app/backend/sql


### Fluxo de execução
1. O serviço etl-scripts executa o código main.py que está dentro da pasta data_scripts. O main.py será o responsável por chamar a função main dos códigos desse diretório. 

#### Resultado dessa etapa
Arquivo /data que possui os seguintes arquivos:
1. /downloads_ans (possui os arquivos que foram baixados da url fornecida).
2. consolidado_despesas.zip e Teste_Thiago_Alves_da_Silva.zip.
#### -----------------------------------------------------------------------

2. O serviço db, que fica esperando até que o etl-scripts termine de executar, irá iniciar o banco PostgreSQL, executando o script sql que está localizado em /healthops-app/backend/sql. Os csv's utilizados para alimentar o banco estão em /csv.

3. O serviço backend irá iniciar a api(FastAPI) que irá fornecer os dados para o frontend.
4. Por fim, o serviço frontend inicia. 

## Decisões Técnicas

### 1.2. Processamento de Arquivos

A abordagem incremental foi escolhida para garantir a escalabilidade do processamento, mantendo o consumo de memória (RAM) baixo e constante, independente do volume total de dados. Além de evitar o uso de Swap, essa estratégia aumenta a resiliência da aplicação: caso ocorra uma falha durante a execução, os arquivos já processados estarão salvos, não sendo necessário reiniciar todo o fluxo do zero.

### 1.3 Consolidação e Análise de Inconsistências

#### CNPJ E Razão Social
Tendo em vista que os arquivos contidos em demonstrações contábeis não possuem CNPJ e Razão Social (Apenas número de registro na ANS), as operações e decisões que seriam tomadas em relação a esses dois campos nessa etapa será deixada para a próxima etapa, onde realizarei um join das despesas consolidadas com as operadoras de plano de saúde ativa e, dessa forma, terei as informações solicitadas.

#### Valores zerados ou negativos
Valores zerados ou negativos serão marcados como suspeitos para posterior análise, para que seja chegado a uma conclusão do porque esses valores estão errados. Para isso, será acrescentada uma coluna 'DespesasSuspeitas' no csv consolidado_despesas, indicando uma despesa suspeita com o valor 'TRUE'

#### Trimestres com formato de data inconsistentes
Esses casos serão corrigidos da seguinte forma:
Como ao extrair os arquivos da URL fornecida foi criado um diretório para cada ano extraído (Nomeado com o ano correspondente) e um diretório para cada trimestre (Nomeado com o trimestre correspodente) dentro dos seus respectivos anos, esses nomes de diretório serão utilizados para montar a data da despesa com a data inconsistente, utilizando a biblioteca "os" para essas operações.

### 2.1. Validação de Dados com Estratégias Diferentes

#### Estratégia adotada

Decidi por não excluir despesas que não passassem pelas validações de CNPJ, Razão social e saldo. Isso porque estamos lidando com despesas financeiras e caso haja alguma inconsistência nesses campos, é necessário que haja uma verificação nessa informação. Portanto, irei adicinar 3 colunas ("FLAG_CNPJ_INVALIDO", "FLAG_RAZAO_SOCIAL_INVALIDA" e "FLAG_VALOR_INVALIDO") no relatório final que será um csv separado das despesas agregadas, cada coluna dessa será uma flag para cada uma dessas verificações e, o valor "TRUE" representa que a despesa não passou na respectiva validação. Além disso, essas despesas não entrarão nos cálculos estatísticos.

##### Os prós
Não perder a informação de uma despesa registrada e marca-lá para uma posterior análise.

##### Os contras
Criação de uma tabela a mais relatorio_final_validado.csv e, portanto, mais gasto de memória.

### 2.2. Enriquecimento de Dados com Tratamento de Falhas

#### CNPJ com mais de um cadastro

Decidi por considerar apenas um cadastro para um CNPJ que tenha mais de um registro. Isso porque, ao realizar o JOIN, caso tenha mais de um registro para um mesmo CNPJ, essa despesa será repetida para todas essas ocorrências, criando despesas que não existiam para esse CNPJ.

#### Despesas sem match no cadastro

Decidi por manter essas despesas sem correspondente, preenchendo o campo que ficaria vazio como "NÃO ENCONTRADO". Escolhi essa decisão pois considero que é importante manter o registro das despesas, mesmo que não se tenha achado a empresa correspondente, visto que a empresa pode ter saído do status de ativa por algum motivo, e portanto não está no cadastro.

#### JOIN em memória

Levando em consideração que o arquivo de despesas consolidadas e cadastros são pequenos, decidi realizar o join em memória.

#### Prós
O JOIN será mais rápido pois não será feito em partes, diminuindo a quantidade de acessos a memória secundária.

#### Contra
Não é a melhor solução para escalabilidade. Caso o arquivo de despesas se torne muito grande, pode consumir a memória RAM. Porém, isso será um pouco difícil de acontecer por dois motivos:
1. As despesas consolidadas vem apenas dos 3 trimestres mais recentes
2. As despesas consolidadas são despesas filtradas pelo assunto "Despesas com Eventos / Sinistros"

#### Conclusão
Levando em consideração esse cenário específico, fazer a operação de JOIN com as duas tabelas em memória foi considerado a melhor opção.

### 2.3. Agregação com Múltiplas Estratégias

#### Ordenação
A ordenação utilizada foi a quicksort, que possui complexidade O(nlogn), em memória, considerando as justificativas anteriores de que os dados cabem em memória tranquilamente.

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