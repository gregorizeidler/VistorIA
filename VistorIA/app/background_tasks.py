from celery import Celery
from typing import List, Dict
import os
import asyncio
from .ai_services import enhanced_image_analysis, extract_text_from_document, calculate_repair_costs
from .database import SessionLocal, ChecklistItem, InspectionFile, Inspection

# Configurar Celery
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("vistoria_tasks", broker=redis_url, backend=redis_url)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
)

@celery_app.task
def process_image_batch(file_paths: List[str], inspection_id: int) -> Dict:
    """Processa múltiplas imagens em background"""
    results = []
    
    db = SessionLocal()
    try:
        for file_path in file_paths:
            if os.path.exists(file_path):
                # Simular UploadFile para a função de análise
                with open(file_path, 'rb') as f:
                    # Análise básica por enquanto - em produção seria mais complexo
                    file_data = f.read()
                    
                    # Salvar resultado no banco
                    file_record = db.query(InspectionFile).filter(
                        InspectionFile.file_path == file_path
                    ).first()
                    
                    if file_record:
                        # Atualizar com análise básica
                        file_record.ai_analysis = f"Processado em background - arquivo {len(file_data)} bytes"
                        db.commit()
                        
                        results.append({
                            'file_path': file_path,
                            'status': 'processed',
                            'file_size': len(file_data)
                        })
    
    except Exception as e:
        results.append({
            'error': str(e),
            'status': 'failed'
        })
    
    finally:
        db.close()
    
    return {
        'inspection_id': inspection_id,
        'processed_files': len(results),
        'results': results
    }

@celery_app.task
def process_audio_batch(file_paths: List[str], inspection_id: int) -> Dict:
    """Processa múltiplos áudios em background"""
    results = []
    
    db = SessionLocal()
    try:
        for file_path in file_paths:
            if os.path.exists(file_path):
                # Simular processamento de áudio
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    
                    file_record = db.query(InspectionFile).filter(
                        InspectionFile.file_path == file_path
                    ).first()
                    
                    if file_record:
                        # Simular transcrição
                        file_record.transcription = f"Transcrição processada em background - {len(file_data)} bytes"
                        db.commit()
                        
                        results.append({
                            'file_path': file_path,
                            'status': 'transcribed',
                            'file_size': len(file_data)
                        })
    
    except Exception as e:
        results.append({
            'error': str(e),
            'status': 'failed'
        })
    
    finally:
        db.close()
    
    return {
        'inspection_id': inspection_id,
        'processed_files': len(results),
        'results': results
    }

@celery_app.task
def calculate_inspection_costs(inspection_id: int, region: str = "RJ") -> Dict:
    """Calcula custos totais da vistoria em background"""
    db = SessionLocal()
    
    try:
        # Buscar todos os itens da vistoria
        items = db.query(ChecklistItem).filter(
            ChecklistItem.inspection_id == inspection_id
        ).all()
        
        total_cost = 0
        detailed_costs = []
        
        # Cálculos simplificados para demonstração
        cost_map = {
            'torneira': 150.0,
            'pia': 200.0,
            'vaso sanitário': 300.0,
            'piso': 45.0,  # por m²
            'parede': 25.0,  # por m²
        }
        
        for item in items:
            if item.status in ['danificado', 'ausente']:
                item_cost = cost_map.get(item.item.lower(), 50.0)  # Default
                
                item.repair_cost_estimate = item_cost
                total_cost += item_cost
                
                detailed_costs.append({
                    'item': item.item,
                    'room': item.room,
                    'cost': item_cost,
                    'status': item.status
                })
        
        # Atualizar custo total da vistoria
        inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if inspection:
            inspection.total_cost_estimate = total_cost
        
        db.commit()
        
        return {
            'inspection_id': inspection_id,
            'total_cost': total_cost,
            'detailed_costs': detailed_costs,
            'items_processed': len(detailed_costs)
        }
    
    except Exception as e:
        db.rollback()
        return {
            'inspection_id': inspection_id,
            'error': str(e),
            'status': 'failed'
        }
    
    finally:
        db.close()

