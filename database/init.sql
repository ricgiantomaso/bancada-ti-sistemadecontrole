-- Criação das tabelas
USE flask_crud;

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_completo VARCHAR(200) NOT NULL,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    numero_funcional VARCHAR(50) UNIQUE NOT NULL,
    senha_hash VARCHAR(200) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de equipamentos
CREATE TABLE IF NOT EXISTS equipamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_entrada DATE NOT NULL,
    local VARCHAR(100) NOT NULL,
    tipo_equipamento VARCHAR(50) NOT NULL,
    patrimonio VARCHAR(50) UNIQUE NOT NULL,
    defeito TEXT NOT NULL,
    observacoes TEXT,
    prioridade VARCHAR(20) DEFAULT 'media',
    status VARCHAR(20) DEFAULT 'entrada',
    criador_id INT,
    responsavel_id INT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (criador_id) REFERENCES usuarios(id),
    FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
);

-- Tabela de unidades
CREATE TABLE IF NOT EXISTS unidades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(20),
    ativo BOOLEAN DEFAULT TRUE,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de logs
CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    usuario_nome VARCHAR(100),
    acao VARCHAR(50) NOT NULL,
    entidade VARCHAR(50) NOT NULL,
    entidade_id INT,
    descricao TEXT,
    dados_antigos JSON,
    dados_novos JSON,
    ip VARCHAR(45),
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
);

-- Inserir admin (senha: admin)
INSERT INTO usuarios (nome_completo, usuario, email, numero_funcional, senha_hash) 
SELECT 'Administrador', 'admin', 'admin@email.com', '000001', 
       '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'
WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE usuario = 'admin');

-- Inserir unidades de exemplo
INSERT INTO unidades (nome, telefone) VALUES
('Matriz São Paulo', '(11) 3333-4444'),
('Filial Rio de Janeiro', '(21) 5555-6666'),
('Filial Minas Gerais', '(31) 7777-8888')
ON DUPLICATE KEY UPDATE nome=nome;