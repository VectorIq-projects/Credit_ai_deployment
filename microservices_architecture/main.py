# """API Gateway application for Credit AI microservices.

# This module exposes gateway endpoints for the individual microservices so that
# clients can interact with each service through a single entry point.
# """

# from __future__ import annotations

# import asyncio
# import os
# from typing import Any, Dict

# import httpx
# from fastapi import FastAPI, File, Form, HTTPException, UploadFile
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel, Field


# class Settings(BaseModel):
#     """Runtime configuration for downstream service locations."""

#     ai_analysis_base_url: str = Field(
#         default=os.getenv("AI_ANALYSIS_SERVICE_URL", "http://localhost:8000")
#     )
#     account_overview_base_url: str = Field(
#         default=os.getenv("ACCOUNT_OVERVIEW_SERVICE_URL", "http://localhost:8002")
#     )
#     financial_statement_base_url: str = Field(
#         default=os.getenv(
#             "FINANCIAL_STATEMENT_SERVICE_URL", "http://localhost:8001/api/v1"
#         )
#     )
#     request_timeout_seconds: float = Field(
#         default=float(os.getenv("GATEWAY_REQUEST_TIMEOUT", "60"))
#     )


# def get_settings() -> Settings:
#     return Settings()


# settings = get_settings()

# app = FastAPI(
#     title="Credit AI Gateway",
#     description="Gateway that forwards requests to the underlying microservices.",
#     version="1.0.0",
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# class FinancialStatementGatewayRequest(BaseModel):
#     ticker: str = Field(..., description="Stock ticker symbol")
#     frequency: str = Field(
#         default="quarterly",
#         description="Statement frequency to request (annual or quarterly)",
#         pattern="^(?i)(annual|quarterly)$",
#     )

#     def normalised(self) -> Dict[str, Any]:
#         """Return a JSON-serialisable payload that matches the downstream API."""

#         data = self.model_dump()
#         data["frequency"] = data["frequency"].lower()
#         return data


# async def _post_json(url: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
#     async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
#         try:
#             response = await client.post(url, json=json_data)
#             response.raise_for_status()
#             return response.json()
#         except httpx.HTTPStatusError as exc:  # pragma: no cover - thin wrapper
#             detail = _extract_error_detail(exc.response)
#             raise HTTPException(status_code=exc.response.status_code, detail=detail)
#         except httpx.RequestError as exc:  # pragma: no cover - network failure
#             raise HTTPException(status_code=502, detail=str(exc)) from exc


# async def _post_form(url: str, data: Dict[str, Any]) -> Dict[str, Any]:
#     async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
#         try:
#             response = await client.post(url, data=data)
#             response.raise_for_status()
#             return response.json()
#         except httpx.HTTPStatusError as exc:  # pragma: no cover - thin wrapper
#             detail = _extract_error_detail(exc.response)
#             raise HTTPException(status_code=exc.response.status_code, detail=detail)
#         except httpx.RequestError as exc:  # pragma: no cover - network failure
#             raise HTTPException(status_code=502, detail=str(exc)) from exc


# async def _post_multipart(
#     url: str, data: Dict[str, Any], files: Dict[str, Any]
# ) -> Dict[str, Any]:
#     async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
#         try:
#             response = await client.post(url, data=data, files=files)
#             response.raise_for_status()
#             return response.json()
#         except httpx.HTTPStatusError as exc:  # pragma: no cover - thin wrapper
#             detail = _extract_error_detail(exc.response)
#             raise HTTPException(status_code=exc.response.status_code, detail=detail)
#         except httpx.RequestError as exc:  # pragma: no cover - network failure
#             raise HTTPException(status_code=502, detail=str(exc)) from exc


# def _extract_error_detail(response: httpx.Response) -> Any:
#     try:
#         payload = response.json()
#     except ValueError:
#         return response.text or "Upstream service returned an error"

#     if isinstance(payload, dict) and "detail" in payload:
#         return payload["detail"]
#     return payload


# @app.post("/gateway/ai-analysis/auto")
# async def gateway_ai_analysis_auto(
#     ticker: str = Form(...),
#     mapping_json: str = Form("core\\\\company_tickers_exchange.json"),
#     similarity_top_k: int = Form(5),
# ) -> Dict[str, Any]:
#     """Forward auto-fetch AI analysis requests to the AI Analysis service."""

#     payload = {
#         "ticker": ticker,
#         "mapping_json": mapping_json,
#         "similarity_top_k": similarity_top_k,
#     }
#     url = f"{settings.ai_analysis_base_url}/ai-analysis/auto"
#     return await _post_form(url, payload)


# @app.post("/gateway/ai-analysis/upload")
# async def gateway_ai_analysis_upload(
#     file: UploadFile = File(...),
#     similarity_top_k: int = Form(5),
# ) -> Dict[str, Any]:
#     """Forward file-upload AI analysis requests to the AI Analysis service."""

#     file_bytes = await file.read()
#     files = {
#         "file": (file.filename, file_bytes, file.content_type or "application/octet-stream")
#     }
#     payload = {"similarity_top_k": similarity_top_k}
#     url = f"{settings.ai_analysis_base_url}/ai-analysis/upload"
#     return await _post_multipart(url, payload, files)


# @app.post("/gateway/account-overview/upload")
# async def gateway_account_overview_upload(
#     item_list: UploadFile = File(...),
#     payment_history: UploadFile = File(...),
# ) -> Dict[str, Any]:
#     """Proxy Account Overview uploads to the Account Overview service."""

#     item_bytes, payment_bytes = await asyncio.gather(
#         item_list.read(), payment_history.read()
#     )
#     files = {
#         "item_list": (
#             item_list.filename,
#             item_bytes,
#             item_list.content_type or "application/octet-stream",
#         ),
#         "payment_history": (
#             payment_history.filename,
#             payment_bytes,
#             payment_history.content_type or "application/octet-stream",
#         ),
#     }
#     url = f"{settings.account_overview_base_url}/account-overview/upload"
#     return await _post_multipart(url, data={}, files=files)


# @app.post("/gateway/financial-statements")
# async def gateway_financial_statements(
#     payload: FinancialStatementGatewayRequest,
# ) -> Dict[str, Any]:
#     """Forward financial statement requests to the Financial Statement service."""

#     url = f"{settings.financial_statement_base_url}/statements"
#     return await _post_json(url, payload.normalised())


# @app.get("/healthz")
# async def healthz() -> Dict[str, str]:
#     """Basic gateway health endpoint."""

#     return {"status": "ok", "service": "gateway"}


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
from services.account_overview.main import account_app as account_overview_app
from services.AI_analysis.main import ai_analysis_app as ai_analysis_app
from services.financial_statement.main import financial_app as financial_statement_app
from fastapi import FastAPI

app = FastAPI(
    title="Credit AI Gateway",
    description="Gateway that forwards requests to the underlying microservices.",
    version="1.0.0",
)
app.mount("/account-overview", account_overview_app)
app.mount("/ai-analysis", ai_analysis_app)
app.mount("/financial-statement", financial_statement_app)