from flask import Flask, render_template, request, jsonify
import base64
import requests
from io import BytesIO
from PIL import Image
import json
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Vision destekleyen popüler OpenRouter modelleri
VISION_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-opus",
    "anthropic/claude-3-sonnet",
    "anthropic/claude-3-haiku",
    "google/gemini-pro-1.5",
    "google/gemini-flash-1.5",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "openai/gpt-4-turbo",
    "meta-llama/llama-3.2-90b-vision-instruct",
    "meta-llama/llama-3.2-11b-vision-instruct",
    "qwen/qwen-2-vl-72b-instruct",
]

def analyze_image(image, api_key, model, system_prompt, user_prompt):
    """
    OpenRouter API kullanarak görseli analiz eder
    """
    if not api_key:
        return {"error": "Lütfen OpenRouter API key giriniz!"}

    if not user_prompt:
        user_prompt = "Bu görseli detaylı bir şekilde analiz et ve açıkla."

    try:
        # Görseli base64'e çevir
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # OpenRouter API isteği
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "Image Analyzer"
        }

        # Mesajları hazırla
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_base64}"
                    }
                }
            ]
        })

        payload = {
            "model": model,
            "messages": messages
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()

        # Yanıtı al
        if 'choices' in result and len(result['choices']) > 0:
            analysis_text = result['choices'][0]['message']['content']
            return {"success": True, "analysis": analysis_text}
        else:
            return {"error": f"Hata: Beklenmeyen yanıt formatı\n{json.dumps(result, indent=2)}"}

    except requests.exceptions.RequestException as e:
        return {"error": f"API Hatası: {str(e)}\n\nLütfen API key ve model seçimini kontrol edin."}
    except Exception as e:
        return {"error": f"Hata: {str(e)}"}


@app.route('/')
def index():
    return render_template('index.html', models=VISION_MODELS)


@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Form verilerini al
        api_key = request.form.get('api_key')
        model = request.form.get('model')
        system_prompt = request.form.get('system_prompt', '')
        user_prompt = request.form.get('user_prompt', 'Bu görseli detaylı bir şekilde analiz et ve açıkla.')

        # Görseli al
        if 'image' not in request.files:
            return jsonify({"error": "Lütfen bir görsel yükleyin!"})

        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "Lütfen bir görsel seçin!"})

        # Görseli aç
        image = Image.open(file.stream)

        # Analiz et
        result = analyze_image(image, api_key, model, system_prompt, user_prompt)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Bir hata oluştu: {str(e)}"})


if __name__ == '__main__':
    # templates klasörünü oluştur
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, host='127.0.0.1', port=5000)
