import streamlit as st
from google import genai  # <--- Khai báo theo chuẩn mới của Google
import tempfile
import time
import os
import json

# ==========================================
# 1. CÀI ĐẶT TỔNG QUAN
# ==========================================
st.set_page_config(page_title="ROMAN-X | Agentic Quant", page_icon="🏛️", layout="wide")

# ==========================================
# 2. KHỞI TẠO BỘ NHỚ LÕI (KÉT SẮT JSON)
# ==========================================
KEY_FILE = "roman_keys.json"

if 'gemini_api_key' not in st.session_state:
    if os.path.exists(KEY_FILE):
        try:
            with open(KEY_FILE, "r") as f:
                st.session_state.gemini_api_key = json.load(f).get("GEMINI_API_KEY", "")
        except:
            st.session_state.gemini_api_key = ""
    else:
        st.session_state.gemini_api_key = ""

if 'uploaded_gemini_files' not in st.session_state:
    st.session_state.uploaded_gemini_files = []

# ==========================================
# 3. GIAO DIỆN ĐIỀU HÀNH
# ==========================================
st.title("🏛️ ROMAN-X: HỘI ĐỒNG ĐẦU TƯ TỰ TRỊ")
st.markdown("*Bộ não AI nạp trực tiếp hàng loạt Video/PDF bài giảng thực chiến của Roman Bogomazov*")
st.divider()

tab1, tab2, tab3 = st.tabs(["🧠 BỘ NÃO (Lò Luyện Đan)", "📐 X-RAY (Đọc Chart)", "🎯 THỰC CHIẾN (POE)"])

