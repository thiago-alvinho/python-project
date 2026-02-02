import pandas as pd
import requests
from bs4 import BeautifulSoup
import zipfile
import os
import glob
import warnings
import io
import re
import csv

# --- CONFIGURAÇÃO ---
BASE_DIR = os.getenv("BASE_DATA_DIR", "../data")
# Calcula o diretório pai (um nível acima de data) para salvar fora de /data
DIR_PAI = os.path.dirname(os.path.normpath(BASE_DIR))

URL_DIRETORIO_ANS = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/"
ARQUIVO_DESPESAS_ZIP = os.path.join(BASE_DIR, "consolidado_despesas.zip")

# Arquivos de Saída
ARQUIVO_ANALITICO = os.path.join(BASE_DIR, "relatorio_final_validado.csv")
ARQUIVO_AGREGADO = os.path.join(BASE_DIR, "despesas_agregadas.csv")
NOME_ZIP_FINAL = os.path.join(BASE_DIR, "Teste_Thiago_Alves_da_Silva.zip")
PASTA_CSV_EXTERNA = os.path.join(DIR_PAI, "csv")

# Coluna utilizada para o join das tabelas
COLUNA_ALVO_REGISTRO = "REGISTRO_OPERADORA"

warnings.filterwarnings("ignore")
requests.packages.urllib3.disable_warnings()

# Função para garantir que a chave utilizada para o join esteja no formato correto
def limpar_e_converter_chave(serie):
    s = serie.astype(str).str.replace(r'\D', '', regex=True)
    return pd.to_numeric(s, errors='coerce').fillna(0).astype(int)

# Função para calcular os valores estatísticos pedidos
def gerar_agregacao_estatistica(df):
    print("8. Calculando estatísticas por Operadora/UF...")
    
    df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce').fillna(0)
    
    # Cria um dataframe temporário contendo apenas despesas > 0
    # Isso remove as negativas e zeradas do cálculo de média e do arquivo final agregado
    df_positivas = df[df['ValorDespesas'] > 0].copy()
    
    if df_positivas.empty:
        print("   Aviso: Nenhuma despesa positiva encontrada para agregação.")
        return pd.DataFrame(columns=['Razao_Social', 'UF', 'Valor_Total', 'Media_Trimestral', 'Desvio_Padrao'])

    # Soma do gasto por trimestre
    df_trimestral = df_positivas.groupby(['Razao_Social', 'UF', 'Ano', 'Trimestre'])['ValorDespesas'].sum().reset_index()

    # Valor total por operadora, Média trimestral por operadora e desvio padrão
    df_agg = df_trimestral.groupby(['Razao_Social', 'UF'])['ValorDespesas'].agg(
        Valor_Total='sum',
        Media_Trimestral='mean',
        Desvio_Padrao='std'
    ).reset_index()

    df_agg['Desvio_Padrao'].fillna(0, inplace=True)

    # Ordenação quicksort em memória
    df_agg.sort_values(by='Valor_Total', ascending=False, inplace=True)
    
    cols = ['Valor_Total', 'Media_Trimestral', 'Desvio_Padrao']
    df_agg[cols] = df_agg[cols].round(2)

    return df_agg

def compactar_entrega_final():
    print(f"9. Gerando arquivo final: {NOME_ZIP_FINAL}...")
    
    with zipfile.ZipFile(NOME_ZIP_FINAL, 'w', zipfile.ZIP_DEFLATED) as zf:

        if os.path.exists(ARQUIVO_AGREGADO):
            zf.write(ARQUIVO_AGREGADO, arcname=os.path.basename(ARQUIVO_AGREGADO))
        
        if os.path.exists(ARQUIVO_ANALITICO):
            zf.write(ARQUIVO_ANALITICO, arcname=os.path.basename(ARQUIVO_ANALITICO))
            
    # Limpeza dos arquivos temporários
    if os.path.exists(ARQUIVO_AGREGADO): os.remove(ARQUIVO_AGREGADO)
    if os.path.exists(ARQUIVO_ANALITICO): os.remove(ARQUIVO_ANALITICO)
    
    print(f"   -> Sucesso! Arquivo ZIP gerado com sucesso.")