@celery_app.task
def process_ocr_documents(file_paths: List[str], inspection_id: int) -> Dict:
    """Processa OCR de documentos em background"""
    results = []
    db = SessionLocal()
    
    try:
        for file_path in file_paths:
            if os.path.exists(file_path):
                # Simular processamento OCR
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    
                    file_record = db.query(InspectionFile).filter(
                        InspectionFile.file_path == file_path
                    ).first()
                    
                    if file_record:
                        # Simular texto extraído
                        extracted_text = f"Texto extraído via OCR - documento {len(file_data)} bytes"
                        file_record.ocr_text = extracted_text
                        db.commit()
                        
                        results.append({
                            'file_path': file_path,
                            'status': 'ocr_completed',
                            'text_length': len(extracted_text)
                        })
    
    except Exception as e:
        results.append({
            'error': str(e),
            'status': 'failed'
        })
    
    finally:
        db.close()
    
    return {
        'inspection_id': inspection_id,
        'processed_files': len(results),
        'results': results
    }

@celery_app.task
def generate_comparison_report(entrada_inspection_id: int, saida_inspection_id: int) -> Dict:
    """Gera relatório de comparação entre entrada e saída"""
    db = SessionLocal()
    
    try:
        # Buscar itens das duas vistorias
        entrada_items = db.query(ChecklistItem).filter(
            ChecklistItem.inspection_id == entrada_inspection_id
        ).all()
        
        saida_items = db.query(ChecklistItem).filter(
            ChecklistItem.inspection_id == saida_inspection_id
        ).all()
        
        # Criar mapeamento dos itens por cômodo e item
        entrada_map = {f"{item.room}_{item.item}": item for item in entrada_items}
        saida_map = {f"{item.room}_{item.item}": item for item in saida_items}
        
        changes = []
        deteriorated = []
        improved = []
        new_damages = []
        
        for key in entrada_map:
            entrada_item = entrada_map[key]
            saida_item = saida_map.get(key)
            
            if saida_item:
                if entrada_item.status != saida_item.status:
                    change = {
                        'room': entrada_item.room,
                        'item': entrada_item.item,
                        'from_status': entrada_item.status,
                        'to_status': saida_item.status
                    }
                    changes.append(change)
                    
                    # Categorizar mudança
                    if entrada_item.status == 'ok' and saida_item.status in ['danificado', 'sujo']:
                        deteriorated.append(change)
                    elif entrada_item.status in ['danificado', 'sujo'] and saida_item.status == 'ok':
                        improved.append(change)
                    elif saida_item.status == 'danificado' and entrada_item.status != 'danificado':
                        new_damages.append(change)
        
        # Calcular custos das mudanças
        deterioration_cost = len(deteriorated) * 100  # Custo médio estimado
        
        comparison_result = {
            'entrada_inspection_id': entrada_inspection_id,
            'saida_inspection_id': saida_inspection_id,
            'total_changes': len(changes),
            'deteriorated_items': len(deteriorated),
            'improved_items': len(improved),
            'new_damages': len(new_damages),
            'estimated_deterioration_cost': deterioration_cost,
            'changes': changes,
            'deteriorated': deteriorated,
            'improved': improved,
            'new_damages': new_damages
        }
        
        return comparison_result
    
    except Exception as e:
        return {
            'error': str(e),
            'status': 'failed'
        }
    
    finally:
        db.close()

# Função auxiliar para iniciar tasks
def start_batch_processing(inspection_id: int, image_files: List[str] = None, 
                          audio_files: List[str] = None, document_files: List[str] = None):
    """Inicia processamento em batch de arquivos"""
    task_results = {}
    
    if image_files:
        result = process_image_batch.delay(image_files, inspection_id)
        task_results['images'] = result.id
    
    if audio_files:
        result = process_audio_batch.delay(audio_files, inspection_id)
        task_results['audios'] = result.id
    
    if document_files:
        result = process_ocr_documents.delay(document_files, inspection_id)
        task_results['documents'] = result.id
    
    # Sempre calcular custos
    cost_result = calculate_inspection_costs.delay(inspection_id)
    task_results['costs'] = cost_result.id
    
    return task_results

# Função para verificar status das tasks
def get_task_status(task_id: str):
    """Verifica status de uma task"""
    result = celery_app.AsyncResult(task_id)
    return {
        'task_id': task_id,
        'status': result.status,
        'result': result.result if result.ready() else None
    }