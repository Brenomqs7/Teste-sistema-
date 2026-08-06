import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

DB_PATH = "vagas.db"

# ---------------------------------------------------------------
# BANCO DE DADOS
# ---------------------------------------------------------------

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS medicos (
            cod TEXT PRIMARY KEY,
            nome TEXT,
            crm TEXT,
            cpf TEXT,
            telefone TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vagas (
            id TEXT PRIMARY KEY,
            unidade TEXT,
            especialidade TEXT,
            data TEXT,
            periodo TEXT,
            especificidade TEXT,
            data_alocacao TEXT,
            cod TEXT,
            criado_em TEXT,
            atualizado_em TEXT
        )
    """)
    conn.commit()
    return conn


conn = get_conn()

PERIODOS = ["DIURNO", "NOTURNO", "MANHÃ", "TARDE"]

st.set_page_config(page_title="Controle de Vagas - PAIS", layout="wide")
st.title("🏥 Controle de Vagas - SPDM PAIS")
st.caption("Substitui a planilha manual do Drive.")

aba1, aba2, aba3, aba4, aba5 = st.tabs(
    ["➕ Nova vaga", "📋 Vagas cadastradas", "🩺 Médicos cadastrados", "📥 Importar Excel", "📤 Exportar"]
)

# ---------------------------------------------------------------
# ABA 1 - CADASTRO DE VAGA
# ---------------------------------------------------------------
with aba1:
    st.subheader("Cadastrar vaga")

    editar_id = st.session_state.get("editar_id")
    vaga_existente = None
    if editar_id:
        row = conn.execute("SELECT * FROM vagas WHERE id=?", (editar_id,)).fetchone()
        if row:
            cols = [c[0] for c in conn.execute("PRAGMA table_info(vagas)").fetchall()]
            vaga_existente = dict(zip(cols, row))
            st.info(f"Editando vaga ID {editar_id}")

    medicos_df = pd.read_sql("SELECT cod, nome FROM medicos ORDER BY nome", conn)
    opcoes_medico = ["(vaga aberta / sem médico)"] + [
        f"{row.cod} - {row.nome}" for row in medicos_df.itertuples()
    ]

    with st.form("form_vaga", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            vaga_id = st.text_input(
                "ID da vaga (igual ao sistema da contratante) *",
                value=vaga_existente["id"] if vaga_existente else "",
                disabled=bool(vaga_existente),
            )
            unidade = st.text_input("Unidade *", value=vaga_existente["unidade"] if vaga_existente else "")
            especialidade = st.text_input(
                "Especialidade *", value=vaga_existente["especialidade"] if vaga_existente else ""
            )
        with c2:
            data_vaga = st.date_input(
                "Data *",
                value=datetime.strptime(vaga_existente["data"], "%Y-%m-%d").date()
                if vaga_existente and vaga_existente["data"] else date.today(),
            )
            periodo = st.selectbox(
                "Período *",
                PERIODOS,
                index=PERIODOS.index(vaga_existente["periodo"]) if vaga_existente and vaga_existente["periodo"] in PERIODOS else 0,
            )
            data_alocacao = st.date_input(
                "Data de alocação (dia que a vaga chegou) *",
                value=datetime.strptime(vaga_existente["data_alocacao"], "%Y-%m-%d").date()
                if vaga_existente and vaga_existente["data_alocacao"] else date.today(),
            )
        with c3:
            especificidade = st.text_area(
                "Especificidade",
                value=vaga_existente["especificidade"] if vaga_existente else "",
                height=100,
            )
            valor_default = 0
            if vaga_existente and vaga_existente["cod"]:
                for i, o in enumerate(opcoes_medico):
                    if o.startswith(vaga_existente["cod"] + " -"):
                        valor_default = i
                        break
            medico_selecionado = st.selectbox("COD do médico (se vaga fechada)", opcoes_medico, index=valor_default)

        salvar = st.form_submit_button("💾 Salvar vaga", use_container_width=True)

        if salvar:
            cod_final = None
            if medico_selecionado != "(vaga aberta / sem médico)":
                cod_final = medico_selecionado.split(" - ")[0]

            erros = []
            if not vaga_id.strip():
                erros.append("Informe o ID da vaga.")
            if not unidade.strip():
                erros.append("Informe a Unidade.")
            if not especialidade.strip():
                erros.append("Informe a Especialidade.")

            if not vaga_existente:
                dup = conn.execute("SELECT 1 FROM vagas WHERE id=?", (vaga_id.strip(),)).fetchone()
                if dup:
                    erros.append(f"Já existe uma vaga cadastrada com o ID {vaga_id}.")

            if erros:
                for e in erros:
                    st.error(e)
            else:
                agora = datetime.now().isoformat(timespec="seconds")
                if vaga_existente:
                    conn.execute(
                        """UPDATE vagas SET unidade=?, especialidade=?, data=?, periodo=?, especificidade=?,
                           data_alocacao=?, cod=?, atualizado_em=? WHERE id=?""",
                        (unidade, especialidade, data_vaga.isoformat(), periodo, especificidade,
                         data_alocacao.isoformat(), cod_final, agora, vaga_id.strip()),
                    )
                    st.success(f"Vaga {vaga_id} atualizada.")
                    st.session_state["editar_id"] = None
                else:
                    conn.execute(
                        """INSERT INTO vagas (id, unidade, especialidade, data, periodo, especificidade,
                           data_alocacao, cod, criado_em, atualizado_em) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (vaga_id.strip(), unidade, especialidade, data_vaga.isoformat(), periodo,
                         especificidade, data_alocacao.isoformat(), cod_final, agora, agora),
                    )
                    st.success(f"Vaga {vaga_id} cadastrada.")
                conn.commit()
                st.rerun()

