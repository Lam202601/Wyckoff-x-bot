import streamlit as st
import google.generativeai as genai
import tempfile
import time
import os
import json  # <--- Vũ khí Két sắt của V46

# ==========================================
# 1. CÀI ĐẶT TỔNG QUAN
# ==========================================
st.set_page_config(page_title="ROMAN-X | Agentic Quant", page_icon="🏛️", layout="wide")

# ==========================================
# 2. KHỞI TẠO BỘ NHỚ LÕI (KÉT SẮT JSON NHƯ V46)
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

# ĐÃ NÂNG CẤP: Biến này giờ là một cái DANH SÁCH (List) để chứa nhiều file
if 'uploaded_gemini_files' not in st.session_state:
    st.session_state.uploaded_gemini_files = []

# ==========================================
# 3. GIAO DIỆN ĐIỀU HÀNH
# ==========================================
st.title("🏛️ ROMAN-X: HỘI ĐỒNG ĐẦU TƯ TỰ TRỊ")
st.markdown("*Bộ脑 AI nạp trực tiếp hàng loạt Video/PDF bài giảng thực chiến của Roman Bogomazov*")
st.divider()

tab1, tab2, tab3 = st.tabs(["🧠 BỘ NÃO (Lò Luyện Đan)", "📐 X-RAY (Đọc Chart)", "🎯 THỰC CHIẾN (POE)"])

# ==========================================
# PHÒNG SỐ 1: LÒ LUYỆN ĐAN (NÂNG CẤP ĐA LUỒNG)
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
            st.success("✅ Đã đúc chìa khóa vào Két sắt ổ cứng!")
            st.rerun()

        # Nút xóa bộ nhớ (Reset não AI khi sếp muốn nạp bộ tài liệu chủ đề khác)
        if len(st.session_state.uploaded_gemini_files) > 0:
            if st.button("🗑️ Xóa sạch bộ nhớ AI hiện tại"):
                st.session_state.uploaded_gemini_files = []
                st.rerun()

    with col2:
        st.header("📚 2. Nạp Di sản của Roman")
        if not st.session_state.gemini_api_key:
            st.warning("⚠️ Vui lòng nhập API Key bên trái để mở khóa Lò Luyện Đan.")
        else:
            genai.configure(api_key=st.session_state.gemini_api_key)
            
            # ĐÃ BẬT CÔNG TẮC accept_multiple_files=True (Cho phép ném nhiều file)
            uploaded_files = st.file_uploader(
                "Kéo thả NHIỀU Video MP4 hoặc sách PDF vào đây cùng lúc", 
                type=['mp4', 'pdf', 'txt'], 
                accept_multiple_files=True
            )
            
            if uploaded_files:
                if st.button(f"🚀 BẮT ĐẦU NUỐT {len(uploaded_files)} TÀI LIỆU VÀO NÃO", use_container_width=True):
                    # Vòng lặp duyệt qua từng file sếp thả vào
                    for uploaded_file in uploaded_files:
                        with st.spinner(f"Đang nhai file: {uploaded_file.name}..."):
                            try:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                                    tmp.write(uploaded_file.getvalue())
                                    tmp_path = tmp.name
                                    
                                gemini_file = genai.upload_file(tmp_path)
                                
                                while gemini_file.state.name == "PROCESSING":
                                    time.sleep(5)
                                    gemini_file = genai.get_file(gemini_file.name)
                                    
                                # Lưu thẳng file vừa xử lý xong vào Não
                                st.session_state.uploaded_gemini_files.append(gemini_file)
                                st.success(f"✅ Đã nuốt xong: {gemini_file.name}")
                                os.remove(tmp_path)
                            except Exception as e:
                                st.error(f"❌ Lỗi khi nuốt {uploaded_file.name}: {e}")

    st.divider()
    
    # KHU VỰC TRA KHẢO (Chỉ hiện khi trong não đã có ít nhất 1 file)
    if len(st.session_state.uploaded_gemini_files) > 0:
        st.subheader(f"🕵️ Trực tiếp tra khảo Đặc vụ Roman (Đang nhớ {len(st.session_state.uploaded_gemini_files)} tài liệu)")
        st.caption("AI sẽ tự động tổng hợp kiến thức chéo từ TẤT CẢ các video và PDF sếp đã nạp vào.")
        
        user_prompt = st.text_area("Ra lệnh trích xuất thuật toán:")
        if st.button("Khai thác Dữ liệu"):
            with st.spinner("Đặc vụ đang kết nối các luồng thông tin để tìm câu trả lời..."):
                try:
                    model = genai.GenerativeModel('models/gemini-1.5-pro')
                    # Chiến thuật ném nguyên rổ file + câu hỏi vào cho AI nhai 1 lượt
                    prompt_parts = st.session_state.uploaded_gemini_files + [user_prompt]
                    
                    response = model.generate_content(prompt_parts)
                    st.markdown("### 📜 Báo cáo từ Đặc vụ:")
                    st.info(response.text)
                except Exception as e:
                    st.error(f"❌ Lỗi phản hồi: {e}")

# --- PHÒNG SỐ 2 & 3 (Giữ nguyên chờ sếp duyệt xong Tab 1) ---
with tab2:
    st.header("Đôi Mắt X-Ray: Giải mã cấu trúc giá")
    st.info("Trạng thái: Chờ ráp thuật toán PineScript lượng hóa độ dốc (ATR).")

with tab3:
    st.header("Bàn Cờ Thực Chiến: Quản trị Rủi Ro & POE")
    st.info("Trạng thái: Chờ thiết lập logic từ Đặc vụ Roman.")

# --- PHÒNG SỐ 2 & 3 (Giữ nguyên chờ sếp duyệt xong Tab 1) ---
with tab2:
    st.header("Đôi Mắt X-Ray: Giải mã cấu trúc giá")
    st.info("Trạng thái: Chờ ráp thuật toán PineScript lượng hóa độ dốc (ATR).")

with tab3:
    st.header("Bàn Cờ Thực Chiến: Quản trị Rủi Ro & POE")
    st.info("Trạng thái: Chờ thiết lập logic từ Đặc vụ Roman.")
