import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import cx_Oracle
from contextlib import contextmanager

load_dotenv()

# =============================
# CONEXÕES
# =============================
def get_engine_sqlserver():
    server = os.getenv("SQLSERVER_SERVER")
    database = os.getenv("SQLSERVER_DATABASE")
    username = os.getenv("SQLSERVER_USER")
    password = os.getenv("SQLSERVER_PASSWORD")
    driver = os.getenv("SQLSERVER_DRIVER")
    conn_str = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}"
    return create_engine(conn_str, fast_executemany=True)

@contextmanager
def get_conn_oracle():
    user = os.getenv("ORACLE_USER")
    password = os.getenv("ORACLE_PASSWORD")
    dsn = os.getenv("ORACLE_DSN")
    conn = cx_Oracle.connect(user=user, password=password, dsn=dsn)
    try:
        yield conn
    finally:
        conn.close()


def get_engine_oracle():
    """Retorna um SQLAlchemy Engine para o Oracle (usa cx_Oracle como driver).
    Usar um engine permite ao pandas.read_sql aceitar um connectable suportado
    e evita o UserWarning sobre DBAPI2 objects.
    """
    user = os.getenv("ORACLE_USER")
    password = os.getenv("ORACLE_PASSWORD")
    dsn = os.getenv("ORACLE_DSN")
    # Exemplo de dsn: host:port/service_name ou um TNS alias configurado
    conn_str = f"oracle+cx_oracle://{user}:{password}@{dsn}"
    return create_engine(conn_str)

# =============================
# UTIL: Normalizar colunas
# =============================
def normalize_columns(df):
    if df is None or df.empty:
        return df

    mapping = {
        "LOCATION_NO": "CodLocal",
        "CONTRACT": "Site",
        "PART_NO": "CodMaterial",
        "QTY_ONHAND": "QtdEstoque",
        "QTY_COUNTED": "QtdContada",
        "LOT_BATCH_NO": "CodLote",
        "INV_LIST_NO": "Numero",
        "COUNT_DATE": "DataConfirmacao",
        "INVENTORY_VALUE": "CustoUnd",
        "DESCRIPTION": "Descricao",
        "DESCRICAO": "Descricao",
        "SEQ": "Seq",
        "UM": "UM",
        "TECHNICAL_CLASS": "Familia"
    }

    col_map = {}
    for col in df.columns:
        if col.upper() in mapping:
            col_map[col] = mapping[col.upper()]

    return df.rename(columns=col_map)

def aplicar_motivo(df, motivo):
    df["Motivo"] = motivo
    return df

# =============================
# LEITURA ORACLE - MATERIAL DE ESTOQUE
# =============================
def ler_material_estoque(inventario, site=None, nave=None, materiais=None, motivo=0):
    query = """
        SELECT ips.LOCATION_NO AS CodLocal,
               ips.CONTRACT AS Site,
               ips.PART_NO AS CodMaterial,
               INVENTORY_PART_API.Get_Description(ips.CONTRACT, ips.PART_NO) AS Descricao,
               Inventory_Part_API.Get_Unit_Meas(ips.CONTRACT, ips.PART_NO) AS UM,
               ips.QTY_ONHAND AS QtdEstoque,
               ips.LOT_BATCH_NO AS CodLote
        FROM IFSACO.INVENTORY_PART_IN_STOCK ips
        WHERE 1=1
    """
    params = {}

    if materiais:
        placeholders = ", ".join([f":mat{i}" for i in range(len(materiais))])
        query += f" AND ips.PART_NO IN ({placeholders})"
        for i, m in enumerate(materiais):
            params[f"mat{i}"] = m
    else:
        if site:
            query += " AND ips.CONTRACT = :site"
            params["site"] = site
        if nave:
            query += " AND ips.LOCATION_NO = :nave"
            params["nave"] = nave

    engine = get_engine_oracle()
    df = pd.read_sql(query, engine, params=params)

    df = normalize_columns(df)
    df["Inventario"] = inventario
    df = aplicar_motivo(df, motivo)
    return df

# =============================
# LEITURA ORACLE - MATERIAL RESCALDO
# =============================
def ler_material_rescaldo(inventario, site=None, nave=None, materiais=None, motivo=0):
    query = """
        SELECT ips.LOCATION_NO AS CodLocal,
               ips.CONTRACT AS Site,
               ips.PART_NO AS CodMaterial,
               INVENTORY_PART_API.Get_Description(ips.CONTRACT, ips.PART_NO) AS Descricao,
               INVENTORY_PART_API.Get_Unit_Meas(ips.CONTRACT, ips.PART_NO) AS UM,
               ips.QTY_ONHAND AS QtdEstoque,
               ips.LOT_BATCH_NO AS CodLote
        FROM IFSACO.INVENTORY_PART_IN_STOCK ips
        WHERE 1=1
    """
    params = {}

    if site:
        query += " AND ips.CONTRACT = :site"
        params["site"] = site
    if nave:
        query += " AND ips.LOCATION_NO LIKE :nave"
        params["nave"] = f"%{nave}%"
    if materiais:
        placeholders = ", ".join([f":mat{i}" for i in range(len(materiais))])
        query += f" AND ips.PART_NO IN ({placeholders})"
        for i, m in enumerate(materiais):
            params[f"mat{i}"] = m

    engine = get_engine_oracle()
    df = pd.read_sql(query, engine, params=params)

    df = normalize_columns(df)
    df["Inventario"] = inventario
    df = aplicar_motivo(df, motivo)
    return df

