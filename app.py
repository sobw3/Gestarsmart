from flask import Flask, jsonify, request, send_from_directory
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import mercadopago

app = Flask(__name__, static_folder='.', static_url_path='')

def get_db_connection():
    """Cria uma conexão com o banco de dados."""
    conn = sqlite3.connect('smart_fridge.db')
    conn.row_factory = sqlite3.Row # Isso permite acessar colunas por nome
    return conn

# --- Rota Principal para servir o HTML ---
@app.route('/')
def index():
    """Serve a página principal da aplicação."""
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run()


# --- API para Usuários (Login/Registro) ---
@app.route('/api/register', methods=['POST'])
def register():
    """Registra um novo usuário."""
    data = request.get_json()
    email = data['email']
    senha = data['password']
    
    conn = get_db_connection()
    # O primeiro usuário registrado será o admin
    count = conn.execute('SELECT COUNT(id) FROM usuarios').fetchone()[0]
    role = 'admin' if count == 0 else 'user'
    
    try:
        conn.execute(
            'INSERT INTO usuarios (email, senha, role) VALUES (?, ?, ?)',
            (email, generate_password_hash(senha), role)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Este email já está cadastrado.'}), 409
    finally:
        conn.close()
        
    return jsonify({'message': 'Usuário registrado com sucesso!', 'role': role})

@app.route('/api/login', methods=['POST'])
def login():
    """Realiza o login de um usuário."""
    data = request.get_json()
    email = data['email']
    senha = data['password']
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['senha'], senha):
        return jsonify({'message': 'Login bem-sucedido!', 'user': {'email': user['email'], 'role': user['role']}})
    
    return jsonify({'error': 'Email ou senha inválidos.'}), 401


# --- API para Produtos ---
@app.route('/api/produtos', methods=['GET', 'POST'])
def handle_produtos():
    """Lida com a listagem e criação de produtos."""
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        conn.execute(
            'INSERT INTO produtos (nome, preco_custo, preco_venda) VALUES (?, ?, ?)',
            (data['nome'], data['precoCusto'], data['precoVenda'])
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Produto criado com sucesso!'}), 201
    
    # GET
    produtos = conn.execute('SELECT * FROM produtos ORDER BY nome').fetchall()
    conn.close()
    return jsonify([dict(p) for p in produtos])

@app.route('/api/produtos/<int:id>', methods=['DELETE'])
def delete_produto(id):
    """Apaga um produto."""
    conn = get_db_connection()
    conn.execute('DELETE FROM produtos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Produto apagado com sucesso!'})

# --- API para Condomínios ---
@app.route('/api/condominios', methods=['GET', 'POST'])
def handle_condominios():
    """Lida com a listagem e criação de condomínios."""
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        conn.execute(
            'INSERT INTO condominios (nome, responsavel, endereco, investimento) VALUES (?, ?, ?, ?)',
            (data['nome'], data['responsavel'], data['endereco'], data['investimento'])
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Condomínio criado com sucesso!'}), 201
    
    # GET
    condominios = conn.execute('SELECT * FROM condominios ORDER BY nome').fetchall()
    conn.close()
    return jsonify([dict(c) for c in condominios])

@app.route('/api/condominios/<int:id>', methods=['DELETE'])
def delete_condominio(id):
    """Apaga um condomínio."""
    conn = get_db_connection()
    conn.execute('DELETE FROM condominios WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Condomínio apagado com sucesso!'})
    
# --- API de Estoque ---
@app.route('/api/estoque/<int:condo_id>', methods=['GET'])
def get_estoque(condo_id):
    """Pega o estoque de um condomínio específico."""
    conn = get_db_connection()
    query = """
    SELECT e.id, p.nome as produtoNome, e.quantidade, e.limite_critico, e.produto_id
    FROM estoque e
    JOIN produtos p ON e.produto_id = p.id
    WHERE e.condominio_id = ?
    ORDER BY p.nome
    """
    estoque = conn.execute(query, (condo_id,)).fetchall()
    conn.close()
    return jsonify([dict(e) for e in estoque])

