import cv2
import numpy as np
import pytesseract
import speech_recognition as sr
from ultralytics import YOLO
import base64
import io
import os
import json
import re
from PIL import Image
from typing import List, Dict, Optional, Tuple
from fastapi import UploadFile
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Caregar modelo YOLO para detecção de objetos (será baixado automaticamente)
# Usaremos YOLOv8n (nano) para ser mais rápido
try:
    yolo_model = YOLO('yolov8n.pt')
except:
    yolo_model = None
    print("YOLO model não disponível")

# Prompts especializados para análise de diferentes itens
SPECIALIZED_PROMPTS = {
    "torneira": """Analise esta torneira detalhadamente e identifique:
1. Estado geral (novo, usado, danificado)
2. Presença de vazamentos ou goteiras
3. Sinais de ferrugem ou corrosão
4. Acúmulo de calcário ou sujeira
5. Funcionamento aparente
6. Necessidade de reparo ou substituição
Seja específico sobre o que observa.""",

    "piso": """Analise este piso detalhadamente:
1. Tipo de material (cerâmica, porcelanato, laminado, etc.)
2. Estado de conservação geral
3. Presença de rachaduras, trincas ou quebras
4. Manchas, riscos ou desgaste
5. Nivelamento (se aparenta estar nivelado)
6. Rejunte (estado de conservação)
7. Necessidade de reparo, limpeza ou troca""",

    "parede": """Analise esta parede cuidadosamente:
1. Estado da pintura (nova, desbotada, descascando)
2. Presença de manchas de umidade ou infiltração
3. Rachaduras, furos ou danos estruturais
4. Sinais de mofo ou fungos
5. Limpeza geral
6. Tipo de acabamento
7. Necessidade de reparo ou repintura""",

    "vaso sanitário": """Analise este vaso sanitário:
1. Estado geral de conservação e limpeza
2. Funcionamento da descarga
3. Presença de vazamentos ou rachaduras
4. Estado da louça (manchas, riscos)
5. Fixação adequada ao piso
6. Acessórios (assento, tampa) e seu estado
7. Necessidade de limpeza, reparo ou substituição""",

    "pia": """Analise esta pia detalhadamente:
1. Material (inox, granito, mármore, cerâmica)
2. Estado de conservação geral
3. Presença de riscos, manchas ou danos
4. Funcionamento do ralo
5. Estado da vedação com a bancada
6. Limpeza e higiene
7. Necessidade de reparo ou substituição""",

    "janela": """Analise esta janela:
1. Tipo de janela (alumínio, madeira, PVC)
2. Estado dos vidros (inteiros, trincados, limpos)
3. Funcionamento da abertura/fechamento
4. Estado da esquadria e vedação
5. Presença de ferrugem ou corrosão
6. Estado das travas e fechaduras
7. Necessidade de reparo ou substituição""",

    "porta": """Analise esta porta:
1. Material (madeira, metal, PVC)
2. Estado geral de conservação
3. Funcionamento das dobradiças
4. Estado da fechadura e chaves
5. Presença de riscos, furos ou danos
6. Alinhamento e vedação
7. Necessidade de reparo, ajuste ou substituição"""
}

# Mapeamento de objetos detectáveis
DETECTABLE_OBJECTS = {
    # Cozinha
    'sink': 'pia',
    'refrigerator': 'geladeira', 
    'oven': 'forno',
    'microwave': 'microondas',
    
    # Banheiro
    'toilet': 'vaso sanitário',
    
    # Geral
    'chair': 'cadeira',
    'dining table': 'mesa',
    'couch': 'sofá',
    'tv': 'televisão',
    'bed': 'cama'
}

