# Controle de Vagas - SPDM PAIS

Protótipo em Python/Streamlit para substituir a planilha manual do Google Drive.

## O que essa versão já resolve (mesmo sem API da contratante)

- **Data e período por seletor**, não texto livre — impossível digitar em formato errado
- **Bloqueio de ID duplicado** — não deixa cadastrar a mesma vaga duas vezes
- **Checagem de conflito de horário** — avisa se o mesmo médico já está alocado em outra vaga que se sobrepõe
- **Campos obrigatórios reais** — não salva vaga incompleta
- **Filtros** por Unidade, Status e Período na tela de visualização
- **Edição e exclusão** de vagas já cadastradas
- **Exportação** para CSV/Excel a qualquer momento

## Como rodar

1. Instale as dependências (uma vez só):
   ```
   pip install -r requirements.txt
   ```

2. Rode o app:
   ```
   streamlit run app.py
   ```

3. Abrirá automaticamente no navegador (geralmente `http://localhost:8501`).

Os dados ficam salvos em `vagas.db` (SQLite), na mesma pasta — não se perdem ao fechar o programa.

## Próximo passo (quando houver exportação do sistema da contratante)

Quando vocês conseguirem um export (mesmo manual, ex: baixar Excel toda segunda) do sistema
da contratante, dá para automatizar ainda mais: os campos Unidade/Especialidade/Data/Período
passam a ser preenchidos automaticamente ao digitar o ID (via `pandas.merge`), e a digitação
manual fica restrita aos dados do médico (Nome, CRM, CPF, Telefone) — que é a única parte que
realmente depende de vocês.

## Para publicar para a equipe toda usar (não só local)

- **Streamlit Community Cloud** (gratuito, mais simples): sobe o projeto num repositório GitHub
  e publica com poucos cliques.
- **Servidor interno da empresa**: rodar com `streamlit run app.py --server.port 8501` num
  servidor acessível pela rede interna.
- Nesses casos, trocar o SQLite por um banco compartilhado (Postgres/MySQL) é recomendado,
  para múltiplos usuários editarem ao mesmo tempo sem conflito de arquivo local.
