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
# PHÒNG SỐ 1: LÒ LUYỆN ĐAN (CÔNG NGHỆ LƯU TRỮ CLOUD)
# ==========================================
with tab1:
    col1, col2 = st.columns([1, 2])
    
    # KHO BÊN TRÁI: HIỂN THỊ TRÍ NHỚ CỦA AI TRÊN GOOGLE CLOUD
    with col1:
        st.header("🔑 1. Đánh thức Đặc vụ")
        api_input = st.text_input("Nhập Gemini API Key:", type="password", value=st.session_state.gemini_api_key)
        
        if st.button("Lưu Chìa Khóa Vĩnh Viễn"):
            st.session_state.gemini_api_key = api_input
            with open(KEY_FILE, "w") as f:
                json.dump({"GEMINI_API_KEY": api_input}, f)
            st.success("✅ Đã đúc chìa khóa vào Két sắt!")
            st.rerun()

        st.divider()
        st.subheader("🗄️ Trí Nhớ Vĩnh Cửu (Trên Google)")
        cloud_files = []
        if st.session_state.gemini_api_key:
            client = genai.Client(api_key=st.session_state.gemini_api_key)
            try:
                # Đòn quyết định: Gọi Google tải danh sách file đã lưu trên mây về
                cloud_files = list(client.files.list())
                if len(cloud_files) == 0:
                    st.info("Não đang trống rỗng. Hãy bơm tài liệu!")
                else:
                    st.success(f"Não đang ghi nhớ {len(cloud_files)} tài liệu.")
                    for f in cloud_files:
                        st.caption(f"📄 {f.display_name or f.name}")
                    
                    # Nút tẩy não vĩnh viễn trên Google (Tránh tràn 20GB)
                    if st.button("🗑️ XÓA TOÀN BỘ KÝ ỨC TRÊN GOOGLE"):
                        with st.spinner("Đang tẩy não..."):
                            for f in cloud_files:
                                client.files.delete(name=f.name)
                        st.rerun()
            except Exception as e:
                st.error("Chưa kết nối được kho dữ liệu.")

    # KHO BÊN PHẢI: TRẠM TRUNG CHUYỂN BƠM DỮ LIỆU
    with col2:
        st.header("📚 2. Bơm Kiến Thức Mới")
        if not st.session_state.gemini_api_key:
            st.warning("⚠️ Vui lòng nhập API Key bên trái để mở khóa Lò Luyện Đan.")
        else:
            # Ép người dùng nạp TỪNG FILE MỘT để Streamlit không bao giờ bị sặc RAM
            uploaded_file = st.file_uploader(
                "Kéo thả 1 File MP4/PDF vào đây (Tải xong file này mới tải tiếp file khác)", 
                type=['mp4', 'pdf', 'txt'], 
                accept_multiple_files=False 
            )
            
            if uploaded_file:
                if st.button("🚀 ĐẨY FILE NÀY LÊN MÂY", use_container_width=True):
                    with st.spinner(f"Đang bơm {uploaded_file.name} vào Não..."):
                        try:
                            # Đổ phễu dữ liệu
                            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                                tmp.write(uploaded_file.getbuffer())
                                tmp_path = tmp.name
                                
                            # Phóng lên mây Google
                            gemini_file = client.files.upload(file=tmp_path, config={'display_name': uploaded_file.name})
                            
                            while gemini_file.state == "PROCESSING":
                                time.sleep(5)
                                gemini_file = client.files.get(name=gemini_file.name)
                                
                            st.success(f"✅ Đã bơm xong! RAM Streamlit được giải phóng.")
                            os.remove(tmp_path)
                            time.sleep(2) # Nghỉ 2s rồi F5 lại để hiện file sang cột bên trái
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Lỗi khi bơm file: {e}")

    st.divider()
    
    # KHU VỰC TRA KHẢO
    if len(cloud_files) > 0:
        st.subheader(f"🕵️ Trực tiếp tra khảo Đặc vụ Roman")
        st.caption(f"Đặc vụ sẽ tự ráp nối logic từ toàn bộ {len(cloud_files)} file ở Cột Bên Trái để trả lời sếp.")
        
        user_prompt = st.text_area("Ra lệnh trích xuất thuật toán:")
        if st.button("Khai thác Dữ liệu"):
            with st.spinner(f"Đặc vụ đang lục lọi {len(cloud_files)} tài liệu... Xin kiên nhẫn đợi (có thể mất 1-2 phút)!"):
                try:
                    # Lọc lấy những file đã chạy xong (ACTIVE)
                    active_files = [f for f in cloud_files if f.state == "ACTIVE"]
                    prompt_parts = active_files + [user_prompt]
                    
                    response = client.models.generate_content(
                        model='gemini-1.5-pro',
                        contents=prompt_parts
                    )
                    st.markdown("### 📜 Báo cáo từ Đặc vụ:")
                    st.info(response.text)
                except Exception as e:
                    st.error(f"❌ Lỗi phản hồi: {e}")

# --- PHÒNG SỐ 2 & 3 ---
with tab2:
    st.header("Đôi Mắt X-Ray: Giải mã cấu trúc giá")
    st.info("Trạng thái: Chờ ráp thuật toán PineScript lượng hóa độ dốc (ATR).")

with tab3:
    st.header("Bàn Cờ Thực Chiến: Quản trị Rủi Ro & POE")
    st.info("Trạng thái: Chờ thiết lập logic từ Đặc vụ Roman.")