@app.route('/api/estoque', methods=['POST'])
def add_estoque():
    """Adiciona ou atualiza um item no estoque."""
    data = request.get_json()
    condo_id = data['condominioId']
    produto_id = data['produtoId']
    quantidade = data['quantidade']
    limite_critico = data['limiteCritico']

    conn = get_db_connection()
    # Verifica se já existe para decidir entre INSERT ou UPDATE
    item_existente = conn.execute(
        'SELECT id, quantidade FROM estoque WHERE condominio_id = ? AND produto_id = ?',
        (condo_id, produto_id)
    ).fetchone()

    if item_existente:
        nova_quantidade = item_existente['quantidade'] + quantidade
        conn.execute(
            'UPDATE estoque SET quantidade = ?, limite_critico = ? WHERE id = ?',
            (nova_quantidade, limite_critico, item_existente['id'])
        )
    else:
        conn.execute(
            'INSERT INTO estoque (condominio_id, produto_id, quantidade, limite_critico) VALUES (?, ?, ?, ?)',
            (condo_id, produto_id, quantidade, limite_critico)
        )
    
    conn.commit()
    conn.close()
    return jsonify({'message': 'Estoque atualizado com sucesso!'})

@app.route('/api/estoque/repor', methods=['PUT'])
def repor_estoque():
    """Repõe uma quantidade específica em um item do estoque."""
    data = request.get_json()
    estoque_id = data['estoqueId']
    quantidade_adicional = data['quantidade']

    conn = get_db_connection()
    item_atual = conn.execute('SELECT quantidade FROM estoque WHERE id = ?', (estoque_id,)).fetchone()
    
    if item_atual:
        nova_quantidade = item_atual['quantidade'] + quantidade_adicional
        conn.execute('UPDATE estoque SET quantidade = ? WHERE id = ?', (nova_quantidade, estoque_id))
        conn.commit()
    conn.close()
    return jsonify({'message': 'Estoque reposto!'})


@app.route('/api/estoque/<int:id>', methods=['DELETE'])
def delete_estoque_item(id):
    """Remove um item do estoque."""
    conn = get_db_connection()
    conn.execute('DELETE FROM estoque WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Item removido do estoque.'})

# --- API de Vendas ---
@app.route('/api/vendas', methods=['POST'])
def registrar_venda():
    """Registra uma nova venda, atualiza o estoque E deposita o lucro no caixa."""
    data = request.get_json()
    condo_id = data['condominioId']
    produto_id = data['produtoId']
    quantidade_vendida = data['quantidade']

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Pega informações do estoque e do produto
    estoque_item = cursor.execute('SELECT * FROM estoque WHERE condominio_id = ? AND produto_id = ?', (condo_id, produto_id)).fetchone()
    if not estoque_item or estoque_item['quantidade'] < quantidade_vendida:
        conn.close()
        return jsonify({'error': 'Estoque insuficiente.'}), 400
        
    produto = cursor.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,)).fetchone()
    
    # 1. ATUALIZA O ESTOQUE
    nova_quantidade = estoque_item['quantidade'] - quantidade_vendida
    cursor.execute('UPDATE estoque SET quantidade = ? WHERE id = ?', (nova_quantidade, estoque_item['id']))
    
    # 2. REGISTRA A VENDA NA TABELA DE VENDAS
    custo_total = produto['preco_custo'] * quantidade_vendida
    venda_total = produto['preco_venda'] * quantidade_vendida
    cursor.execute(
        'INSERT INTO vendas (condominio_id, produto_id, quantidade, preco_custo_total, preco_venda_total) VALUES (?, ?, ?, ?, ?)',
        (condo_id, produto_id, quantidade_vendida, custo_total, venda_total)
    )
    
    # 3. (NOVO!) REGISTRA O LUCRO NO CAIXA CENTRAL
    lucro_da_venda = venda_total - custo_total
    if lucro_da_venda > 0:
        descricao_lucro = f"Lucro da venda de {quantidade_vendida}x {produto['nome']}"
        cursor.execute(
            'INSERT INTO caixa_transacoes (tipo, valor, descricao, responsavel) VALUES (?, ?, ?, ?)',
            ('entrada', lucro_da_venda, descricao_lucro, 'Sistema Automático')
        )
    
    conn.commit() # Salva todas as alterações (estoque, venda e caixa) de uma vez
    conn.close()
    
    return jsonify({'message': 'Venda registrada com sucesso!'})



