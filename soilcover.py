"""
SoilCarbon Planner
Sistema Inteligente de Coberturas Vegetais e Incremento de Matéria Orgânica do Solo
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import requests

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
    .main-header {
        background: linear-gradient(90deg, #1b5e20 0%, #388e3c 50%, #4caf50 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        color: #c8e6c9;
        margin: 5px 0 0 0;
        font-size: 1.1rem;
    }
    .stButton > button {
        background-color: #2e7d32;
        color: white;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #1b5e20;
        color: white;
    }
    .stSelectbox > div > div {
        background-color: #f5f5f5;
    }
    .stNumberInput > div > div {
        background-color: #f5f5f5;
    }
</style>
""", unsafe_allow_html=True)

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
        }
    
    if "cobertura" not in st.session_state:
        st.session_state["cobertura"] = {
            "objetivo": "Produzir palhada",
            "bioma": "",
            "clima": "",
            "recomendacoes": [],
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
    
    if "aba_atual" not in st.session_state:
        st.session_state["aba_atual"] = "Cadastro"


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
    
    if pontuacao >= 90:
        return "Excelente"
    elif pontuacao >= 75:
        return "Boa"
    elif pontuacao >= 60:
        return "Média"
    elif pontuacao >= 40:
        return "Baixa"
    else:
        return "Muito baixa"


def recomendar_coberturas(objetivo, bioma):
    """Recomenda coberturas vegetais baseado no objetivo e bioma"""
    recomendacoes = {
        "Produzir palhada": {
            "Cerrado": ["Milheto", "Crotalária", "Braquiária ruziziensis"],
            "Mata Atlântica": ["Crotalária", "Feijão-guandu", "Braquiária"],
            "Amazônia": ["Crotalária", "Feijão-guandu", "Puerária"],
            "Pampa": ["Aveia-preta", "Ervilhaca", "Nabo-forrageiro"],
            "Caatinga": ["Crotalária", "Feijão-guandu", "Sorgo"],
            "Pantanal": ["Braquiária", "Milheto", "Crotalária"],
        },
        "Produzir matéria orgânica": {
            "Cerrado": ["Braquiária brizantha", "Capim mombaça", "Milheto"],
            "Mata Atlântica": ["Braquiária", "Crotalária", "Feijão-guandu"],
            "Amazônia": ["Braquiária brizantha", "Puerária", "Crotalária"],
            "Pampa": ["Aveia-preta", "Azevém", "Ervilhaca"],
            "Caatinga": ["Braquiária", "Sorgo", "Milheto"],
            "Pantanal": ["Braquiária brizantha", "Capim mombaça"],
        },
        "Descompactação": {
            "Cerrado": ["Crotalária", "Feijão-guandu", "Nabo-forrageiro"],
            "Mata Atlântica": ["Crotalária", "Nabo-forrageiro", "Feijão-guandu"],
            "Amazônia": ["Crotalária", "Feijão-guandu"],
            "Pampa": ["Nabo-forrageiro", "Aveia-preta"],
            "Caatinga": ["Crotalária", "Feijão-guandu"],
            "Pantanal": ["Crotalária", "Nabo-forrageiro"],
        },
        "Reciclagem de nutrientes": {
            "Cerrado": ["Crotalária", "Feijão-guandu", "Milheto"],
            "Mata Atlântica": ["Crotalária", "Feijão-guandu", "Nabo-forrageiro"],
            "Amazônia": ["Crotalária", "Feijão-guandu"],
            "Pampa": ["Ervilhaca", "Aveia-preta", "Nabo-forrageiro"],
            "Caatinga": ["Crotalária", "Feijão-guandu"],
            "Pantanal": ["Crotalária", "Feijão-guandu"],
        },
        "Fixação biológica de nitrogênio": {
            "Cerrado": ["Crotalária", "Feijão-guandu", "Soja"],
            "Mata Atlântica": ["Crotalária", "Feijão-guandu", "Ervilhaca"],
            "Amazônia": ["Crotalária", "Feijão-guandu"],
            "Pampa": ["Ervilhaca", "Tremoço", "Soja"],
            "Caatinga": ["Crotalária", "Feijão-guandu"],
            "Pantanal": ["Crotalária", "Feijão-guandu"],
        },
        "Controle de nematoides": {
            "Cerrado": ["Crotalária", "Feijão-guandu", "Milheto"],
            "Mata Atlântica": ["Crotalária", "Feijão-guandu"],
            "Amazônia": ["Crotalária", "Feijão-guandu"],
            "Pampa": ["Crotalária", "Ervilhaca"],
            "Caatinga": ["Crotalária", "Feijão-guandu"],
            "Pantanal": ["Crotalária", "Feijão-guandu"],
        },
    }
    
    if bioma not in recomendacoes.get(objetivo, {}):
        return recomendacoes.get(objetivo, {}).get("Cerrado", ["Crotalária", "Milheto", "Braquiária"])
    
    return recomendacoes.get(objetivo, {}).get(bioma, ["Crotalária", "Milheto", "Braquiária"])


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


def simular_decomposicao(cobertura, massa_seca):
    """Simula a decomposição da cobertura vegetal ao longo do tempo"""
    
    coef_decomp = {
        "Crotalária": 0.045,
        "Feijão-guandu": 0.040,
        "Milheto": 0.035,
        "Braquiária ruziziensis": 0.030,
        "Braquiária brizantha": 0.025,
        "Capim mombaça": 0.020,
        "Aveia-preta": 0.042,
        "Ervilhaca": 0.045,
        "Nabo-forrageiro": 0.048,
        "Sorgo": 0.032,
        "Soja": 0.050,
        "Puerária": 0.028,
    }
    
    k = coef_decomp.get(cobertura, 0.030)
    dias = [0, 30, 60, 90, 120, 150, 180]
    
    dados = []
    
    for t in dias:
        massa_restante = massa_seca * np.exp(-k * t)
        decomposicao = ((massa_seca - massa_restante) / massa_seca) * 100
        carbono = massa_restante * 0.45
        mo = massa_restante * 1.724
        
        dados.append({
            "Dias": t,
            "Massa Restante (t/ha)": round(massa_restante, 2),
            "Decomposição (%)": round(decomposicao, 1),
            "Carbono (t/ha)": round(carbono, 2),
            "Matéria Orgânica (t/ha)": round(mo, 2)
        })
    
    return pd.DataFrame(dados)


def identificar_bioma(lat, lon):
    """Identifica o bioma baseado nas coordenadas"""
    
    biomas_por_estado = {
        "AC": "Amazônia", "AL": "Mata Atlântica", "AP": "Amazônia",
        "AM": "Amazônia", "BA": "Mata Atlântica/Caatinga", "CE": "Caatinga",
        "DF": "Cerrado", "ES": "Mata Atlântica", "GO": "Cerrado",
        "MA": "Amazônia/Cerrado", "MT": "Cerrado/Amazônia/Pantanal",
        "MS": "Cerrado/Pantanal", "MG": "Mata Atlântica/Cerrado",
        "PA": "Amazônia", "PB": "Caatinga/Mata Atlântica",
        "PR": "Mata Atlântica", "PE": "Caatinga/Mata Atlântica",
        "PI": "Caatinga/Cerrado", "RJ": "Mata Atlântica",
        "RN": "Caatinga/Mata Atlântica", "RS": "Pampa/Mata Atlântica",
        "RO": "Amazônia", "RR": "Amazônia", "SC": "Mata Atlântica",
        "SP": "Mata Atlântica/Cerrado", "SE": "Mata Atlântica",
        "TO": "Cerrado/Amazônia",
    }
    
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {"User-Agent": "SoilCarbonPlanner/1.0"}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            address = data.get("address", {})
            estado = address.get("state", "")
            
            uf = ""
            estados_br = {
                "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
                "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
                "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
                "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
                "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
                "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
                "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins"
            }
            for sigla, nome in estados_br.items():
                if nome in estado:
                    uf = sigla
                    break
            
            if uf and uf in biomas_por_estado:
                return biomas_por_estado[uf], "Aw"
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


def criar_grafico_decomposicao(df):
    """Cria gráfico de decomposição usando Matplotlib"""
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Decomposição
    axes[0, 0].plot(df["Dias"], df["Decomposição (%)"], 'b-o', linewidth=2, markersize=8)
    axes[0, 0].set_title('Decomposição (%)', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('Dias')
    axes[0, 0].set_ylabel('Decomposição (%)')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Massa Restante
    axes[0, 1].plot(df["Dias"], df["Massa Restante (t/ha)"], 'g-o', linewidth=2, markersize=8)
    axes[0, 1].set_title('Massa Restante (t/ha)', fontsize=12, fontweight='bold')
    axes[0, 1].set_xlabel('Dias')
    axes[0, 1].set_ylabel('Massa Restante (t/ha)')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Carbono
    axes[1, 0].plot(df["Dias"], df["Carbono (t/ha)"], 'orange-o', linewidth=2, markersize=8)
    axes[1, 0].set_title('Carbono Residual (t/ha)', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('Dias')
    axes[1, 0].set_ylabel('Carbono (t/ha)')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Matéria Orgânica
    axes[1, 1].plot(df["Dias"], df["Matéria Orgânica (t/ha)"], 'r-o', linewidth=2, markersize=8)
    axes[1, 1].set_title('Matéria Orgânica Adicionada (t/ha)', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('Dias')
    axes[1, 1].set_ylabel('Matéria Orgânica (t/ha)')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


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
        
        nome = st.text_input(
            "Nome Completo",
            value=st.session_state["cadastro"]["nome"],
            key="cad_nome"
        )
        
        email = st.text_input(
            "E-mail",
            value=st.session_state["cadastro"]["email"],
            key="cad_email"
        )
        
        telefone = st.text_input(
            "Telefone",
            value=st.session_state["cadastro"]["telefone"],
            key="cad_telefone"
        )
    
    with col2:
        st.subheader("🏢 Dados da Propriedade")
        
        fazenda = st.text_input(
            "Nome da Fazenda",
            value=st.session_state["cadastro"]["fazenda"],
            key="cad_fazenda"
        )
        
        municipio = st.text_input(
            "Município",
            value=st.session_state["cadastro"]["municipio"],
            key="cad_municipio"
        )
        
        estado = st.text_input(
            "Estado (UF)",
            value=st.session_state["cadastro"]["estado"],
            key="cad_estado"
        )
        
        area_total = st.number_input(
            "Área Total (ha)",
            min_value=0.0,
            value=st.session_state["cadastro"]["area_total"],
            key="cad_area"
        )
    
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
        st.balloons()
    
    with st.expander("📊 Dados Salvos", expanded=False):
        st.json(st.session_state["cadastro"])


def render_manejo():
    """Renderiza a página de manejo"""
    
    st.title("🔬 Diagnóstico do Sistema de Manejo")
    st.markdown("---")
    
    init_session_state()
    
    st.subheader("🌾 Tipo de Manejo Atual")
    
    tipos_manejo = [
        "Convencional",
        "Semi Convencional",
        "Plantio Direto em Transição",
        "Plantio Direto Consolidado"
    ]
    
    tipo = st.selectbox(
        "Selecione o manejo atual",
        tipos_manejo,
        index=tipos_manejo.index(st.session_state["manejo"]["tipo"]) 
        if st.session_state["manejo"]["tipo"] in tipos_manejo else 0,
        key="man_tipo"
    )
    
    st.markdown("---")
    
    st.subheader("📅 Histórico da Área")
    
    anos_pd = st.number_input(
        "Anos em Plantio Direto",
        min_value=0,
        max_value=50,
        value=st.session_state["manejo"]["anos"],
        key="man_anos"
    )
    
    st.markdown("---")
    
    st.subheader("🔄 Rotação de Culturas")
    
    culturas_opcoes = [
        "Soja", "Milho", "Algodão", "Feijão", 
        "Sorgo", "Trigo", "Braquiária", "Outros"
    ]
    
    culturas_selecionadas = st.multiselect(
        "Culturas utilizadas na rotação",
        culturas_opcoes,
        default=st.session_state["manejo"]["culturas"],
        key="man_culturas"
    )
    
    st.markdown("---")
    
    st.subheader("📊 Indicadores do Solo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        mo = st.number_input(
            "Teor de Matéria Orgânica (%)",
            min_value=0.0,
            max_value=10.0,
            value=st.session_state["manejo"]["materia_organica"],
            step=0.1,
            format="%.1f",
            key="man_mo"
        )
        
        argila = st.number_input(
            "Argila (%)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state["manejo"]["argila"],
            step=1.0,
            key="man_argila"
        )
    
    with col2:
        ph = st.number_input(
            "pH do Solo",
            min_value=3.0,
            max_value=9.0,
            value=st.session_state["manejo"]["ph"],
            step=0.1,
            format="%.1f",
            key="man_ph"
        )
        
        ctc = st.number_input(
            "CTC (meq/100g)",
            min_value=0.0,
            max_value=50.0,
            value=st.session_state["manejo"]["ctc"],
            step=0.5,
            key="man_ctc"
        )
    
    st.markdown("---")
    
    st.session_state["manejo"]["tipo"] = tipo
    st.session_state["manejo"]["anos"] = anos_pd
    st.session_state["manejo"]["culturas"] = culturas_selecionadas
    st.session_state["manejo"]["materia_organica"] = mo
    st.session_state["manejo"]["argila"] = argila
    st.session_state["manejo"]["ph"] = ph
    st.session_state["manejo"]["ctc"] = ctc
    
    st.subheader("⭐ Qualidade do Manejo")
    
    qualidade = calcular_qualidade_manejo(mo, argila, ph, ctc, anos_pd)
    
    cores = {
        "Excelente": "🟢",
        "Boa": "🔵",
        "Média": "🟡",
        "Baixa": "🟠",
        "Muito baixa": "🔴"
    }
    
    st.markdown(f"""
    <div style='
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    '>
        <h2>{cores.get(qualidade, '')} {qualidade}</h2>
        <p style='font-size: 14px; color: #666;'>
            Baseado nos indicadores de matéria orgânica, pH, CTC e anos em plantio direto
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📊 Salvar Diagnóstico", use_container_width=True, type="primary"):
        st.success("✅ Diagnóstico salvo com sucesso!")


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
        st.metric("Latitude", f"{lat:.4f}")
    
    with col2:
        st.metric("Longitude", f"{lon:.4f}")
    
    if st.button("🔍 Identificar Bioma e Clima", use_container_width=True):
        with st.spinner("Identificando bioma..."):
            bioma, clima = identificar_bioma(lat, lon)
            st.session_state["cobertura"]["bioma"] = bioma
            st.session_state["cobertura"]["clima"] = clima
            st.rerun()
    
    if st.session_state["cobertura"]["bioma"]:
        st.info(f"""
        **🌍 Bioma identificado:** {st.session_state['cobertura']['bioma']}
        
        **☀️ Clima:** {st.session_state['cobertura']['clima']}
        """)
    
    st.markdown("---")
    
    st.subheader("🎯 Objetivo da Cobertura Vegetal")
    
    objetivos = [
        "Produzir palhada",
        "Produzir matéria orgânica",
        "Descompactação",
        "Reciclagem de nutrientes",
        "Fixação biológica de nitrogênio",
        "Controle de nematoides"
    ]
    
    objetivo = st.selectbox(
        "Selecione o principal objetivo",
        objetivos,
        index=objetivos.index(st.session_state["cobertura"]["objetivo"]) 
        if st.session_state["cobertura"]["objetivo"] in objetivos else 0,
        key="cov_objetivo"
    )
    
    st.session_state["cobertura"]["objetivo"] = objetivo
    
    st.markdown("---")
    
    st.subheader("📋 Recomendações de Coberturas")
    
    bioma = st.session_state["cobertura"]["bioma"]
    
    if bioma:
        recomendacoes = recomendar_coberturas(objetivo, bioma)
        
        st.success(f"✅ Recomendações baseadas no bioma **{bioma}** e objetivo **{objetivo}**")
        
        col1, col2, col3 = st.columns(3)
        
        for idx, rec in enumerate(recomendacoes[:3]):
            with [col1, col2, col3][idx]:
                st.markdown(f"""
                <div style='
                    background-color: #e8f5e9;
                    padding: 15px;
                    border-radius: 10px;
                    text-align: center;
                    margin: 5px 0;
                '>
                    <h3>🌱 {rec}</h3>
                </div>
                """, unsafe_allow_html=True)
        
        st.session_state["cobertura"]["recomendacoes"] = recomendacoes
        
        with st.expander("📖 Mais informações sobre as coberturas recomendadas"):
            info_coberturas = {
                "Crotalária": "Fixação de N, controle de nematoides, decomposição rápida",
                "Milheto": "Alta produção de biomassa, sistema radicular profundo",
                "Braquiária brizantha": "Alta produção de carbono, persistente",
                "Braquiária ruziziensis": "Boa cobertura, fácil manejo",
                "Feijão-guandu": "Fixação de N, reciclagem de nutrientes",
                "Capim mombaça": "Alta biomassa, boa cobertura",
                "Sorgo": "Tolerância à seca, boa biomassa",
                "Nabo-forrageiro": "Descompactação, reciclagem de nutrientes",
                "Aveia-preta": "Boa cobertura em regiões frias",
                "Ervilhaca": "Fixação de N, boa cobertura",
            }
            
            for cobertura in recomendacoes:
                if cobertura in info_coberturas:
                    st.markdown(f"**{cobertura}:** {info_coberturas[cobertura]}")
    else:
        st.warning("⚠️ Clique em 'Identificar Bioma' para obter recomendações personalizadas")


def render_consorcio():
    """Renderiza a página de consórcios inteligentes"""
    
    st.title("🌾 Consórcios Inteligentes")
    st.markdown("---")
    
    init_session_state()
    
    st.subheader("🤝 Escolha a Cultura Principal")
    
    culturas = ["Soja", "Milho", "Algodão", "Feijão"]
    
    cultura_principal = st.selectbox(
        "Selecione a cultura principal",
        culturas,
        index=culturas.index(st.session_state["consorcio"]["cultura_principal"]) 
        if st.session_state["consorcio"]["cultura_principal"] in culturas else 0,
        key="con_cultura"
    )
    
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
                st.caption("Valor estimado: 4 ± 3% depende do clima, fertilidade e manejo")
    
    st.markdown("---")
    
    with st.expander("💡 Dicas para consórcios bem-sucedidos"):
        st.markdown("""
        **1. Escolha da espécie de cobertura:**
        - Considere o ciclo da cultura principal
        - Avalie a competição por água e nutrientes
        - Escolha espécies com sistema radicular complementar
        
        **2. Época de semeadura:**
        - Antecedência de 10-15 dias antes da cultura principal
        - Ou semeadura simultânea em áreas com boa umidade
        
        **3. Manejo da cobertura:**
        - Manejo químico (dessecação) 7-14 dias antes do plantio
        - Roçada mecânica em áreas com alta biomassa
        
        **4. Nutrição:**
        - Ajustar adubação para suprir ambas as culturas
        - Fósforo e potássio são especialmente importantes
        """)


def render_decomposicao():
    """Renderiza a página de simulador de decomposição"""
    
    st.title("📊 Simulador de Decomposição")
    st.markdown("---")
    
    init_session_state()
    
    st.subheader("⚙️ Parâmetros da Simulação")
    
    col1, col2 = st.columns(2)
    
    with col1:
        coberturas = [
            "Crotalária",
            "Feijão-guandu",
            "Milheto",
            "Braquiária ruziziensis",
            "Braquiária brizantha",
            "Capim mombaça",
            "Aveia-preta",
            "Ervilhaca",
            "Nabo-forrageiro",
            "Sorgo",
            "Soja",
            "Puerária"
        ]
        
        cobertura = st.selectbox(
            "Tipo de Cobertura",
            coberturas,
            index=coberturas.index(st.session_state["decomposicao"]["cobertura"]) 
            if st.session_state["decomposicao"]["cobertura"] in coberturas else 0,
            key="dec_cobertura"
        )
        
        st.session_state["decomposicao"]["cobertura"] = cobertura
    
    with col2:
        massa_seca = st.number_input(
            "Quantidade de Massa Seca (t/ha)",
            min_value=1.0,
            max_value=30.0,
            value=st.session_state["decomposicao"]["massa_seca"],
            step=0.5,
            key="dec_massa"
        )
        
        st.session_state["decomposicao"]["massa_seca"] = massa_seca
    
    st.markdown("---")
    
    if st.button("📈 SIMULAR DECOMPOSIÇÃO", use_container_width=True, type="primary"):
        with st.spinner("Simulando decomposição..."):
            df = simular_decomposicao(cobertura, massa_seca)
            st.session_state["decomposicao"]["dados_simulacao"] = df
            st.success("✅ Simulação concluída!")
    
    if st.session_state["decomposicao"]["dados_simulacao"] is not None:
        df = st.session_state["decomposicao"]["dados_simulacao"]
        
        st.subheader("📋 Dados da Simulação")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.subheader("📈 Evolução da Decomposição")
        
        fig = criar_grafico_decomposicao(df)
        st.pyplot(fig)
        plt.close(fig)
        
        st.subheader("📊 Resumo da Simulação")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Decomposição em 90 dias",
                f"{df[df['Dias'] == 90]['Decomposição (%)'].iloc[0]:.1f}%"
            )
        
        with col2:
            st.metric(
                "Carbono residual em 180 dias",
                f"{df[df['Dias'] == 180]['Carbono (t/ha)'].iloc[0]:.2f} t/ha"
            )
        
        with col3:
            st.metric(
                "MO adicionada em 180 dias",
                f"{df[df['Dias'] == 180]['Matéria Orgânica (t/ha)'].iloc[0]:.2f} t/ha"
            )


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
        <div style='
            background-color: #1f4b3a;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        '>
            <h1 style='color: white;'>🌱 SoilCarbon Planner</h1>
            <h3 style='color: white;'>Sistema Inteligente de Coberturas Vegetais</h3>
            <p style='color: #c8e6c9;'>Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("🏢 Resumo da Propriedade", expanded=True):
            cad = st.session_state["cadastro"]
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Fazenda:** {cad['fazenda']}")
                st.markdown(f"**Município:** {cad['municipio']}")
                st.markdown(f"**Estado:** {cad['estado']}")
            
            with col2:
                st.markdown(f"**Área Total:** {cad['area_total']:.1f} ha")
                st.markdown(f"**Latitude:** {cad['latitude']:.4f}")
                st.markdown(f"**Longitude:** {cad['longitude']:.4f}")
        
        with st.expander("🔬 Diagnóstico de Manejo", expanded=True):
            man = st.session_state["manejo"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Tipo de Manejo:** {man['tipo']}")
                st.markdown(f"**Anos em Plantio Direto:** {man['anos']}")
                st.markdown(f"**Culturas:** {', '.join(man['culturas'])}")
            
            with col2:
                st.markdown(f"**Matéria Orgânica:** {man['materia_organica']:.1f}%")
                st.markdown(f"**Argila:** {man['argila']:.1f}%")
                st.markdown(f"**pH:** {man['ph']:.1f}")
                st.markdown(f"**CTC:** {man['ctc']:.1f} meq/100g")
        
        with st.expander("🌿 Coberturas Recomendadas", expanded=True):
            cov = st.session_state["cobertura"]
            
            st.markdown(f"**Objetivo:** {cov['objetivo']}")
            
            if cov['bioma']:
                st.markdown(f"**Bioma:** {cov['bioma']}")
            
            if cov['recomendacoes']:
                st.markdown("**Recomendações:**")
                for rec in cov['recomendacoes']:
                    st.markdown(f"✅ {rec}")
        
        with st.expander("🌾 Consórcios Recomendados", expanded=True):
            con = st.session_state["consorcio"]
            
            st.markdown(f"**Cultura Principal:** {con['cultura_principal']}")
            
            if con['consorcios']:
                for i, consorcio in enumerate(con['consorcios'], 1):
                    st.markdown(f"**{i}. {consorcio['nome']}**")
                    st.markdown(f"   Benefícios: {', '.join(consorcio['beneficios'])}")
                    st.markdown(f"   Impacto: {consorcio['impacto']}")
        
        with st.expander("📊 Simulação de Decomposição", expanded=True):
            dec = st.session_state["decomposicao"]
            
            if dec['dados_simulacao'] is not None:
                df = dec['dados_simulacao']
                
                st.markdown(f"**Cobertura:** {dec['cobertura']}")
                st.markdown(f"**Massa Seca Inicial:** {dec['massa_seca']:.1f} t/ha")
                
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("Nenhuma simulação realizada")
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Exportar PDF", use_container_width=True):
                st.info("Funcionalidade em desenvolvimento")
        
        with col2:
            if st.button("📊 Exportar Excel", use_container_width=True):
                st.info("Funcionalidade em desenvolvimento")
        
        with col3:
            if st.button("🖨️ Imprimir", use_container_width=True):
                st.info("Funcionalidade em desenvolvimento")
    else:
        st.info("📌 Clique em 'GERAR RELATÓRIO' para visualizar o relatório completo")


# ============================================================================
# MAIN - APLICAÇÃO PRINCIPAL
# ============================================================================

# Cabeçalho
st.markdown("""
<div class="main-header">
    <h1>🌱 SoilCarbon Planner</h1>
    <p>Sistema Inteligente de Coberturas Vegetais e Incremento de Matéria Orgânica do Solo</p>
</div>
""", unsafe_allow_html=True)

# Inicializa session_state
init_session_state()

# Barra lateral
st.sidebar.title("📋 Navegação")

aba = st.sidebar.radio(
    "Selecione uma seção:",
    [
        "📝 Cadastro",
        "🔬 Manejo",
        "🌿 Coberturas",
        "🌾 Consórcios",
        "📊 Decomposição",
        "📄 Relatório"
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Desenvolvido para Agronomia**

Este sistema auxilia no planejamento de 
coberturas vegetais e manejo da matéria 
orgânica do solo.
""")

st.sidebar.markdown("---")

if st.session_state["cadastro"]["nome"]:
    st.sidebar.success(f"👤 {st.session_state['cadastro']['nome']}")
    st.sidebar.caption(f"🏢 {st.session_state['cadastro']['fazenda']}")

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

# Rodapé
st.markdown("---")
st.caption("🌱 SoilCarbon Planner v1.0 | Desenvolvido para Disciplina de Agronomia")
