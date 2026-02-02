"""
Handler do fluxo de Compras.
"""
import logging

from app.config import get_settings
from app.models.conversation import ConversationState, Etapa, Fluxo

logger = logging.getLogger(__name__)


class ComprasHandler:
    """Handler para o fluxo de compras."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def start(self, state: ConversationState) -> str:
        """Inicia o fluxo de compras."""
        if state.nome:
            return (
                f"Você é *{state.nome}*, certo? 😊\n\n"
                f"1️⃣ Sim, sou eu\n"
                f"2️⃣ Não, quero informar outro nome"
            )
        else:
            return "Para prosseguir com sua compra, preciso do seu nome.\n\nQual é o seu nome?"
    
    def handle(self, state: ConversationState, message: str) -> str:
        """Processa mensagem dentro do fluxo de compras."""
        
        if state.etapa == Etapa.COMPRAS_CONFIRMAR_NOME:
            return self._handle_confirmar_nome(state, message)
        
        return self._encaminhar_atendente(state)
    
    def _handle_confirmar_nome(self, state: ConversationState, message: str) -> str:
        """Processa confirmação do nome."""
        opcao = message.strip()
        
        if state.nome:
            if opcao == "1":
                return self._encaminhar_atendente(state)
            elif opcao == "2":
                state.nome = None
                return "Ok! Qual é o seu nome?"
            else:
                # Assume que digitou o nome
                if len(opcao) >= 2 and not any(c.isdigit() for c in opcao):
                    state.nome = opcao.title()
                    return self._encaminhar_atendente(state)
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
                return self._encaminhar_atendente(state)
            else:
                return "Por favor, informe um nome válido."
    
    def _encaminhar_atendente(self, state: ConversationState) -> str:
        """Encaminha para atendente para finalizar compra."""
        state.etapa = Etapa.ENCAMINHADO_ATENDENTE
        state.fluxo = Fluxo.ATENDENTE
        state.encaminhado_atendente = True
        
        nome = state.nome or "Cliente"
        
        return (
            f"Perfeito, {nome}! 😄\n\n"
            f"Vou te encaminhar agora para um de nossos atendentes "
            f"para finalizar sua compra 🛒\n\n"
            f"⏳ Aguarde um momento, por favor.\n\n"
            f"_Digite *menu* a qualquer momento para voltar ao início._"
        )
