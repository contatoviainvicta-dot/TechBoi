import streamlit as st
import pandas as pd
from datetime import date
from core.database import inserir_lote, listar_lotes, atualizar_lote, inserir_animal, listar_animais

RACAS = ["Nelore", "Angus", "Brahman", "Simmental", "Hereford", "Brangus", "Gir", "Guzerá", "Tabapuã", "Cruzado", "Outra"]
CATEGORIAS = ["Bezerro", "Garrote", "Novilho", "Boi", "Vaca", "Novilha", "Touro"]
SEXOS = ["Macho", "Fêmea", "Misto"]

def show():
    st.title("📦 Gestão de Lotes")
    tab1, tab2, tab3 = st.tabs(["📋 Listar Lotes", "➕ Cadastrar Lote", "🐄 Animais do Lote"])

    with tab1:
        lotes = listar_lotes()
        if lotes.empty:
            st.info("Nenhum lote cadastrado. Vá para 'Cadastrar Lote' para começar.")
        else:
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                filtro_status = st.selectbox("Filtrar por status", ["Todos", "Ativo", "Encerrado", "Vendido"])
            with col2:
                filtro_raca = st.selectbox("Filtrar por raça", ["Todas"] + RACAS)

            df_filtrado = lotes.copy()
            if filtro_status != "Todos":
                df_filtrado = df_filtrado[df_filtrado["status"] == filtro_status]
            if filtro_raca != "Todas":
                df_filtrado = df_filtrado[df_filtrado["raca"] == filtro_raca]

            colunas = ["codigo", "nome", "data_entrada", "raca", "categoria", "quantidade",
                       "peso_entrada_total", "preco_total", "preco_arroba", "fornecedor", "status"]
            nomes = ["Código", "Nome", "Data Entrada", "Raça", "Categoria", "Qtd",
                     "Peso Total (kg)", "Preço Total (R$)", "R$/arroba", "Fornecedor", "Status"]

            df_exibir = df_filtrado[colunas].copy()
            df_exibir.columns = nomes
            st.dataframe(df_exibir, use_container_width=True, hide_index=True)

            # Editar status
            st.markdown("---")
            st.subheader("✏️ Atualizar Status do Lote")
            lote_opcoes = df_filtrado["codigo"].tolist()
            if lote_opcoes:
                lote_sel = st.selectbox("Selecionar lote", lote_opcoes, key="edit_lote")
                lote_data = lotes[lotes["codigo"] == lote_sel].iloc[0]
                novo_status = st.selectbox("Novo status", ["Ativo", "Encerrado", "Vendido"], index=["Ativo","Encerrado","Vendido"].index(lote_data["status"]) if lote_data["status"] in ["Ativo","Encerrado","Vendido"] else 0)
                if st.button("💾 Atualizar Status"):
                    dados = dict(lote_data)
                    dados["status"] = novo_status
                    atualizar_lote(lote_data["id"], dados)
                    st.success(f"Status do lote {lote_sel} atualizado para {novo_status}!")
                    st.rerun()

    with tab2:
        st.subheader("➕ Cadastrar Novo Lote")
        with st.form("form_lote", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                codigo = st.text_input("Código do Lote *", placeholder="Ex: L2024-001")
                nome = st.text_input("Nome do Lote *", placeholder="Ex: Nelore Engorda Jan/24")
                data_entrada = st.date_input("Data de Entrada *", value=date.today())
                fornecedor = st.text_input("Fornecedor", placeholder="Ex: Fazenda Boa Vista")
            with col2:
                raca = st.selectbox("Raça Principal", RACAS)
                sexo = st.selectbox("Sexo", SEXOS)
                categoria = st.selectbox("Categoria", CATEGORIAS)
                origem = st.text_input("Cidade/Estado de Origem", placeholder="Ex: Uberaba/MG")
            with col3:
                quantidade = st.number_input("Quantidade de Animais *", min_value=1, value=1)
                peso_entrada_total = st.number_input("Peso Total de Entrada (kg)", min_value=0.0, step=0.5)
                preco_total = st.number_input("Preço Total Pago (R$)", min_value=0.0, step=100.0)
                preco_arroba = st.number_input("Preço por @ (R$)", min_value=0.0, step=1.0)

            observacoes = st.text_area("Observações", placeholder="Condições sanitárias, tratamentos prévios, etc.")

            submitted = st.form_submit_button("💾 Cadastrar Lote", use_container_width=True)
            if submitted:
                if not codigo or not nome:
                    st.error("Código e Nome são obrigatórios.")
                else:
                    dados = {
                        "codigo": codigo, "nome": nome, "data_entrada": str(data_entrada),
                        "raca": raca, "sexo": sexo, "categoria": categoria, "quantidade": quantidade,
                        "peso_entrada_total": peso_entrada_total, "preco_total": preco_total,
                        "preco_arroba": preco_arroba, "fornecedor": fornecedor,
                        "origem": origem, "observacoes": observacoes
                    }
                    try:
                        inserir_lote(dados)
                        st.success(f"✅ Lote **{codigo} - {nome}** cadastrado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro: {e}")

    with tab3:
        st.subheader("🐄 Animais por Lote")
        lotes = listar_lotes()
        if lotes.empty:
            st.info("Cadastre um lote primeiro.")
            return

        lote_sel = st.selectbox("Selecionar Lote", lotes["codigo"] + " — " + lotes["nome"])
        lote_codigo = lote_sel.split(" — ")[0]
        lote_id = lotes[lotes["codigo"] == lote_codigo].iloc[0]["id"]

        animais = listar_animais(lote_id)
        if not animais.empty:
            colunas = ["brinco", "nome", "sexo", "raca", "data_nascimento", "peso_entrada", "status"]
            nomes_col = ["Brinco", "Nome", "Sexo", "Raça", "Nasc.", "Peso Entrada (kg)", "Status"]
            st.dataframe(animais[colunas].rename(columns=dict(zip(colunas, nomes_col))),
                         use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum animal individual cadastrado neste lote.")

        st.markdown("---")
        st.subheader("➕ Cadastrar Animal Individual")
        with st.form("form_animal", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                brinco = st.text_input("Número do Brinco *", placeholder="Ex: 0042")
                nome_animal = st.text_input("Nome/Apelido", placeholder="Opcional")
                sexo_animal = st.selectbox("Sexo", ["Macho", "Fêmea"])
                raca_animal = st.selectbox("Raça", RACAS)
            with col2:
                data_nasc = st.date_input("Data de Nascimento", value=None)
                peso_entrada = st.number_input("Peso de Entrada (kg)", min_value=0.0, step=0.5)
                obs_animal = st.text_area("Observações")

            sub_animal = st.form_submit_button("💾 Cadastrar Animal", use_container_width=True)
            if sub_animal:
                if not brinco:
                    st.error("Número do brinco é obrigatório.")
                else:
                    dados_a = {
                        "lote_id": lote_id, "brinco": brinco, "nome": nome_animal,
                        "sexo": sexo_animal, "raca": raca_animal,
                        "data_nascimento": str(data_nasc) if data_nasc else None,
                        "peso_entrada": peso_entrada, "observacoes": obs_animal
                    }
                    try:
                        inserir_animal(dados_a)
                        st.success(f"✅ Animal brinco **{brinco}** cadastrado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
