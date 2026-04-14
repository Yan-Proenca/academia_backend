from flask import Flask, jsonify, request
import firebase_admin
from firebase_admin import credentials, firestore
from auth import token_obrigatorio, gerar_token
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv
from datetime import datetime
from flasgger import Swagger

load_dotenv()

app = Flask(__name__)
# Versão do OPEN API
app.config['SWAGGER']= {
    'openapi':'3.0.0'
}
# Chamar o OPENAPI para o código
swagger = Swagger(app, template_file='openapi.yaml')

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
CORS(app, origins="*")

ADM_USUARIO = os.getenv("ADM_USUARIO")
ADM_SENHA = os.getenv("ADM_SENHA")

if os.getenv("VERCEL"):
    #ONLINE NA VERCEL
    cred = credentials.Certificate(json.loads(os.getenv("FIREBASE_CREDENTIALS")))
else:
    # LOCAL
    cred = credentials.Certificate("firebase.json") 

# ==========================
# Firebase
# ==========================

firebase_admin.initialize_app(cred)
db = firestore.client()

# ==========================
# FUNÇÃO VALIDAR CPF
# ==========================
def cpf_valido(cpf):
    cpf = ''.join(filter(str.isdigit, cpf))

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    dig1 = (soma * 10 % 11) % 10

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    dig2 = (soma * 10 % 11) % 10

    return cpf[-2:] == f"{dig1}{dig2}"

# ==========================
# ROTAS
# ==========================

@app.route("/", methods=['GET'])
def root():
    return jsonify({"api": "Sistema de Catraca"}), 200


@app.route("/login", methods=['POST'])
def login():
    dados = request.get_json()

    if not dados:
        return jsonify({"error": "Envie os dados para login"}), 400

    usuario = dados.get("usuario")
    senha = dados.get("senha")

    if not usuario or not senha:
        return jsonify({"error": "Usuário e senha são obrigatórios!"}), 400

    if usuario == ADM_USUARIO and senha == ADM_SENHA:
        token = gerar_token(usuario)
        return jsonify({
            "message": "Login realizado com sucesso",
            "token": token
        }), 200

    return jsonify({"error": "Usuário ou senha inválidos"}), 401


@app.route("/alunos", methods=['GET'])
def listar_alunos():
    alunos = [doc.to_dict() for doc in db.collection('alunos').stream()]
    return jsonify(alunos), 200


@app.route("/alunos", methods=['POST'])
@token_obrigatorio
def post_alunos():

    dados = request.get_json()

    if not dados or "nome" not in dados or "cpf" not in dados or "status" not in dados:
        return jsonify({"error": "Dados inválidos ou incompletos"}), 400

    cpf = dados["cpf"]

    # Validar CPF
    if not cpf_valido(cpf):
        return jsonify({"error": "CPF inválido"}), 400

    status = dados["status"].lower()

    if status not in ["ativo", "bloqueado"]:
        return jsonify({"error": "Status inválido"}), 400

    try:
        alunos_ref = db.collection("alunos")

        # Verificar CPF único
        query = alunos_ref.where("cpf", "==", cpf).stream()
        for doc in query:
            return jsonify({"error": "CPF já cadastrado"}), 400

        contador_ref = db.collection("contador").document("alunos")

        @firestore.transactional
        def gerar_id(transaction):
            snapshot = contador_ref.get(transaction=transaction)

            if not snapshot.exists:
                # cria o contador se não existir
                transaction.set(contador_ref, {"ultimo_id": 1})
                return 1

            ultimo_id = snapshot.to_dict().get("ultimo_id", 0)
            novo_id = ultimo_id + 1

            transaction.update(contador_ref, {
                "ultimo_id": novo_id
            })

            return novo_id

        transaction = db.transaction()
        novo_id = gerar_id(transaction)


        aluno_ref = alunos_ref.document(str(novo_id))

        aluno_ref.set({
            "id": novo_id,
            "nome": dados["nome"],
            "cpf": cpf,
            "status": status
        })

        return jsonify({
            "message": "Aluno cadastrado com sucesso!",
            "id": novo_id
        }), 201

    except Exception as e:
        return jsonify({
            "error": "Erro ao cadastrar aluno",
            "details": str(e)
        }), 500

@app.route("/catraca", methods=['GET'])
def catraca_json():

    dados = request.get_json()

    if not dados or "cpf" not in dados:
        return jsonify({"error": "CPF não informado"}), 400

    cpf = dados.get("cpf")

    # Validar CPF real
    if not cpf_valido(cpf):
        return jsonify({
            "status": "BLOQUEADO",
            "motivo": "CPF inválido"
        }), 400

    try:
        alunos_ref = db.collection('alunos')
        query = alunos_ref.where('cpf', '==', cpf).limit(1).stream()

        aluno_doc = None
        for doc in query:
            aluno_doc = doc
            break

        # CPF não encontrado
        if not aluno_doc:
            return jsonify({
                "status": "BLOQUEADO",
                "motivo": "Aluno não encontrado"
            }), 404

        aluno = aluno_doc.to_dict()
        status = aluno.get('status', '').lower()

        if status == 'ativo':
            resultado = "LIBERADO"
            codigo = 200
        else:
            resultado = "BLOQUEADO"
            codigo = 403

        # Log da catraca
        db.collection("logs_catraca").add({
            "cpf": cpf,
            "status": resultado,
            "data": datetime.utcnow()
        })

        return jsonify({"status": resultado}), codigo

    except Exception as e:
        return jsonify({
            "error": "Erro na validação da catraca",
            "details": str(e)
        }), 500


