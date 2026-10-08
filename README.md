# 📦 InventarioApp

Sistema de gerenciamento de inventários para controle de estoques e contagens.

## Funcionalidades

- **Material de Estoque**: Consulta e carga de materiais do Oracle para SQL Server
- **Lista de Contagem**: Gerenciamento de listas de contagem de inventário
- **Material Rescaldo**: Controle de materiais de rescaldo
- **Contagem Rescaldo**: Listas de contagem de rescaldo
- **Carga Incremental**: Atualização automática de família de produtos

## Stack

| Tecnologia | Uso |
|------------|-----|
| Python | Linguagem principal |
| Streamlit | Interface web |
| SQLAlchemy | ORM para SQL Server |
| pyodbc | Conexão SQL Server |
| cx_Oracle | Conexão Oracle |
| pandas | Manipulação de dados |
| openpyxl | Exportação Excel |

## Instalação

```bash
# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt
```

## Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
# SQL SERVER
SQLSERVER_SERVER=seu_servidor
SQLSERVER_DATABASE=sua_database
SQLSERVER_USER=seu_usuario
SQLSERVER_PASSWORD=sua_senha
SQLSERVER_DRIVER=ODBC Driver 17 for SQL Server

# ORACLE
ORACLE_USER=seu_usuario
ORACLE_PASSWORD=sua_senha
ORACLE_DSN=host:port/sid
```

## Uso

### Interface Web (Streamlit)

```bash
streamlit run streamlit_app.py
```

### Interface de Linha de Comando (CLI)

```bash
python main.py
```

## Estrutura

```
InventarioApp/
├── streamlit_app.py      # Interface web
├── main.py               # Interface CLI
├── inventario_ops.py     # Operações de banco de dados
├── requirements.txt      # Dependências
├── .env                  # Variáveis de ambiente (não versionar)
└── README.md             # Esta documentação
```

## Licença

Todos os direitos reservados Acotubo 2025
