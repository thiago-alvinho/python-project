import pandas as pd
import os
import csv
import zipfile
import warnings
import re

warnings.filterwarnings("ignore")

# Caminhos utilizados
BASE_DIR = os.getenv("BASE_DATA_DIR", "data")
DIRETORIO_ENTRADA = os.path.join(BASE_DIR, "downloads_ans")
ARQUIVO_INTERMEDIARIO = os.path.join(BASE_DIR, "data_teste_consolidado_temp.csv")
ARQUIVO_FINAL_ZIP = os.path.join(BASE_DIR, "consolidado_despesas.zip")

# Regex para pegar somente as despesas com assunto "Despesas com Eventos / Sinistros ..."
REGEX_PALAVRAS_CHAVE = r"despesas? com eventos?|despesas? com sinistros?|eventos? \/ sinistros?"

# Possíveis nomes de coluna que pode haver no documento e nome específico para substituir
MAPA_COLUNAS = {
    
    'REG_ANS': 'REG_ANS',
    'CD_OPERADORA': 'REG_ANS',
    
    'DT_REGISTRO': 'DATA',
    'DATA': 'DATA',
    
    'VL_SALDO_FINAL': 'ValorDespesas',
    'VALOR_SALDO_FINAL': 'ValorDespesas',
    'SALDO_FINAL': 'ValorDespesas',
    
    'VALOR': 'ValorDespesas',
    'VL_MOVIMENTO': 'ValorDespesas',
    
    'DESCRICAO': 'DESC',
    'NM_CONTA': 'DESC',
    'CD_CONTA_CONTABIL': 'CONTA'
}

# Detectar separador do documento
def detectar_separador(caminho_arquivo):
    try:
        with open(caminho_arquivo, 'r', encoding='latin1', errors='ignore') as f:
            sample = f.read(2048)
            if ';' in sample: return ';'
            sniffer = csv.Sniffer()
            return sniffer.sniff(sample).delimiter
    except:
        return ';'

# Função para pegar ano e trimestre do nome dos diretórios caso a despesa esteja com a data inválida
def extrair_data_do_caminho(caminho_arquivo):
    try:
        partes = caminho_arquivo.split(os.sep)
        for parte in partes:
            if re.match(r"^\d{4}$", parte):
                ano = int(parte)
                idx_ano = partes.index(parte)
                if idx_ano + 1 < len(partes):
                    trim_sujo = partes[idx_ano+1]
                    trim_limpo = trim_sujo.lower().replace('t', '').strip()
                    if trim_limpo.isdigit():
                        return ano, f"{trim_limpo}T"
        return None, None
    except:
        return None, None

# Função para carregar arquivo pensando nas possíveis diferentes extensões
def carregar_arquivo(caminho):
    ext = caminho.lower().split('.')[-1]
    try:
        if ext in ['csv', 'txt']:
            sep = detectar_separador(caminho)
            df = pd.read_csv(caminho, sep=sep, encoding='latin1', on_bad_lines='skip')
        elif ext in ['xlsx', 'xls']:
            df = pd.read_excel(caminho)
        else:
            return None
        return df
    except Exception as e:
        print(f"   [X] Erro leitura {os.path.basename(caminho)}: {e}")
        return None

# Função para normalizar a tabela, filtar apenas as despesas que são referentes a
# 'Despesas com Eventos / Sinistros' e criar a coluna de despesas suspeitas
def normalizar_e_processar(df, caminho_arquivo):
    
    df.columns = [c.strip().upper() for c in df.columns]
    
    df.rename(columns={k.upper(): v for k, v in MAPA_COLUNAS.items()}, inplace=True)

    if 'ValorDespesas' not in df.columns:
        return None

    if 'DESC' in df.columns:
        filtro = df['DESC'].astype(str).str.contains(REGEX_PALAVRAS_CHAVE, case=False, regex=True, na=False)
        df = df[filtro]
    else:
        return None

    if df.empty:
        return None

    if 'DATA' in df.columns:
        try:
            df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
            df['Ano'] = df['DATA'].dt.year
            df['Trimestre'] = ((df['DATA'].dt.month - 1) // 3 + 1).astype(str) + "T"
        except:
            df['Ano'] = None
    
    # Caso não consiga extrair a data dos dados, extrai do nome do diretorio
    if 'Ano' not in df.columns or df['Ano'].isnull().all():
        ano_pasta, trim_pasta = extrair_data_do_caminho(caminho_arquivo)
        if ano_pasta:
            df['Ano'] = ano_pasta
            df['Trimestre'] = trim_pasta

    # Caso o nome da coluna não seja 'REG_ANS' tenta achar por outros ois 'COD' ou 'CD_'
    if 'REG_ANS' not in df.columns:
        possiveis = [c for c in df.columns if 'COD' in c or 'CD_' in c]
        if possiveis:
            df.rename(columns={possiveis[0]: 'REG_ANS'}, inplace=True)
        else:
            return None

    # Colocar o valor no padrão US
    col_valor = df['ValorDespesas'].astype(str)
    
    if col_valor.str.contains(',').any():
        col_valor = col_valor.str.replace('.', '', regex=False).str.replace(',', '.')
    
    df['ValorDespesas'] = pd.to_numeric(col_valor, errors='coerce')
    
    # Cria a flag de Despesas Suspeitas
    # Se ValorDespesas for <= 0 ou NaN (fillna(0)), marca como True
    df['DespesasSuspeitas'] = df['ValorDespesas'].fillna(0) <= 0

    cols_finais = ['REG_ANS', 'Trimestre', 'Ano', 'ValorDespesas', 'DespesasSuspeitas']
    
    return df[cols_finais]

# Função principal
def processar_tudo():
    print(f"--- Iniciando Consolidação ---")
    
    if os.path.exists(ARQUIVO_INTERMEDIARIO): os.remove(ARQUIVO_INTERMEDIARIO)
    
    primeiro = True
    total_linhas = 0

    for root, dirs, files in os.walk(DIRETORIO_ENTRADA):
        for file in files:
            if not file.lower().endswith(('csv', 'txt', 'xlsx')):
                continue

            caminho = os.path.join(root, file)
            print(f" > Lendo: {file}...", end='\r')

            df = carregar_arquivo(caminho)
            
            if df is not None:
                df_final = normalizar_e_processar(df, caminho)

                if df_final is not None and not df_final.empty:
                    qtd = len(df_final)
                    print(f"   [V] {qtd} registros consolidados de: {file}")
                    
                    modo = 'w' if primeiro else 'a'
                    header = primeiro
                    df_final.to_csv(ARQUIVO_INTERMEDIARIO, mode=modo, header=header, sep=';', index=False, encoding='utf-8')
                    
                    primeiro = False
                    total_linhas += qtd

    if total_linhas > 0:
        print(f"\n\nSucesso! {total_linhas} linhas consolidadas.")
        print(f"Gerando arquivo final: {ARQUIVO_FINAL_ZIP}")
        
        with zipfile.ZipFile(ARQUIVO_FINAL_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(ARQUIVO_INTERMEDIARIO, arcname='consolidado_despesas.csv')
        
        os.remove(ARQUIVO_INTERMEDIARIO)
        print("Processo concluído.")
    else:
        print("\n[Aviso] Nenhum dado encontrado. Verifique se os arquivos foram baixados corretamente.")

if __name__ == "__main__":
    processar_tudo()