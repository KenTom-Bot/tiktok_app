import streamlit as st
from st_copy_to_clipboard import st_copy_to_clipboard
from google import genai
from google.genai import types
from PIL import Image
import json
import os
import time

st.set_page_config(page_title="TikTok AI Video Suite Pro", page_icon="🎬", layout="wide")

# CSS tối ưu di động và định dạng tiêu đề
st.markdown("""
<style>
    .main-title { font-size: 1.5rem !important; font-weight: 800; color: #1e1e1e; margin-bottom: 0.5rem; }
    .stExpander { border-radius: 8px !important; margin-bottom: 8px !important; }
    button[kind="primary"], button[kind="secondary"] { width: 100% !important; border-radius: 8px !important; }
    .stCodeBlock { margin-top: -6px !important; margin-bottom: 8px !important; }
</style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))

if not api_key:
    st.error("Chưa cấu hình GEMINI_API_KEY trong Advanced settings -> Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

if "product_analysis" not in st.session_state:
    st.session_state.product_analysis = None
if "all_scripts" not in st.session_state:
    st.session_state.all_scripts = []

SYSTEM_INSTRUCTIONS = """
BẠN LÀ CHUYÊN GIA SẢN XUẤT VIDEO REVIEW TIKTOK SHOP ĐỈNH CAO, ĐẠO DIỄN HÌNH ẢNH CHO IMAGEN 3/VEO 3 VÀ GIÁM ĐỐC LỒNG TIẾNG.

1. TUÂN THỦ CHÍNH SÁCH TIKTOK SHOP:
   - Giá bán: Tuyệt đối không dùng giá số, chỉ dùng từ đời thường ('vài chục', 'cốc trà đá', 'deal hời góc trái').
   - Từ ngữ cấm: Cấm tuyệt đối 'cam kết', 'chữa dứt điểm', 'vĩnh viễn', '100%'.
   - Trẻ em: Phụ huynh luôn xuất hiện thao tác, cấm trẻ em đứng một mình.
   - Sức khỏe/Người lớn tuổi: Hướng vào thư giãn hoặc con cái báo hiếu cha mẹ. Cấm cận cảnh mụn nhọt, vết thương, răng sâu, cử chỉ đau đớn.

2. QUY CHUẨN ĐỒNG NHẤT GIỌNG ĐỌC & TÍCH HỢP PROMPT:
   - Giọng đọc: 100% tiếng Việt miền Bắc chuẩn Hà Nội. Bắt buộc nêu rõ: Giới tính (Nam/Nữ) và Độ tuổi phù hợp bối cảnh. Đồng nhất 100% âm sắc, nhịp điệu từ phân cảnh 1 đến 4.
   - TÍCH HỢP THOẠI VÀO PROMPT VEO 3: Trong 'video_prompt', bắt buộc tích hợp toàn bộ lời thoại tiếng Việt có dấu kèm hướng dẫn khẩu hình, biểu cảm gương mặt (hào hứng, ngạc nhiên, tin cậy) và hành vi cơ thể (tay cầm chắc chắn, chỉ ngón tay vào điểm nổi bật).
   - Tối đa 1 bàn tay người lớn tương tác, chống mọc tay thừa. Màn hình sạch, không chữ nổi, không logo, không watermark.

3. LOẠI HÌNH PHÂN CẢNH:
   - 'transition_type': Nhận diện chính xác là 'Cắt cảnh (Hard Cut)' hoặc 'Cảnh nối tiếp (Continuous Motion)'.
   - Nếu là 'Cảnh nối tiếp (Continuous Motion)': 'image_prompt' PHẢI để giá trị rỗng ("") vì cảnh này sẽ lấy ảnh cuối của video trước.
   - Nếu là 'Cắt cảnh (Hard Cut)': 'image_prompt' là prompt tiếng Anh chi tiết cho Imagen 3 (tỷ lệ 9:16) tạo ảnh thiết lập bối cảnh mới.

Mỗi kịch bản gồm 4 phân cảnh (8s/phân cảnh, tổng thời lượng 32-35s). Xuất kết quả dưới định dạng JSON hợp lệ duy nhất.
"""

st.markdown('<div class="main-title">🎬 Hệ Thống Kịch Bản TikTok Shop Đa Năng</div>', unsafe_allow_html=True)
st.write("Tải ảnh sản phẩm để tự động phân tích chi tiết và xuất kịch bản chuyển đổi cao.")

uploaded_files = st.file_uploader(
    "Tải các góc ảnh sản phẩm (Mặt trước, mặt sau, bao bì, phụ kiện):",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if uploaded_files:
    images = [Image.open(f) for f in uploaded_files]
    cols = st.columns(min(len(images), 4))
    for idx, img in enumerate(images):
        cols[idx % 4].image(img, caption=f"Góc {idx+1}", use_container_width=True)

    col_btn1, col_btn2 = st.columns(2)

    # Nút 1: Khởi tạo 5 kịch bản ban đầu
    with col_btn1:
        if st.button("🚀 Bắt Đầu Tạo 5 Kịch Bản Toàn Diện", use_container_width=True, type="primary"):
            with st.spinner("Đang phân tích chuyên sâu và thiết lập 5 kịch bản..."):
                prompt = """
                Hãy phân tích các ảnh này và xuất JSON gồm:
                1. 'product_analysis':
                   - category: Ngành hàng chi tiết
                   - target_audience: Chân dung khách hàng
                   - core_pain_points: 3 nỗi đau lớn nhất
                   - hero_color: Màu sắc chủ đạo
                   - materials_build: Chi tiết chất liệu, phom dáng, cổng cắm
                   - included_accessories: Danh sách phụ kiện
                   - key_usp: Điểm bán hàng độc nhất (USP)
                2. 'scripts': 5 KỊCH BẢN ĐỘC LẬP:
                   - Kịch bản 1: Giải quyết nỗi đau / Phiền toái thực tế
                   - Kịch bản 2: Trực quan tính năng / Thử nghiệm thực tế
                   - Kịch bản 3: Đập hộp & Quà tặng gia đình tiện ích
                   - Kịch bản 4: So sánh trước & sau khi sử dụng
                   - Kịch bản 5: Góc nhìn tiêu dùng thông minh / Bắt trend
                   Mỗi kịch bản gồm:
                   - script_title: Tên kịch bản in đậm tính chuyển đổi
                   - voice_profile: {gender: 'Nam'/'Nữ', age_range: 'Độ tuổi cụ thể', tone_description: 'Mô tả ngữ điệu'}
                   - scenes: 4 phân cảnh. Mỗi cảnh gồm:
                     + scene_number: Thứ tự (1-4)
                     + duration: '8s'
                     + transition_type: 'Cắt cảnh (Hard Cut)' hoặc 'Cảnh nối tiếp (Continuous Motion)'
                     + voice_director_vn: Phân tích tiếng Việt chi tiết gồm: Giọng đọc (Nam/Nữ, độ tuổi), Tốc độ (nhanh/chậm), Biểu cảm ngữ điệu và Từ khóa cần nhấn giọng.
                     + voiceover_vi: Lời thoại tiếng Việt chuẩn miền Bắc
                     + image_prompt: Prompt Imagen 3 (để rỗng "" nếu là Cảnh nối tiếp)
                     + video_prompt: Prompt Veo 3 tích hợp đầy đủ lời thoại tiếng Việt có dấu, mô tả biểu cảm gương mặt, ngôn ngữ hình thể và chuyển động điện ảnh.
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
                            st.error(f"Lỗi kết nối: {e}")
                            break

    # Nút Nhân bản 5 kịch bản Win
    with col_btn2:
        if st.session_state.all_scripts:
            script_titles = [f"{i+1}. {sc.get('script_title')}" for i, sc in enumerate(st.session_state.all_scripts)]
            selected_idx = st.selectbox("Chọn kịch bản Win cần nhân bản:", range(len(script_titles)), format_func=lambda x: script_titles[x])
            if st.button("🔥 Nhân Bản Thành 5 Kịch Bản Win Mới", use_container_width=True):
                with st.spinner("Đang nhân bản thành 5 biến thể A/B testing giữ nguyên cấu trúc win..."):
                    win_script = st.session_state.all_scripts[selected_idx]
                    prompt_clone = f"""
                    Dựa trên kịch bản win: {json.dumps(win_script, ensure_ascii=False)}
                    Hãy tạo ĐÚNG 5 BIẾN THỂ NHÂN BẢN MỚI (A/B testing):
                    - Giữ nguyên cấu trúc logic win nhưng biến hóa 5 cách mở đầu (Hook) và góc quay camera Veo 3 khác nhau để test tệp.
                    - Tích hợp lời thoại tiếng Việt có dấu và biểu cảm hình thể trực tiếp vào video_prompt.
                    - Xuất đúng JSON chứa key 'scripts' với 5 kịch bản đầy đủ.
                    """
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            response = client.models.generate_content(
                                model="gemini-3.6-flash",
                                contents=[*images, prompt_clone],
                                config=types.GenerateContentConfig(
                                    system_instruction=SYSTEM_INSTRUCTIONS,
                                    response_mime_type="application/json",
                                ),
                            )
                            clone_data = json.loads(response.text)
                            st.session_state.all_scripts.extend(clone_data.get("scripts", []))
                            st.rerun()
                            break
                        except Exception as e:
                            if "503" in str(e) and attempt < max_retries - 1:
                                time.sleep(3)
                                continue
                            else:
                                st.error(f"Lỗi: {e}")
                                break

# Hiển thị Phân tích sản phẩm
if st.session_state.product_analysis:
    st.divider()
    st.markdown("### 🔍 **Phân tích sản phẩm chi tiết**")
    p = st.session_state.product_analysis
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Ngành hàng:** {p.get('category', 'N/A')}")
        st.markdown(f"**Màu nhận diện (Hero Color):** {p.get('hero_color', 'N/A')}")
        st.markdown(f"**Lợi thế độc nhất (USP):** {p.get('key_usp', 'N/A')}")
        st.markdown(f"**Chân dung khách hàng:** {p.get('target_audience', 'N/A')}")
    with c2:
        st.markdown(f"**Chất liệu & Phom dáng:** {p.get('materials_build', 'N/A')}")
        st.markdown(f"**Phụ kiện đi kèm:** {', '.join(p.get('included_accessories', [])) if isinstance(p.get('included_accessories'), list) else p.get('included_accessories', 'N/A')}")
        st.markdown("**Nỗi đau khách hàng cần giải quyết:**")
        for pain in p.get('core_pain_points', []):
            st.markdown(f"- {pain}")

# Hiển thị Danh sách Kịch bản dạng List Accordion
if st.session_state.all_scripts:
    st.divider()
    st.markdown(f"### 📑 **Danh sách {len(st.session_state.all_scripts)} kịch bản sản xuất** *(Bấm để xem chi tiết)*")

    for idx, sc_item in enumerate(st.session_state.all_scripts):
        title = sc_item.get("script_title", f"Kịch bản {idx+1}")
        with st.expander(f"📌 **{idx+1}. {title.upper()}**", expanded=False):
            vp = sc_item.get("voice_profile", {})
            st.info(f"🎙️ **Đồng nhất giọng đọc:** Giọng **{vp.get('gender', 'Nữ')} miền Bắc**, độ tuổi **{vp.get('age_range', '25-30 tuổi')}** | *{vp.get('tone_description', 'Tự nhiên, tốc độ 1.15x')}*")

            for scene in sc_item.get("scenes", []):
                sc_num = scene.get("scene_number", 1)
                trans_type = scene.get("transition_type", "Cắt cảnh (Hard Cut)")
                st.markdown(f"#### **📍 Phân cảnh {sc_num} ({scene.get('duration', '8s')}) — [ {trans_type} ]**")

                # 1. Đạo diễn giọng đọc
                st.markdown("**🎙️ Đạo diễn giọng đọc:**")
                st.write(scene.get("voice_director_vn", f"Giọng {vp.get('gender', 'Nữ')} miền Bắc, tốc độ 1.15x, nhấn nhá tự nhiên."))

                # 2. Lời thoại
                st.markdown("**💬 Lời thoại lồng tiếng (100% Miền Bắc):**")
                st.markdown(f"> *\"{scene.get('voiceover_vi', '')}\"*")

                # 3. Prompt Tạo Ảnh
                st.markdown("**🖼️ Prompt Tạo Ảnh Gốc (Imagen 3 - 9:16):**")
                if "nối tiếp" in trans_type.lower() or not scene.get("image_prompt"):
                    st.warning("👉 **Lấy ảnh cuối của video trước làm ảnh đầu vào cho phân cảnh này.**")
                else:
                    st.code(scene.get("image_prompt", ""), language="text")
                    st_copy_to_clipboard(scene.get("image_prompt", ""), "📋 Copy Prompt Ảnh (Imagen 3)")

                # 4. Prompt Chuyển Động Veo 3
                st.markdown(f"**🎥 Prompt Chuyển Động Video ({trans_type} - Veo 3):**")
                st.code(scene.get("video_prompt", ""), language="text")
                st_copy_to_clipboard(scene.get("video_prompt", ""), "📋 Copy Prompt Video (Veo 3)")

                st.markdown("---")

    # Nút Tạo thêm 5 kịch bản ở dưới cùng danh sách
    st.markdown("#### ➕ **Mở Rộng Thêm Kịch Bản Mới**")
    if st.button("➕ Tạo Thêm 5 Kịch Bản Mới Khác Biệt", use_container_width=True):
        with st.spinner("Đang tư duy thêm 5 góc tiếp cận mới lạ..."):
            cur_len = len(st.session_state.all_scripts)
            prompt_more = f"""
            Dựa trên sản phẩm này, hãy tạo thêm ĐÚNG 5 KỊCH BẢN MỚI HOÀN TOÀN không trùng lặp với {cur_len} kịch bản trước:
            - Đặt tiêu đề: 'Kịch bản {cur_len + 1}: ...' đến 'Kịch bản {cur_len + 5}: ...'
            - Tích hợp lời thoại tiếng Việt có dấu và biểu cảm trực tiếp vào video_prompt.
            - Trả về JSON key 'scripts' chứa 5 kịch bản mới này.
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
                    more_data = json.loads(response.text)
                    st.session_state.all_scripts.extend(more_data.get("scripts", []))
                    st.rerun()
                    break
                except Exception as e:
                    if "503" in str(e) and attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    else:
                        st.error(f"Lỗi: {e}")
                        break
