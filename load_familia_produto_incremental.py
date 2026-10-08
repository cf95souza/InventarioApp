import pandas as pd
import cx_Oracle
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# -------------------------
# 1) Carregar variáveis de ambiente
# -------------------------
load_dotenv()

# SQL Server
SQLSERVER_SERVER = os.getenv("SQLSERVER_SERVER")
SQLSERVER_DATABASE = os.getenv("SQLSERVER_DATABASE")
SQLSERVER_USER = os.getenv("SQLSERVER_USER")
SQLSERVER_PASSWORD = os.getenv("SQLSERVER_PASSWORD")
SQLSERVER_DRIVER = os.getenv("SQLSERVER_DRIVER")

# Oracle
ORACLE_USER = os.getenv("ORACLE_USER")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD")
ORACLE_DSN = os.getenv("ORACLE_DSN")

# -------------------------
# 2) Query Oracle
# -------------------------
QUERY_ORACLE = """
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

# -------------------------
# 3) Conexões
# -------------------------
def get_oracle_connection():
    return cx_Oracle.connect(ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN)

def get_sqlserver_engine():
    conn_str = (
        f"mssql+pyodbc://{SQLSERVER_USER}:{SQLSERVER_PASSWORD}"
        f"@{SQLSERVER_SERVER}/{SQLSERVER_DATABASE}"
        f"?driver={SQLSERVER_DRIVER.replace(' ', '+')}"
    )
    return create_engine(conn_str, fast_executemany=True)

# -------------------------
# 4) Processo Incremental
# -------------------------
def carga_incremental():
    print("Lendo dados Oracle...")
    conn_oracle = get_oracle_connection()
    df_oracle = pd.read_sql(QUERY_ORACLE, conn_oracle)
    conn_oracle.close()

    df_oracle.columns = df_oracle.columns.str.strip().str.upper()
    df_oracle.rename(columns={
        "CODMATERIAL": "CodMaterial",
        "DESCRICAO": "Descricao",
        "SITE": "Site",
        "FAMILIA": "Familia"
    }, inplace=True)

    print(f"Linhas no Oracle: {len(df_oracle)}")

    engine_sql = get_sqlserver_engine()

    print("Lendo dados SQL Server...")
    df_sql = pd.read_sql("SELECT * FROM dbo.FamiliaProduto", engine_sql)

    if df_sql.empty:
        print("SQL Server vazio — primeira carga será 'inserção total'.")
        df_oracle.to_sql("FamiliaProduto", engine_sql, schema="dbo",
                         if_exists="append", index=False)
        print("Primeira carga concluída com sucesso!")
        return {"mensagem": "Primeira carga concluída!", "novos": len(df_oracle), "alterados": 0, "total_oracle": len(df_oracle)}

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

    print(f"Novos registros: {len(df_novos)}")
    print(f"Registros alterados: {len(df_alterados)}")

    if len(df_novos) > 0:
        df_novos[["CodMaterial", "Descricao", "Site", "Familia"]].to_sql(
            "FamiliaProduto", engine_sql, schema="dbo", if_exists="append", index=False
        )
        print("Novos registros inseridos.")

    if len(df_alterados) > 0:
        with engine_sql.begin() as conn:
            for _, row in df_alterados.iterrows():
                conn.execute(text("""
                    UPDATE dbo.FamiliaProduto 
                    SET Descricao = :Descricao, Familia = :Familia
                    WHERE CodMaterial = :CodMaterial AND Site = :Site
                """), dict(row))
        print("Registros alterados atualizados.")

    print("Carga incremental concluída!")
    return {"mensagem": "Carga incremental concluída!", "novos": len(df_novos), "alterados": len(df_alterados), "total_oracle": len(df_oracle)}

# -------------------------
# 5) Executar
# -------------------------
if __name__ == "__main__":
    carga_incremental()
