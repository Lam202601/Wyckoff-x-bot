import streamlit as st
import tempfile
import time
import os
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google import genai
# ==========================================
# 1. CÀI ĐẶT GIAO DIỆN TỔNG QUAN
# ==========================================
st.set_page_config(page_title="ROMAN-X | Agentic Quant", page_icon="🏛️", layout="wide")
st.title("🏛️ ROMAN-X: HỘI ĐỒNG ĐẦU TƯ TỰ TRỊ")
st.divider()

# KHỞI TẠO BỘ NHỚ LÕI (Cho Gemini API Key)
KEY_FILE = "roman_keys.json"
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = ""
if 'uploaded_gemini_files' not in st.session_state:
    st.session_state.uploaded_gemini_files = []

# ==========================================
# 2. DÒNG NÀY CỰC QUAN TRỌNG: ĐẺ RA 3 CÁI TABS
# ==========================================
tab1, tab2, tab3 = st.tabs(["🧠 BỘ NÃO (Lò Luyện Đan)", "📐 X-RAY (Đọc Chart)", "🎯 THỰC CHIẾN (POE)"])

# ==========================================
# PHÒNG SỐ 1: LÒ LUYỆN ĐAN (CẮM VÀO TAB 1)
# ==========================================
# ... (Khai báo API Gemini như cũ) ...

st.header("📚 2. Hút Di sản trực tiếp từ Google Drive")

import json # Sếp nhớ phải có chữ import json ở đầu nhé, nếu chưa có thì sếp thêm vào

# 1. Xác thực bằng Két sắt Streamlit
try:
    # Lấy chuỗi JSON từ Két Sắt và dịch nó ra
    gcp_creds = json.loads(st.secrets["GCP_JSON"])
    credentials = service_account.Credentials.from_service_account_info(
        gcp_creds,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    drive_service = build('drive', 'v3', credentials=credentials)
    st.success("✅ Đã kết nối thành công với đường ống Google Drive!")
except Exception as e:
    st.error("❌ Chưa kết nối được Google Drive. Vui lòng kiểm tra tab Secrets.")

# 2. Giao diện nạp link Google Drive
drive_url = st.text_input("🔗 Dán Link chia sẻ của file MP4/PDF trên Google Drive vào đây:")

if drive_url and st.button("🚀 HÚT VÀ NUỐT FILE NÀY", use_container_width=True):
    # Trích xuất File ID từ Link
    try:
        file_id = drive_url.split('/d/')[1].split('/')[0]
    except:
        st.error("Link không hợp lệ. Vui lòng dùng link dạng 'https://drive.google.com/file/d/...'")
        st.stop()

    with st.status("Đang thực hiện chiến dịch hút dữ liệu...", expanded=True) as status:
        try:
            # Lấy tên file
            file_metadata = drive_service.files().get(fileId=file_id, fields='name').execute()
            file_name = file_metadata.get('name', 'Roman_Video.mp4')
            st.write(f"📁 Đã tìm thấy file: {file_name}")

            # Khởi tạo file tạm trên ổ cứng (Không dùng RAM)
            st.write("⏳ Đang truyền dữ liệu từ Drive qua ống ngầm (Bảo vệ RAM)...")
            request = drive_service.files().get_media(fileId=file_id)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_name.split('.')[-1]}") as tmp:
                downloader = MediaIoBaseDownload(tmp, request, chunksize=1024*1024*20) # Hút từng cục 20MB
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    st.write(f"   ... Đã hút được {int(status.progress() * 100)}%")
                tmp_path = tmp.name

            # Đẩy sang Gemini
            st.write("☁️ Đang nạp vào não Google Gemini (Có thể mất vài phút cho Video)...")
            client = genai.Client(api_key=st.session_state.gemini_api_key)
            gemini_file = client.files.upload(file=tmp_path)
            
            while gemini_file.state == "PROCESSING":
                time.sleep(5)
                gemini_file = client.files.get(name=gemini_file.name)
            
            if gemini_file.state == "FAILED":
                st.error("❌ Gemini không đọc được file này!")
            else:
                st.session_state.uploaded_gemini_files.append(gemini_file)
                st.success(f"✅ Nuốt thành công: {file_name}")
            
            # Xóa rác
            os.remove(tmp_path)
            
        except Exception as e:
            st.error(f"❌ Lỗi đường ống: {e}")

    st.divider()
    
    if len(st.session_state.uploaded_gemini_files) > 0:
        st.subheader("🕵️ Chưng Cất Tri Thức (Ép Xung AI)")
        
        master_prompt = """You are an elite Wyckoff Quant Agent. Analyze the provided materials (videos, images, PDFs) from Roman Bogomazov's lectures. 
Distill this knowledge into a highly detailed, purely quantitative Wiki Markdown file.

CRITICAL RULES:
1. Write the ENTIRE output in 100% ENGLISH. Do not translate anything.
2. Strictly preserve Roman Bogomazov's exact terminology.
3. Focus heavily on quantitative logic (rules that can be coded into trading algorithms).

Output using exactly this Markdown structure:

# [Short Topic Name]
**Metadata:**
- **Tags:** #Wyckoff_Theory, #[Relevant_Keywords]
- **Links:** (Link to other core concepts using double brackets, e.g., [[Phase C]], [[Spring]], [[Change of Character]], [[Composite Operator]])

**1. Roman's Insight:**
(Extract the most critical spoken advice, core philosophy, or specific nuances Roman emphasizes about this topic).

**2. Price/Volume Behavior:**
(Specific details on price spread, closing position, and volume signatures).

**3. Quant Logic:**
(If writing an algorithmic trading script to detect this event, what are the exact mathematical or logical conditions? E.g., Volume < 20-period SMA, Spread < ATR, Close within the lower third of the bar, etc.).

**4. Context & Traps:**
(Where does this event fit within the overall Accumulation/Distribution schematic? What are the common traps Smart Money uses here?)"""

# --- PHÒNG SỐ 2 & 3 ---
with tab2:
    st.header("Đôi Mắt X-Ray: Giải mã cấu trúc giá")
    st.info("Trạng thái: Chờ ráp thuật toán PineScript lượng hóa độ dốc (ATR).")

with tab3:
    st.header("Bàn Cờ Thực Chiến: Quản trị Rủi Ro & POE")
    st.info("Trạng thái: Chờ thiết lập logic từ Đặc vụ Roman.")
