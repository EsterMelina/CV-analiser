# Backend — Sistema Inteligente de Análise e Recomendação de Candidatos

Backend completo da plataforma descrita no prompt mestre: autenticação,
base de dados, CRUD de vagas/requisitos/candidatos, upload de CVs,
extração de texto (PDF/DOCX), NLP, motor de matching/scoring explicável,
ranking por vaga, entrevistas, feedback do recrutador, integração de
e-mail (IMAP funcional; Gmail/Outlook com interface pronta, a aguardar
credenciais OAuth da empresa) e histórico de processamento.

**Não incluído neste entregável:** frontend (React/TypeScript) e
migrations Alembic formais (o schema é criado via `Base.metadata.create_all()`
para simplificar o desenvolvimento local — ver secção "Próximos passos").

## Stack

- Python 3.11+ · FastAPI + Pydantic v2 · SQLAlchemy 2.0 · PostgreSQL
- JWT (python-jose) + bcrypt (passlib)
- PyMuPDF + python-docx (extração de texto de CVs)
- scikit-learn (TF-IDF), sem carregar modelos locais por defeito
  quando disponível (similaridade semântica)
- Fernet (`cryptography`) para cifrar credenciais de e-mail em repouso

## 1. Instalação

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Base de dados

Opção A — Docker: `docker compose up -d` (usa as credenciais do `docker-compose.yml`).

Opção B — PostgreSQL já instalado localmente: crie a base de dados e o
utilizador indicados no `.env` (ver secção seguinte).

## 3. Variáveis de ambiente

```bash
cp .env.example .env
```

O `.env` aceita **ou** variáveis separadas (estilo Laravel) **ou** uma
`DATABASE_URL` completa:

```dotenv
DB_CONNECTION=pgsql
DB_HOST=127.0.0.1
DB_PORT=5432
DB_DATABASE=recruiter_db
DB_USERNAME=recruiter_user
DB_PASSWORD=recruiter_pass
```

Se `DATABASE_URL` estiver definida explicitamente, tem prioridade sobre as
variáveis `DB_*`. Gere um `SECRET_KEY` forte antes de qualquer uso fora do
ambiente local: `python -c "import secrets; print(secrets.token_hex(32))"`
— este valor também é usado para cifrar credenciais de e-mail (ver secção
"Segurança" abaixo), por isso alterá-lo depois invalida contas de e-mail
já ligadas.

## 4. Popular dados de exemplo

```bash
python -m app.seed
```

Cria um administrador (`admin@sistema.co.mz` / `Admin@123`), uma empresa
de exemplo (`TechMoz Solutions`), um recrutador
(`recrutamento@techmoz.co.mz` / `Recruta@123`) e uma vaga de exemplo
(`VAG-2026-014` — Desenvolvedor Backend) com requisitos.
**Altere estas passwords antes de usar em qualquer ambiente partilhado.**

## 5. Correr a aplicação

```bash
uvicorn app.main:app --reload
```

Documentação interativa: http://localhost:8000/docs

## 6. Fluxo de teste rápido via `/docs`

1. `POST /api/auth/login` com `recrutamento@techmoz.co.mz` / `Recruta@123` → copiar `access_token` e usar "Authorize" no Swagger.
2. `GET /api/jobs` e `GET /api/jobs/{id}/requirements` → ver a vaga de exemplo.
3. `POST /api/jobs/{id}/cvs` (multipart/form-data) → carregar um CV real (.pdf ou .docx).
4. `POST /api/cvs/{resume_id}/analyze` → corre o pipeline de NLP/matching/scoring sobre esse CV.
5. `GET /api/cvs/{resume_id}/analysis` → ver o score e o *breakdown* explicável (pontos fortes/lacunas).
6. `GET /api/jobs/{id}/ranking` → ver o ranking ordenado de todos os candidatos da vaga.
7. `POST /api/applications/{id}/interview` → agendar entrevista para um candidato selecionado.
8. `PUT /api/applications/{id}/feedback` → registar o resultado/avaliação do recrutador.

## 7. Correr a suite de testes

SQLite em memória — não precisa do PostgreSQL a correr. Executar nesta pasta
ou na raiz do projecto; ambas usam exclusivamente `backend/`:

```bash
python -m pytest -v
```

A suite ignora `.env`, isola uploads em pastas temporárias, bloqueia rede e
carregamento de modelos e usa TF-IDF local. Inclui fixtures de duas empresas.
Ver [o registo da base controlada](../docs/base-controlada.md).

Cobre autenticação/RBAC, CRUD de vagas e requisitos, upload e deduplicação
de candidatos, o motor de NLP/matching/scoring (unitário e de ponta a
ponta com CVs `.docx` reais gerados em memória), ranking, entrevistas,
feedback do recrutador, integração de e-mail (sem rede real) e histórico
de processamento — ver secção 37 do prompt mestre. Testes que dependem de
`python-docx` são ignorados automaticamente (`skip`) se a biblioteca não
estiver instalada.

## Estrutura

