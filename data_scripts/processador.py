import pandas as pd
import os
import csv
import zipfile
import warnings
import re

# Suprime avisos do Pandas
warnings.filterwarnings("ignore")

# --- CONFIGURAÇÃO ---
DIRETORIO_ENTRADA = "downloads_ans"
ARQUIVO_INTERMEDIARIO = "consolidado_temp.csv"
ARQUIVO_FINAL_ZIP = "consolidado_despesas.zip"

# Regex para pegar singular/plural e variações de espaçamento
REGEX_PALAVRAS_CHAVE = r"despesas? com eventos?|despesas? com sinistros?|eventos? \/ sinistros?"

# --- MAPA DE NORMALIZAÇÃO ---
# Prioridade total para VL_SALDO_FINAL
MAPA_COLUNAS = {
    # Identificador
    'REG_ANS': 'REG_ANS',
    'CD_OPERADORA': 'REG_ANS',
    
    # Data
    'DT_REGISTRO': 'DATA',
    'DATA': 'DATA',
    
    # O Saldo Final, que é o acumulado oficial do período
    'VL_SALDO_FINAL': 'ValorDespesas',
    'VALOR_SALDO_FINAL': 'ValorDespesas',
    'SALDO_FINAL': 'ValorDespesas',
    
    # Fallbacks (apenas se não houver saldo final explícito)
    'VALOR': 'ValorDespesas',
    'VL_MOVIMENTO': 'ValorDespesas',
    
    # Descrição
    'DESCRICAO': 'DESC',
    'NM_CONTA': 'DESC',
    'CD_CONTA_CONTABIL': 'CONTA'
}

def detectar_separador(caminho_arquivo):
    """Detecta automaticamente se é ; ou ,"""
    try:
        with open(caminho_arquivo, 'r', encoding='latin1', errors='ignore') as f:
            sample = f.read(2048)
            if ';' in sample: return ';'
            sniffer = csv.Sniffer()
            return sniffer.sniff(sample).delimiter
    except:
        return ';'

def extrair_data_do_caminho(caminho_arquivo):
    """Pega Ano/Trimestre da estrutura de pastas se não tiver no CSV"""
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

def normalizar_e_processar(df, caminho_arquivo):
    # 1. Padroniza nomes das colunas (Upper case)
    df.columns = [c.strip().upper() for c in df.columns]
    
    # 2. Renomeação com Prioridade
    # O dicionário MAPA_COLUNAS vai transformar VL_SALDO_FINAL em 'ValorDespesas'.
    # VL_SALDO_INICIAL será ignorado/descartado naturalmente.
    df.rename(columns={k.upper(): v for k, v in MAPA_COLUNAS.items()}, inplace=True)

    # Verifica se a coluna alvo foi encontrada
    if 'ValorDespesas' not in df.columns:
        return None

    # 3. Filtro de Linhas (Keywords na Descrição)
    if 'DESC' in df.columns:
        filtro = df['DESC'].astype(str).str.contains(REGEX_PALAVRAS_CHAVE, case=False, regex=True, na=False)
        df = df[filtro]
    else:
        return None

    if df.empty:
        return None

    # 4. Tratamento de Data
    if 'DATA' in df.columns:
        try:
            df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce', dayfirst=True)
            df['Ano'] = df['DATA'].dt.year
            df['Trimestre'] = ((df['DATA'].dt.month - 1) // 3 + 1).astype(str) + "T"
        except:
            df['Ano'] = None
    
    # Fallback de Data (Pasta)
    if 'Ano' not in df.columns or df['Ano'].isnull().all():
        ano_pasta, trim_pasta = extrair_data_do_caminho(caminho_arquivo)
        if ano_pasta:
            df['Ano'] = ano_pasta
            df['Trimestre'] = trim_pasta

    df.dropna(subset=['Ano', 'Trimestre'], inplace=True)
    df['Ano'] = df['Ano'].astype(int)

    # 5. Tratamento REG_ANS
    if 'REG_ANS' not in df.columns:
        possiveis = [c for c in df.columns if 'COD' in c or 'CD_' in c]
        if possiveis:
            df.rename(columns={possiveis[0]: 'REG_ANS'}, inplace=True)
        else:
            return None

    # 6. Limpeza do Valor Numérico
    # Remove pontos de milhar e troca vírgula por ponto (Padrão BR -> US)
    col_valor = df['ValorDespesas'].astype(str)
    
    if col_valor.str.contains(',').any():
        col_valor = col_valor.str.replace('.', '', regex=False).str.replace(',', '.')
    
    df['ValorDespesas'] = pd.to_numeric(col_valor, errors='coerce')
    
    # Filtra valores inválidos ou zerados (opcional, mas recomendado)
    df = df[df['ValorDespesas'].notna() & (df['ValorDespesas'] != 0)]

    # Retorna apenas as colunas solicitadas
    cols_finais = ['REG_ANS', 'Trimestre', 'Ano', 'ValorDespesas']
    return df[cols_finais]

def processar_tudo():
    print(f"--- Iniciando Consolidação (Alvo: VL_SALDO_FINAL) ---")
    
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