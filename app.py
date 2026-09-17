import streamlit as st
import streamlit.components.v1 as components
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

# Quản lý Session State
if "product_analysis" not in st.session_state:
    st.session_state.product_analysis = None
if "all_scripts" not in st.session_state:
    st.session_state.all_scripts = []

def copy_button_ui(text_to_copy: str, button_label: str = "📋 Sao chép"):
    """Tạo nút copy bằng JavaScript 1 chạm với trạng thái Copied"""
    escaped_text = json.dumps(text_to_copy)
    html_code = f"""
    <div style="margin: 4px 0 10px 0;">
        <button id="btn_{hash(text_to_copy) % 1000000}" onclick='
            navigator.clipboard.writeText({escaped_text}).then(() => {{
                var b = document.getElementById("btn_{hash(text_to_copy) % 1000000}");
                var oldText = b.innerText;
                b.innerText = "✅ Đã sao chép!";
                b.style.backgroundColor = "#2e7d32";
                b.style.borderColor = "#2e7d32";
                setTimeout(() => {{
                    b.innerText = oldText;
                    b.style.backgroundColor = "#ff4b4b";
                    b.style.borderColor = "#ff4b4b";
                }}, 2000);
            }});
        ' style="
            background-color: #ff4b4b;
            color: white;
            border: 1px solid #ff4b4b;
            padding: 6px 14px;
            font-size: 13px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        ">{button_label}</button>
    </div>
    """
    components.html(html_code, height=45)

SYSTEM_INSTRUCTIONS = """
BẠN LÀ CHUYÊN GIA SẢN XUẤT VIDEO REVIEW TIKTOK SHOP ĐỈNH CAO, ĐẠO DIỄN HÌNH ẢNH CHO IMAGEN 3/VEO 3 VÀ GIÁM ĐỐC LỒNG TIẾNG (VOICE DIRECTOR).

1. TUÂN THỦ CHÍNH SÁCH TIKTOK SHOP TOÀN DIỆN (MỌI NGÀNH HÀNG):
   - Giá bán: Tuyệt đối không dùng giá số, chỉ dùng từ đời thường tự nhiên ('vài chục', 'cốc trà đá', 'bát phở', 'deal hời góc trái').
   - Từ ngữ cấm: Cấm tuyệt đối 'cam kết', 'chữa dứt điểm', 'vĩnh viễn', '100%', 'hiệu quả ngay tức thì'.
   - Trẻ em: Phụ huynh luôn thao tác, không bao giờ để trẻ em xuất hiện đơn độc trước ống kính.
   - Sức khỏe/Người lớn tuổi: Hướng vào cảm giác thư giãn, nhẹ nhõm hoặc con cái báo hiếu cha mẹ.
   - Bộ lọc an toàn: Cấm cận cảnh mụn nhọt, vết thương, răng sâu, cử chỉ đau đớn dữ dội.

2. KỸ THUẬT HÌNH ẢNH & THẨM MỸ (IMAGEN 3 & VEO 3):
   - Màn hình sạch: Không text overlay, không sub, không logo nổi, không watermark.
   - Bảng màu & kết cấu: Khóa chặt Hero Color, kết cấu cơ khí, tem mác, phụ kiện từ ảnh sản phẩm.
   - Chống dị tật AI: Tối đa 1 bàn tay người lớn tương tác khi cầm/thao tác sản phẩm để chống mọc thừa tay.
   - Chuyển cảnh rõ ràng: Mỗi scene phải nêu rõ 'transition_type': 'Cảnh nối tiếp (Continuous Motion)' hoặc 'Cắt cảnh (Hard Cut)'.
     + Prompt Imagen 3 (image_prompt): Tỷ lệ 9:16, ánh sáng studio/lifestyle điện ảnh chuẩn phom dáng sản phẩm.
     + Prompt Veo 3 (video_prompt): Điều khiển chuyển động camera và hành vi nhân vật mượt mà, tương thích đúng loại chuyển cảnh.

3. KHÓA GIỌNG ĐỌC ĐỒNG NHẤT 100% MIỀN BẮC (VOICEOVER LOCK):
   - Thiết lập cụ thể cho cả kịch bản: Giới tính (Nam/Nữ), Độ tuổi phù hợp tình huống (ví dụ: Nam 24 tuổi năng động, Nữ 30 tuổi mẹ bỉm ấm áp).
   - Đồng nhất: Toàn bộ 4 phân cảnh PHẢI giữ nguyên cùng 1 giọng đọc, cùng ngữ điệu và cao độ.
   - 'voice_direction': Nêu chi tiết tốc độ (1.1x - 1.2x), biểu cảm, từ khóa cần nhấn nhá và vị trí ngắt nghỉ.

Mỗi kịch bản gồm 4 phân cảnh (8s/phân cảnh, tổng thời lượng 32-35s). Định dạng trả về duy nhất là JSON hợp lệ.
"""

