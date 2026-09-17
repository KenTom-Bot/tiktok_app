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

st.set_page_config(page_title="TikTok AI Video Suite Pro", page_icon="🎬", layout="wide")

# CSS tối ưu giao diện: Tiêu đề lớn căn giữa bắt mắt, nút bấm gradient, tương thích Mobile 100%
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

    .stExpander { border-radius: 8px !important; margin-bottom: 8px !important; }
    
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

SYSTEM_INSTRUCTIONS = """
BẠN LÀ BẬC THẦY SẢN XUẤT VIDEO VIRAL VÀ TĂNG CHUYỂN ĐỔI TIKTOK SHOP, TỔNG ĐẠO DIỄN VIRTUAL CHO IMAGEN 3 VÀ VEO 3.

I. GIAO THỨC KHÓA CỨNG GIẢI PHẪU SẢN PHẨM (PRODUCT DNA LOCK):
1. Nhận diện cấu tạo chính xác:
   - Thân vỏ, tỷ lệ kích thước công thái học, màu sắc nhận diện (Hero Color) và chất liệu bề mặt (nhám mờ matte, bóng bóng chrome...).
   - Vị trí cơ học chính xác: Đầu hút/thổi, hộp chứa bụi trong suốt (dust chamber), vị trí lõi lọc HEPA có thể tháo rời, công tắc trượt/bấm, đèn báo LED và cổng sạc (Type-C / DC).
   - KHÓA CỨNG VÀO PROMPT: Mỗi 'image_prompt' và 'video_prompt' BẮT BUỘC chứa chuỗi mô tả cơ khí cố định ('product_dna_prompt') trích xuất từ ảnh để đảm bảo sản phẩm trong ảnh và video hoàn toàn đồng nhất với thực tế, không bị AI biến dạng hoặc đổi kiểu dáng.
2. Thao tác tay thực tế: Chỉ tối đa 1 bàn tay người lớn cầm nắm chuẩn công thái học tại báng cầm, ngón cái gạt công tắc dứt khoát. CẤM biến dạng, cấm mọc thừa ngón tay.

II. VẬT LÝ HÚT & THỔI SIÊU THỰC (REALISTIC SUCTION & BLOWING DYNAMICS):
1. VẬT LÝ HÚT BỤI (SUCTION DYNAMICS):
   - Khi đầu hút lướt qua bề mặt (ghế da ô tô, thảm nỉ, khe bàn phím), các hạt bụi mịn, mẩu vụn bánh, sợi tóc bị LỰC HÚT CHÂN KHÔNG XOÁY VÀ KÉO THẲNG VÀO BÊN TRONG ĐẦU HÚT ('crumbs and dust particles visibly sucked and ingested directly into the clear nozzle and dust chamber').
   - Hộp chứa bụi trong suốt thấy rõ luồng xoáy chứa bụi và vụn rác xoáy tròn bên trong.
   - TUYỆT ĐỐI CẤM: Bụi bị thổi tung ngược ra ngoài khi đang hút, cấm dùng tia sáng, vệt nước ma mị hay chùm khói viễn tưởng.
2. VẬT LÝ THỔI KHÍ (BLOWING DYNAMICS):
   - Luồng khí vô hình áp suất cao ('invisible high-velocity transparent airflow'). Sức gió được biểu thị qua phản lực môi trường: lá khô, bụi, tàn tro bắn văng ra xa tức thì.

III. CHÍNH SÁCH TIKTOK SHOP & AN TOÀN NỘI DUNG:
1. Giá bán: Cấm nhắc giá số cụ thể. Chỉ dùng từ ngữ đời thường ('vài chục', 'cốc trà đá', 'bát phở', 'deal hời góc giỏ hàng').
2. Từ ngữ cấm: Cấm hoàn toàn cam kết tuyệt đối ('chữa dứt điểm', 'vĩnh viễn', '100%', 'khỏi hẳn').
3. Đối tượng trẻ em: Phụ huynh luôn xuất hiện thao tác trực tiếp, cấm để trẻ em một mình trước ống kính.
4. Màn hình sạch: Tuyệt đối không text overlay, không sub nổi, không logo, không watermark.

IV. NHỊP ĐỘ PHÂN CẢNH & ĐẠO DIỄN GIỌNG ĐỌC:
1. Số phân cảnh: Tự động quyết định 3 đến 6 cảnh.
2. Thời lượng từng cảnh: BẮT BUỘC CHỈ DÙNG 3 MỐC: 4s, 6s, 8s. TUYỆT ĐỐI CẤM DÙNG MỐC 10 GIÂY.
3. Giọng đọc: 100% tiếng Việt miền Bắc chuẩn Hà Nội, nêu rõ Giới tính (Nam/Nữ) và Độ tuổi phù hợp tình huống, đồng nhất suốt các cảnh.
4. Tích hợp thoại vào Veo 3: Trong 'video_prompt', nhúng nguyên văn lời thoại tiếng Việt có dấu kèm chỉ đạo biểu cảm gương mặt, khẩu hình và cử chỉ nhấn nhá cơ thể.
"""

