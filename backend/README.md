# Territory Growth Intelligence Backend

## Local setup

```powershell
uv sync
uv run uvicorn app.main:app --reload
```

## Database migrations

```powershell
uv run alembic upgrade head
```
