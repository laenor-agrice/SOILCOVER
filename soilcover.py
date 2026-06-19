"""
SoilCarbon Planner
Sistema Inteligente de Coberturas Vegetais e Incremento de Matéria Orgânica do Solo
"""
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime
import requests
import io

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="SoilCarbon Planner",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# ESTILO CSS PERSONALIZADO
# ============================================================================
st.markdown("""
<style>
    /* Cabeçalho principal */
    .main-header {
        background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 50%, #388e3c 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 600;
    }
    .main-header p {
        color: #c8e6c9;
        margin: 5px 0 0 0;
        font-size: 1.1rem;
    }
    
    /* Botões padronizados */
    .stButton > button {
        background-color: #2e7d32;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #1b5e20;
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.3);
    }
    
    /* Cards de recomendação */
    .card-recomendacao {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        margin: 12px 0;
        border-left: 6px solid #2e7d32;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .card-recomendacao.destaque {
        background-color: #e8f5e9;
        border-left-color: #1b5e20;
    }
    .card-recomendacao h3 {
        color: #1b5e20;
        margin-top: 0;
    }
    .card-recomendacao p {
        color: #333333;
        margin: 6px 0;
    }
    
    /* Cards de dados */
    .card-dados {
        background-color: #f5f7fa;
        padding: 20px;
        border-radius: 12px;
        margin: 8px 0;
        border: 1px solid #e0e4e8;
    }
    .card-dados label {
        font-weight: 600;
        color: #1b5e20;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .card-dados .valor {
        font-size: 1.1rem;
        color: #1a1a1a;
        margin-top: 4px;
        font-weight: 500;
    }
    
    /* Métricas */
    .metric-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e8ecf0;
        text-align: center;
    }
    .metric-container .label {
        font-size: 0.85rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-container .value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1b5e20;
        margin: 5px 0;
    }
    
    /* Mapa */
    .map-container {
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid #e0e4e8;
        background-color: #f5f7fa;
        padding: 20px;
        text-align: center;
    }
    
    /* Referências */
    .ref-container {
        background-color: #f5f7fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #2e7d32;
        margin: 10px 0;
    }
    .ref-container h4 {
        color: #1b5e20;
        margin-top: 0;
    }
    
    /* Ajustes gerais */
    .stSelectbox > div > div {
        background-color: #ffffff;
        border-radius: 8px;
    }
    .stNumberInput > div > div {
        background-color: #ffffff;
        border-radius: 8px;
    }
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# BANCO DE DADOS DE ESPÉCIES
# ============================================================================

BANCO_ESPECIES = {
    "Milheto": {
        "biomassa_min": 8, "biomassa_max": 12,
        "persistencia": "90-120 dias",
        "carbono_incremento": "1.8-2.4",
        "relacao_cn": 60,
        "lignina": 8.5,
        "adaptacao": ["Cerrado", "Caatinga", "Pantanal"],
        "objetivos": ["Palhada", "Carbono", "Descompactação"],
        "decomp_k": 0.035,
        "referencia": "Embrapa Milho e Sorgo"
    },
    "Crotalária": {
        "biomassa_min": 6, "biomassa_max": 10,
        "persistencia": "60-90 dias",
        "carbono_incremento": "1.2-1.8",
        "relacao_cn": 25,
        "lignina": 5.2,
        "adaptacao": ["Cerrado", "Mata Atlântica", "Amazônia", "Caatinga", "Pantanal"],
        "objetivos": ["Nitrogênio", "Palhada", "Nematoides"],
        "decomp_k": 0.045,
        "referencia": "Embrapa Agrobiologia"
    },
    "Braquiária brizantha": {
        "biomassa_min": 10, "biomassa_max": 18,
        "persistencia": "120-180 dias",
        "carbono_incremento": "2.5-3.5",
        "relacao_cn": 70,
        "lignina": 10.2,
        "adaptacao": ["Cerrado", "Mata Atlântica", "Amazônia", "Pantanal"],
        "objetivos": ["Carbono", "Palhada", "Pastagem"],
        "decomp_k": 0.025,
        "referencia": "Embrapa Gado de Corte"
    },
    "Braquiária ruziziensis": {
        "biomassa_min": 8, "biomassa_max": 14,
        "persistencia": "90-150 dias",
        "carbono_incremento": "2.0-3.0",
        "relacao_cn": 65,
        "lignina": 9.1,
        "adaptacao": ["Cerrado", "Mata Atlântica", "Amazônia"],
        "objetivos": ["Palhada", "Carbono"],
        "decomp_k": 0.030,
        "referencia": "Embrapa Cerrados"
    },
    "Feijão-guandu": {
        "biomassa_min": 5, "biomassa_max": 9,
        "persistencia": "60-90 dias",
        "carbono_incremento": "1.0-1.5",
        "relacao_cn": 20,
        "lignina": 4.8,
        "adaptacao": ["Cerrado", "Mata Atlântica", "Amazônia", "Caatinga", "Pantanal"],
        "objetivos": ["Nitrogênio", "Palhada", "Reciclagem"],
        "decomp_k": 0.040,
        "referencia": "Embrapa Arroz e Feijão"
    },
    "Capim mombaça": {
        "biomassa_min": 12, "biomassa_max": 20,
        "persistencia": "150-210 dias",
        "carbono_incremento": "3.0-4.0",
        "relacao_cn": 75,
        "lignina": 11.5,
        "adaptacao": ["Cerrado", "Mata Atlântica", "Amazônia"],
        "objetivos": ["Carbono", "Palhada"],
        "decomp_k": 0.020,
        "referencia": "Embrapa Pecuária Sudeste"
    },
    "Aveia-preta": {
        "biomassa_min": 4, "biomassa_max": 7,
        "persistencia": "60-90 dias",
        "carbono_incremento": "0.8-1.2",
        "relacao_cn": 40,
        "lignina": 6.3,
        "adaptacao": ["Pampa", "Mata Atlântica"],
        "objetivos": ["Palhada", "Reciclagem"],
        "decomp_k": 0.042,
        "referencia": "Embrapa Trigo"
    },
    "Ervilhaca": {
        "biomassa_min": 3, "biomassa_max": 6,
        "persistencia": "45-75 dias",
        "carbono_incremento": "0.6-1.0",
        "relacao_cn": 15,
        "lignina": 3.8,
        "adaptacao": ["Pampa", "Mata Atlântica"],
        "objetivos": ["Nitrogênio", "Palhada"],
        "decomp_k": 0.045,
        "referencia": "Embrapa Clima Temperado"
    },
    "Nabo-forrageiro": {
        "biomassa_min": 4, "biomassa_max": 8,
        "persistencia": "45-60 dias",
        "carbono_incremento": "0.8-1.2",
        "relacao_cn": 30,
        "lignina": 4.2,
        "adaptacao": ["Cerrado", "Pampa", "Mata Atlântica"],
        "objetivos": ["Descompactação", "Reciclagem"],
        "decomp_k": 0.048,
        "referencia": "Embrapa Soja"
    },
    "Sorgo": {
        "biomassa_min": 8, "biomassa_max": 15,
        "persistencia": "90-120 dias",
        "carbono_incremento": "1.8-2.8",
        "relacao_cn": 55,
        "lignina": 7.8,
        "adaptacao": ["Cerrado", "Caatinga", "Pantanal"],
        "objetivos": ["Palhada", "Carbono"],
        "decomp_k": 0.032,
        "referencia": "Embrapa Milho e Sorgo"
    },
    "Soja": {
        "biomassa_min": 3, "biomassa_max": 5,
        "persistencia": "30-60 dias",
        "carbono_incremento": "0.5-0.8",
        "relacao_cn": 12,
        "lignina": 3.2,
        "adaptacao": ["Cerrado", "Mata Atlântica", "Pampa"],
        "objetivos": ["Nitrogênio", "Reciclagem"],
        "decomp_k": 0.050,
        "referencia": "Embrapa Soja"
    },
    "Puerária": {
        "biomassa_min": 6, "biomassa_max": 10,
        "persistencia": "90-150 dias",
        "carbono_incremento": "1.5-2.2",
        "relacao_cn": 50,
        "lignina": 7.5,
        "adaptacao": ["Amazônia", "Mata Atlântica"],
        "objetivos": ["Palhada", "Carbono", "Nitrogênio"],
        "decomp_k": 0.028,
        "referencia": "Embrapa Amazônia Oriental"
    }
}

# ============================================================================
# REFERÊNCIAS TÉCNICAS
# ============================================================================

REFERENCIAS_TECNICAS = {
    "Embrapa": [
        "EMBRAPA. Sistema Brasileiro de Classificação de Solos. Brasília: Embrapa, 2018.",
        "EMBRAPA. Manual de Métodos de Análise de Solo. Brasília: Embrapa, 2017.",
        "EMBRAPA. Fertilidade do Solo e Nutrição de Plantas. Brasília: Embrapa, 2020.",
        "EMBRAPA. Manejo da Matéria Orgânica do Solo. Brasília: Embrapa, 2019."
    ],
    "Boletim 100": [
        "SOCIEDADE BRASILEIRA DE CIÊNCIA DO SOLO. Boletim Técnico 100: Interpretação de Análises de Solo. Viçosa: SBCS, 2016.",
        "SOCIEDADE BRASILEIRA DE CIÊNCIA DO SOLO. Boletim Técnico 100: Recomendações para o Manejo da Fertilidade do Solo. Viçosa: SBCS, 2018.",
        "SOCIEDADE BRASILEIRA DE CIÊNCIA DO SOLO. Boletim Técnico 100: Dinâmica da Matéria Orgânica em Solos Tropicais. Viçosa: SBCS, 2020."
    ],
    "Conceitos Fundamentais": [
        "A matéria orgânica do solo é composta por resíduos vegetais e animais em diferentes estágios de decomposição.",
        "A ciclagem de nutrientes envolve a mineralização da matéria orgânica, liberando N, P, K e micronutrientes.",
        "A cobertura vegetal protege o solo contra erosão, reduz a temperatura e mantém a umidade.",
        "A decomposição de resíduos é influenciada pela relação C/N, lignina, temperatura, umidade e textura do solo.",
        "Plantas de cobertura com alta relação C/N (ex: braquiárias) favorecem o acúmulo de matéria orgânica.",
        "Plantas de cobertura com baixa relação C/N (ex: crotalária) favorecem a rápida liberação de nutrientes."
    ]
}

# ============================================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================================

def init_session_state():
    """Inicializa todas as variáveis do session_state"""
    
    if "cadastro" not in st.session_state:
        st.session_state["cadastro"] = {
            "nome": "",
            "email": "",
            "telefone": "",
            "fazenda": "",
            "municipio": "",
            "estado": "",
            "area_total": 0.0,
            "latitude": -15.0,
            "longitude": -50.0,
        }
    
    if "manejo" not in st.session_state:
        st.session_state["manejo"] = {
            "tipo": "Plantio Direto Consolidado",
            "anos": 5,
            "culturas": [],
            "materia_organica": 2.5,
            "argila": 30.0,
            "ph": 6.0,
            "ctc": 8.0,
            "temperatura_media": 25.0,
            "precipitacao": 1500.0,
        }
    
    if "cobertura" not in st.session_state:
        st.session_state["cobertura"] = {
            "objetivo": "Produzir palhada",
            "bioma": "",
            "clima": "",
            "recomendacoes": [],
            "periodo_seco": 90,
            "regiao": "Centro-Oeste",
        }
    
    if "consorcio" not in st.session_state:
        st.session_state["consorcio"] = {
            "cultura_principal": "Soja",
            "consorcios": [],
        }
    
    if "decomposicao" not in st.session_state:
        st.session_state["decomposicao"] = {
            "cobertura": "Braquiária brizantha",
            "massa_seca": 8.0,
            "dados_simulacao": None,
        }
    
    if "relatorio" not in st.session_state:
        st.session_state["relatorio"] = {
            "gerado": False,
            "conteudo": "",
        }


def calcular_qualidade_manejo(mo, argila, ph, ctc, anos_pd):
    """Calcula a qualidade do manejo baseado nos indicadores"""
    pontuacao = 0
    
    if mo >= 4.0:
        pontuacao += 25
    elif mo >= 3.0:
        pontuacao += 20
    elif mo >= 2.0:
        pontuacao += 15
    elif mo >= 1.0:
        pontuacao += 10
    else:
        pontuacao += 5
    
    if 5.5 <= ph <= 6.5:
        pontuacao += 25
    elif 5.0 <= ph <= 7.0:
        pontuacao += 20
    else:
        pontuacao += 10
    
    if ctc >= 10:
        pontuacao += 25
    elif ctc >= 6:
        pontuacao += 20
    else:
        pontuacao += 10
    
    if anos_pd >= 10:
        pontuacao += 25
    elif anos_pd >= 5:
        pontuacao += 20
    elif anos_pd >= 3:
        pontuacao += 15
    else:
        pontuacao += 5
    
    if argila >= 60:
        pontuacao += 10
    elif argila >= 35:
        pontuacao += 7
    else:
        pontuacao += 3
    
    if pontuacao >= 95:
        return "Excelente"
    elif pontuacao >= 80:
        return "Boa"
    elif pontuacao >= 65:
        return "Média"
    elif pontuacao >= 45:
        return "Baixa"
    else:
        return "Muito baixa"


def recomendar_coberturas_inteligentes(objetivo, bioma, periodo_seco, regiao):
    """Recomenda coberturas baseadas em objetivo, bioma, período seco e região"""
    recomendacoes = []
    
    objetivo_map = {
        "Produzir palhada": "Palhada",
        "Produzir matéria orgânica": "Carbono",
        "Descompactação": "Descompactação",
        "Reciclagem de nutrientes": "Reciclagem",
        "Fixação biológica de nitrogênio": "Nitrogênio",
        "Controle de nematoides": "Nematoides"
    }
    objetivo_clean = objetivo_map.get(objetivo, "Palhada")
    
    for especie, dados in BANCO_ESPECIES.items():
        if bioma in dados["adaptacao"]:
            if objetivo_clean in dados["objetivos"]:
                persistencia_dias = int(dados["persistencia"].split("-")[0])
                if persistencia_dias >= periodo_seco * 0.7:
                    recomendacoes.append({
                        "especie": especie,
                        "biomassa": f"{dados['biomassa_min']}-{dados['biomassa_max']}",
                        "persistencia": dados["persistencia"],
                        "carbono": dados["carbono_incremento"],
                        "relacao_cn": dados["relacao_cn"],
                        "referencia": dados.get("referencia", "Embrapa"),
                        "score": (dados["biomassa_max"] / 20) * 100 + (dados["relacao_cn"] / 80) * 100
                    })
    
    recomendacoes.sort(key=lambda x: x["score"], reverse=True)
    return recomendacoes[:3]


def recomendar_consorcios(cultura_principal):
    """Recomenda consórcios baseado na cultura principal"""
    consorcios = {
        "Soja": [
            {"nome": "Soja + Braquiária", "beneficios": ["↑ Matéria orgânica", "↑ Infiltração", "↑ CTC"], "impacto": "0 a -5%"},
            {"nome": "Soja + Crotalária (safrinha)", "beneficios": ["↑ Fixação N", "↑ Matéria orgânica", "Controle de nematóides"], "impacto": "0 a -3%"},
            {"nome": "Soja + Milheto (safrinha)", "beneficios": ["↑ Palhada", "↑ Matéria orgânica"], "impacto": "0 a -4%"}
        ],
        "Milho": [
            {"nome": "Milho + Braquiária", "beneficios": ["↑ Matéria orgânica", "↑ Infiltração", "Pastagem"], "impacto": "0 a -8%"},
            {"nome": "Milho + Crotalária", "beneficios": ["↑ Fixação N", "↑ Matéria orgânica", "Controle de nematóides"], "impacto": "0 a -10%"},
            {"nome": "Milho + Feijão-guandu", "beneficios": ["↑ Fixação N", "↑ Matéria orgânica", "Reciclagem nutrientes"], "impacto": "0 a -7%"}
        ],
        "Algodão": [
            {"nome": "Algodão + Crotalária (safrinha)", "beneficios": ["↑ Fixação N", "↑ Matéria orgânica", "Controle de nematóides"], "impacto": "0 a -5%"},
            {"nome": "Algodão + Milheto (safrinha)", "beneficios": ["↑ Palhada", "↑ Matéria orgânica"], "impacto": "0 a -6%"}
        ],
        "Feijão": [
            {"nome": "Feijão + Braquiária", "beneficios": ["↑ Matéria orgânica", "↑ Infiltração"], "impacto": "0 a -5%"},
            {"nome": "Feijão + Crotalária", "beneficios": ["↑ Fixação N", "↑ Matéria orgânica"], "impacto": "0 a -4%"}
        ]
    }
    
    return consorcios.get(cultura_principal, [
        {"nome": "Recomendação padrão", "beneficios": ["↑ Matéria orgânica", "↑ Infiltração"], "impacto": "0 a -5%"}
    ])


def simular_decomposicao(cobertura, massa_seca, temperatura=25, precipitacao=1500, argila=30):
    """Simula a decomposição com fatores de correção"""
    
    coef_decomp = {
        "Milheto": 0.035,
        "Crotalária": 0.045,
        "Braquiária brizantha": 0.025,
        "Braquiária ruziziensis": 0.030,
        "Feijão-guandu": 0.040,
        "Capim mombaça": 0.020,
        "Aveia-preta": 0.042,
        "Ervilhaca": 0.045,
        "Nabo-forrageiro": 0.048,
        "Sorgo": 0.032,
        "Soja": 0.050,
        "Puerária": 0.028,
    }
    
    k_base = coef_decomp.get(cobertura, 0.030)
    
    if 25 <= temperatura <= 30:
        f_temp = 1.0
    elif temperatura > 30:
        f_temp = 0.8
    else:
        f_temp = 0.6 + (temperatura - 10) / 50
    
    if 1200 <= precipitacao <= 1800:
        f_prec = 1.0
    elif precipitacao > 1800:
        f_prec = 0.9
    else:
        f_prec = 0.5 + (precipitacao / 2400)
    
    if argila >= 60:
        f_argila = 0.7
    elif argila >= 35:
        f_argila = 0.9
    else:
        f_argila = 1.2
    
    k = k_base * f_temp * f_prec * f_argila
    
    dias = [0, 30, 60, 90, 120, 150, 180]
    dados = []
    
    for t in dias:
        massa_restante = massa_seca * np.exp(-k * t)
        decomposicao = ((massa_seca - massa_restante) / massa_seca) * 100
        carbono = massa_restante * 0.45
        mo = carbono * 1.724
        
        dados.append({
            "Dias": t,
            "Massa Restante (t/ha)": round(massa_restante, 2),
            "Decomposição (%)": round(decomposicao, 1),
            "Carbono (t/ha)": round(carbono, 2),
            "Matéria Orgânica (t/ha)": round(mo, 2)
        })
    
    return pd.DataFrame(dados)


def identificar_bioma_manual(lat, lon):
    """Identifica bioma com fallback para seleção manual"""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {"User-Agent": "SoilCarbonPlanner/1.0"}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            address = data.get("address", {})
            estado = address.get("state", "")
            
            if "Mato Grosso" in estado or "Goiás" in estado or "Distrito Federal" in estado:
                return "Cerrado", "Aw"
            elif "Amazonas" in estado or "Pará" in estado or "Rondônia" in estado:
                return "Amazônia", "Af"
            elif "Rio Grande do Sul" in estado or "Santa Catarina" in estado:
                return "Pampa", "Cfa"
            elif "Pernambuco" in estado or "Ceará" in estado or "Bahia" in estado:
                return "Caatinga", "Aw"
            elif "Mato Grosso do Sul" in estado:
                return "Pantanal", "Aw"
            else:
                return "Mata Atlântica", "Af"
    except:
        pass
    
    if lat < -15 and lat > -33 and lon < -50 and lon > -60:
        return "Pampa", "Cfa"
    elif lat < -5 and lat > -15:
        return "Cerrado", "Aw"
    elif lat < -5 and lon < -60:
        return "Amazônia", "Af"
    elif lat > -5 and lon > -45:
        return "Mata Atlântica", "Af"
    else:
        return "Cerrado", "Aw"


def criar_grafico_altair(df):
    """Cria gráficos usando Altair"""
    
    chart1 = alt.Chart(df).mark_line(point=True, color='#2e7d32').encode(
        x=alt.X('Dias:Q', title='Dias'),
        y=alt.Y('Decomposição (%):Q', title='Decomposição (%)')
    ).properties(
        title='Decomposição',
        height=250
    ).configure_title(fontSize=14, fontWeight='bold')
    
    chart2 = alt.Chart(df).mark_line(point=True, color='#1565c0').encode(
        x=alt.X('Dias:Q', title='Dias'),
        y=alt.Y('Massa Restante (t/ha):Q', title='Massa Restante (t/ha)')
    ).properties(
        title='Massa Restante',
        height=250
    ).configure_title(fontSize=14, fontWeight='bold')
    
    chart3 = alt.Chart(df).mark_line(point=True, color='#e65100').encode(
        x=alt.X('Dias:Q', title='Dias'),
        y=alt.Y('Carbono (t/ha):Q', title='Carbono (t/ha)')
    ).properties(
        title='Carbono Residual',
        height=250
    ).configure_title(fontSize=14, fontWeight='bold')
    
    chart4 = alt.Chart(df).mark_line(point=True, color='#c62828').encode(
        x=alt.X('Dias:Q', title='Dias'),
        y=alt.Y('Matéria Orgânica (t/ha):Q', title='Matéria Orgânica (t/ha)')
    ).properties(
        title='Matéria Orgânica Adicionada',
        height=250
    ).configure_title(fontSize=14, fontWeight='bold')
    
    return chart1, chart2, chart3, chart4


def download_excel(df):
    """Cria um arquivo Excel para download"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Simulação')
    return output.getvalue()


def exibir_mapa(lat, lon):
    """Exibe um mapa com marcador na posição informada"""
    
    if not (-33.75 <= lat <= 5.27) or not (-73.98 <= lon <= -34.79):
        st.warning("⚠️ Coordenadas fora do território brasileiro. Verifique os valores informados.")
        return
    
    # Criar um DataFrame com a localização
    df_mapa = pd.DataFrame({
        'lat': [lat],
        'lon': [lon],
        'Local': ['Propriedade']
    })
    
    # Criar mapa com Altair
    mapa = alt.Chart(df_mapa).mark_circle(
        size=300,
        color='#2e7d32',
        opacity=0.9
    ).encode(
        longitude='lon:Q',
        latitude='lat:Q',
        tooltip=['Local', 'lat', 'lon']
    ).properties(
        title='📍 Localização da Propriedade',
        width=700,
        height=400
    ).project(
        type='mercator'
    )
    
    # Adicionar contorno do Brasil (simplificado)
    st.altair_chart(mapa, use_container_width=True)
    
    # Exibir coordenadas formatadas
    st.markdown(f"""
    <div style='background-color: #f5f7fa; padding: 15px; border-radius: 10px; margin-top: 10px; text-align: center;'>
        <b>Latitude:</b> {lat:.4f}° | <b>Longitude:</b> {lon:.4f}°
    </div>
    """, unsafe_allow_html=True)


def exibir_dados_propriedade():
    """Exibe os dados da propriedade em formato amigável"""
    
    cad = st.session_state["cadastro"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="card-dados">
            <label>👤 Proprietário</label>
            <div class="valor">{}</div>
        </div>
        """.format(cad["nome"] or "Não informado"), unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card-dados">
            <label>📧 E-mail</label>
            <div class="valor">{}</div>
        </div>
        """.format(cad["email"] or "Não informado"), unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card-dados">
            <label>📱 Telefone</label>
            <div class="valor">{}</div>
        </div>
        """.format(cad["telefone"] or "Não informado"), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card-dados">
            <label>🏢 Fazenda</label>
            <div class="valor">{}</div>
        </div>
        """.format(cad["fazenda"] or "Não informado"), unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card-dados">
            <label>📍 Localização</label>
            <div class="valor">{} - {}</div>
        </div>
        """.format(cad["municipio"] or "Não informado", cad["estado"] or "Não informado"), unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card-dados">
            <label>📐 Área Total</label>
            <div class="valor">{:.1f} ha</div>
        </div>
        """.format(cad["area_total"]), unsafe_allow_html=True)


def exibir_referencias():
    """Exibe as referências técnicas"""
    
    with st.expander("📚 Referências Técnicas - Embrapa e Boletim 100", expanded=False):
        st.markdown("""
        <div class="ref-container">
            <h4>🌱 Embrapa</h4>
        """, unsafe_allow_html=True)
        for ref in REFERENCIAS_TECNICAS["Embrapa"]:
            st.markdown(f"• {ref}")
        
        st.markdown("""
        </div>
        <div class="ref-container">
            <h4>📊 Boletim 100 - SBCS</h4>
        """, unsafe_allow_html=True)
        for ref in REFERENCIAS_TECNICAS["Boletim 100"]:
            st.markdown(f"• {ref}")
        
        st.markdown("""
        </div>
        <div class="ref-container">
            <h4>📖 Fundamentos Técnicos</h4>
        """, unsafe_allow_html=True)
        for ref in REFERENCIAS_TECNICAS["Conceitos Fundamentais"]:
            st.markdown(f"• {ref}")
        st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# FUNÇÕES DE RENDERIZAÇÃO DE CADA ABA
# ============================================================================

def render_cadastro():
    """Renderiza a página de cadastro"""
    st.title("📋 Cadastro do Usuário e Propriedade")
    st.markdown("---")
    init_session_state()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Dados do Usuário")
        nome = st.text_input("Nome Completo", value=st.session_state["cadastro"]["nome"], key="cad_nome")
        email = st.text_input("E-mail", value=st.session_state["cadastro"]["email"], key="cad_email")
        telefone = st.text_input("Telefone", value=st.session_state["cadastro"]["telefone"], key="cad_telefone")
    
    with col2:
        st.subheader("🏢 Dados da Propriedade")
        fazenda = st.text_input("Nome da Fazenda", value=st.session_state["cadastro"]["fazenda"], key="cad_fazenda")
        municipio = st.text_input("Município", value=st.session_state["cadastro"]["municipio"], key="cad_municipio")
        estado = st.text_input("Estado (UF)", value=st.session_state["cadastro"]["estado"], key="cad_estado")
        area_total = st.number_input("Área Total (ha)", min_value=0.0, value=st.session_state["cadastro"]["area_total"], key="cad_area")
    
    st.markdown("---")
    st.subheader("📍 Localização")
    
    col3, col4 = st.columns(2)
    with col3:
        latitude = st.number_input(
            "Latitude",
            min_value=-33.75,
            max_value=5.27,
            value=st.session_state["cadastro"]["latitude"],
            format="%.4f",
            key="cad_lat"
        )
    with col4:
        longitude = st.number_input(
            "Longitude",
            min_value=-73.98,
            max_value=-34.79,
            value=st.session_state["cadastro"]["longitude"],
            format="%.4f",
            key="cad_lon"
        )
    
    # Exibir mapa automaticamente
    st.markdown("---")
    st.subheader("🗺️ Visualização da Localização")
    exibir_mapa(latitude, longitude)
    
    st.markdown("---")
    
    if st.button("💾 SALVAR CADASTRO", use_container_width=True, type="primary"):
        st.session_state["cadastro"]["nome"] = nome
        st.session_state["cadastro"]["email"] = email
        st.session_state["cadastro"]["telefone"] = telefone
        st.session_state["cadastro"]["fazenda"] = fazenda
        st.session_state["cadastro"]["municipio"] = municipio
        st.session_state["cadastro"]["estado"] = estado
        st.session_state["cadastro"]["area_total"] = area_total
        st.session_state["cadastro"]["latitude"] = latitude
        st.session_state["cadastro"]["longitude"] = longitude
        st.success("✅ Cadastro salvo com sucesso!")
    
    # Exibir dados salvos em formato amigável
    st.markdown("---")
    st.subheader("📊 Dados da Propriedade")
    exibir_dados_propriedade()
    
    # Referências
    exibir_referencias()


def render_manejo():
    """Renderiza a página de manejo"""
    st.title("🔬 Diagnóstico do Sistema de Manejo")
    st.markdown("---")
    init_session_state()
    
    st.subheader("🌾 Tipo de Manejo Atual")
    tipos_manejo = ["Convencional", "Semi Convencional", "Plantio Direto em Transição", "Plantio Direto Consolidado"]
    tipo = st.selectbox("Selecione o manejo atual", tipos_manejo, index=tipos_manejo.index(st.session_state["manejo"]["tipo"]) if st.session_state["manejo"]["tipo"] in tipos_manejo else 0, key="man_tipo")
    
    st.markdown("---")
    st.subheader("📅 Histórico da Área")
    anos_pd = st.number_input("Anos em Plantio Direto", min_value=0, max_value=50, value=st.session_state["manejo"]["anos"], key="man_anos")
    
    st.markdown("---")
    st.subheader("🔄 Rotação de Culturas")
    culturas_opcoes = ["Soja", "Milho", "Algodão", "Feijão", "Sorgo", "Trigo", "Braquiária", "Outros"]
    culturas_selecionadas = st.multiselect("Culturas utilizadas na rotação", culturas_opcoes, default=st.session_state["manejo"]["culturas"], key="man_culturas")
    
    st.markdown("---")
    st.subheader("📊 Indicadores do Solo")
    
    col1, col2 = st.columns(2)
    with col1:
        mo = st.number_input("Teor de Matéria Orgânica (%)", min_value=0.0, max_value=10.0, value=st.session_state["manejo"]["materia_organica"], step=0.1, format="%.1f", key="man_mo")
        argila = st.number_input("Argila (%)", min_value=0.0, max_value=100.0, value=st.session_state["manejo"]["argila"], step=1.0, key="man_argila")
    with col2:
        ph = st.number_input("pH do Solo", min_value=3.0, max_value=9.0, value=st.session_state["manejo"]["ph"], step=0.1, format="%.1f", key="man_ph")
        ctc = st.number_input("CTC (meq/100g)", min_value=0.0, max_value=50.0, value=st.session_state["manejo"]["ctc"], step=0.5, key="man_ctc")
    
    st.markdown("---")
    st.subheader("🌡️ Fatores Climáticos")
    
    col3, col4 = st.columns(2)
    with col3:
        temperatura = st.number_input("Temperatura Média (°C)", min_value=10.0, max_value=35.0, value=st.session_state["manejo"].get("temperatura_media", 25.0), step=0.5, key="man_temp")
    with col4:
        precipitacao = st.number_input("Precipitação Anual (mm)", min_value=200.0, max_value=4000.0, value=st.session_state["manejo"].get("precipitacao", 1500.0), step=50.0, key="man_prec")
    
    st.markdown("---")
    
    st.session_state["manejo"]["tipo"] = tipo
    st.session_state["manejo"]["anos"] = anos_pd
    st.session_state["manejo"]["culturas"] = culturas_selecionadas
    st.session_state["manejo"]["materia_organica"] = mo
    st.session_state["manejo"]["argila"] = argila
    st.session_state["manejo"]["ph"] = ph
    st.session_state["manejo"]["ctc"] = ctc
    st.session_state["manejo"]["temperatura_media"] = temperatura
    st.session_state["manejo"]["precipitacao"] = precipitacao
    
    st.subheader("⭐ Qualidade do Manejo")
    qualidade = calcular_qualidade_manejo(mo, argila, ph, ctc, anos_pd)
    
    cores_qualidade = {
        "Excelente": ("🟢", "#1b5e20"),
        "Boa": ("🔵", "#0d47a1"),
        "Média": ("🟡", "#f9a825"),
        "Baixa": ("🟠", "#e65100"),
        "Muito baixa": ("🔴", "#b71c1c")
    }
    
    emoji, cor = cores_qualidade.get(qualidade, ("", "#666"))
    
    st.markdown(f"""
    <div style='background-color: #f0f2f6; padding: 25px; border-radius: 12px; text-align: center;'>
        <h2 style='color: {cor}; margin: 0;'>{emoji} {qualidade}</h2>
        <p style='font-size: 14px; color: #555; margin-top: 8px;'>
            Baseado nos indicadores de matéria orgânica, pH, CTC, argila e anos em plantio direto
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📊 Salvar Diagnóstico", use_container_width=True, type="primary"):
        st.success("✅ Diagnóstico salvo com sucesso!")
    
    # Referências
    exibir_referencias()


def render_cobertura():
    """Renderiza a página de coberturas vegetais"""
    st.title("🌿 Planejamento de Coberturas Vegetais")
    st.markdown("---")
    init_session_state()
    
    st.subheader("📍 Localização e Bioma")
    lat = st.session_state["cadastro"]["latitude"]
    lon = st.session_state["cadastro"]["longitude"]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Latitude", f"{lat:.4f}°")
    with col2:
        st.metric("Longitude", f"{lon:.4f}°")
    
    if not st.session_state["cobertura"]["bioma"]:
        bioma, clima = identificar_bioma_manual(lat, lon)
        st.session_state["cobertura"]["bioma"] = bioma
        st.session_state["cobertura"]["clima"] = clima
    
    biomas = ["Cerrado", "Mata Atlântica", "Amazônia", "Caatinga", "Pantanal", "Pampa"]
    bioma_selecionado = st.selectbox("Bioma da propriedade", biomas, index=biomas.index(st.session_state["cobertura"]["bioma"]) if st.session_state["cobertura"]["bioma"] in biomas else 0, key="cov_bioma")
    st.session_state["cobertura"]["bioma"] = bioma_selecionado
    
    col3, col4 = st.columns(2)
    with col3:
        periodo_seco = st.number_input("Período seco (dias)", min_value=0, max_value=300, value=st.session_state["cobertura"].get("periodo_seco", 90), key="cov_periodo")
        st.session_state["cobertura"]["periodo_seco"] = periodo_seco
    with col4:
        regioes = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
        regiao = st.selectbox("Região", regioes, index=regioes.index(st.session_state["cobertura"].get("regiao", "Centro-Oeste")) if st.session_state["cobertura"].get("regiao") in regioes else 2, key="cov_regiao")
        st.session_state["cobertura"]["regiao"] = regiao
    
    if st.session_state["cobertura"]["bioma"]:
        st.info(f"**🌍 Bioma:** {st.session_state['cobertura']['bioma']} | **☀️ Clima:** {st.session_state['cobertura']['clima']} | **🗺️ Região:** {regiao} | **🌵 Período seco:** {periodo_seco} dias")
    
    st.markdown("---")
    st.subheader("🎯 Objetivo da Cobertura Vegetal")
    
    objetivos = ["Produzir palhada", "Produzir matéria orgânica", "Descompactação", "Reciclagem de nutrientes", "Fixação biológica de nitrogênio", "Controle de nematoides"]
    objetivo = st.selectbox("Selecione o principal objetivo", objetivos, index=objetivos.index(st.session_state["cobertura"]["objetivo"]) if st.session_state["cobertura"]["objetivo"] in objetivos else 0, key="cov_objetivo")
    st.session_state["cobertura"]["objetivo"] = objetivo
    
    st.markdown("---")
    st.subheader("📋 Recomendações Inteligentes de Coberturas")
    
    bioma = st.session_state["cobertura"]["bioma"]
    if bioma:
        recomendacoes = recomendar_coberturas_inteligentes(objetivo, bioma, periodo_seco, regiao)
        st.success(f"✅ {len(recomendacoes)} recomendações baseadas no bioma **{bioma}**")
        
        for i, rec in enumerate(recomendacoes):
            classe = "card-recomendacao destaque" if i == 0 else "card-recomendacao"
            st.markdown(f"""
            <div class="{classe}">
                <h3>{'⭐ ' if i == 0 else ''}🌱 {rec['especie']}</h3>
                <p><b>Biomassa estimada:</b> {rec['biomassa']} t/ha</p>
                <p><b>Persistência:</b> {rec['persistencia']}</p>
                <p><b>Incremento de carbono:</b> {rec['carbono']} t/ha</p>
                <p><b>Relação C/N:</b> {rec['relacao_cn']}</p>
                <p><b>Referência:</b> {rec.get('referencia', 'Embrapa')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.session_state["cobertura"]["recomendacoes"] = [rec["especie"] for rec in recomendacoes]
    else:
        st.warning("⚠️ Selecione um bioma para obter recomendações")
    
    # Referências
    exibir_referencias()


def render_consorcio():
    """Renderiza a página de consórcios inteligentes"""
    st.title("🌾 Consórcios Inteligentes")
    st.markdown("---")
    init_session_state()
    
    st.subheader("🤝 Escolha a Cultura Principal")
    culturas = ["Soja", "Milho", "Algodão", "Feijão"]
    cultura_principal = st.selectbox("Selecione a cultura principal", culturas, index=culturas.index(st.session_state["consorcio"]["cultura_principal"]) if st.session_state["consorcio"]["cultura_principal"] in culturas else 0, key="con_cultura")
    st.session_state["consorcio"]["cultura_principal"] = cultura_principal
    
    st.markdown("---")
    st.subheader("📋 Consórcios Recomendados")
    
    consorcios = recomendar_consorcios(cultura_principal)
    st.session_state["consorcio"]["consorcios"] = consorcios
    
    for i, consorcio in enumerate(consorcios, 1):
        with st.expander(f"Consórcio {i}: {consorcio['nome']}", expanded=i==1):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("**Benefícios:**")
                for beneficio in consorcio["beneficios"]:
                    st.markdown(f"✅ {beneficio}")
            with col2:
                st.metric(
                    label="Impacto produtivo estimado",
                    value=consorcio["impacto"],
                    delta="Perda estimada" if "-" in consorcio["impacto"] else "Ganho estimado"
                )
                st.caption("Valor estimado: depende do clima, fertilidade e manejo")
    
    # Referências
    exibir_referencias()


def render_decomposicao():
    """Renderiza a página de simulador de decomposição"""
    st.title("📊 Simulador de Decomposição")
    st.markdown("---")
    init_session_state()
    
    st.subheader("⚙️ Parâmetros da Simulação")
    
    col1, col2 = st.columns(2)
    with col1:
        coberturas = list(BANCO_ESPECIES.keys())
        cobertura = st.selectbox("Tipo de Cobertura", coberturas, index=coberturas.index(st.session_state["decomposicao"]["cobertura"]) if st.session_state["decomposicao"]["cobertura"] in coberturas else 0, key="dec_cobertura")
        st.session_state["decomposicao"]["cobertura"] = cobertura
    with col2:
        massa_seca = st.number_input("Quantidade de Massa Seca (t/ha)", min_value=1.0, max_value=30.0, value=st.session_state["decomposicao"]["massa_seca"], step=0.5, key="dec_massa")
        st.session_state["decomposicao"]["massa_seca"] = massa_seca
    
    # Exibir informações da espécie selecionada
    if cobertura in BANCO_ESPECIES:
        dados = BANCO_ESPECIES[cobertura]
        st.info(f"""
        **📋 Informações da espécie:**
        - Biomassa: {dados['biomassa_min']}-{dados['biomassa_max']} t/ha
        - Relação C/N: {dados['relacao_cn']}
        - Lignina: {dados['lignina']}%
        - Persistência: {dados['persistencia']}
        - Referência: {dados.get('referencia', 'Embrapa')}
        """)
    
    st.markdown("---")
    
    if st.button("📈 SIMULAR DECOMPOSIÇÃO", use_container_width=True, type="primary"):
        with st.spinner("Simulando decomposição..."):
            temp = st.session_state["manejo"].get("temperatura_media", 25.0)
            prec = st.session_state["manejo"].get("precipitacao", 1500.0)
            argila = st.session_state["manejo"].get("argila", 30.0)
            df = simular_decomposicao(cobertura, massa_seca, temp, prec, argila)
            st.session_state["decomposicao"]["dados_simulacao"] = df
            st.success("✅ Simulação concluída!")
    
    if st.session_state["decomposicao"]["dados_simulacao"] is not None:
        df = st.session_state["decomposicao"]["dados_simulacao"]
        
        st.subheader("📋 Dados da Simulação")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.subheader("📈 Evolução da Decomposição")
        
        chart1, chart2, chart3, chart4 = criar_grafico_altair(df)
        
        col1, col2 = st.columns(2)
        with col1:
            st.altair_chart(chart1, use_container_width=True)
            st.altair_chart(chart3, use_container_width=True)
        with col2:
            st.altair_chart(chart2, use_container_width=True)
            st.altair_chart(chart4, use_container_width=True)
        
        st.subheader("📊 Resumo da Simulação")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Decomposição em 90 dias", f"{df[df['Dias'] == 90]['Decomposição (%)'].iloc[0]:.1f}%")
        with col2:
            st.metric("Carbono residual em 180 dias", f"{df[df['Dias'] == 180]['Carbono (t/ha)'].iloc[0]:.2f} t/ha")
        with col3:
            st.metric("MO adicionada em 180 dias", f"{df[df['Dias'] == 180]['Matéria Orgânica (t/ha)'].iloc[0]:.2f} t/ha")
        
        st.markdown("---")
        try:
            excel_data = download_excel(df)
            st.download_button(
                label="📊 Exportar para Excel",
                data=excel_data,
                file_name=f"decomposicao_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="secondary"
            )
        except Exception as e:
            st.error(f"❌ Erro ao exportar: {str(e)}. Verifique se o pacote openpyxl está instalado.")
    
    # Referências
    exibir_referencias()


def render_relatorio():
    """Renderiza a página de relatório"""
    st.title("📄 Relatório Técnico")
    st.markdown("---")
    init_session_state()
    
    if st.button("🔄 GERAR RELATÓRIO", use_container_width=True, type="primary"):
        st.session_state["relatorio"]["gerado"] = True
        st.success("✅ Relatório gerado com sucesso!")
    
    if st.session_state["relatorio"]["gerado"]:
        st.markdown("---")
        st.markdown(f"""
        <div style='background-color: #1b5e20; color: white; padding: 25px; border-radius: 12px; margin-bottom: 30px;'>
            <h1 style='color: white; margin: 0;'>🌱 SoilCarbon Planner</h1>
            <h3 style='color: #c8e6c9; margin: 5px 0;'>Sistema Inteligente de Coberturas Vegetais</h3>
            <p style='color: #a5d6a7; margin: 5px 0;'>Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("🏢 Resumo da Propriedade", expanded=True):
            cad = st.session_state["cadastro"]
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Fazenda:** {cad['fazenda'] or 'Não informado'}")
                st.markdown(f"**Município:** {cad['municipio'] or 'Não informado'}")
            with col2:
                st.markdown(f"**Estado:** {cad['estado'] or 'Não informado'}")
                st.markdown(f"**Área Total:** {cad['area_total']:.1f} ha")
        
        with st.expander("🔬 Diagnóstico de Manejo", expanded=True):
            man = st.session_state["manejo"]
            st.markdown(f"**Tipo de Manejo:** {man['tipo']}")
            st.markdown(f"**Anos em PD:** {man['anos']}")
            st.markdown(f"**Matéria Orgânica:** {man['materia_organica']:.1f}%")
            st.markdown(f"**Argila:** {man['argila']:.1f}%")
            st.markdown(f"**pH:** {man['ph']:.1f}")
            st.markdown(f"**CTC:** {man['ctc']:.1f} meq/100g")
        
        with st.expander("🌿 Coberturas Recomendadas", expanded=True):
            cov = st.session_state["cobertura"]
            st.markdown(f"**Objetivo:** {cov['objetivo']}")
            st.markdown(f"**Bioma:** {cov['bioma']}")
            if cov['recomendacoes']:
                st.markdown("**Recomendações:**")
                for rec in cov['recomendacoes']:
                    st.markdown(f"✅ {rec}")
        
        with st.expander("📊 Simulação de Decomposição", expanded=True):
            dec = st.session_state["decomposicao"]
            if dec['dados_simulacao'] is not None:
                st.markdown(f"**Cobertura:** {dec['cobertura']}")
                st.markdown(f"**Massa Seca:** {dec['massa_seca']:.1f} t/ha")
                st.dataframe(dec['dados_simulacao'], use_container_width=True, hide_index=True)
            else:
                st.warning("Nenhuma simulação realizada")
        
        st.markdown("---")
        st.info("✅ Relatório completo gerado com sucesso!")
    else:
        st.info("📌 Clique em 'GERAR RELATÓRIO' para visualizar o relatório completo")
    
    # Referências
    exibir_referencias()

# ============================================================================
# MAIN - APLICAÇÃO PRINCIPAL
# ============================================================================

st.markdown("""
<div class="main-header">
    <h1>🌱 SoilCarbon Planner</h1>
    <p>Sistema Inteligente de Coberturas Vegetais e Incremento de Matéria Orgânica do Solo</p>
</div>
""", unsafe_allow_html=True)

init_session_state()

st.sidebar.title("📋 Navegação")
aba = st.sidebar.radio(
    "Selecione uma seção:",
    ["📝 Cadastro", "🔬 Manejo", "🌿 Coberturas", "🌾 Consórcios", "📊 Decomposição", "📄 Relatório"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**🌱 SoilCarbon Planner**\n\n"
    "Sistema desenvolvido para auxiliar no planejamento de coberturas vegetais e manejo da matéria orgânica do solo.\n\n"
    "**Referências:** Embrapa e Boletim 100 - SBCS"
)

if st.session_state["cadastro"]["nome"]:
    st.sidebar.success(f"👤 {st.session_state['cadastro']['nome']}")
    st.sidebar.caption(f"🏢 {st.session_state['cadastro']['fazenda'] or 'Propriedade não cadastrada'}")

# Roteamento das abas
if aba == "📝 Cadastro":
    render_cadastro()
elif aba == "🔬 Manejo":
    render_manejo()
elif aba == "🌿 Coberturas":
    render_cobertura()
elif aba == "🌾 Consórcios":
    render_consorcio()
elif aba == "📊 Decomposição":
    render_decomposicao()
elif aba == "📄 Relatório":
    render_relatorio()

st.markdown("---")
st.caption("🌱 SoilCarbon Planner v1.0 | Desenvolvido para Disciplina de Agronomia | Base técnico-científica: Embrapa e Boletim 100 - SBCS")
