import sqlite3
import pandas as pd
from pathlib import Path
import os

DB_PATH = Path(__file__).parent.parent / "data" / "fazenda.db"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS lotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            data_entrada DATE NOT NULL,
            raca TEXT,
            sexo TEXT,
            categoria TEXT,
            quantidade INTEGER,
            peso_entrada_total REAL,
            preco_total REAL,
            preco_arroba REAL,
            fornecedor TEXT,
            origem TEXT,
            observacoes TEXT,
            status TEXT DEFAULT 'Ativo',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS animais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id INTEGER NOT NULL,
            brinco TEXT UNIQUE NOT NULL,
            nome TEXT,
            sexo TEXT,
            raca TEXT,
            data_nascimento DATE,
            peso_entrada REAL,
            status TEXT DEFAULT 'Ativo',
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lote_id) REFERENCES lotes(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS pesagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id INTEGER,
            lote_id INTEGER NOT NULL,
            data_pesagem DATE NOT NULL,
            peso REAL NOT NULL,
            tipo TEXT DEFAULT 'Rotina',
            responsavel TEXT,
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (animal_id) REFERENCES animais(id),
            FOREIGN KEY (lote_id) REFERENCES lotes(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id INTEGER,
            animal_id INTEGER,
            tipo TEXT NOT NULL,
            descricao TEXT,
            data_ocorrencia DATE NOT NULL,
            responsavel TEXT,
            custo REAL DEFAULT 0,
            tratamento TEXT,
            status TEXT DEFAULT 'Aberta',
            data_resolucao DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lote_id) REFERENCES lotes(id),
            FOREIGN KEY (animal_id) REFERENCES animais(id)
        )
    """)

    conn.commit()
    conn.close()

# ---- LOTES ----
def inserir_lote(dados):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO lotes (codigo, nome, data_entrada, raca, sexo, categoria, quantidade,
            peso_entrada_total, preco_total, preco_arroba, fornecedor, origem, observacoes)
        VALUES (:codigo, :nome, :data_entrada, :raca, :sexo, :categoria, :quantidade,
            :peso_entrada_total, :preco_total, :preco_arroba, :fornecedor, :origem, :observacoes)
    """, dados)
    conn.commit()
    lote_id = c.lastrowid
    conn.close()
    return lote_id

def listar_lotes():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM lotes ORDER BY data_entrada DESC", conn)
    conn.close()
    return df

def get_lote(lote_id):
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM lotes WHERE id = ?", conn, params=(lote_id,))
    conn.close()
    return df.iloc[0] if not df.empty else None

def atualizar_lote(lote_id, dados):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE lotes SET nome=:nome, raca=:raca, sexo=:sexo, categoria=:categoria,
            quantidade=:quantidade, peso_entrada_total=:peso_entrada_total,
            preco_total=:preco_total, preco_arroba=:preco_arroba,
            fornecedor=:fornecedor, origem=:origem, observacoes=:observacoes, status=:status
        WHERE id=:id
    """, {**dados, "id": lote_id})
    conn.commit()
    conn.close()

# ---- ANIMAIS ----
def inserir_animal(dados):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO animais (lote_id, brinco, nome, sexo, raca, data_nascimento, peso_entrada, observacoes)
        VALUES (:lote_id, :brinco, :nome, :sexo, :raca, :data_nascimento, :peso_entrada, :observacoes)
    """, dados)
    conn.commit()
    animal_id = c.lastrowid
    conn.close()
    return animal_id

def listar_animais(lote_id=None):
    conn = get_connection()
    if lote_id:
        df = pd.read_sql(
            "SELECT a.*, l.codigo as lote_codigo, l.nome as lote_nome FROM animais a JOIN lotes l ON a.lote_id = l.id WHERE a.lote_id = ? ORDER BY a.brinco",
            conn, params=(lote_id,)
        )
    else:
        df = pd.read_sql(
            "SELECT a.*, l.codigo as lote_codigo, l.nome as lote_nome FROM animais a JOIN lotes l ON a.lote_id = l.id ORDER BY a.brinco",
            conn
        )
    conn.close()
    return df

