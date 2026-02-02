"""
Handler do fluxo de Orçamento.
"""
import logging
from typing import Optional, List, Dict, Any

from app.config import get_settings
from app.models.conversation import (
    ConversationState, Etapa, Fluxo, 
    ItemOrcamento, OrcamentoTemporario
)
from app.services.firebase_service import firebase_service

logger = logging.getLogger(__name__)


class OrcamentoHandler:
    """Handler para o fluxo de criação de orçamento."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def start(self, state: ConversationState) -> str:
        """Inicia o fluxo de orçamento."""
        state.dados_temporarios.orcamento_atual = OrcamentoTemporario()
        return self._show_categorias(state)
    
    def handle(self, state: ConversationState, message: str) -> str:
        """Processa mensagem dentro do fluxo de orçamento."""
        
        if state.etapa == Etapa.ORCAMENTO_CATEGORIA:
            return self._handle_categoria(state, message)
        
        elif state.etapa == Etapa.ORCAMENTO_PRODUTO:
            return self._handle_produto(state, message)
        
        elif state.etapa == Etapa.ORCAMENTO_QUANTIDADE:
            return self._handle_quantidade(state, message)
        
        elif state.etapa == Etapa.ORCAMENTO_ATRIBUTOS:
            return self._handle_atributos(state, message)
        
        elif state.etapa == Etapa.ORCAMENTO_CONFIRMAR:
            return self._handle_confirmar(state, message)
        
        elif state.etapa == Etapa.ORCAMENTO_CONTINUAR:
            return self._handle_continuar(state, message)
        
        return self._show_categorias(state)
    
    def _show_categorias(self, state: ConversationState) -> str:
        """Mostra lista de categorias disponíveis."""
        categorias = firebase_service.get_categorias()
        
        if not categorias:
            state.etapa = Etapa.MENU_PRINCIPAL
            state.fluxo = Fluxo.NENHUM
            return (
                "Ops! Não encontrei categorias disponíveis no momento. 😕\n\n"
                "Por favor, tente novamente mais tarde ou fale com um atendente.\n\n"
                "Digite *menu* para voltar ao menu principal."
            )
        
        # Salva mapeamento de opções
        state.dados_temporarios.opcoes_produtos = {
            str(i+1): cat for i, cat in enumerate(categorias)
        }
        
        state.etapa = Etapa.ORCAMENTO_CATEGORIA
        
        texto = "📦 *Categorias disponíveis:*\n\n"
        for i, cat in enumerate(categorias, 1):
            texto += f"{i}️⃣ {cat}\n"
        
        texto += "\n👉 Digite o *número* da categoria desejada:"
        
        return texto
    
    def _handle_categoria(self, state: ConversationState, message: str) -> str:
        """Processa seleção de categoria."""
        opcao = message.strip()
        opcoes = state.dados_temporarios.opcoes_produtos
        
        if opcao not in opcoes:
            return (
                "Opção inválida. Por favor, escolha um número da lista.\n\n"
                + self._show_categorias(state)
            )
        
        categoria = opcoes[opcao]
        state.dados_temporarios.categoria_selecionada = categoria
        
        return self._show_produtos(state, categoria)
    
    def _show_produtos(self, state: ConversationState, categoria: str) -> str:
        """Mostra produtos da categoria selecionada."""
        produtos = firebase_service.get_produtos_por_categoria(categoria)
        
        if not produtos:
            return (
                f"Não encontrei produtos na categoria *{categoria}*. 😕\n\n"
                "Vamos escolher outra categoria?\n\n"
                + self._show_categorias(state)
            )
        
        # Busca preços dos SKUs para cada produto
        produtos_com_preco = []
        for prod in produtos:
            skus = firebase_service.get_skus_por_produto(prod["_id"])
            if skus:
                preco_min = min(sku.get("preco", 0) for sku in skus)
                preco_max = max(sku.get("preco", 0) for sku in skus)
                prod["preco_min"] = preco_min
                prod["preco_max"] = preco_max
                prod["skus"] = skus
                produtos_com_preco.append(prod)
        
        if not produtos_com_preco:
            return (
                f"Não encontrei produtos disponíveis na categoria *{categoria}*. 😕\n\n"
                + self._show_categorias(state)
            )
        
        # Salva mapeamento
        state.dados_temporarios.opcoes_produtos = {
            str(i+1): prod for i, prod in enumerate(produtos_com_preco)
        }
        
        state.etapa = Etapa.ORCAMENTO_PRODUTO
        
        texto = f"🛍️ *Produtos em {categoria}:*\n\n"
        for i, prod in enumerate(produtos_com_preco, 1):
            nome = prod.get("nome", "Produto")
            if prod["preco_min"] == prod["preco_max"]:
                preco_str = f"R$ {prod['preco_min']:.2f}"
            else:
                preco_str = f"R$ {prod['preco_min']:.2f} - R$ {prod['preco_max']:.2f}"
            texto += f"{i}️⃣ *{nome}*\n   💰 {preco_str}\n\n"
        
        texto += "👉 Digite o *número* do produto desejado:\n"
        texto += "_Ou digite *voltar* para ver outras categorias._"
        
        return texto
    
    def _handle_produto(self, state: ConversationState, message: str) -> str:
        """Processa seleção de produto."""
        if message.lower() == "voltar":
            return self._show_categorias(state)
        
        opcao = message.strip()
        opcoes = state.dados_temporarios.opcoes_produtos
        
        if opcao not in opcoes:
            return "Opção inválida. Por favor, escolha um número da lista de produtos."
        
        produto = opcoes[opcao]
        state.dados_temporarios.produto_selecionado = produto["_id"]
        
        # Verifica se produto tem atributos
        atributos = produto.get("atributos", [])
        skus = produto.get("skus", [])
        
        if len(skus) == 1:
            # Só tem um SKU, seleciona direto
            state.dados_temporarios.sku_selecionado = skus[0]["_id"]
            state.etapa = Etapa.ORCAMENTO_QUANTIDADE
            
            preco = skus[0].get("preco", 0)
            return (
                f"✅ *{produto['nome']}*\n"
                f"💰 Preço: R$ {preco:.2f}\n\n"
                f"Quantas unidades você deseja?"
            )
        
        elif atributos and len(skus) > 1:
            # Múltiplos SKUs com atributos
            return self._show_skus_com_atributos(state, produto, skus)
        
        else:
            # Múltiplos SKUs sem atributos definidos
            return self._show_skus_simples(state, produto, skus)
    
    def _show_skus_com_atributos(
        self, 
        state: ConversationState, 
        produto: Dict, 
        skus: List[Dict]
    ) -> str:
        """Mostra SKUs com seus atributos para seleção."""
        state.dados_temporarios.opcoes_skus = {
            str(i+1): sku for i, sku in enumerate(skus)
        }
        state.etapa = Etapa.ORCAMENTO_ATRIBUTOS
        
        texto = f"🔍 *{produto['nome']}*\n\n"
        texto += "Escolha a variação desejada:\n\n"
        
        for i, sku in enumerate(skus, 1):
            atributos = sku.get("atributos", {})
            attr_str = " / ".join([f"{k}: {v}" for k, v in atributos.items()])
            preco = sku.get("preco", 0)
            estoque = sku.get("estoque", 0)
            
            texto += f"{i}️⃣ {attr_str}\n"
            texto += f"   💰 R$ {preco:.2f}"
            if estoque > 0:
                texto += f" | 📦 {estoque} em estoque\n\n"
            else:
                texto += f" | ⚠️ Sob consulta\n\n"
        
        texto += "👉 Digite o *número* da opção desejada:"
        
        return texto
    
    def _show_skus_simples(
        self, 
        state: ConversationState, 
        produto: Dict, 
        skus: List[Dict]
    ) -> str:
        """Mostra SKUs simples para seleção."""
        state.dados_temporarios.opcoes_skus = {
            str(i+1): sku for i, sku in enumerate(skus)
        }
        state.etapa = Etapa.ORCAMENTO_ATRIBUTOS
        
        texto = f"🔍 *{produto['nome']}*\n\n"
        texto += "Opções disponíveis:\n\n"
        
        for i, sku in enumerate(skus, 1):
            sku_code = sku.get("sku", "")
            preco = sku.get("preco", 0)
            texto += f"{i}️⃣ {sku_code} - R$ {preco:.2f}\n"
        
        texto += "\n👉 Digite o *número* da opção desejada:"
        
        return texto
    
    def _handle_atributos(self, state: ConversationState, message: str) -> str:
        """Processa seleção de SKU/atributos."""
        opcao = message.strip()
        opcoes = state.dados_temporarios.opcoes_skus
        
        if opcao not in opcoes:
            return "Opção inválida. Por favor, escolha um número da lista."
        
        sku = opcoes[opcao]
        state.dados_temporarios.sku_selecionado = sku["_id"]
        state.etapa = Etapa.ORCAMENTO_QUANTIDADE
        
        # Monta descrição do SKU
        atributos = sku.get("atributos", {})
        if atributos:
            attr_str = " - " + " / ".join([f"{v}" for v in atributos.values()])
        else:
            attr_str = ""
        
        preco = sku.get("preco", 0)
        
        return (
            f"✅ Selecionado: *{sku.get('sku', '')}*{attr_str}\n"
            f"💰 Preço unitário: R$ {preco:.2f}\n\n"
            f"Quantas unidades você deseja?"
        )
    
    def _handle_quantidade(self, state: ConversationState, message: str) -> str:
        """Processa quantidade desejada."""
        try:
            quantidade = int(message.strip())
            if quantidade <= 0:
                raise ValueError("Quantidade deve ser positiva")
        except ValueError:
            return "Por favor, informe uma quantidade válida (número inteiro maior que zero)."
        
        # Verifica estoque
        sku_id = state.dados_temporarios.sku_selecionado
        sku = firebase_service.get_sku_by_id(sku_id)
        
        if not sku:
            return "Ops! Não encontrei o produto. Vamos tentar novamente?\n\n" + self._show_categorias(state)
        
        estoque_disponivel = sku.get("estoque", 0)
        
        # Busca também no collection de estoque
        estoque_total = firebase_service.get_estoque_sku(sku.get("sku", ""))
        if estoque_total > 0:
            estoque_disponivel = estoque_total
        
        if estoque_disponivel > 0 and quantidade > estoque_disponivel:
            return (
                f"⚠️ Quantidade indisponível.\n"
                f"Temos apenas *{estoque_disponivel}* unidades em estoque.\n\n"
                f"Qual quantidade você deseja?"
            )
        
        state.dados_temporarios.quantidade_selecionada = quantidade
        
        # Adiciona ao orçamento
        return self._adicionar_item_orcamento(state, sku, quantidade)
    
    def _adicionar_item_orcamento(
        self, 
        state: ConversationState, 
        sku: Dict, 
        quantidade: int
    ) -> str:
        """Adiciona item ao orçamento temporário."""
        produto_id = state.dados_temporarios.produto_selecionado
        produto = firebase_service.get_produto_by_id(produto_id)
        
        preco = sku.get("preco", 0)
        total = preco * quantidade
        
        # Monta descrição
        atributos = sku.get("atributos", {})
        nome_produto = produto.get("nome", "Produto") if produto else "Produto"
        if atributos:
            descricao = f"{nome_produto} - {' / '.join(atributos.values())}"
        else:
            descricao = nome_produto
        
        # Cria item
        item_id = len(state.dados_temporarios.orcamento_atual.itens) + 1
        item = ItemOrcamento(
            item_id=item_id,
            sku=sku.get("sku", ""),
            produto_id=produto_id,
            nome_produto=nome_produto,
            descricao=descricao,
            quantidade=quantidade,
            preco_unitario=preco,
            total=total,
            atributos=atributos
        )
        
        # Adiciona ao orçamento
        state.dados_temporarios.orcamento_atual.itens.append(item)
        state.dados_temporarios.orcamento_atual.subtotal += total
        
        state.etapa = Etapa.ORCAMENTO_CONTINUAR
        
        # Monta resumo
        return self._mostrar_resumo_parcial(state)
    
    def _mostrar_resumo_parcial(self, state: ConversationState) -> str:
        """Mostra resumo parcial do orçamento."""
        orcamento = state.dados_temporarios.orcamento_atual
        
        texto = "✅ *Item adicionado ao orçamento!*\n\n"
        texto += "📋 *Resumo do seu orçamento:*\n"
        texto += "─" * 20 + "\n\n"
        
        for item in orcamento.itens:
            texto += f"• {item.descricao}\n"
            texto += f"  {item.quantidade}x R$ {item.preco_unitario:.2f} = *R$ {item.total:.2f}*\n\n"
        
        texto += "─" * 20 + "\n"
        texto += f"💰 *Subtotal: R$ {orcamento.subtotal:.2f}*\n\n"
        
        texto += "O que deseja fazer agora?\n\n"
        texto += "1️⃣ Adicionar mais produtos\n"
        texto += "2️⃣ Finalizar orçamento\n"
        texto += "3️⃣ Falar com atendente"
        
        return texto
    
    def _handle_continuar(self, state: ConversationState, message: str) -> str:
        """Processa decisão após adicionar item."""
        opcao = message.strip()
        
        if opcao == "1":
            # Adicionar mais produtos
            return self._show_categorias(state)
        
        elif opcao == "2":
            # Finalizar orçamento
            return self._finalizar_orcamento(state)
        
        elif opcao == "3":
            # Falar com atendente
            return self._encaminhar_atendente_com_orcamento(state)
        
        else:
            return (
                "Opção inválida. Por favor, escolha:\n\n"
                "1️⃣ Adicionar mais produtos\n"
                "2️⃣ Finalizar orçamento\n"
                "3️⃣ Falar com atendente"
            )
    
    def _finalizar_orcamento(self, state: ConversationState) -> str:
        """Finaliza e salva o orçamento."""
        orcamento_temp = state.dados_temporarios.orcamento_atual
        
        if not orcamento_temp.itens:
            return (
                "Seu orçamento está vazio! 😅\n\n"
                "Vamos adicionar alguns produtos?\n\n"
                + self._show_categorias(state)
            )
        
        # Prepara itens para salvar
        itens_para_salvar = []
        for item in orcamento_temp.itens:
            itens_para_salvar.append({
                "item_id": item.item_id,
                "sku": item.sku,
                "produto_id": item.produto_id,
                "descricao": item.descricao,
                "quantidade": item.quantidade,
                "preco_unitario": item.preco_unitario,
                "total": item.total,
                "snapshot": {
                    "atributos": item.atributos
                }
            })
        
        # Cria orçamento no Firestore
        orcamento = firebase_service.criar_orcamento(
            cliente_nome=state.nome or "Cliente",
            cliente_telefone=state.phone,
            itens=itens_para_salvar,
            subtotal=orcamento_temp.subtotal
        )
        
        if not orcamento:
            return (
                "Ops! Ocorreu um erro ao salvar seu orçamento. 😕\n"
                "Por favor, tente novamente ou fale com um atendente.\n\n"
                "1️⃣ Tentar novamente\n"
                "2️⃣ Falar com atendente"
            )
        
        numero = orcamento["numero_formatado"]
        validade = orcamento["validade"]
        total = orcamento["valores"]["total"]
        
        # Limpa dados temporários
        state.dados_temporarios = state.dados_temporarios.__class__()
        
        texto = "🎉 *Orçamento gerado com sucesso!*\n\n"
        texto += f"📄 *Número:* {numero}\n"
        texto += f"💰 *Valor Total:* R$ {total:.2f}\n"
        texto += f"📅 *Válido até:* {validade}\n\n"
        texto += "─" * 20 + "\n\n"
        texto += "Agora vou te encaminhar para um de nossos atendentes finalizar seu pedido! 😊\n\n"
        texto += "⏳ Aguarde um momento, por favor."
        
        # Encaminha para atendente
        state.etapa = Etapa.ENCAMINHADO_ATENDENTE
        state.fluxo = Fluxo.ATENDENTE
        state.encaminhado_atendente = True
        
        return texto
    
    def _encaminhar_atendente_com_orcamento(self, state: ConversationState) -> str:
        """Encaminha para atendente mantendo o orçamento."""
        state.etapa = Etapa.ENCAMINHADO_ATENDENTE
        state.fluxo = Fluxo.ATENDENTE
        state.encaminhado_atendente = True
        
        orcamento = state.dados_temporarios.orcamento_atual
        
        texto = "Perfeito! 😊\n\n"
        
        if orcamento.itens:
            texto += f"Seu orçamento parcial (R$ {orcamento.subtotal:.2f}) foi salvo.\n\n"
        
        texto += (
            "Vou te encaminhar agora para um atendente humano.\n\n"
            "⏳ Aguarde um momento, por favor.\n\n"
            "_Digite *menu* a qualquer momento para voltar ao início._"
        )
        
        return texto
