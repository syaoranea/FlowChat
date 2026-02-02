"""
Handler principal de mensagens - orquestra todos os fluxos.
"""
import logging
from typing import Optional

from app.config import get_settings
from app.models.conversation import ConversationState, Etapa, Fluxo
from app.services.firebase_service import firebase_service
from app.services.twilio_service import twilio_service
from app.handlers.orcamento_handler import OrcamentoHandler
from app.handlers.compras_handler import ComprasHandler
from app.handlers.posvenda_handler import PosVendaHandler

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handler principal que processa mensagens e direciona para os fluxos."""
    
    def __init__(self):
        self.settings = get_settings()
        self.orcamento_handler = OrcamentoHandler()
        self.compras_handler = ComprasHandler()
        self.posvenda_handler = PosVendaHandler()
    
    def process_message(self, phone: str, message: str) -> str:
        """
        Processa mensagem recebida e retorna resposta.
        
        Args:
            phone: Número do telefone (formato whatsapp:+55...)
            message: Mensagem recebida
            
        Returns:
            Mensagem de resposta
        """
        message = message.strip()
        
        # Busca ou cria estado da conversa
        state = firebase_service.get_or_create_conversation(phone)
        
        logger.info(f"[{phone}] Etapa: {state.etapa.value}, Fluxo: {state.fluxo.value}, Msg: {message}")
        
        # Comandos globais
        if message.lower() in ["menu", "início", "inicio", "voltar", "0"]:
            state.reset()
            response = self._show_menu_principal(state)
        elif message.lower() in ["sair", "cancelar"]:
            state.reset()
            response = "Orçamento cancelado. ❌\n\n" + self._show_menu_principal(state)
        else:
            # Processa baseado na etapa atual
            response = self._route_message(state, message)
        
        # Salva estado atualizado
        firebase_service.save_conversation_state(state)
        
        # Log da interação
        firebase_service.log_interacao(
            phone=phone,
            tipo="mensagem",
            mensagem_recebida=message,
            mensagem_enviada=response,
            etapa=state.etapa.value,
            fluxo=state.fluxo.value
        )
        
        return response
    
    def _route_message(self, state: ConversationState, message: str) -> str:
        """Roteia mensagem para o handler apropriado."""
        
        # === INÍCIO E NOME ===
        if state.etapa == Etapa.INICIO:
            return self._handle_inicio(state)
        
        if state.etapa == Etapa.AGUARDANDO_NOME:
            return self._handle_nome(state, message)
        
        # === MENU PRINCIPAL ===
        if state.etapa == Etapa.MENU_PRINCIPAL:
            return self._handle_menu_principal(state, message)
        
        # === FLUXO ORÇAMENTO ===
        if state.fluxo == Fluxo.ORCAMENTO:
            return self.orcamento_handler.handle(state, message)
        
        # === FLUXO COMPRAS ===
        if state.fluxo == Fluxo.COMPRAS:
            return self.compras_handler.handle(state, message)
        
        # === FLUXO PÓS-VENDA ===
        if state.fluxo == Fluxo.POS_VENDA:
            return self.posvenda_handler.handle(state, message)
        
        # === ENCAMINHADO ATENDENTE ===
        if state.etapa == Etapa.ENCAMINHADO_ATENDENTE:
            return self._handle_encaminhado_atendente(state, message)
        
        # Fallback
        return self._show_menu_principal(state)
    
    def _handle_inicio(self, state: ConversationState) -> str:
        """Saudação inicial."""
        state.etapa = Etapa.AGUARDANDO_NOME
        return (
            f"👋 Olá! Seja bem-vindo(a) à {self.settings.company_name}. "
            f"Sou o assistente virtual e estou aqui para te ajudar 😊\n\n"
            f"Para começar, qual é o seu nome?"
        )
    
    def _handle_nome(self, state: ConversationState, message: str) -> str:
        """Captura nome do cliente."""
        # Valida nome (mínimo 2 caracteres, sem números)
        nome = message.strip()
        if len(nome) < 2 or any(char.isdigit() for char in nome):
            return (
                "Por favor, me informe seu nome corretamente. 😊\n\n"
                "Qual é o seu nome?"
            )
        
        state.nome = nome.title()
        state.etapa = Etapa.MENU_PRINCIPAL
        
        return (
            f"Prazer em te conhecer, {state.nome}! 😄\n\n"
            f"{self._get_menu_principal_text()}"
        )
    
    def _handle_menu_principal(self, state: ConversationState, message: str) -> str:
        """Processa escolha do menu principal."""
        opcao = message.strip()
        
        if opcao == "1":
            state.fluxo = Fluxo.ORCAMENTO
            state.etapa = Etapa.ORCAMENTO_CATEGORIA
            return self.orcamento_handler.start(state)
        
        elif opcao == "2":
            state.fluxo = Fluxo.COMPRAS
            state.etapa = Etapa.COMPRAS_CONFIRMAR_NOME
            return self.compras_handler.start(state)
        
        elif opcao == "3":
            state.fluxo = Fluxo.POS_VENDA
            state.etapa = Etapa.POS_VENDA_CONFIRMAR_NOME
            return self.posvenda_handler.start(state)
        
        elif opcao == "4":
            return self._encaminhar_atendente(state)
        
        else:
            return (
                "Opção inválida. Por favor, escolha uma das opções abaixo:\n\n"
                f"{self._get_menu_principal_text()}"
            )
    
    def _show_menu_principal(self, state: ConversationState) -> str:
        """Exibe menu principal."""
        state.etapa = Etapa.MENU_PRINCIPAL
        state.fluxo = Fluxo.NENHUM
        
        saudacao = f"Olá, {state.nome}! " if state.nome else ""
        return f"{saudacao}Como posso te ajudar?\n\n{self._get_menu_principal_text()}"
    
    def _get_menu_principal_text(self) -> str:
        """Retorna texto do menu principal."""
        return (
            "Escolha uma das opções abaixo 👇\n\n"
            "1️⃣ Orçamento\n"
            "2️⃣ Compras\n"
            "3️⃣ Pós-venda\n"
            "4️⃣ Falar com atendente"
        )
    
    def _encaminhar_atendente(self, state: ConversationState) -> str:
        """Encaminha para atendente humano."""
        state.etapa = Etapa.ENCAMINHADO_ATENDENTE
        state.fluxo = Fluxo.ATENDENTE
        state.encaminhado_atendente = True
        
        return (
            "Sem problemas 😊\n"
            "Vou te encaminhar agora para um atendente humano.\n\n"
            "⏳ Aguarde um momento, por favor.\n\n"
            "_Digite *menu* a qualquer momento para voltar ao início._"
        )
    
    def _handle_encaminhado_atendente(self, state: ConversationState, message: str) -> str:
        """Mensagem quando já está encaminhado para atendente."""
        return (
            "Você já foi encaminhado para um atendente. ⏳\n"
            "Por favor, aguarde que em breve você será atendido.\n\n"
            "_Digite *menu* para voltar ao menu principal._"
        )


# Instância global
message_handler = MessageHandler()
