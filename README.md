# 🧭 Sistema Itatchi

### Solução para gestão e controle de documentos com prazos de validade  
_Projeto desenvolvido na disciplina BRAOTI2 – Instituto Federal de São Paulo, Campus Bragança Paulista_

---

## 📌 Descrição do Projeto

O **Sistema Itatchi** é uma aplicação web desenvolvida para **gestão automatizada de documentos corporativos com prazos de validade**, substituindo controles manuais e planilhas dispersas por uma solução centralizada, intuitiva e escalável.  
Seu propósito é facilitar o **monitoramento, a consulta e o acompanhamento de documentos** — garantindo maior eficiência e confiabilidade na gestão da informação.

O sistema foi idealizado no contexto da disciplina **Projeto de Tecnologia da Informação e Comunicação 2 (BRAOTI2)**, aplicando princípios de **Design Thinking** e **desenvolvimento ágil** para transformar um problema real em um produto de software funcional.

---

## 🎯 Objetivo

O projeto visa:

- Automatizar o **controle de prazos e vencimentos** de documentos;
- Permitir o **cadastro estruturado e filtragem inteligente** de informações;
- Proporcionar **alertas visuais e relatórios gerenciais**;
- Reduzir o risco de não conformidade e **melhorar a organização interna**.

---

## ⚙️ Arquitetura e Tecnologias

A arquitetura é modular e separa claramente as responsabilidades entre **backend (Flask)** e **frontend (Streamlit)**:

itatchi/
├── backend/
│   ├── app_backend.py                 # Inicialização do servidor Flask
│   ├── routes/
│   │   └── documentos_routes.py       # Rotas da API e atualização automática de status
│   ├── logic/
│   │   └── status_calculator.py       # Cálculo de status (vigente, a vencer, vencido)
│   ├── models/                        # Modelos de dados com SQLAlchemy
│   └── database/
│       └── connection.py              # Configuração de conexão com banco MySQL/SQLite
│
├── frontend/
│   ├── app_frontend.py                # Página principal (Central de Consultas)
│   ├── pages/
│   │   ├── 1_cadastro_documento.py
│   │   └── 2_central_de_alertas.py
│   ├── utils/
│   │   └── ui_helpers.py              # Funções auxiliares (CSS, imagens base64)
│   ├── style.css                      # Estilos globais do sistema
│   └── assets/
│       ├── logo_itatchi.png
│       └── alert_marker.png
│
└── README.md

---

## 💡 Funcionalidades Principais

### 🗂️ Cadastro de Documentos
- Registro de documentos por título, tipo, filial, responsável, validade e número;
- Armazenamento persistente via SQLAlchemy;
- Cálculo automático do status (`VIGENTE`, `A_VENCER`, `VENCIDO`, `SEM_VALIDADE`).

### 📊 Central de Consultas
- Filtros dinâmicos por **categoria**, **período** e **status**;
- Paginação automática em tabelas com resumo dos documentos;
- Calendário interativo com **ícones de alerta personalizados (PNG)**;
- Reordenação automática para exibir **vencidos no topo**.

### ⚠️ Central de Alertas
- Exibição priorizada de documentos **VENCIDOS** e **A_VENCER**;
- Destaque em cores (vermelho/amarelo) conforme o status;
- Atualização automática de status no banco ao carregar os dados.

### 📈 Relatórios
- Geração de relatórios **Excel (.xlsx)** com todos os campos do documento;
- Nome do arquivo reflete o filtro selecionado:
  - `relatorio_alertas_todos_YYYYMMDD_a_YYYYMMDD.xlsx`
  - `relatorio_alertas_a_vencer_YYYYMMDD_a_YYYYMMDD.xlsx`
  - `relatorio_alertas_vencidos_YYYYMMDD_a_YYYYMMDD.xlsx`
- Relatórios ordenados com documentos vencidos primeiro.

---

## 🧩 Metodologia

A metodologia de desenvolvimento seguiu o **Design Thinking**, estruturada em cinco etapas:

1. **Descoberta** – identificação do problema da gestão manual de prazos;  
2. **Definição** – construção da persona *Tati*, gerente de conformidade;  
3. **Ideação** – brainstorming e seleção de soluções viáveis;  
4. **Prototipagem** – implementação do sistema em Python (Flask + Streamlit);  

---

## 🧱 Tecnologias Utilizadas

| Componente | Tecnologia | Função |
|-------------|-------------|--------|
| **Frontend** | Streamlit + CSS | Interface web e exibição de calendários e tabelas |
| **Backend** | Flask | API REST e lógica de negócio |
| **Banco de Dados** | MySQL / SQLite | Armazenamento estruturado |
| **ORM** | SQLAlchemy | Mapeamento objeto-relacional |
| **Planilhas** | Pandas + XlsxWriter | Geração dinâmica de relatórios |
| **Ambiente** | Python 3.11+ | Plataforma base |

---

## 🚀 Como Executar o Sistema

### 1. Clonar o repositório
```bash
git clone https://github.com/usuario/sistema-itatchi.git
cd sistema-itatchi
