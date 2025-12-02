import google.generativeai as genai
import os
from dotenv import load_dotenv

# Carrega a chave do arquivo .env
load_dotenv()

api_key = os.environ.get('GEMINI_API_KEY')

if not api_key:
    print("ERRO: Não foi possível encontrar a GEMINI_API_KEY.")
    print("Verifique se o seu arquivo .env está no lugar certo e com o conteúdo correto.")
else:
    try:
        genai.configure(api_key=api_key)

        print("Buscando modelos disponíveis para sua chave de API...")
        print("=" * 50)

        model_list = list(genai.list_models())

        if not model_list:
            print("Nenhum modelo encontrado. Isso pode indicar um problema com a chave ou com o projeto Google AI.")
            print("Verifique se a 'Generative Language API' está ativada no seu projeto no Google Cloud.")
        else:
            for m in model_list:
                # Verifica se o modelo suporta o método que estamos tentando usar
                if 'generateContent' in m.supported_generation_methods:
                    print(f"✅ Modelo compatível encontrado: '{m.name}'")

        print("=" * 50)
        print("Teste concluído.")

    except Exception as e:
        print(f"\nOcorreu um erro ao tentar acessar a API: {e}")
        print("Isso geralmente indica um problema com a chave de API ou com a configuração do projeto no Google Cloud.")