async def enhanced_image_analysis(file: UploadFile, item_type: str = "geral") -> Dict:
    """Análise aprimorada de imagem com detecção de objetos e análise especializada"""
    try:
        # Ler imagem
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Detectar objetos se YOLO disponível
        detected_objects = []
        if yolo_model:
            detected_objects = detect_objects_in_image(image_data)
        
        # Análise especializada por IA
        prompt = SPECIALIZED_PROMPTS.get(item_type.lower(), "Descreva detalhadamente o estado deste item imobiliário.")
        ai_analysis = await analyze_image_with_specialized_prompt(file, prompt)
        
        # Determinar prioridade de reparo
        priority = determine_repair_priority(ai_analysis)
        
        return {
            "ai_analysis": ai_analysis,
            "detected_objects": detected_objects,
            "item_type": item_type,
            "repair_priority": priority,
            "specialized_analysis": True
        }
        
    except Exception as e:
        print(f"Erro na análise aprimorada: {e}")
        # Fallback para análise básica
        basic_analysis = await analyze_image_with_specialized_prompt(file, "Descreva o estado deste item.")
        return {
            "ai_analysis": basic_analysis,
            "detected_objects": [],
            "item_type": item_type,
            "repair_priority": "unknown",
            "specialized_analysis": False
        }

def detect_objects_in_image(image_data: bytes) -> List[Dict]:
    """Detecta objetos na imagem usando YOLO"""
    if not yolo_model:
        return []
    
    try:
        # Converter bytes para array numpy
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Detectar objetos
        results = yolo_model(image)
        
        detected = []
        for r in results:
            boxes = r.boxes
            if boxes is not None:
                for box in boxes:
                    # Obter classe e confiança
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    if conf > 0.5:  # Apenas detecções com confiança > 50%
                        class_name = yolo_model.names[cls]
                        portuguese_name = DETECTABLE_OBJECTS.get(class_name, class_name)
                        
                        detected.append({
                            "object": portuguese_name,
                            "confidence": round(conf, 2),
                            "english_name": class_name
                        })
        
        return detected
    except Exception as e:
        print(f"Erro na detecção de objetos: {e}")
        return []

async def analyze_image_with_specialized_prompt(file: UploadFile, prompt: str) -> str:
    """Análise de imagem com prompt especializado"""
    try:
        # Resetar posição do arquivo
        await file.seek(0)
        data = await file.read()
        b64 = base64.b64encode(data).decode('utf-8')
        
        # Usar gpt-4o-mini-2024-07-18 que é o snapshot específico do modelo
        response = await _client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": f"Você é um especialista em vistoria imobiliária. {prompt}"
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
            max_tokens=500
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"Erro na análise de imagem: {e}")
        return "Erro na análise da imagem"

def determine_repair_priority(analysis: str) -> str:
    """Determina prioridade de reparo baseado na análise"""
    analysis_lower = analysis.lower()
    
    # Palavras-chave para diferentes prioridades
    critical_keywords = ['vazamento', 'infiltração', 'rachadura estrutural', 'perigo', 'risco', 'quebrado', 'não funciona']
    high_keywords = ['danificado', 'substituição', 'troca necessária', 'reparo urgente', 'deteriorado']
    medium_keywords = ['desgaste', 'manchas', 'riscos', 'ajuste necessário', 'limpeza profunda']
    
    for keyword in critical_keywords:
        if keyword in analysis_lower:
            return 'critical'
    
    for keyword in high_keywords:
        if keyword in analysis_lower:
            return 'high'
    
    for keyword in medium_keywords:
        if keyword in analysis_lower:
            return 'medium'
    
    return 'low'

async def extract_text_from_document(file: UploadFile) -> Dict:
    """Extrai texto de documentos usando OCR"""
    try:
        image_data = await file.read()
        
        # Converter para imagem PIL
        image = Image.open(io.BytesIO(image_data))
        
        # Melhorar qualidade da imagem para OCR
        image = enhance_image_for_ocr(image)
        
        # Extrair texto usando Tesseract
        text = pytesseract.image_to_string(image, lang='por')
        
        # Tentar extrair informações específicas
        extracted_info = extract_document_info(text)
        
        return {
            "raw_text": text,
            "extracted_info": extracted_info,
            "success": True
        }
        
    except Exception as e:
        print(f"Erro no OCR: {e}")
        return {
            "raw_text": "",
            "extracted_info": {},
            "success": False,
            "error": str(e)
        }

