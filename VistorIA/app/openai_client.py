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
    """Analisa imagem usando GPT-5 mini Vision"""
    try:
        # Ler dados do arquivo
        if hasattr(file, 'file') and hasattr(file.file, 'read'):
            # É um BytesIO ou arquivo já aberto (MockUploadFile)
            file.file.seek(0)
            data = file.file.read()
            content_type = getattr(file, 'content_type', 'image/jpeg')
        elif hasattr(file, 'read'):
            # É um UploadFile do FastAPI
            if hasattr(file.read, '__await__'):
                data = await file.read()
            else:
                data = file.read()
            content_type = getattr(file, 'content_type', 'image/jpeg')
        else:
            data = file
            content_type = 'image/jpeg'
        
        # Garantir que data é bytes
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif not isinstance(data, bytes):
            data = bytes(data)
        
        import base64
        b64 = base64.b64encode(data).decode('utf-8')
        
        # Verificar se API key está configurada
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "sua_chave_openai_aqui" or api_key.strip() == "":
            raise ValueError("OPENAI_API_KEY não configurada. Configure sua chave no arquivo .env")
        
        # Usar gpt-4o-mini-2024-07-18 que é o snapshot específico do modelo
        response = await _client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
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
                                "url": f"data:{content_type};base64,{b64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"Erro em analyze_image: {e}")
        import traceback
        traceback.print_exc()
        raise

async def summarize_text(text: str) -> str:
    """Resume texto de observações de vistoria"""
    response = await _client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
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