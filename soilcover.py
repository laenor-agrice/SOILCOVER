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
# CONFIGURAÇÕES
# ============================================================================

# Chave da API Geoapify (fixa no código)
GEOAPIFY_API_KEY = "26d9c20ff9d542ed80fbd9a63a6f50fe"  # ← Substitua pela sua chave

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
    .coordenada-input {
        font-family: monospace;
        font-size: 1.1rem;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1565c0;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3e0;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #e65100;
        margin: 10px 0;
    }
    .success-box {
        background-color: #e8f5e9;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #2e7d32;
        margin: 10px 0;
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
        "referencia": "Embrapa Milho e Sorgo",
        "clima_pref": ["Tropical", "Semiárido"],
        "tipo": "Gramínea",
        "sistema_radicular": "Fibroso",
        "fixacao_n": False
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
        "referencia": "Embrapa Agrobiologia",
        "clima_pref": ["Tropical", "Subtropical"],
        "tipo": "Leguminosa",
        "sistema_radicular": "Pivotante",
        "fixacao_n": True
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
        "referencia": "Embrapa Gado de Corte",
        "clima_pref": ["Tropical"],
        "tipo": "Gramínea",
        "sistema_radicular": "Fibroso",
        "fixacao_n": False
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
        "referencia": "Embrapa Cerrados",
        "clima_pref": ["Tropical"],
        "tipo": "Gramínea",
        "sistema_radicular": "Fibroso",
        "fixacao_n": False
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
        "referencia": "Embrapa Arroz e Feijão",
        "clima_pref": ["Tropical", "Subtropical"],
        "tipo": "Leguminosa",
        "sistema_radicular": "Pivotante",
        "fixacao_n": True
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
        "referencia": "Embrapa Pecuária Sudeste",
        "clima_pref": ["Tropical"],
        "tipo": "Gramínea",
        "sistema_radicular": "Fibroso",
        "fixacao_n": False
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
        "referencia": "Embrapa Trigo",
        "clima_pref": ["Subtropical", "Temperado"],
        "tipo": "Gramínea",
        "sistema_radicular": "Fibroso",
        "fixacao_n": False
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
        "referencia": "Embrapa Clima Temperado",
        "clima_pref": ["Subtropical", "Temperado"],
        "tipo": "Leguminosa",
        "sistema_radicular": "Fibroso",
        "fixacao_n": True
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
        "referencia": "Embrapa Soja",
        "clima_pref": ["Subtropical", "Temperado"],
        "tipo": "Crucífera",
        "sistema_radicular": "Pivotante",
        "fixacao_n": False
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
        "referencia": "Embrapa Milho e Sorgo",
        "clima_pref": ["Tropical", "Semiárido"],
        "tipo": "Gramínea",
        "sistema_radicular": "Fibroso",
        "fixacao_n": False
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
        "referencia": "Embrapa Soja",
        "clima_pref": ["Tropical", "Subtropical"],
        "tipo": "Leguminosa",
        "sistema_radicular": "Pivotante",
        "fixacao_n": True
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
        "referencia": "Embrapa Amazônia Oriental",
        "clima_pref": ["Tropical"],
        "tipo": "Leguminosa",
        "sistema_radicular": "Fibroso",
        "fixacao_n": True
    }
}

# ============================================================================
# REFERÊNCIAS TÉCNICAS (APENAS PARA O RELATÓRIO)
# ============================================================================

REFERENCIAS_TECNICAS = {
    "Embrapa": [
        "EMBRAPA. Sistema Brasileiro de Classificação de Solos. Brasília: Embrapa, 2018.",
        "EMBRAPA. Manual de Métodos de Análise de Solo. Brasília: Embrapa, 2017.",
        "EMBRAPA. Fertilidade do Solo e Nutrição de Plantas. Brasília: Embrapa, 2020.",
        "EMBRAPA. Manejo da Matéria Orgânica do Solo. Brasília: Embrapa, 2019.",
        "EMBRAPA. Plantas de Cobertura do Solo: Recomendações para o Cerrado. Brasília: Embrapa, 2021."
    ],
    "Boletim 100": [
        "SOCIEDADE BRASILEIRA DE CIÊNCIA DO SOLO. Boletim Técnico 100: Interpretação de Análises de Solo. Viçosa: SBCS, 2016.",
        "SOCIEDADE BRASILEIRA DE CIÊNCIA DO SOLO. Boletim Técnico 100: Recomendações para o Manejo da Fertilidade do Solo. Viçosa: SBCS, 2018.",
        "SOCIEDADE BRASILEIRA DE CIÊNCIA DO SOLO. Boletim Técnico 100: Dinâmica da Matéria Orgânica em Solos Tropicais. Viçosa: SBCS, 2020."
    ],
    "Normativos": [
        "BRASIL. Lei nº 12.651/2012 - Código Florestal Brasileiro.",
        "BRASIL. Instrução Normativa MAPA nº 39/2018 - Produção Integrada Agropecuária.",
        "CONAMA. Resolução nº 420/2009 - Critérios de Qualidade do Solo."
    ],
    "Metodologias": [
        "Método de determinação de matéria orgânica: Walkley-Black (Embrapa, 2017).",
        "Método de determinação de CTC: Troca Catiônica com Acetato de Amônio (SBCS, 2016).",
        "Modelo de decomposição: Equação exponencial de Stanford & Smith (1972).",
        "Classificação de biomas: IBGE (2019)."
    ]
}

