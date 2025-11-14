# Credit AI Gateway

This FastAPI application exposes a lightweight API gateway that forwards calls to the
individual Credit AI microservices.  It provides three public routes that mirror the
available functionality across the deployed services:

| Gateway route | Method | Target service | Service endpoint |
| ------------- | ------ | -------------- | ---------------- |
| `/gateway/ai-analysis/auto` | `POST` | AI Analysis | `/ai-analysis/auto` |
| `/gateway/ai-analysis/upload` | `POST` | AI Analysis | `/ai-analysis/upload` |
| `/gateway/account-overview/upload` | `POST` | Account Overview | `/account-overview/upload` |
| `/gateway/financial-statements` | `POST` | Financial Statement | `/statements` |

The gateway is configured with environment variables so the upstream service URLs can be
changed without modifying code.  Requests received at the gateway are forwarded using
`httpx.AsyncClient`, and the JSON payload returned by the downstream service is passed
straight back to the caller.  Any HTTP errors from the services are normalised into
`HTTPException` responses so clients receive consistent error details.

## Running the gateway

```bash
uvicorn main:app --reload
```

The command above launches the FastAPI application locally.  The downstream services are
expected to be reachable at the URLs defined by the following environment variables
(defaults shown in parentheses):

- `AI_ANALYSIS_SERVICE_URL` (`http://localhost:8000`)
- `ACCOUNT_OVERVIEW_SERVICE_URL` (`http://localhost:8002`)
- `FINANCIAL_STATEMENT_SERVICE_URL` (`http://localhost:8001/api/v1`)
- `GATEWAY_REQUEST_TIMEOUT` (`60`)

These variables allow the gateway to be used as the single entry point for the three
microservices once they are deployed.
