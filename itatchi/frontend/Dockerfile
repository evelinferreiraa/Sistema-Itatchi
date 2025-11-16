# Usa uma imagem base Python leve
FROM python:3.10-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante dos arquivos
COPY . .

# Expõe a porta padrão do Streamlit
EXPOSE 8501

# Copia e dá permissão ao entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Executa o entrypoint
ENTRYPOINT ["/entrypoint.sh"]