# ==========================
# GET, PUT PATCH e DELETE
# ==========================

# CONSULTA COM ALUNO
@app.route("/alunos/<int:id>", methods=['GET'])
@token_obrigatorio
def buscar_aluno(id):
    try:
        aluno_ref = db.collection("alunos").document(str(id))
        doc = aluno_ref.get()

        if not doc.exists:
            return jsonify({"error": "Aluno não encontrado"}), 404

        return jsonify(doc.to_dict()), 200

    except Exception as e:
        return jsonify({
            "error": "Erro ao buscar aluno",
            "details": str(e)
        }), 500
    

# CONSULTA COM CPF
@app.route("/alunos/cpf/<cpf>", methods=['GET'])
def buscar_por_cpf(cpf):
    try:
        alunos_ref = db.collection("alunos")
        query = alunos_ref.where("cpf", "==", cpf).limit(1).stream()

        for doc in query:
            return jsonify(doc.to_dict()), 200

        return jsonify({"error": "Aluno não encontrado"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# EDIT ALUNO
@app.route("/alunos/<int:id>", methods=['PUT'])
@token_obrigatorio
def atualizar_aluno(id):

    dados = request.get_json()

    if not dados:
        return jsonify({"error": "Dados não enviados"}), 400

    try:
        aluno_ref = db.collection("alunos").document(str(id))
        doc = aluno_ref.get()

        if not doc.exists:
            return jsonify({"error": "Aluno não encontrado"}), 404

        # Atualizações permitidas
        update_data = {}

        if "nome" in dados:
            update_data["nome"] = dados["nome"]

        if "status" in dados:
            status = dados["status"].lower()
            if status not in ["ativo", "bloqueado"]:
                return jsonify({"error": "Status inválido"}), 400
            update_data["status"] = status

        if "cpf" in dados:
            if not cpf_valido(dados["cpf"]):
                return jsonify({"error": "CPF inválido"}), 400
            update_data["cpf"] = dados["cpf"]

        aluno_ref.update(update_data)

        return jsonify({"message": "Aluno atualizado com sucesso"}), 200

    except Exception as e:
        return jsonify({
            "error": "Erro ao atualizar aluno",
            "details": str(e)
        }), 500
    
# EDITAR PARCIALMENTE ALUNO (PATCH)
@app.route("/alunos/<int:id>", methods=['PATCH'])
@token_obrigatorio
def editar_parcial_aluno(id):
    dados = request.get_json()

    if not dados:
        return jsonify({"error": "Nenhum dado fornecido para atualização"}), 400

    try:
        aluno_ref = db.collection("alunos").document(str(id))
        doc = aluno_ref.get()

        if not doc.exists:
            return jsonify({"error": "Aluno não encontrado"}), 404

        update_data = {}

        # Atualiza apenas se a chave existir no JSON enviado
        if "nome" in dados:
            update_data["nome"] = dados["nome"]

        if "status" in dados:
            status = dados["status"].lower()
            if status not in ["ativo", "bloqueado"]:
                return jsonify({"error": "Status inválido. Use 'ativo' ou 'bloqueado'"}), 400
            update_data["status"] = status

        if "cpf" in dados:
            cpf = dados["cpf"]
            if not cpf_valido(cpf):
                return jsonify({"error": "CPF inválido"}), 400
            
            # Opcional: Verificar se o novo CPF já pertence a outro aluno
            query = db.collection("alunos").where("cpf", "==", cpf).stream()
            for d in query:
                if d.id != str(id):
                    return jsonify({"error": "Este CPF já está cadastrado em outro usuário"}), 400
            
            update_data["cpf"] = cpf

        if not update_data:
            return jsonify({"error": "Nenhum campo válido para atualização foi enviado"}), 400

        aluno_ref.update(update_data)

        return jsonify({
            "message": "Aluno atualizado parcialmente com sucesso",
            "campos_alterados": list(update_data.keys())
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Erro ao atualizar parcialmente o aluno",
            "details": str(e)
        }), 500

# DELETE ALUNO
@app.route("/alunos/<int:id>", methods=['DELETE'])
@token_obrigatorio
def deletar_aluno(id):
    try:
        aluno_ref = db.collection("alunos").document(str(id))
        doc = aluno_ref.get()

        if not doc.exists:
            return jsonify({"error": "Aluno não encontrado"}), 404

        aluno_ref.delete()

        return jsonify({"message": "Aluno deletado com sucesso"}), 200

    except Exception as e:
        return jsonify({
            "error": "Erro ao deletar aluno",
            "details": str(e)
        }), 500

# ==========================
# ERROS
# ==========================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Rota não encontrada!"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Erro interno do servidor!"}), 500


# ==========================
# RUN
# ==========================

if __name__ == "__main__":
    app.run(debug=True)