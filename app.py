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

# Máy tính khởi động: Mở két sắt JSON ra tìm chìa khóa trước
if 'gemini_api_key' not in st.session_state:
    if os.path.exists(KEY_FILE):
        try:
            with open(KEY_FILE, "r") as f:
                st.session_state.gemini_api_key = json.load(f).get("GEMINI_API_KEY", "")
        except:
            st.session_state.gemini_api_key = ""
    else:
        st.session_state.gemini_api_key = ""

if 'uploaded_gemini_file' not in st.session_state:
    st.session_state.uploaded_gemini_file = None

# ==========================================
# 3. GIAO DIỆN ĐIỀU HÀNH
# ==========================================
st.title("🏛️ ROMAN-X: HỘI ĐỒNG ĐẦU TƯ TỰ TRỊ")
st.markdown("*Bộ não AI nạp trực tiếp Video/PDF bài giảng thực chiến của Roman Bogomazov*")
st.divider()

tab1, tab2, tab3 = st.tabs(["🧠 BỘ NÃO (Lò Luyện Đan)", "📐 X-RAY (Đọc Chart)", "🎯 THỰC CHIẾN (POE)"])

# ==========================================
# PHÒNG SỐ 1: LÒ LUYỆN ĐAN
# ==========================================
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("🔑 1. Đánh thức Đặc vụ")
        api_input = st.text_input("Nhập Gemini API Key:", type="password", value=st.session_state.gemini_api_key)
        
        # NÚT BẤM LƯU VÀO KÉT SẮT JSON
        if st.button("Lưu Chìa Khóa Vĩnh Viễn"):
            st.session_state.gemini_api_key = api_input
            with open(KEY_FILE, "w") as f:
                json.dump({"GEMINI_API_KEY": api_input}, f)
            st.success("✅ Đã đúc chìa khóa vào Két sắt ổ cứng!")
            st.rerun()

    with col2:
        st.header("📚 2. Nạp Di sản của Roman")
        if not st.session_state.gemini_api_key:
            st.warning("⚠️ Vui lòng nhập API Key bên trái để mở khóa Lò Luyện Đan.")
        else:
            genai.configure(api_key=st.session_state.gemini_api_key)
            
            uploaded_file = st.file_uploader("Kéo thả Video MP4 hoặc sách PDF của thầy Roman vào đây", type=['mp4', 'pdf', 'txt'])
            
            if uploaded_file:
                if st.button("🚀 BẮT ĐẦU NUỐT TÀI LIỆU VÀO NÃO", use_container_width=True):
                    with st.spinner("Đang đẩy file lên hệ thống lõi của Google (Gemini File API)... Xin kiên nhẫn đợi!"):
                        try:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                                tmp.write(uploaded_file.getvalue())
                                tmp_path = tmp.name
                                
                            gemini_file = genai.upload_file(tmp_path)
                            
                            while gemini_file.state.name == "PROCESSING":
                                st.info("Hệ thống Google đang bóc tách từng khung hình và giọng nói trong Video... Đợi thêm vài giây.")
                                time.sleep(5)
                                gemini_file = genai.get_file(gemini_file.name)
                                
                            st.session_state.uploaded_gemini_file = gemini_file
                            st.success(f"✅ Đã nuốt xong tài liệu: {gemini_file.name} (Sẵn sàng khai thác!)")
                            os.remove(tmp_path)
                        except Exception as e:
                            st.error(f"❌ Lỗi khi nuốt tài liệu: {e}")

    st.divider()
    
    if st.session_state.uploaded_gemini_file:
        st.subheader("🕵️ Trực tiếp tra khảo Đặc vụ Roman")
        st.caption("Ví dụ: 'Dựa vào video này, thầy Roman định nghĩa thế nào là một cú Spring hợp lệ? Dấu hiệu Volume ra sao?'")
        
        user_prompt = st.text_area("Ra lệnh trích xuất thuật toán:")
        if st.button("Khai thác Dữ liệu"):
            with st.spinner("Đặc vụ đang tua lại tài liệu/video để tìm câu trả lời..."):
                try:
                    model = genai.GenerativeModel('models/gemini-1.5-pro')
                    response = model.generate_content([st.session_state.uploaded_gemini_file, user_prompt])
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
