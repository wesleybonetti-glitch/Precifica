from openai import OpenAI
import os

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
print("Script ilustrativo para limpeza de vector stores. Confira a doc da sua versão da SDK.")
