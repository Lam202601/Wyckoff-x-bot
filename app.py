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
                "Kéo thả Video MP4 hoặc sách PDF, hoặc file hình ảnh vào đây", 
                type=['mp4', 'pdf', 'txt','png','jpg', 'jpeg','ppt'], 
                accept_multiple_files=True
            )
            
            if uploaded_files:
                if st.button(f"🚀 BẮT ĐẦU NUỐT {len(uploaded_files)} TÀI LIỆU", use_container_width=True):
                    for uploaded_file in uploaded_files:
                        # DÙNG BẢNG STATUS ĐỂ THEO DÕI TIẾN ĐỘ THAY VÌ SPINNER QUAY VÔ HỒN
                        with st.status(f"Đang xử lý: {uploaded_file.name}...", expanded=True) as status:
                            try:
                                st.write("⏳ 1. Đang lưu file tạm thời...")
                                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                                    tmp.write(uploaded_file.getbuffer()) 
                                    tmp_path = tmp.name
                                
                                st.write("☁️ 2. Đang đẩy dữ liệu lên máy chủ Google...")
                                gemini_file = client.files.upload(file=tmp_path)
                                
                                st.write("🧠 3. Google Gemini đang 'xem' video (Có thể mất 2-10 phút tùy độ dài)...")
                                # Đếm ngược thời gian để sếp biết máy không treo
                                wait_time = 0
                                while gemini_file.state == "PROCESSING":
                                    time.sleep(5)
                                    wait_time += 5
                                    st.write(f"   ... đã phân tích được {wait_time} giây...")
                                    gemini_file = client.files.get(name=gemini_file.name)
                                    
                                if gemini_file.state == "FAILED":
                                    status.update(label=f"❌ Lỗi: Google không thể đọc file này!", state="error", expanded=True)
                                else:
                                    st.session_state.uploaded_gemini_files.append(gemini_file)
                                    status.update(label=f"✅ Nuốt thành công: {gemini_file.name}", state="complete", expanded=False)
                                
                                os.remove(tmp_path)
                            except Exception as e:
                                status.update(label=f"❌ Lỗi hệ thống: {e}", state="error", expanded=True)

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
