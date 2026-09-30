import streamlit as st
from google import genai
from google.genai import types
import os
import time

# ==============================================================================
# CẤU HÌNH GIAO DIỆN APP ĐỘC LẬP
# ==============================================================================
st.set_page_config(
    page_title="Direct Media Studio - Imagen 3 & Veo",
    page_icon="🎨",
    layout="wide"
)

st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem !important;
        font-weight: 900 !important;
        background: linear-gradient(90deg, #2563eb 0%, #db2777 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem !important;
    }
    .sub-title {
        font-size: 1.05rem !important;
        color: #475569 !important;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🎨 Direct AI Media Studio (Imagen 3 & Veo)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Ứng dụng độc lập chuyên thử nghiệm kết xuất trực tiếp Ảnh và Video từ API thương mại.</div>', unsafe_allow_html=True)

# Lấy API Key từ Streamlit Secrets hoặc biến môi trường
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
if not api_key:
    st.error("⚠️ Chưa cấu hình khóa GEMINI_API_KEY trong phần cấu hình bảo mật (Secrets) của Streamlit.")
    st.stop()

# Khởi tạo client chuẩn cho Google GenAI SDK
client = genai.Client(api_key=api_key)

# ==============================================================================
# CÁC HÀM GỌI API TRỰC TIẾP
# ==============================================================================
def generate_image(prompt_text, aspect_ratio):
    try:
        # Gọi trực tiếp Imagen 3 qua SDK
        result = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt_text,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio=aspect_ratio
            )
        )
        for generated_image in result.generated_images:
            return generated_image.image.image_bytes
    except Exception as e:
        st.error(f"Lỗi kết nối Imagen API: {e}")
    return None

def generate_video(image_bytes, video_prompt_text):
    try:
        # Gọi trực tiếp Veo qua SDK
        operation = client.models.generate_videos(
            model='veo-2.0-generate-001',
            prompt=video_prompt_text,
            image=types.Image.from_bytes(data=image_bytes),
            config=types.GenerateVideosConfig(
                fps=24,
                duration_seconds=5
            )
        )
        while not operation.done:
            time.sleep(10)
            operation = client.operations.get(operation)
        
        video_result = operation.response
        return video_result.generated_videos[0].video.video_bytes
    except Exception as e:
        st.error(f"Lỗi kết nối Veo API: {e}")
    return None

# ==============================================================================
# GIAO DIỆN LÀM VIỆC CHIA ĐÔI (SPLIT-SCREEN WORKSPACE)
# ==============================================================================
col_tab1, col_tab2 = st.columns(2, gap="large")

with col_tab1:
    st.markdown("### 🖼️ 1. Tạo Ảnh Tĩnh (Imagen 3)")
    img_prompt_input = st.text_area(
        "Nhập Prompt tiếng Anh miêu tả bức ảnh:",
        value="Cinematic shot, a modern minimalist desk setup with a sleek smartphone, warm lighting, 8k resolution, photorealistic",
        height=100
    )
    aspect_choice = st.selectbox("Chọn tỷ lệ khung hình ảnh:", ["9:16", "16:9"], index=0)
    
    if st.button("🎨 Tạo Ảnh Ngay", type="primary", use_container_width=True):
        if img_prompt_input.strip():
            with st.spinner("⏳ Đang kết nối Imagen 3 để vẽ ảnh..."):
                img_bytes = generate_image(img_prompt_input.strip(), aspect_choice)
                if img_bytes:
                    st.session_state["demo_img_bytes"] = img_bytes
                    st.success("✅ Tạo ảnh thành công!")
        else:
            st.warning("Vui lòng nhập prompt ảnh!")

    if "demo_img_bytes" in st.session_state:
        st.image(st.session_state["demo_img_bytes"], caption="Kết quả ảnh gốc", use_column_width=True)
        st.download_button(
            label="📥 Tải Ảnh Xuống (.jpg)",
            data=st.session_state["demo_img_bytes"],
            file_name="imagen_output.jpg",
            mime="image/jpeg",
            use_container_width=True
        )

with col_tab2:
    st.markdown("### 🎬 2. Tạo Video Chuyển Động (Veo)")
    vid_prompt_input = st.text_area(
        "Nhập Prompt tiếng Anh miêu tả chuyển động video:",
        value="Camera slowly pans forward, subtle lighting shifts, high quality cinematic motion",
        height=100
    )
    
    uploaded_ref_image = st.file_uploader("Hoặc tải lên ảnh tham chiếu tùy ý (Tùy chọn):", type=["jpg", "jpeg", "png"])
    
    if st.button("🚀 Render Video Veo Ngay", type="primary", use_container_width=True):
        # Lấy ảnh từ việc vừa tạo hoặc từ file tải lên
        source_bytes = None
        if uploaded_ref_image is not None:
            source_bytes = uploaded_ref_image.getvalue()
        elif "demo_img_bytes" in st.session_state:
            source_bytes = st.session_state["demo_img_bytes"]
            
        if source_bytes and vid_prompt_input.strip():
            with st.spinner("⏳ Đang kết nối Veo API để dựng video (Quá trình này mất khoảng 1-2 phút)..."):
                vid_bytes = generate_video(source_bytes, vid_prompt_input.strip())
                if vid_bytes:
                    st.session_state["demo_vid_bytes"] = vid_bytes
                    st.success("✅ Render video thành công!")
        else:
            st.warning("⚠️ Vui lòng tạo ảnh ở cột bên trái hoặc tải ảnh tham chiếu lên trước khi tạo video!")

    if "demo_vid_bytes" in st.session_state:
        st.video(st.session_state["demo_vid_bytes"])
        st.download_button(
            label="📥 Tải Video Xuống (.mp4)",
            data=st.session_state["demo_vid_bytes"],
            file_name="veo_output.mp4",
            mime="video/mp4",
            use_container_width=True
        )