import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, time

DB_PATH = "vagas.db"

# ---------------------------------------------------------------
# BANCO DE DADOS
# ---------------------------------------------------------------

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vagas (
            id TEXT PRIMARY KEY,
            contrato TEXT,
            unidade TEXT,
            especialidade TEXT,
            data_inicio TEXT,
            hora_inicio TEXT,
            data_termino TEXT,
            hora_termino TEXT,
            periodo TEXT,
            especificidade TEXT,
            nome_medico TEXT,
            crm TEXT,
            cpf TEXT,
            telefone TEXT,
            status TEXT,
            criado_em TEXT,
            atualizado_em TEXT
        )
    """)
    conn.commit()
    return conn


conn = get_conn()

PERIODOS = ["DIURNO", "NOTURNO", "MANHÃ", "TARDE"]
STATUS_OPCOES = [
    "VAGA ABERTA",
    "ENCAMINHADO PELO CORPORATIVO PARA A EMPRESA",
    "MÉDICO ALOCADO",
    "CONFIRMADO",
    "CANCELADO",
]

st.set_page_config(page_title="Controle de Vagas - PAIS", layout="wide")
st.title("🏥 Controle de Vagas e Médicos - SPDM PAIS")
st.caption("Substitui a planilha manual do Drive — com validações para evitar erros de data/período.")

aba1, aba2, aba3 = st.tabs(["➕ Nova vaga / alocação", "📋 Vagas cadastradas", "📤 Exportar"])

# ---------------------------------------------------------------
# ABA 1 - CADASTRO
# ---------------------------------------------------------------
with aba1:
    st.subheader("Cadastrar vaga (conforme sistema da contratante) e alocar médico")

    editar_id = st.session_state.get("editar_id")
    vaga_existente = None
    if editar_id:
        row = conn.execute("SELECT * FROM vagas WHERE id=?", (editar_id,)).fetchone()
        if row:
            cols = [c[0] for c in conn.execute("PRAGMA table_info(vagas)").fetchall()]
            vaga_existente = dict(zip(cols, row))
            st.info(f"Editando vaga ID {editar_id}")

    with st.form("form_vaga", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            vaga_id = st.text_input(
                "ID da vaga (igual ao sistema da contratante) *",
                value=vaga_existente["id"] if vaga_existente else "",
                disabled=bool(vaga_existente),
            )
            contrato = st.text_input("Contrato", value=vaga_existente["contrato"] if vaga_existente else "")
            unidade = st.text_input("Unidade *", value=vaga_existente["unidade"] if vaga_existente else "")
            especialidade = st.text_input(
                "Especialidade *", value=vaga_existente["especialidade"] if vaga_existente else ""
            )
        with c2:
            data_inicio = st.date_input(
                "Data início *",
                value=datetime.strptime(vaga_existente["data_inicio"], "%Y-%m-%d").date()
                if vaga_existente and vaga_existente["data_inicio"] else date.today(),
            )
            hora_inicio = st.time_input(
                "Hora início",
                value=datetime.strptime(vaga_existente["hora_inicio"], "%H:%M").time()
                if vaga_existente and vaga_existente["hora_inicio"] else time(7, 0),
            )
            data_termino = st.date_input(
                "Data término *",
                value=datetime.strptime(vaga_existente["data_termino"], "%Y-%m-%d").date()
                if vaga_existente and vaga_existente["data_termino"] else date.today(),
            )
            hora_termino = st.time_input(
                "Hora término",
                value=datetime.strptime(vaga_existente["hora_termino"], "%H:%M").time()
                if vaga_existente and vaga_existente["hora_termino"] else time(19, 0),
            )
            periodo = st.selectbox(
                "Período *",
                PERIODOS,
                index=PERIODOS.index(vaga_existente["periodo"]) if vaga_existente and vaga_existente["periodo"] in PERIODOS else 0,
            )
        with c3:
            especificidade = st.text_area(
                "Especificidade / observação",
                value=vaga_existente["especificidade"] if vaga_existente else "",
                height=68,
            )
            status = st.selectbox(
                "Status *",
                STATUS_OPCOES,
                index=STATUS_OPCOES.index(vaga_existente["status"]) if vaga_existente and vaga_existente["status"] in STATUS_OPCOES else 0,
            )

        st.markdown("**Dados do médico alocado** (deixe em branco se a vaga ainda estiver aberta)")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            nome_medico = st.text_input("Nome", value=vaga_existente["nome_medico"] if vaga_existente else "")
        with m2:
            crm = st.text_input("CRM", value=vaga_existente["crm"] if vaga_existente else "")
        with m3:
            cpf = st.text_input("CPF", value=vaga_existente["cpf"] if vaga_existente else "")
        with m4:
            telefone = st.text_input("Telefone", value=vaga_existente["telefone"] if vaga_existente else "")

        salvar = st.form_submit_button("💾 Salvar vaga", use_container_width=True)

        if salvar:
            erros = []
            if not vaga_id.strip():
                erros.append("Informe o ID da vaga.")
            if not unidade.strip():
                erros.append("Informe a Unidade.")
            if not especialidade.strip():
                erros.append("Informe a Especialidade.")
            if data_termino < data_inicio:
                erros.append("Data término não pode ser anterior à data início.")

            # checagem de duplicidade (só ao criar, não ao editar)
            if not vaga_existente:
                dup = conn.execute("SELECT 1 FROM vagas WHERE id=?", (vaga_id.strip(),)).fetchone()
                if dup:
                    erros.append(f"Já existe uma vaga cadastrada com o ID {vaga_id}.")

            # checagem de conflito de horário para o mesmo médico
            if nome_medico.strip():
                inicio_novo = datetime.combine(data_inicio, hora_inicio)
                fim_novo = datetime.combine(data_termino, hora_termino)
                existentes = conn.execute(
                    "SELECT id, data_inicio, hora_inicio, data_termino, hora_termino FROM vagas WHERE nome_medico=? AND id != ?",
                    (nome_medico.strip(), vaga_id.strip() if vaga_existente else "___novo___"),
                ).fetchall()
                for outro_id, di, hi, dt_, ht in existentes:
                    try:
                        inicio_outro = datetime.strptime(f"{di} {hi}", "%Y-%m-%d %H:%M")
                        fim_outro = datetime.strptime(f"{dt_} {ht}", "%Y-%m-%d %H:%M")
                        if inicio_novo < fim_outro and inicio_outro < fim_novo:
                            erros.append(
                                f"Conflito de horário: {nome_medico} já está alocado na vaga {outro_id} "
                                f"({di} {hi} até {dt_} {ht})."
                            )
                    except ValueError:
                        pass

            if erros:
                for e in erros:
                    st.error(e)
            else:
                agora = datetime.now().isoformat(timespec="seconds")
                if vaga_existente:
                    conn.execute(
                        """UPDATE vagas SET contrato=?, unidade=?, especialidade=?, data_inicio=?, hora_inicio=?,
                           data_termino=?, hora_termino=?, periodo=?, especificidade=?, nome_medico=?, crm=?,
                           cpf=?, telefone=?, status=?, atualizado_em=? WHERE id=?""",
                        (contrato, unidade, especialidade, data_inicio.isoformat(), hora_inicio.strftime("%H:%M"),
                         data_termino.isoformat(), hora_termino.strftime("%H:%M"), periodo, especificidade,
                         nome_medico, crm, cpf, telefone, status, agora, vaga_id.strip()),
                    )
                    st.success(f"Vaga {vaga_id} atualizada.")
                    st.session_state["editar_id"] = None
                else:
                    conn.execute(
                        """INSERT INTO vagas (id, contrato, unidade, especialidade, data_inicio, hora_inicio,
                           data_termino, hora_termino, periodo, especificidade, nome_medico, crm, cpf, telefone,
                           status, criado_em, atualizado_em) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (vaga_id.strip(), contrato, unidade, especialidade, data_inicio.isoformat(),
                         hora_inicio.strftime("%H:%M"), data_termino.isoformat(), hora_termino.strftime("%H:%M"),
                         periodo, especificidade, nome_medico, crm, cpf, telefone, status, agora, agora),
                    )
                    st.success(f"Vaga {vaga_id} cadastrada.")
                conn.commit()
                st.rerun()