st.title("🎬 PHẦN MỀM PHÂN TÍCH SẢN PHẨM VÀ TẠO KỊCH BẢN VIDEO")
st.write("Tự động phân tích sản phẩm, xuất 5 kịch bản chuyển đổi cao, hỗ trợ nhân bản kịch bản win và gọi thêm kịch bản liên tục.")

uploaded_files = st.file_uploader(
    "Tải các góc ảnh sản phẩm (Mọi ngành nghề: mặt trước, sau, chi tiết, phụ kiện):",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if uploaded_files:
    images = [Image.open(f) for f in uploaded_files]
    cols = st.columns(min(len(images), 4))
    for idx, img in enumerate(images):
        cols[idx % 4].image(img, caption=f"Góc ảnh {idx+1}", use_container_width=True)

    col1, col2 = st.columns(2)

    # Nút 1: Khởi tạo 5 kịch bản ban đầu
    with col1:
        if st.button("🚀 Bắt Đầu Tạo 5 Kịch Bản Toàn Diện", use_container_width=True):
            with st.spinner("Đang phân tích chuyên sâu sản phẩm và thiết lập 5 kịch bản..."):
                prompt = """
                Hãy phân tích các góc ảnh này và xuất JSON gồm:
                1. 'product_analysis':
                   - category: Tên ngành hàng chi tiết
                   - target_audience: Chân dung khách hàng mục tiêu
                   - core_pain_points: 3 nỗi đau lớn nhất của khách hàng
                   - hero_color: Màu sắc nhận diện chủ đạo
                   - materials_build: Chi tiết chất liệu, phom dáng và cổng cắm/nút bấm
                   - included_accessories: Danh sách phụ kiện bóc tách được
                   - key_usp: Điểm bán hàng độc nhất (USP)
                2. 'scripts': 5 KỊCH BẢN KHÁC NHAU:
                   - Kịch bản 1: Đánh vào nỗi đau / Đập tan phiền toái (Pain-Point Hook)
                   - Kịch bản 2: Trực quan tính năng / Thử thách thực tế (Feature Demo / ASMR)
                   - Kịch bản 3: Đập hộp & Quà tặng tiện ích gia đình (Unboxing / Lifestyle)
                   - Kịch bản 4: So sánh trước & sau khi dùng (Before & After)
                   - Kịch bản 5: Góc nhìn tiêu dùng thông minh / Bắt trend (Trending & Smart Value)
                   Mỗi kịch bản có:
                   - script_title: Tên kịch bản
                   - voice_profile: {gender: 'Nam'/'Nữ', age_range: 'Độ tuổi cụ thể', tone_description: 'Mô tả âm sắc'}
                   - scenes: 4 scenes (scene_number, duration: '8s', transition_type: 'Cảnh nối tiếp (Continuous Motion)' hoặc 'Cắt cảnh (Hard Cut)', image_prompt, video_prompt, voiceover_vi, voice_direction).
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

    # Nút 2: Tạo thêm 5 kịch bản mới
    with col2:
        if st.session_state.all_scripts:
            if st.button("➕ Tạo Thêm 5 Kịch Bản Mới Khác Biệt", use_container_width=True):
                with st.spinner("Đang tư duy thêm 5 góc tiếp cận mới lạ..."):
                    current_count = len(st.session_state.all_scripts)
                    prompt_more = f"""
                    Dựa trên sản phẩm này, hãy tạo thêm ĐÚNG 5 KỊCH BẢN MỚI HOÀN TOÀN không trùng lặp với {current_count} kịch bản trước:
                    - Đặt tiêu đề: 'Kịch bản {current_count + 1}: ...' đến 'Kịch bản {current_count + 5}: ...'
                    - Giữ nguyên cấu trúc: voice_profile (100% giọng Bắc, độ tuổi theo ngữ cảnh, khóa đồng nhất), transition_type, image_prompt, video_prompt, voiceover_vi, voice_direction.
                    - Định dạng JSON trả về chỉ gồm danh mục 'scripts' chứa 5 kịch bản mới này.
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

# Hiển thị kết quả Phân tích sản phẩm
if st.session_state.product_analysis:
    st.divider()
    st.subheader("🔍 Phân tích sản phẩm chi tiết")
    p = st.session_state.product_analysis

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**Ngành hàng:** {p.get('category', 'N/A')}")
        st.markdown(f"**Màu sắc nhận diện (Hero Color):** {p.get('hero_color', 'N/A')}")
        st.markdown(f"**Lợi thế độc nhất (USP):** {p.get('key_usp', 'N/A')}")
    with c2:
        st.markdown(f"**Chân dung khách hàng:** {p.get('target_audience', 'N/A')}")
        st.markdown(f"**Chất liệu & Phom dáng:** {p.get('materials_build', 'N/A')}")
    with c3:
        st.markdown("**Nỗi đau khách hàng:**")
        for pain in p.get('core_pain_points', []):
            st.markdown(f"- {pain}")
        st.markdown(f"**Phụ kiện đi kèm:** {', '.join(p.get('included_accessories', [])) if isinstance(p.get('included_accessories'), list) else p.get('included_accessories', 'N/A')}")

# Hiển thị danh sách Kịch bản & Nhân bản kịch bản Win
if st.session_state.all_scripts:
    st.divider()
    st.subheader(f"📑 Danh sách {len(st.session_state.all_scripts)} kịch bản sẵn sàng sản xuất")

    # Khu vực Nhân bản kịch bản Win
    with st.expander("⭐ NHÂN BẢN KỊCH BẢN WIN (Tạo 3 biến thể A/B Testing từ kịch bản hiệu quả cao)", expanded=False):
        script_titles = [f"{i+1}. {sc.get('script_title')}" for i, sc in enumerate(st.session_state.all_scripts)]
        selected_script_idx = st.selectbox("Chọn kịch bản win bạn muốn nhân bản:", range(len(script_titles)), format_func=lambda x: script_titles[x])
        
        if st.button("🔥 Nhân Bản 3 Biến Thể Mới Từ Kịch Bản Này"):
            with st.spinner("Đang phát triển 3 biến thể A/B Testing giữ nguyên cấu trúc win..."):
                winning_script = st.session_state.all_scripts[selected_script_idx]
                prompt_clone = f"""
                Dựa trên kịch bản win được chọn sau đây:
                {json.dumps(winning_script, ensure_ascii=False)}
                
                Hãy tạo ĐÚNG 3 BIẾN THỂ NHÂN BẢN MỚI (A/B Testing variations):
                - Giữ nguyên ưu điểm bán hàng và logic kịch bản win nhưng thay đổi 3 giây đầu (Hook), cách giật tít, và góc máy chuyển động của Veo 3 để test nhiều tệp khách hàng.
                - Đặt tên: 'Biến thể Win A: ...', 'Biến thể Win B: ...', 'Biến thể Win C: ...'
                - Trả về JSON gồm key 'scripts' chứa 3 kịch bản mới này với đầy đủ các trường: voice_profile, transition_type, image_prompt, video_prompt, voiceover_vi, voice_direction.
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
                            st.error(f"Lỗi nhân bản: {e}")
                            break

    # Hiển thị các Tab kịch bản
    tab_titles = [sc.get("script_title", f"Kịch bản {i+1}") for i, sc in enumerate(st.session_state.all_scripts)]
    tabs = st.tabs(tab_titles)

    for t_idx, tab in enumerate(tabs):
        with tab:
            current_script = st.session_state.all_scripts[t_idx]
            v_prof = current_script.get("voice_profile", {})
            
            # Khung thông số giọng đọc khóa đồng nhất
            st.info(f"🎙️ **Hồ sơ giọng đọc đồng nhất 100% miền Bắc:** Giới tính: **{v_prof.get('gender', 'Nữ')}** | Độ tuổi: **{v_prof.get('age_range', '25-30 tuổi')}** | Phong cách: *{v_prof.get('tone_description', 'Tự nhiên, tốc độ 1.15x, năng động')}*")

            for sc in current_script.get("scenes", []):
                with st.expander(f"📍 Phân cảnh {sc.get('scene_number')} ({sc.get('duration')}) — [ {sc.get('transition_type', 'Cắt cảnh (Hard Cut)')} ]", expanded=True):
                    
                    # 1. Prompt Tạo Ảnh (Imagen 3)
                    st.markdown("**1. Prompt Tạo Ảnh Gốc (Imagen 3 - Tỷ lệ 9:16):**")
                    st.code(sc.get('image_prompt', ''), language="text")
                    copy_button_ui(sc.get('image_prompt', ''), "📋 Copy Prompt Ảnh (Imagen 3)")

                    # 2. Prompt Chuyển Động Veo 3
                    st.markdown(f"**2. Prompt Chuyển Động Video ({sc.get('transition_type', 'Cắt cảnh')} - Veo 3):**")
                    st.code(sc.get('video_prompt', ''), language="text")
                    copy_button_ui(sc.get('video_prompt', ''), "📋 Copy Prompt Video (Veo 3)")

                    # 3. Lời thoại
                    st.markdown("**3. Lời thoại lồng tiếng (Voiceover 100% Miền Bắc):**")
                    st.code(sc.get('voiceover_vi', ''), language="text")
                    copy_button_ui(sc.get('voiceover_vi', ''), "📋 Copy Lời Thoại")

                    # 4. Chỉ đạo diễn xuất giọng đọc
                    st.markdown("**🎙️ Đạo diễn giọng đọc (Voice Director & Nhấn nhá):**")
                    st.caption(sc.get('voice_direction', 'Giọng chuẩn miền Bắc, nhấn nhá điểm nổi bật.'))
                    copy_button_ui(sc.get('voice_direction', ''), "📋 Copy Hướng Dẫn Giọng Đọc")