# ---------------------------------------------------------------
# ABA 2 - VISUALIZAÇÃO / EDIÇÃO / EXCLUSÃO
# ---------------------------------------------------------------
with aba2:
    st.subheader("Vagas cadastradas")

    df = pd.read_sql(
        """SELECT v.id, v.unidade, v.especialidade, v.data, v.periodo, v.especificidade,
                  v.data_alocacao, v.cod, m.nome as medico_nome
           FROM vagas v LEFT JOIN medicos m ON v.cod = m.cod
           ORDER BY v.data""",
        conn,
    )

    if df.empty:
        st.info("Nenhuma vaga cadastrada ainda.")
    else:
        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            filtro_unidade = st.multiselect("Filtrar por Unidade", sorted(df["unidade"].dropna().unique()))
        with colf2:
            filtro_periodo = st.multiselect("Filtrar por Período", sorted(df["periodo"].dropna().unique()))
        with colf3:
            filtro_status = st.selectbox("Filtrar por situação", ["Todas", "Abertas (sem médico)", "Fechadas (com médico)"])

        df_filtrado = df.copy()
        if filtro_unidade:
            df_filtrado = df_filtrado[df_filtrado["unidade"].isin(filtro_unidade)]
        if filtro_periodo:
            df_filtrado = df_filtrado[df_filtrado["periodo"].isin(filtro_periodo)]
        if filtro_status == "Abertas (sem médico)":
            df_filtrado = df_filtrado[df_filtrado["cod"].isna() | (df_filtrado["cod"] == "")]
        elif filtro_status == "Fechadas (com médico)":
            df_filtrado = df_filtrado[df_filtrado["cod"].notna() & (df_filtrado["cod"] != "")]

        st.dataframe(
            df_filtrado[
                ["id", "unidade", "especialidade", "data", "periodo", "especificidade",
                 "data_alocacao", "cod", "medico_nome"]
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("**Editar ou excluir uma vaga:**")
        id_selecionado = st.selectbox("Selecione o ID", [""] + df_filtrado["id"].tolist())
        cbtn1, cbtn2 = st.columns(2)
        with cbtn1:
            if st.button("✏️ Carregar para edição", disabled=not id_selecionado):
                st.session_state["editar_id"] = id_selecionado
                st.rerun()
        with cbtn2:
            if st.button("🗑️ Excluir vaga", disabled=not id_selecionado):
                conn.execute("DELETE FROM vagas WHERE id=?", (id_selecionado,))
                conn.commit()
                st.success(f"Vaga {id_selecionado} excluída.")
                st.rerun()

# ---------------------------------------------------------------
# ABA 3 - MÉDICOS CADASTRADOS
# ---------------------------------------------------------------
with aba3:
    st.subheader("Médicos cadastrados")

    with st.form("form_medico", clear_on_submit=True):
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            novo_cod = st.text_input("COD *")
        with m2:
            novo_nome = st.text_input("Nome *")
        with m3:
            novo_crm = st.text_input("CRM")
        with m4:
            novo_cpf = st.text_input("CPF")
        novo_telefone = st.text_input("Telefone")

        salvar_medico = st.form_submit_button("💾 Salvar médico")

        if salvar_medico:
            if not novo_cod.strip() or not novo_nome.strip():
                st.error("Informe pelo menos o COD e o Nome.")
            else:
                existe = conn.execute("SELECT 1 FROM medicos WHERE cod=?", (novo_cod.strip(),)).fetchone()
                if existe:
                    st.error(f"Já existe um médico com o COD {novo_cod}.")
                else:
                    conn.execute(
                        "INSERT INTO medicos (cod, nome, crm, cpf, telefone) VALUES (?,?,?,?,?)",
                        (novo_cod.strip(), novo_nome.strip(), novo_crm.strip(), novo_cpf.strip(), novo_telefone.strip()),
                    )
                    conn.commit()
                    st.success(f"Médico {novo_nome} (COD {novo_cod}) cadastrado.")
                    st.rerun()

    st.divider()
    df_medicos = pd.read_sql("SELECT * FROM medicos ORDER BY nome", conn)
    if df_medicos.empty:
        st.info("Nenhum médico cadastrado ainda.")
    else:
        st.dataframe(df_medicos, use_container_width=True, hide_index=True)

        cod_excluir = st.selectbox("Excluir médico (selecione o COD)", [""] + df_medicos["cod"].tolist())
        if st.button("🗑️ Excluir médico", disabled=not cod_excluir):
            em_uso = conn.execute("SELECT COUNT(*) FROM vagas WHERE cod=?", (cod_excluir,)).fetchone()[0]
            if em_uso > 0:
                st.error(f"Esse médico está alocado em {em_uso} vaga(s). Remova-o das vagas antes de excluir.")
            else:
                conn.execute("DELETE FROM medicos WHERE cod=?", (cod_excluir,))
                conn.commit()
                st.success("Médico excluído.")
                st.rerun()

# ---------------------------------------------------------------
# ABA 4 - IMPORTAR EXCEL
# ---------------------------------------------------------------
with aba4:
    st.subheader("Importar vagas de um Excel extraído do sistema")
    st.caption(
        "O arquivo deve ter colunas que possam ser mapeadas para: ID, UNIDADE, ESPECIALIDADE, "
        "DATA, PERÍODO, ESPECIFICIDADE. Depois de subir o arquivo, você escolhe qual coluna do "
        "Excel corresponde a cada campo."
    )

    arquivo = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx", "xls"])

    if arquivo is not None:
        try:
            df_import = pd.read_excel(arquivo)
        except Exception as e:
            st.error(f"Não foi possível ler o arquivo: {e}")
            df_import = None

        if df_import is not None:
            st.markdown("**Prévia do arquivo:**")
            st.dataframe(df_import.head(10), use_container_width=True)

            colunas_disponiveis = ["(não usar)"] + list(df_import.columns)

            st.markdown("**Mapeie as colunas do arquivo para os campos do sistema:**")
            c1, c2, c3 = st.columns(3)
            with c1:
                col_id = st.selectbox("Coluna do ID", colunas_disponiveis, index=0)
                col_unidade = st.selectbox("Coluna da Unidade", colunas_disponiveis, index=0)
            with c2:
                col_especialidade = st.selectbox("Coluna da Especialidade", colunas_disponiveis, index=0)
                col_data = st.selectbox("Coluna da Data", colunas_disponiveis, index=0)
            with c3:
                col_periodo = st.selectbox("Coluna do Período", colunas_disponiveis, index=0)
                col_especificidade = st.selectbox("Coluna da Especificidade", colunas_disponiveis, index=0)

            data_alocacao_import = st.date_input("Data de alocação para essas vagas (dia da importação)", value=date.today())

            if st.button("📥 Importar vagas"):
                if col_id == "(não usar)":
                    st.error("É obrigatório mapear a coluna do ID.")
                else:
                    inseridas, atualizadas, ignoradas = 0, 0, 0
                    agora = datetime.now().isoformat(timespec="seconds")

                    for _, linha in df_import.iterrows():
                        vaga_id_val = str(linha[col_id]).strip()
                        if not vaga_id_val or vaga_id_val.lower() == "nan":
                            ignoradas += 1
                            continue

                        def pega(col):
                            if col == "(não usar)":
                                return ""
                            val = linha[col]
                            if pd.isna(val):
                                return ""
                            return str(val).strip()

                        unidade_val = pega(col_unidade)
                        especialidade_val = pega(col_especialidade)
                        periodo_val = pega(col_periodo).upper()
                        especificidade_val = pega(col_especificidade)

                        data_val = ""
                        if col_data != "(não usar)":
                            raw = linha[col_data]
                            try:
                                data_val = pd.to_datetime(raw).date().isoformat()
                            except Exception:
                                data_val = ""

                        existe = conn.execute("SELECT 1 FROM vagas WHERE id=?", (vaga_id_val,)).fetchone()
                        if existe:
                            conn.execute(
                                """UPDATE vagas SET unidade=?, especialidade=?, data=?, periodo=?,
                                   especificidade=?, atualizado_em=? WHERE id=?""",
                                (unidade_val, especialidade_val, data_val, periodo_val,
                                 especificidade_val, agora, vaga_id_val),
                            )
                            atualizadas += 1
                        else:
                            conn.execute(
                                """INSERT INTO vagas (id, unidade, especialidade, data, periodo,
                                   especificidade, data_alocacao, cod, criado_em, atualizado_em)
                                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                                (vaga_id_val, unidade_val, especialidade_val, data_val, periodo_val,
                                 especificidade_val, data_alocacao_import.isoformat(), None, agora, agora),
                            )
                            inseridas += 1

                    conn.commit()
                    st.success(
                        f"Importação concluída: {inseridas} vaga(s) nova(s), "
                        f"{atualizadas} atualizada(s), {ignoradas} ignorada(s) (sem ID)."
                    )
                    st.rerun()

# ---------------------------------------------------------------
# ABA 5 - EXPORTAR
# ---------------------------------------------------------------
with aba5:
    st.subheader("Exportar dados")
    df_export = pd.read_sql(
        """SELECT v.id, v.unidade, v.especialidade, v.data, v.periodo, v.especificidade,
                  v.data_alocacao, v.cod, m.nome as medico_nome, m.crm, m.cpf, m.telefone
           FROM vagas v LEFT JOIN medicos m ON v.cod = m.cod
           ORDER BY v.data""",
        conn,
    )
    if df_export.empty:
        st.info("Nenhum dado para exportar ainda.")
    else:
        st.download_button(
            "⬇️ Baixar vagas como CSV",
            data=df_export.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"vagas_pais_{date.today().isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption("CSV abre direto no Excel/Google Sheets.")
