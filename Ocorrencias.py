import streamlit as st
import pandas as pd
from datetime import date
from utils.database import inserir_ocorrencia, listar_ocorrencias, listar_lotes, listar_animais, resolver_ocorrencia

TIPOS_OCORRENCIA = [
    "Doença Respiratória", "Doença Digestiva", "Lesão/Trauma",
    "Parasitismo (carrapato, berne)", "Brucelose/Vacinação",
    "Morte", "Fuga/Extravio", "Problema Reprodutivo",
    "Deficiência Nutricional", "Outro"
]

def show():
    st.title("🏥 Ocorrências Adversas")
    tab1, tab2, tab3 = st.tabs(["📋 Listar Ocorrências", "➕ Registrar Ocorrência", "📊 Relatório"])

    with tab1:
        st.subheader("📋 Ocorrências Registradas")
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_status = st.selectbox("Status", ["Todos", "Aberta", "Resolvida"])
        with col2:
            filtro_tipo = st.selectbox("Tipo", ["Todos"] + TIPOS_OCORRENCIA)
        with col3:
            lotes = listar_lotes()
            if not lotes.empty:
                opcoes_lote = ["Todos"] + (lotes["codigo"] + " — " + lotes["nome"]).tolist()
            else:
                opcoes_lote = ["Todos"]
            filtro_lote = st.selectbox("Lote", opcoes_lote)

        ocs = listar_ocorrencias()

        if filtro_status != "Todos":
            ocs = ocs[ocs["status"] == filtro_status]
        if filtro_tipo != "Todos":
            ocs = ocs[ocs["tipo"] == filtro_tipo]
        if filtro_lote != "Todos" and not lotes.empty:
            lote_cod = filtro_lote.split(" — ")[0]
            lote_id = lotes[lotes["codigo"] == lote_cod].iloc[0]["id"]
            ocs = ocs[ocs["lote_id"] == lote_id]

        if not ocs.empty:
            for _, oc in ocs.iterrows():
                status_icon = "🔴" if oc["status"] == "Aberta" else "✅"
                with st.expander(f"{status_icon} [{oc['data_ocorrencia']}] {oc['tipo']} — Lote: {oc.get('lote_codigo','N/A')} | Animal: {oc.get('brinco','Lote inteiro')}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"**Tipo:** {oc['tipo']}")
                        st.markdown(f"**Data:** {oc['data_ocorrencia']}")
                        st.markdown(f"**Status:** {oc['status']}")
                    with col2:
                        st.markdown(f"**Responsável:** {oc.get('responsavel','—')}")
                        st.markdown(f"**Custo:** R$ {oc.get('custo', 0):.2f}")
                        if oc.get("data_resolucao"):
                            st.markdown(f"**Resolvida em:** {oc['data_resolucao']}")
                    with col3:
                        st.markdown(f"**Descrição:** {oc.get('descricao','—')}")
                        st.markdown(f"**Tratamento:** {oc.get('tratamento','—')}")

                    if oc["status"] == "Aberta":
                        col_btn1, col_btn2 = st.columns([1, 3])
                        with col_btn1:
                            data_res = st.date_input("Data resolução", value=date.today(), key=f"res_date_{oc['id']}")
                            if st.button("✅ Marcar Resolvida", key=f"resolver_{oc['id']}"):
                                resolver_ocorrencia(oc["id"], str(data_res))
                                st.success("Ocorrência marcada como resolvida!")
                                st.rerun()
        else:
            st.success("✅ Nenhuma ocorrência com os filtros selecionados.")

    with tab2:
        st.subheader("➕ Registrar Nova Ocorrência")
        lotes = listar_lotes()
        if lotes.empty:
            st.warning("Cadastre um lote primeiro.")
            return

        with st.form("form_ocorrencia", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                lote_sel = st.selectbox("Lote *", lotes["codigo"] + " — " + lotes["nome"])
                lote_cod = lote_sel.split(" — ")[0]
                lote_id = lotes[lotes["codigo"] == lote_cod].iloc[0]["id"]

                animais = listar_animais(lote_id)
                opcoes_animal = ["Lote inteiro"] + (animais["brinco"].tolist() if not animais.empty else [])
                animal_sel = st.selectbox("Animal Afetado", opcoes_animal)

                tipo = st.selectbox("Tipo de Ocorrência *", TIPOS_OCORRENCIA)
                data_oc = st.date_input("Data da Ocorrência *", value=date.today())

            with col2:
                responsavel = st.text_input("Responsável", placeholder="Ex: Dr. Carlos (Veterinário)")
                custo = st.number_input("Custo (R$)", min_value=0.0, step=10.0)
                status_oc = st.selectbox("Status", ["Aberta", "Resolvida"])
                data_resolucao = None
                if status_oc == "Resolvida":
                    data_resolucao = st.date_input("Data de Resolução", value=date.today())

            descricao = st.text_area("Descrição da Ocorrência *", placeholder="Descreva detalhadamente o que foi observado...")
            tratamento = st.text_area("Tratamento Aplicado", placeholder="Medicamentos, dosagens, procedimentos realizados...")

            submitted = st.form_submit_button("💾 Registrar Ocorrência", use_container_width=True)
            if submitted:
                if not descricao:
                    st.error("Descrição é obrigatória.")
                else:
                    animal_id = None
                    if animal_sel != "Lote inteiro" and not animais.empty:
                        animal_id = animais[animais["brinco"] == animal_sel].iloc[0]["id"]

                    dados = {
                        "lote_id": lote_id,
                        "animal_id": animal_id,
                        "tipo": tipo,
                        "descricao": descricao,
                        "data_ocorrencia": str(data_oc),
                        "responsavel": responsavel,
                        "custo": custo,
                        "tratamento": tratamento,
                        "status": status_oc
                    }
                    inserir_ocorrencia(dados)
                    if status_oc == "Resolvida" and data_resolucao:
                        # update resolução after insert
                        from utils.database import get_connection
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("UPDATE ocorrencias SET data_resolucao=? WHERE id=(SELECT MAX(id) FROM ocorrencias)", (str(data_resolucao),))
                        conn.commit()
                        conn.close()
                    st.success("✅ Ocorrência registrada com sucesso!")
                    st.rerun()

    with tab3:
        st.subheader("📊 Relatório de Ocorrências")
        ocs = listar_ocorrencias()
        if ocs.empty:
            st.info("Nenhuma ocorrência registrada.")
            return

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", len(ocs))
        with col2:
            st.metric("Abertas", len(ocs[ocs["status"] == "Aberta"]))
        with col3:
            st.metric("Resolvidas", len(ocs[ocs["status"] == "Resolvida"]))
        with col4:
            st.metric("Custo Total", f"R$ {ocs['custo'].sum():,.2f}")

        import plotly.express as px
        col_a, col_b = st.columns(2)
        with col_a:
            tipo_count = ocs.groupby("tipo").size().reset_index(name="count")
            fig = px.bar(tipo_count, x="count", y="tipo", orientation="h",
                         title="Ocorrências por Tipo",
                         color_discrete_sequence=["#5a8a3c"])
            fig.update_layout(yaxis_title="", xaxis_title="Qtd", height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            custo_tipo = ocs.groupby("tipo")["custo"].sum().reset_index()
            custo_tipo = custo_tipo[custo_tipo["custo"] > 0]
            if not custo_tipo.empty:
                fig2 = px.pie(custo_tipo, values="custo", names="tipo",
                              title="Custo por Tipo de Ocorrência",
                              color_discrete_sequence=["#5a8a3c","#8ab05a","#2d4a22","#a8c87a","#d4e8a0","#c8401c","#e8784c"])
                fig2.update_layout(height=350)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Sem custos registrados por tipo.")