def generate_with_smart_retry(contents, system_inst, max_tokens=8192):
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

def create_scene_details_for_id(target_id: int):
    outline = next((sc for sc in st.session_state.script_outlines if isinstance(sc, dict) and sc.get("id") == target_id), None)
    if not outline:
        return
    
    with st.spinner(f"Đang khóa cứng thông số cơ khí và dựng prompt chi tiết cho '{outline.get('title')}'..."):
        vp = outline.get("voice_profile", {})
        if not isinstance(vp, dict):
            vp = {}
        p_info = json.dumps(st.session_state.product_analysis, ensure_ascii=False) if st.session_state.product_analysis else ""
        
        prompt_detail = f"""
        Dựa trên thông số phân tích cơ khí và cấu tạo sản phẩm đã khóa chặt:
        {p_info}

        Ý tưởng kịch bản cần dựng chi tiết:
        - Tiêu đề: {outline.get('title')}
        - Bối cảnh chủ đạo: {outline.get('setting_style')} (phân xưởng sản xuất, showroom hoặc không gian thực tế)
        - Góc độ: {outline.get('angle')}
        - Hook: {outline.get('target_hook')}
        - Giọng đọc: {vp.get('gender', 'Nữ')} miền Bắc, tuổi {vp.get('age_range', '25-30')}

        QUY ĐỊNH KỸ THUẬT NGHIÊM NGẶT:
        1. 'image_prompt' (Imagen 3, 9:16):
           - Khóa chặt hình dạng, báng cầm, màu sắc, vị trí nút bấm, hộp chứa bụi và phụ kiện đúng như cấu tạo thực tế.
           - Nếu là Cảnh nối tiếp (Continuous Motion): Để rỗng ("").
        2. 'video_prompt' (Veo 3):
           - VẬT LÝ HÚT BỤI CHUẨN XÁC: Mô tả rõ ràng bụi mịn, vụn rác, tóc được lực hút chân không hút xoáy thẳng vào bên trong đầu hút và hộp chứa bụi trong suốt. Không để bụi bay lung tung.
           - VẬT LÝ THỔI KHÍ: Luồng khí vô hình trong suốt áp lực cao, thổi bay mảnh rác/bụi ra xa.
           - Tích hợp nguyên văn lời thoại tiếng Việt có dấu, khẩu hình ăn khớp và biểu cảm diễn xuất tự nhiên.
        3. THỜI LƯỢNG: 'duration' của mỗi cảnh CHỈ ĐƯỢC LÀ '4s', '6s' hoặc '8s'. CẤM DÙNG '10s'.

        Định dạng JSON chuẩn (BẮT BUỘC là 1 Dict, không bọc mảng list):
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
              "image_prompt": "Prompt Imagen 3 9:16 khóa cấu tạo cơ khí chi tiết (để rỗng nếu là Cảnh nối tiếp)",
              "video_prompt": "Prompt Veo 3 chi tiết thao tác vật lý hút/thổi chân thực, tích hợp thoại tiếng Việt"
            }}
          ]
        }}
        """
        try:
            detail_data = generate_with_smart_retry([prompt_detail], SYSTEM_INSTRUCTIONS)
            if isinstance(detail_data, list) and len(detail_data) > 0:
                detail_data = detail_data[0]
            if not isinstance(detail_data, dict):
                st.error("Dữ liệu trả về chưa đúng định dạng. Vui lòng bấm thử lại!")
                return
            
            if "voice_profile" not in detail_data or not isinstance(detail_data["voice_profile"], dict):
                detail_data["voice_profile"] = vp

            st.session_state.generated_details[target_id] = detail_data
            st.session_state.active_script_id = target_id
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi tạo chi tiết: {e}")

