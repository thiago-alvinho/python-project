# Usa uma imagem leve do Node.js
FROM node:24-alpine

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Copia os arquivos de dependência primeiro (para cachear a instalação)
COPY package*.json ./

# Instala as dependências
RUN npm install

# Copia o restante do código
COPY . .

# Expõe a porta padrão do Vite
EXPOSE 5173

# Roda o servidor de desenvolvimento liberando o acesso externo (--host)
CMD ["npm", "run", "dev", "--", "--host"]