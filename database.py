import sqlite3
import os

# --- ALTERAÇÃO PARA RENDER ---
# Define o caminho do banco de dados. No Render, ele usará um "Disco Persistente".
# No seu computador, continuará criando o arquivo na pasta local.
DB_PATH = os.environ.get("DB_PATH", ".") 
DB_FILE = os.path.join(DB_PATH, "smart_fridge.db")

# Função para criar o banco de dados e as tabelas
def criar_banco():
    # Não cria um novo banco se ele já existir
    if os.path.exists(DB_FILE):
        print(f"O banco de dados '{DB_FILE}' já existe. Nenhuma ação foi tomada.")
        return

    print(f"Criando novo banco de dados em: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Tabela de Usuários
    cursor.execute('''
    CREATE TABLE usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    )
    ''')

    # Tabela de Produtos
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
        despesas_fixas REAL NOT NULL DEFAULT 200.00
    )
    ''')

    # Tabela de Estoque
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

    # Tabela de Despesas (não usada ativamente, mas mantida)
    cursor.execute('''
    CREATE TABLE despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        valor REAL NOT NULL,
        dia_vencimento INTEGER NOT NULL,
        paga_neste_mes INTEGER NOT NULL DEFAULT 0
    )
    ''')

    # Tabela para o Caixa Central
    cursor.execute('''
    CREATE TABLE caixa_transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        valor REAL NOT NULL,
        descricao TEXT NOT NULL,
        responsavel TEXT,
        data_transacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()
    print(f"Banco de dados '{DB_FILE}' criado com sucesso.")

# Permite que este script seja executado diretamente pelo terminal
if __name__ == "__main__":
    criar_banco()
