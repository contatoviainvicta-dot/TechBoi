import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.database import listar_lotes, calcular_gmd_lote, listar_pesagens, listar_ocorrencias

def show():
    st.title("🔍 Comparativos entre Lotes")
    st.markdown("Compare o desempenho, custos e saúde entre diferentes lotes.")

    lotes = listar_lotes()
    if len(lotes) < 1:
        st.warning("Cadastre pelo menos 1 lote para ver comparativos.")
        return

    tab1, tab2, tab3 = st.tabs(["💰 Comparativo de Preços", "🏆 Desempenho (GMD)", "🏥 Saúde dos Lotes"])

    with tab1:
        st.subheader("💰 Comparativo de Investimento por Lote")
        lotes_ativos = lotes[lotes["status"] == "Ativo"] if "Ativo" in lotes["status"].values else lotes

        if lotes_ativos.empty:
            st.info("Nenhum lote ativo encontrado.")
            return

        # Gráfico: preço total por lote
        fig1 = px.bar(lotes_ativos, x="codigo", y="preco_total",
                     color="raca",
                     title="Investimento Total por Lote (R$)",
                     labels={"codigo": "Lote", "preco_total": "Valor Total (R$)", "raca": "Raça"},
                     color_discrete_sequence=px.colors.qualitative.Set2,
                     text_auto=True)
        fig1.update_layout(height=400)
        st.plotly_chart(fig1, use_container_width=True)

        col_a, col_b = st.columns(2)

        with col_a:
            # Preço por arroba
            fig2 = px.bar(lotes_ativos[lotes_ativos["preco_arroba"] > 0], x="codigo", y="preco_arroba",
                         title="Preço de Compra por @ (R$)",
                         labels={"codigo": "Lote", "preco_arroba": "R$/@"},
                         color_discrete_sequence=["#5a8a3c"], text_auto=True)
            fig2.update_layout(height=320)
            st.plotly_chart(fig2, use_container_width=True)

        with col_b:
            # Custo por cabeça
            lotes_ativos = lotes_ativos.copy()
            lotes_ativos["custo_cab"] = lotes_ativos.apply(
                lambda r: r["preco_total"] / r["quantidade"] if r["quantidade"] > 0 else 0, axis=1
            )
            fig3 = px.bar(lotes_ativos[lotes_ativos["custo_cab"] > 0], x="codigo", y="custo_cab",
                         title="Custo por Cabeça (R$)",
                         labels={"codigo": "Lote", "custo_cab": "R$/cabeça"},
                         color_discrete_sequence=["#2d4a22"], text_auto=True)
            fig3.update_layout(height=320)
            st.plotly_chart(fig3, use_container_width=True)

        # Tabela comparativa
        st.subheader("📋 Tabela Comparativa de Preços")
        tabela = lotes_ativos[["codigo", "nome", "raca", "categoria", "quantidade",
                                "peso_entrada_total", "preco_total", "preco_arroba", "custo_cab"]].copy()
        tabela["peso_medio_entrada"] = tabela.apply(
            lambda r: r["peso_entrada_total"] / r["quantidade"] if r["quantidade"] > 0 else 0, axis=1
        )
        tabela.columns = ["Código", "Nome", "Raça", "Categoria", "Qtd",
                          "Peso Total (kg)", "Preço Total (R$)", "R$/@", "R$/cab", "Peso Médio (kg)"]
        st.dataframe(tabela, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("🏆 Comparativo de GMD entre Lotes")

        lotes_sel = st.multiselect(
            "Selecionar Lotes para Comparar",
            (lotes["codigo"] + " — " + lotes["nome"]).tolist(),
            default=(lotes["codigo"] + " — " + lotes["nome"]).head(3).tolist()
        )

        if not lotes_sel:
            st.info("Selecione pelo menos um lote.")
            return

        resultados = []
        for lote_str in lotes_sel:
            lote_cod = lote_str.split(" — ")[0]
            lote_id = lotes[lotes["codigo"] == lote_cod].iloc[0]["id"]
            lote_info = lotes[lotes["codigo"] == lote_cod].iloc[0]

            df_gmd = calcular_gmd_lote(lote_id)
            if df_gmd is not None and not df_gmd.empty:
                resultados.append({
                    "lote": lote_cod,
                    "nome": lote_info["nome"],
                    "raca": lote_info["raca"],
                    "gmd_medio": df_gmd["gmd"].mean(),
                    "gmd_max": df_gmd["gmd"].max(),
                    "gmd_min": df_gmd["gmd"].min(),
                    "n_animais": len(df_gmd),
                    "ganho_medio": df_gmd["ganho_total"].mean()
                })

        if not resultados:
            st.info("Nenhum dado de GMD calculado para os lotes selecionados. Adicione pesagens.")
            return

        df_comp = pd.DataFrame(resultados)

        # Ranking
        df_rank = df_comp.sort_values("gmd_medio", ascending=False).reset_index(drop=True)
        df_rank.index += 1

        col1, col2, col3 = st.columns(3)
        melhor = df_rank.iloc[0]
        col1.metric("🥇 Melhor Lote", melhor["lote"], f"GMD: {melhor['gmd_medio']:.3f} kg/dia")
        col2.metric("📊 Média Geral (GMD)", f"{df_comp['gmd_medio'].mean():.3f} kg/dia")
        col3.metric("Maior Ganho Médio", f"{df_comp['ganho_medio'].max():.1f} kg", f"Lote: {df_comp.loc[df_comp['ganho_medio'].idxmax(), 'lote']}")

        fig = go.Figure()
        for _, row in df_comp.iterrows():
            fig.add_trace(go.Bar(
                name=row["lote"],
                x=[row["lote"]],
                y=[row["gmd_medio"]],
                error_y=dict(
                    type="data",
                    symmetric=False,
                    array=[row["gmd_max"] - row["gmd_medio"]],
                    arrayminus=[row["gmd_medio"] - row["gmd_min"]]
                )
            ))
        fig.update_layout(
            title="GMD Médio por Lote (com variação min/max)",
            yaxis_title="GMD (kg/dia)",
            xaxis_title="Lote",
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df_rank.rename(columns={
            "lote": "Lote", "nome": "Nome", "raca": "Raça",
            "gmd_medio": "GMD Médio", "gmd_max": "GMD Máx", "gmd_min": "GMD Mín",
            "n_animais": "Animais", "ganho_medio": "Ganho Médio (kg)"
        }), use_container_width=True)

    with tab3:
        st.subheader("🏥 Comparativo de Saúde entre Lotes")
        ocs = listar_ocorrencias()
        if ocs.empty:
            st.success("✅ Nenhuma ocorrência registrada em nenhum lote.")
            return

        resumo_saude = ocs.groupby("lote_codigo").agg(
            total_ocorrencias=("id", "count"),
            abertas=("status", lambda x: (x == "Aberta").sum()),
            custo_total=("custo", "sum")
        ).reset_index()

        # Adiciona info dos lotes
        lotes_info = lotes[["codigo", "quantidade", "nome"]].rename(columns={"codigo": "lote_codigo"})
        resumo_saude = resumo_saude.merge(lotes_info, on="lote_codigo", how="left")
        resumo_saude["ocorrencias_por_cab"] = resumo_saude.apply(
            lambda r: r["total_ocorrencias"] / r["quantidade"] if r["quantidade"] > 0 else 0, axis=1
        )

        col_a, col_b = st.columns(2)
        with col_a:
            fig_oc = px.bar(resumo_saude, x="lote_codigo", y="total_ocorrencias",
                           color="abertas",
                           title="Ocorrências por Lote",
                           labels={"lote_codigo": "Lote", "total_ocorrencias": "Total",
                                   "abertas": "Em aberto"},
                           color_continuous_scale=["#5a8a3c", "#ffc107", "#dc3545"])
            fig_oc.update_layout(height=350)
            st.plotly_chart(fig_oc, use_container_width=True)

        with col_b:
            fig_custo = px.bar(resumo_saude[resumo_saude["custo_total"] > 0],
                              x="lote_codigo", y="custo_total",
                              title="Custo com Saúde por Lote (R$)",
                              labels={"lote_codigo": "Lote", "custo_total": "R$"},
                              color_discrete_sequence=["#c8401c"], text_auto=True)
            fig_custo.update_layout(height=350)
            st.plotly_chart(fig_custo, use_container_width=True)

        st.subheader("Ocorrências por Tipo em cada Lote")
        tipo_lote = ocs.groupby(["lote_codigo", "tipo"]).size().reset_index(name="count")
        fig_heat = px.density_heatmap(tipo_lote, x="lote_codigo", y="tipo", z="count",
                                      color_continuous_scale="YlOrRd",
                                      title="Mapa de Calor: Ocorrências por Tipo e Lote",
                                      labels={"lote_codigo": "Lote", "tipo": "Tipo", "count": "Qtd"})
        st.plotly_chart(fig_heat, use_container_width=True)
