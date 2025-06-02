import streamlit as st
import gspread
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound
import warnings

# Suprimir warnings específicos do pandas
warnings.filterwarnings("ignore", category=FutureWarning, message=".*observed=False.*")

# --- Configurações Globais e Constantes ---
SPREADSHEET_ID = "1NTScbiIna-iE7roQ9XBdjUOssRihTFFby4INAAQNXTg"
WORKSHEET_NAME = "Vendas"
LOGO_URL = "https://raw.githubusercontent.com/lucasricardocs/clips_dashboard/main/logo.png"

# Configuração da página Streamlit
st.set_page_config(
    page_title="Clips Burger - Mobile",
    layout="centered",
    page_icon=LOGO_URL,
    initial_sidebar_state="collapsed"
)

# Configuração de tema para gráficos
alt.data_transformers.enable("json")
alt.data_transformers.disable_max_rows()

# Paleta de cores para modo escuro
CORES_MODO_ESCURO = ["#4c78a8", "#54a24b", "#f58518", "#e45756", "#72b7b2", "#ff9da6", "#9d755d", "#bab0ac"]

# Ordem dos meses
meses_ordem = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
meses_dict = {nome: i+1 for i, nome in enumerate(meses_ordem)}

# --- CSS Customizado Melhorado com Animação de Fogo ---
def inject_enhanced_mobile_css():
    st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        /* Remove Streamlit header/footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Body/App Background */
        html, body, .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%) !important;
            color: #f8fafc;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            overflow-x: hidden;
        }

        /* Main content padding */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100%;
        }

        /* Logo Container com Efeito de Fogo */
        .logo-fire-container {
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 2rem auto;
            height: 280px;
            width: 100%;
            max-width: 400px;
            overflow: visible !important;
            z-index: 1;
        }
        
        /* Logo Principal - Z-INDEX ALTO E ANIMADA */
        .fire-logo {
            position: relative;
            z-index: 50;
            max-width: 200px;
            width: auto;
            height: auto;
            object-fit: contain;
            filter: drop-shadow(0 0 20px rgba(255, 69, 0, 0.8));
            animation: logoFloat 3s ease-in-out infinite;
            display: block;
            margin: 0 auto;
        }
        
        /* Animação de Flutuação da Logo */
        @keyframes logoFloat {
            0%, 100% {
                transform: translateY(0px) scale(1);
                filter: drop-shadow(0 0 20px rgba(255, 69, 0, 0.8));
            }
            50% {
                transform: translateY(-10px) scale(1.05);
                filter: drop-shadow(0 0 30px rgba(255, 140, 0, 1));
            }
        }
        
        /* Container das Chamas */
        .fire-container {
            position: absolute;
            bottom: -30px;
            left: 50%;
            transform: translateX(-50%);
            width: 300px;
            height: 800px;
            z-index: 1;
            pointer-events: none;
            overflow: visible !important;
        }
        
        /* Chamas Individuais */
        .flame {
            position: absolute;
            bottom: 0;
            border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
            transform-origin: center bottom;
            animation: flicker 0.5s ease-in-out infinite alternate;
            z-index: 10;
        }
        
        /* Animação das Chamas */
        @keyframes flicker {
            0% {
                transform: translateX(-50%) rotate(-2deg) scaleY(1);
                opacity: 0.8;
            }
            25% {
                transform: translateX(-50%) rotate(1deg) scaleY(1.1);
                opacity: 0.9;
            }
            50% {
                transform: translateX(-50%) rotate(-1deg) scaleY(0.95);
                opacity: 1;
            }
            75% {
                transform: translateX(-50%) rotate(2deg) scaleY(1.05);
                opacity: 0.85;
            }
            100% {
                transform: translateX(-50%) rotate(-1deg) scaleY(1);
                opacity: 0.9;
            }
        }
        
        /* Chama Principal (Vermelha) */
        .flame-red {
            left: 50%;
            transform: translateX(-50%);
            width: 80px;
            height: 120px;
            background: radial-gradient(circle, #ff4500 0%, #ff6347 30%, #dc143c 70%, #8b0000 100%);
            box-shadow: 0 0 30px #ff4500, 0 0 60px #ff6347, 0 0 90px #dc143c;
            animation: flicker 0.8s ease-in-out infinite alternate;
        }
        
        /* Chama Laranja */
        .flame-orange {
            left: 45%;
            transform: translateX(-50%);
            width: 60px;
            height: 90px;
            background: radial-gradient(circle, #ffa500 0%, #ff8c00 50%, #ff4500 100%);
            box-shadow: 0 0 25px #ffa500, 0 0 50px #ff8c00;
            animation: flicker 0.6s ease-in-out infinite alternate;
            animation-delay: 0.2s;
        }
        
        /* Chama Amarela */
        .flame-yellow {
            left: 55%;
            transform: translateX(-50%);
            width: 40px;
            height: 70px;
            background: radial-gradient(circle, #ffff00 0%, #ffd700 50%, #ffa500 100%);
            box-shadow: 0 0 20px #ffff00, 0 0 40px #ffd700;
            animation: flicker 0.4s ease-in-out infinite alternate;
            animation-delay: 0.4s;
        }
        
        /* Chama Branca (Centro) */
        .flame-white {
            left: 50%;
            transform: translateX(-50%);
            width: 25px;
            height: 50px;
            background: radial-gradient(circle, #ffffff 0%, #ffff99 50%, #ffd700 100%);
            box-shadow: 0 0 15px #ffffff, 0 0 30px #ffff99;
            animation: flicker 0.3s ease-in-out infinite alternate;
            animation-delay: 0.1s;
        }
        
        /* Partículas de Fogo */
        .fire-particle {
            position: absolute;
            bottom: 0;
            border-radius: 50%;
            animation: particle-rise-high linear infinite;
            pointer-events: none;
            z-index: 5;
            opacity: 1;
        }
        
        /* Animação das Partículas */
        @keyframes particle-rise-high {
            0% {
                bottom: 0px;
                opacity: 1;
                transform: translateX(0) scale(1);
            }
            10% {
                bottom: 50px;
                opacity: 1;
                transform: translateX(calc(var(--random-x, 0) * 0.2)) scale(0.95);
            }
            25% {
                bottom: 150px;
                opacity: 0.9;
                transform: translateX(calc(var(--random-x, 0) * 0.5)) scale(0.85);
            }
            40% {
                bottom: 250px;
                opacity: 0.7;
                transform: translateX(calc(var(--random-x, 0) * 0.7)) scale(0.7);
            }
            60% {
                bottom: 400px;
                opacity: 0.6;
                transform: translateX(var(--random-x, 0)) scale(0.6);
            }
            80% {
                bottom: 600px;
                opacity: 0.3;
                transform: translateX(calc(var(--random-x, 0) * 1.2)) scale(0.4);
            }
            100% {
                bottom: 800px;
                opacity: 0;
                transform: translateX(calc(var(--random-x, 0) * 1.5)) scale(0.1);
            }
        }
        
        /* Estilos das Partículas */
        .fire-particle.small {
            width: 4px;
            height: 4px;
            background: radial-gradient(circle, #ff6347 0%, #ff4500 100%);
            box-shadow: 0 0 8px #ff6347;
        }
        
        .fire-particle.medium {
            width: 6px;
            height: 6px;
            background: radial-gradient(circle, #ffa500 0%, #ff6347 100%);
            box-shadow: 0 0 10px #ffa500;
        }
        
        .fire-particle.large {
            width: 8px;
            height: 8px;
            background: radial-gradient(circle, #ffff00 0%, #ffa500 100%);
            box-shadow: 0 0 12px #ffff00;
        }
        
        /* Configuração das Partículas */
        .fire-particle:nth-child(1) { 
            left: 5%; 
            animation-delay: 0.2s; 
            animation-duration: 4.5s;
            --random-x: -12px;
        }
        .fire-particle:nth-child(2) { 
            left: 15%; 
            animation-delay: 0.7s; 
            animation-duration: 4.8s;
            --random-x: 18px;
        }
        .fire-particle:nth-child(3) { 
            left: 25%; 
            animation-delay: 1.2s; 
            animation-duration: 4.2s;
            --random-x: -8px;
        }
        .fire-particle:nth-child(4) { 
            left: 35%; 
            animation-delay: 1.7s; 
            animation-duration: 5.1s;
            --random-x: 14px;
        }
        .fire-particle:nth-child(5) { 
            left: 10%; 
            animation-delay: 0s; 
            animation-duration: 5.0s;
            --random-x: -20px;
        }
        .fire-particle:nth-child(6) { 
            left: 20%; 
            animation-delay: 0.5s; 
            animation-duration: 4.8s;
            --random-x: 25px;
        }
        .fire-particle:nth-child(7) { 
            left: 30%; 
            animation-delay: 1.0s; 
            animation-duration: 5.2s;
            --random-x: -15px;
        }
        .fire-particle:nth-child(8) { 
            left: 40%; 
            animation-delay: 1.5s; 
            animation-duration: 4.6s;
            --random-x: 18px;
        }
        .fire-particle:nth-child(9) { 
            left: 50%; 
            animation-delay: 2.0s; 
            animation-duration: 5.1s;
            --random-x: -22px;
        }
        .fire-particle:nth-child(10) { 
            left: 60%; 
            animation-delay: 2.5s; 
            animation-duration: 4.9s;
            --random-x: 16px;
        }
        .fire-particle:nth-child(11) { 
            left: 70%; 
            animation-delay: 3.0s; 
            animation-duration: 5.3s;
            --random-x: -18px;
        }
        .fire-particle:nth-child(12) { 
            left: 80%; 
            animation-delay: 3.5s; 
            animation-duration: 4.7s;
            --random-x: 24px;
        }
        .fire-particle:nth-child(13) { 
            left: 90%; 
            animation-delay: 4.0s; 
            animation-duration: 5.0s;
            --random-x: -14px;
        }
        .fire-particle:nth-child(14) { 
            left: 45%; 
            animation-delay: 0.8s; 
            animation-duration: 4.4s;
            --random-x: -10px;
        }
        .fire-particle:nth-child(15) { 
            left: 55%; 
            animation-delay: 1.3s; 
            animation-duration: 4.9s;
            --random-x: 20px;
        }
        .fire-particle:nth-child(16) { 
            left: 65%; 
            animation-delay: 1.8s; 
            animation-duration: 4.3s;
            --random-x: -16px;
        }
        .fire-particle:nth-child(17) { 
            left: 75%; 
            animation-delay: 2.3s; 
            animation-duration: 5.2s;
            --random-x: 12px;
        }
        .fire-particle:nth-child(18) { 
            left: 85%; 
            animation-delay: 2.8s; 
            animation-duration: 4.6s;
            --random-x: -19px;
        }
        .fire-particle:nth-child(19) { 
            left: 95%; 
            animation-delay: 3.3s; 
            animation-duration: 4.8s;
            --random-x: 15px;
        }
        .fire-particle:nth-child(20) { 
            left: 12%; 
            animation-delay: 0.3s; 
            animation-duration: 5.0s;
            --random-x: -13px;
        }

        /* Responsividade melhorada para logo */
        @media screen and (max-width: 768px) {
            .logo-fire-container {
                height: 240px;
                max-width: 350px;
            }
            
            .fire-logo {
                max-width: 180px;
            }
            
            .fire-container {
                width: 250px;
                height: 150px;
                bottom: -20px;
            }
        }

        @media screen and (max-width: 480px) {
            .logo-fire-container {
                height: 200px;
                max-width: 300px;
                margin: 1rem auto;
            }
            
            .fire-logo {
                max-width: 150px;
            }
            
            .fire-container {
                width: 200px;
                height: 120px;
                bottom: -15px;
            }
            
            .flame-red {
                width: 60px;
                height: 90px;
            }
            
            .flame-orange {
                width: 45px;
                height: 70px;
            }
            
            .flame-yellow {
                width: 30px;
                height: 50px;
            }
            
            .flame-white {
                width: 20px;
                height: 35px;
            }
        }

        /* Títulos H2 */
        h2 {
            color: #f1f5f9;
            font-size: 1.4rem;
            font-weight: 600;
            margin-top: 2.5rem;
            margin-bottom: 1.5rem;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }

        /* Metric cards melhorados */
        .stMetric {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            padding: 1.5rem;
            border-radius: 1rem;
            margin-bottom: 1.5rem;
            border: 1px solid #475569;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .stMetric:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
        }

        .stMetric > label {
            color: #cbd5e1;
            font-size: 0.95rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }

        .stMetric > div[data-testid="stMetricValue"] {
            color: #f8fafc;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.2;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }

        .stMetric > div[data-testid="stMetricDelta"] {
            font-size: 0.85rem;
            color: #94a3b8;
            font-weight: 500;
        }

        /* Monthly summary melhorado */
        .monthly-summary-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid #374151;
            transition: background-color 0.2s ease;
        }

        .monthly-summary-item:hover {
            background-color: rgba(55, 65, 81, 0.3);
            border-radius: 0.5rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }

        .monthly-summary-item:last-child {
            border-bottom: none;
        }

        .monthly-summary-month {
            color: #e2e8f0;
            font-weight: 600;
            font-size: 1rem;
        }

        .monthly-summary-value {
            color: #f8fafc;
            font-weight: 700;
            font-size: 1.1rem;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }

        /* Chart containers melhorados */
        .stAltairChart {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            padding: 1.5rem;
            border-radius: 1rem;
            margin-top: 1.5rem;
            border: 1px solid #475569;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease;
        }

        .stAltairChart:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }

        /* Tabela melhorada */
        .stDataFrame {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border-radius: 1rem;
            border: 1px solid #475569;
            margin-top: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .stDataFrame thead th {
            background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
            color: #f8fafc;
            font-weight: 600;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }

        .stDataFrame tbody tr:nth-child(even) {
            background-color: rgba(30, 41, 59, 0.5);
        }

        .stDataFrame tbody tr:nth-child(odd) {
            background-color: rgba(51, 65, 85, 0.3);
        }

        .stDataFrame tbody tr:hover {
            background-color: rgba(71, 85, 105, 0.4);
        }

        .stDataFrame tbody td {
            color: #e2e8f0;
            font-weight: 500;
        }

        /* Selectbox melhorado */
        .stSelectbox > div > div {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border: 1px solid #475569;
            border-radius: 0.75rem;
            color: #f8fafc;
        }

    </style>
    """, unsafe_allow_html=True)

inject_enhanced_mobile_css()

# --- Funções de Cache e Acesso ao Google Sheets ---
@st.cache_resource
def get_google_auth():
    """Autoriza o acesso ao Google Sheets."""
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    try:
        if "google_credentials" in st.secrets:
            credentials_dict = st.secrets["google_credentials"]
            if credentials_dict:
                creds = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
                return gspread.authorize(creds)
            else:
                st.warning("Credenciais do Google em st.secrets estão vazias. Tentando carregar de 'credentials.json'.")
        try:
            creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
            return gspread.authorize(creds)
        except FileNotFoundError:
            st.error("Erro: Arquivo 'credentials.json' não encontrado E credenciais não configuradas em st.secrets.")
            st.info("Configure suas credenciais em .streamlit/secrets.toml ou coloque credentials.json na raiz.")
            return None
        except Exception as e_file:
            st.error(f"Erro ao carregar 'credentials.json': {e_file}")
            return None
    except Exception as e_auth:
        st.error(f"Erro geral de autenticação com Google: {e_auth}")
        return None

@st.cache_data(ttl=600)
def read_sales_data(_gc):
    """Lê e processa os dados da planilha."""
    if not _gc:
        return pd.DataFrame()
    try:
        spreadsheet = _gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        rows = worksheet.get_all_records()
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        
        # Processamento e limpeza
        for col in ["Cartão", "Dinheiro", "Pix"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            else:
                df[col] = 0

        if "Data" not in df.columns:
            st.error("Coluna 'Data' não encontrada na planilha!")
            return pd.DataFrame()

        try:
            df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
            if df["Data"].isnull().any():
                df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        except Exception:
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

        df.dropna(subset=["Data"], inplace=True)
        if df.empty:
            return pd.DataFrame()

        df["Total"] = df["Cartão"] + df["Dinheiro"] + df["Pix"]
        df["Ano"] = df["Data"].dt.year
        df["Mês"] = df["Data"].dt.month
        df["Dia"] = df["Data"].dt.day
        df["MêsNome"] = df["Mês"].apply(lambda x: meses_ordem[int(x)-1] if pd.notna(x) and 1 <= int(x) <= 12 else "Inválido")
        df["DiaSemana"] = df["Data"].dt.dayofweek

        return df.sort_values("Data")

    except SpreadsheetNotFound:
        st.error(f"Planilha com ID '{SPREADSHEET_ID}' não encontrada.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler ou processar dados da planilha: {e}")
        return pd.DataFrame()

# --- Função para criar heatmap mensal estilo GitHub ---
def create_monthly_activity_heatmap(df_month, mes_nome, ano):
    """Cria um heatmap estilo GitHub para o mês selecionado."""
    if df_month.empty or 'Data' not in df_month.columns or 'Total' not in df_month.columns:
        return None
    
    try:
        # Obter o primeiro e último dia do mês
        primeiro_dia = datetime(ano, df_month['Mês'].iloc[0], 1)
        if df_month['Mês'].iloc[0] == 12:
            ultimo_dia = datetime(ano + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = datetime(ano, df_month['Mês'].iloc[0] + 1, 1) - timedelta(days=1)
        
        # Obter o dia da semana do primeiro dia do mês (0=segunda, 6=domingo)
        first_day_weekday = primeiro_dia.weekday()
        
        # Calcular quantos dias antes do primeiro dia precisamos para começar na segunda-feira
        days_before = first_day_weekday
        
        # Criar range de datas começando na segunda-feira da semana do primeiro dia
        start_date = primeiro_dia - pd.Timedelta(days=days_before)
        
        # Garantir que terminamos no domingo da última semana
        days_after = 6 - ultimo_dia.weekday()
        if days_after < 6:
            end_date = ultimo_dia + pd.Timedelta(days=days_after)
        else:
            end_date = ultimo_dia
        
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # DataFrame com todas as datas
        full_df = pd.DataFrame({'Data': all_dates})
        
        # Marcar quais datas são do mês atual
        full_df['is_current_month'] = (
            (full_df['Data'].dt.year == ano) & 
            (full_df['Data'].dt.month == df_month['Mês'].iloc[0])
        )
        
        # Merge com dados de vendas
        cols_to_merge = ['Data', 'Total']
        if 'Cartão' in df_month.columns:
            cols_to_merge.append('Cartão')
        if 'Dinheiro' in df_month.columns:
            cols_to_merge.append('Dinheiro')
        if 'Pix' in df_month.columns:
            cols_to_merge.append('Pix')
        
        cols_present = [col for col in cols_to_merge if col in df_month.columns]
        full_df = full_df.merge(df_month[cols_present], on='Data', how='left')
        
        # Preencher NaNs
        for col in ['Total', 'Cartão', 'Dinheiro', 'Pix']:
            if col in full_df.columns:
                full_df[col] = full_df[col].fillna(0)
            else:
                full_df[col] = 0
        
        # Para dias que não são do mês atual, definir como None
        full_df['display_total'] = full_df['Total'].copy()
        mask_not_current_month = ~full_df['is_current_month']
        full_df.loc[mask_not_current_month, 'display_total'] = None

        # Mapear os nomes dos dias
        full_df['day_of_week'] = full_df['Data'].dt.weekday
        day_name_map = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
        full_df['day_display_name'] = full_df['day_of_week'].map(day_name_map)
        
        # Ordem fixa dos dias
        day_display_names = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']

        # Tooltip
        tooltip_fields = [
            alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
            alt.Tooltip('day_display_name:N', title='Dia'),
            alt.Tooltip('Total:Q', title='Total Vendas (R$)', format=',.2f')
        ]
        
        if full_df['Cartão'].sum() > 0:
            tooltip_fields.append(alt.Tooltip('Cartão:Q', title='Cartão (R$)', format=',.2f'))
        if full_df['Dinheiro'].sum() > 0:
            tooltip_fields.append(alt.Tooltip('Dinheiro:Q', title='Dinheiro (R$)', format=',.2f'))
        if full_df['Pix'].sum() > 0:
            tooltip_fields.append(alt.Tooltip('Pix:Q', title='Pix (R$)', format=',.2f'))

        # Domínio da escala baseado nos dados do mês
        max_value = full_df[full_df['is_current_month']]['Total'].max()
        if pd.isna(max_value) or max_value == 0:
            domain_values = [0.01, 500, 1000, 1500]
        else:
            domain_values = [0.01, max_value * 0.25, max_value * 0.5, max_value * 0.75]

        # Heatmap principal
        heatmap = alt.Chart(full_df).mark_rect(
            stroke='#475569',
            strokeWidth=3,
            cornerRadius=3
        ).encode(
            x=alt.X('week_corrected:O',
                    title=None, 
                    axis=alt.Axis(
                        labelColor='#cbd5e1',
                        titleColor='#f1f5f9',
                        grid=False
                    )),
            y=alt.Y('day_display_name:N', 
                    sort=day_display_names,
                    title=None,
                    axis=alt.Axis(
                        labelAngle=0, 
                        labelFontSize=11, 
                        ticks=False, 
                        domain=False, 
                        grid=False, 
                        labelColor='#cbd5e1',
                        titleColor='#f1f5f9'
                    )),
            color=alt.Color('display_total:Q',
                scale=alt.Scale(
                    range=['#e5e7eb', '#bbf7d0', '#86efac', '#4ade80', '#22c55e', '#16a34a', '#15803d'],
                    type='threshold',
                    domain=domain_values
                ),
                legend=alt.Legend(
                    title=None,
                    titleColor='#f1f5f9',
                    labelColor='#cbd5e1',
                    orient='bottom'
                )),
            tooltip=tooltip_fields
        ).properties(
            height=180,
            width=450,
            title=alt.TitleParams(
                text=f'Calendário de Vendas - {mes_nome} {ano}',
                color='#f1f5f9',
                fontSize=14
            )
        )

        # Combinar gráficos
        final_chart = alt.vconcat(
            weeks_chart,
            heatmap,
            spacing=5
        ).resolve_scale(
            color='independent'
        ).configure_view(
            strokeWidth=0
        ).configure(
            background='transparent'
        )

        return final_chart
        
    except Exception as e:
        st.error(f"Erro ao criar heatmap mensal: {e}")
        return None

# --- Funções de Gráficos ---
def create_cumulative_chart_mobile(df_month):
    """Gráfico de área acumulado para o mês selecionado."""
    try:
        if df_month.empty:
            return None
        
        df_month = df_month.copy().sort_values("Dia")
        df_month["Total_Acumulado"] = df_month["Total"].cumsum()
        
        chart = alt.Chart(df_month).mark_area(
            interpolate="monotone",
            line={"color": CORES_MODO_ESCURO[0], "strokeWidth": 2},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color=CORES_MODO_ESCURO[0], offset=0), 
                    alt.GradientStop(color="#1e293b", offset=1)
                ],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X("Dia:O", 
                   axis=alt.Axis(title="Dia do Mês", labelAngle=0, labelColor="#cbd5e1", 
                                titleColor="#f1f5f9", gridColor="#475569")),
            y=alt.Y("Total_Acumulado:Q", 
                   axis=alt.Axis(title="Acumulado (R$)", labelColor="#cbd5e1", 
                                titleColor="#f1f5f9", gridColor="#475569")),
            tooltip=[
                alt.Tooltip("Data:T", title="Data", format="%d/%m/%Y"),
                alt.Tooltip("Total:Q", title="Venda Dia (R$)", format=",.2f"),
                alt.Tooltip("Total_Acumulado:Q", title="Acumulado (R$)", format=",.2f")
            ]
        ).properties(
            height=400,
            title=alt.TitleParams(text="Vendas Acumuladas do Mês", color="#f1f5f9")
        ).configure_view(
            stroke=None
        ).configure(
            background="transparent"
        )
        return chart
    except Exception as e:
        st.error(f"Erro ao criar gráfico acumulado: {e}")
        return None

def create_daily_sales_chart_mobile(df_month):
    """Gráfico de barras de vendas diárias para o mês selecionado."""
    try:
        if df_month.empty:
            return None
        
        chart = alt.Chart(df_month).mark_bar(
            color=CORES_MODO_ESCURO[1], 
            size=15,
            stroke='#f0f0f0',
            strokeWidth=2
        ).encode(
            x=alt.X("Dia:O", 
                   axis=alt.Axis(title="Dia do Mês", labelAngle=0, labelColor="#cbd5e1", 
                                titleColor="#f1f5f9", gridColor="#475569")),
            y=alt.Y("Total:Q", 
                   axis=alt.Axis(title="Venda Diária (R$)", labelColor="#cbd5e1", 
                                titleColor="#f1f5f9", gridColor="#475569")),
            tooltip=[
                alt.Tooltip("Data:T", title="Data", format="%d/%m/%Y"),
                alt.Tooltip("Total:Q", title="Venda (R$)", format=",.2f")
            ]
        ).properties(
            height=400,
            title=alt.TitleParams(text="Vendas Diárias", color="#f1f5f9")
        ).configure_view(
            stroke=None
        ).configure(
            background="transparent"
        )
        return chart
    except Exception as e:
        st.error(f"Erro ao criar gráfico de vendas diárias: {e}")
        return None

# --- Função para formatar moeda ---
def format_brl(value):
    if pd.isna(value) or not isinstance(value, (int, float)):
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

# --- Aplicação Principal ---
def main():
    # Autenticação e Leitura de Dados
    gc = get_google_auth()
    df_all = read_sales_data(gc)

    if df_all.empty:
        st.warning("Não foi possível carregar os dados da planilha ou ela está vazia.")
        return

    # --- Logo com Animação de Fogo ---
    st.markdown(f"""
    <div class="logo-fire-container">
        <img src="{LOGO_URL}" class="fire-logo" alt="Clips Burger Logo">
        <div class="fire-container">
            <div class="flame flame-red"></div>
            <div class="flame flame-orange"></div>
            <div class="flame flame-yellow"></div>
            <div class="flame flame-white"></div>
            <div class="fire-particle small"></div>
            <div class="fire-particle small"></div>
            <div class="fire-particle small"></div>
            <div class="fire-particle small"></div>
            <div class="fire-particle small"></div>
            <div class="fire-particle medium"></div>
            <div class="fire-particle medium"></div>
            <div class="fire-particle medium"></div>
            <div class="fire-particle medium"></div>
            <div class="fire-particle medium"></div>
            <div class="fire-particle large"></div>
            <div class="fire-particle large"></div>
            <div class="fire-particle large"></div>
            <div class="fire-particle large"></div>
            <div class="fire-particle large"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Filtros de Mês e Ano ---
    anos_disponiveis = sorted(df_all["Ano"].unique(), reverse=True)
    meses_disponiveis = meses_ordem

    # Valores padrão: mês e ano atuais
    ano_atual = datetime.now().year
    mes_atual_nome = meses_ordem[datetime.now().month - 1]

    try:
        default_year_index = anos_disponiveis.index(ano_atual)
    except ValueError:
        default_year_index = 0

    default_month_index = meses_disponiveis.index(mes_atual_nome)

    col_filtros1, col_filtros2 = st.columns(2)
    with col_filtros1:
        ano_selecionado = st.selectbox(
            "Ano",
            anos_disponiveis,
            index=default_year_index
        )
    with col_filtros2:
        mes_selecionado_nome = st.selectbox(
            "Mês",
            meses_disponiveis,
            index=default_month_index
        )

    mes_selecionado_num = meses_dict[mes_selecionado_nome]

    # Filtrar dados com base na seleção
    df_filtered_year = df_all[df_all["Ano"] == ano_selecionado]
    df_filtered_month = df_filtered_year[df_filtered_year["Mês"] == mes_selecionado_num]

    # --- Cálculo Vendas Semana Atual ---
    hoje = datetime.now().date()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)

    df_semana_atual = df_all[
        (df_all['Data'].dt.date >= inicio_semana) &
        (df_all['Data'].dt.date <= hoje)
    ]
    total_semana_atual = df_semana_atual["Total"].sum()

    # --- Layout do Dashboard ---

    # KPI Vendas Semana Atual (em destaque)
    st.metric(label="💰 Vendas Semana Atual (até hoje)", value=format_brl(total_semana_atual))

    # KPIs do Mês Selecionado
    st.header(f"📊 Resumo de {mes_selecionado_nome} / {ano_selecionado}")
    if not df_filtered_month.empty:
        total_month = df_filtered_month["Total"].sum()
        avg_daily_month = df_filtered_month["Total"].mean()
        days_in_data = df_filtered_month["Dia"].nunique()
    else:
        total_month = 0
        avg_daily_month = 0
        days_in_data = 0

    kpi_cols = st.columns(2)
    with kpi_cols[0]:
        st.metric(label="Faturamento no Mês", value=format_brl(total_month))
    with kpi_cols[1]:
        st.metric(label="Média Diária no Mês", value=format_brl(avg_daily_month), 
                 help=f"Baseado em {days_in_data} dias com vendas no mês.")

    # --- Resumo Mensal do Ano Selecionado ---
    st.header(f"🗓️ Faturamento Mensal ({ano_selecionado})")
    if not df_filtered_year.empty:
        monthly_revenue = df_filtered_year.groupby("Mês")["Total"].sum().reset_index()
        monthly_revenue["MêsNome"] = monthly_revenue["Mês"].apply(
            lambda x: meses_ordem[int(x)-1] if pd.notna(x) and 1 <= int(x) <= 12 else "Inválido"
        )
        monthly_revenue = monthly_revenue.set_index('Mês').reindex(range(1, 13)).reset_index()
        monthly_revenue['MêsNome'] = monthly_revenue['Mês'].apply(lambda x: meses_ordem[x-1])
        monthly_revenue['Total'] = monthly_revenue['Total'].fillna(0)

        with st.container():
             if not monthly_revenue.empty:
                 for _, row in monthly_revenue.iterrows():
                     st.markdown(f"""
                     <div class="monthly-summary-item">
                         <span class="monthly-summary-month">{row['MêsNome']}</span>
                         <span class="monthly-summary-value">{format_brl(row['Total'])}</span>
                     </div>
                     """, unsafe_allow_html=True)
             else:
                 st.markdown('<div class="monthly-summary-item"><span>Nenhum dado para o ano.</span><span></span></div>', unsafe_allow_html=True)
    else:
        st.info(f"Sem dados de vendas registrados para o ano de {ano_selecionado}.")

    # Tabela de Vendas Diárias do Mês Selecionado
    st.header(f"📋 Vendas Diárias - {mes_selecionado_nome} / {ano_selecionado}")
    if not df_filtered_month.empty:
        df_daily_table = df_filtered_month[['Data', 'Total']].copy()
        df_daily_table['Data'] = df_daily_table['Data'].dt.strftime('%d/%m/%Y')
        df_daily_table['Total'] = df_daily_table['Total'].apply(format_brl)
        df_daily_table = df_daily_table.rename(columns={'Data': 'Dia', 'Total': 'Venda Total'})
        st.dataframe(df_daily_table, use_container_width=True, hide_index=True)
    else:
        st.info(f"Sem dados de vendas diárias para {mes_selecionado_nome} de {ano_selecionado}.")

    # Gráficos do Mês Selecionado
    st.header(f"📈 Gráficos - {mes_selecionado_nome} / {ano_selecionado}")
    if not df_filtered_month.empty:
        # Verificar se há dados suficientes para gráficos
        if len(df_filtered_month) > 0:
            # Heatmap estilo GitHub mensal
            heatmap_chart = create_monthly_activity_heatmap(df_filtered_month, mes_selecionado_nome, ano_selecionado)
            if heatmap_chart:
                st.altair_chart(heatmap_chart, use_container_width=True)
            
            cumulative_chart = create_cumulative_chart_mobile(df_filtered_month)
            if cumulative_chart:
                st.altair_chart(cumulative_chart, use_container_width=True)
            else:
                st.info("Gráfico acumulado indisponível.")

            daily_chart = create_daily_sales_chart_mobile(df_filtered_month)
            if daily_chart:
                st.altair_chart(daily_chart, use_container_width=True)
            else:
                st.info("Gráfico de vendas diárias indisponível.")
        else:
            st.info("Dados insuficientes para gerar gráficos.")
    else:
        st.info(f"Sem dados de vendas registrados para {mes_selecionado_nome} de {ano_selecionado}.")

# --- Ponto de Entrada ---
if __name__ == "__main__":
    main()
