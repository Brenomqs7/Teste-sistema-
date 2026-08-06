import streamlit as st
import sqlite3
import pandas as pd
import io
from datetime import date, datetime

DB_PATH = "vagas.db"
COD_CANCELADA = "1"

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

st.set_page_config(page_title="Controle de Vagas - PAIS", layout="wide", page_icon="🏥")

# ---------------------------------------------------------------
# TEMA VISUAL (verde / preto, aspecto de sistema)
# ---------------------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background-color: #0e1512;
        color: #e6f4ea;
    }
    section[data-testid="stSidebar"] {
        background-color: #0a0f0c;
    }
    h1, h2, h3 {
        color: #2ecc71 !important;
        font-weight: 800 !important;
    }
    p, label, span, div {
        color: #e6f4ea;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #111a15;
        padding: 6px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #16211b;
        border-radius: 8px;
        color: #9fd8b3;
        font-weight: 700;
        padding: 10px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e8449 !important;
        color: #ffffff !important;
    }
    .stButton>button {
        background-color: #1e8449;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        padding: 0.5em 1.2em;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background-color: #2ecc71;
        color: #0e1512;
    }
    .stDownloadButton>button {
        background-color: #145a32;
        color: #ffffff;
        border-radius: 8px;
        font-weight: 700;
    }
    div[data-testid="stMetric"] {
        background-color: #16211b;
        border: 1px solid #1e8449;
        border-radius: 12px;
        padding: 14px;
    }
    div[data-testid="stMetricValue"] {
        color: #2ecc71 !important;
    }
    .stTextInput>div>div>input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #16211b !important;
        color: #e6f4ea !important;
        border-radius: 6px !important;
    }
    hr, .stDivider {
        border-color: #1e8449 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏥 CONTROLE DE VAGAS — SPDM PAIS")
st.caption("Sistema interno · substitui a planilha manual do Drive")

# ---------------------------------------------------------------
# PAINEL RESUMO
# ---------------------------------------------------------------
df_resumo = pd.read_sql("SELECT cod FROM vagas", conn)
total = len(df_resumo)
abertas = int((df_resumo["cod"].isna() | (df_resumo["cod"] == "")).sum())
canceladas = int((df_resumo["cod"] == COD_CANCELADA).sum())
fechadas = total - abertas - canceladas

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total de vagas", total)
k2.metric("🟢 Abertas", abertas)
k3.metric("🔵 Fechadas", fechadas)
k4.metric("🔴 Canceladas", canceladas)

st.divider()

aba1, aba2, aba3, aba4, aba5 = st.tabs(
    ["➕ NOVA VAGA", "📋 VAGAS CADASTRADAS", "🩺 MÉDICOS CADASTRADOS", "📥 IMPORTAR EXCEL", "📤 EXPORTAR"]
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
    opcoes_medico = ["(vaga aberta / sem médico)", "1 - CANCELADA (vaga cancelada)"] + [
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
            medico_selecionado = st.selectbox("COD (médico ou situação da vaga)", opcoes_medico, index=valor_default)

        salvar = st.form_submit_button("💾 SALVAR VAGA", use_container_width=True)

        if salvar:
            if medico_selecionado == "(vaga aberta / sem médico)":
                cod_final = None
            else:
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
# ABA 2 - VISUALIZAÇÃO / EDIÇÃO INLINE DO COD / EXCLUSÃO
# ---------------------------------------------------------------
with aba2:
    st.subheader("Vagas cadastradas")
    st.caption(
        "Edite o campo **COD** direto na tabela: cole o código do médico para fechar a vaga, "
        "deixe em branco para vaga aberta, ou digite **1** para marcar como CANCELADA."
    )

    df_base = pd.read_sql(
        "SELECT id, unidade, especialidade, data, periodo, especificidade, data_alocacao, cod FROM vagas ORDER BY data",
        conn,
    )

    if df_base.empty:
        st.info("Nenhuma vaga cadastrada ainda.")
    else:
        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            filtro_unidade = st.multiselect("Filtrar por Unidade", sorted(df_base["unidade"].dropna().unique()))
        with colf2:
            filtro_periodo = st.multiselect("Filtrar por Período", sorted(df_base["periodo"].dropna().unique()))
        with colf3:
            filtro_status = st.selectbox("Filtrar por situação", ["Todas", "Abertas", "Fechadas", "Canceladas"])

        df_filtrado = df_base.copy()
        if filtro_unidade:
            df_filtrado = df_filtrado[df_filtrado["unidade"].isin(filtro_unidade)]
        if filtro_periodo:
            df_filtrado = df_filtrado[df_filtrado["periodo"].isin(filtro_periodo)]
        if filtro_status == "Abertas":
            df_filtrado = df_filtrado[df_filtrado["cod"].isna() | (df_filtrado["cod"] == "")]
        elif filtro_status == "Fechadas":
            df_filtrado = df_filtrado[df_filtrado["cod"].notna() & (df_filtrado["cod"] != "") & (df_filtrado["cod"] != COD_CANCELADA)]
        elif filtro_status == "Canceladas":
            df_filtrado = df_filtrado[df_filtrado["cod"] == COD_CANCELADA]

        df_filtrado = df_filtrado.reset_index(drop=True)

        edited = st.data_editor(
            df_filtrado,
            column_config={
                "id": st.column_config.TextColumn("ID", disabled=True),
                "unidade": st.column_config.TextColumn("Unidade", disabled=True),
                "especialidade": st.column_config.TextColumn("Especialidade", disabled=True),
                "data": st.column_config.TextColumn("Data", disabled=True),
                "periodo": st.column_config.TextColumn("Período", disabled=True),
                "especificidade": st.column_config.TextColumn("Especificidade", disabled=True),
                "data_alocacao": st.column_config.TextColumn("Data alocação", disabled=True),
                "cod": st.column_config.TextColumn("COD", help="Código do médico, vazio (aberta) ou 1 (cancelada)"),
            },
            hide_index=True,
            use_container_width=True,
            key="editor_vagas",
        )

        if st.button("💾 SALVAR ALTERAÇÕES DE COD", use_container_width=True):
            alteracoes = 0
            avisos = []
            agora = datetime.now().isoformat(timespec="seconds")
            for _, row in edited.iterrows():
                original = df_filtrado.loc[df_filtrado["id"] == row["id"], "cod"].values[0]
                original = original if pd.notna(original) else ""
                novo_cod = (row["cod"] or "").strip() if pd.notna(row["cod"]) else ""

                if novo_cod == original:
                    continue

                if novo_cod and novo_cod != COD_CANCELADA:
                    existe_medico = conn.execute("SELECT 1 FROM medicos WHERE cod=?", (novo_cod,)).fetchone()
                    if not existe_medico:
                        avisos.append(f"COD '{novo_cod}' não encontrado nos médicos cadastrados (vaga {row['id']}) — não aplicado.")
                        continue

                conn.execute(
                    "UPDATE vagas SET cod=?, atualizado_em=? WHERE id=?",
                    (novo_cod if novo_cod else None, agora, row["id"]),
                )
                alteracoes += 1

            conn.commit()
            for a in avisos:
                st.warning(a)
            st.success(f"{alteracoes} vaga(s) atualizada(s).")
            st.rerun()

        st.divider()
        st.markdown("**Visão detalhada (com dados do médico)**")

        df_join = pd.read_sql(
            """SELECT v.id, v.unidade, v.especialidade, v.data, v.periodo, v.especificidade,
                      v.data_alocacao, v.cod, m.nome as medico_nome, m.crm, m.cpf, m.telefone
               FROM vagas v LEFT JOIN medicos m ON v.cod = m.cod
               ORDER BY v.data""",
            conn,
        )
        df_join = df_join[df_join["id"].isin(df_filtrado["id"])]

        def status_da_vaga(cod):
            if pd.isna(cod) or cod == "":
                return "ABERTA"
            if cod == COD_CANCELADA:
                return "CANCELADA"
            return "FECHADA"

        df_join["situação"] = df_join["cod"].apply(status_da_vaga)

        def colorir(row):
            if row["situação"] == "CANCELADA":
                return ["background-color:#5c1a1a; color:#ff6b6b; font-weight:700"] * len(row)
            if row["situação"] == "ABERTA":
                return ["background-color:#123322; color:#8ee6ac"] * len(row)
            return ["background-color:#12241c; color:#e6f4ea"] * len(row)

        st.dataframe(
            df_join.style.apply(colorir, axis=1),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("**Editar todos os campos ou excluir uma vaga:**")
        id_selecionado = st.selectbox("Selecione o ID", [""] + df_filtrado["id"].tolist())
        cbtn1, cbtn2 = st.columns(2)
        with cbtn1:
            if st.button("✏️ CARREGAR PARA EDIÇÃO COMPLETA", disabled=not id_selecionado):
                st.session_state["editar_id"] = id_selecionado
                st.rerun()
        with cbtn2:
            if st.button("🗑️ EXCLUIR VAGA", disabled=not id_selecionado):
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

        salvar_medico = st.form_submit_button("💾 SALVAR MÉDICO")

        if salvar_medico:
            if not novo_cod.strip() or not novo_nome.strip():
                st.error("Informe pelo menos o COD e o Nome.")
            elif novo_cod.strip() == COD_CANCELADA:
                st.error(f"O COD '{COD_CANCELADA}' é reservado para identificar vagas canceladas e não pode ser usado por um médico.")
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
    st.markdown("**📥 Importar médicos em lote via Excel**")
    st.caption("O arquivo deve conter colunas com: Código, Nome, CRM, CPF e Telefone (qualquer ordem/nome de coluna — você mapeia abaixo).")

    arquivo_medicos = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx", "xls"], key="upload_medicos")

    if arquivo_medicos is not None:
        try:
            df_medicos_import = pd.read_excel(arquivo_medicos)
        except Exception as e:
            st.error(f"Não foi possível ler o arquivo: {e}")
            df_medicos_import = None

        if df_medicos_import is not None:
            st.dataframe(df_medicos_import.head(10), use_container_width=True)
            colunas_disp = ["(não usar)"] + list(df_medicos_import.columns)

            mc1, mc2, mc3, mc4, mc5 = st.columns(5)
            with mc1:
                col_cod = st.selectbox("Coluna do Código", colunas_disp, index=0, key="map_cod")
            with mc2:
                col_nome = st.selectbox("Coluna do Nome", colunas_disp, index=0, key="map_nome")
            with mc3:
                col_crm = st.selectbox("Coluna do CRM", colunas_disp, index=0, key="map_crm")
            with mc4:
                col_cpf = st.selectbox("Coluna do CPF", colunas_disp, index=0, key="map_cpf")
            with mc5:
                col_tel = st.selectbox("Coluna do Telefone", colunas_disp, index=0, key="map_tel")

            if st.button("📥 IMPORTAR MÉDICOS", use_container_width=True):
                if col_cod == "(não usar)" or col_nome == "(não usar)":
                    st.error("É obrigatório mapear pelo menos Código e Nome.")
                else:
                    inseridos, atualizados, ignorados = 0, 0, 0

                    def pega(linha, col):
                        if col == "(não usar)":
                            return ""
                        val = linha[col]
                        return "" if pd.isna(val) else str(val).strip()

                    for _, linha in df_medicos_import.iterrows():
                        cod_val = pega(linha, col_cod)
                        if not cod_val or cod_val == COD_CANCELADA:
                            ignorados += 1
                            continue
                        nome_val = pega(linha, col_nome)
                        crm_val = pega(linha, col_crm)
                        cpf_val = pega(linha, col_cpf)
                        tel_val = pega(linha, col_tel)

                        existe = conn.execute("SELECT 1 FROM medicos WHERE cod=?", (cod_val,)).fetchone()
                        if existe:
                            conn.execute(
                                "UPDATE medicos SET nome=?, crm=?, cpf=?, telefone=? WHERE cod=?",
                                (nome_val, crm_val, cpf_val, tel_val, cod_val),
                            )
                            atualizados += 1
                        else:
                            conn.execute(
                                "INSERT INTO medicos (cod, nome, crm, cpf, telefone) VALUES (?,?,?,?,?)",
                                (cod_val, nome_val, crm_val, cpf_val, tel_val),
                            )
                            inseridos += 1

                    conn.commit()
                    st.success(f"Importação concluída: {inseridos} novo(s), {atualizados} atualizado(s), {ignorados} ignorado(s).")
                    st.rerun()

    st.divider()
    df_medicos = pd.read_sql("SELECT * FROM medicos ORDER BY nome", conn)
    if df_medicos.empty:
        st.info("Nenhum médico cadastrado ainda.")
    else:
        st.dataframe(df_medicos, use_container_width=True, hide_index=True)

        cod_excluir = st.selectbox("Excluir médico (selecione o COD)", [""] + df_medicos["cod"].tolist())
        if st.button("🗑️ EXCLUIR MÉDICO", disabled=not cod_excluir):
            em_uso = conn.execute("SELECT COUNT(*) FROM vagas WHERE cod=?", (cod_excluir,)).fetchone()[0]
            if em_uso > 0:
                st.error(f"Esse médico está alocado em {em_uso} vaga(s). Remova-o das vagas antes de excluir.")
            else:
                conn.execute("DELETE FROM medicos WHERE cod=?", (cod_excluir,))
                conn.commit()
                st.success("Médico excluído.")
                st.rerun()

# ---------------------------------------------------------------
# ABA 4 - IMPORTAR EXCEL DE VAGAS
# ---------------------------------------------------------------
with aba4:
    st.subheader("Importar vagas de um Excel extraído do sistema")
    st.caption(
        "O arquivo deve ter colunas que possam ser mapeadas para: ID, UNIDADE, ESPECIALIDADE, "
        "DATA, PERÍODO, ESPECIFICIDADE. Depois de subir o arquivo, você escolhe qual coluna do "
        "Excel corresponde a cada campo."
    )

    arquivo = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx", "xls"], key="upload_vagas")

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

            if st.button("📥 IMPORTAR VAGAS", use_container_width=True):
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
# ABA 5 - EXPORTAR (Excel real, colunas separadas)
# ---------------------------------------------------------------
with aba5:
    st.subheader("Exportar dados")

    df_export = pd.read_sql(
        """SELECT v.id, v.unidade, v.especialidade, v.data, v.periodo, v.especificidade,
                  v.data_alocacao, v.cod, m.nome as medico_nome, m.cpf, m.crm, m.telefone
           FROM vagas v LEFT JOIN medicos m ON v.cod = m.cod
           ORDER BY v.data""",
        conn,
    )

    if df_export.empty:
        st.info("Nenhum dado para exportar ainda.")
    else:
        df_export = df_export.rename(columns={
            "id": "ID",
            "unidade": "UNIDADE",
            "especialidade": "ESPECIALIDADE",
            "data": "DATA",
            "periodo": "PERÍODO",
            "especificidade": "ESPECIFICIDADE",
            "data_alocacao": "DATA ALOCAÇÃO",
            "cod": "CÓDIGO",
            "medico_nome": "MÉDICO NOME",
            "cpf": "CPF",
            "crm": "CRM",
            "telefone": "TEL",
        })

        st.dataframe(df_export, use_container_width=True, hide_index=True)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_export.to_excel(writer, index=False, sheet_name="Vagas")
            worksheet = writer.sheets["Vagas"]
            for i, col in enumerate(df_export.columns, start=1):
                largura = max(12, min(40, df_export[col].astype(str).map(len).max() + 2))
                worksheet.column_dimensions[worksheet.cell(row=1, column=i).column_letter].width = largura
        buffer.seek(0)

        st.download_button(
            "⬇️ BAIXAR VAGAS EM EXCEL (.xlsx)",
            data=buffer,
            file_name=f"vagas_pais_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