# =============================
# LEITURA ORACLE - LISTA DE CONTAGEM
# =============================
def ler_lista_contagem(numero_lista, inventario, tipo_contagem=1, motivo=0):
    query = """
        SELECT crt.INV_LIST_NO AS Numero,
               crt.SEQ,
               crt.CONTRACT AS Site,
               crt.PART_NO AS CodMaterial,
               IFSACO.INVENTORY_PART_API.Get_Description(crt.CONTRACT, crt.PART_NO) AS Descricao,
               crt.LOCATION_NO AS CodLocal,
               crt.QTY_ONHAND AS QtdEstoque,
               crt.QTY_COUNTED AS QtdContada,
               IFSACO.Inventory_part_API.Get_Unit_Meas(crt.CONTRACT, crt.PART_NO) AS UM,
               crt.COUNT_DATE AS DataConfirmacao,
               crt.LOT_BATCH_NO AS CodLote,
               crt.INVENTORY_VALUE AS CustoUnd
        FROM IFSACO.COUNTING_RESULT_TAB crt
        WHERE crt.INV_LIST_NO = :lista
    """

    engine = get_engine_oracle()
    df = pd.read_sql(query, engine, params={"lista": numero_lista})

    df = normalize_columns(df)
    df["Inventario"] = inventario
    df["TipoContagem"] = tipo_contagem
    df = aplicar_motivo(df, motivo)
    return df

# =============================
# LEITURA ORACLE - LISTA DE CONTAGEM RESCALDO
# =============================
def ler_lista_rescaldo(numero_lista, inventario, motivo=0):
    return ler_lista_contagem(numero_lista, inventario, tipo_contagem=2, motivo=motivo)

# =============================
# GRAVAÇÃO SQL SERVER
# =============================
def inserir_dados_sqlserver(df, tabela):
    if df.empty:
        return {"sucesso": False, "mensagem": "Nenhum dado para inserir.", "registros": 0}

    engine = get_engine_sqlserver()
    try:
        df.to_sql(tabela, engine, if_exists="append", index=False)
        return {"sucesso": True, "mensagem": f"{len(df)} registros inseridos em {tabela}", "registros": len(df)}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e), "registros": 0}

# =============================
# CARGA INCREMENTAL - FAMILIA PRODUTO
# =============================
QUERY_FAMILIA_ORACLE = """
SELECT DISTINCT 
    a.part_no AS CodMaterial,
    PART_CATALOG_API.Get_Description(a.part_no) AS Descricao,
    a.contract AS Site, 
    TECHNICAL_CLASS AS Familia
FROM inventory_part a
INNER JOIN part_catalog b 
    ON b.part_no = a.part_no 
LEFT JOIN TECHNICAL_OBJECT_REFERENCE c 
    ON c.lu_name = 'PartCatalog' 
    AND c.key_value = Concat(a.part_no,'^')
"""

def carga_incremental_familia():
    engine = get_engine_oracle()
    df_oracle = pd.read_sql(QUERY_FAMILIA_ORACLE, engine)

    df_oracle.columns = df_oracle.columns.str.strip().str.upper()
    df_oracle.rename(columns={
        "CODMATERIAL": "CodMaterial",
        "DESCRICAO": "Descricao",
        "SITE": "Site",
        "FAMILIA": "Familia"
    }, inplace=True)

    engine_sql = get_engine_sqlserver()
    df_sql = pd.read_sql("SELECT * FROM dbo.FamiliaProduto", engine_sql)

    if df_sql.empty:
        df_oracle.to_sql("FamiliaProduto", engine_sql, schema="dbo",
                         if_exists="append", index=False)
        return {"novos": len(df_oracle), "alterados": 0, "mensagem": "Primeira carga concluída!"}

    df_sql.columns = df_sql.columns.str.strip()
    df_oracle["Chave"] = df_oracle["CodMaterial"] + "-" + df_oracle["Site"]
    df_sql["Chave"] = df_sql["CodMaterial"] + "-" + df_sql["Site"]

    df_novos = df_oracle[~df_oracle["Chave"].isin(df_sql["Chave"])]
    df_merge = df_oracle.merge(df_sql, on="Chave", suffixes=("_new", "_old"))
    df_alterados = df_merge[
        (df_merge["Descricao_new"] != df_merge["Descricao_old"]) |
        (df_merge["Familia_new"] != df_merge["Familia_old"])
    ][["CodMaterial_new", "Descricao_new", "Site_new", "Familia_new"]]
    df_alterados.columns = ["CodMaterial", "Descricao", "Site", "Familia"]

    if len(df_novos) > 0:
        df_novos[["CodMaterial", "Descricao", "Site", "Familia"]].to_sql(
            "FamiliaProduto", engine_sql, schema="dbo", if_exists="append", index=False
        )

    if len(df_alterados) > 0:
        with engine_sql.begin() as conn:
            batch_size = 500
            records = df_alterados[["CodMaterial", "Descricao", "Site", "Familia"]].to_dict("records")
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                conn.execute(
                    text("UPDATE dbo.FamiliaProduto SET Descricao = :Descricao, Familia = :Familia WHERE CodMaterial = :CodMaterial AND Site = :Site"),
                    batch
                )

    return {"novos": len(df_novos), "alterados": len(df_alterados), "mensagem": "Carga incremental concluída!"}
