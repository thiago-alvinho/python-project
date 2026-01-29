import requests
from bs4 import BeautifulSoup
import os
import re
import zipfile

BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/"
CATEGORIA = "demonstracoes_contabeis/" 
DIR_SAIDA = "downloads_ans"

#Função para obter o html da url utilizando a biblioteca beautifulsoup que irá facilitar a navegação pela estrutura
def obter_sopa(url):
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"   [Erro conexão]: {e}")
        return None

#Função responsável por baixar o arquivo
def baixar_arquivo_unico(url, caminho_local):
    
    try:
        os.makedirs(os.path.dirname(caminho_local), exist_ok=True)
        print(f"      -> Baixando arquivo direto: {os.path.basename(caminho_local)}")
        
        #Decidi baixar os arquivos em chunks, para evitar o problema de encher a memória principal e a máquina ficar lenta
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(caminho_local, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"      [Erro Download]: {e}")
        return False

#Função responsável por entrar nos diretórios. Recursiva até achar os arquivos finais.
def processar_pasta_recursiva(url_diretorio, pasta_destino):
    soup = obter_sopa(url_diretorio)
    if not soup: return

    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    for link in soup.find_all('a'):
        href = link.get('href')
        
        if not href or href in ['../', './'] or href.startswith('?'):
            continue

        url_completa = url_diretorio + href
        
        # CASO A: É arquivo
        if href.lower().endswith(('.zip', '.csv', '.pdf', '.rar')):
            print(f"      [Arquivo encontrado na pasta]: {href}")
            caminho_arquivo = os.path.join(pasta_destino, href)
            baixar_arquivo_unico(url_completa, caminho_arquivo)
        
        # CASO B: É subpasta
        elif href.endswith('/'):
            print(f"      [Subpasta encontrada]: {href}")
            nova_pasta = os.path.join(pasta_destino, href.strip('/'))
            processar_pasta_recursiva(url_completa, nova_pasta)

#Função utilizada para listar os links das tags <a> que satisfaçam o regex especificado.
def listar_links(url, padrao_regex):
    soup = obter_sopa(url)
    if not soup: return []
    
    links_encontrados = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and re.match(padrao_regex, href):
            links_encontrados.append(href)
    
    return sorted(links_encontrados, reverse=True)


#Função utilizada para extrair os arquivos .zip
def extrair_arquivos(diretorio_alvo):

    if not os.path.exists(diretorio_alvo):
        print(f"Erro: A pasta '{diretorio_alvo}' não existe.")
        return

    print(f"\n--- Iniciando extração em: {os.path.abspath(diretorio_alvo)} ---\n")
    
    arquivos_extraidos = 0

    for pasta_atual, subpastas, arquivos in os.walk(diretorio_alvo):
        for arquivo in arquivos:
            if arquivo.lower().endswith('.zip'):
                caminho_completo = os.path.join(pasta_atual, arquivo)
                print(f" > Extraindo ZIP encontrado: {arquivo}")
                
                try:
                    with zipfile.ZipFile(caminho_completo, 'r') as zip_ref:
                        zip_ref.extractall(pasta_atual)
                        print(f"   -> Sucesso!")
                        arquivos_extraidos += 1
                        
                except zipfile.BadZipFile:
                    print(f"   [X] Erro: Arquivo corrompido.")
                except Exception as e:
                    print(f"   [X] Erro desconhecido: {e}")

    print(f"\nConcluído! Total de arquivos extraídos: {arquivos_extraidos}")

def main():
    url_categoria = BASE_URL + CATEGORIA
    print(f"Acessando: {url_categoria}")

    #Obtendo os anos disponíveis
    anos = listar_links(url_categoria, r"^\d{4}/$")
    
    trimestres_coletados = 0
    meta_trimestres = 3

    for ano in anos:
        if trimestres_coletados >= meta_trimestres: break
            
        print(f"\nVerificando Ano: {ano}")
        url_ano = url_categoria + ano
        
        #Links começando com dígito são os links dos trimestres
        trimestres = listar_links(url_ano, r"^\d.*")
        print(f"   Itens encontrados: {trimestres}")

        for trim in trimestres:
            if trimestres_coletados >= meta_trimestres: break

            print(f"   > Processando item: {trim}")
            
            nome_sujo = trim.strip('/')
            if nome_sujo.lower().endswith('.zip'):
                nome_pasta = nome_sujo[:-4]
            else:
                nome_pasta = nome_sujo

            #Criando o nome das pastas que ficará salvo o arquivo
            pasta_local = os.path.join(DIR_SAIDA, ano.strip('/'), nome_pasta)
            url_item = url_ano + trim
            
            sucesso = False
            
            # CASO A: É arquivo
            if trim.lower().endswith('.zip'):
                caminho_final = os.path.join(pasta_local, trim)
                sucesso = baixar_arquivo_unico(url_item, caminho_final)
            
            # CASO B: É subpasta
            elif trim.endswith('/'):
                processar_pasta_recursiva(url_item, pasta_local)
                sucesso = True
            
            else:
                print(f"     [Ignorado]: {trim}")

            if sucesso:
                trimestres_coletados += 1
        
    extrair_arquivos(DIR_SAIDA)

    print(f"\nProcesso Finalizado.")

if __name__ == "__main__":
    main()