# ==========================================
# PHÒNG SỐ 1: LÒ LUYỆN ĐAN (CỐI XAY WIKI)
# ==========================================
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("🔑 1. Đánh thức Đặc vụ")
        api_input = st.text_input("Nhập Gemini API Key:", type="password", value=st.session_state.gemini_api_key)
        
        if st.button("Lưu Chìa Khóa Vĩnh Viễn"):
            st.session_state.gemini_api_key = api_input
            with open(KEY_FILE, "w") as f:
                json.dump({"GEMINI_API_KEY": api_input}, f)
            st.success("✅ Đã đúc chìa khóa vào Két sắt!")
            st.rerun()

        if len(st.session_state.uploaded_gemini_files) > 0:
            if st.button("🗑️ Xóa sạch bộ nhớ tạm (Xóa MP4 trên mây)"):
                st.session_state.uploaded_gemini_files = []
                if 'latest_wiki_content' in st.session_state:
                    del st.session_state['latest_wiki_content']
                st.rerun()
                
        st.info("💡 Quy trình: Nạp File -> AI Tiêu hóa -> Bấm tải file Text (.md) về ném vào thư mục Obsidian trên máy sếp.")

    with col2:
        st.header("📚 2. Nạp Di sản của Roman")
        if not st.session_state.gemini_api_key:
            st.warning("⚠️ Vui lòng nhập API Key bên trái để mở khóa.")
        else:
            client = genai.Client(api_key=st.session_state.gemini_api_key)
            
            uploaded_files = st.file_uploader(
                "Kéo thả Video MP4 hoặc sách PDF vào đây", 
                type=['mp4', 'pdf', 'txt','png','jpg', 'jpeg','ppt'], 
                accept_multiple_files=True
            )
            
            if uploaded_files:
                if st.button(f"🚀 BẮT ĐẦU NUỐT {len(uploaded_files)} TÀI LIỆU", use_container_width=True):
                    for uploaded_file in uploaded_files:
                        with st.spinner(f"Đang nhai file: {uploaded_file.name}..."):
                            try:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                                    tmp.write(uploaded_file.getbuffer()) 
                                    tmp_path = tmp.name
                                
                                gemini_file = client.files.upload(file=tmp_path)
                                
                                while gemini_file.state == "PROCESSING":
                                    time.sleep(5)
                                    gemini_file = client.files.get(name=gemini_file.name)
                                    
                                st.session_state.uploaded_gemini_files.append(gemini_file)
                                st.success(f"✅ Đã nuốt xong: {gemini_file.name}")
                                os.remove(tmp_path)
                            except Exception as e:
                                st.error(f"❌ Lỗi khi nuốt: {e}")

    st.divider()
    
    if len(st.session_state.uploaded_gemini_files) > 0:
        st.subheader("🕵️ Chưng Cất Tri Thức (Ép Xung AI)")
        
        master_prompt = """Mày là Đặc vụ Wyckoff Quant. Hãy xem kỹ các video/tài liệu tao vừa nạp, đặc biệt LẮNG NGHE kỹ lời thầy Roman Bogomazov giảng giải và đối chiếu với biểu đồ.
Hãy chưng cất bài giảng này thành 1 file Wiki Markdown siêu chi tiết. BẮT BUỘC dùng Tiếng Việt và xuất theo đúng cấu trúc sau:

# [Tên Chủ Đề Bài Học Ngắn Gọn]
**Metadata:**
- **Tags:** #Wyckoff_Theory, #Roman_Bogomazov
- **Links:** (Gắn link tới các khái niệm khác bằng cú pháp [[Tên Khái Niệm]], ví dụ: [[Pha C]], [[Spring]], [[VSA]])

**1. Tâm pháp gốc (Roman's Insight):**
(Trích xuất những câu nói, lời dặn dò quan trọng nhất của thầy Roman bằng lời).

**2. Dấu hiệu Hành vi (Price/Volume):**
(Cụ thể giá và khối lượng di chuyển thế nào?)

**3. Ánh xạ Định lượng (Quant Logic):**
(Nếu phải viết code để tìm dấu hiệu này trên biểu đồ, điều kiện toán học là gì?)

**4. Bối cảnh & Cạm bẫy:**
(Thường đi sau sự kiện nào? Chú ý gì để không bị bẫy?)"""

        if st.button("🔥 CHẠY LÒ PHẢN ỨNG TẠO FILE WIKI", type="primary", use_container_width=True):
            with st.spinner("Đặc vụ đang dịch MP4 và viết sách Markdown... Sếp chờ khoảng 1-2 phút nhé..."):
                try:
                    client = genai.Client(api_key=st.session_state.gemini_api_key)
                    prompt_parts = st.session_state.uploaded_gemini_files + [master_prompt]
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt_parts
                    )
                    
                    st.session_state.latest_wiki_content = response.text
                    st.success("✅ Đã chưng cất thành công! Sếp hãy xem trước và tải về bên dưới.")
                    
                except Exception as e:
                    st.error(f"❌ Lỗi phản hồi: {e}")
        
        if 'latest_wiki_content' in st.session_state:
            with st.expander("👀 Xem trước nội dung Wiki", expanded=True):
                st.markdown(st.session_state.latest_wiki_content)
            
            # Đặt tên file thân thiện
            timestamp = time.strftime("%Y%m%d_%H%M")
            default_filename = f"Roman_Lesson_{timestamp}.md"
            
            st.download_button(
                label="📥 TẢI FILE NÀY VỀ MÁY (Dành cho Obsidian Vault)",
                data=st.session_state.latest_wiki_content,
                file_name=default_filename,
                mime="text/markdown",
                type="primary"
            )

# --- PHÒNG SỐ 2 & 3 ---
with tab2:
    st.header("Đôi Mắt X-Ray: Giải mã cấu trúc giá")
    st.info("Trạng thái: Chờ ráp thuật toán PineScript lượng hóa độ dốc (ATR).")

with tab3:
    st.header("Bàn Cờ Thực Chiến: Quản trị Rủi Ro & POE")
    st.info("Trạng thái: Chờ thiết lập logic từ Đặc vụ Roman.")