def enhance_image_for_ocr(image: Image.Image) -> Image.Image:
    """Melhora qualidade da imagem para OCR"""
    try:
        # Converter para escala de cinza
        if image.mode != 'L':
            image = image.convert('L')
        
        # Converter para array numpy
        img_array = np.array(image)
        
        # Aplicar threshold para binarização
        _, thresh = cv2.threshold(img_array, 127, 255, cv2.THRESH_BINARY)
        
        # Remover ruído
        kernel = np.ones((1,1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        # Converter de volta para PIL
        enhanced = Image.fromarray(cleaned)
        return enhanced
        
    except Exception as e:
        print(f"Erro no enhancement da imagem: {e}")
        return image

def extract_document_info(text: str) -> Dict:
    """Extrai informações específicas de documentos"""
    import re
    
    info = {}
    
    # Padrões para extrair informações
    patterns = {
        'cpf': r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}',
        'rg': r'\d{1,2}\.?\d{3}\.?\d{3}-?[0-9X]',
        'telefone': r'\(?(\d{2})\)?\s*\d{4,5}-?\d{4}',
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'cep': r'\d{5}-?\d{3}',
        'nome': r'(?:NOME|Nome):\s*([A-ZÁÊÂÔÇÕ][a-záêâôçõ\s]+)'
    }
    
    for field, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            info[field] = matches
    
    return info

async def transcribe_audio_enhanced(file: UploadFile) -> Dict:
    """Transcrição de áudio aprimorada com detecção de comandos por voz"""
    try:
        # Usar função original do openai_client.py
        from .openai_client import transcribe_audio
        basic_transcription = await transcribe_audio(file)
        
        # Detectar comandos de voz
        voice_commands = detect_voice_commands(basic_transcription)
        
        return {
            "text": basic_transcription,
            "voice_commands": voice_commands,
            "enhanced": True
        }
        
    except Exception as e:
        print(f"Erro na transcrição aprimorada: {e}")
        return {
            "text": "",
            "voice_commands": [],
            "enhanced": False,
            "error": str(e)
        }

def detect_voice_commands(text: str) -> List[Dict]:
    """Detecta comandos de voz no texto transcrito"""
    commands = []
    text_lower = text.lower()
    
    # Padrões de comandos
    command_patterns = {
        'marcar_status': {
            'patterns': [r'marcar?\s+(.+?)\s+como\s+(ok|danificado|sujo|ausente)', 
                        r'(.+?)\s+está\s+(ok|danificado|sujo|ausente)'],
            'action': 'set_status'
        },
        'proximo_comodo': {
            'patterns': [r'próximo\s+cômodo', r'próxima\s+sala', r'avançar'],
            'action': 'next_room'
        },
        'adicionar_observacao': {
            'patterns': [r'observação:\s*(.+)', r'anotar:\s*(.+)', r'nota:\s*(.+)'],
            'action': 'add_note'
        }
    }
    
    for command_type, config in command_patterns.items():
        for pattern in config['patterns']:
            matches = re.findall(pattern, text_lower)
            if matches:
                commands.append({
                    'type': command_type,
                    'action': config['action'],
                    'matches': matches
                })
    
    return commands

async def calculate_repair_costs(inspection_items: List[Dict], region: str = "RJ") -> Dict:
    """Calcula custos estimados de reparo"""
    from .database import SessionLocal, RepairCostTable
    
    db = SessionLocal()
    total_cost = 0
    detailed_costs = []
    
    try:
        for item in inspection_items:
            if item.get('status') in ['danificado', 'ausente']:
                # Buscar custo na tabela
                cost_data = db.query(RepairCostTable).filter(
                    RepairCostTable.region == region,
                    RepairCostTable.item_type == item.get('item', '').lower()
                ).first()
                
                if cost_data:
                    item_cost = cost_data.cost_per_unit
                    total_cost += item_cost
                    
                    detailed_costs.append({
                        'item': item.get('item'),
                        'room': item.get('room'),
                        'repair_type': cost_data.repair_type,
                        'cost': item_cost,
                        'unit': cost_data.unit,
                        'description': cost_data.description
                    })
    
    finally:
        db.close()
    
    return {
        'total_cost': total_cost,
        'detailed_costs': detailed_costs,
        'currency': 'BRL',
        'region': region
    }

# Função auxiliar para detectar itens em uma única foto usando GPT Vision
async def detect_items_in_single_image(photo: UploadFile) -> List[str]:
    """Detecta itens em uma única foto usando GPT Vision"""
    DETECTION_PROMPT = """Você é um especialista em vistoria imobiliária. Analise esta imagem cuidadosamente e identifique TODOS os itens físicos que devem ser verificados em uma vistoria.

Categorias de itens a detectar:
- Instalações sanitárias: pia, torneira, vaso sanitário, chuveiro, box, espelho, tanque
- Estrutura: piso, parede, teto, janela, porta, azulejo, rejunte
- Elétrica: tomadas, interruptores, lâmpadas, fiação visível
- Móveis fixos: armário, bancada, prateleiras
- Eletrodomésticos: fogão, geladeira, microondas, máquina de lavar
- Externos: portão, muro, varal, churrasqueira, jardim

REGRAS IMPORTANTES:
1. Retorne APENAS um array JSON válido com strings em português
2. Use nomes genéricos e padronizados (ex: "pia" não "pia de inox")
3. Não inclua descrições, cores ou detalhes - apenas o nome do item
4. Se houver múltiplos itens do mesmo tipo, liste apenas uma vez (ex: várias tomadas = apenas "tomadas")
5. Seja específico: "vaso sanitário" não apenas "vaso"
6. Formato obrigatório: ["item1", "item2", "item3"]

Exemplo de resposta CORRETA:
["pia", "torneira", "azulejo", "piso", "armário", "bancada", "tomadas", "interruptores"]

Retorne SOMENTE o JSON array, sem explicações, sem markdown, sem texto adicional."""

    try:
        # Ler dados da foto
        if hasattr(photo, 'file') and hasattr(photo.file, 'read'):
            # É um BytesIO ou arquivo já aberto (MockUploadFile)
            photo.file.seek(0)
            photo_data = photo.file.read()
            mime_type = getattr(photo, 'content_type', 'image/jpeg')
        elif hasattr(photo, 'read'):
            # É um UploadFile do FastAPI
            try:
                if hasattr(photo, 'seek'):
                    await photo.seek(0) if hasattr(photo.seek, '__await__') else photo.seek(0)
            except:
                pass
            # Tentar ler de forma assíncrona ou síncrona
            if hasattr(photo.read, '__await__'):
                photo_data = await photo.read()
            else:
                photo_data = photo.read()
            mime_type = getattr(photo, 'content_type', 'image/jpeg')
        else:
            # Fallback: assumir que é bytes
            photo_data = photo if isinstance(photo, bytes) else bytes(photo)
            mime_type = 'image/jpeg'
        
        # Garantir que photo_data é bytes
        if isinstance(photo_data, str):
            photo_data = photo_data.encode('utf-8')
        elif not isinstance(photo_data, bytes):
            photo_data = bytes(photo_data)
        
        # Converter para base64
        b64_image = base64.b64encode(photo_data).decode('utf-8')
        
        # Usar gpt-4o-mini-2024-07-18 que é o snapshot específico do modelo
        print(f"Processando imagem com gpt-4o-mini-2024-07-18...")
        response = await _client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": DETECTION_PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.3
        )
        print(f"✅ Resposta recebida do modelo!")
        
        # Extrair resposta
        response_text = response.choices[0].message.content.strip()
        
        # Limpar resposta (remover markdown code blocks se houver)
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        response_text = response_text.strip()
        
        try:
            detected_items = json.loads(response_text)
            if isinstance(detected_items, list):
                return [item.lower().strip() for item in detected_items if item]
        except json.JSONDecodeError:
            # Tentar extrair lista manualmente se JSON falhar
            matches = re.findall(r'"([^"]+)"', response_text)
            if matches:
                return [item.lower().strip() for item in matches if item]
            else:
                # Fallback: dividir por vírgulas e limpar
                items = [item.strip().strip('"').strip("'") for item in response_text.split(',')]
                return [item.lower().strip() for item in items if item]
        
        return []
        
    except Exception as e:
        import traceback
        print(f"❌ Erro na detecção de itens em foto única: {e}")
        print(traceback.format_exc())
        # Retornar lista vazia em vez de levantar exceção para não quebrar o fluxo
        return []

