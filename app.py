import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import json
import os
import time

st.set_page_config(page_title="TikTok AI Video Suite Pro", page_icon="🎬", layout="wide")

api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))

if not api_key:
    st.error("Chưa cấu hình GEMINI_API_KEY trong Advanced settings -> Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# Khởi tạo bộ nhớ tạm để lưu danh sách kịch bản
if "product_analysis" not in st.session_state:
    st.session_state.product_analysis = None
if "all_scripts" not in st.session_state:
    st.session_state.all_scripts = []

SYSTEM_INSTRUCTIONS = """
BẠN LÀ CHUYÊN GIA SẢN XUẤT VIDEO REVIEW TIKTOK SHOP, VIRTUAL DIRECTOR CHO IMAGEN 3/VEO 3 VÀ GIÁM ĐỐC LỒNG TIẾNG (VOICE DIRECTOR).

Quy tắc bắt buộc:
1. Tuân thủ TikTok Shop: Không nhắc giá số cụ thể, dùng từ ngữ tự nhiên ('vài chục', 'cốc trà đá', 'deal hời góc trái'). Tuyệt đối không dùng từ cam kết tuyệt đối ('chữa dứt điểm', 'vĩnh viễn', '100%').
2. Ngành hàng nhạy cảm:
   - Trẻ em: Phụ huynh luôn xuất hiện thao tác, cấm trẻ em đứng một mình.
   - Sức khỏe/Người cao tuổi: Hướng vào thư giãn, nhẹ nhõm hoặc con cái báo hiếu cha mẹ.
   - Bộ lọc an toàn: Cấm cận cảnh mụn nhọt, vết thương, răng sâu, cử chỉ đau đớn dữ dội.
3. Kỹ thuật hình ảnh & Chống lỗi AI:
   - Khóa cứng màu nhận diện (Hero Color), kết cấu cơ khí, cổng sạc, tem mác từ ảnh gốc.
   - 'image_prompt' (Imagen 3): Tỷ lệ 9:16, phom dáng chuẩn xác, ánh sáng studio/lifestyle điện ảnh.
   - 'video_prompt' (Veo 3): Điều khiển chuyển động camera, thao tác tay mượt mà. Tối đa 1 bàn tay người lớn tương tác, chống mọc tay thừa. Màn hình sạch, không chữ nổi/watermark.
4. Voiceover & Phân tích đạo diễn âm thanh (Voice Director Analysis):
   - Giọng đọc: Phát thanh viên miền Bắc chuẩn Hà Nội, tự nhiên, cuốn hút.
   - 'voice_direction': Bắt buộc phân tích chi tiết:
     + Tốc độ: Nhanh dồn dập (1.2x), vừa phải đĩnh đạc (1.1x) hay nhịp chậm nhấn nhá (1.0x).
     + Biểu cảm: Hào hứng bắt trend, chân thật chia sẻ, hay thì thầm bí mật kích thích tò mò.
     + Nhấn nhá & Ngắt nhịp: Chỉ định rõ từ khóa cần gằn giọng/nhấn mạnh và vị trí ngắt hơi để khớp nhịp chuyển cảnh.

Mỗi kịch bản gồm 4 phân cảnh (8s/phân cảnh, tổng thời lượng 32-35s).
Định dạng trả về duy nhất là chuỗi JSON hợp lệ không bọc markdown.
"""

st.title("🎬 Bộ Công Cụ Sản Xuất Video TikTok Shop Đa Kịch Bản & Voice Director")
st.write("Tự động bóc tách sản phẩm, tạo 5 kịch bản chuyển đổi cao kèm Prompt Imagen 3, Veo 3 và chỉ đạo giọng đọc chi tiết.")

uploaded_files = st.file_uploader(
    "Tải các góc ảnh sản phẩm (Mặt trước, mặt sau, bao bì, phụ kiện):",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if uploaded_files:
    images = [Image.open(f) for f in uploaded_files]
    cols = st.columns(min(len(images), 4))
    for idx, img in enumerate(images):
        cols[idx % 4].image(img, caption=f"Góc ảnh {idx+1}", use_container_width=True)

    col_btn1, col_btn2 = st.columns([1, 1])

    # Nút 1: Khởi tạo 5 kịch bản đầu tiên
    with col_btn1:
        if st.button("🚀 Bắt Đầu Tạo 5 Kịch Bản Toàn Diện", use_container_width=True):
            with st.spinner("Đang bóc tách giải phẫu và sáng tạo 5 kịch bản chuyển đổi..."):
                prompt = """
                Hãy phân tích các góc ảnh này và xuất đúng định dạng JSON gồm:
                - product_analysis: category, hero_color, key_features.
                - scripts: ĐÚNG 5 KỊCH BẢN độc lập:
                  1. Kịch bản 1: Giải quyết nỗi đau / Đập tan phiền toái (Pain-Point Focus).
                  2. Kịch bản 2: Trực quan tính năng / Thử nghiệm thực tế (Feature Demo / ASMR).
                  3. Kịch bản 3: Đập hộp & Quà tặng báo hiếu gia đình (Unboxing & Lifestyle).
                  4. Kịch bản 4: So sánh trước & sau khi dùng (Before & After Transformation).
                  5. Kịch bản 5: Góc nhìn tiêu dùng thông minh / Bắt trend (Smart Consumer & Trending Hook).
                Mỗi kịch bản gồm 4 scenes (scene_number, duration: '8s', image_prompt, video_prompt, voiceover_vi, voice_direction).
                Trong đó 'voice_direction' nêu rõ: Tốc độ đọc, Sắc thái biểu cảm, Từ khóa cần nhấn mạnh và Nhịp ngắt hơi.
                """
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=[*images, prompt],
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_INSTRUCTIONS,
                                response_mime_type="application/json",
                            ),
                        )
                        data = json.loads(response.text)
                        st.session_state.product_analysis = data.get("product_analysis", {})
                        st.session_state.all_scripts = data.get("scripts", [])
                        break
                    except Exception as e:
                        if "503" in str(e) and attempt < max_retries - 1:
                            time.sleep(3)
                            continue
                        else:
                            st.error(f"Lỗi: {e}")
                            break

    # Nút 2: Gọi thêm kịch bản mới
    with col_btn2:
        if st.session_state.all_scripts:
            if st.button("➕ Tạo Thêm 2 Kịch Bản Mới Khác Biệt", use_container_width=True):
                with st.spinner("Đang tư duy thêm các góc tiếp cận mới lạ..."):
                    current_count = len(st.session_state.all_scripts)
                    prompt_more = f"""
                    Dựa trên sản phẩm này, hãy tạo thêm 2 KỊCH BẢN MỚI HOÀN TOÀN không trùng lặp với {current_count} kịch bản trước:
                    - Đặt tiêu đề: 'Kịch bản {current_count + 1}: ...' và 'Kịch bản {current_count + 2}: ...'
                    - Định dạng JSON trả về chỉ gồm danh sách 'scripts' chứa 2 kịch bản mới (mỗi kịch bản 4 scenes: image_prompt, video_prompt, voiceover_vi, voice_direction).
                    """
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            response = client.models.generate_content(
                                model="gemini-3.6-flash",
                                contents=[*images, prompt_more],
                                config=types.GenerateContentConfig(
                                    system_instruction=SYSTEM_INSTRUCTIONS,
                                    response_mime_type="application/json",
                                ),
                            )
                            new_data = json.loads(response.text)
                            st.session_state.all_scripts.extend(new_data.get("scripts", []))
                            break
                        except Exception as e:
                            if "503" in str(e) and attempt < max_retries - 1:
                                time.sleep(3)
                                continue
                            else:
                                st.error(f"Lỗi: {e}")
                                break

