import streamlit as st
import graphviz
import base64
import gspread
from google.oauth2.service_account import Credentials

# 設定頁面配置
st.set_page_config(page_title="AI 開發專案儀表板", layout="wide", page_icon="🚀")

# --- Google Sheets 連線設定 ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def init_google_sheet():
    try:
        # 從 st.secrets 讀取憑證
        credentials_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(
            credentials_info, scopes=SCOPES
        )
        client = gspread.authorize(creds)
        
        # 開啟試算表
        sheet_url = st.secrets["sheets"]["spreadsheet_url"]
        sh = client.open_by_url(sheet_url)
        
        # 嘗試取得或建立工作表
        try:
            worksheet = sh.worksheet("dashboard_data")
        except gspread.WorksheetNotFound:
            worksheet = sh.add_worksheet(title="dashboard_data", rows=100, cols=3)
            # 寫入標題列
            worksheet.append_row(["key", "value", "category"])
            
        return worksheet
    except Exception as e:
        st.error(f"無法連線至 Google Sheets: {str(e)}")
        return None

def load_data():
    default_data = {
        "strategy": {
            "general": "BQML 難題：評估模型在 BigQuery 中的限制與解決方案。",
            "cloud_vs_onprem": "權衡分析：資源分配最佳化與成本效益計算。",
            "continuous_improvement": "Fine-tuning：建立模型持續優化與迭代機制。"
        },
        "resources": {
            "bigquery": { 
                "progress": "已完成 Raw Data 串接，正在進行數據清洗。", 
                "notes": "目前先列出熱銷產品，正在嘗試連結其他索引。" 
            },
            "website": { 
                "progress": "官網資料爬取完成，Bonsale 標籤化進行中。", 
                "notes": "匯整銷售知識，建立產品索引。" 
            },
            "notion": { 
                "progress": "產品資料已匯入，正在規劃主題分類。", 
                "notes": "針對成分與適用族群做關聯。" 
            },
            "recording": { 
                "progress": "Top Sales 錄音檔已轉文字，向量化測試中。", 
                "notes": "Milvus 比 Gemini 爬蟲省 10 倍 Token 且速度快，目標是全資訊匯整。" 
            }
        }
    }
    
    worksheet = init_google_sheet()
    if worksheet:
        try:
            records = worksheet.get_all_records()
            if not records:
                return default_data
                
            # 將 List of Dicts 轉換回巢狀結構
            data = default_data.copy() # 先複製預設結構
            
            for row in records:
                key = row.get('key')
                value = row.get('value')
                category = row.get('category')
                
                if category == 'strategy':
                    if key in data['strategy']:
                        data['strategy'][key] = value
                elif category in data['resources']:
                    # key 格式預期為 "progress" 或 "notes"
                    if key in data['resources'][category]:
                        data['resources'][category][key] = value
                        
            return data
        except Exception as e:
            st.warning(f"讀取資料失敗，使用預設值。錯誤: {str(e)}")
            return default_data
            
    return default_data

def save_data():
    worksheet = init_google_sheet()
    if not worksheet:
        st.error("無法儲存：連線失敗")
        return

    # 準備要寫入的資料 (Flatten)
    rows_to_write = [["key", "value", "category"]] # Header
    
    # Strategy
    rows_to_write.append(["general", st.session_state.get("strategy_general", ""), "strategy"])
    rows_to_write.append(["cloud_vs_onprem", st.session_state.get("strategy_cloud", ""), "strategy"])
    rows_to_write.append(["continuous_improvement", st.session_state.get("strategy_improve", ""), "strategy"])
    
    # Resources
    resources = ["bigquery", "website", "notion", "recording"]
    resource_keys = {
        "bigquery": "bq",
        "website": "web",
        "notion": "notion",
        "recording": "rec"
    }
    
    for res in resources:
        prefix = resource_keys[res]
        rows_to_write.append(["progress", st.session_state.get(f"{prefix}_progress", ""), res])
        rows_to_write.append(["notes", st.session_state.get(f"{prefix}_notes", ""), res])
        
    try:
        worksheet.clear()
        worksheet.update(rows_to_write)
        # st.toast("資料已儲存至 Google Sheets!", icon="☁️") 
    except Exception as e:
        st.error(f"儲存失敗: {str(e)}")

