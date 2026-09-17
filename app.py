import io
import json
import os
import subprocess
from google import genai
from google.genai import types
from PIL import Image
import streamlit as st

# CẤU HÌNH GIAO DIỆN WEB
st.set_page_config(
    page_title='TikTok Shop AI Video Generator', page_icon='🎬', layout='wide'
)
st.title('🎬 Hệ Thống Tự Động Sản Xuất Video TikTok Shop với Veo 3')
st.caption(
    'Tải ảnh sản phẩm lên -> Tự động phân tích giải phẫu, lập kịch bản, tạo'
    ' ảnh Master và render video 35-40s.'
)

# KẾT NỐI GEMINI API
gemini_key = st.secrets.get('GEMINI_API_KEY', '')
if not gemini_key:
  st.warning('⚠️ Vui lòng cấu hình GEMINI_API_KEY trong mục Secrets của App!')

client = genai.Client(api_key=gemini_key) if gemini_key else None

SYSTEM_INSTRUCTIONS = """
BẠN LÀ CHUYÊN GIA BIÊN TẬP KỊCH BẢN TIKTOK SHOP & KỸ SƯ PROMPT AI (IMAGE & VEO 3 VIDEO) ĐẠT CHUẨN CHUYỂN ĐỔI CAO.
NHIỆM VỤ: Chuyển đổi thông tin, hình ảnh giải phẫu sản phẩm thành gói sản xuất video ngắn TikTok Shop (35-40s) hoàn chỉnh, trực quan, tuân thủ chính sách và tối ưu cho công cụ tạo ảnh cùng Veo 3 Image-to-Video. Áp dụng chuẩn xác cho 100% mọi nhóm sản phẩm vật lý.

I. NGUYÊN TẮC CHÍNH SÁCH & BỘ LỌC AN TOÀN:
- Không nói giá số trực tiếp (dùng từ: vài chục, bằng cốc trà đá, deal hời góc trái).
- Cấm từ tuyệt đối: cam kết, chữa dứt điểm, vĩnh viễn, rẻ nhất, 100%.
- Trẻ em: Luôn để phụ huynh/người lớn thao tác, cấm trẻ em xuất hiện đơn độc.
- Sức khỏe & Người già: Cấm từ ngữ y tế (chữa bệnh, điều trị, dứt điểm). Dùng từ trải nghiệm: hỗ trợ thư giãn, nhẹ nhõm, đỡ mỏi hẳn. Nhân vật người già hoặc con cái trưởng thành mua báo hiếu.
- Bộ lọc an toàn: Cấm cử chỉ đau đớn dữ dội (ôm đầu quằn quại, ôm lưng nhăn nhó). Cấm cận cảnh mụn viêm, răng sâu, vết cắt đứt tay.

II. QUY CHUẨN KỸ THUẬT:
- Khóa màu sắc & vật liệu (Hero Color), khóa cứng cấu trúc cơ học nút bấm, cổng cắm, quai xách.
- Bảo toàn nguyên vẹn 100% tem họa tiết, chữ in trên thân vỏ, phụ kiện và lớp đệm bên trong.
- CẤM mọi loại chữ phụ đề nổi (no on-screen text overlays, no subtitles, no video graphics, no watermarks, no icons).
- Chống mọc tay thừa: Cảnh tương tác chỉ định 'A single adult hand enters from the side'.

BẮT BUỘC ĐẦU RA LÀ ĐỊNH DẠNG JSON THUẦN TÚY CÓ CẤU TRÚC SAU:
{
  "scenario_name": "Tên kịch bản",
  "hero_color": "Chuỗi từ khóa tiếng Anh khóa màu sắc",
  "hardware_lock": "Chuỗi từ khóa tiếng Anh khóa nút bấm/cơ khí",
  "shots": [
    {
      "shot_id": 1,
      "type": "HARD_CUT",
      "duration": 6,
      "master_image_prompt": "Prompt tiếng Anh 9:16 tạo ảnh Master Shot độc lập không có tay thừa",
      "veo_prompt": "Prompt tiếng Anh mô tả chuyển động camera cho Veo 3. Voiceover Track: Exactly the same native Northern Vietnamese narrator voice (standard Hanoi broadcast accent, consistent timbre and 1.15x pace). Flawless Vietnamese pronunciation with natural emphatic stress on key words: 'lời thoại tiếng Việt viết thường có dấu', synced natural speech cadence, authentic ambient sounds."
    },
    {
      "shot_id": 2,
      "type": "CONTINUITY",
      "duration": 6,
      "master_image_prompt": "",
      "veo_prompt": "Prompt tiếng Anh chuyển động nối tiếp cho Veo 3. Voiceover Track: Exactly the same native Northern Vietnamese narrator voice (standard Hanoi broadcast accent, consistent timbre and 1.15x pace). Flawless Vietnamese pronunciation with natural emphatic stress on key words: 'lời thoại tiếng Việt viết thường có dấu', synced natural speech cadence, authentic ambient sounds."
    }
  ]
}
"""


def analyze_product_to_json(image):
  response = client.models.generate_content(
      model='gemini-2.5-flash',
      contents=[
          image,
          (
              'Hãy phân tích sản phẩm này và xuất gói kịch bản hoàn chỉnh định'
              ' dạng JSON.'
          ),
      ],
      config=types.GenerateContentConfig(
          system_instruction=SYSTEM_INSTRUCTIONS,
          response_mime_type='application/json',
      ),
  )
  return json.loads(response.text)


# GIAO DIỆN NGƯỜI DÙNG
uploaded_file = st.file_uploader(
    'Tải ảnh sản phẩm của bạn lên đây (Mọi ngành hàng):',
    type=['jpg', 'jpeg', 'png'],
)

if uploaded_file and client:
  image = Image.open(uploaded_file)
  st.image(image, caption='Ảnh sản phẩm gốc', width=300)

  if st.button('🚀 Bắt Đầu Tạo Video Tự Động'):
    with st.spinner(
        'Đang bóc tách giải phẫu sản phẩm và lập kịch bản tự động...'
    ):
      try:
        script_data = analyze_product_to_json(image)
        st.success(
            f"🎉 Đã lập xong kịch bản: {script_data.get('scenario_name')}"
        )

        with st.expander('Xem chi tiết các Shot và Prompt chuẩn hóa'):
          st.json(script_data)

        st.info(
            'Hệ thống đã sẵn sàng điều phối Imagen và Veo để xuất video hoàn'
            ' chỉnh!'
        )
      except Exception as e:
        st.error(f'Đã xảy ra lỗi: {e}')