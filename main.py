import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from inventario_ops import (
    get_engine_sqlserver,
    ler_material_estoque,
    ler_lista_contagem,
    ler_material_rescaldo,
    ler_lista_rescaldo,
    inserir_dados_sqlserver
)

# =============================
# CORES ANSI
# =============================
class Cores:
    RESET = "\033[0m"
    VERDE = "\033[92m"
    VERMELHO = "\033[91m"
    AMARELO = "\033[93m"
    AZUL = "\033[94m"
    CIANO = "\033[96m"
    NEGRITO = "\033[1m"

def sucesso(msg):
    print(f"{Cores.VERDE}✅ {msg}{Cores.RESET}")

def erro(msg):
    print(f"{Cores.VERMELHO}❌ {msg}{Cores.RESET}")

def info(msg):
    print(f"{Cores.CIANO}ℹ️  {msg}{Cores.RESET}")

def aviso(msg):
    print(f"{Cores.AMARELO}⚠️  {msg}{Cores.RESET}")

def titulo(msg):
    print(f"\n{Cores.NEGRITO}{Cores.AZUL}{msg}{Cores.RESET}")

def separador():
    print(f"{Cores.AZUL}{'=' * 60}{Cores.RESET}")

# =============================
# FUNÇÕES AUXILIARES
# =============================
def listar_inventarios():
    engine = get_engine_sqlserver()
    query = "SELECT ID_INVENTARIO, SITE, NAVE, RESPONSAVEL, ATIVO, DATACADASTRO FROM Inventario ORDER BY ID_INVENTARIO DESC"
    df = pd.read_sql(query, engine)
    if df.empty:
        aviso("Nenhum inventário encontrado.")
    else:
        print(f"\n{Cores.NEGRITO}📋 Inventários existentes:{Cores.RESET}")
        print(df.to_string(index=False))
    return df

def criar_inventario():
    engine = get_engine_sqlserver()

    separador()
    titulo("CRIAR NOVO INVENTÁRIO")
    separador()

    site = input("SITE: ").strip()
    nave = input("NAVE: ").strip()
    responsavel = input("RESPONSÁVEL: ").strip()

    if not site or not nave or not responsavel:
        erro("Todos os campos são obrigatórios!")
        return None

    query = """
        INSERT INTO Inventario (SITE, NAVE, RESPONSAVEL, ATIVO)
        VALUES (:site, :nave, :responsavel, 1)
    """
    with engine.connect() as conn:
        conn.execute(
            text(query),
            {"site": site, "nave": nave, "responsavel": responsavel}
        )
        conn.commit()

    sucesso("Inventário criado com sucesso!")

    df = pd.read_sql("SELECT MAX(ID_INVENTARIO) AS NovoID FROM Inventario", engine)
    novo_id = df.iloc[0]["NovoID"]
    info(f"Novo ID do inventário: {novo_id}")
    return novo_id

def solicitar_motivo():
    print(f"\n{Cores.NEGRITO}Selecione o motivo da carga:{Cores.RESET}")
    print(f"  {Cores.VERDE}0 = Inicial{Cores.RESET}")
    print(f"  {Cores.VERMELHO}1 = Final{Cores.RESET}")

    while True:
        motivo = input("Motivo (0/1): ").strip()
        if motivo in ["0", "1"]:
            return int(motivo)
        aviso("Valor inválido! Digite 0 ou 1.")

def solicitar_inventario():
    listar_inventarios()
    while True:
        inventario = input("\nID do inventário: ").strip()
        if inventario.isdigit() and int(inventario) > 0:
            return int(inventario)
        erro("ID inválido! Digite um número inteiro positivo.")

# =============================
# FUNÇÕES DE CARGA
# =============================
def carregar_material_estoque(inventario):
    motivo = solicitar_motivo()
    modo = input("Buscar por (1) Site/Nave ou (2) Lista de materiais? ").strip()

    site, nave, materiais = None, None, None

    if modo == "1":
        site = input("SITE: ").strip()
        nave = input("NAVE: ").strip()
    else:
        lista_materiais = input("Códigos separados por vírgula: ").strip()
        materiais = [m.strip() for m in lista_materiais.split(",") if m.strip()]

    info("Consultando Oracle...")
    df = ler_material_estoque(inventario, site=site, nave=nave, materiais=materiais, motivo=motivo)
    info(f"Registros encontrados: {len(df)}")

    if df.empty:
        aviso("Nenhum registro encontrado.")
        return

    print(df.head())
    confirmar = input("\nConfirmar inserção? (s/n): ").strip().lower()

    if confirmar == "s":
        result = inserir_dados_sqlserver(df, "MaterialEstoque")
        if result["sucesso"]:
            sucesso(result["mensagem"])
        else:
            erro(result["mensagem"])

