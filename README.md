# Controle de Vagas - SPDM PAIS

Protótipo em Python/Streamlit para substituir a planilha manual do Google Drive.

## Campos da vaga

ID, Unidade, Especialidade, Data, Período, Especificidade, Data de alocação
(dia que a vaga chegou) e COD do médico (se a vaga estiver fechada).

## Abas do sistema

1. **Nova vaga** — cadastro manual com os campos acima
2. **Vagas cadastradas** — visualização, filtros (Unidade/Período/Situação), edição e exclusão
3. **Médicos cadastrados** — cadastro de médicos com COD, Nome, CRM, CPF, Telefone;
   o COD escolhido aqui é o mesmo usado para fechar uma vaga
4. **Importar Excel** — sobe um arquivo .xlsx extraído do sistema da contratante,
   mostra uma prévia e deixa você mapear livremente qual coluna do arquivo
   corresponde a ID/Unidade/Especialidade/Data/Período/Especificidade.
   Vagas com ID já existente são atualizadas; vagas novas são inseridas.
5. **Exportar** — baixa tudo (vagas + médico alocado) em CSV

## O que essa versão já resolve (mesmo sem API da contratante)

- **Data por seletor**, período por lista fixa — impossível digitar em formato errado
- **Bloqueio de ID duplicado** no cadastro manual
- **Importação em lote** do Excel do sistema da contratante, sem redigitação manual de
  ID/Unidade/Especialidade/Data/Período/Especificidade
- **Campos obrigatórios reais** — não salva vaga incompleta
- **Filtros** por Unidade, Período e Situação (aberta/fechada) na tela de visualização
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
