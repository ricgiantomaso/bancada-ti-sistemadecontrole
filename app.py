from flask import Flask, request, jsonify, render_template, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import secrets

app = Flask(__name__)

# ==================== CONFIGURAÇÕES ====================
# Configuração CORS completa
CORS(app, 
     origins=["http://127.0.0.1:5000", "http://localhost:5000"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     expose_headers=["Content-Type", "X-Requested-With"],
     supports_credentials=True,
     max_age=3600)

app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui-mude-em-producao'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/flask_crud'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== MODELOS ====================
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(200), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    numero_funcional = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_senha(self, senha):
        self.senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    
    def verificar_senha(self, senha):
        return self.senha_hash == hashlib.sha256(senha.encode()).hexdigest()
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome_completo': self.nome_completo,
            'usuario': self.usuario,
            'email': self.email,
            'numero_funcional': self.numero_funcional,
            'ativo': self.ativo
        }

class Equipamento(db.Model):
    __tablename__ = 'equipamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    data_entrada = db.Column(db.Date, nullable=False)
    local = db.Column(db.String(100), nullable=False)
    tipo_equipamento = db.Column(db.String(50), nullable=False)
    patrimonio = db.Column(db.String(50), unique=True, nullable=False)
    defeito = db.Column(db.Text, nullable=False)
    observacoes = db.Column(db.Text)
    prioridade = db.Column(db.String(20), default='media')
    status = db.Column(db.String(20), default='entrada')
    criador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    criador = db.relationship('Usuario', backref='equipamentos')
    
    def to_dict(self):
        return {
            'id': self.id,
            'data_entrada': self.data_entrada.strftime('%Y-%m-%d') if self.data_entrada else None,
            'local': self.local,
            'tipo_equipamento': self.tipo_equipamento,
            'patrimonio': self.patrimonio,
            'defeito': self.defeito,
            'observacoes': self.observacoes,
            'prioridade': self.prioridade,
            'status': self.status,
            'criador_nome': self.criador.nome_completo if self.criador else 'Sistema'
        }

class Unidade(db.Model):
    __tablename__ = 'unidades'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20))
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'telefone': self.telefone,
            'ativo': self.ativo
        }

class Log(db.Model):
    __tablename__ = 'logs'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    usuario_nome = db.Column(db.String(100))
    acao = db.Column(db.String(50), nullable=False)
    entidade = db.Column(db.String(50), nullable=False)
    entidade_id = db.Column(db.Integer)
    descricao = db.Column(db.Text)
    dados_antigos = db.Column(db.JSON)
    dados_novos = db.Column(db.JSON)
    ip = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    usuario = db.relationship('Usuario', backref='logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario': self.usuario_nome or 'Sistema',
            'acao': self.acao,
            'entidade': self.entidade,
            'entidade_id': self.entidade_id,
            'descricao': self.descricao,
            'ip': self.ip,
            'user_agent': self.user_agent,
            'data': self.created_at.strftime('%d/%m/%Y %H:%M:%S') if self.created_at else None,
            'dados_antigos': self.dados_antigos,
            'dados_novos': self.dados_novos
        }

# ==================== FUNÇÃO DE LOG ====================