def add_five_more_scripts():
    """Hàm bổ sung thêm 5 ý tưởng kịch bản mới không gửi kèm ảnh để tối ưu tốc độ và tránh 503"""
    with st.spinner("Đang tư duy thêm 5 góc tiếp cận kịch bản mới lạ..."):
        cur_len = len(st.session_state.script_outlines)
        p_info = json.dumps(st.session_state.product_analysis, ensure_ascii=False) if st.session_state.product_analysis else "Sản phẩm đang phân tích"
        
        prompt_more = f"""
        Dựa trên thông số phân tích cơ khí đã khóa:
        {p_info}

        Hãy tạo thêm ĐÚNG 5 Ý TƯỞNG KỊCH BẢN MỚI HOÀN TOÀN không trùng lặp với {cur_len} kịch bản trước:
        - id: {cur_len + 1} đến {cur_len + 5}
        - title: Tên kịch bản giật tít, hấp dẫn
        - setting_style: Bối cảnh chính (Phân xưởng sản xuất, kho hàng, showroom, không gian thực tế)
        - angle: Góc độ mới lạ
        - target_hook: Ý tưởng hook 3-4s
        - recommended_scenes_count: Phân bổ nhịp cảnh CHỈ DÙNG 4s, 6s, 8s (tuyệt đối không dùng 10s)
        - voice_profile: Giọng miền Bắc đồng nhất
        - Xuất JSON gồm key 'script_outlines' chứa 5 ý tưởng này.
        """
        try:
            more_data = generate_with_smart_retry([prompt_more], SYSTEM_INSTRUCTIONS)
            if isinstance(more_data, list) and len(more_data) > 0:
                more_data = more_data[0]
            st.session_state.script_outlines.extend(more_data.get("script_outlines", []))
            st.success("✅ Đã bổ sung thêm 5 tình huống kịch bản mới vào danh sách!")
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi tạo thêm: {e}")

