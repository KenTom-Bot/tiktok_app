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
from datetime import datetime, timedelta

st.set_page_config(page_title="Universal AI Video Studio Pro & License Manager", page_icon="🎬", layout="wide")

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
    .badge-pending { color: #d97706; font-weight: 700; background: #fef3c7; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
    .badge-ready { color: #15803d; font-weight: 700; background: #dcfce7; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
    
    .support-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1.5px solid #86efac;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
if not api_key:
    st.error("Chưa cấu hình GEMINI_API_KEY trong Advanced settings -> Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

ACCOUNTS_FILE = "accounts.json"
ADMIN_EMAIL = "binhnguyenmedia.vn@gmail.com"

def load_licensed_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    default_accounts = {
        ADMIN_EMAIL: {
            "contact": ADMIN_EMAIL,
            "roles": ["Tất cả thể loại"],
            "expires_at": "2099-12-31"
        }
    }
    save_licensed_accounts(default_accounts)
    return default_accounts

def save_licensed_accounts(accounts_dict):
    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(accounts_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Lỗi lưu danh sách tài khoản: {e}")

# Khởi tạo Session State
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
if "projects_library" not in st.session_state:
    st.session_state.projects_library = {}
if "licensed_accounts" not in st.session_state:
    st.session_state.licensed_accounts = load_licensed_accounts()

if ADMIN_EMAIL not in st.session_state.licensed_accounts:
    st.session_state.licensed_accounts[ADMIN_EMAIL] = {
        "contact": ADMIN_EMAIL,
        "roles": ["Tất cả thể loại"],
        "expires_at": "2099-12-31"
    }
    save_licensed_accounts(st.session_state.licensed_accounts)

# ==============================================================================
# HÀM XỬ LÝ ĐĂNG NHẬP (HỖ TRỢ NHẤN ENTER)
# ==============================================================================
def process_login(login_val):
    input_val = login_val.strip()
    if not input_val:
        return
    if input_val == ADMIN_EMAIL or input_val in st.session_state.licensed_accounts:
        if input_val != ADMIN_EMAIL:
            acc_info = st.session_state.licensed_accounts[input_val]
            exp_date_str = acc_info.get("expires_at", "2099-12-31")
            try:
                exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d")
                if datetime.now() > exp_date:
                    st.error(f"❌ Tài khoản đã hết hạn vào ngày {exp_date_str}!")
                    return
            except Exception:
                pass
        st.session_state.is_logged_in = True
        st.session_state.current_user_email = input_val
        st.success("🎉 Đăng nhập thành công!")
        st.rerun()
    else:
        st.error("❌ Tài khoản chưa được cấp quyền!")

# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown("### 🔐 **Đăng Nhập Hệ Thống**")
    if "is_logged_in" not in st.session_state:
        st.session_state.is_logged_in = False
    if "current_user_email" not in st.session_state:
        st.session_state.current_user_email = ""

    if not st.session_state.is_logged_in:
        with st.form("login_form", clear_on_submit=False):
            login_input = st.text_input("Nhập Email / SĐT của bạn:", placeholder="vd: user@gmail.com")
            submitted_login = st.form_submit_button("🔑 Đăng Nhập", use_container_width=True)
            if submitted_login:
                process_login(login_input)
    else:
        st.success(f"👤 Đang đăng nhập: **{st.session_state.current_user_email}**")
        if st.button("🚪 Đăng Xuất", use_container_width=True):
            st.session_state.is_logged_in = False
            st.session_state.current_user_email = ""
            st.rerun()

    st.markdown("""
    <div class="support-box">
        <b style="color: #166534; font-size: 0.95rem;">💬 Cần Hỗ Trợ / Mua Gói?</b><br>
        <p style="font-size: 0.85rem; color: #15803d; margin: 6px 0 8px 0;">Kết nối ngay với chúng tôi:</p>
        <a href="https://zalo.me/0968484369" target="_blank" style="display: inline-block; background: #0068ff; color: white; padding: 5px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 11px; margin: 2px;">📱 Zalo Chat</a>
        <a href="#" target="_blank" style="display: inline-block; background: #1877f2; color: white; padding: 5px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 11px; margin: 2px;">📘 Facebook</a>
        <a href="#" target="_blank" style="display: inline-block; background: #010101; color: white; padding: 5px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 11px; margin: 2px;">🎬 TikTok</a>
        <div style="font-weight: 700; color: #166534; font-size: 12px; margin-top: 8px;">📞 Hotline: 096 8484 369</div>
    </div>
    """, unsafe_allow_html=True)

    IS_ADMIN = (st.session_state.current_user_email == ADMIN_EMAIL)
    if st.session_state.is_logged_in and IS_ADMIN:
        st.markdown("---")
        st.markdown("### ⚙️ **Quản Lý Tài Khoản (Admin)**")
        with st.form("add_license_form"):
            new_account_id = st.text_input("Thêm Email / SĐT mới:", placeholder="khachhang@gmail.com")
            assigned_modules = st.multiselect(
                "Phân quyền chức năng:",
                options=[
                    "🛒 TikTok Shop & Bán Hàng", "👶 Mẹ & Bé & Cùng Con Học", "📺 TVC Quảng Cáo & Thương Hiệu",
                    "🏡 Nhà Cửa & Kiến Trúc", "🌿 Du Lịch & Phong Cảnh", "🚗 Xe Cộ & Trải Nghiệm Lái",
                    "🍲 Ẩm Thực & Đời Sống", "📖 Đời Sống & Giáo Dục", "🏛️ Lịch Sử & Di Sản", "🧘 Chữa Lành & Lifestyle"
                ],
                default=["🛒 TikTok Shop & Bán Hàng"]
            )
            duration_option = st.selectbox("Thời hạn sử dụng:", options=["Dùng thử 3 ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "2 Năm", "3 Năm", "5 Năm", "10 Năm", "Vĩnh viễn (Trọn đời)"], index=0)
            if st.form_submit_button("➕ Cấp Quyền Truy Cập", use_container_width=True):
                if new_account_id.strip():
                    if "Vĩnh viễn" in duration_option:
                        expiry_date = "2099-12-31"
                    elif "Dùng thử 3 ngày" in duration_option:
                        expiry_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                    else:
                        num_map = {"1 Tháng": 1, "3 Tháng": 3, "6 Tháng": 6, "1 Năm": 12, "2 Năm": 24, "3 Năm": 36, "5 Năm": 60, "10 Năm": 120}
                        months = num_map.get(duration_option, 1)
                        expiry_date = (datetime.now() + timedelta(days=months * 30)).strftime("%Y-%m-%d")

                    st.session_state.licensed_accounts[new_account_id.strip()] = {
                        "contact": new_account_id.strip(), "roles": assigned_modules, "expires_at": expiry_date
                    }
                    save_licensed_accounts(st.session_state.licensed_accounts)
                    st.success(f"✅ Đã cấp quyền cho {new_account_id}!")
                    st.rerun()

    if st.session_state.is_logged_in:
        st.markdown("---")
        st.markdown("### 🗂️ **Quản Lý Dự Án**")
        project_title_input = st.text_input("Tên dự án:", value=st.session_state.get("active_project_title", "Chiến dịch mới"))
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("💾 Lưu", use_container_width=True):
                if st.session_state.all_scripts:
                    p_id = f"proj_{int(time.time())}"
                    st.session_state.projects_library[p_id] = {
                        "title": project_title_input, "mode": st.session_state.get("selected_mode"),
                        "style": st.session_state.get("selected_style"), "content_analysis": st.session_state.content_analysis,
                        "all_scripts": st.session_state.all_scripts, "cloned_scripts": st.session_state.cloned_scripts,
                        "expanded_scripts": st.session_state.expanded_scripts, "generated_details": st.session_state.generated_details
                    }
                    st.success("✅ Đã lưu dự án!")
        with col_p2:
            if st.session_state.projects_library:
                proj_keys = list(st.session_state.projects_library.keys())
                selected_load_id = st.selectbox("Chọn dự án:", options=proj_keys, format_func=lambda x: st.session_state.projects_library[x]["title"], label_visibility="collapsed")
                if st.button("📂 Mở", use_container_width=True):
                    p_data = st.session_state.projects_library[selected_load_id]
                    st.session_state.active_project_title = p_data["title"]
                    st.session_state.content_analysis = p_data["content_analysis"]
                    st.session_state.all_scripts = p_data["all_scripts"]
                    st.session_state.cloned_scripts = p_data["cloned_scripts"]
                    st.session_state.expanded_scripts = p_data["expanded_scripts"]
                    st.session_state.generated_details = p_data["generated_details"]
                    st.rerun()

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
                setTimeout(() => {{ btn.innerText = old; }}, 2000);
            }});
        ' style="background: linear-gradient(135deg, #ff4b4b 0%, #ff7300 100%); color: white; border: none; padding: 8px 16px; font-size: 13px; font-weight: 700; border-radius: 6px; cursor: pointer; width: 100%;">{button_label}</button>
    </div>
    """
    components.html(html_code, height=48)

def clean_and_parse_json(text_content: str):
    cleaned = text_content.strip()
    if cleaned.startswith("```json"): cleaned = cleaned[7:]
    elif cleaned.startswith("```"): cleaned = cleaned[3:]
    if cleaned.endswith("```"): cleaned = cleaned[:-3]
    parsed = json.loads(cleaned.strip())
    if isinstance(parsed, list) and len(parsed) > 0: parsed = parsed[0]
    return parsed

def optimize_image_for_api(image: Image.Image, max_dimension: int = 896, quality: int = 85) -> Image.Image:
    img = image.convert("RGB") if image.mode != "RGB" else image.copy()
    if max(img.size) > max_dimension: img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True)
    buffer.seek(0)
    return Image.open(buffer)

def format_analysis_field(field_val) -> str:
    if isinstance(field_val, dict):
        return "<br>".join([f"• <b>{k.replace('_', ' ').title()}:</b> {v}" for k, v in field_val.items()])
    elif isinstance(field_val, list):
        return "<br>".join([f"• {item}" for item in field_val])
    
    text = str(field_val)
    keywords = ["Chức năng:", "Tài chính:", "Cảm xúc:", "1.", "2.", "3.", "•", "-"]
    for kw in keywords:
        if kw in text and not text.startswith(kw):
            text = text.replace(kw, f"<br><br>• <b>{kw.replace(':', '')}</b>:")
    return text.replace("\n", "<br>")

def get_system_instructions(mode: str, style: str) -> str:
    base = r"""
BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL ĐA NĂNG CHO IMAGEN 3 VÀ VEO 3.
PHONG CÁCH KẾT XUẤT THỊ GIÁC: """ + style.upper() + r"""
QUY TẮC ĐẠO DIỄN & LỜI THOẠI BẮT BUỘC:
1. THỜI LƯỢNG MỖI CẢNH: CHỈ DÙNG 3 MỐC: 4s, 6s, 8s. TUYỆT ĐỐI CẤM DÙNG MỐC 10 GIÂY.
2. 100% CÁC PHÂN CẢNH ĐỀU PHẢI CÓ LỜI THOẠI (VOICEOVER).
3. ĐỊNH MỨC TỪ VỰNG: Cảnh 4s (10-12 từ), Cảnh 6s (15-18 từ), Cảnh 8s (22-25 từ). Giọng miền Bắc chuẩn Hà Nội.
4. Màn hình sạch: Tuyệt đối không text overlay, không sub nổi, không logo, không watermark.
"""
    if mode == "🛒 TikTok Shop & Bán Hàng":
        return base + r"""
CHẾ ĐỘ: TIKTOK SHOP & SẢN PHẨM CHUYỂN ĐỔI (BẮT BUỘC ƯU TIÊN DEAL & GIÁ XƯỞNG)
- Luôn nhấn mạnh yếu tố GIÁ TẬN GỐC TẠI XƯỞNG / KHO / SHOWROOM và deal sốc giới hạn giờ.
- Ma trận nỗi đau & mong muốn: Bóc tách 3 tầng (Chức năng, Tài chính - giá hời, Cảm xúc).
"""
    return base

def generate_with_smart_retry(contents, system_inst, max_tokens=16384):
    for attempt in range(6):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash", contents=contents,
                config=types.GenerateContentConfig(system_instruction=system_inst, response_mime_type="application/json", max_output_tokens=max_tokens, temperature=0.7)
            )
            return clean_and_parse_json(response.text)
        except Exception as e:
            if "429" in str(e): time.sleep(35)
            elif "503" in str(e): time.sleep(3 * (attempt + 1))
            else: raise e
    raise Exception("Quá giới hạn thử lại.")

def create_scene_details_for_id(target_id: int, current_mode: str, current_style: str):
    all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_sources if isinstance(sc, dict) and sc.get("id") == target_id), None)
    if not outline: return
    with st.spinner(f"Đang dựng kịch bản chi tiết #{target_id}..."):
        prompt_detail = f"""
        Ý tưởng kịch bản: ID {target_id} - {outline.get('title')} ({current_mode})
        Bối cảnh: {outline.get('setting_style')} | Góc tiếp cận: {outline.get('angle')} | Hook: {outline.get('target_hook')}
        QUY ĐỊNH: Thời lượng 'duration' chỉ dùng '4s', '6s', '8s'. Xuất chuẩn 1 Dict JSON:
        {{
          "id": {target_id}, "title": "{outline.get('title')}", "setting_style": "{outline.get('setting_style')}",
          "voice_profile": {json.dumps(outline.get('voice_profile', {}), ensure_ascii=False)},
          "total_estimated_duration": "24s",
          "scenes": [{{"scene_number": 1, "duration": "4s", "scene_setting": "...", "transition_type": "Hard Cut", "voice_director_vn": "...", "voiceover_vi": "...", "image_prompt": "...", "video_prompt": "..."}}]
        }}
        """
        try:
            res = generate_with_smart_retry([prompt_detail], get_system_instructions(current_mode, current_style))
            st.session_state.generated_details[target_id] = res
            st.session_state.active_script_id = target_id
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi: {e}")

def add_five_scripts_continuation(current_mode: str, current_style: str):
    with st.spinner("Đang bổ sung 5 kịch bản mới..."):
        all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
        cur_len = len(all_sources)
        prompt_more = f"Tạo thêm đúng 5 kịch bản mới (id từ {cur_len + 1} đến {cur_len + 5}) với các key: id, title, setting_style, angle, target_hook, recommended_scenes_count, voice_profile. Xuất JSON key 'script_outlines'."
        try:
            res = generate_with_smart_retry([prompt_more], get_system_instructions(current_mode, current_style))
            new_scripts = res.get("script_outlines", [])
            for i, sc in enumerate(new_scripts): sc["id"] = cur_len + i + 1
            st.session_state.expanded_scripts.extend(new_scripts)
            st.success("✅ Đã thêm 5 kịch bản!")
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi: {e}")

# ==============================================================================
# GIAO DIỆN CHÍNH
# ==============================================================================
st.markdown("""
<div class="header-container">
    <div class="header-badge">🌟 UNIVERSAL AI VIDEO STUDIO PRO</div>
    <div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ</div>
    <div class="sub-title">TikTok Shop, Mẹ & Bé Viral, TVC Điện Ảnh, Phim Đời Sống & Giáo Dục</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.is_logged_in:
    st.warning("⚠️ **Vui lòng đăng nhập ở thanh Sidebar bên trái để bắt đầu.**")
    st.stop()

col_mode, col_style = st.columns([1.5, 1])
with col_mode:
    selected_mode = st.selectbox("🎯 Chọn Thể Loại Nội Dung:", options=[
        "🛒 TikTok Shop & Bán Hàng", "👶 Mẹ & Bé & Cùng Con Học (Viral Parenting)", "📺 TVC Quảng Cáo & Thương Hiệu Cao Cấp",
        "🏡 Nhà Cửa, Kiến Trúc & Cảnh Quan", "🌿 Du Lịch & Phong Cảnh Đất Nước", "🚗 Xe Cộ & Trải Nghiệm Lái",
        "🍲 Ẩm Thực & Trải Nghiệm Đời Sống", "📖 Đời Sống & Bài Học Giáo Dục", "🏛️ Lịch Sử & Tín Ngưỡng Di Sản", "🧘 Chữa Lành & Phong Cách Sống"
    ])
with col_style:
    selected_style = st.selectbox("🎨 Chọn Phong Cách Hình Ảnh:", options=[
        "Cinematic Realism (Người thật / Siêu thực 8K)", "3D Pixar / Disney Animation", "2D Ghibli / Anime Art",
        "Tranh Thủy Mặc Cổ Phong", "Cyberpunk / Sci-Fi Neon", "Vintage / Retro Film 1980s-90s",
        "Minimalist Studio / Commercial Clean", "Dark Moody / Noir", "Paper Cut-out / Stop Motion"
    ])

# Bảng Cẩm Nang Phối Hợp Đầy Đủ 10 Thể Loại (Cheat Sheet)
with st.expander("💡 Bấm vào đây để xem Bảng Gợi Ý Phối Hợp 'Thể Loại & Phong Cách' Chuẩn Xác Nhất", expanded=False):
    st.markdown("""
    <div style="background-color: #f8fafc; padding: 16px; border-radius: 12px; border: 1.5px solid #e2e8f0; font-size: 0.95rem; color: #334155;">
        <h4 style="color: #0f172a; margin-top: 0; margin-bottom: 12px; font-size: 1.05rem;">🎯 Cẩm Nang Phối Hợp Sáng Tạo Nội Dung Đa Vũ Trụ</h4>
        <ul style="padding-left: 20px; line-height: 1.8; margin-bottom: 0;">
            <li><b>🛒 TikTok Shop & Bán Hàng:</b> Phù hợp nhất với <code style="color: #e11d48;">Minimalist Studio / Commercial Clean</code> hoặc <code style="color: #e11d48;">Cyberpunk / Sci-Fi Neon</code> (đồ công nghệ).</li>
            <li><b>👶 Mẹ & Bé & Cùng Con Học:</b> Tối ưu với <code style="color: #e11d48;">Paper Cut-out / Stop Motion</code> hoặc <code style="color: #e11d48;">3D Pixar / Disney Animation</code> (ấm áp, an toàn).</li>
            <li><b>📺 TVC Quảng Cáo Cao Cấp:</b> Nên chọn <code style="color: #e11d48;">Cinematic Realism (8K)</code> hoặc <code style="color: #e11d48;">Dark Moody / Noir</code> (sang trọng, kịch tính).</li>
            <li><b>🏡 Nhà Cửa & Kiến Trúc:</b> Kết hợp <code style="color: #e11d48;">Cinematic Realism</code> (hiện đại) hoặc <code style="color: #e11d48;">Vintage / Retro Film</code> (hoài niệm).</li>
            <li><b>🌿 Du Lịch & Phong Cảnh:</b> Sử dụng <code style="color: #e11d48;">Cinematic Realism</code> (hùng vĩ) hoặc <code style="color: #e11d48;">Tranh Thủy Mặc Cổ Phong</code> (vùng cao, tâm linh).</li>
            <li><b>🚗 Xe Cộ & Trải Nghiệm Lái:</b> Tối ưu với <code style="color: #e11d48;">Cinematic Realism</code> kết hợp <code style="color: #e11d48;">Cyberpunk / Sci-Fi Neon</code> (tốc độ, ánh sáng đèn).</li>
            <li><b>🍲 Ẩm Thực & Đời Sống:</b> Sử dụng <code style="color: #e11d48;">Vintage / Retro Film</code> hoặc <code style="color: #e11d48;">Minimalist Studio</code> (tôn vinh món ăn).</li>
            <li><b>📖 Đời Sống & Giáo Dục:</b> Phù hợp với <code style="color: #e11d48;">2D Ghibli / Anime Art</code> hoặc <code style="color: #e11d48;">Paper Cut-out</code> (gần gũi, nhân văn).</li>
            <li><b>🏛️ Lịch Sử & Tín Ngưỡng Di Sản:</b> Tối ưu tuyệt đối bằng <code style="color: #e11d48;">Tranh Thủy Mặc Cổ Phong</code> hoặc <code style="color: #e11d48;">Dark Moody / Noir</code> (cổ kính, huyền bí).</li>
            <li><b>🧘 Chữa Lành & Lifestyle:</b> Kết hợp <code style="color: #e11d48;">Minimalist Studio</code> hoặc <code style="color: #e11d48;">Cinematic Realism</code> (bình yên, thư thái).</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
input_text = st.text_area("✍️ Tóm tắt ý tưởng, chủ đề hoặc mô tả chi tiết sản phẩm:", height=100)
uploaded_files = st.file_uploader("🖼️ Tải ảnh tham chiếu (Tùy chọn):", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if st.button("🚀 Bắt Đầu Phân Tích Sản Phẩm & Lên Trận Kịch Bản", type="primary", use_container_width=True, disabled=not (input_text.strip() or uploaded_files)):
    with st.spinner("Đang xử lý hình ảnh và phân tích chuyên sâu dữ liệu đầu vào..."):
        prompt = f"Phân tích chuyên sâu cho '{selected_mode}' phong cách '{selected_style}'. Nội dung: '{input_text.strip() if input_text else 'Phân tích qua hình ảnh đính kèm.'}'."
        try:
            # Xử lý an toàn danh sách ảnh tải lên để truyền vào SDK Gemini
            optimized_images = []
            if uploaded_files:
                for f in uploaded_files:
                    img_pil = Image.open(f)
                    optimized_images.append(optimize_image_for_api(img_pil))
            
            api_payload = [*optimized_images, prompt] if optimized_images else [prompt]
            res = generate_with_smart_retry(api_payload, get_system_instructions(selected_mode, selected_style))
            
            st.session_state.content_analysis = res.get("content_analysis")
            st.session_state.all_scripts = res.get("script_outlines", [])
            st.session_state.cloned_scripts, st.session_state.expanded_scripts, st.session_state.generated_details, st.session_state.active_script_id = [], [], {}, None
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi xử lý API: {e}")

# Hiển thị DNA Phân tích với các ý ngắt dòng rõ ràng
if st.session_state.content_analysis and isinstance(st.session_state.content_analysis, dict):
    st.divider()
    st.markdown(f"### 🔍 **Phân Tích DNA Chi Tiết Đa Tầng — [{selected_mode.upper()}]**")
    ca = st.session_state.content_analysis
    with st.container(border=True):
        st.markdown("##### 🏭 **1. Thông số Cốt lõi & Chi tiết đặc thù:**")
        st.markdown(f"<div style='line-height: 1.8;'>{format_analysis_field(ca.get('mechanical_and_accessories', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 🎯 **2. Ma trận Nỗi đau & Tâm lý:**")
        st.markdown(f"<div style='line-height: 1.8;'>{format_analysis_field(ca.get('customer_pain_points', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 💡 **3. Mong muốn cốt lõi & USP:**")
        st.markdown(f"<div style='line-height: 1.8;'>• <b>Mong muốn:</b> {format_analysis_field(ca.get('core_desires', 'N/A'))}<br>• <b>USP / Slogan:</b> {format_analysis_field(ca.get('emotional_or_usp_hook', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### ⚙️ **4. Quy chuẩn Vật lý:**")
        st.markdown(f"<div style='line-height: 1.8;'>{format_analysis_field(ca.get('visual_physics_rules', 'N/A'))}</div>", unsafe_allow_html=True)
    st.markdown("##### 📌 **Chuỗi khóa thị giác (Visual DNA Lock):**")
    st.code(format_analysis_field(ca.get('prompt_dna_lock', 'N/A')), language="text")

# GIAI ĐOẠN 1: DANH SÁCH KỊCH BẢN BAN ĐẦU
if st.session_state.all_scripts and st.session_state.active_script_id is None:
    st.divider()
    st.markdown(f"### 📋 **Danh Sách 5 Ma Trận Kịch Bản Thực Chiến**")
    for outline in st.session_state.all_scripts:
        sc_id = outline.get("id")
        col_info, col_act = st.columns([3, 1.2])
        with col_info:
            st.markdown(f"**{sc_id}. {outline.get('title')}** — <span class='badge-pending'>CHƯA TẠO CHI TIẾT</span>", unsafe_allow_html=True)
            st.caption(f"🏛️ Bối cảnh: {outline.get('setting_style')} | ⚡ Hook: *\"{outline.get('target_hook')}\"*")
        with col_act:
            if st.button("✨ Tạo chi tiết kịch bản này", key=f"btn_init_{sc_id}", use_container_width=True):
                create_scene_details_for_id(sc_id, selected_mode, selected_style)
    st.markdown("---")
    if st.button("➕ Gọi Thêm 5 Kịch Bản Khác", key="btn_add_more_1", type="primary", use_container_width=True):
        add_five_scripts_continuation(selected_mode, selected_style)

# GIAI ĐOẠN 2: CHI TIẾT KỊCH BẢN & BỐ CỤC (TRÁI: NHÂN BẢN & GỌI THÊM | PHẢI: DANH SÁCH KỊCH BẢN)
if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details:
    st.divider()
    active_script = st.session_state.generated_details[st.session_state.active_script_id]
    if isinstance(active_script, list): active_script = active_script[0]

    vp = active_script.get("voice_profile", {})
    st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(active_script.get('title', '')).upper()}**")
    st.info(f"⏱️ Tổng thời lượng: **{active_script.get('total_estimated_duration', '24s')}** | 🎙️ Giọng: **{vp.get('gender', 'Nữ')} miền Bắc ({vp.get('age_range', '25-30')})**")

    for scene in active_script.get("scenes", []):
        sc_num = scene.get("scene_number", 1)
        dur = scene.get("duration", "6s")
        st.markdown(f"#### **📍 Phân cảnh {sc_num} ({dur}) — [ {scene.get('transition_type', 'Hard Cut')} ]**")
        st.markdown(f"🏛️ **Bối cảnh:** *{scene.get('scene_setting')}*")
        st.markdown(f"**💬 Lời thoại miền Bắc:** `\"{scene.get('voiceover_vi')}\"`")
        
        img_p = scene.get('image_prompt', '')
        if img_p:
            st.code(img_p, language="text")
            safe_copy_button(img_p, f"📋 Copy Prompt Ảnh Cảnh {sc_num}")
            
        vid_p = scene.get('video_prompt', '')
        st.code(vid_p, language="text")
        safe_copy_button(vid_p, f"📋 Copy Prompt Video Cảnh {sc_num}")
        st.markdown("---")

    st.markdown("### ⚡ **Khu Vực Quản Trị & Mở Rộng Kịch Bản**")
    
    col_left, col_right = st.columns([1.1, 0.9])

    with col_left:
        # 1. VÙNG NHÂN BẢN KỊCH BẢN WIN (Ở TRÊN)
        st.markdown("""
        <div class="custom-card">
            <div class="card-title-win">🔥 Vùng Nhân Bản Kịch Bản Win (A/B Test)</div>
            <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 8px;">Nhân bản thành 5 biến thể mở đầu khác nhau.</div>
        </div>
        """, unsafe_allow_html=True)

        generated_ids = list(st.session_state.generated_details.keys())
        if generated_ids:
            options_dict = {gid: f"#{gid}. {st.session_state.generated_details[gid].get('title', '')}" for gid in generated_ids}
            selected_win_id = st.selectbox("Chọn kịch bản win cần nhân bản:", options=generated_ids, format_func=lambda x: options_dict[x], key="sel_win_cb")
            
            if st.button("🚀 Nhân Bản 5 Biến Thể Win", type="primary", use_container_width=True):
                with st.spinner("Đang nhân bản biến thể..."):
                    target_script = st.session_state.generated_details[selected_win_id]
                    all_src = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
                    cur_len = len(all_src)
                    prompt_clone = f"Dựa trên kịch bản: {json.dumps(target_script, ensure_ascii=False)}. Tạo đúng 5 biến thể mới (id từ {cur_len+1} đến {cur_len+5}). Xuất JSON key 'cloned_outlines'."
                    try:
                        res_c = generate_with_smart_retry([prompt_clone], get_system_instructions(selected_mode, selected_style))
                        cloned_list = res_c.get("cloned_outlines", [])
                        for idx_c, cl in enumerate(cloned_list): cl["id"] = cur_len + idx_c + 1
                        st.session_state.cloned_scripts.extend(cloned_list)
                        st.success("✅ Đã nhân bản 5 biến thể thành công!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. VÙNG GỌI THÊM KỊCH BẢN MỚI (Ở DƯỚI)
        st.markdown("""
        <div class="custom-card">
            <div class="card-title-add">➕ Vùng Gọi Thêm Kịch Bản Mới</div>
            <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 8px;">Mở rộng thêm ý tưởng từ dữ liệu DNA đã phân tích.</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("➕ Gọi Thêm 5 Tình Huống Kịch Bản Mới", key="btn_add_more_phase2", use_container_width=True):
            add_five_scripts_continuation(selected_mode, selected_style)

    with col_right:
        # CỘT PHẢI: DANH SÁCH TẤT CẢ KỊCH BẢN ĐỂ GỢI Ý/CHUYỂN ĐỔI
        st.markdown("""
        <div class="custom-card" style="background: #f8fafc;">
            <div style="color: #0f172a; font-weight: 800; font-size: 1.1rem; margin-bottom: 10px;">📋 Danh Sách Kịch Bản Hệ Thống</div>
        </div>
        """, unsafe_allow_html=True)

        all_combined_scripts = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
        
        for item in all_combined_scripts:
            it_id = item.get("id")
            is_gen = it_id in st.session_state.generated_details
            badge = '<span class="badge-ready">ĐÃ TẠO</span>' if is_gen else '<span class="badge-pending">CHƯA TẠO</span>'
            is_active = (it_id == st.session_state.active_script_id)
            prefix = "👉 " if is_active else "• "
            
            st.markdown(f"{prefix} **#{it_id}. {item.get('title')}** — {badge}", unsafe_allow_html=True)
            btn_text = "👁️ Xem lại" if is_gen else "✨ Tạo chi tiết"
            if st.button(btn_text, key=f"nav_sc_{it_id}", use_container_width=True):
                if is_gen:
                    st.session_state.active_script_id = it_id
                    st.rerun()
                else:
                    create_scene_details_for_id(it_id, selected_mode, selected_style)
            st.markdown("<hr style='margin: 6px 0;'>", unsafe_allow_html=True)