# ---- PESAGENS ----
def inserir_pesagem(dados):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO pesagens (animal_id, lote_id, data_pesagem, peso, tipo, responsavel, observacoes)
        VALUES (:animal_id, :lote_id, :data_pesagem, :peso, :tipo, :responsavel, :observacoes)
    """, dados)
    conn.commit()
    conn.close()

def listar_pesagens(lote_id=None, animal_id=None):
    conn = get_connection()
    if animal_id:
        df = pd.read_sql("""
            SELECT p.*, a.brinco, l.codigo as lote_codigo
            FROM pesagens p 
            LEFT JOIN animais a ON p.animal_id = a.id
            LEFT JOIN lotes l ON p.lote_id = l.id
            WHERE p.animal_id = ? ORDER BY p.data_pesagem
        """, conn, params=(animal_id,))
    elif lote_id:
        df = pd.read_sql("""
            SELECT p.*, a.brinco, l.codigo as lote_codigo
            FROM pesagens p 
            LEFT JOIN animais a ON p.animal_id = a.id
            LEFT JOIN lotes l ON p.lote_id = l.id
            WHERE p.lote_id = ? ORDER BY p.data_pesagem
        """, conn, params=(lote_id,))
    else:
        df = pd.read_sql("""
            SELECT p.*, a.brinco, l.codigo as lote_codigo
            FROM pesagens p 
            LEFT JOIN animais a ON p.animal_id = a.id
            LEFT JOIN lotes l ON p.lote_id = l.id
            ORDER BY p.data_pesagem DESC
        """, conn)
    conn.close()
    return df

# ---- OCORRÊNCIAS ----
def inserir_ocorrencia(dados):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO ocorrencias (lote_id, animal_id, tipo, descricao, data_ocorrencia, responsavel, custo, tratamento, status)
        VALUES (:lote_id, :animal_id, :tipo, :descricao, :data_ocorrencia, :responsavel, :custo, :tratamento, :status)
    """, dados)
    conn.commit()
    conn.close()

def listar_ocorrencias(lote_id=None, animal_id=None):
    conn = get_connection()
    base = """
        SELECT o.*, l.codigo as lote_codigo, a.brinco 
        FROM ocorrencias o 
        LEFT JOIN lotes l ON o.lote_id = l.id
        LEFT JOIN animais a ON o.animal_id = a.id
    """
    if animal_id:
        df = pd.read_sql(base + " WHERE o.animal_id = ? ORDER BY o.data_ocorrencia DESC", conn, params=(animal_id,))
    elif lote_id:
        df = pd.read_sql(base + " WHERE o.lote_id = ? ORDER BY o.data_ocorrencia DESC", conn, params=(lote_id,))
    else:
        df = pd.read_sql(base + " ORDER BY o.data_ocorrencia DESC", conn)
    conn.close()
    return df

def resolver_ocorrencia(ocorrencia_id, data_resolucao):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE ocorrencias SET status='Resolvida', data_resolucao=? WHERE id=?", (data_resolucao, ocorrencia_id))
    conn.commit()
    conn.close()

# ---- ANALYTICS ----
def calcular_gmd(animal_id):
    """Calcula GMD (Ganho de Peso Médio Diário) de um animal."""
    df = listar_pesagens(animal_id=animal_id)
    if len(df) < 2:
        return None
    df = df.sort_values("data_pesagem")
    df["data_pesagem"] = pd.to_datetime(df["data_pesagem"])
    primeiro = df.iloc[0]
    ultimo = df.iloc[-1]
    dias = (ultimo["data_pesagem"] - primeiro["data_pesagem"]).days
    if dias == 0:
        return None
    gmd = (ultimo["peso"] - primeiro["peso"]) / dias
    return {
        "gmd": round(gmd, 3),
        "peso_inicial": primeiro["peso"],
        "peso_final": ultimo["peso"],
        "ganho_total": round(ultimo["peso"] - primeiro["peso"], 2),
        "dias": dias,
        "n_pesagens": len(df)
    }

def calcular_gmd_lote(lote_id):
    """Calcula GMD médio do lote."""
    animais = listar_animais(lote_id)
    if animais.empty:
        return None
    resultados = []
    for _, animal in animais.iterrows():
        gmd = calcular_gmd(animal["id"])
        if gmd:
            gmd["brinco"] = animal["brinco"]
            gmd["animal_id"] = animal["id"]
            resultados.append(gmd)
    return pd.DataFrame(resultados) if resultados else None

def resumo_dashboard():
    conn = get_connection()
    lotes = pd.read_sql("SELECT * FROM lotes WHERE status='Ativo'", conn)
    animais = pd.read_sql("SELECT * FROM animais WHERE status='Ativo'", conn)
    ocorrencias = pd.read_sql("SELECT * FROM ocorrencias WHERE status='Aberta'", conn)
    pesagens = pd.read_sql("SELECT * FROM pesagens", conn)
    conn.close()
    return {
        "total_lotes": len(lotes),
        "total_animais": len(animais),
        "ocorrencias_abertas": len(ocorrencias),
        "total_pesagens": len(pesagens),
        "valor_total_investido": lotes["preco_total"].sum() if not lotes.empty else 0
    }

# Inicializa banco ao importar
init_db()