def carregar_lista_contagem(inventario):
    motivo = solicitar_motivo()
    numero_lista = input("Número da lista de contagem: ").strip()

    if not numero_lista:
        erro("Número da lista é obrigatório!")
        return

    info("Consultando Oracle...")
    df = ler_lista_contagem(numero_lista, inventario, tipo_contagem=1, motivo=motivo)
    info(f"Registros encontrados: {len(df)}")

    if df.empty:
        aviso("Nenhum registro encontrado.")
        return

    print(df.head())
    confirmar = input("\nConfirmar inserção? (s/n): ").strip().lower()

    if confirmar == "s":
        result = inserir_dados_sqlserver(df, "RelContagem")
        if result["sucesso"]:
            sucesso(result["mensagem"])
        else:
            erro(result["mensagem"])

def carregar_material_rescaldo(inventario):
    motivo = solicitar_motivo()
    modo = input("Buscar por (1) Site/Nave ou (2) Lista de materiais? ").strip()

    site, nave, materiais = None, None, None

    if modo == "1":
        site = input("SITE: ").strip()
        nave = input("NAVE: ").strip()
    else:
        lista_materiais = input("Códigos separados por vírgula: ").strip()
        materiais = [m.strip() for m in lista_materiais.split(",") if m.strip()]

    info("Consultando Oracle...")
    df = ler_material_rescaldo(inventario, site=site, nave=nave, materiais=materiais, motivo=motivo)
    info(f"Registros encontrados: {len(df)}")

    if df.empty:
        aviso("Nenhum registro encontrado.")
        return

    print(df.head())
    confirmar = input("\nConfirmar inserção? (s/n): ").strip().lower()

    if confirmar == "s":
        result = inserir_dados_sqlserver(df, "MaterialEstoqueRescaldo")
        if result["sucesso"]:
            sucesso(result["mensagem"])
        else:
            erro(result["mensagem"])

def carregar_contagem_rescaldo(inventario):
    motivo = solicitar_motivo()
    numero_lista = input("Número da lista de rescaldo: ").strip()

    if not numero_lista:
        erro("Número da lista é obrigatório!")
        return

    info("Consultando Oracle...")
    df = ler_lista_rescaldo(numero_lista, inventario, motivo)
    info(f"Registros encontrados: {len(df)}")

    if df.empty:
        aviso("Nenhum registro encontrado.")
        return

    print(df.head())
    confirmar = input("\nConfirmar inserção? (s/n): ").strip().lower()

    if confirmar == "s":
        result = inserir_dados_sqlserver(df, "RelContagemRescaldo")
        if result["sucesso"]:
            sucesso(result["mensagem"])
        else:
            erro(result["mensagem"])

# =============================
# MENU PRINCIPAL
# =============================
def menu_principal():
    while True:
        separador()
        titulo("📦 SISTEMA DE INVENTÁRIO")
        separador()
        print(f"  {Cores.CIANO}1.{Cores.RESET} Listar inventários existentes")
        print(f"  {Cores.CIANO}2.{Cores.RESET} Criar novo inventário")
        print(f"  {Cores.CIANO}3.{Cores.RESET} Carregar Material de Estoque")
        print(f"  {Cores.CIANO}4.{Cores.RESET} Carregar Lista de Contagem")
        print(f"  {Cores.CIANO}5.{Cores.RESET} Carregar Material de Rescaldo")
        print(f"  {Cores.CIANO}6.{Cores.RESET} Carregar Contagem de Rescaldo")
        print(f"  {Cores.VERMELHO}0.{Cores.RESET} Sair")
        separador()

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            listar_inventarios()
        elif opcao == "2":
            criar_inventario()
        elif opcao == "3":
            inventario = solicitar_inventario()
            carregar_material_estoque(inventario)
        elif opcao == "4":
            inventario = solicitar_inventario()
            carregar_lista_contagem(inventario)
        elif opcao == "5":
            inventario = solicitar_inventario()
            carregar_material_rescaldo(inventario)
        elif opcao == "6":
            inventario = solicitar_inventario()
            carregar_contagem_rescaldo(inventario)
        elif opcao == "0":
            titulo("👋 Saindo do sistema...")
            break
        else:
            erro("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    menu_principal()
