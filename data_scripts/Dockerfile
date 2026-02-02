# Por que 'slim'? É uma versão mais leve do Python (baseada em Debian), 
# removendo ferramentas inúteis, mas mantendo o necessário para compilar libs comuns.
FROM python:3.11-slim

# PYTHONDONTWRITEBYTECODE=1: Evita que o Python crie arquivos .pyc (desnecessário em container).
# PYTHONUNBUFFERED=1: CRUCIAL. Faz com que os 'prints' do Python apareçam imediatamente 
# no log do Docker, sem ficar "presos" em buffer.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV BASE_DATA_DIR="/app/data"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia tudo da pasta atual para /app
COPY . . 


CMD ["python", "main.py"]
