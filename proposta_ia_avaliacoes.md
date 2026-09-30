# Proposta de construção: recrutamento com IA e questionários por vaga

Versão: 2.0 — âmbito reorganizado após clarificação do utilizador  
Data: 11/09/2026  
Estado: planeamento; nenhum desenvolvimento iniciado neste trabalho  
Documentos: [Requisitos](requisitos.md) · [Tasks de construção](tasks.md) · [Diagnóstico do sistema actual](descricao_sistema.md)

## 1. Ideia central

O sistema ajuda o recrutador a compreender CVs pelo significado e a preparar perguntas adequadas a cada vaga. O recrutador define os critérios, revê as sugestões da IA e toma as decisões.

Dois produtos de IA independentes:

1. **Análise de CV:** perfil estruturado e compatibilidade com a vaga, com evidências verificáveis.
2. **Proposta de questionário:** perguntas geradas a partir da vaga e dos seus requisitos, com respostas esperadas e critérios de avaliação, para revisão e utilização pelo recrutador.

Gerar um questionário não exige que um candidato tenha sido registado ou que algum CV tenha sido analisado. O questionário base é associado à vaga, não personalizado a partir de dados pessoais do candidato.

## 2. Âmbito da primeira versão

| Incluído | Resultado |
|---|---|
| Autenticação e isolamento entre empresas | Cada recrutador trabalha apenas com dados autorizados. |
| Vagas e requisitos editáveis | Critérios claros e versionados para orientar a IA. |
| Recepção manual de CVs PDF/DOCX | Documentos válidos, identificados e consultáveis. |
| Análise semântica de CVs | Perfil, evidências, lacunas e pontuação explicável. |
| Ranking e revisão | Resultados por vaga sem substituir decisões humanas. |
| Geração de questionário por vaga | Rascunho com perguntas e rubricas relevantes. |
| Edição e aprovação do questionário | Recrutador pode alterar, remover, acrescentar e reordenar. |
| Versões e reutilização | Preservação do que foi aprovado e criação de novas versões. |
| Impressão do questionário | Folha de perguntas e guia de avaliação separados. |
| Entrevistas, feedback e painel existentes | Corrigir inconsistências e manter o percurso operacional. |

**Fora da primeira versão:** convites automáticos, ligação de resposta, portal do candidato, cronómetro, recolha de respostas, correcção automática de respostas de candidatos, fornecedor psicométrico, percentis, diagnóstico psicológico, combinação do questionário com ranking e aprendizagem automática com feedback.

Também ficam no backlog de expansão: OAuth Gmail/Outlook, importação automática por e-mail, gestão administrativa visual completa, relatórios avançados e publicação pública de vagas. A integração IMAP actual deve ser corrigida ou ficar desactivada na entrega enquanto não cumprir os requisitos de segurança e integridade. Não será removida nesta fase de documentação.

## 3. Jornada do recrutador

### Preparar vaga

Criar vaga → preencher descrição → adicionar requisitos → rever pesos e obrigatoriedade → guardar/publicar.

### Compreender candidatos

Carregar CV → acompanhar análise → consultar perfil e excertos → rever lacunas → comparar ranking → registar entrevista e decisão.

Exemplo: “Controlava entradas, saídas e reposição de mercadorias” pode sustentar experiência em gestão de stocks. Não comprova utilização de SAP ou outro produto não mencionado. A análise deve explicar essa distinção.

### Preparar questionário

Abrir vaga → separador **Questionário** → **Gerar proposta com IA** → escolher configuração → receber rascunho → rever/editar → aprovar → consultar ou imprimir.

O recrutador pode aplicar as perguntas numa entrevista ou fora da aplicação. O sistema não convida candidatos nem recolhe respostas nesta versão.

## 4. Geração da proposta de questionário

### Entradas

- Título, descrição e versão dos requisitos da vaga.
- Competências a avaliar, escolhidas dos requisitos ou adicionadas explicitamente.
- Categoria: raciocínio, conhecimento técnico e/ou situação de trabalho.
- Formato: resposta aberta, escolha única ou misto.
- Quantidade de perguntas, idioma e dificuldade pretendida.
- Duração total estimada como orientação; não existe cronómetro.

Os limites de quantidade e comprimento serão configuráveis. Dificuldade e duração geradas são estimativas editoriais, sem equivaler a calibração psicométrica.

### Saída por pergunta

| Campo | Conteúdo |
|---|---|
| Enunciado | Pergunta clara relacionada com a função. |
| Competência/requisito | Identificador e motivo da ligação à vaga. |
| Tipo e dificuldade estimada | Configuração editorial. |
| Opções | Apenas quando aplicável; sem duplicados. |
| Resposta esperada | Solução para escolha única ou pontos esperados para resposta aberta. |
| Critérios de avaliação | Aspectos que o recrutador deve observar. |
| Justificação | Razão pela qual a pergunta é relevante. |
| Tempo estimado | Indicação de esforço, sem garantia estatística. |
| Proveniência | Versões da vaga, instruções e modelo usados na geração. |

Não é necessário que uma pergunta situacional tenha uma única resposta correcta. A rubrica deve admitir alternativas justificadas.

### Exemplo ilustrativo

Vaga: gestor de armazém.  
Competência: controlo de inventário.

