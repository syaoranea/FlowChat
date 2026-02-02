"""
Serviço de integração com Firebase/Firestore.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.config import get_settings
from app.models.conversation import ConversationState, Etapa, Fluxo

logger = logging.getLogger(__name__)


class FirebaseService:
    """Serviço para operações com Firestore."""
    
    _instance = None
    _db = None
    _initialized = False
    _mock_mode = False
    
    def __new__(cls):
        """Singleton pattern para garantir única instância."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa conexão com Firebase."""
        if not self._initialized:
            self._initialize_firebase()
            self._initialized = True
    
    def _initialize_firebase(self):
        """Inicializa o Firebase Admin SDK."""
        settings = get_settings()
        try:
            # Tenta inicializar com credenciais do arquivo
            if not firebase_admin._apps:
                try:
                    cred = credentials.Certificate(settings.firebase_credentials_path)
                    firebase_admin.initialize_app(cred, {
                        'projectId': settings.firebase_project_id
                    })
                except FileNotFoundError:
                    # Se não encontrar o arquivo, tenta inicializar com credenciais padrão
                    firebase_admin.initialize_app(options={
                        'projectId': settings.firebase_project_id
                    })
            
            self._db = firestore.client()
            logger.info("Firebase inicializado com sucesso")
        except Exception as e:
            logger.warning(f"Firebase não disponível: {e}")
            logger.warning("Executando em modo MOCK (dados simulados)")
            self._mock_mode = True
            self._db = None
    
    @property
    def db(self):
        """Retorna instância do Firestore."""
        return self._db
    
    # ==================== MOCK DATA (para testes) ====================
    
    _mock_conversas = {}
    _mock_orcamento_seq = 0
    
    _mock_produtos = [
        {"_id": "prod_001", "nome": "Camiseta Básica", "descricao": "Camiseta 100% algodão", "categoria": "Roupas", "ativo": True, "atributos": ["Cor", "Tamanho"]},
        {"_id": "prod_002", "nome": "Calça Jeans", "descricao": "Calça jeans tradicional", "categoria": "Roupas", "ativo": True, "atributos": ["Cor", "Tamanho"]},
        {"_id": "prod_003", "nome": "Notebook Dell", "descricao": "Notebook Dell Inspiron 15", "categoria": "Informática", "ativo": True, "atributos": []},
        {"_id": "prod_004", "nome": "Mouse Wireless", "descricao": "Mouse sem fio Logitech", "categoria": "Informática", "ativo": True, "atributos": ["Cor"]},
        {"_id": "prod_005", "nome": "Fone Bluetooth", "descricao": "Fone de ouvido Bluetooth", "categoria": "Eletrônicos", "ativo": True, "atributos": ["Cor"]},
    ]
    
    _mock_skus = [
        {"_id": "sku_001", "produto_id": "prod_001", "sku": "CAM-PRE-M", "preco": 59.90, "estoque": 10, "ativo": True, "atributos": {"Cor": "Preto", "Tamanho": "M"}},
        {"_id": "sku_002", "produto_id": "prod_001", "sku": "CAM-PRE-G", "preco": 59.90, "estoque": 8, "ativo": True, "atributos": {"Cor": "Preto", "Tamanho": "G"}},
        {"_id": "sku_003", "produto_id": "prod_001", "sku": "CAM-BRA-M", "preco": 59.90, "estoque": 5, "ativo": True, "atributos": {"Cor": "Branco", "Tamanho": "M"}},
        {"_id": "sku_004", "produto_id": "prod_002", "sku": "CAL-AZU-42", "preco": 149.90, "estoque": 6, "ativo": True, "atributos": {"Cor": "Azul", "Tamanho": "42"}},
        {"_id": "sku_005", "produto_id": "prod_002", "sku": "CAL-PRE-42", "preco": 149.90, "estoque": 4, "ativo": True, "atributos": {"Cor": "Preto", "Tamanho": "42"}},
        {"_id": "sku_006", "produto_id": "prod_003", "sku": "NOTE-DELL-01", "preco": 3499.00, "estoque": 3, "ativo": True, "atributos": {}},
        {"_id": "sku_007", "produto_id": "prod_004", "sku": "MOU-PRE-01", "preco": 89.90, "estoque": 15, "ativo": True, "atributos": {"Cor": "Preto"}},
        {"_id": "sku_008", "produto_id": "prod_004", "sku": "MOU-BRA-01", "preco": 89.90, "estoque": 12, "ativo": True, "atributos": {"Cor": "Branco"}},
        {"_id": "sku_009", "produto_id": "prod_005", "sku": "FON-PRE-01", "preco": 199.90, "estoque": 20, "ativo": True, "atributos": {"Cor": "Preto"}},
    ]
    
    # ==================== CONVERSAS ====================
    
    def get_conversation_state(self, phone: str) -> Optional[ConversationState]:
        """Busca estado da conversa pelo número de telefone."""
        if self._mock_mode:
            data = self._mock_conversas.get(phone)
            if data:
                return ConversationState.from_dict(data)
            return None
        
        try:
            doc = self._db.collection("conversas").document(phone).get()
            if doc.exists:
                return ConversationState.from_dict(doc.to_dict())
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar conversa: {e}")
            return None
    
    def save_conversation_state(self, state: ConversationState) -> bool:
        """Salva estado da conversa no Firestore."""
        if self._mock_mode:
            state.ultima_atualizacao = datetime.utcnow()
            self._mock_conversas[state.phone] = state.to_dict()
            logger.info(f"[MOCK] Estado salvo para {state.phone}")
            return True
        
        try:
            state.ultima_atualizacao = datetime.utcnow()
            self._db.collection("conversas").document(state.phone).set(
                state.to_dict()
            )
            logger.info(f"Estado salvo para {state.phone}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar conversa: {e}")
            return False
    
    def get_or_create_conversation(self, phone: str) -> ConversationState:
        """Busca ou cria nova conversa para o telefone."""
        state = self.get_conversation_state(phone)
        if state is None:
            state = ConversationState(phone=phone)
            self.save_conversation_state(state)
        return state
    
    # ==================== PRODUTOS ====================
    
    def get_categorias(self) -> List[str]:
        """Busca categorias únicas dos produtos ativos."""
        if self._mock_mode:
            categorias = set(p["categoria"] for p in self._mock_produtos if p.get("ativo"))
            return sorted(list(categorias))
        
        try:
            docs = self._db.collection("produtos").where(
                filter=FieldFilter("ativo", "==", True)
            ).stream()
            
            categorias = set()
            for doc in docs:
                data = doc.to_dict()
                if "categoria" in data:
                    categorias.add(data["categoria"])
            
            return sorted(list(categorias))
        except Exception as e:
            logger.error(f"Erro ao buscar categorias: {e}")
            return []
    
    def get_produtos_por_categoria(self, categoria: str) -> List[Dict[str, Any]]:
        """Busca produtos ativos de uma categoria."""
        if self._mock_mode:
            return [p.copy() for p in self._mock_produtos 
                    if p.get("categoria") == categoria and p.get("ativo")]
        
        try:
            docs = self._db.collection("produtos").where(
                filter=FieldFilter("categoria", "==", categoria)
            ).where(
                filter=FieldFilter("ativo", "==", True)
            ).stream()
            
            produtos = []
            for doc in docs:
                data = doc.to_dict()
                data["_id"] = doc.id
                produtos.append(data)
            
            return produtos
        except Exception as e:
            logger.error(f"Erro ao buscar produtos: {e}")
            return []
    
    def get_produto_by_id(self, produto_id: str) -> Optional[Dict[str, Any]]:
        """Busca produto pelo ID."""
        if self._mock_mode:
            for p in self._mock_produtos:
                if p["_id"] == produto_id:
                    return p.copy()
            return None
        
        try:
            doc = self._db.collection("produtos").document(produto_id).get()
            if doc.exists:
                data = doc.to_dict()
                data["_id"] = doc.id
                return data
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar produto: {e}")
            return None
    
    # ==================== SKUS ====================
    
    def get_skus_por_produto(self, produto_id: str) -> List[Dict[str, Any]]:
        """Busca SKUs ativos de um produto."""
        if self._mock_mode:
            return [s.copy() for s in self._mock_skus 
                    if s.get("produto_id") == produto_id and s.get("ativo")]
        
        try:
            docs = self._db.collection("skus").where(
                filter=FieldFilter("produto_id", "==", produto_id)
            ).where(
                filter=FieldFilter("ativo", "==", True)
            ).stream()
            
            skus = []
            for doc in docs:
                data = doc.to_dict()
                data["_id"] = doc.id
                skus.append(data)
            
            return skus
        except Exception as e:
            logger.error(f"Erro ao buscar SKUs: {e}")
            return []
    
    def get_sku_by_id(self, sku_id: str) -> Optional[Dict[str, Any]]:
        """Busca SKU pelo ID."""
        if self._mock_mode:
            for s in self._mock_skus:
                if s["_id"] == sku_id:
                    return s.copy()
            return None
        
        try:
            doc = self._db.collection("skus").document(sku_id).get()
            if doc.exists:
                data = doc.to_dict()
                data["_id"] = doc.id
                return data
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar SKU: {e}")
            return None
    
    def get_sku_by_codigo(self, sku_codigo: str) -> Optional[Dict[str, Any]]:
        """Busca SKU pelo código."""
        if self._mock_mode:
            for s in self._mock_skus:
                if s["sku"] == sku_codigo:
                    return s.copy()
            return None
        
        try:
            docs = self._db.collection("skus").where(
                filter=FieldFilter("sku", "==", sku_codigo)
            ).limit(1).stream()
            
            for doc in docs:
                data = doc.to_dict()
                data["_id"] = doc.id
                return data
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar SKU: {e}")
            return None
    
    # ==================== ESTOQUE ====================
    
    def get_estoque_sku(self, sku: str) -> int:
        """Retorna quantidade total em estoque de um SKU."""
        if self._mock_mode:
            for s in self._mock_skus:
                if s["sku"] == sku:
                    return s.get("estoque", 0)
            return 0
        
        try:
            docs = self._db.collection("estoque").where(
                filter=FieldFilter("sku", "==", sku)
            ).stream()
            
            total = 0
            for doc in docs:
                data = doc.to_dict()
                total += data.get("quantidade", 0)
            
            return total
        except Exception as e:
            logger.error(f"Erro ao buscar estoque: {e}")
            return 0
    
    # ==================== ORÇAMENTOS ====================
    
    def get_proximo_numero_orcamento(self) -> int:
        """Retorna próximo número sequencial de orçamento."""
        if self._mock_mode:
            FirebaseService._mock_orcamento_seq += 1
            return FirebaseService._mock_orcamento_seq
        
        try:
            # Busca documento de controle de sequência
            doc_ref = self._db.collection("controle").document("orcamento_seq")
            doc = doc_ref.get()
            
            if doc.exists:
                numero_atual = doc.to_dict().get("ultimo_numero", 0)
            else:
                numero_atual = 0
            
            proximo_numero = numero_atual + 1
            
            # Atualiza o contador
            doc_ref.set({"ultimo_numero": proximo_numero})
            
            return proximo_numero
        except Exception as e:
            logger.error(f"Erro ao gerar número de orçamento: {e}")
            # Fallback: usa timestamp
            return int(datetime.utcnow().timestamp()) % 100000
    
    _mock_orcamentos = {}
    
    def criar_orcamento(
        self,
        cliente_nome: str,
        cliente_telefone: str,
        itens: List[Dict[str, Any]],
        subtotal: float
    ) -> Optional[Dict[str, Any]]:
        """Cria novo orçamento no Firestore."""
        try:
            settings = get_settings()
            numero = self.get_proximo_numero_orcamento()
            ano = datetime.utcnow().year
            numero_formatado = f"ORC-{ano}-{numero:05d}"
            doc_id = f"orc_{ano}_{numero:06d}"
            
            validade = datetime.utcnow() + timedelta(days=settings.orcamento_validade_dias)
            
            orcamento = {
                "_id": doc_id,
                "numero": numero,
                "numero_formatado": numero_formatado,
                "status": "RASCUNHO",
                "data_criacao": datetime.utcnow().isoformat(),
                "validade": validade.strftime("%Y-%m-%d"),
                "cliente": {
                    "nome": cliente_nome,
                    "telefone": cliente_telefone
                },
                "valores": {
                    "subtotal": subtotal,
                    "desconto": 0,
                    "frete": 0,
                    "impostos": 0,
                    "total": subtotal
                },
                "itens": itens,
                "observacoes": "",
                "encaminhado_atendente": False
            }
            
            if self._mock_mode:
                self._mock_orcamentos[doc_id] = orcamento
                logger.info(f"[MOCK] Orçamento {numero_formatado} criado com sucesso")
            else:
                self._db.collection("orcamentos").document(doc_id).set(orcamento)
                logger.info(f"Orçamento {numero_formatado} criado com sucesso")
            
            return orcamento
        except Exception as e:
            logger.error(f"Erro ao criar orçamento: {e}")
            return None
    
    def get_orcamento_by_numero(self, numero_formatado: str) -> Optional[Dict[str, Any]]:
        """Busca orçamento pelo número formatado."""
        if self._mock_mode:
            for orc in self._mock_orcamentos.values():
                if orc.get("numero_formatado") == numero_formatado:
                    return orc.copy()
            return None
        
        try:
            docs = self._db.collection("orcamentos").where(
                filter=FieldFilter("numero_formatado", "==", numero_formatado)
            ).limit(1).stream()
            
            for doc in docs:
                data = doc.to_dict()
                data["_id"] = doc.id
                return data
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar orçamento: {e}")
            return None
    
    # ==================== LOGS ====================
    
    _mock_logs = []
    
    def log_interacao(
        self,
        phone: str,
        tipo: str,
        mensagem_recebida: str,
        mensagem_enviada: str,
        etapa: str,
        fluxo: str
    ):
        """Registra log de interação no Firestore."""
        try:
            log_data = {
                "phone": phone,
                "tipo": tipo,
                "mensagem_recebida": mensagem_recebida,
                "mensagem_enviada": mensagem_enviada[:500] if mensagem_enviada else "",
                "etapa": etapa,
                "fluxo": fluxo,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if self._mock_mode:
                self._mock_logs.append(log_data)
            else:
                self._db.collection("logs_interacoes").add(log_data)
        except Exception as e:
            logger.error(f"Erro ao salvar log: {e}")


# Instância global do serviço
firebase_service = FirebaseService()
