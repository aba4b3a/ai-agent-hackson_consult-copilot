"""Tenant authorization middleware (skeleton).

TODO(auth): The authentication basis (Firebase Auth ID token / OIDC / session
cookie) has not been decided yet. This module provides the shape and
intercept points so that the rest of the API can be wired now and the real
checks can be added without changing call sites.

The contract once implemented:

1. Resolve the calling principal (subject id, email, tenant claim) from the
   request (e.g. ``Authorization: Bearer <id_token>``).
2. Extract ``company_id`` from the path (``/api/v1/companies/{company_id}/...``).
3. Reject the request with 401 if there is no principal, or 403 if the
   principal's tenant claim does not include ``company_id``.
4. Stash the resolved principal on ``request.state.principal`` so downstream
   handlers (e.g. ``approvals.approve``) can record ``decided_by`` without
   trusting client-supplied user identifiers.

Until the auth basis is decided this middleware is a pass-through that only
logs the unenforced state once per process.
"""
from __future__ import annotations

import logging
import re
from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_logger = logging.getLogger(__name__)
_warned = False

_COMPANY_PATH = re.compile(r"^/api/v1/companies/(?P<company_id>[^/]+)")


class TenantAuthMiddleware(BaseHTTPMiddleware):
    """Pass-through tenant auth gate.

    Currently only extracts ``company_id`` from the path and attaches it to
    ``request.state.company_id``. It does NOT verify anything — see TODO at
    the top of this file.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        global _warned
        if not _warned:
            _logger.warning(
                "TenantAuthMiddleware is in pass-through mode — no authentication is performed. "
                "Wire Firebase Auth (or chosen IdP) before going to production."
            )
            _warned = True

        match = _COMPANY_PATH.match(request.url.path)
        if match:
            request.state.company_id = match.group("company_id")
        else:
            request.state.company_id = None

        # TODO(auth): once a principal is resolved, attach it here:
        #     request.state.principal = Principal(sub=..., email=..., tenants=[...])
        # and reject when request.state.company_id is not in principal.tenants.
        request.state.principal = None

        return await call_next(request)
