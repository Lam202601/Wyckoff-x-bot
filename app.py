import streamlit as st
import json
import tempfile
import time
import os
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

# ==========================================
# KHỞI TẠO BỘ NHỚ LÕI (GHI VÀO Ổ CỨNG)
# ==========================================
KEY_FILE = "roman_keys.json"

def load_keys():
    if os.path.exists(KEY_FILE):
        try:
            with open(KEY_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_keys(keys_dict):
    with open(KEY_FILE, "w") as f:
        json.dump(keys_dict, f)

saved_keys = load_keys()

if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = saved_keys.get("gemini_api_key", "")
if 'uploaded_gemini_files' not in st.session_state:
    st.session_state.uploaded_gemini_files = []
if 'gcp_creds' not in st.session_state:
    st.session_state.gcp_creds = None

# ==========================================
# 2. KHUNG SƯỜN: 3 TABS CHIẾN LƯỢC
# ==========================================
tab1, tab2, tab3 = st.tabs(["🧠 BỘ NÃO (Lò Luyện Đan)", "📐 X-RAY (Đọc Chart)", "🎯 THỰC CHIẾN (POE)"])

# --- HÀM HỖ TRỢ ĐỆ QUY (QUÉT TOÀN BỘ THƯ MỤC CON) ---
def get_all_files_recursive(service, folder_id):
    all_files = []
    page_token = None
    while True:
        try:
            results = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token
            ).execute()
            items = results.get('files', [])
            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    all_files.extend(get_all_files_recursive(service, item['id']))
                else:
                    all_files.append(item)
            page_token = results.get('nextPageToken', None)
            if not page_token: break
        except Exception:
            break
    return all_files

