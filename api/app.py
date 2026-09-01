from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
from dotenv import load_dotenv
import google.generativeai as genai
from api.utils.embedding_manager import EmbeddingManager

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

api = Flask(__name__)
CORS(api)
api.secret_key = os.urandom(24)  # Necessário para usar sessions

# Configurar a chave da API do Google
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY não encontrada nas variáveis de ambiente")

# Configuração do modelo Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Configurações de segurança corretas
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]

# Configuração do modelo
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

# Inicialização do modelo
model = genai.GenerativeModel(
    model_name="gemini-3.6-flash",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

# Instância global do EmbeddingManager
embedding_manager = EmbeddingManager(GOOGLE_API_KEY)

# Dicionário para armazenar as sessões de chat
chat_sessions = {}


@api.route("/")
def index():
    # Gera um ID de sessão único se não existir
    if "chat_id" not in session:
        session["chat_id"] = os.urandom(16).hex()
    return render_template("index.html")


@api.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.json["message"]
        chat_id = session.get("chat_id")
        bot_response_text = ""

        # Inicializa uma nova sessão de chat se necessário
        if chat_id not in chat_sessions:
            chat = model.start_chat(history=[])
            chat_sessions[chat_id] = chat

            # Busca o contexto relevante para a introdução
            context = embedding_manager.search_query("introdução")

            # Prompt inicial com instruções e contexto
            # Prompt inicial com instruções e contexto
            initial_prompt = f"""Você é um especialista no assunto descrito no seguinte contexto: 

                        A EPI-DATA é uma plataforma digital de **mapeamento epidemiológico e gestão de dados de saúde**. Seu objetivo é **facilitar o monitoramento de endemias e o controle de saúde pública**, oferecendo um sistema seguro e eficiente para agentes de saúde, gestores e pesquisadores analisarem dados estratificados. A plataforma segue as diretrizes de vigilância em saúde e boas práticas de segurança de dados, e está sendo constantemente aprimorada para oferecer análises e processamento rápido de informações.

                        Você é um chatbot treinado para atuar como **assistente virtual de suporte dentro do sistema EPI-DATA**, auxiliando usuários (profissionais de saúde, pesquisadores e administradores) com dúvidas técnicas, problemas de acesso, navegação na plataforma, importação de arquivos DBF, visualização de notificações de pacientes, filtros de agravos, configurações de conta e uso de recursos gerais da plataforma.

                        Seu papel é fornecer **respostas claras, precisas e objetivas**, sempre com foco em resolver os problemas dos usuários ou direcioná-los corretamente. Você deve:

                        - Entender o funcionamento da plataforma EPI-DATA (listagem de notificações de endemias, dashboards epidemiológicos, filtros geográficos e controle de agravos).
                        - Ser capaz de simular interações humanas cordiais e respeitosas, com tom amigável e profissional.
                        - Responder em **português brasileiro**.
                        - Sugerir soluções passo a passo, quando possível, especialmente para processos de upload e filtragem de dados.
                        - Encaminhar para o suporte técnico humano (vigilanciafloriano@gmail.com), caso o problema seja muito específico ou envolva falha no banco de dados.

                        Lembre-se: você é parte essencial da experiência de suporte da EPI-DATA e atua para garantir que todos os usuários tenham uma jornada fluida, segura e bem assistida dentro da plataforma de análise de saúde.

                        A partir de agora, responda sempre como se estivesse dentro do sistema da EPI-DATA, pronto para ajudar. 

                        {context} 

                        Instruções importantes: 
                        1. Baseie suas respostas principalmente no contexto fornecido. 
                        2. Você pode adicionar informações complementares sobre o tema, desde que sejam precisas e relevantes. 
                        3. Se a pergunta fugir do tema do contexto, gentilmente redirecione para o assunto principal. 
                        4. Use markdown quando apropriado para melhorar a legibilidade. 
                        5. Mantenha suas respostas organizadas e fáceis de ler. 
                        6. Responda sempre em português.

                        Por favor, confirme que entendeu estas instruções respondendo com uma breve saudação de boas-vindas como assistente da EPI-DATA."""

            # Envia o prompt inicial para obter a saudação
            initial_response = chat.send_message(initial_prompt)
            bot_response_text += (
                initial_response.text + "\\n\\n"
            )  # Acumula a saudação inicial

        # Continua o chat com a mensagem do usuário
        chat = chat_sessions[chat_id]
        response = chat.send_message(user_message)
        bot_response_text += response.text  # Adiciona a resposta da pergunta atual

        return jsonify({"response": bot_response_text, "status": "success"})

    except Exception as e:
        print(f"Erro ao processar mensagem: {str(e)}")
        return (
            jsonify(
                {
                    "response": "Desculpe, ocorreu um erro ao processar sua mensagem.",
                    "status": "error",
                }
            ),
            500,
        )


# Rota para limpar o histórico do chat
@api.route("/clear-chat", methods=["POST"])
def clear_chat():
    try:
        if "chat_id" in session:
            chat_id = session["chat_id"]
            if chat_id in chat_sessions:
                del chat_sessions[chat_id]
        session.pop("chat_id", None)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    api.run(debug=True)
