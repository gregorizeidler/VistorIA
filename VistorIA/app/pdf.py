from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os
import io
import base64
import uuid
from datetime import datetime
from typing import List
from .schemas import ReportRequest

async def build_report_pdf(payload: ReportRequest) -> str:
    """Gera relatório PDF da vistoria"""
    out_dir = 'VistorIA/static/uploads'
    os.makedirs(out_dir, exist_ok=True)
    
    filename = f'vistoria_{uuid.uuid4().hex[:8]}.pdf'
    path = os.path.join(out_dir, filename)
    
    # Criar PDF usando canvas para maior controle
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    
    # Cores
    primary_color = HexColor('#667eea')
    secondary_color = HexColor('#764ba2')
    
    # Cabeçalho
    y = height - 2*cm
    
    # Logo (se fornecido)
    if payload.logoPath and os.path.exists(payload.logoPath):
        try:
            c.drawImage(payload.logoPath, 2*cm, y-2*cm, width=4*cm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    
    # Título
    c.setFillColor(primary_color)
    c.setFont('Helvetica-Bold', 20)
    c.drawString(7*cm, y, 'RELATÓRIO DE VISTORIA')
    
    y -= 0.8*cm
    c.setFillColor(secondary_color)
    c.setFont('Helvetica-Bold', 16)
    c.drawString(7*cm, y, 'VistorIA - Sistema Inteligente')
    
    y -= 2*cm
    
    # Informações do imóvel
    c.setFillColor(HexColor('#333333'))
    c.setFont('Helvetica-Bold', 14)
    c.drawString(2*cm, y, 'DADOS DO IMÓVEL')
    
    y -= 0.8*cm
    c.setFont('Helvetica', 12)
    c.drawString(2*cm, y, f'Endereço: {payload.propertyAddress}')
    
    y -= 0.6*cm
    c.drawString(2*cm, y, f'Locador: {payload.landlordName}')
    
    y -= 0.6*cm
    c.drawString(2*cm, y, f'Locatário: {payload.tenantName}')
    
    y -= 0.6*cm
    inspection_date = payload.inspectionDate or datetime.now()
    c.drawString(2*cm, y, f'Data da Vistoria: {inspection_date.strftime("%d/%m/%Y %H:%M")}')
    
    y -= 0.6*cm
    c.drawString(2*cm, y, f'Tipo de Vistoria: {payload.inspectionType.title()}')
    
    y -= 1.5*cm
    
    # Linha separadora
    c.setStrokeColor(primary_color)
    c.setLineWidth(2)
    c.line(2*cm, y, width-2*cm, y)
    
    y -= 1*cm
    
    # Itens do checklist
    c.setFillColor(HexColor('#333333'))
    c.setFont('Helvetica-Bold', 14)
    c.drawString(2*cm, y, 'ITENS VERIFICADOS')
    
    y -= 1*cm
    
    for item in payload.checklist:
        # Verificar se precisa de nova página
        if y < 8*cm:
            c.showPage()
            y = height - 2*cm
        
        # Status com cor
        status_color = _get_status_color(item.status)
        c.setFillColor(status_color)
        c.setFont('Helvetica-Bold', 12)
        c.drawString(2*cm, y, f"● {item.room} - {item.item}")
        
        c.setFillColor(HexColor('#666666'))
        c.setFont('Helvetica', 11)
        c.drawString(2.5*cm, y-0.5*cm, f"Status: {item.status.upper()}")
        
        y -= 1*cm
        
        # Observações
        if item.notes:
            c.setFillColor(HexColor('#333333'))
            c.setFont('Helvetica', 10)
            # Quebrar texto longo
            notes_text = item.notes[:200] + "..." if len(item.notes) > 200 else item.notes
            c.drawString(2.5*cm, y, f"Obs: {notes_text}")
            y -= 0.6*cm
        
        # Fotos
        photo_count = 0
        for photo_path in (item.photos or [])[:2]:  # Máximo 2 fotos por item
            if os.path.exists(photo_path) and photo_count < 2:
                try:
                    # Verificar espaço para imagem
                    if y < 4*cm:
                        c.showPage()
                        y = height - 2*cm
                    
                    c.drawImage(photo_path, 2.5*cm, y-3*cm, width=5*cm, height=3*cm, 
                              preserveAspectRatio=True, mask='auto')
                    y -= 3.5*cm
                    photo_count += 1
                except Exception:
                    pass
        
        # Transcrições de áudio
        if item.audioTranscripts:
            c.setFillColor(HexColor('#555555'))
            c.setFont('Helvetica-Oblique', 9)
            for transcript in item.audioTranscripts[:2]:  # Máximo 2 transcrições
                transcript_text = transcript[:100] + "..." if len(transcript) > 100 else transcript
                c.drawString(2.5*cm, y, f"🎤 {transcript_text}")
                y -= 0.5*cm
        
        y -= 0.5*cm
    
    # Nova página para assinaturas
    c.showPage()
    y = height - 3*cm
    
    # Título das assinaturas
    c.setFillColor(primary_color)
    c.setFont('Helvetica-Bold', 16)
    c.drawString(2*cm, y, 'ASSINATURAS')
    
    y -= 2*cm
    
    # Assinatura do locador
    if payload.landlordSignature:
        c.setFillColor(HexColor('#333333'))
        c.setFont('Helvetica-Bold', 12)
        c.drawString(2*cm, y, 'LOCADOR')
        _draw_signature(c, payload.landlordSignature, 2*cm, y-4*cm)
        c.setFont('Helvetica', 10)
        c.drawString(2*cm, y-4.5*cm, payload.landlordName)
    
    # Assinatura do locatário
    if payload.tenantSignature:
        c.setFillColor(HexColor('#333333'))
        c.setFont('Helvetica-Bold', 12)
        c.drawString(12*cm, y, 'LOCATÁRIO')
        _draw_signature(c, payload.tenantSignature, 12*cm, y-4*cm)
        c.setFont('Helvetica', 10)
        c.drawString(12*cm, y-4.5*cm, payload.tenantName)
    
    # Rodapé
    c.setFillColor(HexColor('#999999'))
    c.setFont('Helvetica', 8)
    c.drawString(2*cm, 1*cm, f'Relatório gerado pelo VistorIA em {datetime.now().strftime("%d/%m/%Y às %H:%M")}')
    
    c.save()
    return path

def _get_status_color(status: str) -> HexColor:
    """Retorna cor baseada no status"""
    colors = {
        'ok': HexColor('#4CAF50'),
        'danificado': HexColor('#F44336'),
        'sujo': HexColor('#FF9800'),
        'ausente': HexColor('#9E9E9E')
    }
    return colors.get(status.lower(), HexColor('#333333'))

def _draw_signature(c, data_url: str, x: float, y: float):
    """Desenha assinatura no PDF"""
    try:
        # Remover prefixo data:image se presente
        if ',' in data_url:
            header, b64data = data_url.split(',', 1)
        else:
            b64data = data_url
        
        img_bytes = base64.b64decode(b64data)
        bio = io.BytesIO(img_bytes)
        
        c.drawImage(ImageReader(bio), x, y, width=6*cm, height=3*cm, 
                   preserveAspectRatio=True, mask='auto')
    except Exception as e:
        # Fallback: desenhar texto
        c.setFont('Helvetica', 10)
        c.drawString(x, y, '[Assinatura digital]')