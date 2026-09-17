import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from PIL import Image
import json
import base64
import os
import re
import time
import io

st.set_page_config(page_title="KenTom AI Video Studio Pro", page_icon="🎬", layout="wide")

st.markdown("""
<style>
    .header-container {
        text-align: center;
        padding: 1.2rem 1rem 1.8rem 1rem;
        margin-bottom: 1rem;
        background: radial-gradient(circle, rgba(255,75,75,0.08) 0%, rgba(255,255,255,0) 70%);
        border-radius: 16px;
    }
    .main-title {
        font-size: 2.35rem !important;
        font-weight: 900 !important;
        background: linear-gradient(90deg, #ff0050 0%, #ff5252 50%, #ff7300 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem !important;
        line-height: 1.25 !important;
        letter-spacing: -0.5px;
    }
    .sub-title {
        font-size: 1.12rem !important;
        font-weight: 500 !important;
        color: #4a5568 !important;
        margin-top: 0.2rem;
    }
    .header-badge {
        display: inline-block;
        background: #fee2e2;
        color: #b91c1c;
        font-size: 0.8rem;
        font-weight: 800;
        padding: 3px 12px;
        border-radius: 9999px;
        margin-bottom: 0.5rem;
        letter-spacing: 0.5px;
        border: 1px solid #fca5a5;
    }
    
    /* --- PHÓNG TO TIÊU ĐỀ VÀ KHUNG CHỌN (SELECTBOX) --- */
    div[data-testid="stSelectbox"] label p {
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        color: #1e293b !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        min-height: 52px !important;
        background-color: #ffffff !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 10px !important;
    }
    /* ------------------------------------------------ */

    .custom-card {
        background: #ffffff;
        border: 1.5px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .card-title-win { color: #dc2626; font-weight: 800; font-size: 1.2rem; margin-bottom: 6px; }
    .card-title-add { color: #d97706; font-weight: 800; font-size: 1.2rem; margin-bottom: 6px; }
    .card-title-unmade { color: #2563eb; font-weight: 800; font-size: 1.2rem; margin-bottom: 6px; }
    
    div[data-testid="stButton"] > button {
        width: 100% !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        border: none !important;
        transition: all 0.25s ease-in-out !important;
    }
    div[data-testid="stButton"] > button[kind="secondary"] {
        background: linear-gradient(135deg, #ff4b4b 0%, #ff7300 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 3px 8px rgba(255, 75, 75, 0.35) !important;
        padding: 0.55rem 1rem !important;
    }
    div[data-testid="stButton"] > button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #e63946 0%, #e85d04 100%) !important;
        box-shadow: 0 5px 14px rgba(255, 75, 75, 0.5) !important;
        transform: translateY(-1px) !important;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #e63946 0%, #d90429 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 10px rgba(230, 57, 70, 0.4) !important;
        padding: 0.6rem 1rem !important;
    }
    .stCodeBlock { margin-top: -6px !important; margin-bottom: 4px !important; }
    .badge-pending { color: #d97706; font-weight: 700; background: #fef3c7; padding: 2px 8px; border-radius: 4px; }
    .badge-ready { color: #15803d; font-weight: 700; background: #dcfce7; padding: 2px 8px; border-radius: 4px; }
    .badge-dynamic { color: #1e40af; font-weight: 700; background: #dbeafe; padding: 2px 8px; border-radius: 4px; }
    @media (max-width: 768px) {
        .main-title { font-size: 1.65rem !important; }
        .sub-title { font-size: 0.95rem !important; }
        .header-container { padding: 0.8rem 0.5rem 1.2rem 0.5rem; }
    }
</style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
if not api_key:
    st.error("Chưa cấu hình GEMINI_API_KEY trong Advanced settings -> Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# Quản lý Session State
if "content_analysis" not in st.session_state:
    st.session_state.content_analysis = None
if "all_scripts" not in st.session_state:
    st.session_state.all_scripts = []
if "cloned_scripts" not in st.session_state:
    st.session_state.cloned_scripts = []
if "expanded_scripts" not in st.session_state:
    st.session_state.expanded_scripts = []
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
            background: linear-gradient(135deg, #ff4b4b 0%, #ff7300 100%);
            color: white;
            border: none;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 700;
            border-radius: 6px;
            cursor: pointer;
            width: 100%;
            max-width: 280px;
            box-shadow: 0 2px 6px rgba(255, 75, 75, 0.3);
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
    parsed = json.loads(cleaned.strip())
    if isinstance(parsed, list) and len(parsed) > 0:
        parsed = parsed[0]
    return parsed

def optimize_image_for_api(image: Image.Image, max_dimension: int = 896, quality: int = 85) -> Image.Image:
    img = image.convert("RGB") if image.mode != "RGB" else image.copy()
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True)
    buffer.seek(0)
    return Image.open(buffer)

def format_analysis_field(field_val) -> str:
    """Tự động định dạng và ngắt dòng rõ ràng theo các ý chính"""
    if isinstance(field_val, dict):
        return "<br>".join([f"• <b>{k.replace('_', ' ').title()}:</b> {v}" for k, v in field_val.items()])
    elif isinstance(field_val, list):
        return "<br>".join([f"• {item}" for item in field_val])
    
    text = str(field_val)
    keywords = ["Chức năng:", "Tài chính:", "Cảm xúc:", "Chức năng", "Tài chính", "Cảm xúc", "1.", "2.", "3."]
    for kw in keywords:
        if kw in text and not text.startswith(kw):
            text = text.replace(kw, f"<br>• <b>{kw}</b>")
    return text

def get_system_instructions(mode: str, style: str) -> str:
    base = r"""
BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL ĐA NĂNG CHO IMAGEN 3 VÀ VEO 3.
PHONG CÁCH KẾT XUẤT THỊ GIÁC: """ + style.upper() + r"""
MỌI PROMPT PHẢI TUÂN THEO ĐÚNG PHONG CÁCH NÀY.

QUY TẮC ĐẠO DIỄN & LỜI THOẠI BẮT BUỘC:
1. THỜI LƯỢNG MỖI CẢNH: CHỈ ĐƯỢC DÙNG 3 MỐC: 4s, 6s, 8s. TUYỆT ĐỐI CẤM DÙNG MỐC 10 GIÂY.
2. 100% CÁC PHÂN CẢNH ĐỀU PHẢI CÓ LỜI THOẠI (VOICEOVER): Đảm bảo mạch truyền tải thông tin liên tục, hấp dẫn.
3. QUY CHUẨN ĐỊNH MỨC TỪ VỰNG THEO THỜI LƯỢNG (Khớp hoàn hảo nhịp đọc thực tế, 1s = ~2.5 - 3 từ):
   - Cảnh 4s: Lời thoại tối đa 10 - 12 từ (Câu ngắn, gãy gọn, tập trung điểm nhấn).
   - Cảnh 6s: Lời thoại từ 15 - 18 từ (Mô tả hành động hoặc nỗi đau vừa đủ).
   - Cảnh 8s: Lời thoại từ 22 - 25 từ (Giải thích tính năng sâu hoặc CTA).
4. Giọng đọc: 100% tiếng Việt miền Bắc chuẩn Hà Nội, nêu rõ Giới tính và Độ tuổi phù hợp, đồng nhất suốt các cảnh.
5. Tích hợp thoại vào Veo 3: Trong 'video_prompt', nhúng nguyên văn lời thoại tiếng Việt có dấu kèm biểu cảm gương mặt, khẩu hình và cử chỉ cơ thể khớp với thời lượng.
6. Màn hình sạch: Tuyệt đối không text overlay, không sub nổi, không logo, không watermark.
"""
    if mode == "🛒 TikTok Shop & Bán Hàng":
        return base + r"""
CHẾ ĐỘ: TIKTOK SHOP & SẢN PHẨM CHUYỂN ĐỔI
- Khóa chặt giải phẫu cơ khí: Màu sắc Hero Color, chất liệu (nhám matte, nhựa ABS, kim loại), vị trí nút bấm, cổng sạc, danh sách phụ kiện đi kèm.
- Ma trận nỗi đau & mong muốn: Bóc tách rõ 3 tầng nỗi đau (Chức năng, Tài chính, Cảm xúc) và mong muốn cốt lõi của khách hàng.
- Vật lý siêu thực: Bụi/vụn rác bị hút xoáy thẳng vào buồng chứa trong suốt; hơi sương siêu mịn; vải đàn hồi hồi form ngay.
- Chính sách TikTok: Cấm giá cụ thể (chỉ dùng 'vài chục', 'cốc trà đá', 'deal hời giỏ hàng'); cấm từ ngữ tuyệt đối ('100%', 'khỏi hẳn'); tương tác tay chuẩn công thái học.
- 5 Kịch bản gốc bắt buộc tuân thủ 5 ma trận: 1. Phân xưởng/Kho hàng, 2. Showroom/Cửa hàng, 3. Deal xưởng/Trợ giá, 4. Nỗi đau đời sống, 5. Stress-test độ bền.
"""
    elif mode == "📺 TVC Quảng Cáo & Thương Hiệu Cao Cấp":
        return base + r"""
CHẾ ĐỘ: TVC QUẢNG CÁO ĐIỆN ẢNH & THƯƠNG HIỆU CAO CẤP
- Ngôn ngữ thị giác điện ảnh: Ánh sáng Dramatic Lighting, Rim Light, tương phản sắc nét, chuyển động máy nghệ thuật.
- Lời thoại cô đọng, giàu cảm xúc, kết thúc bằng Slogan hoặc Tagline định vị thương hiệu đẳng cấp.
"""
    else:
        return base + f"""
CHẾ ĐỘ CHUYÊN BIỆT: {mode}
- Khóa chặt không gian, bối cảnh, đặc tính cốt lõi và nhịp động học chân thật.
"""

def generate_with_smart_retry(contents, system_inst, max_tokens=16384):
    model_name = "gemini-3.6-flash"
    max_attempts = 6
    last_err = None

    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_inst,
                    response_mime_type="application/json",
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                ),
            )
            return clean_and_parse_json(response.text)
        except Exception as e:
            last_err = e
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                wait_match = re.search(r"retry in (\d+\.?\d*)s", err_msg)
                wait_sec = int(float(wait_match.group(1))) + 2 if wait_match else 35
                with st.spinner(f"⏳ Chạm hạn mức tạm thời. Đang chờ {wait_sec}s rồi tiếp tục..."):
                    time.sleep(wait_sec)
                continue
            elif "503" in err_msg or "UNAVAILABLE" in err_msg or "high demand" in err_msg:
                delay = 3 * (attempt + 1)
                with st.spinner(f"🔄 Máy chủ bận. Tự động kết nối lại lần {attempt + 1}/{max_attempts} sau {delay}s..."):
                    time.sleep(delay)
                continue
            else:
                break
    raise last_err

def create_scene_details_for_id(target_id: int, current_mode: str, current_style: str):
    all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_sources if isinstance(sc, dict) and sc.get("id") == target_id), None)
    
    if not outline:
        st.error(f"Không tìm thấy dữ liệu cho kịch bản ID #{target_id}. Vui lòng thử lại!")
        return
    
    with st.spinner(f"Đang dựng kịch bản chi tiết #{target_id} '{outline.get('title')}' theo phong cách {current_style}..."):
        vp = outline.get("voice_profile", {})
        if not isinstance(vp, dict):
            vp = {}
        analysis_info = json.dumps(st.session_state.content_analysis, ensure_ascii=False) if st.session_state.content_analysis else ""
        
        prompt_detail = f"""
        Dựa trên phân tích DNA đầu vào đã khóa chặt:
        {analysis_info}

        Ý tưởng kịch bản cần dựng chi tiết:
        - ID: {target_id}
        - Tiêu đề: {outline.get('title')}
        - Thể loại: {current_mode}
        - Phong cách thị giác: {current_style}
        - Bối cảnh chủ đạo: {outline.get('setting_style')}
        - Góc tiếp cận: {outline.get('angle')}
        - Hook: {outline.get('target_hook')}
        - Giọng đọc: {vp.get('gender', 'Nữ')} miền Bắc, tuổi {vp.get('age_range', '25-30')}

        QUY ĐỊNH KỸ THUẬT:
        1. 'image_prompt' (Imagen 3, 9:16): Tuân thủ phong cách {current_style}, khóa nhận diện nhân vật/bối cảnh/sản phẩm chuẩn xác. Để rỗng ("") nếu là Cảnh nối tiếp.
        2. 'video_prompt' (Veo 3): Động học siêu thực đúng thể loại, nhúng nguyên văn lời thoại tiếng Việt có dấu, khẩu hình và biểu cảm tự nhiên.
        3. THỜI LƯỢNG: 'duration' của mỗi cảnh CHỈ ĐƯỢC LÀ '4s', '6s' hoặc '8s' (TUYỆT ĐỐI CẤM 10s). Lời thoại phải khớp hoàn hảo nhịp đọc (1s = ~3 từ).

        Định dạng JSON chuẩn (BẮT BUỘC là 1 Dict):
        {{
          "id": {target_id},
          "title": "{outline.get('title')}",
          "setting_style": "{outline.get('setting_style')}",
          "voice_profile": {json.dumps(vp, ensure_ascii=False)},
          "total_estimated_duration": "Ví dụ: 24s (4s+6s+6s+8s)",
          "scenes": [
            {{
              "scene_number": 1,
              "duration": "4s",
              "scene_setting": "Mô tả bối cảnh không gian cụ thể cho cảnh 1",
              "transition_type": "Cắt cảnh (Hard Cut)",
              "voice_director_vn": "Chỉ đạo diễn xuất giọng đọc tiếng Việt",
              "voiceover_vi": "Lời thoại tiếng Việt miền Bắc",
              "image_prompt": "Prompt Imagen 3 9:16 khóa phong cách {current_style} (để rỗng nếu là Cảnh nối tiếp)",
              "video_prompt": "Prompt Veo 3 chi tiết động học, tích hợp thoại tiếng Việt"
            }}
          ]
        }}
        """
        try:
            sys_inst = get_system_instructions(current_mode, current_style)
            detail_data = generate_with_smart_retry([prompt_detail], sys_inst)
            if isinstance(detail_data, list) and len(detail_data) > 0:
                detail_data = detail_data[0]
            if not isinstance(detail_data, dict):
                st.error("Dữ liệu trả về chưa đúng định dạng Dict. Vui lòng bấm tạo lại!")
                return
            if "voice_profile" not in detail_data or not isinstance(detail_data["voice_profile"], dict):
                detail_data["voice_profile"] = vp

            st.session_state.generated_details[target_id] = detail_data
            st.session_state.active_script_id = target_id
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi tạo chi tiết kịch bản: {e}")

def add_five_scripts_continuation(current_mode: str, current_style: str):
    with st.spinner("Đang tư duy thêm 5 góc tiếp cận kịch bản mới lạ..."):
        all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
        cur_len = len(all_sources)
        analysis_info = json.dumps(st.session_state.content_analysis, ensure_ascii=False) if st.session_state.content_analysis else "Nội dung đang phân tích"
        
        prompt_more = f"""
        Dựa trên phân tích DNA nội dung:
        {analysis_info}

        Thể loại: {current_mode} | Phong cách: {current_style}
        Hãy tạo thêm ĐÚNG 5 Ý TƯỞNG KỊCH BẢN MỚI HOÀN TOÀN không trùng lặp với {cur_len} kịch bản trước:
        - id: {cur_len + 1} đến {cur_len + 5}
        - title: Tên kịch bản giật tít, sâu sắc
        - setting_style: Bối cảnh chính
        - angle: Góc độ mới lạ
        - target_hook: Ý tưởng hook 3-4s đầu
        - recommended_scenes_count: Phân bổ nhịp cảnh CHỈ DÙNG 4s, 6s, 8s (tuyệt đối không dùng 10s)
        - voice_profile: Giọng miền Bắc đồng nhất
        - Xuất JSON gồm key 'script_outlines' chứa 5 ý tưởng này.
        """
        try:
            sys_inst = get_system_instructions(current_mode, current_style)
            more_data = generate_with_smart_retry([prompt_more], sys_inst)
            if isinstance(more_data, list) and len(more_data) > 0:
                more_data = more_data[0]
            new_scripts = more_data.get("script_outlines", [])
            
            for i, sc in enumerate(new_scripts):
                sc["id"] = cur_len + i + 1

            if st.session_state.active_script_id is None:
                st.session_state.all_scripts.extend(new_scripts)
            else:
                st.session_state.expanded_scripts.extend(new_scripts)
                
            st.success("✅ Đã bổ sung thành công 5 kịch bản mới!")
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi tạo thêm: {e}")

# ==============================================================================
# KHU VỰC 1: BANNER & BỘ CHỌN THỂ LOẠI (MODE SWITCHER)
# ==============================================================================
st.markdown("""
<div class="header-container">
    <div class="header-badge">🌟 KENTOM AI VIDEO STUDIO PRO</div>
    <div class="main-title">🎬 Xây Dựng Kịch Bản Đa Vũ Trụ</div>
    <div class="sub-title">TikTok Shop Chuyên Sâu, TVC Điện Ảnh, Phim Đời Sống, Du Lịch,Văn Hóa - Tâm Linh, Nhà Đẹp & Xe Cộ</div>
</div>
""", unsafe_allow_html=True)

col_mode, col_style = st.columns([1.5, 1])
with col_mode:
    selected_mode = st.selectbox(
        "🎯 Chọn Thể Loại Nội Dung:",
        options=[
            "🛒 TikTok Shop & Bán Hàng",
            "📺 TVC Quảng Cáo & Thương Hiệu Cao Cấp",
            "🏡 Nhà Cửa, Kiến Trúc & Cảnh Quan",
            "🌿 Du Lịch & Phong Cảnh Đất Nước",
            "🚗 Xe Cộ & Trải Nghiệm Lái",
            "🍲 Ẩm Thực & Trải Nghiệm Đời Sống",
            "📖 Đời Sống & Bài Học Giáo Dục",
            "🏛️ Lịch Sử & Tín Ngưỡng Di Sản",
            "🧘 Chữa Lành & Phong Cách Sống"
        ],
        index=0
    )

with col_style:
    selected_style = st.selectbox(
        "🎨 Chọn Phong Cách Hình Ảnh (Visual Style):",
        options=[
            "Cinematic Realism (Người thật / Siêu thực 8K)",
            "3D Pixar / Disney Animation (Hoạt hình 3D cao cấp)",
            "2D Ghibli / Anime Art (Hoạt hình vẽ tay Nhật Bản)",
            "Tranh Thủy Mặc Cổ Phong (Cổ kính / Nghệ thuật)"
        ],
        index=0
    )

# ==============================================================================
# KHU VỰC 2: ĐẦU VÀO KÉP THÔNG MINH (VĂN BẢN + ẢNH THU GỌN)
# ==============================================================================
st.markdown("---")
st.markdown("### 📥 **Dữ Liệu Đầu Vào (Nhập Văn Bản, Tải Ảnh hoặc Kết Hợp Cả Hai)**")

prompt_placeholders = {
    "🛒 TikTok Shop & Bán Hàng": "Mô tả sản phẩm, tính năng độc nhất (USP), chương trình khuyến mãi hoặc đối tượng sử dụng...",
    "📺 TVC Quảng Cáo & Thương Hiệu Cao Cấp": "Mô tả sản phẩm/dịch vụ TVC: Spa trị liệu cao cấp, khu nghỉ dưỡng ven biển, đồng hồ xa xỉ...",
    "🏡 Nhà Cửa, Kiến Trúc & Cảnh Quan": "Mô tả căn nhà: Biệt thự đồi thông Đà Lạt, căn hộ penthouse tối giản, nhà vườn phong cách Indochine...",
    "🌿 Du Lịch & Phong Cảnh Đất Nước": "Nhập tên địa danh hoặc ý tưởng: Vịnh Hạ Long lúc hoàng hôn, Mù Cang Chải mùa lúa chín...",
    "🚗 Xe Cộ & Trải Nghiệm Lái": "Nhập dòng xe & bối cảnh: Porsche 911 GT3 RS màu xanh Shark Blue, xe lướt trên cung đèo ven biển...",
    "🍲 Ẩm Thực & Trải Nghiệm Đời Sống": "Tên món ăn hoặc quán ăn: Phở bò tái lăn Hà Nội khói nghi ngút, ẩm thực chợ đêm...",
    "📖 Đời Sống & Bài Học Giáo Dục": "Tóm tắt cốt truyện: Người cha đạp xích lô nuôi con gái đỗ đại học...",
    "🏛️ Lịch Sử & Tín Ngưỡng Di Sản": "Chủ đề lịch sử/tâm linh: Khí thế hào hùng thời nhà Trần chống giặc...",
    "🧘 Chữa Lành & Phong Cách Sống": "Không gian & thông điệp: Buổi sớm yên bình trong ngôi nhà gỗ Wabi-sabi..."
}

input_text = st.text_area(
    f"✍️ Tóm tắt ý tưởng, cốt truyện, tên địa danh, dòng xe hoặc mô tả chi tiết:",
    placeholder=prompt_placeholders.get(selected_mode, "Nhập thông tin mô tả tại đây..."),
    height=100
)

uploaded_files = st.file_uploader(
    "🖼️ Tải ảnh tham chiếu (Tùy chọn - Có thể bỏ qua nếu đã nhập văn bản mô tả ở trên):",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

images = []
if uploaded_files:
    images = [Image.open(f) for f in uploaded_files]
    with st.expander(f"👁️ Xem lại {len(images)} ảnh đã tải lên (Bấm để mở/đóng)", expanded=False):
        cols = st.columns(min(len(images), 4))
        for idx, img in enumerate(images):
            cols[idx % 4].image(img, caption=f"Ảnh {idx+1}", use_container_width=True)

can_generate = bool(input_text.strip()) or bool(images)

if st.button("🚀 Bắt Đầu Bóc Tách DNA Chi Tiết & Lên 5 Ma Trận Kịch Bản", type="primary", use_container_width=True, disabled=not can_generate):
    with st.spinner(f"Đang bóc tách chi tiết cơ khí, ma trận nỗi đau khách hàng và lên kịch bản cho '{selected_mode}'..."):
        prompt = f"""
        Phân tích chuyên sâu dữ liệu đầu vào cho thể loại '{selected_mode}' theo phong cách '{selected_style}' và xuất JSON chuẩn xác:
        THÔNG TIN TỪ NGƯỜI DÙNG:
        "{input_text.strip() if input_text.strip() else 'Không có mô tả văn bản, phân tích hoàn toàn từ ảnh.'}"

        YÊU CẦU CẤU TRÚC JSON (Bắt buộc trả về đúng các key sau):
        - "content_analysis": {{
            "category_or_genre": "...",
            "mechanical_and_accessories": "...",
            "customer_pain_points": "...",
            "core_desires": "...",
            "emotional_or_usp_hook": "...",
            "visual_physics_rules": "...",
            "target_audience": "...",
            "prompt_dna_lock": "..."
          }}
        - "script_outlines": [
            {{
              "id": 1,
              "title": "...",
              "setting_style": "...",
              "angle": "...",
              "target_hook": "...",
              "recommended_scenes_count": "...",
              "voice_profile": {{"gender": "...", "age_range": "...", "tone": "..."}}
            }}
          ] (Đúng 5 kịch bản từ id 1 đến 5)
        """
        try:
            sys_inst = get_system_instructions(selected_mode, selected_style)
            optimized_images = [optimize_image_for_api(img) for img in images] if images else []
            api_payload = [*optimized_images, prompt] if optimized_images else [prompt]
            
            data = generate_with_smart_retry(api_payload, sys_inst)
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            if not isinstance(data, dict):
                st.error("⚠️ Dữ liệu trả về từ mô hình không đúng định dạng JSON cấu trúc. Vui lòng bấm lại nút chạy!")
                st.stop()

            analysis_data = data.get("content_analysis") or data.get("analysis") or data.get("dna_analysis")
            outlines_data = data.get("script_outlines") or data.get("scripts") or data.get("outlines")

            if not analysis_data or not outlines_data:
                st.error(f"⚠️ Cấu trúc JSON thiếu trường dữ liệu quan trọng. Phản hồi nhận được: {list(data.keys())}")
                st.stop()

            st.session_state.content_analysis = analysis_data
            st.session_state.all_scripts = outlines_data
            st.session_state.cloned_scripts = []
            st.session_state.expanded_scripts = []
            st.session_state.generated_details = {}
            st.session_state.active_script_id = None
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi khởi tạo hệ thống: {e}")

# Hiển thị Bóc tách DNA chi tiết đa tầng (Gọn gàng trong 1 ô container, có xuống dòng ngắt ý)
if st.session_state.content_analysis and isinstance(st.session_state.content_analysis, dict):
    st.divider()
    st.markdown(f"### 🔍 **Phân Tích DNA Chi Tiết Đa Tầng — [{selected_mode.upper()}]**")
    ca = st.session_state.content_analysis
    
    mech_text = format_analysis_field(ca.get('mechanical_and_accessories', 'N/A'))
    pain_text = format_analysis_field(ca.get('customer_pain_points', 'N/A'))
    desire_text = format_analysis_field(ca.get('core_desires', 'N/A'))
    usp_text = format_analysis_field(ca.get('emotional_or_usp_hook', 'N/A'))
    physics_text = format_analysis_field(ca.get('visual_physics_rules', 'N/A'))
    prompt_lock_text = format_analysis_field(ca.get('prompt_dna_lock', 'N/A'))

    with st.container(border=True):
        st.markdown("##### 🏭 **1. Thông số Cơ khí & Phụ kiện đi kèm:**")
        st.markdown(f"<div style='line-height: 1.6;'>{mech_text}</div>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("##### 🎯 **2. Ma trận 3 Tầng Nỗi đau Khách hàng:**")
        st.markdown(f"<div style='line-height: 1.6;'>{pain_text}</div>", unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("##### 💡 **3. Mong muốn cốt lõi & USP:**")
        st.markdown(f"• **Mong muốn:** {desire_text}")
        st.markdown(f"• **USP / Slogan:** {usp_text}")
        st.markdown("---")

        st.markdown("##### ⚙️ **4. Quy chuẩn Vật lý:**")
        st.markdown(f"<div style='line-height: 1.6;'>{physics_text}</div>", unsafe_allow_html=True)

    st.markdown("##### 📌 **Chuỗi khóa thị giác (Visual DNA Lock - Dùng cho Imagen 3 & Veo 3):**")
    st.code(prompt_lock_text, language="text")

# ==============================================================================
# GIAI ĐOẠN 1: KHI CHƯA TẠO CHI TIẾT KỊCH BẢN NÀO
# ==============================================================================
if st.session_state.all_scripts and st.session_state.active_script_id is None:
    st.divider()
    st.markdown(f"### 📋 **Danh Sách 5 Ma Trận Kịch Bản Thực Chiến**")
    st.write("Chọn **'✨ Tạo chi tiết kịch bản này'** để AI tiến hành phân cảnh chi tiết (chỉ gồm 4s, 6s, 8s).")

    for outline in st.session_state.all_scripts:
        if not isinstance(outline, dict):
            continue
        sc_id = outline.get("id")
        col_info, col_act = st.columns([3, 1.2])
        with col_info:
            pacing_badge = f'<span class="badge-dynamic">{outline.get("recommended_scenes_count", "Động học")}</span>'
            st.markdown(f"**{sc_id}. {outline.get('title')}** — <span class='badge-pending'>CHƯA TẠO CHI TIẾT</span> {pacing_badge}", unsafe_allow_html=True)
            st.caption(f"🏛️ **Bối cảnh:** {outline.get('setting_style')} | 🎯 **Góc tiếp cận:** {outline.get('angle')} | ⚡ **Hook:** *\"{outline.get('target_hook')}\"*")
        with col_act:
            if st.button("✨ Tạo chi tiết kịch bản này", key=f"btn_init_{sc_id}", use_container_width=True):
                create_scene_details_for_id(sc_id, selected_mode, selected_style)

    st.markdown("---")
    if st.button("➕ Gọi Thêm 5 Kịch Bản Khác", key="btn_add_more_only_one", type="primary", use_container_width=True):
        add_five_scripts_continuation(selected_mode, selected_style)

# ==============================================================================
# GIAI ĐOẠN 2: KHI ĐÃ TẠO CHI TIẾT KỊCH BẢN
# ==============================================================================
if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details:
    st.divider()
    active_script = st.session_state.generated_details[st.session_state.active_script_id]
    
    if isinstance(active_script, list) and len(active_script) > 0:
        active_script = active_script[0]
        st.session_state.generated_details[st.session_state.active_script_id] = active_script

    if isinstance(active_script, dict):
        vp = active_script.get("voice_profile", {})
        if not isinstance(vp, dict):
            vp = {}
        
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(active_script.get('title', '')).upper()}**")
        st.info(f"⏱️ **Tổng thời lượng:** **{active_script.get('total_estimated_duration', '24s')}** ({len(active_script.get('scenes', []))} phân cảnh) | 🎨 **Phong cách:** {selected_style} | 🎙️ **Giọng:** **{vp.get('gender', 'Nữ')} miền Bắc ({vp.get('age_range', '25-30')})** - *{vp.get('tone', 'Tự nhiên')}*")

        for scene in active_script.get("scenes", []):
            if not isinstance(scene, dict):
                continue
            sc_num = scene.get("scene_number", 1)
            trans_type = scene.get("transition_type", "Cắt cảnh (Hard Cut)")
            dur = scene.get("duration", "6s")
            st.markdown(f"#### **📍 Phân cảnh {sc_num} ({dur}) — [ {trans_type} ]**")

            scene_setting_desc = scene.get("scene_setting", active_script.get("setting_style", "Không gian sản phẩm"))
            st.markdown(f"🏛️ **Bối cảnh phân cảnh:** *{scene_setting_desc}*")

            st.markdown("**🎙️ Đạo diễn giọng đọc:**")
            st.write(scene.get("voice_director_vn", ""))

            st.markdown("**💬 Lời thoại lồng tiếng (100% Miền Bắc - Chuẩn nhịp thời lượng):**")
            st.markdown(f"> *\"{scene.get('voiceover_vi', '')}\"*")

            st.markdown(f"**🖼️ Prompt Tạo Ảnh Gốc (Imagen 3 - 9:16 - {selected_style}):**")
            if "nối tiếp" in str(trans_type).lower() or not scene.get("image_prompt"):
                st.warning("👉 **Lấy ảnh cuối của video trước làm ảnh đầu vào cho phân cảnh này.**")
            else:
                img_p = scene.get("image_prompt", "")
                st.code(img_p, language="text")
                safe_copy_button(img_p, "📋 Copy Prompt Ảnh (Imagen 3)")

            st.markdown(f"**🎥 Prompt Chuyển Động Video (Veo 3 - {selected_mode}):**")
            vid_p = scene.get("video_prompt", "")
            st.code(vid_p, language="text")
            safe_copy_button(vid_p, "📋 Copy Prompt Video (Veo 3)")

            st.markdown("---")

        # ==============================================================================
        # KHU VỰC 3 VÙNG QUẢN TRỊ DƯỚI CÙNG
        # ==============================================================================
        st.markdown("### ⚡ **Khu Vực Quản Trị & Mở Rộng Kịch Bản**")
        col_win_zone, col_explore_zone = st.columns(2)

        # VÙNG 1: NHÂN BẢN KỊCH BẢN WIN BẰNG DROPDOWN
        with col_win_zone:
            st.markdown("""
            <div class="custom-card">
                <div class="card-title-win">🔥 Vùng Nhân Bản Kịch Bản Win (A/B Test)</div>
                <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 12px;">
                    Chọn kịch bản thành công từ danh sách xổ xuống để nhân bản thành 5 biến thể mở đầu & bối cảnh khác nhau.
                </div>
            </div>
            """, unsafe_allow_html=True)

            generated_ids = list(st.session_state.generated_details.keys())
            if generated_ids:
                options_dict = {
                    gid: f"#{gid}. {st.session_state.generated_details[gid].get('title') if isinstance(st.session_state.generated_details[gid], dict) else 'Kịch bản ' + str(gid)}"
                    for gid in generated_ids
                }
                default_index = generated_ids.index(st.session_state.active_script_id) if st.session_state.active_script_id in generated_ids else 0
                
                selected_win_id = st.selectbox(
                    "Chọn kịch bản win cần nhân bản (bấm để xổ danh sách):",
                    options=generated_ids,
                    index=default_index,
                    format_func=lambda x: options_dict[x],
                    key="select_win_dropdown_universal"
                )
                
                if st.button("🚀 Nhân Bản 5 Biến Thể Win Từ Kịch Bản Đã Chọn", type="primary", use_container_width=True):
                    with st.spinner("Đang nhân bản thành 5 biến thể A/B testing..."):
                        target_win_script = st.session_state.generated_details[selected_win_id]
                        all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
                        cur_len = len(all_sources)
                        
                        prompt_clone = f"""
                        Dựa trên kịch bản win chi tiết sau: {json.dumps(target_win_script, ensure_ascii=False)}
                        Thể loại: {selected_mode} | Phong cách: {selected_style}
                        Hãy tạo ĐÚNG 5 BIẾN THỂ WIN MỚI:
                        - Biến hóa 5 cách mở đầu (Hook 3-4s) và góc tiếp cận bối cảnh khác biệt.
                        - Phân bổ số phân cảnh kết hợp thời lượng CHỈ GỒM 4s, 6s, 8s (TUYỆT ĐỐI KHÔNG DÙNG 10s).
                        - Xuất JSON gồm 'cloned_outlines' chứa 5 ý tưởng biến thể (id mới tiếp theo: {cur_len + 1} đến {cur_len + 5}, title, setting_style, angle, target_hook, recommended_scenes_count, voice_profile).
                        """
                        try:
                            sys_inst = get_system_instructions(selected_mode, selected_style)
                            clone_data = generate_with_smart_retry([prompt_clone], sys_inst)
                            if isinstance(clone_data, list) and len(clone_data) > 0:
                                clone_data = clone_data[0]
                            cloned_list = clone_data.get("cloned_outlines", [])
                            for i, cl in enumerate(cloned_list):
                                cl["id"] = cur_len + i + 1
                            st.session_state.cloned_scripts.extend(cloned_list)
                            st.success("✅ Đã nhân bản 5 biến thể Win vào ô bên dưới!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi nhân bản: {e}")

            if st.session_state.cloned_scripts:
                st.markdown("---")
                st.markdown(f"##### 🎯 **Ô Các Kịch Bản Đã Nhân Bản Win ({len(st.session_state.cloned_scripts)}):**")
                for cl_sc in st.session_state.cloned_scripts:
                    c_id = cl_sc.get("id")
                    is_gen = c_id in st.session_state.generated_details
                    badge = '<span class="badge-ready">ĐÃ CÓ CHI TIẾT</span>' if is_gen else '<span class="badge-pending">CHƯA TẠO</span>'
                    st.markdown(f"**• #{c_id}. {cl_sc.get('title')}** — {badge}", unsafe_allow_html=True)
                    st.caption(f"🏛️ {cl_sc.get('setting_style')} | ⚡ Hook: *\"{cl_sc.get('target_hook')}\"*")
                    btn_lbl = "👁️ Xem chi tiết" if is_gen else "✨ Tạo chi tiết kịch bản này"
                    if st.button(btn_lbl, key=f"btn_clone_phase2_{c_id}", use_container_width=True):
                        create_scene_details_for_id(c_id, selected_mode, selected_style)
                    st.write("")

        # VÙNG 2 & 3: GỌI THÊM & HIỂN THỊ KỊCH BẢN CHƯA TẠO TRƯỚC ĐÓ
        with col_explore_zone:
            st.markdown("""
            <div class="custom-card">
                <div class="card-title-add">➕ Vùng Gọi Thêm Kịch Bản Mới</div>
                <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 12px;">
                    Mở rộng thêm nhiều ý tưởng kịch bản độc đáo từ dữ liệu DNA đã phân tích.
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("➕ Gọi Thêm 5 Tình Huống Kịch Bản Mới", key="btn_add_more_phase2", use_container_width=True):
                add_five_scripts_continuation(selected_mode, selected_style)

            if st.session_state.expanded_scripts:
                st.markdown("---")
                st.markdown(f"##### 🚀 **Ô Các Tình Huống Vừa Gọi Thêm ({len(st.session_state.expanded_scripts)}):**")
                for ex_sc in st.session_state.expanded_scripts:
                    e_id = ex_sc.get("id")
                    is_ex_gen = e_id in st.session_state.generated_details
                    badge = '<span class="badge-ready">ĐÃ CÓ CHI TIẾT</span>' if is_ex_gen else '<span class="badge-pending">CHƯA TẠO</span>'
                    st.markdown(f"**• #{e_id}. {ex_sc.get('title')}** — {badge}", unsafe_allow_html=True)
                    st.caption(f"🏛️ {ex_sc.get('setting_style')} | ⚡ Hook: *\"{ex_sc.get('target_hook')}\"*")
                    btn_lbl = "👁️ Xem chi tiết" if is_ex_gen else "✨ Tạo chi tiết kịch bản này"
                    if st.button(btn_lbl, key=f"btn_expand_phase2_{e_id}", use_container_width=True):
                        create_scene_details_for_id(e_id, selected_mode, selected_style)
                    st.write("")

            st.markdown("---")
            st.markdown("""
            <div class="custom-card">
                <div class="card-title-unmade">⏳ Vùng Kịch Bản Chưa Tạo Chi Tiết</div>
                <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 12px;">
                    Các kịch bản gốc trước đó đang chờ dựng cảnh. Bấm để tạo chi tiết ngay.
                </div>
            </div>
            """, unsafe_allow_html=True)

            all_combined_outlines = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
            unmade_prior = [
                sc for sc in all_combined_outlines
                if isinstance(sc, dict) and sc.get("id") not in st.session_state.generated_details
            ]

            if unmade_prior:
                for unsc in unmade_prior:
                    u_id = unsc.get("id")
                    st.markdown(f"**• #{u_id}. {unsc.get('title')}** (*Bối cảnh: {unsc.get('setting_style', 'Thực tế')}*)")
                    if st.button("✨ Tạo chi tiết kịch bản này", key=f"btn_unmade_prior_{u_id}", use_container_width=True):
                        create_scene_details_for_id(u_id, selected_mode, selected_style)
                    st.write("")
            else:
                st.success("🎉 Bạn đã tạo chi tiết cho toàn bộ các kịch bản!")
