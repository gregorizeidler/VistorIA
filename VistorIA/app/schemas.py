from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ChecklistItem(BaseModel):
    """Item do checklist de vistoria"""
    room: str = Field(..., description="Nome do cômodo")
    item: str = Field(..., description="Item a ser verificado")
    status: str = Field(..., description="Status: 'ok', 'danificado', 'sujo', 'ausente'")
    notes: Optional[str] = Field(None, description="Observações adicionais")
    photos: List[str] = Field(default=[], description="Caminhos das fotos")
    audioTranscripts: List[str] = Field(default=[], description="Transcrições de áudio")

class ReportRequest(BaseModel):
    """Dados para geração do relatório de vistoria"""
    propertyAddress: str = Field(..., description="Endereço do imóvel")
    landlordName: str = Field(..., description="Nome do locador")
    tenantName: str = Field(..., description="Nome do locatário")
    checklist: List[ChecklistItem] = Field(..., description="Lista de itens verificados")
    landlordSignature: Optional[str] = Field(None, description="Assinatura do locador (base64)")
    tenantSignature: Optional[str] = Field(None, description="Assinatura do locatário (base64)")
    logoPath: Optional[str] = Field(None, description="Caminho do logo da imobiliária")
    inspectionDate: Optional[datetime] = Field(default_factory=datetime.now, description="Data da vistoria")
    inspectionType: str = Field(default="entrada", description="Tipo: 'entrada' ou 'saida'")

class TranscriptionResponse(BaseModel):
    """Resposta da transcrição de áudio"""
    text: str = Field(..., description="Texto transcrito")

class VisionResponse(BaseModel):
    """Resposta da análise de imagem"""
    description: str = Field(..., description="Descrição da imagem")

class SummaryResponse(BaseModel):
    """Resposta do resumo de texto"""
    summary: str = Field(..., description="Texto resumido")