# ---------------------------------------------------------------
# ABA 2 - VISUALIZAÇÃO / EDIÇÃO / EXCLUSÃO
# ---------------------------------------------------------------
with aba2:
    st.subheader("Vagas cadastradas")

    df = pd.read_sql("SELECT * FROM vagas ORDER BY data_inicio", conn)

    if df.empty:
        st.info("Nenhuma vaga cadastrada ainda.")
    else:
        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            filtro_unidade = st.multiselect("Filtrar por Unidade", sorted(df["unidade"].dropna().unique()))
        with colf2:
            filtro_status = st.multiselect("Filtrar por Status", sorted(df["status"].dropna().unique()))
        with colf3:
            filtro_periodo = st.multiselect("Filtrar por Período", sorted(df["periodo"].dropna().unique()))

        df_filtrado = df.copy()
        if filtro_unidade:
            df_filtrado = df_filtrado[df_filtrado["unidade"].isin(filtro_unidade)]
        if filtro_status:
            df_filtrado = df_filtrado[df_filtrado["status"].isin(filtro_status)]
        if filtro_periodo:
            df_filtrado = df_filtrado[df_filtrado["periodo"].isin(filtro_periodo)]

        st.dataframe(
            df_filtrado[
                ["id", "unidade", "especialidade", "data_inicio", "hora_inicio", "data_termino",
                 "hora_termino", "periodo", "nome_medico", "crm", "status"]
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
# ABA 3 - EXPORTAR
# ---------------------------------------------------------------
with aba3:
    st.subheader("Exportar dados")
    df_export = pd.read_sql("SELECT * FROM vagas ORDER BY data_inicio", conn)
    if df_export.empty:
        st.info("Nenhum dado para exportar ainda.")
    else:
        st.download_button(
            "⬇️ Baixar como Excel",
            data=df_export.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"vagas_pais_{date.today().isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption("Exportado como CSV (abre direto no Excel/Google Sheets). Para .xlsx nativo, use openpyxl.")
