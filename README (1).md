# Controle de Vagas - SPDM PAIS

Protótipo em Python/Streamlit para substituir a planilha manual do Google Drive.
Tema visual verde/preto, com painel de indicadores e várias abas de sistema.

## Campos da vaga

ID, Unidade, Especialidade, Data, Período, Especificidade, Data de alocação
(dia que a vaga chegou) e COD do médico.

- **COD vazio** → vaga considerada ABERTA
- **COD = 1** → vaga considerada CANCELADA (destacada em vermelho)
- **COD de um médico cadastrado** → vaga considerada FECHADA (nome/CRM/CPF/telefone
  aparecem automaticamente na visão detalhada, puxados da aba Médicos)

## Abas do sistema

1. **Nova vaga** — cadastro manual completo
2. **Vagas cadastradas** — tabela editável: o COD pode ser alterado direto na célula
   (fechar, abrir ou cancelar vaga) com botão "Salvar alterações de COD"; abaixo,
   uma visão detalhada com os dados do médico já cruzados e cores por situação.
   Também permite edição completa ou exclusão de uma vaga específica.
3. **Médicos cadastrados** — cadastro manual (COD, Nome, CRM, CPF, Telefone) e
   **importação em lote via Excel**, com mapeamento de colunas do arquivo.
4. **Importar Excel** — sobe um `.xlsx` de vagas extraído do sistema da contratante,
   com mapeamento de colunas. Vaga com ID já existente é atualizada; ID novo é inserido.
5. **Exportar** — baixa um `.xlsx` real (não CSV) com cada informação em sua própria
   coluna: ID, Unidade, Especialidade, Data, Período, Especificidade, Data Alocação,
   Código, Médico Nome, CPF, CRM, Tel.

## O que essa versão já resolve (mesmo sem API da contratante)

- **Data por seletor**, período por lista fixa — impossível digitar em formato errado
- **Bloqueio de ID duplicado** no cadastro manual
- **Importação em lote** de vagas e de médicos via Excel, sem redigitação manual
- **COD "1" reservado para cancelamento**, destacado visualmente em vermelho
- **Campos obrigatórios reais** — não salva vaga incompleta
- **Filtros** por Unidade, Período e Situação (aberta/fechada/cancelada)
- **Exportação em Excel de verdade**, com colunas separadas corretamente

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