# ==========================================
# PHÒNG SỐ 1: LÒ LUYỆN ĐAN
# ==========================================
with tab1:
    col1, col2 = st.columns([1, 2])
    
    # --- CỘT TRÁI: API KEY ---
    with col1:
        st.header("🔑 1. Đánh thức Đặc vụ")
        api_input = st.text_input("Gemini API Key:", type="password", value=st.session_state.gemini_api_key)
        if st.button("Lưu Chìa Khóa AI"):
            st.session_state.gemini_api_key = api_input
            save_keys({"gemini_api_key": api_input})
            st.success("✅ Đã ghim Key vĩnh viễn!")
            time.sleep(1)
            st.rerun()

        if len(st.session_state.uploaded_gemini_files) > 0:
            st.info(f"Đã nạp {len(st.session_state.uploaded_gemini_files)} tài liệu vào não AI.")
            if st.button("🗑️ Xóa sạch bộ nhớ tạm"):
                st.session_state.uploaded_gemini_files = []
                if 'latest_wiki_content' in st.session_state:
                    del st.session_state['latest_wiki_content']
                st.rerun()
                
    # --- CỘT PHẢI: HÚT DATA TỪ GOOGLE DRIVE ---
    with col2:
        st.header("📚 2. Hút Di sản từ Google Drive")
        
        if st.session_state.gcp_creds is None:
            st.info("Bảo mật: File JSON chỉ lưu trên RAM tạm thời, dùng xong tự hủy.")
            uploaded_json = st.file_uploader("Ném file Chìa khóa Google (.json) vào đây:", type=["json"])
            
            if uploaded_json is not None:
                try:
                    st.session_state.gcp_creds = json.load(uploaded_json)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi đọc file JSON: {e}")

        drive_service = None
        if st.session_state.gcp_creds is not None:
            try:
                credentials = service_account.Credentials.from_service_account_info(
                    st.session_state.gcp_creds,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                drive_service = build('drive', 'v3', credentials=credentials)
                st.success("✅ Kết nối Drive đã được GHIM (Khỏi lo mất)!")
                if st.button("🔌 Hủy ghim kết nối Drive"):
                    st.session_state.gcp_creds = None
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Lỗi kết nối: {e}")
                st.session_state.gcp_creds = None

        if not st.session_state.gemini_api_key:
            st.error("⚠️ Sếp phải nhập Gemini API Key ở bên trái trước.")
        elif drive_service is not None:
            drive_url = st.text_input("🔗 Link Thư mục lớn (Chứa nhiều sub-folders):")
            
            col_a, col_b = st.columns(2)
            with col_a: start_idx = st.number_input("Hút từ file số:", min_value=1, value=1)
            with col_b: end_idx = st.number_input("Đến file số:", min_value=1, value=20)

            if drive_url and st.button("🚀 HÚT THEO ĐỢT", use_container_width=True):
                try:
                    folder_id = drive_url.split('/folders/')[1].split('?')[0] if '/folders/' in drive_url else drive_url.split('/d/')[1].split('/')[0]
                    
                    with st.status("🔍 Đang rà soát danh sách tài liệu...", expanded=True) as status:
                        all_files = get_all_files_recursive(drive_service, folder_id)
                        files_to_process = all_files[start_idx-1 : end_idx]
                        
                        st.write(f"🎯 Tổng kho có {len(all_files)} file. Đang xử lý đợt này: {len(files_to_process)} file (Từ #{start_idx} đến #{end_idx})")
                        
                        for i, file_item in enumerate(files_to_process):
                            file_id = file_item['id']
                            file_name = file_item['name']
                            mime_type = file_item.get('mimeType', '')
                            
                            st.write(f"[{i+1}/{len(files_to_process)}] Đang xử lý: {file_name}...")
                            
                            try:
                                if mime_type == 'application/vnd.google-apps.folder':
                                    st.write(f"   ⏭️ Bỏ qua {file_name} (Thư mục con)")
                                    continue
                                    
                                exportable_types = [
                                    'application/vnd.google-apps.document', 
                                    'application/vnd.google-apps.spreadsheet', 
                                    'application/vnd.google-apps.presentation'
                                ]
                                
                                if mime_type in exportable_types:
                                    st.write("   ... Ép sang PDF...")
                                    request = drive_service.files().export_media(fileId=file_id, mimeType='application/pdf')
                                    file_suffix = ".pdf"
                                elif 'vnd.google-apps' in mime_type:
                                    st.write(f"   ⏭️ Bỏ qua {file_name} (Form/Site/Shortcut)")
                                    continue
                                else:
                                    request = drive_service.files().get_media(fileId=file_id)
                                    file_suffix = f".{file_name.split('.')[-1]}" if '.' in file_name else ".tmp"
                                
                                with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp:
                                    downloader = MediaIoBaseDownload(tmp, request, chunksize=1024*1024*20)
                                    done = False
                                    while done is False:
                                        d_status, done = downloader.next_chunk()
                                    tmp_path = tmp.name

                                client = genai.Client(api_key=st.session_state.gemini_api_key)
                                gemini_file = client.files.upload(file=tmp_path)
                                
                                while gemini_file.state == "PROCESSING":
                                    time.sleep(5)
                                    gemini_file = client.files.get(name=gemini_file.name)
                                
                                if gemini_file.state == "FAILED":
                                    st.error(f"❌ Lỗi: Gemini từ chối file {file_name}")
                                else:
                                    st.session_state.uploaded_gemini_files.append(gemini_file)
                                
                                os.remove(tmp_path)
                                
                                if i < len(files_to_process) - 1:
                                    time.sleep(15) 
                                    
                            except Exception as e:
                                st.error(f"❌ Thất bại với file này: {e}")
                                
                        status.update(label=f"✅ Đã nuốt xong đợt từ {start_idx} đến {end_idx}!", state="complete")
                except Exception as e:
                    st.error(f"❌ Lỗi xử lý Drive: {e}")

    st.divider()
    
    # --- KHÚC DƯỚI: LÒ PHẢN ỨNG "KẸP CHẢ" (GOM FILE ĐỂ ĐỐI CHIẾU) ---
    if len(st.session_state.uploaded_gemini_files) > 0:
        st.subheader("🕵️ 3. Chưng Cất Tri Thức (Ép Xung AI - Kẹp Chả)")
        
        # PROMPT ĐÃ ĐƯỢC CẬP NHẬT ĐÚNG NHƯ CAM KẾT
        master_prompt = """You are an elite Wyckoff Quant Agent. 
CONTEXT: You are provided with multiple Transcripts (text) and Slides/Charts (PDFs) of Roman Bogomazov's lectures.

CRITICAL INSTRUCTION FOR FILE MATCHING (KẸP CHẢ):
You must strictly group and correlate files based on their filenames. Explicitly match the Transcript file with its corresponding Slide/Chart PDF that shares the same base name (e.g., match "Buoi_1_Transcript" EXACTLY with "Buoi_1_Slides"). 
ABSOLUTELY DO NOT mix verbal insights from one session with visual charts from a different session.

CRITICAL INSTRUCTION FOR KNOWLEDGE DISTILLATION: 
Use the matched transcript for verbal insights and core philosophy. 
CRUCIAL: Correlate these spoken insights with the visual price/volume charts in the matched PDF file to define precise, quantitative rules. 

Output a highly detailed Wiki Markdown file in 100% ENGLISH.
Strictly preserve Roman's terminology.

Structure:
# [Topic Name]
**1. Roman's Insight:** (Spoken advice from transcript)
**2. Price/Volume Behavior:** (Visual evidence from PDF charts)
**3. Quant Logic:** (Mathematical rules: Spread, Volume vs SMA, Position of Close, etc.)
**4. Context & Traps:** (Phases, Springs, Upthrusts context)"""

        if st.button("🚀 CHẠY LÒ PHẢN ỨNG (GOM TẤT CẢ ĐỂ ĐỐI CHIẾU)", type="primary", use_container_width=True):
            with st.status("🔥 Đang thực hiện cú 'Kẹp Chả' đa phương thức...", expanded=True) as status:
                try:
                    client = genai.Client(api_key=st.session_state.gemini_api_key)
                    
                    # THAY ĐỔI CHIẾN THUẬT: KHÔNG DÙNG VÒNG LẶP CHO TỪNG FILE
                    # GOM TẤT CẢ FILE VÀO 1 DANH SÁCH ĐỂ AI ĐỐI CHIẾU CÙNG LÚC
                    prompt_parts = st.session_state.uploaded_gemini_files + [master_prompt]
                    
                    st.write("📡 Đang gửi toàn bộ Transcript và PDF lên não bộ AI...")
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash', # Model xịn 1 triệu token
                        contents=prompt_parts
                    )
                    
                    st.session_state.latest_wiki_content = response.text
                    status.update(label="✅ Đã chưng cất và đối chiếu xong!", state="complete")
                    st.success("🎉 Wiki đã được tạo ra bằng cách khớp lời giảng với biểu đồ!")
                    
                except Exception as e:
                    st.error(f"❌ Đặc vụ bị nghẽn mạch: {e}")
        
        # HIỂN THỊ KẾT QUẢ
        if 'latest_wiki_content' in st.session_state:
            with st.expander("👀 Xem trước nội dung Wiki (Đã đối chiếu)", expanded=True):
                st.markdown(st.session_state.latest_wiki_content)
            
            st.download_button(
                label="📥 TẢI WIKI TỔNG HỢP VỀ MÁY",
                data=st.session_state.latest_wiki_content,
                file_name=f"Roman_Wyckoff_Correlated_Wiki.md",
                mime="text/markdown",
                type="primary"
            )

# ==========================================
# PHÒNG SỐ 2 & 3
# ==========================================
with tab2:
    st.header("📐 Đôi Mắt X-Ray: Giải mã cấu trúc giá")
    st.info("Trạng thái: Chờ ráp thuật toán PineScript lượng hóa độ dốc (ATR).")

with tab3:
    st.header("🎯 Bàn Cờ Thực Chiến: Quản trị Rủi Ro & POE")
    st.info("Trạng thái: Chờ thiết lập logic từ Đặc vụ Roman.")
