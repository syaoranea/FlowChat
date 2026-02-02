"""
Handler do fluxo de Pós-venda.
"""
import logging

from app.config import get_settings
from app.models.conversation import ConversationState, Etapa, Fluxo

logger = logging.getLogger(__name__)


class PosVendaHandler:
    """Handler para o fluxo de pós-venda."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def start(self, state: ConversationState) -> str:
        """Inicia o fluxo de pós-venda."""
        if state.nome:
            return (
                f"Você é *{state.nome}*, certo? 😊\n\n"
                f"1️⃣ Sim, sou eu\n"
                f"2️⃣ Não, quero informar outro nome"
            )
        else:
            return "Para prosseguir com seu atendimento, preciso do seu nome.\n\nQual é o seu nome?"
    
    def handle(self, state: ConversationState, message: str) -> str:
        """Processa mensagem dentro do fluxo de pós-venda."""
        
        if state.etapa == Etapa.POS_VENDA_CONFIRMAR_NOME:
            return self._handle_confirmar_nome(state, message)
        
        elif state.etapa == Etapa.POS_VENDA_NUMERO_PEDIDO:
            return self._handle_numero_pedido(state, message)
        
        return self._pedir_numero_pedido(state)
    
    def _handle_confirmar_nome(self, state: ConversationState, message: str) -> str:
        """Processa confirmação do nome."""
        opcao = message.strip()
        
        if state.nome:
            if opcao == "1":
                return self._pedir_numero_pedido(state)
            elif opcao == "2":
                state.nome = None
                return "Ok! Qual é o seu nome?"
            else:
                # Assume que digitou o nome
                if len(opcao) >= 2 and not any(c.isdigit() for c in opcao):
                    state.nome = opcao.title()
                    return self._pedir_numero_pedido(state)
                return (
                    "Por favor, escolha uma opção:\n\n"
                    f"1️⃣ Sim, sou {state.nome}\n"
                    f"2️⃣ Não, quero informar outro nome"
                )
        else:
            # Captura nome
            nome = opcao
            if len(nome) >= 2 and not any(c.isdigit() for c in nome):
                state.nome = nome.title()
                return self._pedir_numero_pedido(state)
            else:
                return "Por favor, informe um nome válido."
    
    def _pedir_numero_pedido(self, state: ConversationState) -> str:
        """Pede o número do pedido."""
        state.etapa = Etapa.POS_VENDA_NUMERO_PEDIDO
        
        return (
            f"Certo, {state.nome}! 😊\n\n"
            f"Por favor, me informe o *número do seu pedido* para que eu possa localizar:\n\n"
            f"_Exemplo: 12345 ou PED-2026-00001_"
        )
    
    def _handle_numero_pedido(self, state: ConversationState, message: str) -> str:
        """Processa número do pedido."""
        numero = message.strip()
        
        # Validação básica
        if len(numero) < 3:
            return (
                "Por favor, informe um número de pedido válido.\n\n"
                "_Exemplo: 12345 ou PED-2026-00001_"
            )
        
        state.dados_temporarios.numero_pedido = numero
        
        return self._encaminhar_atendente(state, numero)
    
    def _encaminhar_atendente(self, state: ConversationState, numero_pedido: str) -> str:
        """Encaminha para atendente com informações do pedido."""
        state.etapa = Etapa.ENCAMINHADO_ATENDENTE
        state.fluxo = Fluxo.ATENDENTE
        state.encaminhado_atendente = True
        
        return (
            f"Perfeito! Já localizei sua solicitação ✅\n\n"
            f"📦 *Pedido:* {numero_pedido}\n"
            f"👤 *Cliente:* {state.nome}\n\n"
            f"Vou te encaminhar para um atendente que vai te ajudar "
            f"com isso agora mesmo 😊\n\n"
            f"⏳ Aguarde um momento, por favor.\n\n"
            f"_Digite *menu* a qualquer momento para voltar ao início._"
        )
