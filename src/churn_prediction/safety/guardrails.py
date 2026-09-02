import re

from pydantic import BaseModel, Field


class GuardrailCheckResult(BaseModel):
    """Resultado da avaliação de segurança e sanitização."""

    is_safe: bool
    blocked: bool
    sanitized_text: str
    violations: list[str] = Field(default_factory=list)
    redacted_entities: list[str] = Field(default_factory=list)
    risk_level: str = "LOW"  # LOW | MEDIUM | HIGH | CRITICAL


class PIISanitizer:
    """Sanitizador e mascarador de dados pessoais (PII / LGPD)."""

    CPF_PATTERN = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
    CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    PHONE_PATTERN = re.compile(r"\b(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\d{4}|\d{4})[-.\s]?\d{4}\b")

    def sanitize(self, text: str) -> tuple[str, list[str]]:
        sanitized = text
        redacted = []

        if self.CPF_PATTERN.search(sanitized):
            sanitized = self.CPF_PATTERN.sub("[REDACTED_CPF]", sanitized)
            redacted.append("CPF")

        if self.CARD_PATTERN.search(sanitized):
            sanitized = self.CARD_PATTERN.sub("[REDACTED_CARD]", sanitized)
            redacted.append("CREDIT_CARD")

        if self.EMAIL_PATTERN.search(sanitized):
            sanitized = self.EMAIL_PATTERN.sub("[REDACTED_EMAIL]", sanitized)
            redacted.append("EMAIL")

        return sanitized, redacted


class PromptInjectionDetector:
    """Detector ativo de tentativas de Jailbreak e Prompt Injection."""

    INJECTION_KEYWORDS = [
        "ignore previous instructions",
        "ignore all previous",
        "disregard all prior",
        "reveal your system prompt",
        "show me your prompt",
        "reveal your instructions",
        "act as dan",
        "jailbreak",
        "bypass security",
        "override safety",
        "esqueça suas instruções",
        "ignore as instruções anteriores",
        "revele seu prompt",
        "desconsidere todas as regras",
    ]

    def detect(self, text: str) -> tuple[bool, str | None]:
        lower_text = text.lower()
        for kw in self.INJECTION_KEYWORDS:
            if kw in lower_text:
                return True, f"Prompt Injection detectado: correspondência com padrão '{kw}'"
        return False, None


class OutputPolicyGuard:
    """Validador de limites contratuais e políticas comerciais na geração LLM."""

    DISCOUNT_REGEX = re.compile(r"(\d{1,3})%\s*(?:de\s+desconto|off|desconto)", re.IGNORECASE)
    FORBIDDEN_PROMISES = [
        "isenção vitalícia",
        "gratuito para sempre",
        "cancelar todas as faturas anteriores",
        "perdão total de dívida",
        "indenização financeira imediata",
    ]

    def validate_output(self, text: str, max_discount_pct: float = 35.0) -> tuple[bool, list[str]]:
        violations = []
        lower_text = text.lower()

        # Verifica promessas ilegais ou não autorizadas
        for promise in self.FORBIDDEN_PROMISES:
            if promise in lower_text:
                violations.append(f"Promessa proibida pela política comercial: '{promise}'")

        # Verifica teto máximo de desconto oferecido
        for match in self.DISCOUNT_REGEX.finditer(text):
            pct = float(match.group(1))
            if pct > max_discount_pct:
                violations.append(
                    f"Desconto oferecido de {pct}% excede o limite contratual máximo permitido de {max_discount_pct}%"
                )

        return len(violations) == 0, violations


class SafetyGuardrails:
    """Orquestrador central de AI Safety Guardrails."""

    def __init__(self):
        self.pii_sanitizer = PIISanitizer()
        self.injection_detector = PromptInjectionDetector()
        self.output_guard = OutputPolicyGuard()

    def check_input(self, prompt: str) -> GuardrailCheckResult:
        """Avalia e sanitiza a entrada do usuário/agente."""
        sanitized_text, redacted = self.pii_sanitizer.sanitize(prompt)
        is_inj, inj_reason = self.injection_detector.detect(prompt)

        violations = []
        if is_inj and inj_reason:
            violations.append(inj_reason)

        blocked = is_inj
        risk = "CRITICAL" if is_inj else ("MEDIUM" if len(redacted) > 0 else "LOW")

        return GuardrailCheckResult(
            is_safe=not blocked,
            blocked=blocked,
            sanitized_text=sanitized_text,
            violations=violations,
            redacted_entities=redacted,
            risk_level=risk,
        )

    def check_output(
        self, generated_script: str, max_discount: float = 35.0
    ) -> GuardrailCheckResult:
        """Avalia a resposta gerada pelo LLM quanto a conformidade e integridade."""
        sanitized_text, redacted = self.pii_sanitizer.sanitize(generated_script)
        is_valid, policy_violations = self.output_guard.validate_output(
            generated_script, max_discount_pct=max_discount
        )

        blocked = not is_valid
        risk = "HIGH" if blocked else ("MEDIUM" if len(redacted) > 0 else "LOW")

        return GuardrailCheckResult(
            is_safe=not blocked,
            blocked=blocked,
            sanitized_text=sanitized_text,
            violations=policy_violations,
            redacted_entities=redacted,
            risk_level=risk,
        )


# Instância Singleton
safety_guardrails = SafetyGuardrails()
