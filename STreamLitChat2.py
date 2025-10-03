import os
import streamlit as st
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from PIL import Image
from io import BytesIO
import base64
from openai import OpenAI

# MODELO DO CHAT TEVE QUE SER SEPARADO DO MODELO DE IMAGEM POIS A API DA GROQ ESTÁ COM PROBLEMAS
api_key = st.secrets["GROQ_API_KEY"]
os.environ["GROQ_API_KEY"] = api_key

chat = ChatGroq(model="llama-3.3-70b-versatile")

def resposta_do_bot(lista_mensagens):
    template = ChatPromptTemplate.from_messages(
        [('system', 'Você é um assistente que responde de forma clara e objetiva, sempre ajudando o usuário com suas dúvidas.') ] + lista_mensagens
    )
    chain = template | chat
    return chain.invoke({}).content

# TENTATIVA SEM SABER MUITO DE FRONT END NO STREAMLIT... USANDO TUTORIAL BÁSICO.

def principal():
    cor_fundo_titulo = "#2A397C"  
    cor_usuario = "#5338B4"  
    cor_bot = "#3C3297"  

    st.markdown(f"<div style='background-color:{cor_fundo_titulo}; padding: 20px;'><h1 style='color: white;'>Roberto o Bot - Multimodal UNA 2025</h1></div>", unsafe_allow_html=True)
    st.write("Bem-vindo ao **Roberto o BOT**! Envie uma imagem ou uma mensagem e eu te ajudo!")

    # SALVANDO O HISTORICO DE MENSAGENS NA SESSÃO
    if 'mensagens' not in st.session_state:
        st.session_state['mensagens'] = []

    for msg in st.session_state['mensagens']:
        if msg[0] == 'user':
            st.markdown(f"<div style='background-color:{cor_usuario}; padding: 10px; margin: 5px 0; border-radius: 8px;'><strong>Você:</strong> {msg[1]}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background-color:{cor_bot}; padding: 10px; margin: 5px 0; border-radius: 8px;'><strong>Bot:</strong> {msg[1]}</div>", unsafe_allow_html=True)

    # TRAVANDO O INPUT NA EMBAIXO DA TELA
    st.markdown("""
        <style>
            .css-1v3fvcr { position: fixed; bottom: 0; width: 100%; background-color: #fff; padding: 10px; box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1); z-index: 100; }
            .css-1s12jw9 { margin-bottom: 0; }
            .css-1v3fvcr .stTextInput input { padding-left: 10px; }
        </style>
    """, unsafe_allow_html=True)

    # INPUT DE TEXTO DO USUÁRIO 
    user_input = st.text_input("Digite sua mensagem:", "", key="input_usuario", max_chars=300)

    if user_input:  # salvando mensagens no histórico
        st.session_state['mensagens'].append(('user', user_input))  
        resposta = resposta_do_bot(st.session_state['mensagens'])  
        st.session_state['mensagens'].append(('assistant', resposta))  

        st.markdown(f"<div style='background-color:{cor_bot}; padding: 10px; margin: 5px 0; border-radius: 8px;'><strong>Bot:</strong> {resposta}</div>", unsafe_allow_html=True)

    # TENTANDO CONSERTAR O BOTÃO DE IMAGEM
    col1, col2 = st.columns([3, 1])

    # INPUT DE IMAGEM DO USUÁRIO PARA ANALISAR
    with col2:
        uploaded_image = st.file_uploader("", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

    if uploaded_image is not None:
        st.image(uploaded_image, caption="Imagem carregada", use_container_width=True)
        st.write("Analisando a imagem...") 
        resultado = analisar_imagem(uploaded_image)
        st.write("Resultado da Análise:")
        st.write(resultado)

# ANALISANDO A IMAGEM QUE O USUARIO MANDOU... ( CÓDIGO ENSINADO EM SALA DE AULA )
def analisar_imagem(image_path):
    try:
        image = Image.open(image_path)
        image = image.resize((800, 600))
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    except FileNotFoundError:
        return "Erro: Imagem não encontrada no caminho especificado."
    except Exception as e:
        return f"Erro ao processar a imagem: {str(e)}"

    instrucoes = """
        Analise a imagem fornecida de forma detalhada e forneça uma descrição completa do seu conteúdo. A descrição deve incluir:
        1. **Objetos e elementos visíveis**: Identifique e descreva todos os objetos, pessoas, animais, paisagens ou elementos presentes na imagem.
        2. **Cenário e contexto**: Se a imagem se passar em um ambiente específico (ex: praia, cidade, floresta, ambiente interno, etc.), descreva o local e a atmosfera.
        3. **Ações ou interações**: Caso haja pessoas ou animais, descreva qualquer ação ou interação que esteja acontecendo (ex: uma pessoa sorrindo, uma pessoa sentada em uma cadeira, animais brincando, etc.).
        4. **Composição e detalhes visuais**: Analise a disposição dos elementos na imagem, como as cores predominantes, texturas, iluminação, perspectiva e outros detalhes visuais.
        5. **Qualquer outro aspecto relevante**: Se houver algo significativo na imagem, como símbolos, textos, ou objetos que se destaquem, mencione-os e forneça uma interpretação.
        6. **Caso a imagem contenha comida, adicione uma estimativa nutricional, incluindo: - Calorias  - Macronutrientes (carboidratos, proteínas, gorduras) 
        - (Se possível) ingredientes ou categorias de alimentos visíveis.
        
        A descrição deve ser clara, objetiva e fornecer informações ricas sobre o que está acontecendo ou sendo mostrado na imagem.
        Responda em português.
    """

    try:
        client = OpenAI(
            api_key=st.secrets["GROQ_API_KEY"],  # Usando a chave da API do Streamlit Secrets
            base_url='https://api.groq.com/openai/v1'
        )
        message = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instrucoes},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]
            }
        ]

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=message,
            temperature=0.1,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro ao chamar a API da Groq: {str(e)}"

if __name__ == "__main__":
    principal()
