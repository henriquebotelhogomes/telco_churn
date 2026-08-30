import json
import os
import time
import urllib.error
import urllib.request
from typing import Any


class RetentionCopilot:
    """
    Motor de IA Generativa e Assistente Inteligente de Retenção de Clientes.
    Suporta LLMs em nuvem (Gemini / OpenAI) com Fallback Heurístico Determinístico de alta fidelidade.
    """

    def __init__(self) -> None:
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    def generate_script(
        self,
        customer_id: str,
        canal: str,
        tom: str,
        cliente: dict[str, Any],
        fatores_shap: list[dict[str, Any]],
        playbook: str,
        reducao_estimada_risco: float = 0.0,
        economia_esperada: float = 0.0,
    ) -> dict[str, Any]:
        """
        Gera roteiro e comunicação de retenção sob medida com variação semântica por Tom e Canal.
        """
        t0 = time.perf_counter()

        # Tenta LLM externa se houver chave configurada
        if self.gemini_api_key:
            try:
                resultado_llm = self._call_gemini(
                    customer_id, canal, tom, cliente, fatores_shap, playbook, economia_esperada
                )
                if resultado_llm:
                    elapsed_ms = (time.perf_counter() - t0) * 1000
                    resultado_llm["latency_ms"] = round(elapsed_ms, 2)
                    resultado_llm["provider_used"] = "google_gemini"
                    return resultado_llm
            except Exception as e:
                print(f"[COPILOT] Fallback ativado após falha na LLM: {e}")

        # Motor de Fallback Heurístico Determinístico (Resiliente, Rápido e Gratuito)
        resultado_fallback = self._generate_deterministic(
            customer_id,
            canal,
            tom,
            cliente,
            fatores_shap,
            playbook,
            reducao_estimada_risco,
            economia_esperada,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        resultado_fallback["latency_ms"] = round(elapsed_ms, 2)
        resultado_fallback["provider_used"] = "deterministic_rules_engine"
        return resultado_fallback

    def _generate_deterministic(
        self,
        customer_id: str,
        canal: str,
        tom: str,
        cliente: dict[str, Any],
        fatores_shap: list[dict[str, Any]],
        playbook: str,
        reducao_risco: float,
        economia: float,
    ) -> dict[str, Any]:
        meses = cliente.get("meses_permanencia") or cliente.get("tenure") or 12

        # Identifica dores a partir dos fatores SHAP com DEDUPLICAÇÃO
        dores_detectadas = []
        for f in fatores_shap[:4]:
            fator_nome = f.get("fator", "")
            if "Contrato" in fator_nome:
                dores_detectadas.append("previsibilidade e estabilidade contratual")
            elif "Internet" in fator_nome or "Fibra" in fator_nome:
                dores_detectadas.append("velocidade e estabilidade da internet fibra")
            elif "Suporte" in fator_nome:
                dores_detectadas.append("agilidade e disponibilidade do suporte técnico")
            elif "Segurança" in fator_nome or "Proteção" in fator_nome:
                dores_detectadas.append("segurança digital e antivírus para a família")
            elif "Pagamento" in fator_nome or "Cobrança" in fator_nome:
                dores_detectadas.append("praticidade e automatização da forma de pagamento")

        # Deduplicação preservando a ordem
        dores_unicas = list(dict.fromkeys(dores_detectadas))
        dores_str = ", ".join(dores_unicas) if dores_unicas else "otimização do pacote de serviços"

        # -----------------------------------------------------------------------
        # ROTEIRO DE CALL CENTER COM VARIAÇÃO EXPLÍCITA POR TOM
        # -----------------------------------------------------------------------
        if tom == "direto":
            etapas_call_center = {
                "etapa_1_abertura": (
                    f"Olá! Sou da equipe de Negociação RetainIQ. Falo com o titular da conta {customer_id}? "
                    f"Identifiquei que você é cliente há {meses} meses e tenho uma oportunidade de otimização direta para seu plano hoje."
                ),
                "etapa_2_sondagem": (
                    f"Analisando seus dados, notamos pontos de ganho imediato de eficiência em {dores_str}. "
                    f"Qual o principal ponto que você gostaria de melhorar hoje?"
                ),
                "etapa_3_proposta_valor": (
                    f"Liberamos para você a ativação imediata do plano '{playbook}'. "
                    f"Essa proposta reduz custos e gera uma economia líquida projetada de R$ {economia:.2f} ao ano."
                ),
                "etapa_4_fechamento": (
                    "Podemos aplicar este benefício agora mesmo para já valer na sua próxima fatura?"
                ),
            }
        elif tom == "consultivo":
            etapas_call_center = {
                "etapa_1_abertura": (
                    f"Olá! Aqui é da Consultoria de Contas Estratégicas RetainIQ. Gostaria de falar com o responsável pela conta {customer_id}? "
                    f"Como você possui um relacionamento consolidado de {meses} meses conosco, realizamos um diagnóstico executivo do seu perfil."
                ),
                "etapa_2_sondagem": (
                    f"Nosso mapeamento identificou oportunidades de modernização técnica com foco em {dores_str}. "
                    f"Faz sentido avaliarmos como otimizar essa estrutura?"
                ),
                "etapa_3_proposta_valor": (
                    f"Nossa recomendação estratégica para sua conta é a implementação do playbook '{playbook}'. "
                    f"Além de blindar a estabilidade dos serviços, essa ação resulta em uma otimização financeira de R$ {economia:.2f} anuais."
                ),
                "etapa_4_fechamento": (
                    "Podemos formalizar este novo acordo de serviços na sua conta para garantirmos essas condições?"
                ),
            }
        else:  # tom == "empatico" (padrão)
            etapas_call_center = {
                "etapa_1_abertura": (
                    f"Olá! Aqui é da equipe de Cuidado ao Cliente RetainIQ. É um prazer falar com você! Gostaria de falar com o titular da conta {customer_id}? "
                    f"Primeiramente, muito obrigado por estar conosco há {meses} meses. Você é uma pessoa muito especial para nós!"
                ),
                "etapa_2_sondagem": (
                    f"Estou te ligando porque sua satisfação é a nossa maior prioridade. Notamos que podemos cuidar melhor do seu dia a dia em relação a {dores_str}. "
                    f"Como tem sido sua experiência recente? Queremos muito te ouvir!"
                ),
                "etapa_3_proposta_valor": (
                    f"Para retribuir seu carinho e sua confiança de {meses} meses, preparei com muito carinho uma condição exclusiva: "
                    f"a estratégia '{playbook}'. Você terá máxima tranquilidade e uma economia anual estimada de até R$ {economia:.2f}."
                ),
                "etapa_4_fechamento": (
                    "Gostaria que eu já ativasse esse benefício agora mesmo para você ter essa tranquilidade na sua próxima fatura?"
                ),
            }

        # -----------------------------------------------------------------------
        # MENSAGENS DIRETAS (WHATSAPP E E-MAIL) POR TOM
        # -----------------------------------------------------------------------
        if canal == "whatsapp":
            if tom == "direto":
                mensagem_formatada = (
                    f"⚡ *RetainIQ | Oportunidade Direta de Economia*\n\n"
                    f"Titular da conta `{customer_id}` (Cliente há {meses} meses):\n\n"
                    f"🎯 *Proposta:* {playbook}\n"
                    f"💵 *Economia Anual:* R$ {economia:.2f}\n"
                    f"🚀 *Otimização:* Resolução focada em {dores_str}.\n\n"
                    f"Responda *1* para ativar agora na sua fatura."
                )
            elif tom == "consultivo":
                mensagem_formatada = (
                    f"👔 *RetainIQ Consultoria VIP | Conta {customer_id}*\n\n"
                    f"Prezado(a), concluímos a revisão do seu plano de {meses} meses de relacionamento.\n\n"
                    f"📋 *Recomendação Executiva:* {playbook}\n"
                    f"💼 *Impacto Financeiro:* R$ {economia:.2f}/ano de otimização\n"
                    f"🛡️ *Garantia de Qualidade:* {dores_str}\n\n"
                    f"Podemos confirmar a aplicação deste novo modelo de serviço? Responda *CONFIRMAR* para prosseguir."
                )
            else:  # empatico
                mensagem_formatada = (
                    f"👋 Olá! Aqui é do setor de Cuidado ao Cliente RetainIQ.\n\n"
                    f"Como você já é nosso cliente parceiro há *{meses} meses*, preparamos um carinho especial para a conta `{customer_id}`:\n\n"
                    f"✨ *Oferta Exclusiva:* {playbook}\n"
                    f"💰 *Economia Anual Estimada:* R$ {economia:.2f}\n"
                    f"❤️ *Benefício:* Mais tranquilidade em {dores_str}.\n\n"
                    f"Podemos aplicar esse benefício diretamente na sua próxima fatura? Responda *SIM* para confirmar! 🚀"
                )
        elif canal == "email":
            if tom == "direto":
                mensagem_formatada = (
                    f"Assunto: [Ação Rápida] Otimização e Economia de R$ {economia:.2f} na conta {customer_id}\n\n"
                    f"Prezado(a),\n\n"
                    f"Identificamos uma oportunidade de redução direta de custos no seu plano de {meses} meses.\n\n"
                    f"• Proposta: {playbook}\n"
                    f"• Economia Projetada: R$ {economia:.2f}/ano\n"
                    f"• Foco de Melhoria: {dores_str}\n\n"
                    f"Para aprovar a mudança com efeito na próxima fatura, responda com 'APROVADO'.\n\n"
                    f"Atenciosamente,\n"
                    f"Equipe de Negociação RetainIQ"
                )
            elif tom == "consultivo":
                mensagem_formatada = (
                    f"Assunto: Parecer Executivo de Retenção e Otimização para a conta {customer_id}\n\n"
                    f"Prezado(a),\n\n"
                    f"Agradecemos pela parceria continuada de {meses} meses com a nossa plataforma.\n\n"
                    f"Após análise detalhada do histórico de utilização, o Comitê Estratégico RetainIQ aprovou a implementação da solução '{playbook}'. "
                    f"Esta reestruturação resolve gargalos em {dores_str} e proporciona um ganho financeiro estimado em R$ {economia:.2f} ao longo de 12 meses.\n\n"
                    f"Permanecemos à disposição para formalizar a transição.\n\n"
                    f"Cordialmente,\n"
                    f"Gestão de Contas Corporativas | RetainIQ"
                )
            else:  # empatico
                mensagem_formatada = (
                    f"Assunto: Condição Especial de Cuidado e Fidelidade para a sua conta {customer_id}\n\n"
                    f"Olá,\n\n"
                    f"Agradecemos muito por ter você como nosso cliente há {meses} meses. Queremos garantir que você continue tendo a melhor experiência conosco.\n\n"
                    f"Com base no seu perfil, aprovamos a liberação do benefício especial: {playbook}.\n"
                    f"Esta condição garante maior carinho no atendimento, tranquilidade em {dores_str} e uma economia estimada em até R$ {economia:.2f} ao longo do ano.\n\n"
                    f"Para ativar sem custos adicionais, basta responder a este e-mail.\n\n"
                    f"Com carinho,\n"
                    f"Equipe de Sucesso do Cliente RetainIQ"
                )
        else:  # call_center
            mensagem_formatada = (
                f"[ROTEIRO DE LIGAÇÃO - {tom.upper()}]\n\n"
                f"1. ABERTURA:\n{etapas_call_center['etapa_1_abertura']}\n\n"
                f"2. SONDAGEM DE DORES ({dores_str}):\n{etapas_call_center['etapa_2_sondagem']}\n\n"
                f"3. PROPOSTA DE VALOR ({playbook}):\n{etapas_call_center['etapa_3_proposta_valor']}\n\n"
                f"4. CALL TO ACTION / FECHAMENTO:\n{etapas_call_center['etapa_4_fechamento']}"
            )

        argumentos = [
            f"Fidelidade de {meses} meses como âncora de valor e tratamento diferenciado",
            f"Foco na solução das dores identificadas: {dores_str}",
            f"Benefício financeiro explícito: R$ {economia:.2f} de economia anual estimada",
            f"Aplicação direta do playbook recomendado '{playbook}'",
        ]

        return {
            "customer_id": customer_id,
            "canal": canal,
            "tom": tom,
            "roteiro_etapas": etapas_call_center,
            "mensagem_completa": mensagem_formatada,
            "argumentos_chave": argumentos,
            "playbook_aplicado": playbook,
        }

    def _call_gemini(
        self,
        customer_id: str,
        canal: str,
        tom: str,
        cliente: dict[str, Any],
        fatores_shap: list[dict[str, Any]],
        playbook: str,
        economia: float,
    ) -> dict[str, Any] | None:
        """Chamada direta à API do Google Gemini se GEMINI_API_KEY estiver configurada."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"

        prompt = (
            f"Você é o RetainIQ AI Copilot, um especialista sênior em retenção de clientes e negociação comercial.\n"
            f"Gere um roteiro de atendimento altamente persuasivo para o cliente {customer_id}.\n"
            f"Dados do Cliente: {json.dumps(cliente, ensure_ascii=False)}\n"
            f"Principais fatores de risco (SHAP): {json.dumps(fatores_shap, ensure_ascii=False)}\n"
            f"Playbook recomendado: {playbook}\n"
            f"Economia anual estimada: R$ {economia:.2f}\n"
            f"Canal de saída: {canal} | Tom de voz: {tom}\n\n"
            f"Responda EXCLUSIVAMENTE em formato JSON com as chaves: 'mensagem_completa' (string formatada com quebras de linha), "
            f"'argumentos_chave' (lista de strings com 4 bullets estratégicos) e 'resumo_estrategia' (string curta)."
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.3},
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=6.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidate_text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(candidate_text)
            return {
                "customer_id": customer_id,
                "canal": canal,
                "tom": tom,
                "mensagem_completa": parsed.get("mensagem_completa", ""),
                "argumentos_chave": parsed.get("argumentos_chave", []),
                "playbook_aplicado": playbook,
            }


copilot = RetentionCopilot()