# Hiển thị dữ liệu
if st.session_state.all_scripts:
    st.success(f"✅ Hiện có {len(st.session_state.all_scripts)} kịch bản đã sẵn sàng sản xuất!")

    if st.session_state.product_analysis:
        analysis = st.session_state.product_analysis
        st.subheader("🔍 Giải phẫu sản phẩm")
        st.write(f"**Ngành hàng:** {analysis.get('category', 'N/A')}")
        st.write(f"**Màu sắc nhận diện (Hero Color):** {analysis.get('hero_color', 'N/A')}")
        st.write("**Đặc điểm nổi bật:**", ", ".join(analysis.get("key_features", [])))

    st.divider()
    st.subheader(f"📑 Danh sách {len(st.session_state.all_scripts)} kịch bản chi tiết")

    tab_titles = [sc.get("script_title", f"Kịch bản {i+1}") for i, sc in enumerate(st.session_state.all_scripts)]
    tabs = st.tabs(tab_titles)

    for t_idx, tab in enumerate(tabs):
        with tab:
            current_script = st.session_state.all_scripts[t_idx]
            for sc in current_script.get("scenes", []):
                with st.expander(f"📍 Phân cảnh {sc.get('scene_number')} ({sc.get('duration')})", expanded=True):
                    # Khung 1: Prompt Tạo Ảnh (có nút copy góc phải của khung code)
                    st.markdown("**1. Prompt Tạo Ảnh Gốc (Imagen 3 - Tỷ lệ 9:16):**")
                    st.code(sc.get('image_prompt', ''), language="text")

                    # Khung 2: Prompt Chuyển Động Veo 3
                    st.markdown("**2. Prompt Chuyển Động Video (Veo 3 Image-to-Video):**")
                    st.code(sc.get('video_prompt', ''), language="text")

                    # Khung 3: Lời thoại
                    st.markdown(f"**3. Lời thoại lồng tiếng (Voiceover):**")
                    st.code(sc.get('voiceover_vi', ''), language="text")

                    # Khung 4: Chỉ đạo diễn xuất giọng đọc
                    st.markdown("**🎙️ Phân tích giọng đọc (Audio Director Guidelines):**")
                    st.info(sc.get('voice_direction', 'Giọng miền Bắc tự nhiên, tốc độ 1.15x, nhấn nhá từ khóa sản phẩm.'))