# Função para criar checklist automático baseado em detecção de objetos usando GPT Vision
async def auto_generate_checklist(room_photos: List[UploadFile]) -> Dict:
    """Gera checklist automaticamente baseado nas fotos do cômodo usando GPT-4 Vision"""
    
    DETECTION_PROMPT = """Você é um especialista em vistoria imobiliária. Analise esta imagem cuidadosamente e identifique TODOS os itens físicos que devem ser verificados em uma vistoria.

Categorias de itens a detectar:
- Instalações sanitárias: pia, torneira, vaso sanitário, chuveiro, box, espelho, tanque
- Estrutura: piso, parede, teto, janela, porta, azulejo, rejunte
- Elétrica: tomadas, interruptores, lâmpadas, fiação visível
- Móveis fixos: armário, bancada, prateleiras
- Eletrodomésticos: fogão, geladeira, microondas, máquina de lavar
- Externos: portão, muro, varal, churrasqueira, jardim

REGRAS IMPORTANTES:
1. Retorne APENAS um array JSON válido com strings em português
2. Use nomes genéricos e padronizados (ex: "pia" não "pia de inox")
3. Não inclua descrições, cores ou detalhes - apenas o nome do item
4. Se houver múltiplos itens do mesmo tipo, liste apenas uma vez (ex: várias tomadas = apenas "tomadas")
5. Seja específico: "vaso sanitário" não apenas "vaso"
6. Formato obrigatório: ["item1", "item2", "item3"]

Exemplo de resposta CORRETA:
["pia", "torneira", "azulejo", "piso", "armário", "bancada", "tomadas", "interruptores"]

Retorne SOMENTE o JSON array, sem explicações, sem markdown, sem texto adicional."""

    all_detected_items = []
    
    try:
        # Usar a função auxiliar para cada foto
        for photo in room_photos:
            detected_items = await detect_items_in_single_image(photo)
            all_detected_items.extend(detected_items)
            await photo.seek(0)  # Reset para outras funções usarem
        
        # Remover duplicatas e normalizar
        unique_items = []
        seen = set()
        
        for item in all_detected_items:
            # Normalizar: lowercase, remover espaços extras
            normalized = item.lower().strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                # Capitalizar primeira letra para melhor apresentação
                unique_items.append(normalized)
        
        return {
            'detected_items': unique_items,
            'total_detections': len(all_detected_items),
            'unique_items': len(unique_items),
            'method': 'gpt-4-vision'
        }
        
    except Exception as e:
        import traceback
        error_detail = str(e)
        print(f"❌ Erro na detecção com GPT Vision: {error_detail}")
        print(traceback.format_exc())
        # Retornar erro detalhado para o frontend
        raise Exception(f"Erro ao processar imagens: {error_detail}")