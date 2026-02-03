# python-project

## Como executar?

### Necessário possuir docker instalado

1. Clone o repositório.
2. No diretório python-project execute o comando: docker compose up -d --build
3. A aplicação ficará disponível em localhost:3001.
4. Caso desejado, a api pode ser acessada por localhost:8000/docs, onde poderão ser vistas as rotas disponíveis.
5. Caso desejado, há como acessar o banco através do pgAdmin (Interessante para testar as queries analíticas solicitadas) em localhost:15432/

OBS: Os serviços podem demorar um pouco para iniciar e serem acessíveis nos links

Login pgAdmin: thiago_silva.9@hotmail.com senha: PgAdmin2018!

Conecte ao servidor:

(GENERAL)
Name: (O que preferir)

(CONNECTION)
Host name/address: db
Maintenance database: ans_db
Username: postgres
senha: Postgres2018!

### Arquivos solicitados

1. Arquivos .zip estão em /data
2. Script sql que estrutura o banco está em /healthops-app/backend/sql
3. Queries analíticas estão em /queries_analiticas


## Fluxo de execução
1. O serviço etl-scripts executa o código main.py que está dentro da pasta data_scripts. O main.py será o responsável por chamar a função main dos códigos desse diretório. 

### Resultado dessa etapa
Arquivo /data que possui os seguintes arquivos: 
/downloads_ans (possui os arquivos que foram baixados da url fornecida).
consolidado_despesas.zip e Teste_Thiago_Alves_da_Silva.zip.


2. O serviço db, que fica esperando até que o etl-scripts termine de executar, irá iniciar o banco PostgreSQL, executando o script sql que está localizado em /healthops-app/backend/sql. Os csv's utilizados para alimentar o banco estão em /csv.
3. O serviço backend irá iniciar a api(FastAPI) que irá fornecer os dados para o frontend.
4. Por fim, o serviço frontend inicia. 

## Decisões Técnicas

### 1.2. Processamento de Arquivos
A abordagem incremental foi escolhida para garantir a escalabilidade do processamento, mantendo o consumo de memória (RAM) baixo e constante, independente do volume total de dados. Além de evitar o uso de Swap, essa estratégia aumenta a resiliência da aplicação: caso ocorra uma falha durante a execução, os arquivos já processados estarão salvos, não sendo necessário reiniciar todo o fluxo do zero.

### Observação
Foi considerado que o interesse é só de processar os dados com assunto "Despesas com Eventos / Sinistros * ". Portanto o código foi feito para selecionar somente essas linhas, porém, isso é facilmente reversível, caso desejado, e tudo continuará funcionando normalmente.


### 1.3 Consolidação e Análise de Inconsistências

#### CNPJ E Razão Social
Tendo em vista que os arquivos contidos em demonstrações contábeis não possuem CNPJ e Razão Social (Apenas número de registro na ANS), as operações e decisões que seriam tomadas em relação a esses dois campos nessa etapa serão deixadas para a próxima etapa, onde realizarei um join das despesas consolidadas com as operadoras de plano de saúde ativa e, dessa forma, terei as informações solicitadas.

#### Valores zerados ou negativos
Valores zerados ou negativos serão marcados como suspeitos para posterior análise, para que seja chegado a uma conclusão do porquê esses valores estão errados. Para isso, será acrescentada uma coluna 'DespesasSuspeitas' no csv consolidado_despesas, indicando uma despesa suspeita com o valor 'TRUE'

#### Trimestres com formato de data inconsistentes
Esses casos serão corrigidos da seguinte forma:
Como ao extrair os arquivos da URL fornecida foi criado um diretório para cada ano extraído (Nomeado com o ano correspondente) e um diretório para cada trimestre (Nomeado com o trimestre correspondente) dentro dos seus respectivos anos, esses nomes de diretório serão utilizados para montar a data da despesa com a data inconsistente, utilizando a biblioteca "os" para essas operações.

### 2.1. Validação de Dados com Estratégias Diferentes

#### Estratégia adotada

Decidi por não excluir despesas que não passassem pelas validações de CNPJ, Razão social e saldo. Isso porque estamos lidando com despesas financeiras e caso haja alguma inconsistência nesses campos, é necessário que haja uma verificação nessa informação. Portanto, irei adicionar 3 colunas ("FLAG_CNPJ_INVALIDO", "FLAG_RAZAO_SOCIAL_INVALIDA" e "FLAG_VALOR_INVALIDO") no relatório final que será um csv separado das despesas agregadas, cada coluna dessa será uma flag para cada uma dessas verificações e, o valor "TRUE" representa que a despesa não passou na respectiva validação. Além disso, essas despesas não entrarão nos cálculos estatísticos.

##### Os prós
Não perder a informação de uma despesa registrada e marcá-la para uma posterior análise.

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
O JOIN será mais rápido pois não será feito em partes, diminuindo a quantidade de acessos à memória secundária.

#### Contra
Não é a melhor solução para escalabilidade. Caso o arquivo de despesas se torne muito grande, pode consumir a memória RAM. Porém, isso será um pouco difícil de acontecer por dois motivos:
1. As despesas consolidadas vêm apenas dos 3 trimestres mais recentes
2. As despesas consolidadas são despesas filtradas pelo assunto "Despesas com Eventos / Sinistros"

#### Conclusão
Levando em consideração esse cenário específico, fazer a operação de JOIN com as duas tabelas em memória foi considerado a melhor opção.

### 2.3. Agregação com Múltiplas Estratégias

#### Ordenação
A ordenação utilizada foi a quicksort, que possui complexidade O(nlogn), e será realizada com todos os dados em memória RAM, levando em consideração as justificativas anteriores de que os dados ocupam pouco espaço de memória.

