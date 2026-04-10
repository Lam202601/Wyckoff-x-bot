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
KEY_FILE = "roman_keys.json"
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = ""
if 'uploaded_gemini_files' not in st.session_state:
    st.session_state.uploaded_gemini_files = []

# ==========================================
# 2. KHUNG SƯỜN: 3 TABS CHIẾN LƯỢC
# ==========================================
tab1, tab2, tab3 = st.tabs(["🧠 BỘ NÃO (Lò Luyện Đan)", "📐 X-RAY (Đọc Chart)", "🎯 THỰC CHIẾN (POE)"])

# ==========================================
# PHÒNG SỐ 1: LÒ LUYỆN ĐAN
# ==========================================
with tab1:
    col1, col2 = st.columns([1, 2])
    
    # --- CỘT TRÁI: NHẬP CHÌA KHÓA API ---
    with col1:
        st.header("🔑 1. Đánh thức Đặc vụ")
        api_input = st.text_input("Nhập Gemini API Key (Bắt buộc):", type="password", value=st.session_state.gemini_api_key)
        
        if st.button("Lưu Chìa Khóa AI"):
            st.session_state.gemini_api_key = api_input
            st.success("✅ Đã ghi nhớ API Key!")
            st.rerun()

        if len(st.session_state.uploaded_gemini_files) > 0:
            st.info(f"Đang có {len(st.session_state.uploaded_gemini_files)} file trong não AI.")
            if st.button("🗑️ Xóa sạch bộ nhớ tạm"):
                st.session_state.uploaded_gemini_files = []
                if 'latest_wiki_content' in st.session_state:
                    del st.session_state['latest_wiki_content']
                st.rerun()
                
    # --- CỘT PHẢI: HÚT DATA TỪ GOOGLE DRIVE ---
    with col2:
        st.header("📚 2. Hút Di sản từ Google Drive")
        
        st.info("Bảo mật: File JSON chỉ lưu trên RAM tạm thời, dùng xong tự hủy.")
        uploaded_json = st.file_uploader("Tải file Chìa khóa Google (.json) lên đây:", type=["json"])
        
        drive_service = None
        if uploaded_json is not None:
            try:
                gcp_creds = json.load(uploaded_json)
                credentials = service_account.Credentials.from_service_account_info(
                    gcp_creds,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                drive_service = build('drive', 'v3', credentials=credentials)
                st.success("✅ Đã kết nối thành công với đường ống Google Drive!")
            except Exception as e:
                st.error(f"❌ Lỗi đọc file JSON: {e}")

        if not st.session_state.gemini_api_key:
            st.error("⚠️ Sếp phải nhập Gemini API Key ở bên trái trước.")
        elif drive_service is not None:
            drive_url = st.text_input("🔗 Dán Link THƯ MỤC (Folder) hoặc FILE trên Drive vào đây:")
            
            if drive_url and st.button("🚀 HÚT TRỌN Ổ DỮ LIỆU", use_container_width=True):
                files_to_process = []
                
                try:
                    if '/folders/' in drive_url:
                        folder_id = drive_url.split('/folders/')[1].split('?')[0]
                        # NÂNG CẤP: Lấy thêm định dạng file (mimeType) để nhận diện Google Docs
                        results = drive_service.files().list(
                            q=f"'{folder_id}' in parents and trashed=false", 
                            fields="files(id, name, mimeType)"
                        ).execute()
                        files_to_process = results.get('files', [])
                        if not files_to_process:
                            st.warning("Thư mục này trống hoặc sếp chưa Share quyền cho Đặc vụ!")
                            st.stop()
                    elif '/file/d/' in drive_url:
                        file_id = drive_url.split('/d/')[1].split('/')[0]
                        file_meta = drive_service.files().get(fileId=file_id, fields='name, mimeType').execute()
                        files_to_process = [{'id': file_id, 'name': file_meta.get('name'), 'mimeType': file_meta.get('mimeType')}]
                    else:
                        st.error("Link không đúng chuẩn Google Drive.")
                        st.stop()
                except Exception as e:
                    st.error(f"❌ Lỗi đọc link: {e}")
                    st.stop()

                st.write(f"🎯 Đặc vụ đã khóa mục tiêu: {len(files_to_process)} tài liệu.")
                
                for i, file_item in enumerate(files_to_process):
                    file_id = file_item['id']
                    file_name = file_item['name']
                    mime_type = file_item.get('mimeType', '')
                    
                    with st.status(f"[{i+1}/{len(files_to_process)}] Đang xử lý: {file_name}...", expanded=True) as status:
                        try:
                            # CƠ CHẾ TỰ ĐỘNG ÉP GOOGLE DOCS SANG PDF
                            if 'vnd.google-apps' in mime_type:
                                st.write("   ... Phát hiện Google Docs/Sheets. Đang tự động ép sang PDF...")
                                request = drive_service.files().export_media(fileId=file_id, mimeType='application/pdf')
                                file_suffix = ".pdf"
                            else:
                                request = drive_service.files().get_media(fileId=file_id)
                                file_suffix = f".{file_name.split('.')[-1]}" if '.' in file_name else ".tmp"
                            
                            with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp:
                                downloader = MediaIoBaseDownload(tmp, request, chunksize=1024*1024*20)
                                done = False
                                while done is False:
                                    d_status, done = downloader.next_chunk()
                                    st.write(f"   ... Đang hút từ Drive: {int(d_status.progress() * 100)}%")
                                tmp_path = tmp.name

                            st.write("☁️ Đang nhồi vào não AI Gemini...")
                            client = genai.Client(api_key=st.session_state.gemini_api_key)
                            gemini_file = client.files.upload(file=tmp_path)
                            
                            while gemini_file.state == "PROCESSING":
                                time.sleep(5)
                                gemini_file = client.files.get(name=gemini_file.name)
                            
                            if gemini_file.state == "FAILED":
                                status.update(label=f"❌ Lỗi: Gemini từ chối file {file_name}", state="error")
                            else:
                                st.session_state.uploaded_gemini_files.append(gemini_file)
                                status.update(label=f"✅ Nuốt thành công: {file_name}", state="complete", expanded=False)
                            
                            os.remove(tmp_path)
                            
                            if i < len(files_to_process) - 1:
                                st.info("⏱️ Máy đang nghỉ 15 giây để né cảnh báo quá tải của Google...")
                                time.sleep(15)
                                
                        except Exception as e:
                            status.update(label=f"❌ Thất bại với file này: {e}", state="error")
                
                st.success("🎉 TỔNG TIẾN CÔNG THÀNH CÔNG! Đã nuốt trọn ổ dữ liệu!")

    st.divider()
    
    # --- KHÚC DƯỚI: LÒ PHẢN ỨNG VÀ NÚT TẢI XUỐNG ---
    if len(st.session_state.uploaded_gemini_files) > 0:
        st.subheader("🕵️ 3. Chưng Cất Tri Thức (Ép Xung AI)")
        
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

        if st.button("🔥 CHẠY LÒ PHẢN ỨNG TẠO FILE WIKI", type="primary", use_container_width=True):
            with st.spinner("Đặc vụ đang chưng cất thành Wiki. Sếp chờ chút nhé..."):
                try:
                    client = genai.Client(api_key=st.session_state.gemini_api_key)
                    prompt_parts = st.session_state.uploaded_gemini_files + [master_prompt]
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt_parts
                    )
                    
                    st.session_state.latest_wiki_content = response.text
                    st.success("✅ Đã chưng cất thành công! Sếp xem trước và tải về bên dưới.")
                    
                except Exception as e:
                    st.error(f"❌ Lỗi AI: {e}")
        
        # HIỂN THỊ KẾT QUẢ VÀ NÚT TẢI XUỐNG
        if 'latest_wiki_content' in st.session_state:
            with st.expander("👀 Xem trước nội dung Wiki", expanded=True):
                st.markdown(st.session_state.latest_wiki_content)
            
            timestamp = time.strftime("%Y%m%d_%H%M")
            default_filename = f"Roman_Lesson_EN_{timestamp}.md"
            
            st.download_button(
                label="📥 TẢI FILE WIKI NÀY VỀ MÁY M4",
                data=st.session_state.latest_wiki_content,
                file_name=default_filename,
                mime="text/markdown",
                type="primary"
            )

# ==========================================
# PHÒNG SỐ 2 & 3: GIỮ NGUYÊN CHỜ NÂNG CẤP
# ==========================================
with tab2:
    st.header("Đôi Mắt X-Ray: Giải mã cấu trúc giá")
    st.info("Trạng thái: Chờ ráp thuật toán PineScript lượng hóa độ dốc (ATR).")

with tab3:
    st.header("Bàn Cờ Thực Chiến: Quản trị Rủi Ro & POE")
    st.info("Trạng thái: Chờ thiết lập logic từ Đặc vụ Roman.")