def registrar_log(acao, entidade, entidade_id=None, descricao=None, 
                  dados_antigos=None, dados_novos=None):
    """
    Registra uma ação no sistema
    """
    try:
        # Pegar informações do usuário
        usuario_id = None
        usuario_nome = 'Sistema'
        
        # Tentar pegar da sessão
        if 'usuario_id' in session:
            usuario_id = session.get('usuario_id')
            usuario_nome = session.get('usuario_nome', 'Sistema')
        
        # Se não tiver na sessão, tenta pegar do token
        if not usuario_id and hasattr(request, 'usuario'):
            usuario_id = request.usuario.id
            usuario_nome = request.usuario.nome_completo
        
        # Criar log
        log = Log(
            usuario_id=usuario_id,
            usuario_nome=usuario_nome,
            acao=acao,
            entidade=entidade,
            entidade_id=entidade_id,
            descricao=descricao,
            dados_antigos=dados_antigos,
            dados_novos=dados_novos,
            ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        db.session.add(log)
        db.session.commit()
        print(f"✅ Log registrado: {acao} - {entidade} #{entidade_id if entidade_id else ''}")
        
    except Exception as e:
        print(f"❌ Erro ao registrar log: {e}")
        db.session.rollback()

# ==================== CRIAR TABELAS ====================
with app.app_context():
    # Criar tabelas se não existirem (NÃO APAGA DADOS)
    db.create_all()
    print("✅ Tabelas verificadas/criadas com sucesso!")
    
    # Criar admin apenas se não existir
    if not Usuario.query.filter_by(usuario='admin').first():
        admin = Usuario(
            nome_completo='Administrador',
            usuario='admin',
            email='admin@email.com',
            numero_funcional='000001'
        )
        admin.set_senha('admin')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin criado!")
    else:
        print("✅ Admin já existe")

# ==================== DECORADOR DE TOKEN ====================
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Para requisições OPTIONS, não verificar token
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)
            
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'erro': 'Token não fornecido'}), 401
        
        try:
            # Token simples (ID do usuário + hash)
            user_id = int(token.split('-')[0])
            usuario = Usuario.query.get(user_id)
            if not usuario:
                return jsonify({'erro': 'Token inválido'}), 401
            request.usuario = usuario
            return f(*args, **kwargs)
        except:
            return jsonify({'erro': 'Token inválido'}), 401
    
    return decorated

# ==================== ROTAS DE PÁGINAS ====================
@app.route('/')
def home():
    return redirect('/login')

@app.route('/login')
def pagina_login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('index.html')

@app.route('/equipamento/cadastro')
def cadastro_equipamento():
    return render_template('entrada-equipamento.html')

@app.route('/usuario/cadastro')
def pagina_cadastro_usuario():
    return render_template('cadastro-usuario.html')

@app.route('/quadro-chamados')
def quadro_chamados():
    return render_template('quadro-chamados.html')

@app.route('/relatorios')
def relatorios():
    return render_template('relatorios.html')

@app.route('/editar-chamado')
def editar_chamado():
    return render_template('editar-chamado.html')

@app.route('/logs')
def pagina_logs():
    return render_template('logs.html')

