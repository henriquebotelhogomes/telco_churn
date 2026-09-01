import contextvars
from collections.abc import Awaitable, Callable

from fastapi import Header, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Variável de contexto assíncrona para isolamento de tenant por requisição
_tenant_context_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "tenant_id", default="tenant-default"
)


def get_current_tenant_id() -> str:
    """Retorna o ID do tenant ativo no contexto assíncrono atual."""
    return _tenant_context_var.get()


def set_current_tenant_id(tenant_id: str) -> None:
    """Define o ID do tenant no contexto assíncrono atual."""
    _tenant_context_var.set(tenant_id or "tenant-default")


def get_current_tenant(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
) -> str:
    """Dependência FastAPI para extração e validação do tenant_id da requisição."""
    tenant = (x_tenant_id or "tenant-default").strip()
    set_current_tenant_id(tenant)
    return tenant


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware que garante a propagação do contexto de tenant em todas as requisições HTTP."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        header_tenant = request.headers.get("X-Tenant-ID")
        query_tenant = request.query_params.get("tenant_id")
        tenant_id = (header_tenant or query_tenant or "tenant-default").strip()

        # Define a variável de contexto para o ciclo de vida desta task assíncrona
        token = _tenant_context_var.set(tenant_id)
        try:
            response = await call_next(request)
            response.headers["X-Tenant-ID"] = tenant_id
            return response
        finally:
            _tenant_context_var.reset(token)