```
app/
├── core/            # configuração (.env), BD, segurança (JWT/hash), cifragem (crypto.py)
├── models/          # entidades SQLAlchemy — ver "Modelo de dados" abaixo
├── schemas/         # schemas Pydantic (validação/serialização)
├── api/             # routers FastAPI (um por área funcional)
├── services/        # lógica de negócio: extração de texto, NLP, matching/scoring,
│                    # análise (orquestração do pipeline), sincronização de e-mail
├── integrations/
│   └── email/       # camada de abstração de e-mail (base/factory + adaptadores
│                     # IMAP funcional, Gmail/Outlook com interface OAuth pronta)
├── seed.py          # dados de exemplo
└── main.py          # ponto de entrada da aplicação

tests/               # pytest — ver secção 7
```

## Modelo de dados — pontos-chave

- **Candidate ≠ Application**: um candidato (pessoa) pode ter várias
  candidaturas a vagas diferentes. Deduplicação pelo e-mail (secção 13).
- **CandidateMatch**: um registo por candidatura, com o score, a etiqueta
  de recomendação e o *breakdown* completo por requisito (JSON) — é a base
  da explicabilidade (secção 25). `Application.score` replica o valor
  numérico apenas para ordenar/filtrar sem juntar tabelas.
- **CandidateSkill/Education/Language/Certification/Project**: perfil
  estruturado extraído do CV mais recente do candidato (secção 14).
- **ProcessingLog**: um registo por documento processado (upload ou
  e-mail), com o resultado e eventuais erros (secção 31).
- **EmailAccount/EmailMessage/EmailAttachment**: integração de e-mail
  (secções 9-13); credenciais sempre cifradas (`app/core/crypto.py`),
  nunca em texto simples.

## Motor de matching/scoring — como funciona

1. **Extração de texto** (`services/text_extraction.py`): PyMuPDF para
   PDF, python-docx para DOCX.
2. **NLP em camadas** (`services/nlp_extraction.py`): dicionário de
   sinónimos (rápido, explicável) para competências conhecidas; datas de
   experiência e linhas de formação por regras/palavras-chave.
3. **Matching** (`services/matching_engine.py`): para requisitos não
   encontrados por sinónimo, usa similaridade semântica
   (`services/embeddings.py` — TF-IDF/scikit-learn por defeito;
   sentence-transformers requer instalação e `LOCAL_EMBEDDINGS_ENABLED=true`) sobre o texto
   completo do CV, em vez de apenas "a palavra existe?" (secção 16).
4. **Scoring**: score ponderado 0–100 pelos pesos dos requisitos da vaga.
   Requisitos obrigatórios em falta **nunca são escondidos**, mesmo com
   score alto — a etiqueta de recomendação (`Recomendado` / `Avaliar` /
   `Baixa compatibilidade` / `Requisito obrigatório ausente`) reflete
   isso explicitamente (secção 19).

Este motor é intencionalmente "regras + NLP + embeddings" (secção 24) —
a base para evoluir para Machine Learning supervisionado quando houver
dados históricos suficientes (score, entrevista, contratação, feedback já
ficam todos persistidos para esse fim).

## Papéis e permissões

- **admin**: gere empresas e utilizadores (`/api/companies`, `/api/users`).
- **recruiter**: cria/gere vagas, requisitos, candidatos, candidaturas,
  entrevistas e feedback, sempre restrito à empresa a que pertence.
- `require_roles` (`app/api/deps.py`) permite adicionar novos papéis sem
  alterar os endpoints existentes.

## Segurança implementada

- Passwords com hash bcrypt; credenciais de e-mail cifradas com Fernet
  (nunca em texto simples — secções 10 e 35).
- JWT de acesso (curta duração) + refresh; RBAC em todos os endpoints sensíveis.
- Validação de tipo/tamanho de ficheiro no upload; isolamento de dados por
  empresa (`company_id`) em todos os recursos multi-tenant.
- O motor de matching nunca recebe nem usa características pessoais
  irrelevantes (foto, género, idade, etc. — secção 35).

Ainda por implementar: rate limiting, logs de auditoria estruturados,
blacklist de refresh tokens, fila de tarefas assíncrona para sincronização
de e-mail em produção (secção 40).

## Integração de e-mail — estado real

- **IMAP**: totalmente funcional (usa só a biblioteca padrão do Python).
- **Gmail / Microsoft 365**: a interface está pronta (`EmailProvider`) e o
  resto do sistema já funciona de forma agnóstica ao provedor, mas a troca
  de tokens OAuth real exige que a empresa registe uma app na Google Cloud
  Console / Azure AD — ver docstring de
  `app/integrations/email/oauth_providers.py` para os passos exatos.

## Próximos passos (não incluídos neste entregável)

1. **Frontend React/TypeScript** consumindo esta API.
2. **Migrations Alembic** formais (atualmente `Base.metadata.create_all()`).
3. Completar a troca de tokens OAuth real para Gmail/Outlook.
4. Fila de tarefas assíncrona (Celery/RQ) para sincronização periódica de
   e-mail e processamento de grandes volumes de CVs (secção 40).
5. Avaliação do modelo com métricas formais (Precision@K, Recall@K, NDCG —
   secção 36) assim que houver dados históricos de contratação suficientes.
