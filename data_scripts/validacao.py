import pandas as pd
import requests
from bs4 import BeautifulSoup
import zipfile
import os
import glob
import warnings
import io
import re
import numpy as np

# --- CONFIGURAÇÃO ---
URL_DIRETORIO_ANS = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/"
PASTA_CADASTRO = "downloads_ans/cadastral"
ARQUIVO_DESPESAS_ZIP = "consolidado_despesas.zip"

# Arquivos de Saída
ARQUIVO_ANALITICO = "relatorio_final_validado.csv"
ARQUIVO_AGREGADO = "despesas_agregadas.csv"
NOME_ZIP_FINAL = "Teste_Thiago_Alves_da_Silva.zip"

COLUNA_ALVO_REGISTRO = "REGISTRO_OPERADORA"

warnings.filterwarnings("ignore")
requests.packages.urllib3.disable_warnings()

# ==============================================================================
# UTILITÁRIOS
# ==============================================================================

def detectar_separador(caminho_ou_buffer, is_buffer=False):
    try:
        if is_buffer:
            sample = caminho_ou_buffer.read(2048)
            caminho_ou_buffer.seek(0)
        else:
            with open(caminho_ou_buffer, 'r', encoding='latin1', errors='ignore') as f:
                sample = f.read(2048)
        
        if ';' in sample: return ';'
        if ',' in sample: return ','
        return ';'
    except:
        return ';'

def limpar_e_converter_chave(serie):
    s = serie.astype(str).str.replace(r'\D', '', regex=True)
    return pd.to_numeric(s, errors='coerce').fillna(0).astype(int)

# ==============================================================================
# MÓDULO DE ANÁLISE E AGREGAÇÃO
# ==============================================================================
def gerar_agregacao_estatistica(df):
    print("8. [Analytics] Calculando estatísticas por Operadora/UF...")
    
    df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce').fillna(0)
    
    df_agg = df.groupby(['Razao_Social', 'UF'])['ValorDespesas'].agg(
        Valor_Total='sum',
        Media_Trimestral='mean',
        Desvio_Padrao='std'
    ).reset_index()

    df_agg['Desvio_Padrao'].fillna(0, inplace=True)
    df_agg.sort_values(by='Valor_Total', ascending=False, inplace=True)
    
    cols = ['Valor_Total', 'Media_Trimestral', 'Desvio_Padrao']
    df_agg[cols] = df_agg[cols].round(2)

    return df_agg