**Pergunta:** “O sistema indica 120 unidades, mas a contagem física encontra 105. Como investigaria a diferença antes de ajustar o stock?”

**Pontos esperados:** repetir/verificar contagem, conferir entradas e saídas, examinar documentos e movimentos recentes, identificar causa e seguir o procedimento de regularização.

**Critérios:** sequência de investigação, utilização de evidências, prevenção de correcção prematura e comunicação da divergência.

A IA produz uma proposta; o recrutador verifica se corresponde aos procedimentos e responsabilidades da organização.

## 5. Revisão, aprovação e versões

Estados: **rascunho → em revisão → aprovado → arquivado**.

Só o conteúdo aprovado é apresentado como pronto para aplicação. Rascunhos podem ser consultados e impressos com identificação clara de rascunho.

O recrutador pode editar perguntas, opções, respostas esperadas e rubricas; reordenar; acrescentar perguntas manuais; remover; pedir nova geração de uma pergunta ou do conjunto. Nova geração nunca substitui silenciosamente alterações humanas.

Uma versão aprovada é imutável. Editar cria novo rascunho. Alterações posteriores na vaga sinalizam desactualização; não mudam automaticamente um questionário aprovado.

A impressão tem dois modos: **folha de perguntas**, sem respostas/rubricas internas, e **guia do recrutador**, com critérios e respostas esperadas. Ambos mostram vaga e versão. Impressão do navegador com opção de guardar em PDF basta para o MVP.

## 6. IA para compreender CVs

Fluxo: documento → texto localizado/OCR quando necessário → perfil estruturado → evidências por requisito → validação → regras de pontuação → revisão.

Estados de evidência: evidenciado, parcialmente evidenciado, não evidenciado, contraditório e não avaliável.

O modelo interpreta; o sistema valida os excertos e calcula a pontuação através de política versionada. Datas sobrepostas, formação versus experiência e negação precisam de tratamento explícito. Informação em falta não deve ser inventada.

A primeira análise deve avaliar requisitos sobre trechos do CV; não é necessário instalar uma base vectorial antes de demonstrar essa necessidade. Pesquisa semântica e reclassificação são alternativas técnicas já investigadas no projecto. [Sentence Transformers — Retrieve & Re-Rank](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html).

Reanalisar preserva o resultado anterior e o estado de contratação. Resultados ligados a requisitos antigos devem aparecer como desactualizados. A IA não deve inferir características pessoais sensíveis nem personalidade a partir do CV.

## 7. Escolhas técnicas propostas

Manter React, FastAPI e PostgreSQL. Consolidar o backend em uma fonte antes de desenvolver novos módulos, preservando diferenças úteis da cópia existente.

Introduzir um serviço de IA com duas operações separadas: extrair/analisar perfil e gerar questionário. O fornecedor será substituível, com schema, versões de instruções, timeouts, controlo de custo e tratamento de erros.

Comparar API gerida e modelo privado com exemplos representativos e política de dados definida. Não contratar fornecedor nem fixar modelo apenas pela demonstração de um caso.

Execuções demoradas terão estado persistido, processamento em segundo plano e repetição idempotente. Falha de IA deve manter documentos e rascunhos anteriores e permitir nova tentativa.

A IA não deve receber ferramentas para executar comandos, enviar mensagens ou aprovar decisões. Texto de CV e descrição de vaga são dados; instruções neles contidas não podem modificar as regras do serviço.

## 8. Dados novos

| Entidade proposta | Responsabilidade |
|---|---|
| JobCriteriaVersion | Versão dos critérios usada na análise/geração. |
| ResumeVersion / AnalysisRun / Evidence | Documento, execução, evidências e resultados históricos. |
| Questionnaire | Identidade do questionário ligado à vaga/empresa. |
| QuestionnaireVersion | Configuração, estado, origem, criador, aprovador e datas. |
| QuestionnaireQuestion | Ordem, tipo, enunciado, opções, resposta esperada, rubrica e competência. |
| AIGenerationRun | Estado, modelo, instruções, custo/tempo quando disponível e falhas. |

Não criar entidades de convite, tentativa, resposta de candidato ou resultado psicométrico no MVP.

O questionário não altera o score do CV. Entrevista e feedback existentes continuam separados. Geração não exige candidato associado.

## 9. Critério de produto entregue

Um recrutador consegue criar uma vaga, receber um CV e obter análise com evidências; noutra acção independente, gera um questionário, revê o conteúdo, aprova uma versão e imprime apenas as perguntas para aplicação externa.

A demonstração deve funcionar com vaga sem candidatos para provar a independência do questionário. Após reabrir a página, edições e aprovação permanecem. A mesma operação com conta de outra empresa é recusada.

## 10. Limites da proposta

O produto gera propostas de perguntas de raciocínio, conhecimentos e situações profissionais. Não apresenta o conteúdo como diagnóstico, QI ou instrumento psicométrico validado.

A eventual introdução de psicometria formal exige decisão de produto e avaliação de adequação à função e ao uso, conforme orientação profissional consultada. Isso é uma expansão futura e não bloqueia a autoria de questionários agora pretendida. [OPM — Assessment Strategy](https://www.opm.gov/policy-data-oversight/assessment-and-selection/assessment-strategy/).

Os detalhes executáveis, dependências e critérios de conclusão estão em [tasks.md](tasks.md). As tarefas são planeamento: não foram implementadas.