# --- API de Relatórios e Análises ---
@app.route('/api/reposicao', methods=['GET'])
def get_reposicao_list():
    """Gera a lista de produtos que precisam de reposição."""
    conn = get_db_connection()
    query = """
    SELECT p.nome as produtoNome, e.quantidade, e.limite_critico, c.nome as condominioNome, c.endereco
    FROM estoque e
    JOIN produtos p ON e.produto_id = p.id
    JOIN condominios c ON e.condominio_id = c.id
    WHERE e.quantidade <= e.limite_critico
    ORDER BY c.nome, p.nome
    """
    itens = conn.execute(query).fetchall()
    conn.close()
    return jsonify([dict(i) for i in itens])


@app.route('/api/financeiro/<int:condo_id>', methods=['GET'])
def get_financeiro_condo(condo_id):
    """Calcula os dados financeiros dinâmicos para um condomínio."""
    conn = get_db_connection()
    
    condo = conn.execute(
        'SELECT investimento, despesas_fixas FROM condominios WHERE id = ?', 
        (condo_id,)
    ).fetchone()
    
    investimento_inicial = condo['investimento'] if condo else 0
    despesas_fixas = condo['despesas_fixas'] if condo else 0.00
    
    vendas = conn.execute(
        'SELECT SUM(preco_venda_total) as faturamento, SUM(preco_custo_total) as custo_total FROM vendas WHERE condominio_id = ?',
        (condo_id,)
    ).fetchone()
    
    conn.close()
    
    faturamento = vendas['faturamento'] or 0
    custo_produtos = vendas['custo_total'] or 0
    
    # Cálculos principais
    lucro_bruto = faturamento - custo_produtos
    lucro_liquido = lucro_bruto - despesas_fixas
    comissao = lucro_liquido * 0.02 if lucro_liquido > 0 else 0
    
    # (NOVO!) Cálculo do investimento restante a ser recuperado
    investimento_restante = investimento_inicial - lucro_bruto
    
    return jsonify({
        'investimentoInicial': investimento_inicial, # Enviando o valor original
        'investimentoRestante': investimento_restante, # (NOVO!) Enviando o valor a recuperar
        'despesas': despesas_fixas,
        'faturamento': faturamento, # (NOVO!) Enviando o faturamento total
        'lucroBruto': lucro_bruto, # Enviando o lucro bruto para a barra de progresso
        'lucroLiquido': lucro_liquido,
        'comissao': comissao
    })


    
@app.route('/api/relatorios/vendas', methods=['GET'])
def get_relatorio_vendas():
    """Gera um relatório de vendas por período."""
    data_inicio = request.args.get('inicio')
    data_fim = request.args.get('fim')
    
    conn = get_db_connection()
    query = """
    SELECT 
        v.data_venda, 
        c.nome as condominioNome, 
        p.nome as produtoNome, 
        v.quantidade, 
        v.preco_venda_total, 
        v.preco_custo_total,
        (v.preco_venda_total - v.preco_custo_total) as lucro
    FROM vendas v
    JOIN condominios c ON v.condominio_id = c.id
    JOIN produtos p ON v.produto_id = p.id
    WHERE v.data_venda BETWEEN ? AND ?
    ORDER BY v.data_venda
    """
    vendas = conn.execute(query, (f'{data_inicio} 00:00:00', f'{data_fim} 23:59:59')).fetchall()
    conn.close()
    return jsonify([dict(v) for v in vendas])

@app.route('/api/condominios/<int:id>/despesas', methods=['PUT'])
def update_despesas_condo(id):
    """Atualiza o valor das despesas fixas de um condomínio."""
    data = request.get_json()
    novo_valor = data.get('valor')
    
    if novo_valor is None:
        return jsonify({'error': 'Valor não fornecido'}), 400

    conn = get_db_connection()
    conn.execute('UPDATE condominios SET despesas_fixas = ? WHERE id = ?', (novo_valor, id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Despesas atualizadas com sucesso!'})

@app.route('/api/caixa', methods=['GET'])
def get_caixa_info():
    """Busca as transações e o saldo atual do caixa."""
    conn = get_db_connection()
    
    transacoes = conn.execute(
        'SELECT * FROM caixa_transacoes ORDER BY data_transacao DESC'
    ).fetchall()
    
    saldo = conn.execute(
        """
        SELECT 
            (SELECT IFNULL(SUM(valor), 0) FROM caixa_transacoes WHERE tipo = 'entrada') - 
            (SELECT IFNULL(SUM(valor), 0) FROM caixa_transacoes WHERE tipo = 'saida')
        """
    ).fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'saldo_atual': saldo,
        'transacoes': [dict(t) for t in transacoes]
    })

