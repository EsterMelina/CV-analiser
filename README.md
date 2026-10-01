# Jornadas

`backend/` é a única fonte da API. `frontend/` contém a aplicação React.

Para instalar e configurar a API, seguir [backend/README.md](backend/README.md).
Executar a partir da raiz:

```powershell
cd backend
python -m uvicorn app.main:app --reload
```

Num segundo terminal, na pasta `backend` e com o ambiente virtual activo:

```powershell
python -m app.worker
```

Cada novo CV carregado entra automaticamente na fila de análise quando a IA
está configurada e a vaga tem requisitos com pesos positivos no total. A API
e o worker devem permanecer ligados. O botão de análise manual continua
disponível para novas análises e tentativas após uma falha. Carregar novamente
o mesmo ficheiro para a mesma candidatura não cria outra análise.
Se a IA ou os requisitos não estiverem configurados, o CV é guardado para
análise manual posterior. O processamento está sujeito aos limites do fornecedor.

O nome e o e-mail do candidato são extraídos do texto do PDF/DOCX durante o
upload; o formulário pede apenas o ficheiro. A leitura procura um campo de nome ou
um nome no cabeçalho. Quando não é identificado (incluindo PDFs digitalizados
sem texto), aparece “Nome não identificado”; nomes já guardados são preservados.
Se não existir um e-mail legível, ou existirem vários endereços de contacto
ambíguos, o upload indica que é necessário enviar uma versão com um único
e-mail do candidato. Endereços após a secção de referências são ignorados.

Na página da vaga, o separador **Requisitos** permite importar um `.txt`
(UTF-8/UTF-16, até 100 KB), com um requisito por linha. Listas com marcadores
ou números são aceites. A importação acrescenta requisitos sem apagar os
existentes e ignora repetições. Reveja categorias, níveis, obrigatoriedade e
pesos após importar. Os novos itens usam categoria Outros, nível Intermédio
e não são obrigatórios; numa vaga vazia os pesos são iguais e somam 100%,
caso contrário cada item novo recebe peso 10%. O texto longo é preservado
na descrição. A importação actualiza a versão dos critérios da vaga.

Use **Descarregar modelo TXT** nesse separador, substitua os exemplos pelos
requisitos da vaga e importe o ficheiro preenchido. O modelo também está
disponível em [modelo-requisitos.txt](frontend/public/modelo-requisitos.txt).

Para testar, a partir da raiz ou de `backend/`:

```powershell
python -m pytest -q
```

Os testes configuram SQLite em memória, uploads temporários e bloqueios de
rede/modelos antes de importar a aplicação. Não é necessário configurar `.env`,
PostgreSQL, IMAP ou um fornecedor de IA para os executar.

Consultar [o registo de consolidação e testes](docs/base-controlada.md).
