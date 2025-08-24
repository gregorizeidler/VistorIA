import os
from fastapi import UploadFile
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def transcribe_audio(file: UploadFile) -> str:
    """Transcreve áudio para texto usando Whisper"""
    data = await file.read()
    from tempfile import NamedTemporaryFile
    
    with NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    
    try:
        with open(tmp_path, 'rb') as f:
            transcription = await _client.audio.transcriptions.create(
                model='whisper-1', 
                file=f,
                language='pt'
            )
        return transcription.text or ''
    finally:
        os.unlink(tmp_path)

async def analyze_image(file: UploadFile, prompt: str) -> str:
    """Analisa imagem usando GPT-4 Vision"""
    data = await file.read()
    import base64
    
    b64 = base64.b64encode(data).decode('utf-8')
    
    response = await _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": f"Você é um especialista em vistoria imobiliária. {prompt} Seja detalhado sobre o estado de conservação."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{file.content_type or 'image/jpeg'};base64,{b64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=300
    )
    return response.choices[0].message.content or ""

async def summarize_text(text: str) -> str:
    """Resume texto de observações de vistoria"""
    response = await _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", 
                "content": "Você é um assistente especializado em resumir observações de vistoria imobiliária. Seja conciso, objetivo e mantenha informações importantes sobre o estado dos itens."
            },
            {
                "role": "user", 
                "content": f"Resuma esta observação de vistoria de forma clara e profissional: {text}"
            }
        ],
        max_tokens=150
    )
    return response.choices[0].message.content or ""