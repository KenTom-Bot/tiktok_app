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
    
    /* Phóng to tiêu đề và khung chọn (Selectbox) */
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
    
    /* Thanh hỗ trợ nhanh nổi */
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

def load_licensed_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    default_accounts = {
        "admin@studiopro.com": {
            "contact": "admin@studiopro.com",
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

# ==============================================================================
# SIDEBAR: ĐĂNG NHẬP, QUẢN TRỊ TÀI KHOẢN, HỖ TRỢ & QUẢN LÝ DỰ ÁN
# ==============================================================================
with st.sidebar:
    st.markdown("### 🔐 **Đăng Nhập Hệ Thống**")
    if "is_logged_in" not in st.session_state:
        st.session_state.is_logged_in = False
    if "current_user_email" not in st.session_state:
        st.session_state.current_user_email = ""

    if not st.session_state.is_logged_in:
        login_input = st.text_input("Nhập Email / SĐT của bạn:", placeholder="vd: user@gmail.com")
        if st.button("🔑 Đăng Nhập", use_container_width=True):
            ADMIN_EMAILS = ["admin@studiopro.com", "admin"]
            input_val = login_input.strip()
            
            if input_val in ADMIN_EMAILS or input_val in st.session_state.licensed_accounts:
                if input_val not in ADMIN_EMAILS:
                    acc_info = st.session_state.licensed_accounts[input_val]
                    exp_date_str = acc_info.get("expires_at", "2099-12-31")
                    try:
                        exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d")
                        if datetime.now() > exp_date:
                            st.error(f"❌ Tài khoản của bạn đã hết hạn vào ngày {exp_date_str}. Vui lòng liên hệ Admin để gia hạn!")
                            st.stop()
                    except Exception:
                        pass

                st.session_state.is_logged_in = True
                st.session_state.current_user_email = input_val
                st.success("🎉 Đăng nhập thành công!")
                st.rerun()
            else:
                st.error("❌ Tài khoản chưa được cấp quyền truy cập!")
    else:
        st.success(f"👤 Đang đăng nhập: **{st.session_state.current_user_email}**")
        if st.button("🚪 Đăng Xuất", use_container_width=True):
            st.session_state.is_logged_in = False
            st.session_state.current_user_email = ""
            st.rerun()

    # THÔNG TIN HỖ TRỢ NHANH (ZALO, HOTLINE, FACEBOOK, TIKTOK CHỜ SẴN LINK)
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

    # Chỉ Admin mới nhìn thấy khu vực quản lý tài khoản
    IS_ADMIN = st.session_state.current_user_email in ["admin@studiopro.com", "admin"]

    if st.session_state.is_logged_in and IS_ADMIN:
        st.markdown("---")
        st.markdown("### ⚙️ **Quản Lý Tài Khoản (Admin)**")
        with st.form("add_license_form"):
            new_account_id = st.text_input("Thêm Email / SĐT mới:", placeholder="khachhang@gmail.com")
            
            assigned_modules = st.multiselect(
                "Phân quyền chức năng:",
                options=[
                    "🛒 TikTok Shop & Bán Hàng",
                    "👶 Mẹ & Bé & Cùng Con Học",
                    "📺 TVC Quảng Cáo & Thương Hiệu",
                    "🏡 Nhà Cửa & Kiến Trúc",
                    "🌿 Du Lịch & Phong Cảnh",
                    "🚗 Xe Cộ & Trải Nghiệm Lái",
                    "🍲 Ẩm Thực & Đời Sống",
                    "📖 Đời Sống & Giáo Dục",
                    "🏛️ Lịch Sử & Di Sản",
                    "🧘 Chữa Lành & Lifestyle"
                ],
                default=["🛒 TikTok Shop & Bán Hàng"]
            )
            
            duration_option = st.selectbox(
                "Thời hạn sử dụng:",
                options=[
                    "Dùng thử 3 ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", 
                    "2 Năm", "3 Năm", "5 Năm", "10 Năm", "Vĩnh viễn (Trọn đời)"
                ],
                index=0
            )
            
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
                        "contact": new_account_id.strip(),
                        "roles": assigned_modules,
                        "expires_at": expiry_date
                    }
                    save_licensed_accounts(st.session_state.licensed_accounts)
                    st.success(f"✅ Đã cấp quyền cho {new_account_id} ({duration_option})!")
                    st.rerun()
                else:
                    st.warning("⚠️ Vui lòng nhập thông tin hợp lệ.")

        if st.session_state.licensed_accounts:
            with st.expander(f"📋 Danh sách đã cấp ({len(st.session_state.licensed_accounts)})"):
                for acc, info in st.session_state.licensed_accounts.items():
                    roles_str = ", ".join(info.get("roles", ["Tất cả"]))
                    st.markdown(f"**👤 {acc}**")
                    st.caption(f"• Quyền: {roles_str}<br>• Hết hạn: {info['expires_at']}", unsafe_allow_html=True)
                    st.markdown("---")

    # Khu vực quản lý dự án (Hiển thị cho mọi user đã đăng nhập)
    if st.session_state.is_logged_in:
        st.markdown("---")
        st.markdown("### 🗂️ **Quản Lý Dự Án (Projects)**")
        project_title_input = st.text_input("Tên dự án hiện tại:", value=st.session_state.get("active_project_title", "Chiến dịch mới"))
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("💾 Lưu Dự Án", use_container_width=True):
                if st.session_state.all_scripts:
                    p_id = f"proj_{int(time.time())}"
                    st.session_state.projects_library[p_id] = {
                        "title": project_title_input,
                        "mode": st.session_state.get("selected_mode", "TikTok"),
                        "style": st.session_state.get("selected_style", "Cinematic"),
                        "content_analysis": st.session_state.content_analysis,
                        "all_scripts": st.session_state.all_scripts,
                        "cloned_scripts": st.session_state.cloned_scripts,
                        "expanded_scripts": st.session_state.expanded_scripts,
                        "generated_details": st.session_state.generated_details
                    }
                    st.success(f"✅ Đã lưu dự án thành công!")
                else:
                    st.warning("⚠️ Chưa có kịch bản để lưu!")

        with col_p2:
            if st.session_state.projects_library:
                proj_keys = list(st.session_state.projects_library.keys())
                selected_load_id = st.selectbox("Chọn dự án:", options=proj_keys, format_func=lambda x: st.session_state.projects_library[x]["title"], label_visibility="collapsed")
                if st.button("📂 Mở Lại", use_container_width=True):
                    p_data = st.session_state.projects_library[selected_load_id]
                    st.session_state.active_project_title = p_data["title"]
                    st.session_state.content_analysis = p_data["content_analysis"]
                    st.session_state.all_scripts = p_data["all_scripts"]
                    st.session_state.cloned_scripts = p_data["cloned_scripts"]
                    st.session_state.expanded_scripts = p_data["expanded_scripts"]
                    st.session_state.generated_details = p_data["generated_details"]
                    st.success(f"✅ Đã tải dự án thành công!")
                    st.rerun()

        if st.session_state.all_scripts:
            export_data = json.dumps({
                "title": project_title_input,
                "content_analysis": st.session_state.content_analysis,
                "all_scripts": st.session_state.all_scripts,
                "cloned_scripts": st.session_state.cloned_scripts,
                "expanded_scripts": st.session_state.expanded_scripts,
                "generated_details": st.session_state.generated_details
            }, ensure_ascii=False, indent=2)
            
            st.download_button(
                label="📥 Tải File Dự Án (JSON)",
                data=export_data,
                file_name=f"project_{int(time.time())}.json",
                mime="application/json",
                use_container_width=True
            )

        import_uploaded_file = st.file_uploader("📤 Mở file Dự án từ máy", type=["json"])
        if import_uploaded_file:
            try:
                imported_json = json.load(import_uploaded_file)
                st.session_state.content_analysis = imported_json.get("content_analysis")
                st.session_state.all_scripts = imported_json.get("all_scripts", [])
                st.session_state.cloned_scripts = imported_json.get("cloned_scripts", [])
                st.session_state.expanded_scripts = imported_json.get("expanded_scripts", [])
                st.session_state.generated_details = imported_json.get("generated_details", {})
                st.success("✅ Đã mở dự án thành công từ file!")
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi đọc file: {e}")

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
            color: white; border: none; padding: 8px 16px; font-size: 13px; font-weight: 700;
            border-radius: 6px; cursor: pointer; width: 100%; max-width: 280px;
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
2. 100% CÁC PHÂN CẢNH ĐỀU PHẢI CÓ LỜI THOẠI (VOICEOVER): Đảm bảo mạch truyền tải liên tục, hấp dẫn.
3. QUY CHUẨN ĐỊNH MỨC TỪ VỰNG THEO THỜI LƯỢNG (Khớp hoàn hảo nhịp đọc thực tế, 1s = ~2.5 - 3 từ):
   - Cảnh 4s: Lời thoại tối đa 10 - 12 từ.
   - Cảnh 6s: Lời thoại từ 15 - 18 từ.
   - Cảnh 8s: Lời thoại từ 22 - 25 từ.
4. Giọng đọc: 100% tiếng Việt miền Bắc chuẩn Hà Nội, nêu rõ Giới tính và Độ tuổi, đồng nhất suốt các cảnh.
5. Tích hợp thoại vào Veo 3: Trong 'video_prompt', nhúng nguyên văn lời thoại tiếng Việt có dấu kèm biểu cảm gương mặt và cử chỉ.
6. Màn hình sạch: Tuyệt đối không text overlay, không sub nổi, không logo, không watermark.
"""
    if mode == "🛒 TikTok Shop & Bán Hàng":
        return base + r"""
CHẾ ĐỘ: TIKTOK SHOP & SẢN PHẨM CHUYỂN ĐỔI
- Khóa chặt giải phẫu cơ khí: Màu sắc Hero Color, chất liệu, vị trí nút bấm, cổng sạc, phụ kiện.
- Ma trận nỗi đau & mong muốn: Bóc tách rõ 3 tầng nỗi đau (Chức năng, Tài chính, Cảm xúc).
"""
    elif mode == "👶 Mẹ & Bé & Cùng Con Học (Viral Parenting)":
        return base + r"""
CHẾ ĐỘ: MẸ & BÉ & GIÁO DỤC SỚM (VIRAL PARENTING)
- Khoảnh khắc ấm áp, tương tác tự nhiên giữa mẹ/bố và con nhỏ.
- Phương pháp giáo dục hiện đại: Montessori, STEM tại nhà, học qua chơi, phát triển EQ.
"""
    elif mode == "📺 TVC Quảng Cáo & Thương Hiệu Cao Cấp":
        return base + r"""
CHẾ ĐỘ: TVC QUẢNG CÁO ĐIỆN ẢNH & THƯƠNG HIỆU CAO CẤP
- Ngôn ngữ thị giác điện ảnh: Ánh sáng Dramatic Lighting, Rim Light, tương phản sắc nét.
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
                with st.spinner(f"⏳ Chạm hạn mức tạm thời. Đang chờ {wait_sec}s..."):
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
        st.error(f"Không tìm thấy dữ liệu cho kịch bản ID #{target_id}.")
        return
    
    with st.spinner(f"Đang dựng kịch bản chi tiết #{target_id} '{outline.get('title')}'..."):
        vp = outline.get("voice_profile", {})
        if not isinstance(vp, dict):
            vp = {}
        analysis_info = json.dumps(st.session_state.content_analysis, ensure_ascii=False) if st.session_state.content_analysis else ""
        
        prompt_detail = f"""
        Dựa trên phân tích DNA đầu vào:
        {analysis_info}
        Ý tưởng kịch bản: ID {target_id} - {outline.get('title')} ({current_mode})
        Bối cảnh: {outline.get('setting_style')} | Góc tiếp cận: {outline.get('angle')} | Hook: {outline.get('target_hook')}

        QUY ĐỊNH KỸ THUẬT:
        1. 'image_prompt' (Imagen 3, 9:16): Khóa phong cách {current_style}. Để rỗng ("") nếu là Cảnh nối tiếp.
        2. 'video_prompt' (Veo 3): Động học chuẩn, nhúng lời thoại tiếng Việt có dấu.
        3. THỜI LƯỢNG: 'duration' CHỈ DÙNG '4s', '6s', '8s' (CẤM 10s). Lời thoại khớp nhịp đọc (~3 từ/s).

        Định dạng JSON chuẩn (BẮT BUỘC 1 Dict):
        {{
          "id": {target_id},
          "title": "{outline.get('title')}",
          "setting_style": "{outline.get('setting_style')}",
          "voice_profile": {json.dumps(vp, ensure_ascii=False)},
          "total_estimated_duration": "24s",
          "scenes": [
            {{
              "scene_number": 1,
              "duration": "4s",
              "scene_setting": "Mô tả không gian",
              "transition_type": "Cắt cảnh (Hard Cut)",
              "voice_director_vn": "Chỉ đạo diễn xuất",
              "voiceover_vi": "Lời thoại miền Bắc",
              "image_prompt": "Prompt Imagen 3",
              "video_prompt": "Prompt Veo 3 tích hợp thoại"
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
                st.error("Dữ liệu trả về chưa đúng định dạng Dict.")
                return
            if "voice_profile" not in detail_data or not isinstance(detail_data["voice_profile"], dict):
                detail_data["voice_profile"] = vp

            st.session_state.generated_details[target_id] = detail_data
            st.session_state.active_script_id = target_id
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi tạo chi tiết kịch bản: {e}")

def add_five_scripts_continuation(current_mode: str, current_style: str):
    with st.spinner("Đang tư duy thêm 5 góc tiếp cận kịch bản mới..."):
        all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
        cur_len = len(all_sources)
        analysis_info = json.dumps(st.session_state.content_analysis, ensure_ascii=False) if st.session_state.content_analysis else ""
        
        prompt_more = f"""
        Dựa trên phân tích DNA: {analysis_info}
        Thể loại: {current_mode} | Phong cách: {current_style}
        Tạo thêm ĐÚNG 5 KỊCH BẢN MỚI (id từ {cur_len + 1} đến {cur_len + 5}):
        - title, setting_style, angle, target_hook, recommended_scenes_count (vd: 4), voice_profile.
        - Xuất JSON gồm key 'script_outlines'.
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
            st.success("✅ Đã bổ sung 5 kịch bản mới!")
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi tạo thêm: {e}")

# ==============================================================================
# GIAO DIỆN CHÍNH (CHỈ CHO PHÉP KHI ĐÃ ĐĂNG NHẬP)
# ==============================================================================
st.markdown("""
<div class="header-container">
    <div class="header-badge">🌟 UNIVERSAL AI VIDEO STUDIO PRO</div>
    <div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ</div>
    <div class="sub-title">TikTok Shop, Mẹ & Bé Viral, TVC Điện Ảnh, Phim Đời Sống & Giáo Dục</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.is_logged_in:
    st.warning("⚠️ **Vui lòng nhập Email hoặc Số điện thoại ở thanh bên (Sidebar) bên trái để đăng nhập vào hệ thống sáng tạo.**")
    st.stop()

col_mode, col_style = st.columns([1.5, 1])
with col_mode:
    selected_mode = st.selectbox(
        "🎯 Chọn Thể Loại Nội Dung:",
        options=[
            "🛒 TikTok Shop & Bán Hàng",
            "👶 Mẹ & Bé & Cùng Con Học (Viral Parenting)",
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
st.session_state["selected_mode"] = selected_mode

with col_style:
    selected_style = st.selectbox(
        "🎨 Chọn Phong Cách Hình Ảnh (Visual Style):",
        options=[
            "Cinematic Realism (Người thật / Siêu thực 8K)",
            "3D Pixar / Disney Animation (Hoạt hình 3D cao cấp)",
            "2D Ghibli / Anime Art (Hoạt hình vẽ tay Nhật Bản)",
            "Tranh Thủy Mặc Cổ Phong (Cổ kính / Nghệ thuật)",
            "Cyberpunk / Sci-Fi Neon (Tương lai / Công nghệ cao)",
            "Vintage / Retro Film 1980s-90s (Hoài cổ / Cảm xúc)",
            "Minimalist Studio / Commercial Clean (Tối giản cao cấp)",
            "Dark Moody / Noir (Bí ẩn / Kịch tính / Tương phản mạnh)",
            "Paper Cut-out / Stop Motion (Nghệ thuật cắt giấy / Đất sét)"
        ],
        index=0
    )
st.session_state["selected_style"] = selected_style

# Bảng Cẩm Nang Phối Hợp (Cheat Sheet)
with st.expander("💡 Bấm vào đây để xem Bảng Gợi Ý Phối Hợp 'Thể Loại & Phong Cách' Chuẩn Xác Nhất", expanded=False):
    st.markdown("""
    <div style="background-color: #f8fafc; padding: 16px; border-radius: 12px; border: 1.5px solid #e2e8f0; font-size: 0.95rem; color: #334155;">
        <h4 style="color: #0f172a; margin-top: 0; margin-bottom: 12px; font-size: 1.05rem;">🎯 Cẩm Nang Phối Hợp Sáng Tạo Nội Dung</h4>
        <ul style="padding-left: 20px; line-height: 1.7; margin-bottom: 0;">
            <li><b>🛒 TikTok Shop & Bán Hàng:</b> Phù hợp nhất với <code style="color: #e11d48;">Minimalist Studio / Commercial Clean</code> hoặc <code style="color: #e11d48;">Cyberpunk / Sci-Fi Neon</code> (đồ công nghệ).</li>
            <li><b>👶 Mẹ & Bé & Cùng Con Học:</b> Tối ưu với <code style="color: #e11d48;">Paper Cut-out / Stop Motion</code> hoặc <code style="color: #e11d48;">3D Pixar / Disney Animation</code> (ấm áp, an toàn).</li>
            <li><b>📺 TVC Quảng Cáo Cao Cấp:</b> Nên chọn <code style="color: #e11d48;">Cinematic Realism (8K)</code> hoặc <code style="color: #e11d48;">Dark Moody / Noir</code> (sang trọng, kịch tính).</li>
            <li><b>🏡 Nhà Cửa & Kiến Trúc:</b> Kết hợp <code style="color: #e11d48;">Cinematic Realism</code> (hiện đại) hoặc <code style="color: #e11d48;">Vintage / Retro Film</code> (hoài niệm).</li>
            <li><b>🌿 Du Lịch & Ẩm Thực:</b> Sử dụng <code style="color: #e11d48;">Cinematic Realism</code> (hùng vĩ) hoặc <code style="color: #e11d48;">Vintage / Retro</code> (ấm cúng, ngon miệng).</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 📥 **Dữ Liệu Đầu Vào (Nhập Văn Bản, Tải Ảnh hoặc Cả Hai)**")

prompt_placeholders = {
    "🛒 TikTok Shop & Bán Hàng": "Mô tả sản phẩm, tính năng độc nhất (USP), chương trình khuyến mãi...",
    "👶 Mẹ & Bé & Cùng Con Học (Viral Parenting)": "Nhập chủ đề: Mẹo trị trẻ lười ăn, bộ flashcard học tiếng Anh, đồ chơi STEM...",
    "📺 TVC Quảng Cáo & Thương Hiệu Cao Cấp": "Mô tả sản phẩm/dịch vụ TVC cao cấp...",
    "🏡 Nhà Cửa, Kiến Trúc & Cảnh Quan": "Mô tả căn nhà, biệt thự, căn hộ...",
    "🌿 Du Lịch & Phong Cảnh Đất Nước": "Nhập tên địa danh hoặc ý tưởng du lịch...",
    "🚗 Xe Cộ & Trải Nghiệm Lái": "Nhập dòng xe & bối cảnh lái...",
    "🍲 Ẩm Thực & Trải Nghiệm Đời Sống": "Tên món ăn hoặc quán ăn...",
    "📖 Đời Sống & Bài Học Giáo Dục": "Tóm tắt cốt truyện bài học cuộc sống...",
    "🏛️ Lịch Sử & Tín Ngưỡng Di Sản": "Chủ đề lịch sử/tâm linh...",
    "🧘 Chữa Lành & Phong Cách Sống": "Không gian & thông điệp chữa lành..."
}

input_text = st.text_area(
    f"✍️ Tóm tắt ý tưởng, chủ đề hoặc mô tả chi tiết:",
    placeholder=prompt_placeholders.get(selected_mode, "Nhập thông tin mô tả tại đây..."),
    height=100
)

uploaded_files = st.file_uploader(
    "🖼️ Tải ảnh tham chiếu (Tùy chọn):",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

images = []
if uploaded_files:
    images = [Image.open(f) for f in uploaded_files]
    with st.expander(f"👁️ Xem lại {len(images)} ảnh đã tải lên", expanded=False):
        cols = st.columns(min(len(images), 4))
        for idx, img in enumerate(images):
            cols[idx % 4].image(img, caption=f"Ảnh {idx+1}", use_container_width=True)

can_generate = bool(input_text.strip()) or bool(images)

if st.button("🚀 Bắt Đầu Bóc Tách DNA Chi Tiết & Lên 5 Ma Trận Kịch Bản", type="primary", use_container_width=True, disabled=not can_generate):
    with st.spinner(f"Đang phân tích và xây dựng kịch bản cho '{selected_mode}'..."):
        prompt = f"""
        Phân tích chuyên sâu dữ liệu đầu vào cho thể loại '{selected_mode}' theo phong cách '{selected_style}' và xuất JSON chuẩn xác:
        THÔNG TIN: "{input_text.strip() if input_text.strip() else 'Phân tích từ ảnh.'}"

        YÊU CẦU CẤU TRÚC JSON:
        - "content_analysis": {{"category_or_genre": "...", "mechanical_and_accessories": "...", "customer_pain_points": "...", "core_desires": "...", "emotional_or_usp_hook": "...", "visual_physics_rules": "...", "target_audience": "...", "prompt_dna_lock": "..."}}
        - "script_outlines": [{{"id": 1, "title": "...", "setting_style": "...", "angle": "...", "target_hook": "...", "recommended_scenes_count": "4", "voice_profile": {{"gender": "...", "age_range": "...", "tone": "..."}}}}] (Đúng 5 kịch bản)
        """
        try:
            sys_inst = get_system_instructions(selected_mode, selected_style)
            optimized_images = [optimize_image_for_api(img) for img in images] if images else []
            api_payload = [*optimized_images, prompt] if optimized_images else [prompt]
            
            data = generate_with_smart_retry(api_payload, sys_inst)
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            analysis_data = data.get("content_analysis") or data.get("analysis")
            outlines_data = data.get("script_outlines") or data.get("scripts")

            if not analysis_data or not outlines_data:
                st.error(f"⚠️ Cấu trúc JSON thiếu trường dữ liệu quan trọng.")
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

# Hiển thị DNA Phân tích
if st.session_state.content_analysis and isinstance(st.session_state.content_analysis, dict):
    st.divider()
    st.markdown(f"### 🔍 **Phân Tích DNA Chi Tiết Đa Tầng — [{selected_mode.upper()}]**")
    ca = st.session_state.content_analysis
    with st.container(border=True):
        st.markdown("##### 🏭 **1. Thông số Cốt lõi & Chi tiết đặc thù:**")
        st.markdown(f"<div style='line-height: 1.6;'>{format_analysis_field(ca.get('mechanical_and_accessories', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 🎯 **2. Ma trận Nỗi đau & Tâm lý:**")
        st.markdown(f"<div style='line-height: 1.6;'>{format_analysis_field(ca.get('customer_pain_points', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 💡 **3. Mong muốn cốt lõi & USP:**")
        st.markdown(f"• **Mong muốn:** {format_analysis_field(ca.get('core_desires', 'N/A'))}")
        st.markdown(f"• **USP / Slogan:** {format_analysis_field(ca.get('emotional_or_usp_hook', 'N/A'))}")
        st.markdown("---")
        st.markdown("##### ⚙️ **4. Quy chuẩn Vật lý:**")
        st.markdown(f"<div style='line-height: 1.6;'>{format_analysis_field(ca.get('visual_physics_rules', 'N/A'))}</div>", unsafe_allow_html=True)
    st.markdown("##### 📌 **Chuỗi khóa thị giác (Visual DNA Lock):**")
    st.code(format_analysis_field(ca.get('prompt_dna_lock', 'N/A')), language="text")

# GIAI ĐOẠN 1: DANH SÁCH KỊCH BẢN
if st.session_state.all_scripts and st.session_state.active_script_id is None:
    st.divider()
    st.markdown(f"### 📋 **Danh Sách 5 Ma Trận Kịch Bản Thực Chiến**")
    st.write("Chọn **'✨ Tạo chi tiết kịch bản này'** để phân cảnh chi tiết (4s, 6s, 8s).")

    for outline in st.session_state.all_scripts:
        if not isinstance(outline, dict):
            continue
        sc_id = outline.get("id")
        col_info, col_act = st.columns([3, 1.2])
        with col_info:
            raw_scenes_count = outline.get("recommended_scenes_count", "4")
            scenes_display_text = f"{raw_scenes_count} Phân cảnh" if str(raw_scenes_count).isdigit() else str(raw_scenes_count)
            pacing_badge = f'<span class="badge-dynamic">🎬 {scenes_display_text}</span>'
            
            st.markdown(f"**{sc_id}. {outline.get('title')}** — <span class='badge-pending'>CHƯA TẠO CHI TIẾT</span> {pacing_badge}", unsafe_allow_html=True)
            st.caption(f"🏛️ **Bối cảnh:** {outline.get('setting_style')} | 🎯 **Góc tiếp cận:** {outline.get('angle')} | ⚡ **Hook:** *\"{outline.get('target_hook')}\"*")
        with col_act:
            if st.button("✨ Tạo chi tiết kịch bản này", key=f"btn_init_{sc_id}", use_container_width=True):
                create_scene_details_for_id(sc_id, selected_mode, selected_style)

    st.markdown("---")
    if st.button("➕ Gọi Thêm 5 Kịch Bản Khác", key="btn_add_more_only_one", type="primary", use_container_width=True):
        add_five_scripts_continuation(selected_mode, selected_style)

# GIAI ĐOẠN 2: CHI TIẾT KỊCH BẢN & QUẢN TRỊ
if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details:
    st.divider()
    active_script = st.session_state.generated_details[st.session_state.active_script_id]
    if isinstance(active_script, list) and len(active_script) > 0:
        active_script = active_script[0]

    if isinstance(active_script, dict):
        vp = active_script.get("voice_profile", {})
        if not isinstance(vp, dict):
            vp = {}
        
        st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(active_script.get('title', '')).upper()}**")
        st.info(f"⏱️ **Tổng thời lượng:** **{active_script.get('total_estimated_duration', '24s')}** ({len(active_script.get('scenes', []))} phân cảnh) | 🎨 **Phong cách:** {selected_style} | 🎙️ **Giọng:** **{vp.get('gender', 'Nữ')} miền Bắc ({vp.get('age_range', '25-30')})**")

        for scene in active_script.get("scenes", []):
            if not isinstance(scene, dict):
                continue
            sc_num = scene.get("scene_number", 1)
            trans_type = scene.get("transition_type", "Cắt cảnh (Hard Cut)")
            dur = scene.get("duration", "6s")
            st.markdown(f"#### **📍 Phân cảnh {sc_num} ({dur}) — [ {trans_type} ]**")
            st.markdown(f"🏛️ **Bối cảnh:** *{scene.get('scene_setting', active_script.get('setting_style', ''))}*")
            st.markdown("**🎙️ Đạo diễn giọng đọc:**")
            st.write(scene.get("voice_director_vn", ""))
            st.markdown("**💬 Lời thoại lồng tiếng (100% Miền Bắc):**")
            st.markdown(f"> *\"{scene.get('voiceover_vi', '')}\"*")

            st.markdown(f"**🖼️ Prompt Tạo Ảnh Gốc (Imagen 3 - 9:16):**")
            if "nối tiếp" in str(trans_type).lower() or not scene.get("image_prompt"):
                st.warning("👉 **Lấy ảnh cuối của video trước làm ảnh đầu vào.**")
            else:
                img_p = scene.get("image_prompt", "")
                st.code(img_p, language="text")
                safe_copy_button(img_p, "📋 Copy Prompt Ảnh (Imagen 3)")

            st.markdown(f"**🎥 Prompt Chuyển Động Video (Veo 3):**")
            vid_p = scene.get("video_prompt", "")
            st.code(vid_p, language="text")
            safe_copy_button(vid_p, "📋 Copy Prompt Video (Veo 3)")
            st.markdown("---")

        st.markdown("### ⚡ **Khu Vực Quản Trị & Mở Rộng Kịch Bản**")
        col_win_zone, col_explore_zone = st.columns(2)

        with col_win_zone:
            st.markdown("""
            <div class="custom-card">
                <div class="card-title-win">🔥 Vùng Nhân Bản Kịch Bản Win (A/B Test)</div>
                <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 12px;">Nhân bản thành 5 biến thể mở đầu khác nhau.</div>
            </div>
            """, unsafe_allow_html=True)

            generated_ids = list(st.session_state.generated_details.keys())
            if generated_ids:
                options_dict = {gid: f"#{gid}. {st.session_state.generated_details[gid].get('title', '')}" for gid in generated_ids}
                default_index = generated_ids.index(st.session_state.active_script_id) if st.session_state.active_script_id in generated_ids else 0
                
                selected_win_id = st.selectbox(
                    "Chọn kịch bản win cần nhân bản:",
                    options=generated_ids,
                    index=default_index,
                    format_func=lambda x: options_dict[x],
                    key="select_win_dropdown_universal"
                )
                
                if st.button("🚀 Nhân Bản 5 Biến Thể Win", type="primary", use_container_width=True):
                    with st.spinner("Đang nhân bản biến thể..."):
                        target_win_script = st.session_state.generated_details[selected_win_id]
                        all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
                        cur_len = len(all_sources)
                        
                        prompt_clone = f"""
                        Dựa trên kịch bản win: {json.dumps(target_win_script, ensure_ascii=False)}
                        Thể loại: {selected_mode} | Phong cách: {selected_style}
                        Tạo ĐÚNG 5 BIẾN THỂ WIN MỚI (id từ {cur_len + 1} đến {cur_len + 5}):
                        - Thay đổi hook và bối cảnh mở đầu. Thời lượng cảnh 4s, 6s, 8s.
                        - Xuất JSON gồm key 'cloned_outlines'.
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
                            st.success("✅ Đã nhân bản 5 biến thể thành công!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi nhân bản: {e}")

            if st.session_state.cloned_scripts:
                st.markdown("---")
                st.markdown(f"##### 🎯 **Kịch Bản Nhân Bản ({len(st.session_state.cloned_scripts)}):**")
                for cl_sc in st.session_state.cloned_scripts:
                    c_id = cl_sc.get("id")
                    is_gen = c_id in st.session_state.generated_details
                    badge = '<span class="badge-ready">ĐÃ CÓ CHI TIẾT</span>' if is_gen else '<span class="badge-pending">CHƯA TẠO</span>'
                    st.markdown(f"**• #{c_id}. {cl_sc.get('title')}** — {badge}", unsafe_allow_html=True)
                    btn_lbl = "👁️ Xem chi tiết" if is_gen else "✨ Tạo chi tiết kịch bản này"
                    if st.button(btn_lbl, key=f"btn_clone_{c_id}", use_container_width=True):
                        create_scene_details_for_id(c_id, selected_mode, selected_style)

        with col_explore_zone:
            st.markdown("""
            <div class="custom-card">
                <div class="card-title-add">➕ Vùng Gọi Thêm Kịch Bản Mới</div>
                <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 12px;">Mở rộng thêm ý tưởng từ dữ liệu DNA đã phân tích.</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("➕ Gọi Thêm 5 Tình Huống Kịch Bản Mới", key="btn_add_more_phase2", use_container_width=True):
                add_five_scripts_continuation(selected_mode, selected_style)

            if st.session_state.expanded_scripts:
                st.markdown("---")
                st.markdown(f"##### 🚀 **Vừa Gọi Thêm ({len(st.session_state.expanded_scripts)}):**")
                for ex_sc in st.session_state.expanded_scripts:
                    e_id = ex_sc.get("id")
                    is_ex_gen = e_id in st.session_state.generated_details
                    badge = '<span class="badge-ready">ĐÃ CÓ CHI TIẾT</span>' if is_ex_gen else '<span class="badge-pending">CHƯA TẠO</span>'
                    st.markdown(f"**• #{e_id}. {ex_sc.get('title')}** — {badge}", unsafe_allow_html=True)
                    btn_lbl = "👁️ Xem chi tiết" if is_ex_gen else "✨ Tạo chi tiết kịch bản này"
                    if st.button(btn_lbl, key=f"btn_expand_{e_id}", use_container_width=True):
                        create_scene_details_for_id(e_id, selected_mode, selected_style)
