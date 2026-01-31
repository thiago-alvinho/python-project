# Usa uma imagem leve do Python
FROM python:3.9-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia os requirements e instala
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Comando para rodar a API
# --host 0.0.0.0 é obrigatório dentro do Docker
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]