# KHU VỰC HEADER CHÍNH CĂN GIỮA
st.markdown("""
<div class="header-container">
    <div class="header-badge">🚀 VEO 3 & IMAGEN 3 AUTOMATION PRO</div>
    <div class="main-title">🎬 Hệ Thống Kịch Bản TikTok Shop Đa Năng</div>
    <div class="sub-title">Khóa chuẩn cấu tạo cơ khí, vật lý hút/thổi siêu thực & nhịp độ động (4s, 6s, 8s)</div>
</div>
""", unsafe_allow_html=True)

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
        with st.spinner("Đang bóc tách giải phẫu cơ khí, nguyên lý hút/thổi và lên ý tưởng viral..."):
            prompt = """
            Phân tích toàn diện sản phẩm từ ảnh và xuất JSON:
            1. 'product_analysis':
               - category: Ngành hàng chi tiết
               - target_audience: Chân dung khách hàng mục tiêu
               - core_pain_points: 3 nỗi đau lớn nhất của khách
               - hero_color: Màu nhận diện chủ đạo và chất liệu bề mặt (ví dụ: 'Màu xám nòng súng matte, viền cam chrome, hộp chứa bụi nhựa ABS trong suốt')
               - structure_and_functions: Cấu tạo và chức năng cốt lõi (ví dụ: 'Thân máy dạng súng lục công thái học, đầu hút dẹt có thể tháo rời, cổng sạc Type-C ở chuôi cầm, lõi lọc HEPA có thể giặt')
               - mechanical_details: Vị trí chính xác của công tắc nguồn, khớp xoay hộp bụi, cổng sạc, các đầu chuyển đổi
               - included_accessories: Danh sách các đầu hút/thổi/dây cáp nhận diện được từ ảnh
               - suction_and_aerodynamics_notes: Nguyên lý hút bụi thực tế (bụi bị hút thẳng vào miệng hút/khoang chứa) và thổi khí vô hình
               - product_dna_prompt: Một đoạn mô tả tiếng Anh chuẩn xác về ngoại hình sản phẩm để nhúng vào prompt tạo ảnh và video
               - key_usp: Điểm bán hàng độc nhất (USP)
            2. 'script_outlines': ĐÚNG 5 Ý TƯỞNG KỊCH BẢN:
               - id: 1 đến 5
               - title: Tên kịch bản giật tít, hấp dẫn
               - setting_style: Bối cảnh chính (Phân xưởng sản xuất, Kho hàng tấp nập, Showroom, Không gian thực tế)
               - angle: Góc tiếp cận chuyển đổi
               - target_hook: Ý tưởng câu hook 3-4s đầu
               - recommended_scenes_count: Phân bổ nhịp cảnh CHỈ DÙNG 4s, 6s, 8s (TUYỆT ĐỐI KHÔNG DÙNG 10s, ví dụ: '4 cảnh (4s-6s-8s-8s)', '3 cảnh (4s-6s-8s)')
               - voice_profile: {gender: 'Nam'/'Nữ', age_range: 'Độ tuổi', tone: 'Âm điệu miền Bắc'}
            """
            try:
                data = generate_with_smart_retry([*images, prompt], SYSTEM_INSTRUCTIONS)
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]
                st.session_state.product_analysis = data.get("product_analysis", {})
                st.session_state.script_outlines = data.get("script_outlines", [])
                st.session_state.generated_details = {}
                st.session_state.active_script_id = None
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi khởi tạo: {e}")

# Hiển thị Phân tích sản phẩm
if st.session_state.product_analysis and isinstance(st.session_state.product_analysis, dict):
    st.divider()
    st.markdown("### 🔍 **Phân tích cấu tạo cơ khí & Khóa nhận diện sản phẩm**")
    p = st.session_state.product_analysis
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Ngành hàng:** {p.get('category', 'N/A')}")
        st.markdown(f"**Màu nhận diện & Bề mặt:** {p.get('hero_color', 'N/A')}")
        st.markdown(f"**Cấu tạo & Chức năng:** {p.get('structure_and_functions', 'N/A')}")
        st.markdown(f"**Chi tiết cơ khí & Nút bấm:** {p.get('mechanical_details', 'N/A')}")
        st.markdown(f"**Lợi thế độc nhất (USP):** {p.get('key_usp', 'N/A')}")
    with c2:
        st.markdown(f"**Phụ kiện đi kèm:** {', '.join(p.get('included_accessories', [])) if isinstance(p.get('included_accessories'), list) else p.get('included_accessories', 'N/A')}")
        st.markdown(f"**Vật lý hút & thổi thực tế:** {p.get('suction_and_aerodynamics_notes', 'N/A')}")
        st.markdown(f"**Chân dung khách hàng:** {p.get('target_audience', 'N/A')}")
        st.markdown(f"**Khóa nhận diện sản phẩm (Product DNA):** `{p.get('product_dna_prompt', 'N/A')}`")

