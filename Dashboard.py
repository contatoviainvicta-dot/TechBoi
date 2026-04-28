import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.database import resumo_dashboard, listar_lotes, listar_ocorrencias, listar_pesagens

def show():
    st.title("🏠 Dashboard — Visão Geral da Fazenda")
    st.markdown("---")

    resumo = resumo_dashboard()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("🗂️ Lotes Ativos", resumo["total_lotes"])
    with col2:
        st.metric("🐄 Animais Ativos", resumo["total_animais"])
    with col3:
        st.metric("⚠️ Ocorrências Abertas", resumo["ocorrencias_abertas"])
    with col4:
        st.metric("⚖️ Total Pesagens", resumo["total_pesagens"])
    with col5:
        valor = resumo["valor_total_investido"]
        st.metric("💰 Investimento Total", f"R$ {valor:,.2f}")

    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("📦 Lotes por Raça")
        lotes = listar_lotes()
        if not lotes.empty:
            raca_count = lotes[lotes["status"] == "Ativo"].groupby("raca")["quantidade"].sum().reset_index()
            if not raca_count.empty:
                fig = px.pie(raca_count, values="quantidade", names="raca",
                             color_discrete_sequence=["#5a8a3c", "#8ab05a", "#2d4a22", "#a8c87a", "#d4e8a0"],
                             hole=0.4)
                fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=280)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum lote ativo com raça cadastrada.")
        else:
            st.info("Nenhum lote cadastrado ainda.")

    with col_b:
        st.subheader("💰 Investimento por Lote")
        if not lotes.empty:
            lotes_ativos = lotes[lotes["status"] == "Ativo"].head(8)
            if not lotes_ativos.empty:
                fig = px.bar(lotes_ativos, x="codigo", y="preco_total",
                             labels={"codigo": "Lote", "preco_total": "R$"},
                             color_discrete_sequence=["#5a8a3c"])
                fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=280)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum lote com preço registrado.")
        else:
            st.info("Nenhum lote cadastrado ainda.")

    st.markdown("---")
    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("⚠️ Ocorrências Recentes")
        ocs = listar_ocorrencias()
        if not ocs.empty:
            ocs_recentes = ocs.head(5)[["data_ocorrencia", "tipo", "lote_codigo", "brinco", "status"]]
            ocs_recentes.columns = ["Data", "Tipo", "Lote", "Animal", "Status"]
            st.dataframe(ocs_recentes, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Nenhuma ocorrência registrada.")

    with col_d:
        st.subheader("⚖️ Evolução de Pesagens (Últimas 30)")
        pesagens = listar_pesagens()
        if not pesagens.empty:
            pesagens["data_pesagem"] = pd.to_datetime(pesagens["data_pesagem"])
            pesagens_sorted = pesagens.sort_values("data_pesagem").tail(30)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=pesagens_sorted["data_pesagem"],
                y=pesagens_sorted["peso"],
                mode="markers+lines",
                marker=dict(color="#5a8a3c", size=6),
                line=dict(color="#5a8a3c", width=2)
            ))
            fig.update_layout(
                xaxis_title="Data", yaxis_title="Peso (kg)",
                margin=dict(t=10, b=20, l=20, r=20), height=280
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma pesagem registrada ainda.")

    # Alertas
    st.markdown("---")
    st.subheader("🔔 Alertas")
    alertas = []
    if resumo["ocorrencias_abertas"] > 0:
        alertas.append(f"⚠️ **{resumo['ocorrencias_abertas']} ocorrência(s) em aberto** requerem atenção.")
    if resumo["total_animais"] == 0:
        alertas.append("📋 Nenhum animal cadastrado. Cadastre um lote para começar.")
    if not alertas:
        st.success("✅ Tudo em ordem! Nenhum alerta no momento.")
    else:
        for a in alertas:
            st.warning(a)
