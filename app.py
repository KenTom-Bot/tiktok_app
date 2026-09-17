import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import json
import os
import time

st.set_page_config(page_title="TikTok AI Video Generator", page_icon="🎬", layout="wide")

# Lấy API Key từ Secrets hoặc biến môi trường
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))

if not api_key:
    st.error("Chưa cấu hình GEMINI_API_KEY trong Advanced settings -> Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

SYSTEM_INSTRUCTIONS = """
BẠN LÀ CHUYÊN GIA SẢN XUẤT VIDEO REVIEW TIKTOK SHOP & VIRTUAL DIRECTOR CHO VEO 3.
Tuân thủ tuyệt đối các nguyên tắc:
1. Chính sách TikTok Shop: Tuyệt đối không nhắc giá số cụ thể, chỉ dùng từ đời thường ('vài chục', 'cốc trà đá', 'deal hời góc trái'). Không cam kết tuyệt đối (chữa dứt điểm, vĩnh viễn, 100%).
2. Ngành hàng nhạy cảm:
   - Trẻ em: Phụ huynh luôn xuất hiện thao tác, cấm trẻ em một mình.
   - Sức khỏe/Người già: Tránh từ y tế, hướng tới thư giãn hoặc con cái báo hiếu cha mẹ.
   - Bộ lọc an toàn: Cấm cận cảnh vết thương, mụn viêm, răng sâu, cử chỉ đau đớn dữ dội.
3. Đồng nhất giải phẫu & nhân vật:
   - Khóa cứng màu sắc chủ đạo (Hero Color), kết cấu cơ khí, cổng cắm, nhãn mác.
   - Thao tác tay: Tối đa 1 bàn tay người lớn xuất hiện từ cạnh viền, chống mọc thêm tay.
   - Màn hình sạch: Không gắn phụ đề nổi, logo đè, watermark vào prompt video.
4. Voiceover: Giọng phát thanh viên miền Bắc chuẩn Hà Nội, âm sắc đồng nhất, tốc độ 1.15x, tự nhiên.

Định dạng trả về duy nhất: Chuỗi JSON hợp lệ không bọc markdown:
{
  "product_analysis": {
    "category": "Tên ngành hàng",
    "hero_color": "Mã/Tên màu chính",
    "key_features": ["Đặc điểm 1", "Đặc điểm 2", "Đặc điểm 3"]
  },
  "scenes": [
    {
      "scene_number": 1,
      "duration": "8s",
      "visual_prompt": "Mô tả chi tiết góc quay, ánh sáng, thao tác điện ảnh cho Veo 3...",
      "voiceover_vi": "Lời bình thoại tiếng Việt chuẩn miền Bắc..."
    },
    {
      "scene_number": 2,
      "duration": "8s",
      "visual_prompt": "...",
      "voiceover_vi": "..."
    },
    {
      "scene_number": 3,
      "duration": "8s",
      "visual_prompt": "...",
      "voiceover_vi": "..."
    },
    {
      "scene_number": 4,
      "duration": "8s",
      "visual_prompt": "...",
      "voiceover_vi": "..."
    }
  ]
}
"""

st.title("🎬 Hệ Thống Tự Động Sản Xuất Video TikTok Shop với Veo 3")
st.write("Tải lên các góc ảnh sản phẩm để AI bóc tách giải phẫu và tạo kịch bản video chuẩn chính sách.")

uploaded_files = st.file_uploader(
    "Tải các góc ảnh sản phẩm lên đây (Mặt trước, mặt sau, chi tiết, bao bì):",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if uploaded_files:
    images = [Image.open(f) for f in uploaded_files]
    cols = st.columns(min(len(images), 4))
    for idx, img in enumerate(images):
        cols[idx % 4].image(img, caption=f"Góc ảnh {idx+1}", use_container_width=True)

    if st.button("🚀 Bắt Đầu Tạo Video Tự Động"):
        with st.spinner(f"Đang bóc tách giải phẫu {len(images)} góc ảnh và lập kịch bản tự động..."):
            max_retries = 3
            script_data = None
            last_err = None

            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=[
                            *images,
                            "Hãy đối chiếu toàn bộ các góc ảnh này để bóc tách giải phẫu sản phẩm chi tiết nhất và xuất gói kịch bản hoàn chỉnh định dạng JSON."
                        ],
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTIONS,
                            response_mime_type="application/json",
                        ),
                    )
                    script_data = json.loads(response.text)
                    break
                except Exception as e:
                    last_err = e
                    if "503" in str(e) and attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    else:
                        break

            if script_data:
                st.success("✅ Đã bóc tách giải phẫu và lên kịch bản thành công!")
                
                # Hiển thị thông tin giải phẫu
                st.subheader("🔍 Kết quả bóc tách sản phẩm")
                analysis = script_data.get("product_analysis", {})
                st.write(f"**Ngành hàng:** {analysis.get('category', 'N/A')}")
                st.write(f"**Màu sắc nhận diện (Hero Color):** {analysis.get('hero_color', 'N/A')}")
                st.write("**Đặc điểm nổi bật:**", ", ".join(analysis.get("key_features", [])))

                # Hiển thị từng phân cảnh kịch bản
                st.subheader("📋 Kịch bản 4 phân cảnh (32-35s)")
                for sc in script_data.get("scenes", []):
                    with st.expander(f"Phân cảnh {sc.get('scene_number')} ({sc.get('duration')})", expanded=True):
                        st.markdown(f"**Prompt cho Veo 3:** `{sc.get('visual_prompt')}`")
                        st.markdown(f"**Lời thoại miền Bắc:** *\"{sc.get('voiceover_vi')}\"*")
            else:
                st.error(f"Đã xảy ra lỗi: {last_err}")