### 3 Teste de banco de dados e análise

#### Normalização

##### Escolha
A escolha foi manter as tabelas normalizadas.

##### Motivo
A tabela desnormalizada com todos os dados em uma única tabela teria as seguintes desvantagens:
1. Aumento significativo do espaço de armazenamento utilizado, pois informações particulares de cada operadora, como seu endereço, seria repetido em todas as suas despesas.
2. A operação de UPDATE seria cara, pois para, por exemplo, mudar o representante de uma empresa, teria que atualizar essa informação em todas as ocorrências da empresa.

A vantagem que essa abordagem tem é diminuir a quantidade de joins, que é uma operação cara, porém, dá para diminuir de forma significativa esse custo utilizando os índices.

#### Tratamento de inconsistência nos dados ao importar do csv
Decidi por importar os dados em tabelas temporárias com campos do tipo TEXT para tratamento antes da inserção no banco. Utilizei a função "LPAD()" (para preencher registro de operadora, cnp e cep com zeros a esquerda), "NULLIF()" (Para preencher com NULL campos que venham vazios) e REPLACE() (para colocar valores monetários no formato US).

Além disso, utilizei a cláusula WHERE para filtar despesas com valor menor ou igual a zero.

#### Tipo de dados

##### Escolhas
Decimal e DATE

##### Motivo
Decimal pois é mais preciso para cálculos financeiros. Integer não conseguiríamos ter valores com centavos e float não é preciso para frações exatas.

Date pois string tornaria operações no banco como ORDER BY mais custosas e TIMESTAMP não é necessário porque não usaremos hora.

#### Queries analíticas
Estão localizadas em /queries_analiticas e podem ser testadas no pgAdmin em localhost:15432/

##### 5 operadoras com maior crescimento percentual entre o primeiro e último trimestre analisado
Fórmula do crescimento percentual: ((gasto final - gasto inicial) / (gasto inicial)) * 100

Para operadoras que não possuem gastos no primeiro trimestre (gasto 0), acarretaria em divisão por 0, o que não é possível calcular. A princípio, considerei que essas operadoras não tiveram gastos nesse trimestre e portanto, atribui os seus crescimentos percentuais como infinito. Porém, isso resultou nessas operadoras tomando conta das primeiras posições da tabela. Isso me fez considerar outro cenário e creio que o mais provável seja que elas são operadoras novas e não atuavam naquele trimestre. Tendo isso em mente, irei desconsiderá-las nesses cálculos.

Para operadoras que não possuem gastos no último trimestre analisado, resultaria em crescimento percentual negativo de 100%. Elas seriam as últimas nessa tabela e como queremos as 5 com maiores, eu irei desconsiderá-las.

Foi utilizada a função COALESCE() para não utilizar valores nulos.

##### Despesas acima da média geral

###### Trade-off técnico
Optei por utilizar CTE(Common Table Expression) para quebrar os cálculos em partes menores, isso proporciona:
Performance - O cálculo é realizado apenas uma vez, e esse resultado é reutilizado posteriormente.
Legibilidade - Não há estruturas aninhadas e a consulta é dividida em partes menores.
Manutenibilidade - Basta alterar um trecho do script que as alterações refletem nas outras partes que o estão utilizando.

### Escolha do framework
Optei por utilizar o FastAPI por apresentar um maior desempenho, suporte nativo a assincronismo, validação de dados com Pydantic e documentação automática.

### Estratégia de paginação
Optei por utilizar o Offset-based levando em consideração que o volume de dados é pequeno, tendo em vista que selecionamos apenas os 3 últimos trimestres e filtramos os gastos para apenas "Despesas com Eventos / Sinistros *" e a frequência de atualização do banco é baixa.

### Cache vs Queries diretas
A solução técnica escolhida é o cache, visto que os dados da ANS são históricos e trimestrais. Por esse motivo, não é necessário atualizar o cálculo desses dados a todo momento. A utilização do cache evitará esses cálculos desnecessários.

### Estrutura de resposta da API
Optei por fornecer os dados + metadados (total, page, limit) para o frontend para que ele seja capaz de mostrar para o usuário o total de páginas disponíveis, e desativar os botões de próximo/anterior quando for o caso.

### Estratégia de busca/filtro
Optei pela busca no servidor, tendo em vista que por conta da estratégia de paginação, o cliente só possui os 10 registros da página atual.

### Gerenciamento de estado
Optei por utilizar o pinia.

Complexidade da Aplicação: O projeto possui complexidade média, onde componentes distintos (Barra de Busca, Tabela e Paginação) precisam acessar e modificar os mesmos dados simultaneamente. O uso de props simples tornaria o código confuso e difícil de manter ("Prop Drilling").

Necessidade de Compartilhamento: A principal razão foi garantir a continuidade da navegação. É necessário que o filtro de busca e o número da página sejam preservados na memória global quando o usuário navega para a tela de "Detalhes" e clica em "Voltar". Sem o gerenciamento de estado global, esses dados seriam perdidos e a lista resetaria a cada troca de tela.


### Tratamento de erros e loading
Loading: Controlado por uma variável booleana (loading) dentro de blocos try/catch/finally. Enquanto a requisição ocorre, a interface exibe um spinner de carregamento e oculta a tabela de dados.

Dados Vazios: O sistema verifica se a lista retornada está vazia (length === 0). Se estiver, exibe uma mensagem amigável (ex: "Nenhuma despesa registrada") em vez de uma tabela em branco.

Tratamento de erros:
Backend: Retorna códigos HTTP específicos, como 404 quando uma operadora não é encontrada.
Frontend: Intercepta falhas com try/catch. Para erros críticos na tela de detalhes, usa um alert() nativo; para a listagem geral, registra o erro no console e no estado da store.