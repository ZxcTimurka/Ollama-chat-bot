from flask import Flask, render_template, request, jsonify
import os
from openai import OpenAI
from langchain_ollama import OllamaLLM

app = Flask(__name__, template_folder='templates') # Added template_folder
app.secret_key = os.urandom(24)

# Configuration
openai_model_name = "gpt-4o"
openai_base_url = "https://models.inference.ai.azure.com"
openai_api_key = "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"

ollama_model_name = "llama3.1"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_message = request.form["user_message"]
        selected_provider = request.form["provider"]
        selected_model = request.form["model_name"]

        if selected_provider == "OpenAI":
            client = OpenAI(api_key=openai_api_key, base_url=openai_base_url)
            llm = client.Completion.create(model=openai_model_name, prompt=user_message, max_tokens=150)
            ai_response = llm.choices[0].text.strip()

        elif selected_provider == "Ollama":
            llm = OllamaLLM(model=selected_model)
            ai_response = llm(user_message)
        else:
            return jsonify({"error": "Invalid provider selected"}), 400

        try:
            return jsonify({"ai_response": ai_response})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return render_template("index.html", openai_model_name=openai_model_name, 
                           openai_base_url=openai_base_url, openai_api_key=openai_api_key,
                           ollama_model_name=ollama_model_name)

if __name__ == "__main__":
    app.run(debug=True)