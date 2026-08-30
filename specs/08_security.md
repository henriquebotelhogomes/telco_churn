# 08 — Estratégia de Segurança

> Segurança e privacidade **por design**, não como camada posterior. Cobre
> `RNF-30`–`RNF-34` e os requisitos de conformidade `RNF-80`–`RNF-83`.

---

## 1. Princípios

1. **Security by design & by default** — controles habilitados de fábrica.
2. **Defense in depth** — múltiplas camadas independentes.
3. **Least privilege** — mínimo acesso necessário (já refletido no container non-root).
4. **Zero trust** — nada é confiável por estar "dentro da rede".
5. **Privacy by design** — minimização de dados pessoais e propósito explícito.

---

## 2. Modelo de Ameaças (resumo STRIDE)

| Ameaça | Exemplo | Mitigação |
|--------|---------|-----------|
| **S**poofing | Token forjado | JWT assinado, rotação de chaves, MFA (admin) |
| **T**ampering | Alteração de payload/modelo | TLS, assinatura de artefatos, RLS |
| **R**epudiation | Negar uma ação | Trilha de auditoria imutável |
| **I**nformation disclosure | Vazamento entre tenants | RLS + testes de isolamento |
| **D**enial of service | Flood de scoring | Rate limit, cotas, autoscaling |
| **E**levation of privilege | Burlar RBAC | RBAC central + testes de autorização |

---

## 3. Autenticação e Autorização

- **AuthN:** OAuth2/OIDC; JWT de curta duração + refresh token. **SSO (OIDC/SAML)**
  e **SCIM** para enterprise (`Futuro`).
- **MFA** obrigatório para papéis administrativos.
- **AuthZ:** **RBAC** com papéis mínimos — `Admin`, `Analista`, `Leitor` (RF-81).
  Toda rota declara a permissão exigida; autorização centralizada e testada.
- **Multi-tenant:** `tenant_id` carregado no token; **Row-Level Security** no
  Postgres garante isolamento mesmo em caso de bug de aplicação (`RNF-32`).
- **Testes de isolamento de tenant** automatizados no CI (tentativa de acesso
  cross-tenant deve falhar).

---

## 4. Proteção de Dados

| Estado | Controle |
|--------|----------|
| **Em trânsito** | TLS 1.2+ ponta a ponta; HSTS (`RNF-30`) |
| **Em repouso** | Criptografia de volume e de banco (`RNF-31`) |
| **Em uso** | Mascaramento de PII em logs; minimização |
| **Segredos** | Secret manager (Vault/cloud), nunca no código (`RNF-33`) |
| **Chaves** | Rotação periódica; KMS gerenciado |

- **Classificação de dados:** PII de clientes finais marcada e tratada com
  políticas específicas (retenção, acesso, anonimização para treino).
- **Pseudonimização:** identificadores de cliente hasheados em logs/traces.

---

## 5. Segurança de Aplicação (AppSec)

- **Validação estrita de entrada** via Pydantic V2 (já adotado) — *allow-list*.
- **Output encoding** no frontend (React escapa por padrão; CSP estrita).
- **Proteções OWASP Top 10:** injeção (ORM parametrizado), XSS (CSP + sanitização),
  CSRF (tokens/SameSite), SSRF (allow-list em conectores), etc.
- **Rate limiting & cotas** por tenant e por IP (anti-abuso/DoS).
- **Headers de segurança:** CSP, HSTS, X-Content-Type-Options, Referrer-Policy.
- **Error handling seguro:** RFC 7807 sem vazar stack traces/segredos.

---

## 6. Segurança da Cadeia de Suprimentos (Supply Chain)

| Controle | Ferramenta |
|----------|-----------|
| **SAST** | CodeQL / Bandit |
| **Dependências (SCA)** | `pip-audit` / Dependabot / Trivy |
| **Secret scanning** | Gitleaks / GitHub secret scanning |
| **Imagem de container** | Trivy/Grype scan; base slim; non-root (já adotado) |
| **SBOM** | Geração de SBOM (Syft) por release |
| **Assinatura** | Cosign para imagens e artefatos de modelo |
| **Pinning** | Versões fixas + lockfile (uv.lock) |

- **CI bloqueia** merge com vulnerabilidades críticas/altas conhecidas.

---

## 7. Segurança de ML (MLSecOps)

Riscos específicos de sistemas de ML e suas mitigações:

| Risco | Mitigação |
|-------|-----------|
| **Data poisoning** (treino) | Validação de qualidade + revisão de fontes + versionamento de dados |
| **Model inversion / extraction** | Rate limiting, não expor probabilidades cruas em excesso, auditoria |
| **Adversarial inputs** | Validação de ranges/schema; detecção de outliers |
| **Model/artifact tampering** | Assinatura (Cosign) + checksum no carregamento |
| **PII em modelo** | Minimização e anonimização no dataset de treino |

---

## 8. Segurança de Infraestrutura

- **Isolamento de rede:** Network Policies no Kubernetes; segmentação por namespace.
- **Princípio do menor privilégio** em IAM/RBAC do cluster.
- **Pods non-root, read-only filesystem, seccomp/AppArmor**.
- **IaC seguro:** Terraform com `tfsec`/`checkov` no CI.
- **Backups criptografados** e testados (restore drills) — suporta RPO/RTO.

---

## 9. Conformidade e Privacidade (LGPD/GDPR)

| Requisito | Implementação |
|-----------|---------------|
| Base legal e propósito | Processamento documentado por finalidade |
| Direito de acesso/exportação | Endpoint de *data subject request* (`RNF-81`) |
| Direito ao esquecimento | Fluxo de deleção/anonimização |
| Trilha de auditoria | Logs de auditoria retidos e imutáveis (`RNF-82`) |
| Transparência algorítmica | Explicabilidade (SHAP) suporta contestação de decisão (`RNF-83`) |
| Data residency | Implantação regional (roadmap enterprise) |

---

## 10. Resposta a Incidentes

- **Runbook** de incidentes de segurança com severidades e responsáveis.
- **Detecção:** alertas de anomalia (acessos cross-tenant, picos de erro/auth).
- **Contenção e comunicação:** processo de *disclosure* e notificação (LGPD: ANPD).
- **Post-mortem sem culpa (blameless)** com itens de ação rastreados.

---

## 11. Checklist de Segurança por Fase

| Item | MVP | V1 |
|------|-----|----|
| TLS + non-root container | ✅ | ✅ |
| JWT + RBAC + RLS | ✅ | ✅ |
| Secret manager | ✅ | ✅ |
| SAST/SCA/secret scan no CI | ✅ | ✅ |
| SSO/SCIM enterprise | — | ✅ |
| SBOM + assinatura de artefatos | — | ✅ |
| Pentest externo | — | ✅ |