# Danh sách kịch bản đề xuất ban đầu
if st.session_state.script_outlines:
    st.divider()
    st.markdown(f"### 📋 **Danh sách {len(st.session_state.script_outlines)} ý tưởng kịch bản tối ưu chuyển đổi**")
    st.write("Bấm **'✨ Tạo chi tiết kịch bản này'** để AI tự động phân bổ nhịp cảnh linh hoạt (chỉ gồm 4s, 6s, 8s).")

    for outline in st.session_state.script_outlines:
        if not isinstance(outline, dict):
            continue
        sc_id = outline.get("id")
        is_generated = sc_id in st.session_state.generated_details
        
        col_info, col_act = st.columns([3, 1.2])
        with col_info:
            status_badge = '<span class="badge-ready">ĐÃ CÓ CHI TIẾT</span>' if is_generated else '<span class="badge-pending">CHƯA TẠO CHI TIẾT</span>'
            pacing_badge = f'<span class="badge-dynamic">{outline.get("recommended_scenes_count", "Động học")}</span>'
            st.markdown(f"**{outline.get('id')}. {outline.get('title')}** — {status_badge} {pacing_badge}", unsafe_allow_html=True)
            st.caption(f"🏭 **Bối cảnh:** {outline.get('setting_style', 'Thực tế')} | 🎯 **Góc độ:** {outline.get('angle')} | ⚡ **Hook:** *\"{outline.get('target_hook')}\"*")
        
        with col_act:
            btn_label = "👁️ Xem chi tiết" if is_generated else "✨ Tạo chi tiết kịch bản này"
            if st.button(btn_label, key=f"btn_gen_top_{sc_id}", use_container_width=True):
                if not is_generated:
                    create_scene_details_for_id(sc_id)
                else:
                    st.session_state.active_script_id = sc_id
                    st.rerun()

    # Nút mở rộng thêm 5 kịch bản dưới danh sách chính
    st.markdown("---")
    st.markdown("#### ➕ **Mở Rộng Thêm Kịch Bản Mới Khác Biệt**")
    if st.button("➕ Tạo Thêm 5 Kịch Bản Mới Khác Biệt", key="btn_add_more_main", type="primary", use_container_width=True):
        add_five_more_scripts()

