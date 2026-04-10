import streamlit as st
import json
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

# KHỞI TẠO BỘ NHỚ LÕI
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = ""
if 'uploaded_gemini_files' not in st.session_state:
    st.session_state.uploaded_gemini_files = []

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
                    # Nếu là thư mục, tự động chui vào sâu hơn
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
    
    with col1:
        st.header("🔑 1. Đánh thức Đặc vụ")
        api_input = st.text_input("Gemini API Key:", type="password", value=st.session_state.gemini_api_key)
        if st.button("Lưu Chìa Khóa AI"):
            st.session_state.gemini_api_key = api_input
            st.rerun()

        if len(st.session_state.uploaded_gemini_files) > 0:
            st.info(f"Đã nạp {len(st.session_state.uploaded_gemini_files)} tài liệu.")
            if st.button("🗑️ Xóa bộ nhớ"):
                st.session_state.uploaded_gemini_files = []
                st.rerun()
                
    with col2:
        st.header("📚 2. Hút Di sản (Càn quét thư mục)")
        uploaded_json = st.file_uploader("Ném file JSON Google Cloud vào đây:", type=["json"])
        
        drive_service = None
        if uploaded_json:
            try:
                gcp_creds = json.load(uploaded_json)
                credentials = service_account.Credentials.from_service_account_info(
                    gcp_creds, scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                drive_service = build('drive', 'v3', credentials=credentials)
                st.success("✅ Hệ thống quét đệ quy đã sẵn sàng!")
            except Exception as e: st.error(f"Lỗi JSON: {e}")

        if drive_service and st.session_state.gemini_api_key:
            drive_url = st.text_input("🔗 Link Thư mục lớn (Chứa nhiều sub-folders):")
            
            if drive_url and st.button("🚀 TỔNG TIẾN CÔNG HÚT SẠCH", use_container_width=True):
                try:
                    folder_id = drive_url.split('/folders/')[1].split('?')[0] if '/folders/' in drive_url else drive_url.split('/d/')[1].split('/')[0]
                    
                    with st.status("🔍 Đang càn quét các thư mục con...", expanded=True) as status:
                        files_to_process = get_all_files_recursive(drive_service, folder_id)
                        st.write(f"🎯 Tìm thấy tổng cộng {len(files_to_process)} file trong mọi ngóc ngách.")
                        
                        for i, file_item in enumerate(files_to_process):
                            f_id, f_name, f_mime = file_item['id'], file_item['name'], file_item.get('mimeType', '')
                            
                            # Bỏ qua các file rác không đọc được
                            if 'folder' in f_mime or 'shortcut' in f_mime: continue
                            
                            st.write(f"[{i+1}/{len(files_to_process)}] Đang nuốt: {f_name}")
                            
                            # Xử lý Ép PDF nếu là Google Docs/Sheets
                            if 'vnd.google-apps' in f_mime and any(x in f_mime for x in ['document', 'spreadsheet', 'presentation']):
                                request = drive_service.files().export_media(fileId=f_id, mimeType='application/pdf')
                                suffix = ".pdf"
                            else:
                                request = drive_service.files().get_media(fileId=f_id)
                                suffix = f".{f_name.split('.')[-1]}" if '.' in f_name else ".tmp"

                            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                                downloader = MediaIoBaseDownload(tmp, request, chunksize=1024*1024*10)
                                done = False
                                while not done: status_dl, done = downloader.next_chunk()
                                tmp_path = tmp.name

                            client = genai.Client(api_key=st.session_state.gemini_api_key)
                            gemini_file = client.files.upload(file=tmp_path)
                            while gemini_file.state == "PROCESSING": time.sleep(5); gemini_file = client.files.get(name=gemini_file.name)
                            
                            st.session_state.uploaded_gemini_files.append(gemini_file)
                            os.remove(tmp_path)
                            if i < len(files_to_process)-1: time.sleep(15) # Né lỗi 429
                        
                        status.update(label="🎉 Đã nuốt trọn di sản từ mọi thư mục con!", state="complete")
                except Exception as e: st.error(f"Lỗi: {e}")

    st.divider()
    if len(st.session_state.uploaded_gemini_files) > 0:
        if st.button("🔥 TẠO WIKI TỔNG HỢP TỪ TẤT CẢ FILE", type="primary", use_container_width=True):
            # ... (Phần logic Generate Content dùng master_prompt thuần Anh của sếp ở đây) ...
            st.info("Đang xử lý Wiki chuẩn Wyckoff English...")

# ==========================================
# PHÒNG SỐ 2 & 3: GIỮ NGUYÊN KHÔNG MẤT
# ==========================================
with tab2:
    st.header("📐 Đôi Mắt X-Ray")
with tab3:
    st.header("🎯 Thực Chiến (POE)")
