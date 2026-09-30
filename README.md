# Jornadas

`backend/` é a única fonte da API. `frontend/` contém a aplicação React.

Para instalar e configurar a API, seguir [backend/README.md](backend/README.md).
Executar a partir da raiz:

```powershell
cd backend
python -m uvicorn app.main:app --reload
```

Para testar, a partir da raiz ou de `backend/`:

```powershell
python -m pytest -q
```

Os testes configuram SQLite em memória, uploads temporários e bloqueios de
rede/modelos antes de importar a aplicação. Não é necessário configurar `.env`,
PostgreSQL, IMAP ou um fornecedor de IA para os executar.

Consultar [o registo de consolidação e testes](docs/base-controlada.md).
