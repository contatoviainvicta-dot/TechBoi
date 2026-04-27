import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from utils.database import inserir_pesagem, listar_pesagens, listar_lotes, listar_animais

def show():
    st.title("⚖️ Controle de Pesagens")
    tab1, tab2, tab3 = st.tabs(["📋 Histórico", "➕ Registrar Pesagem", "📈 Evolução por Animal"])

    with tab1:
        st.subheader("📋 Histórico de Pesagens")
        lotes = listar_lotes()

        col1, col2 = st.columns(2)
        with col1:
            filtro_lote = st.selectbox("Filtrar por Lote", ["Todos"] + (lotes["codigo"] + " — " + lotes["nome"]).tolist())
        with col2:
            filtro_tipo = st.selectbox("Tipo de Pesagem", ["Todos", "Entrada", "Rotina", "Saída", "Veterinária"])

        if filtro_lote != "Todos":
            lote_cod = filtro_lote.split(" — ")[0]
            lote_id = lotes[lotes["codigo"] == lote_cod].iloc[0]["id"]
            pesagens = listar_pesagens(lote_id=lote_id)
        else:
            pesagens = listar_pesagens()

        if filtro_tipo != "Todos":
            pesagens = pesagens[pesagens["tipo"] == filtro_tipo]

        if not pesagens.empty:
            colunas = ["data_pesagem", "lote_codigo", "brinco", "peso", "tipo", "responsavel", "observacoes"]
            nomes = ["Data", "Lote", "Brinco", "Peso (kg)", "Tipo", "Responsável", "Obs"]
            df_exib = pesagens[[c for c in colunas if c in pesagens.columns]].copy()
            df_exib.columns = nomes[:len(df_exib.columns)]
            st.dataframe(df_exib, use_container_width=True, hide_index=True)

            # Resumo
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Registros", len(pesagens))
            with col2:
                st.metric("Peso Médio (kg)", f"{pesagens['peso'].mean():.1f}")
            with col3:
                st.metric("Peso Máximo (kg)", f"{pesagens['peso'].max():.1f}")
        else:
            st.info("Nenhuma pesagem encontrada com os filtros selecionados.")

    with tab2:
        st.subheader("➕ Registrar Nova Pesagem")
        lotes = listar_lotes()
        if lotes.empty:
            st.warning("Cadastre um lote primeiro.")
            return

        with st.form("form_pesagem", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                lote_sel = st.selectbox("Lote *", lotes["codigo"] + " — " + lotes["nome"])
                lote_cod = lote_sel.split(" — ")[0]
                lote_id = lotes[lotes["codigo"] == lote_cod].iloc[0]["id"]

                animais = listar_animais(lote_id)
                if not animais.empty:
                    opcoes_animal = ["Lote inteiro (sem animal individual)"] + animais["brinco"].tolist()
                else:
                    opcoes_animal = ["Lote inteiro (sem animal individual)"]

                animal_sel = st.selectbox("Animal (Brinco)", opcoes_animal)
                data_pesagem = st.date_input("Data da Pesagem *", value=date.today())
                tipo = st.selectbox("Tipo de Pesagem", ["Rotina", "Entrada", "Saída", "Veterinária"])

            with col2:
                peso = st.number_input("Peso (kg) *", min_value=0.1, step=0.5, value=300.0)
                responsavel = st.text_input("Responsável", placeholder="Ex: João Silva")
                observacoes = st.text_area("Observações", placeholder="Condição corporal, etc.")

            submitted = st.form_submit_button("💾 Registrar Pesagem", use_container_width=True)
            if submitted:
                animal_id = None
                if animal_sel != "Lote inteiro (sem animal individual)":
                    animal_id = animais[animais["brinco"] == animal_sel].iloc[0]["id"]

                dados = {
                    "lote_id": lote_id,
                    "animal_id": animal_id,
                    "data_pesagem": str(data_pesagem),
                    "peso": peso,
                    "tipo": tipo,
                    "responsavel": responsavel,
                    "observacoes": observacoes
                }
                inserir_pesagem(dados)
                st.success(f"✅ Pesagem de {peso} kg registrada com sucesso!")
                st.rerun()

    with tab3:
        st.subheader("📈 Evolução de Peso por Animal")
        lotes = listar_lotes()
        if lotes.empty:
            st.info("Nenhum lote cadastrado.")
            return

        lote_sel = st.selectbox("Selecionar Lote", lotes["codigo"] + " — " + lotes["nome"], key="ev_lote")
        lote_cod = lote_sel.split(" — ")[0]
        lote_id = lotes[lotes["codigo"] == lote_cod].iloc[0]["id"]
        animais = listar_animais(lote_id)

        if animais.empty:
            st.info("Nenhum animal individual cadastrado neste lote.")
            # Mostrar pesagens do lote inteiro
            pesagens_lote = listar_pesagens(lote_id=lote_id)
            if not pesagens_lote.empty:
                pesagens_lote["data_pesagem"] = pd.to_datetime(pesagens_lote["data_pesagem"])
                fig = px.line(pesagens_lote.sort_values("data_pesagem"),
                              x="data_pesagem", y="peso",
                              title="Evolução de Peso — Lote Inteiro",
                              markers=True,
                              color_discrete_sequence=["#5a8a3c"])
                fig.update_layout(xaxis_title="Data", yaxis_title="Peso (kg)")
                st.plotly_chart(fig, use_container_width=True)
            return

        animais_sel = st.multiselect("Selecionar Animais (Brincos)", animais["brinco"].tolist(),
                                      default=animais["brinco"].head(5).tolist())

        if animais_sel:
            all_data = []
            for brinco in animais_sel:
                animal = animais[animais["brinco"] == brinco].iloc[0]
                pesagens = listar_pesagens(animal_id=animal["id"])
                if not pesagens.empty:
                    pesagens["brinco"] = brinco
                    all_data.append(pesagens)

            if all_data:
                df_all = pd.concat(all_data)
                df_all["data_pesagem"] = pd.to_datetime(df_all["data_pesagem"])
                fig = px.line(df_all.sort_values("data_pesagem"),
                              x="data_pesagem", y="peso", color="brinco",
                              markers=True,
                              title="Evolução de Peso por Animal",
                              color_discrete_sequence=px.colors.qualitative.Set2)
                fig.update_layout(xaxis_title="Data", yaxis_title="Peso (kg)",
                                  legend_title="Brinco")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhuma pesagem registrada para os animais selecionados.")
