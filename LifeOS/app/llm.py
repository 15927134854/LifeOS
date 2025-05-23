from langchain_community.llms import Ollama

def call_llm(prompt):
    llm = Ollama(model="your_model_name")
    response = llm(prompt)
    return response