# Função para validação do cnpj
def validar_digitos_cnpj(cnpj):
    cnpj = re.sub(r'\D', '', str(cnpj)).zfill(14)
    if len(cnpj) != 14 or len(set(cnpj)) == 1: return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma1 = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    d1 = 0 if (soma1 % 11) < 2 else 11 - (soma1 % 11)
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma2 = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    d2 = 0 if (soma2 % 11) < 2 else 11 - (soma2 % 11)
    return str(d1) == cnpj[12] and str(d2) == cnpj[13]

def aplicar_validacoes(df):
    print("6. Calculando flags de inconsistência...")
    
    # 1. Flag CNPJ Inválido (True = Erro)
    df['FLAG_CNPJ_INVALIDO'] = df['CNPJ'].apply(
        lambda x: True if "NAO" in str(x) else (not validar_digitos_cnpj(x))
    )

    # 2. Flag Razão Social Inválida (True = Erro)
    df['FLAG_RAZAO_SOCIAL_INVALIDA'] = df['Razao_Social'].apply(
        lambda x: str(x).strip() == '' or "NAO LOCALIZADA" in str(x)
    )

    # 3. Flag Valor Inválido (True = Erro)
    if 'FLAG_VALOR_INVALIDO' not in df.columns:
         df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce').fillna(0)
         df['FLAG_VALOR_INVALIDO'] = df['ValorDespesas'] <= 0
    else:
         df['FLAG_VALOR_INVALIDO'] = df['FLAG_VALOR_INVALIDO'].astype(bool)
    
    return df

