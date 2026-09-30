# T09 — Modelo externo

Decisão de 15/09/2026: usar uma API externa devido às limitações de hardware.
Fornecedor e modelo ainda não seleccionados. O ambiente passou para
`AI_PROVIDER=openai-compatible`, com endpoint e modelo por preencher.
O adaptador suporta Chat Completions com JSON mode; a compatibilidade do serviço
escolhido deve ser confirmada num teste real. Não foram feitas chamadas pagas
nem enviados CVs durante esta alteração.
Consulte a [configuração actual](analise-automatica.md).

## Histórico (decisões anteriores, substituídas)

Actualização de 14/09/2026: foi seleccionado o Ollama local com `qwen2.5:7b`,
já instalado neste ambiente. A integração e a configuração estão implementadas;
foi executado um teste real com texto fictício. Consulte
[análise automática](analise-automatica.md) para execução, política e limites.
O levantamento abaixo documenta a situação anterior a esta decisão.

A integração real permanece desactivada até serem definidos fornecedor, modelo,
credenciais, orçamento e dados permitidos. Não foram enviados CVs a terceiros.

| Opção | Benefício | Trabalho necessário antes de activar |
|---|---|---|
| API gerida através de adaptador JSON | Operação do modelo pelo fornecedor | Contrato de dados, região/retenção, preços, limites e avaliação de fidelidade. |
| Modelo privado através do mesmo contrato | Controlo da infraestrutura e dos dados | Hardware, operação, segurança, latência/custo medidos e avaliação de fidelidade. |
| Simulador local `mock-v1` | Testar os fluxos sem rede nem credenciais | Não avalia significado nem substitui revisão de conteúdo; não utilizar para decisões de recrutamento. |

O contrato tem operações `profile`, `evaluate` e `questionnaire`, JSON Schema,
versão de contrato/instruções, timeout e limite de saída. Um adaptador real deve
aceitar esse contrato; não se trata de uma integração pronta com qualquer API
comercial. Configuração: `AI_PROVIDER=json-http`, `AI_ENDPOINT`, `AI_MODEL`,
`AI_API_KEY`, `AI_REAL_ENABLED=true` e `AI_DATA_APPROVED=true`.

Não há custos reais medidos ou fornecedor seleccionado. T09 continua pendente.
O simulador permite desenvolver T10 em diante, como previsto no backlog.
