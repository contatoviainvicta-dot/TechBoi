import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.database import (listar_lotes, listar_animais, listar_pesagens,
                             calcular_gmd, calcular_gmd_lote)

def show():
    st.title("📊 Análises & Cálculo de GMD")
    st.markdown("""
    > **GMD — Ganho de Peso Médio Diário**: Indica quantos kg o animal ganha por dia em média.
    > É o principal indicador de desempenho zootécnico em confinamento/pastagem.
    """)

    lotes = listar_lotes()
    if lotes.empty:
        st.warning("Cadastre lotes e pesagens para visualizar análises.")
        return

    tab1, tab2, tab3 = st.tabs(["🐄 GMD por Animal", "📦 GMD por Lote", "💹 Custo de Produção"])

    with tab1:
        st.subheader("🐄 Análise Individual do Animal")
        lote_sel = st.selectbox("Selecionar Lote", lotes["codigo"] + " — " + lotes["nome"], key="an_lote")
        lote_cod = lote_sel.split(" — ")[0]
        lote_id = lotes[lotes["codigo"] == lote_cod].iloc[0]["id"]
        lote_info = lotes[lotes["codigo"] == lote_cod].iloc[0]

        animais = listar_animais(lote_id)
        if animais.empty:
            st.info("Nenhum animal individual cadastrado. Pesagens do lote inteiro:")
            pesagens_lote = listar_pesagens(lote_id=lote_id)
            if not pesagens_lote.empty:
                pesagens_lote["data_pesagem"] = pd.to_datetime(pesagens_lote["data_pesagem"])
                pesagens_lote = pesagens_lote.sort_values("data_pesagem")
                if len(pesagens_lote) >= 2:
                    primeiro = pesagens_lote.iloc[0]
                    ultimo = pesagens_lote.iloc[-1]
                    dias = (ultimo["data_pesagem"] - primeiro["data_pesagem"]).days
                    if dias > 0:
                        gmd = (ultimo["peso"] - primeiro["peso"]) / dias
                        ganho = ultimo["peso"] - primeiro["peso"]
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Peso Inicial (kg)", f"{primeiro['peso']:.1f}")
                        col2.metric("Peso Atual (kg)", f"{ultimo['peso']:.1f}")
                        col3.metric("Ganho Total (kg)", f"{ganho:.1f}")
                        col4.metric("GMD (kg/dia)", f"{gmd:.3f}", delta=f"em {dias} dias")

                        if lote_info["preco_total"] > 0 and lote_info["quantidade"] > 0:
                            custo_animal = lote_info["preco_total"] / lote_info["quantidade"]
                            custo_kg_ganho = custo_animal / ganho if ganho > 0 else 0
                            st.metric("Custo por kg Ganho", f"R$ {custo_kg_ganho:.2f}")

                        fig = px.line(pesagens_lote, x="data_pesagem", y="peso",
                                     markers=True, title="Evolução de Peso — Lote",
                                     color_discrete_sequence=["#5a8a3c"])
                        st.plotly_chart(fig, use_container_width=True)
            return

        animal_sel = st.selectbox("Selecionar Animal (Brinco)", animais["brinco"].tolist())
        animal = animais[animais["brinco"] == animal_sel].iloc[0]
        animal_id = animal["id"]

        gmd_data = calcular_gmd(animal_id)
        pesagens = listar_pesagens(animal_id=animal_id)

        if gmd_data is None:
            st.info("São necessárias pelo menos 2 pesagens para calcular o GMD.")
        else:
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Peso Inicial (kg)", f"{gmd_data['peso_inicial']:.1f}")
            col2.metric("Peso Final (kg)", f"{gmd_data['peso_final']:.1f}")
            col3.metric("Ganho Total (kg)", f"{gmd_data['ganho_total']:.1f}")
            col4.metric("GMD (kg/dia)", f"{gmd_data['gmd']:.3f}")
            col5.metric("Dias em Análise", gmd_data["dias"])

            # Classificação do GMD
            gmd_val = gmd_data["gmd"]
            if gmd_val >= 1.2:
                st.success(f"🏆 **Desempenho Excelente!** GMD de {gmd_val:.3f} kg/dia — Animal de alto rendimento.")
            elif gmd_val >= 0.8:
                st.info(f"👍 **Bom Desempenho.** GMD de {gmd_val:.3f} kg/dia — Dentro do esperado.")
            elif gmd_val >= 0.5:
                st.warning(f"⚠️ **Desempenho Moderado.** GMD de {gmd_val:.3f} kg/dia — Abaixo do ideal.")
            else:
                st.error(f"🔴 **Desempenho Baixo!** GMD de {gmd_val:.3f} kg/dia — Verificar alimentação e saúde.")

            if not pesagens.empty:
                pesagens["data_pesagem"] = pd.to_datetime(pesagens["data_pesagem"])
                pesagens = pesagens.sort_values("data_pesagem")

                # Linha de tendência
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=pesagens["data_pesagem"], y=pesagens["peso"],
                    mode="lines+markers", name="Peso Real",
                    line=dict(color="#5a8a3c", width=2),
                    marker=dict(size=8)
                ))

                # Projeção 30 dias
                import numpy as np
                ultima_data = pesagens["data_pesagem"].max()
                projecao_datas = pd.date_range(start=ultima_data, periods=31, freq="D")
                projecao_pesos = [pesagens["peso"].iloc[-1] + gmd_val * i for i in range(31)]
                fig.add_trace(go.Scatter(
                    x=projecao_datas, y=projecao_pesos,
                    mode="lines", name="Projeção 30 dias",
                    line=dict(color="#e8784c", width=2, dash="dash")
                ))

                fig.update_layout(
                    title=f"Evolução de Peso — Brinco {animal_sel}",
                    xaxis_title="Data", yaxis_title="Peso (kg)",
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
                )
                st.plotly_chart(fig, use_container_width=True)

                # Tabela de pesagens
                with st.expander("Ver todas as pesagens"):
                    st.dataframe(pesagens[["data_pesagem", "peso", "tipo", "responsavel", "observacoes"]].rename(
                        columns={"data_pesagem": "Data", "peso": "Peso (kg)", "tipo": "Tipo",
                                 "responsavel": "Responsável", "observacoes": "Obs"}
                    ), hide_index=True, use_container_width=True)

    with tab2:
        st.subheader("📦 GMD Médio por Lote")
        lote_sel2 = st.selectbox("Selecionar Lote", lotes["codigo"] + " — " + lotes["nome"], key="gmd_lote")
        lote_cod2 = lote_sel2.split(" — ")[0]
        lote_id2 = lotes[lotes["codigo"] == lote_cod2].iloc[0]["id"]

        df_gmd = calcular_gmd_lote(lote_id2)
        if df_gmd is None or df_gmd.empty:
            st.info("Sem dados suficientes para calcular GMD dos animais deste lote (mín. 2 pesagens por animal).")
        else:
            st.markdown(f"**{len(df_gmd)} animais** com GMD calculado.")
            col1, col2, col3 = st.columns(3)
            col1.metric("GMD Médio do Lote", f"{df_gmd['gmd'].mean():.3f} kg/dia")
            col2.metric("Melhor GMD", f"{df_gmd['gmd'].max():.3f} kg/dia — Brinco: {df_gmd.loc[df_gmd['gmd'].idxmax(),'brinco']}")
            col3.metric("Pior GMD", f"{df_gmd['gmd'].min():.3f} kg/dia — Brinco: {df_gmd.loc[df_gmd['gmd'].idxmin(),'brinco']}")

            fig = px.bar(df_gmd.sort_values("gmd", ascending=False), x="brinco", y="gmd",
                        color="gmd", color_continuous_scale=["#c8401c", "#ffc107", "#5a8a3c"],
                        title="GMD por Animal",
                        labels={"brinco": "Brinco", "gmd": "GMD (kg/dia)"})
            fig.add_hline(y=df_gmd["gmd"].mean(), line_dash="dash", line_color="navy",
                         annotation_text="Média do lote")
            st.plotly_chart(fig, use_container_width=True)

            # Ranking
            df_rank = df_gmd.sort_values("gmd", ascending=False).reset_index(drop=True)
            df_rank.index += 1
            df_rank = df_rank.rename(columns={
                "brinco": "Brinco", "gmd": "GMD (kg/dia)", "peso_inicial": "Peso Inicial",
                "peso_final": "Peso Final", "ganho_total": "Ganho Total (kg)", "dias": "Dias"
            })
            st.dataframe(df_rank[["Brinco", "GMD (kg/dia)", "Peso Inicial", "Peso Final", "Ganho Total (kg)", "Dias"]],
                        use_container_width=True)

    with tab3:
        st.subheader("💹 Análise de Custo de Produção")
        lote_sel3 = st.selectbox("Selecionar Lote", lotes["codigo"] + " — " + lotes["nome"], key="custo_lote")
        lote_cod3 = lote_sel3.split(" — ")[0]
        lote_info3 = lotes[lotes["codigo"] == lote_cod3].iloc[0]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Dados de Entrada**")
            preco_total = lote_info3["preco_total"] or 0
            qtd = lote_info3["quantidade"] or 1
            peso_entrada = lote_info3["peso_entrada_total"] or 0

            custo_extra = st.number_input("Custos extras até hoje (R$)", min_value=0.0, step=100.0,
                                          help="Alimentação, medicamentos, mão de obra, etc.")
            preco_venda_arroba = st.number_input("Preço esperado de venda (@)", min_value=0.0, step=1.0, value=280.0)
            peso_carcaca_pct = st.number_input("Rendimento de carcaça (%)", min_value=40.0, max_value=65.0, value=52.0)

        with col2:
            custo_total = preco_total + custo_extra
            custo_cab = custo_total / qtd if qtd > 0 else 0

            # Pegar peso atual do lote
            pesagens_lote3 = listar_pesagens(lote_id=lote_info3["id"])
            if not pesagens_lote3.empty:
                peso_medio_atual = pesagens_lote3.groupby(pesagens_lote3.columns[1] if "animal_id" in pesagens_lote3.columns else pesagens_lote3.index)["peso"].last().mean()
            else:
                peso_medio_atual = peso_entrada / qtd if qtd > 0 else 0

            arrobas_por_cab = (peso_medio_atual * (peso_carcaca_pct / 100)) / 15
            receita_cab = arrobas_por_cab * preco_venda_arroba
            lucro_cab = receita_cab - custo_cab
            lucro_total = lucro_cab * qtd

            st.markdown("**Resultado Estimado**")
            st.metric("Custo Total do Lote", f"R$ {custo_total:,.2f}")
            st.metric("Custo por Cabeça", f"R$ {custo_cab:,.2f}")
            st.metric("Receita estimada por Cabeça", f"R$ {receita_cab:,.2f}")
            st.metric("Lucro estimado por Cabeça", f"R$ {lucro_cab:,.2f}", delta=f"Total: R$ {lucro_total:,.2f}")

        if preco_total > 0:
            st.markdown("---")
            st.markdown("**Ponto de Equilíbrio**")
            ponto_eq = custo_total / qtd / (arrobas_por_cab) if arrobas_por_cab > 0 else 0
            st.info(f"Para cobrir todos os custos, você precisa vender a **@ por R$ {ponto_eq:.2f}** (preço mínimo).")