def baixar_cadastro():
    print("1. Buscando arquivo de Cadastro...")
    if not os.path.exists(PASTA_CSV_EXTERNA): os.makedirs(PASTA_CSV_EXTERNA)
    try:
        url_base = URL_DIRETORIO_ANS
        resp = requests.get(url_base, verify=False, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        link = next((l.get('href') for l in soup.find_all('a') if l.get('href', '').lower().endswith('.csv')), None)
        if not link: return None
        if not link.startswith('http'): link = url_base + link
        
        caminho = os.path.join(PASTA_CSV_EXTERNA, link.split('/')[-1])
        if os.path.exists(caminho): return caminho

        print(f"   -> Baixando: {link}")
        with requests.get(link, stream=True, verify=False) as r:
            with open(caminho, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
        return caminho
    except: return None

def executar_pipeline():
    # Cria a pasta CSV externa se não existir
    if not os.path.exists(PASTA_CSV_EXTERNA): os.makedirs(PASTA_CSV_EXTERNA)

    # Baixa o cadastro
    caminho_cad = baixar_cadastro()
    if not caminho_cad:
        files = glob.glob(os.path.join(PASTA_CSV_EXTERNA, "*.csv"))
        caminho_cad = files[0] if files else None

    if not caminho_cad:
        print("Erro Fatal: Nenhum arquivo de cadastro encontrado.")
        return

    print("2. Carregando tabelas...")
    try:
        with zipfile.ZipFile(ARQUIVO_DESPESAS_ZIP, 'r') as z:
            with z.open(z.namelist()[0]) as f:
                texto = io.TextIOWrapper(f, encoding='utf-8')
                df_despesas = pd.read_csv(f, sep=';', encoding='utf-8')
                # Salva o dataframe de despesas bruto na pasta CSV externa, fora de /data
                df_despesas.to_csv(os.path.join(PASTA_CSV_EXTERNA, "consolidado_despesas.csv"), index=False, sep=';', encoding='utf-8', quoting=csv.QUOTE_NONNUMERIC, quotechar='"')

    except Exception as e:
        print(f"Erro despesas: {e}"); return

    try:
        df_cadastro = pd.read_csv(caminho_cad, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
    except Exception as e:
        print(f"Erro cadastro: {e}"); return

    # Mapeamento das colunas 
    print("3. Mapeando colunas...")
    df_cadastro.columns = [c.strip().upper() for c in df_cadastro.columns]
    
    col_reg = COLUNA_ALVO_REGISTRO if COLUNA_ALVO_REGISTRO in df_cadastro.columns else \
              next((c for c in df_cadastro.columns if 'DATA' not in c and 'REGISTRO' in c and 'OPERADORA' in c), None)

    if not col_reg:
        print(f"Erro: Coluna '{COLUNA_ALVO_REGISTRO}' não encontrada."); return

    col_uf = next((c for c in df_cadastro.columns if c == 'UF' or 'ESTADO' in c or 'SIGLA' in c), None)
    
    # Limpeza da chave que será utilizaada para o join
    df_despesas['REG_ANS'] = limpar_e_converter_chave(df_despesas['REG_ANS'])
    df_cadastro[col_reg] = limpar_e_converter_chave(df_cadastro[col_reg])
    
    # Caso possua registro de operadora duplicado, irá descartar um deles
    print("4. Deduplicando cadastro...")
    df_cadastro.drop_duplicates(subset=[col_reg], keep='first', inplace=True)

    print("5. Cruzando tabelas...")
    df_final = df_despesas.join(df_cadastro.set_index(COLUNA_ALVO_REGISTRO), on="REG_ANS")

    renomear = {}
    col_cnpj = next((c for c in df_cadastro.columns if 'CNPJ' in c), None)
    col_razao = next((c for c in df_cadastro.columns if 'RAZAO' in c or 'NOME' in c), None)
    col_mod = next((c for c in df_cadastro.columns if 'MODALIDADE' in c), None)

    if col_cnpj: renomear[col_cnpj] = 'CNPJ'
    if col_razao: renomear[col_razao] = 'Razao_Social'
    if col_mod: renomear[col_mod] = 'Modalidade'
    if col_uf: renomear[col_uf] = 'UF'
    
    df_final.rename(columns=renomear, inplace=True)
    
    df_final['Razao_Social'].fillna("RAZAO SOCIAL NAO LOCALIZADA", inplace=True)
    df_final['UF'].fillna("INDETERMINADO", inplace=True)
    df_final['CNPJ'].fillna("NAO ENCONTRADO", inplace=True)

    # Cria as flags
    df_final = aplicar_validacoes(df_final)

    print("7. Selecionando colunas finais...")
    colunas_desejadas = [
        'REG_ANS', 'CNPJ', 'Razao_Social', 'Modalidade', 'UF', 
        'Trimestre', 'Ano', 'ValorDespesas',
        'FLAG_CNPJ_INVALIDO', 'FLAG_RAZAO_SOCIAL_INVALIDA', 'FLAG_VALOR_INVALIDO'
    ]
    
    for c in colunas_desejadas:
        if c not in df_final.columns: df_final[c] = pd.NA
            
    df_final = df_final[colunas_desejadas]
    
    # Salva o relatório final
    df_final.to_csv(ARQUIVO_ANALITICO, index=False, sep=';', encoding='utf-8', quoting=csv.QUOTE_NONNUMERIC, quotechar='"')

    # Gera e salva a agregação
    df_agregado = gerar_agregacao_estatistica(df_final)
    df_agregado.to_csv(ARQUIVO_AGREGADO, index=False, sep=';', encoding='utf-8', quoting=csv.QUOTE_NONNUMERIC, quotechar='"')
    
    # Salva o arquivo de despesas agregadas na pasta CSV externa
    df_agregado.to_csv(os.path.join(PASTA_CSV_EXTERNA, "despesas_agregadas.csv"), index=False, sep=';', encoding='utf-8', quoting=csv.QUOTE_NONNUMERIC, quotechar='"')

    # Compacta ambos no ZIP final
    compactar_entrega_final()

if __name__ == "__main__":
    executar_pipeline()