@app.route('/api/caixa/transacao', methods=['POST'])
def add_caixa_transacao():
    """Adiciona uma nova transação (entrada ou saida) ao caixa."""
    data = request.get_json()
    tipo = data.get('tipo')
    valor = data.get('valor')
    descricao = data.get('descricao')
    responsavel = data.get('responsavel') # Pode ser nulo

    if not tipo or not valor or not descricao:
        return jsonify({'error': 'Dados incompletos'}), 400

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO caixa_transacoes (tipo, valor, descricao, responsavel) VALUES (?, ?, ?, ?)',
        (tipo, valor, descricao, responsavel)
    )
    conn.commit()
    conn.close()

    return jsonify({'message': 'Transação registrada com sucesso!'}), 201

@app.route('/webhook-mercadopago', methods=['POST'])
def webhook_mercadopago():
    """Recebe notificações de pagamento do Mercado Pago."""
    data = request.get_json()

    if data and data.get('type') == 'payment':
        payment_id = data['data']['id']
        
        # Substitua 'SEU_ACCESS_TOKEN' pela sua chave, se ainda não o fez
        sdk = mercadopago.SDK("SEU_ACCESS_TOKEN") 
        payment_info = sdk.payment().get(payment_id)
        
        # --- LINHAS DE DEBUG CORRIGIDAS ---
        # A indentação aqui está correta, alinhada com o 'if' abaixo.
        print("--- DADOS RECEBIDOS DO MERCADO PAGO ---")
        print(payment_info)
        print("-----------------------------------------")
        
        if payment_info["status"] == 200 and payment_info["response"]["status"] == "approved":
            payment = payment_info["response"]
            
            # Loop através dos itens vendidos
            for item in payment.get("additional_info", {}).get("items", []):
                try:
                    # Extrai o nome do produto e do condomínio
                    parts = item['title'].strip().rsplit('(', 1)
                    if len(parts) != 2:
                        print(f"ERRO: Título do produto fora do padrão: {item['title']}")
                        continue

                    product_name = parts[0].strip()
                    condo_name = parts[1].replace(')', '').strip()
                    quantity_sold = int(item['quantity'])

                    # Conecta ao nosso banco de dados local
                    conn = get_db_connection()
                    
                    # Encontra o ID do produto e do condomínio no nosso sistema
                    produto_db = conn.execute('SELECT id, preco_custo, preco_venda FROM produtos WHERE nome = ?', (product_name,)).fetchone()
                    condo_db = conn.execute('SELECT id FROM condominios WHERE nome = ?', (condo_name,)).fetchone()

                    if not produto_db or not condo_db:
                        print(f"ERRO: Produto '{product_name}' ou Condomínio '{condo_name}' não encontrado no sistema.")
                        conn.close() # Fecha a conexão antes de pular para o próximo item
                        continue

                    # Atualiza o estoque
                    estoque_item = conn.execute('SELECT id, quantidade FROM estoque WHERE condominio_id = ? AND produto_id = ?', (condo_db['id'], produto_db['id'])).fetchone()
                    if estoque_item and estoque_item['quantidade'] >= quantity_sold:
                        nova_quantidade = estoque_item['quantidade'] - quantity_sold
                        conn.execute('UPDATE estoque SET quantidade = ? WHERE id = ?', (nova_quantidade, estoque_item['id']))
                        
                        # Registra a venda
                        custo_total = produto_db['preco_custo'] * quantity_sold
                        venda_total = produto_db['preco_venda'] * quantity_sold
                        conn.execute(
                            'INSERT INTO vendas (condominio_id, produto_id, quantidade, preco_custo_total, preco_venda_total) VALUES (?, ?, ?, ?, ?)',
                            (condo_db['id'], produto_db['id'], quantity_sold, custo_total, venda_total)
                        )
                        conn.commit()
                        print(f"SUCESSO: Venda de {quantity_sold}x {product_name} no {condo_name} registrada.")
                    else:
                        print(f"ERRO DE ESTOQUE: Não foi possível registrar a venda de {product_name}.")
                    
                    conn.close()

                except Exception as e:
                    print(f"Ocorreu um erro ao processar o item: {e}")
    
    # Responde ao Mercado Pago que recebemos a notificação com sucesso
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    # Usar host='0.0.0.0' torna o servidor acessível na sua rede local
    app.run(debug=True, host='0.0.0.0', port=5000)