# ==================== ROTAS DA API - LOGIN ====================
@app.route('/api/login', methods=['POST', 'OPTIONS'])
def api_login():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        dados = request.get_json()
        
        if not dados or 'usuario' not in dados or 'senha' not in dados:
            return jsonify({'erro': 'Usuário e senha obrigatórios'}), 400
        
        usuario = Usuario.query.filter(
            (Usuario.usuario == dados['usuario']) | 
            (Usuario.email == dados['usuario'])
        ).first()
        
        if not usuario or not usuario.verificar_senha(dados['senha']):
            # Registrar tentativa de login falha
            registrar_log(
                acao='LOGIN_FAILED',
                entidade='usuario',
                descricao=f"Tentativa de login falha para: {dados.get('usuario')}"
            )
            return jsonify({'erro': 'Credenciais inválidas'}), 401
        
        if not usuario.ativo:
            registrar_log(
                acao='LOGIN_FAILED',
                entidade='usuario',
                entidade_id=usuario.id,
                descricao=f"Tentativa de login com usuário inativo: {usuario.nome_completo}"
            )
            return jsonify({'erro': 'Usuário inativo'}), 403
        
        # Criar sessão
        session['usuario_id'] = usuario.id
        session['usuario_nome'] = usuario.nome_completo
        
        # Gerar token
        token = f"{usuario.id}-{secrets.token_hex(8)}"
        
        # Registrar login bem-sucedido
        registrar_log(
            acao='LOGIN',
            entidade='usuario',
            entidade_id=usuario.id,
            descricao=f"Usuário {usuario.nome_completo} fez login"
        )
        
        return jsonify({
            'success': True,
            'token': token,
            'usuario': usuario.to_dict()
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ==================== ROTAS DA API - USUÁRIOS ====================
@app.route('/api/usuarios', methods=['OPTIONS'])
def usuarios_options():
    return '', 200

@app.route('/api/usuarios', methods=['POST'])
@token_required
def criar_usuario():
    try:
        dados = request.get_json()
        print("📝 Dados recebidos:", dados)
        
        # Validar campos obrigatórios
        campos = ['nome_completo', 'usuario', 'email', 'numero_funcional', 'senha']
        for campo in campos:
            if campo not in dados or not dados[campo]:
                return jsonify({'erro': f'Campo {campo} obrigatório'}), 400
        
        # Verificar se já existe
        if Usuario.query.filter_by(usuario=dados['usuario']).first():
            return jsonify({'erro': 'Nome de usuário já existe'}), 400
        
        if Usuario.query.filter_by(email=dados['email']).first():
            return jsonify({'erro': 'Email já cadastrado'}), 400
        
        if Usuario.query.filter_by(numero_funcional=dados['numero_funcional']).first():
            return jsonify({'erro': 'Número funcional já cadastrado'}), 400
        
        # Validar senha (mínimo 6 caracteres)
        if len(dados['senha']) < 6:
            return jsonify({'erro': 'Senha deve ter no mínimo 6 caracteres'}), 400
        
        # Criar usuário
        usuario = Usuario(
            nome_completo=dados['nome_completo'],
            usuario=dados['usuario'],
            email=dados['email'],
            numero_funcional=dados['numero_funcional']
        )
        usuario.set_senha(dados['senha'])
        
        db.session.add(usuario)
        db.session.flush()  # Para pegar o ID antes do commit
        
        # Registrar criação
        registrar_log(
            acao='CREATE',
            entidade='usuario',
            entidade_id=usuario.id,
            descricao=f"Usuário criado: {usuario.nome_completo} ({usuario.usuario})",
            dados_novos=usuario.to_dict()
        )
        
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Usuário criado com sucesso',
            'usuario': usuario.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print("❌ Erro:", str(e))
        return jsonify({'erro': str(e)}), 500

@app.route('/api/usuarios', methods=['GET'])
@token_required
def listar_usuarios():
    try:
        usuarios = Usuario.query.all()
        return jsonify([u.to_dict() for u in usuarios])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ==================== ROTAS DA API - EQUIPAMENTOS ====================
@app.route('/api/equipamentos', methods=['OPTIONS'])
def equipamentos_options():
    return '', 200

@app.route('/api/equipamentos', methods=['GET'])
@token_required
def listar_equipamentos():
    try:
        equipamentos = Equipamento.query.order_by(Equipamento.id.desc()).all()
        return jsonify([e.to_dict() for e in equipamentos])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/equipamentos/<int:id>', methods=['GET', 'OPTIONS'])
@token_required
def buscar_equipamento(id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        equipamento = Equipamento.query.get(id)
        if not equipamento:
            return jsonify({'erro': 'Equipamento não encontrado'}), 404
        return jsonify(equipamento.to_dict())
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/equipamentos', methods=['POST'])
@token_required
def criar_equipamento():
    try:
        dados = request.get_json()
        print("📝 Dados equipamento:", dados)
        
        # Validar campos
        campos = ['data_entrada', 'local', 'tipo_equipamento', 'patrimonio', 'defeito', 'prioridade']
        for campo in campos:
            if campo not in dados or not dados[campo]:
                return jsonify({'erro': f'Campo {campo} obrigatório'}), 400
        
        # Verificar patrimônio
        if Equipamento.query.filter_by(patrimonio=dados['patrimonio']).first():
            return jsonify({'erro': 'Patrimônio já cadastrado'}), 400
        
        # Criar equipamento
        equipamento = Equipamento(
            data_entrada=datetime.strptime(dados['data_entrada'], '%Y-%m-%d').date(),
            local=dados['local'],
            tipo_equipamento=dados['tipo_equipamento'],
            patrimonio=dados['patrimonio'],
            defeito=dados['defeito'],
            observacoes=dados.get('observacoes', ''),
            prioridade=dados['prioridade'],
            criador_id=request.usuario.id
        )
        
        db.session.add(equipamento)
        db.session.flush()
        
        # Registrar criação
        registrar_log(
            acao='CREATE',
            entidade='equipamento',
            entidade_id=equipamento.id,
            descricao=f"Equipamento criado: {equipamento.tipo_equipamento} - {equipamento.patrimonio}",
            dados_novos=equipamento.to_dict()
        )
        
        db.session.commit()
        
        return jsonify(equipamento.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        print("❌ Erro:", str(e))
        return jsonify({'erro': str(e)}), 500

@app.route('/api/equipamentos/estatisticas', methods=['GET', 'OPTIONS'])
@token_required
def estatisticas_equipamentos():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        total = Equipamento.query.count()
        stats = {
            'entrada': Equipamento.query.filter_by(status='entrada').count(),
            'manutencao': Equipamento.query.filter_by(status='manutencao').count(),
            'pronto': Equipamento.query.filter_by(status='pronto').count(),
            'entregue': Equipamento.query.filter_by(status='entregue').count()
        }
        return jsonify({'total': total, 'por_status': stats})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/equipamentos/<int:id>/mover', methods=['PATCH', 'OPTIONS'])
@token_required
def mover_equipamento(id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        equipamento = Equipamento.query.get(id)
        if not equipamento:
            return jsonify({'erro': 'Equipamento não encontrado'}), 404
        
        dados = request.get_json()
        novo_status = dados.get('status')
        status_antigo = equipamento.status
        
        status_validos = ['entrada', 'manutencao', 'pronto', 'entregue']
        if novo_status not in status_validos:
            return jsonify({'erro': 'Status inválido'}), 400
        
        equipamento.status = novo_status
        
        # Registrar movimento
        registrar_log(
            acao='MOVE',
            entidade='equipamento',
            entidade_id=id,
            descricao=f"Equipamento movido de '{status_antigo}' para '{novo_status}'",
            dados_antigos={'status': status_antigo},
            dados_novos={'status': novo_status}
        )
        
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Status atualizado com sucesso',
            'equipamento': equipamento.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@app.route('/api/equipamentos/<int:id>', methods=['DELETE', 'OPTIONS'])
@token_required
def deletar_equipamento(id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        equipamento = Equipamento.query.get(id)
        if not equipamento:
            return jsonify({'erro': 'Equipamento não encontrado'}), 404
        
        dados_equipamento = equipamento.to_dict()
        
        # Registrar exclusão
        registrar_log(
            acao='DELETE',
            entidade='equipamento',
            entidade_id=id,
            descricao=f"Equipamento deletado: {equipamento.tipo_equipamento} - {equipamento.patrimonio}",
            dados_antigos=dados_equipamento
        )
        
        db.session.delete(equipamento)
        db.session.commit()
        return jsonify({'mensagem': 'Equipamento deletado'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@app.route('/api/equipamentos/<int:id>', methods=['PUT', 'OPTIONS'])
@token_required
def atualizar_equipamento(id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        equipamento = Equipamento.query.get(id)
        if not equipamento:
            return jsonify({'erro': 'Equipamento não encontrado'}), 404
        
        dados_antigos = equipamento.to_dict()
        dados = request.get_json()
        
        # Campos que podem ser atualizados
        campos_permitidos = ['local', 'tipo_equipamento', 'defeito', 
                           'observacoes', 'prioridade', 'status']
        
        campos_alterados = []
        for campo in campos_permitidos:
            if campo in dados and dados[campo] != getattr(equipamento, campo):
                campos_alterados.append(campo)
                setattr(equipamento, campo, dados[campo])
        
        if campos_alterados:
            # Registrar atualização
            registrar_log(
                acao='UPDATE',
                entidade='equipamento',
                entidade_id=id,
                descricao=f"Equipamento #{id} atualizado: {', '.join(campos_alterados)}",
                dados_antigos=dados_antigos,
                dados_novos=equipamento.to_dict()
            )
        
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Equipamento atualizado com sucesso',
            'equipamento': equipamento.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ==================== ROTAS DE UNIDADES ====================

@app.route('/api/unidades', methods=['GET', 'OPTIONS'])
@token_required
def listar_unidades():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        unidades = Unidade.query.filter_by(ativo=True).order_by(Unidade.nome).all()
        return jsonify([u.to_dict() for u in unidades])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/unidades/<int:id>', methods=['GET', 'OPTIONS'])
@token_required
def buscar_unidade(id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        unidade = Unidade.query.get(id)
        if not unidade:
            return jsonify({'erro': 'Unidade não encontrada'}), 404
        return jsonify(unidade.to_dict())
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/unidades', methods=['POST', 'OPTIONS'])
@token_required
def criar_unidade():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        dados = request.get_json()
        
        if not dados or 'nome' not in dados:
            return jsonify({'erro': 'Nome da unidade é obrigatório'}), 400
        
        unidade = Unidade(
            nome=dados['nome'],
            telefone=dados.get('telefone', '')
        )
        
        db.session.add(unidade)
        db.session.flush()
        
        # Registrar criação
        registrar_log(
            acao='CREATE',
            entidade='unidade',
            entidade_id=unidade.id,
            descricao=f"Unidade criada: {unidade.nome}",
            dados_novos=unidade.to_dict()
        )
        
        db.session.commit()
        
        return jsonify(unidade.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ==================== ROTAS DA API - LOGS ====================

@app.route('/api/logs', methods=['GET', 'OPTIONS'])
@token_required
def listar_logs():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # Verificar se é admin (apenas admin pode ver logs)
        if request.usuario.usuario != 'admin':
            return jsonify({'erro': 'Acesso negado'}), 403
            
        logs = Log.query.order_by(Log.created_at.desc()).limit(5000).all()
        return jsonify([l.to_dict() for l in logs])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/logs/estatisticas', methods=['GET', 'OPTIONS'])
@token_required
def estatisticas_logs():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        if request.usuario.usuario != 'admin':
            return jsonify({'erro': 'Acesso negado'}), 403
            
        hoje = datetime.utcnow().date()
        
        stats = {
            'total': Log.query.count(),
            'hoje': Log.query.filter(db.func.date(Log.created_at) == hoje).count(),
            'por_acao': {
                'CREATE': Log.query.filter_by(acao='CREATE').count(),
                'UPDATE': Log.query.filter_by(acao='UPDATE').count(),
                'DELETE': Log.query.filter_by(acao='DELETE').count(),
                'MOVE': Log.query.filter_by(acao='MOVE').count(),
                'LOGIN': Log.query.filter_by(acao='LOGIN').count(),
                'LOGIN_FAILED': Log.query.filter_by(acao='LOGIN_FAILED').count()
            }
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ==================== ROTA PARA LOGOUT ====================

@app.route('/logout')
def logout():
    if 'usuario_id' in session:
        registrar_log(
            acao='LOGOUT',
            entidade='usuario',
            entidade_id=session['usuario_id'],
            descricao=f"Usuário {session.get('usuario_nome')} fez logout"
        )
    session.clear()
    return redirect('/login')

# ==================== INICIALIZAÇÃO ====================
if __name__ == '__main__':
    app.run(debug=True, port=5000)