def compactar_entrega_final():
    print(f"9. [Entrega] Gerando arquivo final: {NOME_ZIP_FINAL}...")
    with zipfile.ZipFile(NOME_ZIP_FINAL, 'w', zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(ARQUIVO_AGREGADO): zf.write(ARQUIVO_AGREGADO)
        if os.path.exists(ARQUIVO_ANALITICO): zf.write(ARQUIVO_ANALITICO)
            
    if os.path.exists(ARQUIVO_AGREGADO): os.remove(ARQUIVO_AGREGADO)
    if os.path.exists(ARQUIVO_ANALITICO): os.remove(ARQUIVO_ANALITICO)
    print(f"   -> Sucesso! Arquivo ZIP gerado.")

# ==============================================================================
# VALIDAÇÃO
# ==============================================================================
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
    print("6. [Qualidade] Aplicando validações...")
    df['FLAG_CNPJ_VALIDO'] = df['CNPJ'].apply(lambda x: validar_digitos_cnpj(x) if "NAO" not in str(x) else False)
    df['FLAG_RAZAO_SOCIAL_VALIDA'] = df['Razao_Social'].apply(lambda x: str(x).strip() != '' and "NAO LOCALIZADA" not in str(x))
    df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce').fillna(0)
    df['FLAG_VALOR_POSITIVO'] = df['ValorDespesas'] > 0
    return df

# ==============================================================================
# CRAWLER & ETL
# ==============================================================================
def baixar_cadastro():
    print("1. [Crawler] Buscando arquivo de Cadastro...")
    if not os.path.exists(PASTA_CADASTRO): os.makedirs(PASTA_CADASTRO)
    try:
        url_base = URL_DIRETORIO_ANS
        resp = requests.get(url_base, verify=False, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        link = next((l.get('href') for l in soup.find_all('a') if l.get('href', '').lower().endswith('.csv')), None)
        if not link: return None
        if not link.startswith('http'): link = url_base + link
        
        caminho = os.path.join(PASTA_CADASTRO, link.split('/')[-1])
        # Otimização: Se já existe, não baixa de novo (comente se quiser forçar)
        if os.path.exists(caminho): return caminho

        print(f"   -> Baixando: {link}")
        with requests.get(link, stream=True, verify=False) as r:
            with open(caminho, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
        return caminho
    except: return None

def executar_pipeline():
    # 1. Carga
    caminho_cad = baixar_cadastro()
    if not caminho_cad:
        files = glob.glob(os.path.join(PASTA_CADASTRO, "*.csv"))
        caminho_cad = files[0] if files else None

    if not caminho_cad:
        print("Erro Fatal: Nenhum arquivo de cadastro encontrado.")
        return

    print("2. [Leitura] Carregando tabelas...")
    try:
        with zipfile.ZipFile(ARQUIVO_DESPESAS_ZIP, 'r') as z:
            with z.open(z.namelist()[0]) as f:
                texto = io.TextIOWrapper(f, encoding='utf-8')
                sep = detecting_sep = detectar_separador(texto, is_buffer=True)
                df_despesas = pd.read_csv(f, sep=sep, encoding='utf-8')
    except Exception as e:
        print(f"Erro despesas: {e}"); return

    try:
        sep_cad = detectar_separador(caminho_cad)
        df_cadastro = pd.read_csv(caminho_cad, sep=sep_cad, encoding='latin1', on_bad_lines='skip', dtype=str)
    except Exception as e:
        print(f"Erro cadastro: {e}"); return

    # 2. Mapeamento
    print("3. [Tratamento] Mapeando colunas...")
    df_cadastro.columns = [c.strip().upper() for c in df_cadastro.columns]
    
    col_reg = COLUNA_ALVO_REGISTRO if COLUNA_ALVO_REGISTRO in df_cadastro.columns else \
              next((c for c in df_cadastro.columns if 'DATA' not in c and 'REGISTRO' in c and 'OPERADORA' in c), None)

    if not col_reg:
        print(f"Erro: Coluna '{COLUNA_ALVO_REGISTRO}' não encontrada."); return

    col_uf = next((c for c in df_cadastro.columns if c == 'UF' or 'ESTADO' in c or 'SIGLA' in c), None)
    
    df_despesas['KEY_JOIN'] = limpar_e_converter_chave(df_despesas['REG_ANS'])
    df_cadastro['KEY_JOIN'] = limpar_e_converter_chave(df_cadastro[col_reg])
    
    print("4. [Limpeza] Deduplicando cadastro...")
    df_cadastro.drop_duplicates(subset=['KEY_JOIN'], keep='first', inplace=True)

    # 3. Join
    print("5. [Join] Cruzando tabelas...")
    df_final = pd.merge(df_despesas, df_cadastro, on='KEY_JOIN', how='left')

    # Renomeação
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

    # 4. Validação
    df_final = aplicar_validacoes(df_final)

    # ---------------------------------------------------------
    # CORREÇÃO: FILTRAGEM ESTRITA DAS COLUNAS (O QUE FALTOU)
    # ---------------------------------------------------------
    print("7. [Finalização] Selecionando colunas finais...")
    colunas_desejadas = [
        'REG_ANS', 'CNPJ', 'Razao_Social', 'Modalidade', 'UF', 
        'Trimestre', 'Ano', 'ValorDespesas',
        'FLAG_CNPJ_VALIDO', 'FLAG_RAZAO_SOCIAL_VALIDA', 'FLAG_VALOR_POSITIVO'
    ]
    
    # Garante que todas existam (mesmo que vazias)
    for c in colunas_desejadas:
        if c not in df_final.columns: df_final[c] = pd.NA
            
    # APLICA O FILTRO (Remove colunas de lixo do cadastro)
    df_final = df_final[colunas_desejadas]

    # Salva Analítico
    df_final.to_csv(ARQUIVO_ANALITICO, index=False, sep=';', encoding='utf-8')

    # 5. Agregação
    df_agregado = gerar_agregacao_estatistica(df_final)
    df_agregado.to_csv(ARQUIVO_AGREGADO, index=False, sep=';', encoding='utf-8')

    # 6. Compactação
    compactar_entrega_final()

if __name__ == "__main__":
    executar_pipeline()