# HIỂN THỊ KỊCH BẢN CHI TIẾT ĐANG CHỌN
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
        st.info(f"⏱️ **Tổng thời lượng:** **{active_script.get('total_estimated_duration', '24s')}** ({len(active_script.get('scenes', []))} phân cảnh) | 🏭 **Bối cảnh:** {active_script.get('setting_style', 'Thực tế')} | 🎙️ **Giọng:** **{vp.get('gender', 'Nữ')} miền Bắc ({vp.get('age_range', '25-30')})** - *{vp.get('tone', 'Tự nhiên')}*")

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

            st.markdown("**💬 Lời thoại lồng tiếng (100% Miền Bắc):**")
            st.markdown(f"> *\"{scene.get('voiceover_vi', '')}\"*")

            st.markdown("**🖼️ Prompt Tạo Ảnh Gốc (Imagen 3 - 9:16 - Khóa Chi Tiết Thực Tế):**")
            if "nối tiếp" in str(trans_type).lower() or not scene.get("image_prompt"):
                st.warning("👉 **Lấy ảnh cuối của video trước làm ảnh đầu vào cho phân cảnh này.**")
            else:
                img_p = scene.get("image_prompt", "")
                st.code(img_p, language="text")
                safe_copy_button(img_p, "📋 Copy Prompt Ảnh (Imagen 3)")

            st.markdown(f"**🎥 Prompt Chuyển Động Video (Veo 3 - Vật Lý Hút/Thổi Chuẩn):**")
            vid_p = scene.get("video_prompt", "")
            st.code(vid_p, language="text")
            safe_copy_button(vid_p, "📋 Copy Prompt Video (Veo 3)")

            st.markdown("---")

        # KHU VỰC BƯỚC TIẾP THEO: NHÂN BẢN & KHAI THÁC CÁC TÌNH HUỐNG KHÁC
        st.markdown("### ⚡ **Bước Tiếp Theo: Nhân Bản Win & Khai Thác Kịch Bản Khác**")
        col_win, col_unmade = st.columns(2)

        with col_win:
            st.markdown("#### 🔥 **Nhân Bản Kịch Bản Win (A/B Test)**")
            st.caption("Chọn 1 kịch bản win đã tạo chi tiết để AI nhân bản thành 5 biến thể mở đầu (Hook) và bối cảnh khác nhau.")
            
            generated_ids = list(st.session_state.generated_details.keys())
            if generated_ids:
                options_dict = {
                    gid: f"{gid}. {st.session_state.generated_details[gid].get('title') if isinstance(st.session_state.generated_details[gid], dict) else 'Kịch bản ' + str(gid)}"
                    for gid in generated_ids
                }
                default_index = generated_ids.index(st.session_state.active_script_id) if st.session_state.active_script_id in generated_ids else 0
                selected_win_id = st.radio(
                    "Chọn kịch bản win bạn muốn nhân bản:",
                    options=generated_ids,
                    index=default_index,
                    format_func=lambda x: options_dict[x],
                    key="radio_win_selection"
                )
                
                if st.button("🚀 Nhân Bản 5 Biến Thể Win Từ Kịch Bản Đã Chọn", type="primary", use_container_width=True):
                    with st.spinner("Đang nhân bản thành 5 biến thể A/B testing..."):
                        target_win_script = st.session_state.generated_details[selected_win_id]
                        prompt_clone = f"""
                        Dựa trên kịch bản win chi tiết sau: {json.dumps(target_win_script, ensure_ascii=False)}
                        Hãy tạo ĐÚNG 5 BIẾN THỂ WIN MỚI:
                        - Biến hóa 5 cách mở đầu (Hook 3-4s) và bối cảnh (chuyển đổi linh hoạt giữa phân xưởng sản xuất, kho hàng bận rộn và showroom sang trọng).
                        - Phân bổ số phân cảnh kết hợp thời lượng CHỈ GỒM 4s, 6s, 8s (TUYỆT ĐỐI KHÔNG DÙNG 10s).
                        - Xuất JSON gồm 'cloned_outlines' chứa 5 ý tưởng biến thể (id mới tiếp theo, title, setting_style, angle, target_hook, recommended_scenes_count, voice_profile).
                        """
                        try:
                            clone_data = generate_with_smart_retry([prompt_clone], SYSTEM_INSTRUCTIONS)
                            if isinstance(clone_data, list) and len(clone_data) > 0:
                                clone_data = clone_data[0]
                            cloned_list = clone_data.get("cloned_outlines", [])
                            cur_len = len(st.session_state.script_outlines)
                            for i, cl in enumerate(cloned_list):
                                cl["id"] = cur_len + i + 1
                            st.session_state.script_outlines.extend(cloned_list)
                            st.success("✅ Đã nhân bản thêm 5 kịch bản win vào danh sách!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi nhân bản: {e}")

                # BỔ SUNG NÚT GỌI THÊM TÌNH HUỐNG DƯỚI BUTTON NHÂN BẢN THEO YÊU CẦU
                st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
                if st.button("➕ Tạo Thêm 5 Tình Huống Kịch Bản Mới", key="btn_add_more_bottom", use_container_width=True):
                    add_five_more_scripts()
            else:
                st.info("Chưa có kịch bản chi tiết nào để nhân bản.")

        with col_unmade:
            st.markdown("#### ⏳ **Các Kịch Bản Khác Chưa Tạo Chi Tiết**")
            unmade_scripts = [sc for sc in st.session_state.script_outlines if isinstance(sc, dict) and sc.get("id") not in st.session_state.generated_details]
            
            if unmade_scripts:
                for unsc in unmade_scripts:
                    u_id = unsc.get("id")
                    with st.container():
                        st.markdown(f"**• {u_id}. {unsc.get('title')}** (*Bối cảnh: {unsc.get('setting_style', 'Thực tế')}*)")
                        if st.button("✨ Tạo chi tiết kịch bản này", key=f"btn_unmade_{u_id}", use_container_width=True):
                            create_scene_details_for_id(u_id)
                        st.write("")
            else:
                st.success("🎉 Bạn đã tạo chi tiết cho toàn bộ các kịch bản trong danh sách!")
