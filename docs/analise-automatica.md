# Análise automática de CVs com modelo externo

## Configuração actual — 15/09/2026

Por limitações de hardware, a execução passa para uma API externa. Fornecedor e
modelo ainda por seleccionar. O adaptador está implementado; a análise só fica
disponível após preencher a configuração no `backend/.env`:

```dotenv
AI_PROVIDER=openai-compatible
AI_ENDPOINT=
AI_MODEL=
AI_API_KEY=
AI_REAL_ENABLED=true
AI_DATA_APPROVED=true
AI_TIMEOUT_SECONDS=120
LOCAL_EMBEDDINGS_ENABLED=false
```

`AI_ENDPOINT` deve ser a URL HTTPS completa, incluindo `/chat/completions`.
O modelo deve suportar mensagens system/user e JSON mode (`json_object`).
A chave permanece no backend. Ao executar a análise, o texto extraído do CV e
os requisitos são enviados ao fornecedor configurado.

A análise usa duas chamadas (perfil e avaliação); o questionário usa uma.
Com esta configuração, o worker tem prazo de 270 segundos e reserva de 280 segundos.
A resposta tem limite de 256 KB. Respostas incompletas, JSON inválido e citações
sem suporte são recusados. A validação do esquema e a pontuação mantêm-se no backend.
Reinicie a API e o worker após alterar o `.env`. A rota
`/api/analysis-configuration` verifica o preenchimento, sem testar conectividade.

Sentence Transformers deixou de ser instalado e carregado por defeito; o matching
antigo usa TF-IDF. A análise externa não exige Ollama nem downloads de modelos.
Ainda não foi feito um teste real: falta seleccionar o serviço e configurar a chave.

Contrato: [Chat Completions — documentação oficial OpenAI](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create).
JSON mode garante JSON, não o esquema; este é validado pela aplicação.

## Histórico — implementação Ollama (substituída pela configuração acima)

Os detalhes e comandos locais abaixo documentam a implementação anterior e só
se aplicam caso seja explicitamente seleccionado o adaptador opcional `ollama`.

A análise compara as evidências do CV com os requisitos versionados da vaga,
calcula a compatibilidade e publica a recomendação no detalhe e no ranking.
Não existe aprovação manual necessária para concluir uma análise. Agendar uma
entrevista continua a ser uma acção operacional separada.

Actualização de desempenho: a análise Ollama utiliza uma única chamada para avaliar
os requisitos, referenciando fragmentos do CV por identificador. O backend recupera
as citações exactas e valida-as. O resumo do perfil inclui apenas requisitos comprovados;
não há uma segunda chamada para reconstruir todo o histórico profissional. A janela
de contexto é reduzida para 4096 tokens em entradas curtas e a geração da avaliação
fica limitada a 1200 tokens, com justificações curtas. Falhas de execução são apresentadas
como erros mesmo quando a candidatura ainda tem um estado de processamento em cache.
Durante a avaliação, a resposta é recebida em partes e o progresso é persistido
a cada cinco segundos de geração. O prazo do worker continua limitado a 630 segundos;
os resultados só são publicados depois de a resposta estar completa e validada.

## Configuração local

O ambiente desta implementação usa o modelo já instalado `qwen2.5:7b`.
No `backend/.env`:

```dotenv
AI_PROVIDER=ollama
AI_ENDPOINT=http://127.0.0.1:11434
AI_MODEL=qwen2.5:7b
AI_REAL_ENABLED=true
AI_DATA_APPROVED=true
AI_TIMEOUT_SECONDS=300
```

O adaptador aceita apenas Ollama em loopback e modelos locais. Não requer chave
de API. Inicie o Ollama e, em terminais separados a partir de `backend`, execute:

```powershell
python -m uvicorn app.main:app --reload
python -m app.worker
```

Reinicie os processos existentes após alterar a configuração. O worker tem
prazo de 630 segundos para as duas operações e reserva de 640 segundos;
resultados de workers cuja reserva expirou não são publicados.

O histórico `mock-v1` não muda retroactivamente. Clique em **Analisar CV com IA**
para criar uma análise real. Fora dos testes, pedidos com simulador são recusados
antes de entrar na fila. `/api/analysis-configuration` permite verificar a
configuração sem expor credenciais; não substitui um teste de conectividade.

## Resultado e limites

A política `evidence-v2-automatic` atribui 100% do peso a um requisito evidenciado,
50% a um requisito parcial e zero a ausência de evidência ou contradição.
Com os obrigatórios comprovados: pelo menos 80% é **Recomendado**, de 50% até
menos de 80% é **Compatibilidade parcial**, e abaixo de 50% é **Baixa compatibilidade**.
Qualquer obrigatório sem comprovação completa prevalece com **Requisito obrigatório
ausente**. Isto significa ausência de comprovação documental, não incapacidade do candidato.
Os limiares são uma política explícita do produto, não uma probabilidade calibrada.

As conclusões usam somente os requisitos com pesos configurados na vaga. A descrição
da vaga é contexto para interpretar esses requisitos. Critérios que precisem de
contribuir para a pontuação devem estar na lista de requisitos.

O modelo é executado com contexto de 8192 tokens, geração até 2500 tokens e limite
conservador de entrada de 15000 caracteres incluindo esquema e instruções. Entradas
maiores, saídas incompletas, citações inventadas e respostas fora do contrato são
recusadas. PDFs digitalizados sem texto continuam sem avaliação; não há OCR.
O tempo depende do hardware: neste ambiente o Ollama usa CPU.

Integração baseada na [API Generate](https://docs.ollama.com/api/generate) e nas
[respostas estruturadas](https://docs.ollama.com/capabilities/structured-outputs).
O esquema enviado ao compilador local mantém a estrutura; limites de tamanho e
formatos são validados pelo Pydantic após a resposta.
