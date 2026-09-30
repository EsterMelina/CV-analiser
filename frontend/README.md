# Frontend — Sistema Inteligente de Recrutamento

React + TypeScript + Tailwind CSS + React Query + React Router, consumindo
a API REST do backend (`../backend`).

## Instalação

```bash
cd frontend
npm install
npm run dev
```

Abre em http://localhost:5173. O servidor de desenvolvimento (Vite) já
está configurado para reencaminhar pedidos `/api/*` para
`http://localhost:8000` (ver `vite.config.ts`) — por isso **o backend tem
de estar a correr** (`python -m uvicorn app.main:app --reload` na pasta `backend/` da raiz do projecto; a partir de `frontend/`, executar primeiro `cd ../backend`)
para a aplicação funcionar.

## Login de teste

Use os dados criados pelo `python -m app.seed` do backend:

```
recrutamento@techmoz.co.mz / Recruta@123
```

## Estrutura

```
src/
├── pages/       # uma página por rota
├── components/  # Layout (barra lateral), RecommendationBadge, ProtectedRoute
├── context/     # AuthContext (sessão, login/logout)
├── lib/api.ts   # cliente Axios com refresh automático de token JWT
└── types/       # tipos TypeScript espelhando os schemas Pydantic do backend
```

## Páginas incluídas

- `/login` — autenticação
- `/` — dashboard com métricas agregadas
- `/jobs`, `/jobs/new`, `/jobs/:id` — gestão de vagas, requisitos, upload de
  CVs, candidatos e ranking (tudo dentro de `/jobs/:id`, por separadores)
- `/jobs/:jobId/applications/:id` — detalhe do candidato: score explicável
  por requisito, entrevistas e feedback do recrutador
- `/settings/email` — integração de e-mail (IMAP funcional; Gmail/Outlook
  com aviso claro sobre a configuração OAuth pendente)

## Não incluído nesta fase

- Páginas de gestão de utilizadores/empresas (admin) — apenas a API existe;
  a interface pode ser acrescentada seguindo o mesmo padrão das páginas de
  vagas.
- Histórico de processamento (`/api/processing-logs`) não tem página
  dedicada ainda — os dados já existem na API.
- Testes de frontend (ex: Vitest + Testing Library) — o backend já tem
  suite própria (ver `backend/tests`).
