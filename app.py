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

        if st.button("🔥 CHẠY DÂY CHUYỀN TẠO WIKI TỰ ĐỘNG", type="primary", use_container_width=True):
            st.session_state.latest_wiki_content = "# TỔNG HỢP WIKI WYCKOFF (ROMAN)\n\n"
            total_files = len(st.session_state.uploaded_gemini_files)
            
            # Thanh tiến độ xịn xò để sếp không phải ngóng
            progress_bar = st.progress(0, text="Chuẩn bị khởi động lò phản ứng...")
            status_text = st.empty()
            
            client = genai.Client(api_key=st.session_state.gemini_api_key)
            
            for i, gemini_file in enumerate(st.session_state.uploaded_gemini_files):
                # Cập nhật trạng thái cho sếp biết
                progress_bar.progress((i) / total_files, text=f"Đang chưng cất bài học {i+1}/{total_files}...")
                status_text.info(f"⏳ Đang phân tích: Tài liệu số {i+1}. Chờ chút nhé sếp...")
                
                try:
                    # Truyền TỪNG FILE MỘT + master prompt vào AI
                    prompt_parts = [gemini_file, master_prompt]
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt_parts
                    )
                    
                    # Ghép bài mới vào cuốn Wiki tổng
                    st.session_state.latest_wiki_content += f"\n\n---\n## TÀI LIỆU SỐ {i+1}\n\n"
                    st.session_state.latest_wiki_content += response.text
                    
                    status_text.success(f"✅ Đã đúc kết xong Tài liệu số {i+1}!")
                    
                    # Làm mát AI 15 giây để không bị khóa mõm
                    if i < total_files - 1:
                        status_text.warning("⏱️ Đang làm mát lò AI 15 giây trước khi nhai bài tiếp theo...")
                        time.sleep(15)
                        
                except Exception as e:
                    status_text.error(f"❌ Đặc vụ bị vấp ở Tài liệu số {i+1}: {e}")
            
            # Cập nhật khi hoàn tất 100%
            progress_bar.progress(100, text="✅ Dây chuyền hoàn tất!")
            status_text.success("🎉 ĐÃ ĐÚC KẾT XONG TOÀN BỘ WIKI! Sếp xem trước và tải về bên dưới.")
        
        # KHÚC XUẤT FILE TẢI VỀ
        if 'latest_wiki_content' in st.session_state:
            with st.expander("👀 Xem trước nội dung Wiki", expanded=True):
                st.markdown(st.session_state.latest_wiki_content)
            
            timestamp = time.strftime("%Y%m%d_%H%M")
            default_filename = f"Roman_Wyckoff_FullWiki_{timestamp}.md"
            
            st.download_button(
                label="📥 TẢI FILE WIKI TỔNG HỢP NÀY VỀ MÁY",
                data=st.session_state.latest_wiki_content,
                file_name=default_filename,
                mime="text/markdown",
                type="primary"
            )

# ==========================================
# PHÒNG SỐ 2 & 3: GIỮ NGUYÊN KHÔNG MẤT
# ==========================================
with tab2:
    st.header("📐 Đôi Mắt X-Ray")
with tab3:
    st.header("🎯 Thực Chiến (POE)")
