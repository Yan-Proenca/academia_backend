# 🏋️‍♂️ Academia Ratão - Backend & API

Este repositório contém a inteligência central (Backend) do ecossistema Academia Ratão. A API foi desenvolvida para gerenciar de forma segura a autenticação de administradores e o controle de acesso dos alunos, servindo como a ponte de dados para as interfaces de gerenciamento e de acesso físico.

---

## 👤 Desenvolvedor
* **Yan Matheus Proenca Camargo**

---

## 🔗 Interfaces Conectadas (Frontend)

Este backend alimenta as seguintes aplicações:

* **[Painel Administrativo](https://dashboard-admin-gym-kshz.vercel.app/)**: Interface para gestão de alunos, matrículas e visualização de estatísticas.
* **[Sistema de Catraca](https://catraca-gym.vercel.app/)**: Interface de autoatendimento para validação de entrada de alunos via CPF.

---

## 🚀 Tecnologias e Frameworks

* **Python (Flask):** Micro-framework utilizado para construção da API RESTful.
* **Firebase Admin SDK:** Integração com Google Firebase para armazenamento de dados e autenticação.
* **Flask-CORS:** Configuração de permissões para permitir o acesso das interfaces Frontend citadas acima.
* **PyJWT:** Implementação de tokens de segurança (JSON Web Tokens) para proteção das rotas administrativas.
* **Pyrebase:** Utilizado para a comunicação simplificada com o banco de dados em tempo real do Firebase.

---

## 🛠️ Funcionalidades do Sistema

* **Autenticação JWT:** Sistema de login que gera tokens temporários para garantir que apenas administradores autorizados acessem os dados.
* **Gerenciamento de Alunos:** Endpoints preparados para operações de Criação, Leitura, Atualização e Exclusão (CRUD) de registros.
* **Validação de Catraca:** Lógica de verificação de status (Ativo/Bloqueado) para controle de entrada física.
* **Documentação OpenAPI:** O projeto conta com um arquivo de especificação `openapi.yaml` para facilitar testes e integrações.

---

## 📂 Estrutura de Arquivos

* `app.py`: Ponto de entrada da aplicação e definição das rotas da API.
* `auth.py`: Lógica de criptografia, geração e validação de tokens de segurança.
* `firebase.json`: Configurações de credenciais e conexão com o banco de dados.
* `openapi.yaml`: Documentação técnica detalhada de todos os endpoints.
* `requirements.txt`: Lista de dependências necessárias para rodar o projeto.

---

## 🔧 Como Instalar e Rodar

1. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
