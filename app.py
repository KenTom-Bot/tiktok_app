import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from PIL import Image
import json
import base64
import os
import time

st.set_page_config(page_title="TikTok AI Video Suite Pro", page_icon="🎬", layout="wide")

st.markdown("""
<style>
    .main-title { font-size: 1.55rem !important; font-weight: 800; color: #1e1e1e; margin-bottom: 0.5rem; }
    .stExpander { border-radius: 8px !important; margin-bottom: 8px !important; }
    button[kind="primary"], button[kind="secondary"] { width: 100% !important; border-radius: 8px !important; }
    .stCodeBlock { margin-top: -6px !important; margin-bottom: 4px !important; }
    .badge-pending { color: #d97706; font-weight: 700; background: #fef3c7; padding: 2px 8px; border-radius: 4px; }
    .badge-ready { color: #15803d; font-weight: 700; background: #dcfce7; padding: 2px 8px; border-radius: 4px; }
    .badge-dynamic { color: #1e40af; font-weight: 700; background: #dbeafe; padding: 2px 8px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))

if not api_key:
    st.error("Chưa cấu hình GEMINI_API_KEY trong Advanced settings -> Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# Quản lý Session State
if "product_analysis" not in st.session_state:
    st.session_state.product_analysis = None
if "script_outlines" not in st.session_state:
    st.session_state.script_outlines = []
if "generated_details" not in st.session_state:
    st.session_state.generated_details = {}
if "active_script_id" not in st.session_state:
    st.session_state.active_script_id = None

def safe_copy_button(text_to_copy: str, button_label: str = "📋 Copy Prompt"):
    b64_content = base64.b64encode(text_to_copy.encode('utf-8')).decode('utf-8')
    btn_id = f"copy_btn_{abs(hash(text_to_copy)) % 1000000}"
    html_code = f"""
    <div style="margin: 4px 0 10px 0;">
        <button id="{btn_id}" onclick='
            const text = decodeURIComponent(escape(atob("{b64_content}")));
            navigator.clipboard.writeText(text).then(() => {{
                const btn = document.getElementById("{btn_id}");
                const old = btn.innerText;
                btn.innerText = "✅ Đã sao chép!";
                btn.style.backgroundColor = "#2e7d32";
                setTimeout(() => {{
                    btn.innerText = old;
                    btn.style.backgroundColor = "#ff4b4b";
                }}, 2000);
            }});
        ' style="
            background-color: #ff4b4b;
            color: white;
            border: none;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            width: 100%;
            max-width: 280px;
        ">{button_label}</button>
    </div>
    """
    components.html(html_code, height=48)

def clean_and_parse_json(text_content: str):
    cleaned = text_content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())

SYSTEM_INSTRUCTIONS = """
BẠN LÀ BẬC THẦY SẢN XUẤT VIDEO VIRAL VÀ TĂNG CHUYỂN ĐỔI TIKTOK SHOP, TỔNG ĐẠO DIỄN VIRTUAL CHO IMAGEN 3 VÀ VEO 3.

I. QUY CHUẨN THỜI LƯỢNG PHÂN CẢNH (PACING & RETENTION PROTOCOL):
- Mốc thời lượng được phép: 4s, 6s, 8s, 10s.
- ƯU TIÊN CHỦ YẾU LÀ 4s, 6s, 8s:
  + 4s: Cực kỳ hiệu quả cho Hook 3-4s đầu giữ chân (giật tít, cảnh báo, bắt cận điểm nóng) hoặc chuyển cảnh chuyển tiếp nhanh.
  + 6s & 8s: Thời lượng vàng cho biểu diễn tính năng sản phẩm, thao tác công thái học thực tế, phản lực môi trường, bối cảnh xưởng/showroom.
- KHÓA CỨNG MỐC 10s: Mỗi kịch bản TỐI ĐA CHỈ ĐƯỢC DÙNG 1 ĐẾN 2 CẢNH 10s (chỉ dành riêng cho phân cảnh tổng kết giải pháp phức tạp hoặc đại cảnh kho xưởng/showroom chốt deal CTA mạnh mẽ).

II. ĐỘ CHUẨN XÁC VẬT LÝ & GIẢI PHẪU CƠ KHÍ:
1. Giải phẫu chi tiết: Khóa chặt hình dạng, màu nhận diện (Hero Color), kết cấu bề mặt, vị trí/số lượng nút nguồn, lẫy khóa, cổng sạc, và phụ kiện đi kèm theo đúng ảnh gốc.
2. Thao tác cơ học thực tế: Cầm, nắm, cắm đầu nối, xoay ngàm khóa chuẩn công thái học. Chỉ tối đa 1 bàn tay người lớn tương tác, chống mọc thừa tay.
3. KHÍ ĐỘNG HỌC THỰC TẾ (MÁY THỔI, HÚT, SẤY):
   - Tuyệt đối cấm tạo luồng gió thành tia laser, tia lửa, khói đặc hay vệt nước chảy.
   - Luồng khí phải là không khí trong suốt áp lực cao ("invisible high-velocity transparent air stream").
   - Thể hiện sức mạnh luồng gió qua phản lực môi trường: bụi mịn bay tung tóe tức thì, mảnh vụn/giấy tờ bay phần phật rõ rệt.

III. BỐI CẢNH TĂNG UY TÍN:
- Với kịch bản Deal hời, Siêu Sale, Review thực tế: Đặt bối cảnh quay tại PHÂN XƯỞNG SẢN XUẤT (dây chuyền tấp nập, thùng hàng xuất khẩu), KHO BÃI hoặc SHOWROOM TRƯNG BÀY để tạo lòng tin tuyệt đối.

IV. ĐỒNG NHẤT GIỌNG ĐỌC & TÍCH HỢP PROMPT:
- Giọng 100% miền Bắc chuẩn Hà Nội, nêu rõ Giới tính (Nam/Nữ) và Độ tuổi phù hợp bối cảnh, đồng nhất suốt các cảnh.
- 'video_prompt': Tích hợp lời thoại tiếng Việt có dấu, biểu cảm gương mặt và ngôn ngữ hình thể.
- Màn hình sạch (no text, no watermark, no logo).
- 'transition_type': 'Cắt cảnh (Hard Cut)' hoặc 'Cảnh nối tiếp (Continuous Motion)'. Nếu là nối tiếp thì 'image_prompt' để rỗng ("").
"""

st.markdown('<div class="main-title">🎬 Hệ Thống Kịch Bản TikTok Shop Đa Năng</div>', unsafe_allow_html=True)
st.write("Tự động bóc tách cơ khí sản phẩm, tối ưu nhịp độ (4s, 6s, 8s - hạn chế 10s) và tạo kịch bản viral chuyển đổi cao.")

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

    if st.button("🚀 Bắt Đầu Phân Tích Cơ Khí & Đề Xuất 5 Ý Tưởng Kịch Bản", type="primary", use_container_width=True):
        with st.spinner("Đang bóc tách chi tiết cơ khí và phân tích góc tiếp cận viral..."):
            prompt = """
            Phân tích toàn diện sản phẩm từ ảnh và xuất JSON:
            1. 'product_analysis':
               - category: Ngành hàng chi tiết
               - target_audience: Chân dung khách hàng mục tiêu
               - core_pain_points: 3 nỗi đau lớn nhất của khách
               - hero_color: Màu nhận diện chủ đạo và chất liệu bề mặt
               - mechanical_details: Chi tiết chính xác về vị trí công tắc, số nút bấm, ngàm xoay, cổng cắm, cơ chế hoạt động thực tế
               - included_accessories: Danh sách phụ kiện bóc tách được từ ảnh
               - aerodynamics_or_action_notes: Lưu ý vật lý đặc thù (luồng khí trong suốt, lực cắm khớp)
               - key_usp: Điểm bán hàng độc nhất (USP)
            2. 'script_outlines': ĐÚNG 5 Ý TƯỞNG KỊCH BẢN (chỉ phác thảo khung):
               - id: 1 đến 5
               - title: Tên kịch bản giật tít, hấp dẫn
               - setting_style: Bối cảnh chính (Phân xưởng sản xuất, Kho hàng tấp nập, Showroom, Không gian thực tế)
               - angle: Góc tiếp cận chuyển đổi (Deal xưởng/Siêu Sale, Giải quyết nỗi đau, Demo tính năng ASMR, So sánh trước sau, Unboxing bảo hành)
               - target_hook: Ý tưởng câu hook 3-4s đầu
               - recommended_scenes_count: Phân bổ nhịp cảnh đề xuất (ví dụ: '4 cảnh (4s-6s-8s-8s)', '4 cảnh (4s-6s-8s-10s)')
               - voice_profile: {gender: 'Nam'/'Nữ', age_range: 'Độ tuổi', tone: 'Âm điệu miền Bắc'}
            """
            try:
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[*images, prompt],
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTIONS,
                        response_mime_type="application/json",
                        temperature=0.7,
                    ),
                )
                data = clean_and_parse_json(response.text)
                st.session_state.product_analysis = data.get("product_analysis", {})
                st.session_state.script_outlines = data.get("script_outlines", [])
                st.session_state.generated_details = {}
                st.session_state.active_script_id = None
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi khởi tạo: {e}")

# Hiển thị Phân tích sản phẩm
if st.session_state.product_analysis:
    st.divider()
    st.markdown("### 🔍 **Phân tích sản phẩm chi tiết & Cơ khí thực tế**")
    p = st.session_state.product_analysis
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Ngành hàng:** {p.get('category', 'N/A')}")
        st.markdown(f"**Màu nhận diện & Bề mặt:** {p.get('hero_color', 'N/A')}")
        st.markdown(f"**Lợi thế độc nhất (USP):** {p.get('key_usp', 'N/A')}")
        st.markdown(f"**Chân dung khách hàng:** {p.get('target_audience', 'N/A')}")
        st.markdown(f"**Chi tiết cơ khí & Nút bấm:** {p.get('mechanical_details', 'N/A')}")
    with c2:
        st.markdown(f"**Phụ kiện đi kèm:** {', '.join(p.get('included_accessories', [])) if isinstance(p.get('included_accessories'), list) else p.get('included_accessories', 'N/A')}")
        st.markdown(f"**Lưu ý vật lý thao tác:** {p.get('aerodynamics_or_action_notes', 'N/A')}")
        st.markdown("**Nỗi đau khách hàng:**")
        for pain in p.get('core_pain_points', []):
            st.markdown(f"- {pain}")

# Hiển thị Danh sách các Kịch bản đề xuất
if st.session_state.script_outlines:
    st.divider()
    st.markdown(f"### 📋 **Danh sách {len(st.session_state.script_outlines)} ý tưởng kịch bản tối ưu chuyển đổi**")
    st.write("Bấm **'Tạo chi tiết kịch bản này'** để AI tự động phân bổ nhịp cảnh (chủ yếu 4s, 6s, 8s; mốc 10s tối đa 1-2 cảnh).")

    for outline in st.session_state.script_outlines:
        sc_id = outline.get("id")
        is_generated = sc_id in st.session_state.generated_details
        
        col_info, col_act = st.columns([3, 1])
        with col_info:
            status_badge = '<span class="badge-ready">ĐÃ CÓ CHI TIẾT</span>' if is_generated else '<span class="badge-pending">CHƯA TẠO CHI TIẾT</span>'
            pacing_badge = f'<span class="badge-dynamic">{outline.get("recommended_scenes_count", "Động học")}</span>'
            st.markdown(f"**{outline.get('id')}. {outline.get('title')}** — {status_badge} {pacing_badge}", unsafe_allow_html=True)
            st.caption(f"🏭 **Bối cảnh:** {outline.get('setting_style', 'Thực tế')} | 🎯 **Góc độ:** {outline.get('angle')} | ⚡ **Hook:** *\"{outline.get('target_hook')}\"*")
        
        with col_act:
            btn_label = "👁️ Xem chi tiết" if is_generated else "✨ Tạo chi tiết kịch bản này"
            if st.button(btn_label, key=f"btn_gen_{sc_id}", use_container_width=True):
                if not is_generated:
                    with st.spinner(f"Đang phân bổ nhịp cảnh (4s, 6s, 8s) và dựng prompt chi tiết cho '{outline.get('title')}'..."):
                        vp = outline.get("voice_profile", {})
                        prompt_detail = f"""
                        Dựa trên sản phẩm cơ khí chuẩn xác và ý tưởng sau:
                        - Tiêu đề: {outline.get('title')}
                        - Bối cảnh chủ đạo: {outline.get('setting_style')}
                        - Góc độ: {outline.get('angle')}
                        - Hook: {outline.get('target_hook')}
                        - Giọng đọc: {vp.get('gender', 'Nữ')} miền Bắc, tuổi {vp.get('age_range', '25-30')}

                        QUY ĐỊNH THỜI LƯỢNG NGHIÊM NGẶT:
                        - 'duration' của mỗi cảnh CHỈ ĐƯỢC LÀ một trong các mốc: '4s', '6s', '8s', '10s'.
                        - CHỦ YẾU SỬ DỤNG: '4s' (Hook/chuyển cảnh), '6s' và '8s' (demo tính năng, cơ khí, bối cảnh xưởng/showroom, thao tác thực tế).
                        - MỐC '10s': TOÀN BỘ KỊCH BẢN TỐI ĐA CHỈ ĐƯỢC XUẤT HIỆN 1 ĐẾN 2 CẢNH (ưu tiên cho cảnh chốt deal CTA cuối hoặc biểu diễn tổng thể phức tạp).
                        - Máy thổi/hút: Luồng khí là không khí trong suốt áp lực cao, không tia lửa/vệt sáng. Thể hiện lực qua bụi bay tung tóe, giấy bay phần phật.
                        - 'video_prompt': Tích hợp nguyên văn lời thoại tiếng Việt có dấu và biểu cảm diễn xuất.

                        Định dạng JSON:
                        {{
                          "id": {sc_id},
                          "title": "{outline.get('title')}",
                          "setting_style": "{outline.get('setting_style')}",
                          "voice_profile": {json.dumps(vp, ensure_ascii=False)},
                          "total_estimated_duration": "Ví dụ: 24s (4s+6s+6s+8s)",
                          "scenes": [
                            {{
                              "scene_number": 1,
                              "duration": "4s",
                              "transition_type": "Cắt cảnh (Hard Cut)",
                              "voice_director_vn": "Chỉ đạo diễn xuất giọng đọc tiếng Việt",
                              "voiceover_vi": "Lời thoại tiếng Việt miền Bắc",
                              "image_prompt": "Prompt Imagen 3 9:16 (để rỗng nếu là Cảnh nối tiếp)",
                              "video_prompt": "Prompt Veo 3 chi tiết thao tác cơ học, bối cảnh xưởng/showroom, khí động học trong suốt, tích hợp thoại tiếng Việt"
                            }}
                          ]
                        }}
                        """
                        try:
                            res = client.models.generate_content(
                                model="gemini-3.6-flash",
                                contents=[*images, prompt_detail],
                                config=types.GenerateContentConfig(
                                    system_instruction=SYSTEM_INSTRUCTIONS,
                                    response_mime_type="application/json",
                                    max_output_tokens=8192,
                                    temperature=0.7,
                                ),
                            )
                            detail_data = clean_and_parse_json(res.text)
                            st.session_state.generated_details[sc_id] = detail_data
                            st.session_state.active_script_id = sc_id
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi tạo chi tiết: {e}")
                else:
                    st.session_state.active_script_id = sc_id
                    st.rerun()

# HIỂN THỊ KỊCH BẢN CHI TIẾT ĐANG CHỌN
if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details:
    st.divider()
    active_script = st.session_state.generated_details[st.session_state.active_script_id]
    vp = active_script.get("voice_profile", {})
    
    st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {active_script.get('title').upper()}**")
    st.info(f"⏱️ **Tổng thời lượng:** **{active_script.get('total_estimated_duration', '24s')}** ({len(active_script.get('scenes', []))} phân cảnh) | 🏭 **Bối cảnh:** {active_script.get('setting_style', 'Thực tế')} | 🎙️ **Giọng:** **{vp.get('gender', 'Nữ')} miền Bắc ({vp.get('age_range', '25-30')})** - *{vp.get('tone', 'Tự nhiên')}*")

    for scene in active_script.get("scenes", []):
        sc_num = scene.get("scene_number", 1)
        trans_type = scene.get("transition_type", "Cắt cảnh (Hard Cut)")
        dur = scene.get("duration", "6s")
        st.markdown(f"#### **📍 Phân cảnh {sc_num} ({dur}) — [ {trans_type} ]**")

        st.markdown("**🎙️ Đạo diễn giọng đọc:**")
        st.write(scene.get("voice_director_vn", ""))

        st.markdown("**💬 Lời thoại lồng tiếng (100% Miền Bắc):**")
        st.markdown(f"> *\"{scene.get('voiceover_vi', '')}\"*")

        st.markdown("**🖼️ Prompt Tạo Ảnh Gốc (Imagen 3 - 9:16):**")
        if "nối tiếp" in trans_type.lower() or not scene.get("image_prompt"):
            st.warning("👉 **Lấy ảnh cuối của video trước làm ảnh đầu vào cho phân cảnh này.**")
        else:
            img_p = scene.get("image_prompt", "")
            st.code(img_p, language="text")
            safe_copy_button(img_p, "📋 Copy Prompt Ảnh (Imagen 3)")

        st.markdown(f"**🎥 Prompt Chuyển Động Video ({trans_type} - Veo 3):**")
        vid_p = scene.get("video_prompt", "")
        st.code(vid_p, language="text")
        safe_copy_button(vid_p, "📋 Copy Prompt Video (Veo 3)")

        st.markdown("---")

    # KHU VỰC NHẮC LẠI KỊCH BẢN CHƯA TẠO & NHÂN BẢN KỊCH BẢN WIN PHÍA DƯỚI
    st.markdown("### ⚡ **Bước Tiếp Theo: Nhân Bản Win & Khai Thác Kịch Bản Khác**")
    col_win, col_unmade = st.columns(2)

    with col_win:
        st.markdown("#### 🔥 **Nhân Bản Kịch Bản Này Thành 5 Bản Win (A/B Test)**")
        st.caption("Giữ nguyên cấu trúc chốt đơn và cơ khí nhưng đổi mới 5 cách giật Hook và bối cảnh xưởng/showroom.")
        if st.button("🚀 Nhân Bản 5 Biến Thể Win Ngay", type="primary", use_container_width=True):
            with st.spinner("Đang nhân bản thành 5 biến thể A/B testing..."):
                prompt_clone = f"""
                Dựa trên kịch bản win chi tiết sau: {json.dumps(active_script, ensure_ascii=False)}
                Hãy tạo ĐÚNG 5 BIẾN THỂ WIN MỚI:
                - Biến hóa 5 cách mở đầu (Hook 3-4s) và bối cảnh (chuyển đổi linh hoạt giữa phân xưởng sản xuất, kho hàng bận rộn và showroom sang trọng).
                - Phân bổ số phân cảnh kết hợp thời lượng chủ yếu 4s, 6s, 8s (mốc 10s chỉ tối đa 1-2 cảnh).
                - Xuất JSON gồm 'cloned_outlines' chứa 5 ý tưởng biến thể (id mới tiếp theo, title, setting_style, angle, target_hook, recommended_scenes_count, voice_profile).
                """
                try:
                    res_clone = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=[*images, prompt_clone],
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTIONS,
                            response_mime_type="application/json",
                            temperature=0.7,
                        ),
                    )
                    clone_data = clean_and_parse_json(res_clone.text)
                    cloned_list = clone_data.get("cloned_outlines", [])
                    cur_len = len(st.session_state.script_outlines)
                    for i, cl in enumerate(cloned_list):
                        cl["id"] = cur_len + i + 1
                    st.session_state.script_outlines.extend(cloned_list)
                    st.success("✅ Đã nhân bản thêm 5 kịch bản win vào danh sách!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi nhân bản: {e}")

    with col_unmade:
        st.markdown("#### ⏳ **Các Kịch Bản Khác Chưa Tạo Chi Tiết**")
        unmade_scripts = [sc for sc in st.session_state.script_outlines if sc.get("id") not in st.session_state.generated_details]
        
        if unmade_scripts:
            for unsc in unmade_scripts:
                st.markdown(f"- **{unsc.get('id')}. {unsc.get('title')}** (*Bối cảnh: {unsc.get('setting_style', 'Thực tế')}*)")
            st.info("👆 Bạn có thể cuộn lên danh sách ở trên và bấm 'Tạo chi tiết' cho kịch bản mong muốn bất cứ lúc nào.")
        else:
            st.success("🎉 Bạn đã tạo chi tiết cho toàn bộ các kịch bản trong danh sách!")
