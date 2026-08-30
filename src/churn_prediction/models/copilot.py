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
        Gera roteiro e comunicação de retenção sob medida.
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
        mensalidade = cliente.get("cobranca_mensal") or cliente.get("MonthlyCharges") or 75.0
        nome_cliente = f"Cliente ({customer_id})"

        # Identifica dores a partir dos fatores SHAP
        dores_detectadas = []
        for f in fatores_shap[:3]:
            fator_nome = f.get("fator", "")
            if "Contrato" in fator_nome:
                dores_detectadas.append(
                    "flexibilidade vs. previsibilidade de custo do plano mensal"
                )
            elif "Internet" in fator_nome or "Fibra" in fator_nome:
                dores_detectadas.append("estabilidade e velocidade máxima da conexão de internet")
            elif "Suporte" in fator_nome:
                dores_detectadas.append(
                    "agilidade e disponibilidade de atendimento técnico especializado"
                )
            elif "Segurança" in fator_nome or "Proteção" in fator_nome:
                dores_detectadas.append(
                    "segurança digital e proteção contra ameaças para a família"
                )
            elif "Pagamento" in fator_nome or "Cobrança" in fator_nome:
                dores_detectadas.append(
                    "praticidade e pontualidade na forma de pagamento da fatura"
                )

        dores_str = (
            ", ".join(dores_detectadas) if dores_detectadas else "otimização do pacote de serviços"
        )

        # Roteiro de Call Center estruturado
        etapas_call_center = {
            "etapa_1_abertura": (
                f"Olá! Aqui é da equipe de relacionamento VIP RetainIQ. Gostaria de falar com o responsável pela conta {customer_id}? "
                f"Primeiramente, muito obrigado por estar conosco há {meses} meses. Você é um cliente prioritário para nós!"
            ),
            "etapa_2_sondagem": (
                f"Estou entrando em contato exclusivamente para entender como tem sido sua experiência com nossos serviços. "
                f"Notamos uma oportunidade de aprimorar sua experiência em relação a {dores_str}. Como tem sido seu uso recente?"
            ),
            "etapa_3_proposta_valor": (
                f"Para valorizar sua fidelidade de {meses} meses, temos uma condição exclusiva autorizada hoje: "
                f"o plano com a estratégia '{playbook}'. Com essa proposta, você garante uma economia anual projetada de até "
                f"R$ {economia:.2f} com upgrade de benefícios imediatos."
            ),
            "etapa_4_fechamento": (
                "Podemos confirmar a ativação desta condição especial agora mesmo na sua fatura para que você já aproveite os benefícios a partir deste ciclo?"
            ),
        }

        # Mensagem formatada por canal
        if canal == "whatsapp":
            mensagem_formatada = (
                f"👋 Olá! Aqui é do setor de Relacionamento RetainIQ.\n\n"
                f"Como você já é nosso cliente há *{meses} meses*, selecionamos uma condição exclusiva para a sua conta `{customer_id}`:\n\n"
                f"✨ *Oferta Especial:* {playbook}\n"
                f"💰 *Economia Anual Estimada:* R$ {economia:.2f}\n"
                f"🛡️ *Garantia:* Upgrade de qualidade e suporte dedicado.\n\n"
                f"Podemos aplicar esse benefício diretamente na sua próxima fatura? Responda *SIM* para confirmar! 🚀"
            )
        elif canal == "email":
            mensagem_formatada = (
                f"Assunto: Condição Exclusiva de Fidelidade para a sua conta {customer_id}\n\n"
                f"Olá,\n\n"
                f"Agradecemos por ter você como nosso cliente há {meses} meses. Queremos garantir que você continue tendo a melhor experiência conosco.\n\n"
                f"Com base no seu perfil de uso, aprovamos a liberação do benefício: {playbook}.\n"
                f"Esta condição garante maior estabilidade e uma economia estimada em até R$ {economia:.2f} ao longo do ano.\n\n"
                f"Para ativar sem custos adicionais, basta responder a este e-mail ou clicar no link de confirmação.\n\n"
                f"Atenciosamente,\n"
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
            f"Fidelidade de {meses} meses como âncora de valor para tratamento VIP",
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
