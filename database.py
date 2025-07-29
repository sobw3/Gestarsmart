import sqlite3
import os

DB_FILE = "smart_fridge.db"

# Apaga o banco de dados antigo, se existir, para um início limpo.
# Cuidado: em um ambiente real, você não faria isso.
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

# Conecta-se ao banco de dados (irá criar o arquivo se ele não existir)
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Criação das tabelas

# Tabela de Usuários (para login)
cursor.execute('''
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' -- 'admin' ou 'user'
)
''')

# Tabela de Produtos (catálogo geral)
cursor.execute('''
CREATE TABLE produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco_custo REAL NOT NULL,
    preco_venda REAL NOT NULL
)
''')

# Tabela de Condomínios
cursor.execute('''
CREATE TABLE condominios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    responsavel TEXT,
    endereco TEXT,
    investimento REAL NOT NULL DEFAULT 0,
    despesas_fixas REAL NOT NULL DEFAULT 200.00 -- << ADICIONE ESTA LINHA
)
''')

# Tabela de Estoque (relaciona produtos e condomínios)
cursor.execute('''
CREATE TABLE estoque (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    condominio_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    limite_critico INTEGER NOT NULL,
    FOREIGN KEY (condominio_id) REFERENCES condominios (id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos (id) ON DELETE CASCADE,
    UNIQUE(condominio_id, produto_id)
)
''')

# Tabela de Vendas
cursor.execute('''
CREATE TABLE vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    condominio_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_custo_total REAL NOT NULL,
    preco_venda_total REAL NOT NULL,
    data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (condominio_id) REFERENCES condominios (id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos (id) ON DELETE CASCADE
)
''')

# Tabela de Despesas recorrentes
cursor.execute('''
CREATE TABLE despesas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    valor REAL NOT NULL,
    dia_vencimento INTEGER NOT NULL, -- Dia do mês (1-31)
    paga_neste_mes INTEGER NOT NULL DEFAULT 0 -- 0 para não, 1 para sim
)
''')

# Tabela para o Caixa Central
cursor.execute('''
CREATE TABLE caixa_transacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL, -- 'entrada' ou 'saida'
    valor REAL NOT NULL,
    descricao TEXT NOT NULL,
    responsavel TEXT, -- Para quem foi a retirada, etc.
    data_transacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Salva (commit) as alterações
conn.commit()

# Fecha a conexão
conn.close()

print(f"Banco de dados '{DB_FILE}' criado com sucesso.")
