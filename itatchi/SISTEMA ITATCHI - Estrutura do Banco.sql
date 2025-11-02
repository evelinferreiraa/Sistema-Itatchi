CREATE DATABASE itatchi CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; -- Codificação UTF-8 para nomes e acentos em português

-- SISTEMA ITATCHI - Estrutura do Banco 

USE itatchi;

-- 1. Tabela: filial
CREATE TABLE filial (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    codigo VARCHAR(10) NOT NULL UNIQUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. Tabela: tipodocumento
CREATE TABLE tipodocumento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    categoria ENUM('Regulatórios','Qualidade','Pessoas','Veículos','Locais') NOT NULL,
    nome VARCHAR(100) NOT NULL,
    obrigatorio BOOLEAN DEFAULT FALSE,
    prazo_padrao_dias INT DEFAULT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. Tabela: documento
CREATE TABLE documento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filial_id INT NOT NULL,
    tipo_id INT NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    numero VARCHAR(100),
    responsavel VARCHAR(100) NOT NULL,
    emissao DATE,
    validade DATE,
    sem_validade BOOLEAN DEFAULT FALSE,
    orgao_emissor VARCHAR(150),
    observacoes TEXT,
    caminho_atual VARCHAR(500),
    versao_atual VARCHAR(20) DEFAULT '1.0.0',
    status_calc ENUM('VIGENTE','A_VENCER','VENCIDO','SEM_VALIDADE') DEFAULT 'VIGENTE',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (filial_id) REFERENCES filial(id),
    FOREIGN KEY (tipo_id) REFERENCES tipodocumento(id)
);

-- 4. Tabela: versao
CREATE TABLE versao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    documento_id INT NOT NULL,
    numero_versao VARCHAR(20) NOT NULL,
    caminho_arquivo VARCHAR(500) NOT NULL,
    motivo VARCHAR(255),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (documento_id) REFERENCES documento(id)
);

-- 5. (Opcional) Tabela: vinculo
CREATE TABLE vinculo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    documento_id INT NOT NULL,
    tipo_alvo ENUM('MOTORISTA','VEICULO','LOCAL') NOT NULL,
    alvo_id VARCHAR(100),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (documento_id) REFERENCES documento(id)
);

-- Verificar 
SHOW TABLES;

-- Dados de teste
INSERT INTO filial (nome, codigo) VALUES ('Matriz São Paulo', 'SP01');

INSERT INTO tipodocumento (categoria, nome, obrigatorio, prazo_padrao_dias)
VALUES ('Regulatórios', 'CNPJ', TRUE, 365),
       ('Veículos', 'ANTT', TRUE, 180),
       ('Pessoas', 'CNH', TRUE, 365);