# 初始化資料
if 'data' not in st.session_state:
    with st.spinner('正在從 Google Sheets 載入資料...'):
        st.session_state.data = load_data()

# --- 背景圖片處理 ---

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = '''
    <style>
    .stApp {
        background-image: url("data:image/png;base64,%s");
        background-size: cover;
        background-attachment: fixed;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)

try:
    set_png_as_page_bg('background.png')
except Exception as e:
    pass # 避免找不到檔案時報錯

# 自訂 CSS
st.markdown("""
<style>
    /* 全域字體與背景優化 */
    .stApp {
        font-family: 'Inter', 'Helvetica Neue', sans-serif;
    }
    
    /* 讓內容區塊背景半透明黑底以凸顯文字 */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background-color: rgba(0, 0, 0, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 20px;
        backdrop-filter: blur(5px);
    }

    /* 標題樣式 */
    h1 {
        padding-bottom: 1rem;
    }
    
    .gradient-text {
        background: -webkit-linear-gradient(45deg, #00d4ff, #005bea);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    
    h2, h3, p, li, span, div {
        color: #e0e0e0 !important;
    }
    
    h3 {
        font-weight: 600;
    }

    /* 調整 Expander 樣式 */
    .streamlit-expanderHeader {
        font-weight: 500;
        color: #ffffff !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 5px;
    }
    
    .streamlit-expanderContent {
        background-color: transparent !important;
        color: #e0e0e0 !important;
    }
    
    /* 側邊欄優化 */
    [data-testid="stSidebar"] {
        background-color: rgba(20, 20, 30, 0.9);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 強制側邊欄文字顏色為白色 */
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] li {
        color: #ffffff !important;
    }
    
    /* 隱藏 Streamlit 預設的 Deploy 按鈕 */
    .stDeployButton, [data-testid="stDeployButton"], [data-testid="stAppDeployButton"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* 隱藏頂部彩條，但保留 Header 以便顯示側邊欄開關 */
    [data-testid="stDecoration"] {
        display: none;
    }
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0.9);
    }
    
    /* 修正：讓 Header 內的按鈕和連結文字變白 */
    [data-testid="stHeader"] button, 
    [data-testid="stHeader"] a {
        color: white !important;
    }
    
    /* 修正：讓 SVG 圖示顏色跟隨文字 (解決灰色問題，避免變成方塊) */
    [data-testid="stHeader"] svg {
        fill: currentColor !important;
    }
    
    /* Text Area 樣式優化 */
    .stTextArea textarea {
        background-color: rgba(0, 0, 0, 0.5) !important;
        color: #ffffff !important;
        caret-color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    .stTextArea label {
        color: #00d4ff !important;
        font-weight: bold;
    }

</style>
""", unsafe_allow_html=True)


# 標題
st.markdown("# 🚀 <span class='gradient-text'>AI 開發專案儀表板</span>", unsafe_allow_html=True)


# 側邊欄：策略考量
with st.sidebar:
    st.header("💡 策略考量")
    st.markdown("---")
    
    st.text_area("🎯 通用性", 
                 value=st.session_state.data['strategy']['general'], 
                 key="strategy_general", 
                 on_change=save_data,
                 height=100)
    
    st.text_area("☁️ 雲端 vs 地端", 
                 value=st.session_state.data['strategy']['cloud_vs_onprem'], 
                 key="strategy_cloud", 
                 on_change=save_data,
                 height=100)
    
    st.text_area("🔄 持續改善", 
                 value=st.session_state.data['strategy']['continuous_improvement'], 
                 key="strategy_improve", 
                 on_change=save_data,
                 height=100)

# 分割成四個欄位
col1, col2, col3, col4 = st.columns(4)

# 1. BigQuery 資源
with col1:
    with st.container(border=True):
        st.subheader("📊 BigQuery 資源")
        st.caption("數據倉儲與分析核心")
        with st.expander("查看流程與筆記", expanded=True):
            st.markdown("##### 🔗 資料處理流程")
            graph1 = graphviz.Digraph()
            graph1.attr(bgcolor='transparent')
            graph1.attr('node', shape='box', style='filled', fillcolor='#262730', fontcolor='white', color='#4b4b4b')
            graph1.attr('edge', color='#888888')
            graph1.node('A', 'Raw Data\n(Member/Sales)')
            graph1.node('B', '數據分析\n(熱銷/高獲利)')
            graph1.node('C', '推薦模型\n(年齡/性別/消費力)')
            graph1.edge('A', 'B')
            graph1.edge('B', 'C')
            st.graphviz_chart(graph1, use_container_width=True)
            
            st.divider()
            st.text_area("📈 目前進展", 
                         value=st.session_state.data['resources']['bigquery']['progress'],
                         key="bq_progress",
                         on_change=save_data)
            st.text_area("📝 測試筆記", 
                         value=st.session_state.data['resources']['bigquery']['notes'],
                         key="bq_notes",
                         on_change=save_data)

# 2. 官網/公司資源
with col2:
    with st.container(border=True):
        st.subheader("🏢 官網/公司資源")
        st.caption("企業知識與產品資訊")
        with st.expander("查看流程與筆記", expanded=True):
            st.markdown("##### 🔗 資料處理流程")
            graph2 = graphviz.Digraph()
            graph2.attr(bgcolor='transparent')
            graph2.attr('node', shape='box', style='filled', fillcolor='#262730', fontcolor='white', color='#4b4b4b')
            graph2.attr('edge', color='#888888')
            graph2.node('A', '官網資料')
            graph2.node('B', '標籤化\n(Bonsale)')
            graph2.node('C', '連結資訊\n(成分/價格/族群)')
            graph2.edge('A', 'B')
            graph2.edge('B', 'C')
            st.graphviz_chart(graph2, use_container_width=True)
            
            st.divider()
            st.text_area("📈 目前進展", 
                         value=st.session_state.data['resources']['website']['progress'],
                         key="web_progress",
                         on_change=save_data)
            st.text_area("📝 測試筆記", 
                         value=st.session_state.data['resources']['website']['notes'],
                         key="web_notes",
                         on_change=save_data)

# 3. Notion 知識庫
with col3:
    with st.container(border=True):
        st.subheader("📘 Notion 知識庫")
        st.caption("產品規劃與話術管理")
        with st.expander("查看流程與筆記", expanded=True):
            st.markdown("##### 🔗 資料處理流程")
            graph3 = graphviz.Digraph()
            graph3.attr(bgcolor='transparent')
            graph3.attr('node', shape='box', style='filled', fillcolor='#262730', fontcolor='white', color='#4b4b4b')
            graph3.attr('edge', color='#888888')
            graph3.node('A', 'Notion 產品資料')
            graph3.node('B', '主題規劃\n(保健食品)')
            graph3.node('C', '連結銷售話術')
            graph3.edge('A', 'B')
            graph3.edge('B', 'C')
            st.graphviz_chart(graph3, use_container_width=True)
            
            st.divider()
            st.text_area("📈 目前進展", 
                         value=st.session_state.data['resources']['notion']['progress'],
                         key="notion_progress",
                         on_change=save_data)
            st.text_area("📝 測試筆記", 
                         value=st.session_state.data['resources']['notion']['notes'],
                         key="notion_notes",
                         on_change=save_data)

# 4. 錄音檔/向量庫
with col4:
    with st.container(border=True):
        st.subheader("🎙️ 錄音檔/向量庫")
        st.caption("銷售對話智能檢索")
        with st.expander("查看流程與筆記", expanded=True):
            st.markdown("##### 🔗 資料處理流程")
            graph4 = graphviz.Digraph()
            graph4.attr(bgcolor='transparent')
            graph4.attr('node', shape='box', style='filled', fillcolor='#262730', fontcolor='white', color='#4b4b4b')
            graph4.attr('edge', color='#888888')
            graph4.node('A', 'Top Sales 錄音')
            graph4.node('B', '轉文字/向量化')
            graph4.node('C', '存入 Milvus')
            graph4.node('D', 'AI 助手檢索')
            graph4.edge('A', 'B')
            graph4.edge('B', 'C')
            graph4.edge('C', 'D')
            st.graphviz_chart(graph4, use_container_width=True)
            
            st.divider()
            st.text_area("📈 目前進展", 
                         value=st.session_state.data['resources']['recording']['progress'],
                         key="rec_progress",
                         on_change=save_data)
            st.text_area("📝 測試筆記", 
                         value=st.session_state.data['resources']['recording']['notes'],
                         key="rec_notes",
                         on_change=save_data)


