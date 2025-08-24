from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vistoria.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Database Models
class Inspection(Base):
    """Vistoria principal"""
    __tablename__ = "inspections"
    
    id = Column(Integer, primary_key=True, index=True)
    property_address = Column(String, nullable=False)
    landlord_name = Column(String, nullable=False)
    tenant_name = Column(String, nullable=False)
    inspection_type = Column(String, default="entrada")  # entrada, saida
    inspection_date = Column(DateTime, default=func.now())
    status = Column(String, default="draft")  # draft, in_progress, completed
    template_type = Column(String, default="apartamento")  # apartamento, casa, comercial
    landlord_signature = Column(Text, nullable=True)  # base64
    tenant_signature = Column(Text, nullable=True)  # base64
    logo_path = Column(String, nullable=True)
    total_cost_estimate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    checklist_items = relationship("ChecklistItem", back_populates="inspection")
    files = relationship("InspectionFile", back_populates="inspection")

class Template(Base):
    """Templates de checklist personalizáveis"""
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # "Apartamento Padrão", "Casa com Quintal"
    type = Column(String, nullable=False)  # apartamento, casa, comercial
    rooms_items = Column(JSON, nullable=False)  # {"cozinha": ["pia", "torneira"], "banheiro": [...]}
    is_default = Column(Boolean, default=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

class ChecklistItem(Base):
    """Item individual do checklist"""
    __tablename__ = "checklist_items"
    
    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"))
    room = Column(String, nullable=False)
    item = Column(String, nullable=False)
    status = Column(String, nullable=False)  # ok, danificado, sujo, ausente
    notes = Column(Text, nullable=True)
    ai_analysis = Column(Text, nullable=True)  # Análise da IA
    repair_cost_estimate = Column(Float, default=0.0)
    priority = Column(String, default="low")  # low, medium, high, critical
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    inspection = relationship("Inspection", back_populates="checklist_items")
    files = relationship("InspectionFile", back_populates="checklist_item")

class InspectionFile(Base):
    """Arquivos da vistoria (fotos, áudios)"""
    __tablename__ = "inspection_files"
    
    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"))
    checklist_item_id = Column(Integer, ForeignKey("checklist_items.id"), nullable=True)
    file_type = Column(String, nullable=False)  # photo, audio, document
    file_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    ai_analysis = Column(Text, nullable=True)  # Análise específica do arquivo
    transcription = Column(Text, nullable=True)  # Para arquivos de áudio
    ocr_text = Column(Text, nullable=True)  # Para documentos com OCR
    detected_objects = Column(JSON, nullable=True)  # Para reconhecimento de objetos
    uploaded_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    inspection = relationship("Inspection", back_populates="files")
    checklist_item = relationship("ChecklistItem", back_populates="files")

class RepairCostTable(Base):
    """Tabela de preços para cálculo de orçamentos"""
    __tablename__ = "repair_costs"
    
    id = Column(Integer, primary_key=True, index=True)
    region = Column(String, nullable=False)  # RJ, SP, MG, etc.
    item_type = Column(String, nullable=False)  # torneira, piso, parede
    repair_type = Column(String, nullable=False)  # troca, reparo, pintura
    unit = Column(String, nullable=False)  # unidade, m2, ml
    cost_per_unit = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    updated_at = Column(DateTime, default=func.now())

# Criar tabelas
def create_tables():
    Base.metadata.create_all(bind=engine)

# Dependency para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Templates padrão
DEFAULT_TEMPLATES = {
    "apartamento": {
        "name": "Apartamento Padrão",
        "type": "apartamento",
        "rooms_items": {
            "sala": ["piso", "parede", "teto", "janela", "porta", "tomadas", "interruptores"],
            "cozinha": ["pia", "torneira", "fogão", "geladeira", "armários", "bancada", "azulejo", "piso"],
            "banheiro": ["vaso sanitário", "pia", "chuveiro", "box", "espelho", "azulejo", "piso", "ventilação"],
            "quarto1": ["piso", "parede", "teto", "janela", "porta", "armário", "tomadas"],
            "quarto2": ["piso", "parede", "teto", "janela", "porta", "armário", "tomadas"],
            "área de serviço": ["tanque", "torneira", "varal", "piso", "parede"]
        }
    },
    "casa": {
        "name": "Casa Padrão",
        "type": "casa",
        "rooms_items": {
            "sala": ["piso", "parede", "teto", "janela", "porta", "tomadas", "interruptores"],
            "cozinha": ["pia", "torneira", "fogão", "geladeira", "armários", "bancada", "azulejo", "piso"],
            "banheiro": ["vaso sanitário", "pia", "chuveiro", "box", "espelho", "azulejo", "piso"],
            "quarto1": ["piso", "parede", "teto", "janela", "porta", "armário", "tomadas"],
            "quarto2": ["piso", "parede", "teto", "janela", "porta", "armário", "tomadas"],
            "área de serviço": ["tanque", "torneira", "varal", "piso", "parede"],
            "quintal": ["portão", "jardim", "churrasqueira", "piso externo", "muros"],
            "garagem": ["portão", "piso", "tomada", "iluminação"]
        }
    }
}

# Dados padrão de custos (exemplo para RJ)
DEFAULT_REPAIR_COSTS = [
    {"region": "RJ", "item_type": "torneira", "repair_type": "troca", "unit": "unidade", "cost_per_unit": 150.0, "description": "Troca de torneira comum"},
    {"region": "RJ", "item_type": "piso", "repair_type": "reparo", "unit": "m2", "cost_per_unit": 45.0, "description": "Reparo de piso cerâmico"},
    {"region": "RJ", "item_type": "parede", "repair_type": "pintura", "unit": "m2", "cost_per_unit": 25.0, "description": "Pintura de parede"},
    {"region": "RJ", "item_type": "vaso sanitário", "repair_type": "troca", "unit": "unidade", "cost_per_unit": 300.0, "description": "Troca de vaso sanitário"},
    {"region": "RJ", "item_type": "pia", "repair_type": "troca", "unit": "unidade", "cost_per_unit": 200.0, "description": "Troca de pia"},
    {"region": "RJ", "item_type": "azulejo", "repair_type": "reparo", "unit": "m2", "cost_per_unit": 35.0, "description": "Reparo de azulejos"},
    {"region": "RJ", "item_type": "porta", "repair_type": "reparo", "unit": "unidade", "cost_per_unit": 120.0, "description": "Reparo de porta"},
    {"region": "RJ", "item_type": "janela", "repair_type": "reparo", "unit": "unidade", "cost_per_unit": 180.0, "description": "Reparo de janela"},
]

def init_default_data():
    """Inicializa dados padrão no banco"""
    db = SessionLocal()
    
    try:
        # Inserir templates padrão se não existirem
        for template_key, template_data in DEFAULT_TEMPLATES.items():
            existing = db.query(Template).filter(Template.type == template_key).first()
            if not existing:
                template = Template(**template_data, is_default=True)
                db.add(template)
        
        # Inserir custos padrão se não existirem
        existing_costs = db.query(RepairCostTable).first()
        if not existing_costs:
            for cost_data in DEFAULT_REPAIR_COSTS:
                cost = RepairCostTable(**cost_data)
                db.add(cost)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao inserir dados padrão: {e}")
    finally:
        db.close()