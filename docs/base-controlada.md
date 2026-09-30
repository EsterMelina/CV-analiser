# T01 e T02 — base controlada

## Consolidação em 11/09/2026

A fonte executável é `backend/`. O README do frontend já apontava para a API
da raiz; os dois ficheiros `pytest.ini` seleccionam os testes dessa fonte.
Não existe repositório Git nesta pasta, pelo que não foi possível obter um diff
contra commits anteriores. Todas as alterações encontradas foram preservadas.

A comparação de todos os ficheiros da antiga `frontend/backend/`, incluindo
ficheiros ocultos, encontrou seis diferenças e nenhum ficheiro exclusivo:

| Ficheiro | Decisão |
|---|---|
| `app/core/config.py` | Preservar a configuração da raiz que ignora `.env` em testes. |
| `app/core/database.py` | Preservar StaticPool para SQLite em memória partilhado. |
| `app/services/nlp_extraction.py` | Preservar limites de palavras de Java/Excel da raiz. |
| `tests/conftest.py` | Preservar e completar o isolamento existente na raiz. |
| `tests/test_email_integration.py` | Preservar o simulador de IMAP, sem ligação real. |
| `tests/test_nlp_extraction.py` | Preservar os três testes adicionais Java/JavaScript/Excel. |

A cópia foi movida integralmente para `.maintenance/frontend-backend-original/`.
Os 73 ficheiros foram verificados após a movimentação contra o manifesto SHA-256
em `.maintenance/frontend-backend-manifest.json`. Este arquivo é histórico,
excluído da descoberta de testes, e não deve ser usado para executar a API.
Não foram removidos ou movidos `.env` nem uploads do backend principal.
As referências à cópia nos documentos de diagnóstico descrevem o estado anterior.

Para recuperar um ficheiro antigo, consultar o manifesto e copiá-lo do arquivo
para uma pasta de revisão; comparar antes de substituir a fonte actual.

## Infraestrutura de testes

`backend/tests/conftest.py` configura o ambiente antes de importar `app`:

- Perfil `test` sem leitura de `.env`, segredo fictício e BD SQLite em memória.
- Mesmo engine para arranque, `SessionLocal` e pedidos; tabelas recriadas por teste.
- Uploads em directórios temporários e limpeza das substituições de dependências.
- Bloqueio de engines de BD externos, DNS e sockets de rede. A única excepção
  é o socketpair interno que o asyncio necessita no Windows.
- Backend TF-IDF local e construtor de SentenceTransformer bloqueado, com modo
  offline de Hugging Face. IMAP é substituído por um simulador no teste.
- Fixtures de duas empresas, dois recrutadores autenticáveis e duas vagas.
  `test_test_isolation.py` verifica configuração, engine, uploads, bloqueios e
  acesso às vagas de cada empresa. Não certifica o isolamento de candidatos,
  cuja correcção pertence à T04.

## Comportamento inicial

Na primeira execução, o sandbox impediu acesso ao directório temporário padrão
do pytest no Windows. A repetição com essa permissão produziu **69 testes
aprovados e 1 falha**: o endereço `recruitment@example.test` era rejeitado pelo
validador de e-mail (HTTP 422), antes de chamar o simulador IMAP. O dado foi
corrigido para `recruitment@example.com`, mantendo a rede bloqueada.

Há avisos de depreciação de `datetime.utcnow()` na dependência `python-jose`.
O cache do pytest também encontrou restrições de permissões neste ambiente;
`-p no:cacheprovider` permite verificar sem escrever esse cache.

Valida??o final a partir da raiz: `python -m pytest -q --tb=short -p no:cacheprovider`
? **77 aprovados**, sem falhas nem testes ignorados (Python 3.12.8).