# ============================================================================
# BANCO DE DADOS DE CONSÓRCIOS
# ============================================================================

CONSORCIOS_DB = {
    "Soja": {
        "opcoes": [
            {
                "nome": "Soja + Braquiária",
                "beneficios": ["↑ Matéria orgânica", "↑ Infiltração", "↑ CTC"],
                "impacto": "0 a -5%",
                "justificativa": "A braquiária produz alta biomassa e melhora a estrutura do solo.",
                "compatibilidade": "Alta",
                "tipo_consorcio": "Safra + Cobertura",
                "recomendacao": "Semeie a braquiária a lanço na dessecação da soja."
            },
            {
                "nome": "Soja + Crotalária (safrinha)",
                "beneficios": ["↑ Fixação N", "↑ Matéria orgânica", "Controle de nematóides"],
                "impacto": "0 a -3%",
                "justificativa": "Crotalária fixa nitrogênio e controla nematoides do gênero Meloidogyne.",
                "compatibilidade": "Muito Alta",
                "tipo_consorcio": "Safrinha",
                "recomendacao": "Semeie a crotalária após a colheita da soja."
            },
            {
                "nome": "Soja + Milheto (safrinha)",
                "beneficios": ["↑ Palhada", "↑ Matéria orgânica"],
                "impacto": "0 a -4%",
                "justificativa": "Milheto produz grande quantidade de palhada para o sistema plantio direto.",
                "compatibilidade": "Alta",
                "tipo_consorcio": "Safrinha",
                "recomendacao": "Semeie o milheto após a colheita da soja."
            }
        ]
    },
    "Milho": {
        "opcoes": [
            {
                "nome": "Milho + Braquiária",
                "beneficios": ["↑ Matéria orgânica", "↑ Infiltração", "Pastagem"],
                "impacto": "0 a -8%",
                "justificativa": "Sistema integrado lavoura-pecuária, a braquiária forma pastagem após a colheita.",
                "compatibilidade": "Muito Alta",
                "tipo_consorcio": "Integração Lavoura-Pecuária",
                "recomendacao": "Semeie a braquiária junto com o milho ou a lanço."
            },
            {
                "nome": "Milho + Crotalária",
                "beneficios": ["↑ Fixação N", "↑ Matéria orgânica", "Controle de nematóides"],
                "impacto": "0 a -10%",
                "justificativa": "Crotalária fornece N para o milho em sucessão e controla nematoides.",
                "compatibilidade": "Alta",
                "tipo_consorcio": "Safra + Cobertura",
                "recomendacao": "Intercale a crotalária nas entrelinhas do milho."
            },
            {
                "nome": "Milho + Feijão-guandu",
                "beneficios": ["↑ Fixação N", "↑ Matéria orgânica", "Reciclagem nutrientes"],
                "impacto": "0 a -7%",
                "justificativa": "Feijão-guandu fixa N e recicla nutrientes das camadas profundas.",
                "compatibilidade": "Alta",
                "tipo_consorcio": "Safra + Cobertura",
                "recomendacao": "Semeie o guandu a lanço na pré-colheita do milho."
            }
        ]
    },
    "Algodão": {
        "opcoes": [
            {
                "nome": "Algodão + Crotalária (safrinha)",
                "beneficios": ["↑ Fixação N", "↑ Matéria orgânica", "Controle de nematóides"],
                "impacto": "0 a -5%",
                "justificativa": "Crotalária melhora a fertilidade e controla nematoides do algodoeiro.",
                "compatibilidade": "Alta",
                "tipo_consorcio": "Safrinha",
                "recomendacao": "Semeie a crotalária após a colheita do algodão."
            },
            {
                "nome": "Algodão + Milheto (safrinha)",
                "beneficios": ["↑ Palhada", "↑ Matéria orgânica"],
                "impacto": "0 a -6%",
                "justificativa": "Milheto produz palhada para o sistema plantio direto.",
                "compatibilidade": "Alta",
                "tipo_consorcio": "Safrinha",
                "recomendacao": "Semeie o milheto após a colheita do algodão."
            }
        ]
    },
    "Feijão": {
        "opcoes": [
            {
                "nome": "Feijão + Braquiária",
                "beneficios": ["↑ Matéria orgânica", "↑ Infiltração"],
                "impacto": "0 a -5%",
                "justificativa": "Braquiária melhora a estrutura e a infiltração do solo.",
                "compatibilidade": "Alta",
                "tipo_consorcio": "Safra + Cobertura",
                "recomendacao": "Semeie a braquiária a lanço após o feijão."
            },
            {
                "nome": "Feijão + Crotalária",
                "beneficios": ["↑ Fixação N", "↑ Matéria orgânica"],
                "impacto": "0 a -4%",
                "justificativa": "Crotalária fixa N e melhora a fertilidade para a próxima safra.",
                "compatibilidade": "Muito Alta",
                "tipo_consorcio": "Safra + Cobertura",
                "recomendacao": "Intercale a crotalária nas entrelinhas do feijão."
            }
        ]
    }
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
            "sistema_produtivo": "Grãos",
            "disponibilidade_hidrica": "Média",
            "fertilidade": "Média"
        }
    
    if "cobertura" not in st.session_state:
        st.session_state["cobertura"] = {
            "objetivo": "Produzir palhada",
            "bioma": "",
            "clima": "",
            "recomendacoes": [],
            "periodo_seco": 90,
            "regiao": "Centro-Oeste",
            "tempo_permanencia": 90,
            "producao_biomassa": 8.0,
            "fixacao_n": "Não",
            "sistema_produtivo": "Grãos",
            "problema_principal": "",
            "caracteristica_desejada": "",
            "dados_salvos": False,
            "recomendacoes_geradas": False
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


def recomendar_coberturas_dinamicas(problema, caracteristica, bioma, clima, 
                                   sistema_produtivo, fertilidade, periodo_seco,
                                   temperatura, precipitacao, objetivo):
    """
    Recomenda coberturas baseada em múltiplos fatores agronômicos
    """
    recomendacoes = []
    
    # Mapeamento de objetivos para tipo de espécie
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
        score = 0
        justificativas = []
        
        # 1. Verifica bioma
        if bioma in dados["adaptacao"]:
            score += 20
            justificativas.append(f"Adaptada ao bioma {bioma}")
        
        # 2. Verifica objetivo
        if objetivo_clean in dados["objetivos"]:
            score += 25
            justificativas.append(f"Ideal para {objetivo}")
        
        # 3. Verifica clima
        if clima in dados.get("clima_pref", []):
            score += 15
            justificativas.append(f"Adaptada ao clima {clima}")
        
        # 4. Verifica persistência
        persistencia_dias = int(dados["persistencia"].split("-")[0])
        if persistencia_dias >= periodo_seco * 0.7:
            score += 10
            justificativas.append("Boa persistência no período seco")
        
        # 5. Verifica sistema produtivo
        if sistema_produtivo == "Pecuária" and "Pastagem" in dados["objetivos"]:
            score += 10
            justificativas.append("Recomendada para sistemas pecuários")
        
        if sistema_produtivo == "Integração Lavoura-Pecuária" and "Pastagem" in dados["objetivos"]:
            score += 8
            justificativas.append("Compatível com integração lavoura-pecuária")
        
        # 6. Verifica fertilidade
        if fertilidade == "Baixa" and dados["relacao_cn"] > 50:
            score += 8
            justificativas.append("Tolerante à baixa fertilidade")
        elif fertilidade == "Alta" and dados["relacao_cn"] < 40:
            score += 5
            justificativas.append("Responde bem à alta fertilidade")
        
        # 7. Verifica fixação de N
        if objetivo_clean == "Nitrogênio" and dados["fixacao_n"]:
            score += 15
            justificativas.append("Realiza fixação biológica de nitrogênio")
        
        # 8. Verifica descompactação
        if objetivo_clean == "Descompactação" and dados["sistema_radicular"] == "Pivotante":
            score += 10
            justificativas.append("Sistema radicular pivotante descompacta o solo")
        
        # 9. Verifica temperatura
        if 25 <= temperatura <= 30 and clima == "Tropical":
            if dados["clima_pref"] == ["Tropical"]:
                score += 5
                justificativas.append("Adaptada a temperaturas tropicais")
        
        # Só adiciona se tiver score mínimo
        if score >= 40:
            recomendacoes.append({
                "especie": especie,
                "biomassa": f"{dados['biomassa_min']}-{dados['biomassa_max']}",
                "persistencia": dados["persistencia"],
                "carbono": dados["carbono_incremento"],
                "relacao_cn": dados["relacao_cn"],
                "referencia": dados.get("referencia", "Embrapa"),
                "tipo": dados.get("tipo", ""),
                "sistema_radicular": dados.get("sistema_radicular", ""),
                "fixacao_n": dados.get("fixacao_n", False),
                "score": score,
                "justificativas": justificativas[:4]  # Limita a 4 justificativas
            })
    
    # Ordena por score
    recomendacoes.sort(key=lambda x: x["score"], reverse=True)
    return recomendacoes


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
                return "Cerrado", "Aw", "Tropical"
            elif "Amazonas" in estado or "Pará" in estado or "Rondônia" in estado:
                return "Amazônia", "Af", "Tropical"
            elif "Rio Grande do Sul" in estado or "Santa Catarina" in estado:
                return "Pampa", "Cfa", "Subtropical"
            elif "Pernambuco" in estado or "Ceará" in estado or "Bahia" in estado:
                return "Caatinga", "Aw", "Semiárido"
            elif "Mato Grosso do Sul" in estado:
                return "Pantanal", "Aw", "Tropical"
            else:
                return "Mata Atlântica", "Af", "Tropical"
    except:
        pass
    
    if lat < -15 and lat > -33 and lon < -50 and lon > -60:
        return "Pampa", "Cfa", "Subtropical"
    elif lat < -5 and lat > -15:
        return "Cerrado", "Aw", "Tropical"
    elif lat < -5 and lon < -60:
        return "Amazônia", "Af", "Tropical"
    elif lat > -5 and lon > -45:
        return "Mata Atlântica", "Af", "Tropical"
    else:
        return "Cerrado", "Aw", "Tropical"


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


def exibir_mapa_geoapify(lat, lon):
    """Exibe um mapa usando Geoapify com chave fixa"""
    
    if not GEOAPIFY_API_KEY or GEOAPIFY_API_KEY == "SUA_CHAVE_AQUI":
        st.warning("⚠️ Chave da API Geoapify não configurada. Substitua 'SUA_CHAVE_AQUI' no código.")
        return
    
    if not (-33.75 <= lat <= 5.27) or not (-73.98 <= lon <= -34.79):
        st.warning("⚠️ Coordenadas fora do território brasileiro. Verifique os valores informados.")
        return
    
    try:
        map_url = f"https://maps.geoapify.com/v1/staticmap?style=osm-bright&width=800&height=400&center=lonlat:{lon},{lat}&zoom=10&marker=lonlat:{lon},{lat};color:%23ff0000;size:large&apiKey={GEOAPIFY_API_KEY}"
        
        st.image(map_url, use_container_width=True)
        
        st.markdown(f"""
        <div style='background-color: #f5f7fa; padding: 15px; border-radius: 10px; margin-top: 10px; text-align: center;'>
            <b>📍 Localização:</b> Latitude: {lat:.4f}° | Longitude: {lon:.4f}°
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.warning(f"⚠️ Não foi possível carregar o mapa: {str(e)}")


def exibir_dados_propriedade():
    """Exibe os dados da propriedade em formato amigável"""
    
    cad = st.session_state["cadastro"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="card-dados">
            <label>👤 Proprietário</label>
            <div class="valor">{cad["nome"] or "Não informado"}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="card-dados">
            <label>📧 E-mail</label>
            <div class="valor">{cad["email"] or "Não informado"}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="card-dados">
            <label>📱 Telefone</label>
            <div class="valor">{cad["telefone"] or "Não informado"}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="card-dados">
            <label>🏢 Fazenda</label>
            <div class="valor">{cad["fazenda"] or "Não informado"}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="card-dados">
            <label>📍 Localização</label>
            <div class="valor">{cad["municipio"] or "Não informado"} - {cad["estado"] or "Não informado"}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="card-dados">
            <label>📐 Área Total</label>
            <div class="valor">{cad["area_total"]:.1f} ha</div>
        </div>
        """, unsafe_allow_html=True)


def get_referencias_relatorio():
    """Gera as referências para o relatório final"""
    
    refs = []
    refs.append("## 📚 Referências Técnicas\n")
    
    refs.append("### 🌱 Embrapa")
    for ref in REFERENCIAS_TECNICAS["Embrapa"]:
        refs.append(f"- {ref}")
    refs.append("")
    
    refs.append("### 📊 Boletim 100 - SBCS")
    for ref in REFERENCIAS_TECNICAS["Boletim 100"]:
        refs.append(f"- {ref}")
    refs.append("")
    
    refs.append("### 📜 Normativos")
    for ref in REFERENCIAS_TECNICAS["Normativos"]:
        refs.append(f"- {ref}")
    refs.append("")
    
    refs.append("### 🔬 Metodologias")
    for ref in REFERENCIAS_TECNICAS["Metodologias"]:
        refs.append(f"- {ref}")
    
    return "\n".join(refs)

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
        lat_str = st.text_input(
            "Latitude",
            value=str(st.session_state["cadastro"]["latitude"]),
            key="cad_lat_text",
            placeholder="-15.0000"
        )
        try:
            latitude = float(lat_str)
            if -33.75 <= latitude <= 5.27:
                st.session_state["cadastro"]["latitude"] = latitude
            else:
                st.warning("⚠️ Latitude fora do território brasileiro (-33.75 a 5.27)")
        except ValueError:
            latitude = st.session_state["cadastro"]["latitude"]
    
    with col4:
        lon_str = st.text_input(
            "Longitude",
            value=str(st.session_state["cadastro"]["longitude"]),
            key="cad_lon_text",
            placeholder="-50.0000"
        )
        try:
            longitude = float(lon_str)
            if -73.98 <= longitude <= -34.79:
                st.session_state["cadastro"]["longitude"] = longitude
            else:
                st.warning("⚠️ Longitude fora do território brasileiro (-73.98 a -34.79)")
        except ValueError:
            longitude = st.session_state["cadastro"]["longitude"]
    
    st.markdown("---")
    st.subheader("🗺️ Visualização da Localização")
    exibir_mapa_geoapify(latitude, longitude)
    
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
    
    st.markdown("---")
    st.subheader("📊 Dados da Propriedade")
    exibir_dados_propriedade()


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
    st.subheader("🏗️ Sistema Produtivo e Fertilidade")
    
    col5, col6, col7 = st.columns(3)
    with col5:
        sistemas = ["Grãos", "Pecuária", "Integração Lavoura-Pecuária", "Hortaliças", "Fruticultura"]
        sistema_produtivo = st.selectbox("Sistema Produtivo", sistemas, key="man_sistema")
    with col6:
        fertilidades = ["Baixa", "Média", "Alta"]
        fertilidade = st.selectbox("Fertilidade do Solo", fertilidades, key="man_fertilidade")
    with col7:
        hidricas = ["Baixa", "Média", "Alta"]
        disponibilidade_hidrica = st.selectbox("Disponibilidade Hídrica", hidricas, key="man_hidrica")
    
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
    st.session_state["manejo"]["sistema_produtivo"] = sistema_produtivo
    st.session_state["manejo"]["fertilidade"] = fertilidade
    st.session_state["manejo"]["disponibilidade_hidrica"] = disponibilidade_hidrica
    
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


def render_cobertura():
    """Renderiza a página de coberturas vegetais com fluxo corrigido"""
    st.title("🌿 Planejamento de Coberturas Vegetais")
    st.markdown("---")
    init_session_state()
    
    st.markdown("""
    <div class="info-box">
        <b>📌 Instruções:</b> Preencha todas as informações sobre sua propriedade e clique em 
        <b>"Salvar Variáveis"</b> para gerar recomendações personalizadas de cobertura vegetal.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ===== ETAPA 1: PREENCHIMENTO DOS DADOS =====
    st.subheader("📋 Etapa 1: Informações da Propriedade")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🌾 Sistema Produtivo**")
        sistemas = ["Grãos", "Pecuária", "Integração Lavoura-Pecuária", "Hortaliças", "Fruticultura"]
        sistema_produtivo = st.selectbox("Sistema Produtivo", sistemas, key="cov_sistema")
    
    with col2:
        st.markdown("**🌍 Bioma**")
        biomas = ["Cerrado", "Mata Atlântica", "Amazônia", "Caatinga", "Pantanal", "Pampa"]
        bioma = st.selectbox("Bioma da propriedade", biomas, key="cov_bioma")
    
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**🌡️ Clima**")
        climas = ["Tropical", "Subtropical", "Semiárido", "Temperado"]
        clima = st.selectbox("Clima predominante", climas, key="cov_clima")
    
    with col4:
        st.markdown("**🌵 Período Seco**")
        periodo_seco = st.number_input("Período seco (dias)", min_value=0, max_value=300, value=st.session_state["cobertura"].get("periodo_seco", 90), key="cov_periodo")
    
    st.markdown("---")
    st.subheader("🎯 Etapa 2: Objetivos e Limitações")
    
    col5, col6 = st.columns(2)
    with col5:
        st.markdown("**🎯 Objetivo Principal**")
        objetivos = ["Produzir palhada", "Produzir matéria orgânica", "Descompactação", "Reciclagem de nutrientes", "Fixação biológica de nitrogênio", "Controle de nematoides"]
        objetivo = st.selectbox("Selecione o objetivo principal", objetivos, key="cov_objetivo")
    
    with col6:
        st.markdown("**🔧 Problema Principal**")
        problemas = [
            "Baixa matéria orgânica",
            "Compactação do solo",
            "Baixa fertilidade",
            "Erosão",
            "Infestação de nematoides",
            "Baixa infiltração",
            "Crosta superficial"
        ]
        problema = st.selectbox("Selecione o problema principal", problemas, key="cov_problema")
    
    col7, col8 = st.columns(2)
    with col7:
        st.markdown("**✨ Característica Desejada**")
        caracteristicas = [
            "Alta produção de biomassa",
            "Rápida decomposição",
            "Lenta decomposição",
            "Sistema radicular profundo",
            "Fixação biológica de N",
            "Controle de plantas daninhas"
        ]
        caracteristica = st.selectbox("Selecione a característica desejada", caracteristicas, key="cov_caracteristica")
    
    with col8:
        st.markdown("**⏱️ Tempo de Permanência**")
        tempo_permanencia = st.number_input("Tempo de permanência desejado (dias)", min_value=30, max_value=365, value=st.session_state["cobertura"].get("tempo_permanencia", 90), key="cov_tempo")
    
    col9, col10 = st.columns(2)
    with col9:
        st.markdown("**🧪 Fertilidade do Solo**")
        fertilidades = ["Baixa", "Média", "Alta"]
        fertilidade = st.selectbox("Fertilidade do solo", fertilidades, key="cov_fertilidade")
    
    with col10:
        st.markdown("**💧 Disponibilidade Hídrica**")
        hidricas = ["Baixa", "Média", "Alta"]
        disponibilidade_hidrica = st.selectbox("Disponibilidade hídrica", hidricas, key="cov_hidrica")
    
    st.markdown("---")
    
    # ===== ETAPA 2: SALVAR DADOS =====
    if st.button("💾 SALVAR VARIÁVEIS E GERAR RECOMENDAÇÕES", use_container_width=True, type="primary"):
        st.session_state["cobertura"]["sistema_produtivo"] = sistema_produtivo
        st.session_state["cobertura"]["bioma"] = bioma
        st.session_state["cobertura"]["clima"] = clima
        st.session_state["cobertura"]["periodo_seco"] = periodo_seco
        st.session_state["cobertura"]["objetivo"] = objetivo
        st.session_state["cobertura"]["problema_principal"] = problema
        st.session_state["cobertura"]["caracteristica_desejada"] = caracteristica
        st.session_state["cobertura"]["tempo_permanencia"] = tempo_permanencia
        st.session_state["cobertura"]["fertilidade"] = fertilidade
        st.session_state["cobertura"]["disponibilidade_hidrica"] = disponibilidade_hidrica
        st.session_state["cobertura"]["dados_salvos"] = True
        st.session_state["cobertura"]["recomendacoes_geradas"] = False
        
        st.success("✅ Variáveis salvas com sucesso! Clique em 'Gerar Recomendações' para ver as sugestões.")
    
    st.markdown("---")
    
    # ===== ETAPA 3: GERAR RECOMENDAÇÕES =====
    if st.session_state["cobertura"]["dados_salvos"]:
        if st.button("🔍 GERAR RECOMENDAÇÕES", use_container_width=True, type="primary"):
            with st.spinner("Processando recomendações..."):
                # Obtém dados da propriedade
                bioma = st.session_state["cobertura"]["bioma"]
                clima = st.session_state["cobertura"]["clima"]
                objetivo = st.session_state["cobertura"]["objetivo"]
                problema = st.session_state["cobertura"]["problema_principal"]
                caracteristica = st.session_state["cobertura"]["caracteristica_desejada"]
                periodo_seco = st.session_state["cobertura"]["periodo_seco"]
                sistema_produtivo = st.session_state["cobertura"]["sistema_produtivo"]
                fertilidade = st.session_state["cobertura"]["fertilidade"]
                disponibilidade_hidrica = st.session_state["cobertura"]["disponibilidade_hidrica"]
                temperatura = st.session_state["manejo"].get("temperatura_media", 25.0)
                precipitacao = st.session_state["manejo"].get("precipitacao", 1500.0)
                
                # Gera recomendações
                recomendacoes = recomendar_coberturas_dinamicas(
                    problema, caracteristica, bioma, clima,
                    sistema_produtivo, fertilidade, periodo_seco,
                    temperatura, precipitacao, objetivo
                )
                
                st.session_state["cobertura"]["recomendacoes"] = recomendacoes
                st.session_state["cobertura"]["recomendacoes_geradas"] = True
                st.success("✅ Recomendações geradas com sucesso!")
    
    st.markdown("---")
    
    # ===== ETAPA 4: EXIBIR RECOMENDAÇÕES =====
    if st.session_state["cobertura"]["recomendacoes_geradas"]:
        st.subheader("📋 Recomendações Personalizadas")
        
        recomendacoes = st.session_state["cobertura"]["recomendacoes"]
        
        if recomendacoes:
            st.markdown(f"""
            <div class="success-box">
                <b>✅ Encontradas {len(recomendacoes)} espécies recomendadas</b>
            </div>
            """, unsafe_allow_html=True)
            
            for i, rec in enumerate(recomendacoes):
                classe = "card-recomendacao destaque" if i == 0 else "card-recomendacao"
                
                # Monta justificativas
                justificativas_texto = ""
                if rec.get("justificativas"):
                    justificativas_texto = "<br>".join([f"✓ {j}" for j in rec["justificativas"]])
                
                # Monta informações adicionais
                info_extra = ""
                if rec.get("tipo"):
                    info_extra += f"<p><b>Tipo:</b> {rec['tipo']}</p>"
                if rec.get("sistema_radicular"):
                    info_extra += f"<p><b>Sistema radicular:</b> {rec['sistema_radicular']}</p>"
                if rec.get("fixacao_n") is not None:
                    info_extra += f"<p><b>Fixação de N:</b> {'✅ Sim' if rec['fixacao_n'] else '❌ Não'}</p>"
                
                st.markdown(f"""
                <div class="{classe}">
                    <h3>{'⭐ ' if i == 0 else ''}🌱 {rec['especie']}</h3>
                    <p><b>Biomassa estimada:</b> {rec['biomassa']} t/ha</p>
                    <p><b>Persistência:</b> {rec['persistencia']}</p>
                    <p><b>Incremento de carbono:</b> {rec['carbono']} t/ha</p>
                    <p><b>Relação C/N:</b> {rec['relacao_cn']}</p>
                    <p><b>Score de adequação:</b> {rec['score']}%</p>
                    {info_extra}
                    <p><b>Justificativas:</b><br>{justificativas_texto}</p>
                    <p><b>Referência:</b> {rec.get('referencia', 'Embrapa')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Nenhuma espécie encontrada com os parâmetros atuais. Tente ajustar os filtros.")
        
        # Salva nomes das recomendações para o relatório
        st.session_state["cobertura"]["recomendacoes_nomes"] = [rec["especie"] for rec in recomendacoes]
    elif st.session_state["cobertura"]["dados_salvos"]:
        st.info("📌 Clique em 'Gerar Recomendações' para visualizar as sugestões.")


def render_consorcio():
    """Renderiza a página de consórcios inteligentes com lógica revisada"""
    st.title("🌾 Consórcios Inteligentes")
    st.markdown("---")
    init_session_state()
    
    st.subheader("🤝 Escolha a Cultura Principal")
    culturas = ["Soja", "Milho", "Algodão", "Feijão"]
    cultura_principal = st.selectbox("Selecione a cultura principal", culturas, index=culturas.index(st.session_state["consorcio"]["cultura_principal"]) if st.session_state["consorcio"]["cultura_principal"] in culturas else 0, key="con_cultura")
    st.session_state["consorcio"]["cultura_principal"] = cultura_principal
    
    st.markdown("---")
    st.subheader("🌡️ Condições de Cultivo")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        clima_consorcio = st.selectbox("Clima", ["Tropical", "Subtropical", "Semiárido", "Temperado"], key="con_clima")
    with col2:
        objetivo_consorcio = st.selectbox("Objetivo Principal", ["Produção de Palhada", "Fixação de N", "Descompactação", "Ciclagem de Nutrientes"], key="con_objetivo")
    with col3:
        sistema_consorcio = st.selectbox("Sistema de Produção", ["Grãos", "Pecuária", "Integração Lavoura-Pecuária"], key="con_sistema")
    
    st.markdown("---")
    
    if st.button("🔍 ANALISAR CONSÓRCIOS", use_container_width=True, type="primary"):
        st.session_state["consorcio"]["analisado"] = True
    
    st.markdown("---")
    
    if st.session_state.get("consorcio", {}).get("analisado", False):
        st.subheader("📋 Consórcios Recomendados")
        
        if cultura_principal in CONSORCIOS_DB:
            opcoes = CONSORCIOS_DB[cultura_principal]["opcoes"]
            
            # Filtra por objetivo
            opcoes_filtradas = []
            for opcao in opcoes:
                # Verifica compatibilidade com o objetivo
                if objetivo_consorcio == "Produção de Palhada" and "Palhada" in str(opcao["beneficios"]):
                    opcoes_filtradas.append(opcao)
                elif objetivo_consorcio == "Fixação de N" and "Fixação" in str(opcao["beneficios"]):
                    opcoes_filtradas.append(opcao)
                elif objetivo_consorcio == "Descompactação" and "Infiltração" in str(opcao["beneficios"]):
                    opcoes_filtradas.append(opcao)
                elif objetivo_consorcio == "Ciclagem de Nutrientes" and "Reciclagem" in str(opcao["beneficios"]):
                    opcoes_filtradas.append(opcao)
                else:
                    # Se não encaixar no filtro, mantém como opção secundária
                    opcoes_filtradas.append(opcao)
            
            for i, consorcio in enumerate(opcoes_filtradas[:3], 1):
                with st.expander(f"Consórcio {i}: {consorcio['nome']}", expanded=i==1):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown("**Benefícios:**")
                        for beneficio in consorcio["beneficios"]:
                            st.markdown(f"✅ {beneficio}")
                        
                        st.markdown(f"""
                        **📖 Justificativa Técnica:**
                        {consorcio['justificativa']}
                        """)
                        
                        st.markdown(f"""
                        **📌 Recomendação de Manejo:**
                        {consorcio['recomendacao']}
                        """)
                    with col2:
                        st.metric("Impacto produtivo estimado", consorcio["impacto"])
                        st.metric("Compatibilidade", consorcio["compatibilidade"])
                        st.caption(f"Tipo: {consorcio['tipo_consorcio']}")
        else:
            st.warning("⚠️ Cultura não encontrada no banco de dados")
    else:
        st.info("📌 Clique em 'Analisar Consórcios' para visualizar as recomendações.")


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
            st.warning(f"⚠️ Não foi possível exportar para Excel: {str(e)}")
            
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📊 Exportar para CSV",
                data=csv_data,
                file_name=f"decomposicao_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                type="secondary"
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
            st.markdown(f"**Sistema Produtivo:** {man.get('sistema_produtivo', 'Não informado')}")
        
        with st.expander("🌿 Coberturas Recomendadas", expanded=True):
            cov = st.session_state["cobertura"]
            st.markdown(f"**Objetivo:** {cov.get('objetivo', 'Não definido')}")
            st.markdown(f"**Bioma:** {cov.get('bioma', 'Não definido')}")
            st.markdown(f"**Problema:** {cov.get('problema_principal', 'Não definido')}")
            
            if cov.get('recomendacoes_nomes'):
                st.markdown("**Recomendações:**")
                for rec in cov['recomendacoes_nomes']:
                    st.markdown(f"✅ {rec}")
            elif cov.get('recomendacoes'):
                st.markdown("**Recomendações:**")
                for rec in cov['recomendacoes']:
                    st.markdown(f"✅ {rec.get('especie', rec)}")
            else:
                st.warning("Nenhuma recomendação gerada")
        
        with st.expander("📊 Simulação de Decomposição", expanded=True):
            dec = st.session_state["decomposicao"]
            if dec['dados_simulacao'] is not None:
                st.markdown(f"**Cobertura:** {dec['cobertura']}")
                st.markdown(f"**Massa Seca:** {dec['massa_seca']:.1f} t/ha")
                st.dataframe(dec['dados_simulacao'], use_container_width=True, hide_index=True)
            else:
                st.warning("Nenhuma simulação realizada")
        
        st.markdown("---")
        with st.expander("📚 Referências Técnicas", expanded=True):
            st.markdown(get_referencias_relatorio())
        
        st.markdown("---")
        st.info("✅ Relatório completo gerado com sucesso!")
    else:
        st.info("📌 Clique em 'GERAR RELATÓRIO' para visualizar o relatório completo")

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
    "Sistema desenvolvido para auxiliar no planejamento de coberturas vegetais e manejo da matéria orgânica do solo."
)

if st.session_state["cadastro"]["nome"]:
    st.sidebar.success(f"👤 {st.session_state['cadastro']['nome']}")
    st.sidebar.caption(f"🏢 {st.session_state['cadastro']['fazenda'] or 'Propriedade não cadastrada'}")

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
