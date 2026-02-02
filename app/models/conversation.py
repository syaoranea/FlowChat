"""
Modelos para gerenciamento de estado da conversa.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class Etapa(str, Enum):
    """Etapas possíveis da conversa."""
    INICIO = "inicio"
    AGUARDANDO_NOME = "aguardando_nome"
    MENU_PRINCIPAL = "menu_principal"
    
    # Orçamento
    ORCAMENTO_CATEGORIA = "orcamento_categoria"
    ORCAMENTO_PRODUTO = "orcamento_produto"
    ORCAMENTO_QUANTIDADE = "orcamento_quantidade"
    ORCAMENTO_ATRIBUTOS = "orcamento_atributos"
    ORCAMENTO_CONFIRMAR = "orcamento_confirmar"
    ORCAMENTO_CONTINUAR = "orcamento_continuar"
    
    # Compras
    COMPRAS_CONFIRMAR_NOME = "compras_confirmar_nome"
    
    # Pós-venda
    POS_VENDA_CONFIRMAR_NOME = "pos_venda_confirmar_nome"
    POS_VENDA_NUMERO_PEDIDO = "pos_venda_numero_pedido"
    
    # Atendente
    ENCAMINHADO_ATENDENTE = "encaminhado_atendente"


class Fluxo(str, Enum):
    """Fluxos conversacionais disponíveis."""
    NENHUM = "nenhum"
    ORCAMENTO = "orcamento"
    COMPRAS = "compras"
    POS_VENDA = "pos_venda"
    ATENDENTE = "atendente"


class ItemOrcamento(BaseModel):
    """Item de um orçamento em construção."""
    item_id: int
    sku: str
    produto_id: str
    nome_produto: str
    descricao: str
    quantidade: int
    preco_unitario: float
    total: float
    atributos: Dict[str, str] = {}


class OrcamentoTemporario(BaseModel):
    """Orçamento sendo construído durante a conversa."""
    itens: List[ItemOrcamento] = []
    subtotal: float = 0.0


class DadosTemporarios(BaseModel):
    """Dados temporários durante o fluxo."""
    categoria_selecionada: Optional[str] = None
    produto_selecionado: Optional[str] = None
    sku_selecionado: Optional[str] = None
    quantidade_selecionada: Optional[int] = None
    atributos_pendentes: List[str] = []
    atributos_selecionados: Dict[str, str] = {}
    opcoes_produtos: Dict[str, Any] = {}
    opcoes_skus: Dict[str, Any] = {}
    numero_pedido: Optional[str] = None
    orcamento_atual: OrcamentoTemporario = OrcamentoTemporario()


class ConversationState(BaseModel):
    """Estado completo da conversa de um usuário."""
    phone: str
    nome: Optional[str] = None
    etapa: Etapa = Etapa.INICIO
    fluxo: Fluxo = Fluxo.NENHUM
    dados_temporarios: DadosTemporarios = DadosTemporarios()
    encaminhado_atendente: bool = False
    ultima_atualizacao: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para salvar no Firestore."""
        return {
            "phone": self.phone,
            "nome": self.nome,
            "etapa": self.etapa.value,
            "fluxo": self.fluxo.value,
            "dados_temporarios": self.dados_temporarios.model_dump(),
            "encaminhado_atendente": self.encaminhado_atendente,
            "ultima_atualizacao": self.ultima_atualizacao.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationState":
        """Cria instância a partir de dicionário do Firestore."""
        if "etapa" in data:
            data["etapa"] = Etapa(data["etapa"])
        if "fluxo" in data:
            data["fluxo"] = Fluxo(data["fluxo"])
        if "dados_temporarios" in data:
            data["dados_temporarios"] = DadosTemporarios(**data["dados_temporarios"])
        if "ultima_atualizacao" in data and isinstance(data["ultima_atualizacao"], str):
            data["ultima_atualizacao"] = datetime.fromisoformat(data["ultima_atualizacao"])
        return cls(**data)
    
    def reset(self):
        """Reseta o estado para o início."""
        self.etapa = Etapa.MENU_PRINCIPAL
        self.fluxo = Fluxo.NENHUM
        self.dados_temporarios = DadosTemporarios()
        self.encaminhado_atendente = False
