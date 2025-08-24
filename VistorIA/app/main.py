from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Imports locais
from .openai_client import transcribe_audio, analyze_image, summarize_text
from .ai_services import (
    enhanced_image_analysis, extract_text_from_document, 
    transcribe_audio_enhanced, calculate_repair_costs,
    auto_generate_checklist
)
from .pdf import build_report_pdf
from .schemas import ReportRequest
from .database import (
    get_db, create_tables, init_default_data, 
    Inspection, Template, ChecklistItem, InspectionFile, RepairCostTable
)
from .background_tasks import start_batch_processing, get_task_status

load_dotenv()

# Criar tabelas e dados iniciais
create_tables()
init_default_data()

app = FastAPI(
    title=os.getenv('APP_NAME', 'VistorIA'),
    description="Sistema de Vistoria Imobiliária com IA - Versão Completa",
    version="2.0.0"
)

# Configurar templates
templates = Jinja2Templates(directory="VistorIA/templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory="VistorIA/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Página inicial do VistorIA"""
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VistorIA - Sistema de Vistoria Imobiliária</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; color: white; margin-bottom: 40px; }
            .header h1 { font-size: 3rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
            .header p { font-size: 1.2rem; opacity: 0.9; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin-bottom: 40px; }
            .feature-card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); transition: transform 0.3s ease; }
            .feature-card:hover { transform: translateY(-5px); }
            .feature-card h3 { color: #333; margin-bottom: 15px; font-size: 1.5rem; }
            .feature-card p { color: #666; line-height: 1.6; }
            .cta { text-align: center; }
            .btn { display: inline-block; background: #ff6b6b; color: white; padding: 15px 30px; border-radius: 50px; text-decoration: none; font-weight: bold; transition: all 0.3s ease; }
            .btn:hover { background: #ff5252; transform: scale(1.05); }
            .api-info { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin-top: 30px; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏠 VistorIA</h1>
                <p>Sistema Inteligente de Vistoria Imobiliária</p>
            </div>
            
            <div class="features">
                <div class="feature-card">
                    <h3>📋 Checklist Digital</h3>
                    <p>Organize vistorias por cômodo com checklists personalizáveis e intuitivos.</p>
                </div>
                <div class="feature-card">
                    <h3>📸 Captura Inteligente</h3>
                    <p>Tire fotos e grave áudios com análise automática por IA para descrições precisas.</p>
                </div>
                <div class="feature-card">
                    <h3>📄 Relatórios Automáticos</h3>
                    <p>Gere PDFs profissionais com um clique, incluindo fotos e transcrições.</p>
                </div>
                <div class="feature-card">
                    <h3>✍️ Assinatura Digital</h3>
                    <p>Colete assinaturas digitais de locadores e locatários diretamente no app.</p>
                </div>
            </div>
            
            <div class="cta">
                <a href="/docs" class="btn">📚 Ver Documentação da API</a>
            </div>
            
            <div class="api-info">
                <h3>🚀 Endpoints Disponíveis:</h3>
                <ul style="margin-top: 10px; list-style: none;">
                    <li>• <strong>POST /api/transcribe</strong> - Transcrição de áudio</li>
                    <li>• <strong>POST /api/vision</strong> - Análise de imagens</li>
                    <li>• <strong>POST /api/summarize</strong> - Resumo de textos</li>
                    <li>• <strong>POST /api/report</strong> - Geração de relatórios PDF</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

@app.get('/vistoria')
async def vistoria_interface():
    """Interface web completa para vistoria"""
    with open('VistorIA/templates/vistoria.html', 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get('/api/health')
async def health():
    """Health check endpoint"""
    return {'status': 'ok', 'service': 'VistorIA API'}

# ==================== ENDPOINTS DE TEMPLATES ====================
@app.get('/api/templates')
async def get_templates(db: Session = Depends(get_db)):
    """Lista todos os templates disponíveis"""
    templates = db.query(Template).all()
    return {'templates': [{'id': t.id, 'name': t.name, 'type': t.type, 'rooms_items': t.rooms_items} for t in templates]}

@app.get('/api/templates/{template_id}')
async def get_template(template_id: int, db: Session = Depends(get_db)):
    """Obter template específico"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    return template

@app.post('/api/templates')
async def create_template(template_data: dict, db: Session = Depends(get_db)):
    """Criar novo template personalizado"""
    template = Template(**template_data)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template

# ==================== ENDPOINTS DE VISTORIAS ====================
@app.post('/api/inspections')
async def create_inspection(inspection_data: dict, db: Session = Depends(get_db)):
    """Criar nova vistoria"""
    inspection = Inspection(**inspection_data)
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    return inspection

@app.get('/api/inspections/{inspection_id}')
async def get_inspection(inspection_id: int, db: Session = Depends(get_db)):
    """Obter vistoria específica"""
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Vistoria não encontrada")
    return inspection

@app.get('/api/inspections')
async def list_inspections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Listar vistorias"""
    inspections = db.query(Inspection).offset(skip).limit(limit).all()
    return {'inspections': inspections}

# ==================== ENDPOINTS DE IA APRIMORADA ====================
@app.post('/api/vision/enhanced')
async def enhanced_vision_analysis(file: UploadFile = File(...), item_type: str = Form("geral")):
    """Análise aprimorada de imagem com detecção de objetos"""
    try:
        result = await enhanced_image_analysis(file, item_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise aprimorada: {str(e)}")

@app.post('/api/auto-checklist')
async def auto_create_checklist(files: List[UploadFile] = File(...)):
    """Gera checklist automaticamente baseado nas fotos"""
    try:
        result = await auto_generate_checklist(files)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na detecção automática: {str(e)}")

# ==================== ENDPOINTS DE OCR ====================
@app.post('/api/ocr')
async def extract_document_text(file: UploadFile = File(...)):
    """Extrai texto de documentos usando OCR"""
    try:
        result = await extract_text_from_document(file)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no OCR: {str(e)}")

# ==================== ENDPOINTS DE TRANSCRIÇÃO APRIMORADA ====================
@app.post('/api/transcribe/enhanced')
async def enhanced_transcription(file: UploadFile = File(...)):
    """Transcrição aprimorada com detecção de comandos de voz"""
    try:
        result = await transcribe_audio_enhanced(file)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na transcrição aprimorada: {str(e)}")

# ==================== ENDPOINTS DE COMPARAÇÃO ====================
@app.get('/api/compare/{entrada_id}/{saida_id}')
async def compare_inspections(entrada_id: int, saida_id: int, db: Session = Depends(get_db)):
    """Compara vistoria de entrada com saída"""
    from .background_tasks import generate_comparison_report
    try:
        result = generate_comparison_report.delay(entrada_id, saida_id)
        return {'task_id': result.id, 'status': 'processing'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na comparação: {str(e)}")

# ==================== ENDPOINTS DE CUSTOS ====================
@app.post('/api/estimate-costs')
async def estimate_repair_costs(inspection_id: int, region: str = "RJ", db: Session = Depends(get_db)):
    """Calcula custos estimados de reparo"""
    try:
        inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if not inspection:
            raise HTTPException(status_code=404, detail="Vistoria não encontrada")
        
        items = db.query(ChecklistItem).filter(ChecklistItem.inspection_id == inspection_id).all()
        items_data = [{'item': item.item, 'status': item.status, 'room': item.room} for item in items]
        
        costs = await calculate_repair_costs(items_data, region)
        return costs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no cálculo de custos: {str(e)}")

@app.get('/api/repair-costs/{region}')
async def get_repair_costs_table(region: str, db: Session = Depends(get_db)):
    """Obter tabela de custos por região"""
    costs = db.query(RepairCostTable).filter(RepairCostTable.region == region).all()
    return {'costs': costs}

# ==================== ENDPOINTS DE BACKGROUND TASKS ====================
@app.post('/api/batch-process')
async def start_batch_processing_endpoint(
    inspection_id: int,
    image_files: List[str] = [],
    audio_files: List[str] = [],
    document_files: List[str] = []
):
    """Inicia processamento em batch"""
    try:
        task_results = start_batch_processing(inspection_id, image_files, audio_files, document_files)
        return {'task_results': task_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento em batch: {str(e)}")

@app.get('/api/task-status/{task_id}')
async def check_task_status(task_id: str):
    """Verifica status de task em background"""
    try:
        status = get_task_status(task_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar status: {str(e)}")

# ==================== ENDPOINTS DE ARQUIVOS ====================
@app.post('/api/upload-file')
async def upload_file(
    file: UploadFile = File(...),
    inspection_id: int = Form(...),
    checklist_item_id: Optional[int] = Form(None),
    file_type: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload de arquivo com salvamento no banco"""
    try:
        # Criar diretório se não existe
        upload_dir = "VistorIA/static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Salvar arquivo
        file_path = os.path.join(upload_dir, f"{inspection_id}_{file.filename}")
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Salvar no banco
        file_record = InspectionFile(
            inspection_id=inspection_id,
            checklist_item_id=checklist_item_id,
            file_type=file_type,
            file_path=file_path,
            original_filename=file.filename
        )
        db.add(file_record)
        db.commit()
        
        return {'file_id': file_record.id, 'file_path': file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")

@app.post('/api/transcribe')
async def api_transcribe(file: UploadFile = File(...)):
    """Transcreve áudio para texto usando Whisper"""
    try:
        text = await transcribe_audio(file)
        return {'text': text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na transcrição: {str(e)}")

@app.post('/api/vision')
async def api_vision(file: UploadFile = File(...), prompt: str = Form('Descreva o estado do item na imagem.')):
    """Analisa imagem e gera descrição usando GPT-4 Vision"""
    try:
        description = await analyze_image(file, prompt)
        return {'description': description}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise de imagem: {str(e)}")

@app.post('/api/summarize')
async def api_summarize(text: str = Form(...)):
    """Resume texto usando GPT"""
    try:
        summary = await summarize_text(text)
        return {'summary': summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no resumo: {str(e)}")

@app.post('/api/report')
async def api_report(payload: ReportRequest):
    """Gera relatório PDF da vistoria"""
    try:
        pdf_path = await build_report_pdf(payload)
        return FileResponse(
            pdf_path, 
            media_type='application/pdf', 
            filename=f"vistoria_{payload.propertyAddress.replace(' ', '_')}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na geração do PDF: {str(e)}")