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

# ==============================================================================
# CẤU HÌNH GIAO DIỆN & CSS CHUYÊN NGHIỆP
# ==============================================================================
st.set_page_config(
    page_title="Universal AI Video Studio Pro & License Manager",
    page_icon="🎬",
    layout="wide"
)

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
    [data-testid="stFileUploader"] { padding: 0px !important; }
    [data-testid="stFileUploader"] > section { padding: 8px !important; }
    
    @keyframes pulse {
        0% { transform: scale(0.98); opacity: 0.8; }
        50% { transform: scale(1.02); opacity: 1; }
        100% { transform: scale(0.98); opacity: 0.8; }
    }
    .loading-pulse {
        animation: pulse 1.5s infinite ease-in-out;
        color: #d90429;
        font-weight: 800;
        text-align: center;
        padding: 25px;
        background: #fef2f2;
        border: 2px dashed #fca5a5;
        border-radius: 12px;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
if not api_key:
    st.error("Chưa cấu hình khóa GEMINI_API_KEY trong phần cấu hình bảo mật (Secrets).")
    st.stop()

client = genai.Client(api_key=api_key)

ACCOUNTS_FILE = "accounts.json"
ADMIN_EMAIL = "binhnguyenmedia.vn@gmail.com"

ALL_MODULES = [
    "🛒 TikTok Shop & Bán Hàng", "👶 Mẹ & Bé & Cùng Con Học (Viral Parenting)", "📺 TVC Quảng Cáo & Thương Hiệu Cao Cấp",
    "🏡 Nhà Cửa, Kiến Trúc & Cảnh Quan", "🌿 Du Lịch & Phong Cảnh Đất Nước", "🚗 Xe Cộ & Trải Nghiệm Lái",
    "🍲 Ẩm Thực & Đời Sống", "📖 Đời Sống & Giáo Dục", "🏛️ Lịch Sử & Tín Ngưỡng Di Sản", "🧘 Chữa Lành & Phong Cách Sống",
    "📢 Tuyên Truyền, Phóng Sự & Thông Điệp Xã Hội", "🏢 Giới Thiệu Doanh Nghiệp & Hồ Sơ Năng Lực"
]

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

for key, default_val in [
    ("content_analysis", None), ("all_scripts", []), ("cloned_scripts", []), 
    ("expanded_scripts", []), ("generated_details", {}), ("active_script_id", None), 
    ("projects_library", {}), ("licensed_accounts", load_licensed_accounts()), 
    ("current_input_context", ""), ("admin_toast_msg", ""), ("is_logged_in", False),
    ("current_user_email", ""), ("active_project_title", "Chiến dịch mới"),
    ("last_loaded_file_id", None), ("file_uploader_key", 0), ("scroll_to_top", False),
    ("action_trigger", None), ("action_param", None), ("character_profiles", [])
]:
    if key not in st.session_state:
        st.session_state[key] = default_val

if st.session_state.scroll_to_top:
    components.html(f"""
        <script>
            setTimeout(function() {{
                var parentDoc = window.parent.document;
                var mainElements = parentDoc.querySelectorAll('.main, .block-container, [data-testid="stAppViewContainer"]');
                mainElements.forEach(function(el) {{ el.scrollTo({{top: 0, behavior: 'smooth'}}); }});
                window.parent.scrollTo({{top: 0, behavior: 'smooth'}});
            }}, 300);
        </script>
    """, height=0)
    st.session_state.scroll_to_top = False

def process_login(login_val):
    input_val = login_val.strip()
    if not input_val: return
    if input_val == ADMIN_EMAIL or input_val in st.session_state.licensed_accounts:
        if input_val != ADMIN_EMAIL:
            acc_info = st.session_state.licensed_accounts[input_val]
            exp_date_str = acc_info.get("expires_at", "2099-12-31")
            try:
                if datetime.now() > datetime.strptime(exp_date_str, "%Y-%m-%d"):
                    st.error(f"❌ Tài khoản đã hết hạn vào ngày {exp_date_str}!")
                    return
            except Exception: pass
        st.session_state.is_logged_in = True
        st.session_state.current_user_email = input_val
        st.rerun()
    else:
        st.error("❌ Tài khoản chưa được cấp quyền!")

def format_analysis_field(field_val) -> str:
    if isinstance(field_val, dict):
        return "<br>".join([f"• <b>{str(k).replace('_', ' ').title()}:</b> {str(v)}" for k, v in field_val.items()])
    elif isinstance(field_val, list):
        return "<br>".join([f"• {str(item)}" for item in field_val])
    
    text = str(field_val).strip()
    text = re.sub(r'<<\.?', '', text)
    text = text.replace('<b>', '').replace('</b>', '')
    text = re.sub(r'(?i)\bnỗi đau\b\s*[:\.-]?', '', text)
    text = re.sub(r'(?i)(?:\b|^)(?:1[\.\)]\s*)?chức năng\s*[:\.-]?', '<br>• <b>Chức năng:</b>', text)
    text = re.sub(r'(?i)(?:\b|^)(?:2[\.\)]\s*)?tài chính\s*[:\.-]?', '<br>• <b>Tài chính:</b>', text)
    text = re.sub(r'(?i)(?:\b|^)(?:3[\.\)]\s*)?cảm xúc\s*[:\.-]?', '<br>• <b>Cảm xúc:</b>', text)
    
    lines = [l.strip() for l in text.split('<br>') if l.strip()]
    formatted_output = []
    for line in lines:
        if line:
            if line.startswith('•'):
                formatted_output.append(f"<div style='margin-top: 6px;'>{line}</div>")
            else:
                formatted_output.append(f"<div style='margin-left: 15px; margin-top: 4px;'>• {line}</div>")
    return "".join(formatted_output) if formatted_output else text

with st.sidebar:
    if not st.session_state.is_logged_in:
        st.markdown("### 🔐 **Đăng Nhập Hệ Thống**")
        with st.form("login_form"):
            login_input = st.text_input("Nhập Email / SĐT:", placeholder="vd: user@gmail.com")
            if st.form_submit_button("🔑 Đăng Nhập", use_container_width=True):
                process_login(login_input)
    
    if st.session_state.is_logged_in:
        st.markdown("### 🗂️ **Quản Lý Dự Án**")
        if st.button("➕ Tạo Dự Án Mới (Làm Mới)", type="primary", use_container_width=True):
            st.session_state.content_analysis = None
            st.session_state.all_scripts = []
            st.session_state.cloned_scripts = []
            st.session_state.expanded_scripts = []
            st.session_state.generated_details = {}
            st.session_state.active_script_id = None
            st.session_state.current_input_context = ""
            st.session_state.active_project_title = "Chiến dịch mới"
            st.session_state.last_loaded_file_id = None  
            st.session_state.file_uploader_key += 1
            st.session_state.scroll_to_top = True
            st.session_state.character_profiles = []
            st.success("✨ Đã tạo dự án mới thành công!")
            time.sleep(0.3)
            st.rerun()

        project_title_input = st.text_input("Tên dự án hiện tại:", value=st.session_state.get("active_project_title", "Chiến dịch mới"))
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("💾 Lưu Dự Án", use_container_width=True):
                p_id = f"proj_{int(time.time())}"
                st.session_state.projects_library[p_id] = {
                    "title": project_title_input, "mode": st.session_state.get("selected_mode"),
                    "style": st.session_state.get("selected_style"), "content_analysis": st.session_state.content_analysis,
                    "all_scripts": st.session_state.all_scripts, "cloned_scripts": st.session_state.cloned_scripts,
                    "expanded_scripts": st.session_state.expanded_scripts, "generated_details": st.session_state.generated_details,
                    "character_profiles": st.session_state.character_profiles
                }
                st.success("✅ Đã lưu vào bộ nhớ ứng dụng!")
        with col_p2:
            export_data = {
                "title": project_title_input, "mode": st.session_state.get("selected_mode"),
                "style": st.session_state.get("selected_style"), "content_analysis": st.session_state.content_analysis,
                "all_scripts": st.session_state.all_scripts, "cloned_scripts": st.session_state.cloned_scripts,
                "expanded_scripts": st.session_state.expanded_scripts, "generated_details": st.session_state.generated_details,
                "character_profiles": st.session_state.character_profiles
            }
            json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
            st.download_button(label="📥 Tải JSON", data=json_str, file_name=f"{project_title_input.replace(' ', '_')}.json", mime="application/json", use_container_width=True)

        if st.session_state.projects_library:
            proj_keys = list(st.session_state.projects_library.keys())
            selected_load_id = st.selectbox("📂 Chọn dự án đã lưu:", options=proj_keys, format_func=lambda x: st.session_state.projects_library[x]["title"])
            if st.button("📂 Mở Dự Án Này", use_container_width=True):
                p_data = st.session_state.projects_library[selected_load_id]
                st.session_state.active_project_title = p_data["title"]
                st.session_state.content_analysis = p_data["content_analysis"]
                st.session_state.all_scripts = p_data["all_scripts"]
                st.session_state.cloned_scripts = p_data["cloned_scripts"]
                st.session_state.expanded_scripts = p_data["expanded_scripts"]
                st.session_state.generated_details = p_data["generated_details"]
                st.session_state.character_profiles = p_data.get("character_profiles", [])
                st.session_state.active_script_id = None
                st.session_state.last_loaded_file_id = None
                st.session_state.file_uploader_key += 1
                st.session_state.scroll_to_top = True
                st.success("✅ Đã mở dự án thành công!")
                time.sleep(0.3)
                st.rerun()

        st.markdown("<div style='font-size: 0.85rem; color: #64748b; margin-top: 8px;'>Hoặc tải file dự án từ máy tính:</div>", unsafe_allow_html=True)
        uploaded_project_file = st.file_uploader("📤 Tải file kịch bản (.json)", type=["json"], label_visibility="collapsed", key=f"project_uploader_{st.session_state.file_uploader_key}")
        
        if uploaded_project_file is not None:
            file_identifier = f"{uploaded_project_file.name}_{uploaded_project_file.size}"
            if st.session_state.get("last_loaded_file_id") != file_identifier:
                try:
                    file_bytes = uploaded_project_file.getvalue()
                    loaded_proj = json.loads(file_bytes.decode("utf-8"))
                    
                    proj_data = loaded_proj
                    if "projects_library" in loaded_proj and isinstance(loaded_proj["projects_library"], dict) and len(loaded_proj["projects_library"]) > 0:
                        proj_data = loaded_proj["projects_library"][list(loaded_proj["projects_library"].keys())[0]]
                    elif "all_scripts" not in loaded_proj and "script_outlines" not in loaded_proj and isinstance(loaded_proj, dict):
                        for k, v in loaded_proj.items():
                            if isinstance(v, dict) and ("all_scripts" in v or "content_analysis" in v):
                                proj_data = v
                                break

                    st.session_state.active_project_title = proj_data.get("title", proj_data.get("project_title", "Dự án tải lên"))
                    st.session_state.content_analysis = proj_data.get("content_analysis", proj_data.get("analysis", None))
                    st.session_state.all_scripts = proj_data.get("all_scripts", proj_data.get("script_outlines", proj_data.get("outlines", [])))
                    st.session_state.expanded_scripts = proj_data.get("expanded_scripts", [])
                    st.session_state.cloned_scripts = proj_data.get("cloned_scripts", [])
                    st.session_state.generated_details = {int(k): v for k, v in proj_data.get("generated_details", proj_data.get("details", {})).items()}
                    st.session_state.character_profiles = proj_data.get("character_profiles", [])
                    
                    st.session_state.active_script_id = None
                    st.session_state.last_loaded_file_id = file_identifier
                    st.session_state.scroll_to_top = True
                    st.success("🎉 Đã khôi phục thành công dự án từ file!")
                    time.sleep(0.4)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi đọc file JSON: {e}")

        if st.session_state.current_user_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙️ **Quản Lý Tài Khoản (Quản Trị)**")
            if st.session_state.admin_toast_msg:
                st.success(st.session_state.admin_toast_msg)
                st.session_state.admin_toast_msg = ""

            with st.form("add_license_form"):
                st.markdown("<b>➕ Cấp Quyền Tài Khoản Mới</b>", unsafe_allow_html=True)
                new_account_id = st.text_input("Email / SĐT khách hàng:")
                assigned_modules = st.multiselect("Phân quyền chức năng:", options=ALL_MODULES, default=["🛒 TikTok Shop & Bán Hàng"])
                duration_option = st.selectbox("Thời hạn:", options=["Dùng thử 3 ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "2 Năm", "3 Năm", "5 Năm", "10 Năm", "Vĩnh viễn (Trọn đời)"], index=0)
                
                if st.form_submit_button("💾 Lưu / Cấp Quyền Mới", use_container_width=True):
                    if new_account_id.strip():
                        expiry_date = "2099-12-31" if "Vĩnh viễn" in duration_option else (datetime.now() + timedelta(days=3 if "Dùng thử" in duration_option else {"1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730, "3 Năm": 1095, "5 Năm": 1825, "10 Năm": 3650}.get(duration_option, 30))).strftime("%Y-%m-%d")
                        st.session_state.licensed_accounts[new_account_id.strip()] = {"contact": new_account_id.strip(), "roles": assigned_modules, "expires_at": expiry_date}
                        save_licensed_accounts(st.session_state.licensed_accounts)
                        st.session_state.admin_toast_msg = f"✅ Đã cấp quyền thành công: {new_account_id.strip()}!"
                        st.rerun()

            if st.session_state.licensed_accounts:
                with st.expander(f"📋 Danh sách tài khoản đã cấp ({len(st.session_state.licensed_accounts)})"):
                    for acc, info in list(st.session_state.licensed_accounts.items()):
                        st.markdown(f"**👤 {acc}**")
                        st.caption(f"• Quyền: {', '.join(info.get('roles', []))}<br>• Hết hạn: {info.get('expires_at')}", unsafe_allow_html=True)
                        if acc != ADMIN_EMAIL and st.button(f"🗑️ Xóa {acc}", key=f"del_acc_{acc}"):
                            del st.session_state.licensed_accounts[acc]
                            save_licensed_accounts(st.session_state.licensed_accounts)
                            st.session_state.admin_toast_msg = f"Đã xóa tài khoản {acc}!"
                            st.rerun()
                        st.markdown("---")

    st.markdown("---")
    st.markdown("""
    <div class="support-box">
        <b style="color: #166534; font-size: 0.95rem;">💬 Cần Hỗ Trợ / Mua Gói?</b><br>
        <p style="font-size: 0.85rem; color: #15803d; margin: 6px 0 8px 0;">Kết nối ngay với chúng tôi:</p>
        <a href="https://zalo.me/0968484369" target="_blank" style="display: inline-block; background: #0068ff; color: white; padding: 5px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 11px; margin: 2px;">📱 Zalo Chat</a>
        <div style="font-weight: 700; color: #166534; font-size: 12px; margin-top: 8px;">📞 Hotline: 096 8484 369</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.is_logged_in:
        st.markdown("---")
        st.markdown("### 👤 **Thông Tin Tài Khoản**")
        st.success(f"Đang đăng nhập: **{st.session_state.current_user_email}**")
        if st.button("🚪 Đăng Xuất", use_container_width=True):
            st.session_state.is_logged_in = False
            st.session_state.current_user_email = ""
            st.rerun()

def safe_copy_button(text_to_copy: str, button_label: str = "📋 Sao Chép Prompt"):
    b64 = base64.b64encode(text_to_copy.encode('utf-8')).decode('utf-8')
    components.html(f"""
    <button onclick='navigator.clipboard.writeText(decodeURIComponent(escape(atob("{b64}"))));this.innerText="✅ Đã sao chép!";setTimeout(()=>this.innerText="{button_label}",2000);' style="background:linear-gradient(135deg, #ff4b4b, #ff7300);color:white;border:none;padding:8px 16px;font-size:13px;font-weight:700;border-radius:6px;cursor:pointer;width:100%;">{button_label}</button>
    """, height=40)

def clean_and_parse_json(text_content: str):
    cleaned = text_content.strip()
    if cleaned.startswith("```json"): cleaned = cleaned[7:]
    elif cleaned.startswith("```"): cleaned = cleaned[3:]
    if cleaned.endswith("```"): cleaned = cleaned[:-3]
    parsed = json.loads(cleaned.strip())
    return parsed[0] if isinstance(parsed, list) and len(parsed) > 0 else parsed

def get_realtime_context():
    now = datetime.now()
    month = now.month
    year = now.year
    if month in [2, 3, 4]: season = "Mùa Xuân"
    elif month in [5, 6, 7]: season = "Mùa Hè"
    elif month in [8, 9, 10]: season = "Mùa Thu (Mùa tựu trường / Back-to-school)"
    else: season = "Mùa Đông (Mùa lễ hội cuối năm / Winter holidays)"
    return f"THỜI GIAN THỰC TẾ HIỆN TẠI LÀ: Tháng {month} năm {year} (Thuộc {season}). BẠN BẮT BUỘC PHẢI điều chỉnh kịch bản (Bối cảnh, Hook, Lý do mua hàng) sao cho logic và PHÙ HỢP VỚI THỜI ĐIỂM {season} này. TUYỆT ĐỐI KHÔNG làm sai lệch mùa vụ thực tế."

def get_system_instructions(mode: str, style: str, aspect_ratio: str, goal: str, target_duration_mins: float = 0.5, char_rules: str = "") -> str:
    is_sales = ("Bán Hàng" in mode or "Sales" in goal)
    is_knowledge = "Chia sẻ kiến thức" in goal or "Review" in goal
    is_story = "Kể chuyện" in goal or "Phim ngắn" in goal
    is_corporate = "Doanh Nghiệp" in mode or "Tuyên Truyền" in mode
    
    format_instruction = "9:16 vertical video format, mobile-first framing" if aspect_ratio == "9:16" else "16:9 widescreen cinematic format, professional movie framing"
    
    # 1. LOGIC KIỂM SOÁT THỜI LƯỢNG (GIỚI HẠN VEO 3 LIMITATION)
    total_seconds = int(target_duration_mins * 60)
    if is_sales:
        duration_rule = "QUY CHUẨN THỜI LƯỢNG BÁN HÀNG (24s - 35s): Phân rã tự động thành số lượng cảnh hợp lý linh hoạt, nhịp độ cực nhanh, tập trung dồn dập vào hook, test thực tế và chốt đơn."
    else:
        duration_rule = f"QUY CHUẨN THỜI LƯỢNG KỂ CHUYỆN / REVIEW DÀI ({target_duration_mins} phút / {total_seconds} giây): Xây dựng cốt truyện có chiều sâu. Vì AI Video (Veo 3) chỉ sinh được video dài tối đa 4s, 6s, 8s, nên bạn BẮT BUỘC phải chia TỔNG {total_seconds} GIÂY thành nhiều phân cảnh nhỏ (chỉ được chọn mốc 4s, 6s hoặc 8s mỗi cảnh). Để làm một hành động kéo dài (VD cảnh dài 16s), hãy chia làm 2 cảnh 8s liên tiếp."

    # 2. LOGIC KIỂM SOÁT TÔNG ĐIỆU (TONE OF VOICE & SCRIPT FLOW)
    if is_sales:
        goal_directive = "MỤC TIÊU 'BÁN HÀNG': Kịch bản đánh thẳng vào nỗi đau, đưa giải pháp, test thực tế và Kêu gọi hành động (CTA) dồn dập."
        tone_instruction = "NHỊP ĐỘ VÀ NĂNG LƯỢNG (PACE & ENERGY): fast-paced, high-energy, enthusiastic sales tone."
    elif is_knowledge:
        goal_directive = "MỤC TIÊU 'CHIA SẺ KIẾN THỨC / REVIEW': Kịch bản phải VÀO THẲNG TRỌNG TÂM ngay giây đầu tiên, lược bỏ hoàn toàn các phần dạo đầu, chào hỏi dài dòng hay văn vẻ. Trình bày thông tin sắc bén, dễ hiểu."
        tone_instruction = "NHỊP ĐỘ VÀ NĂNG LƯỢNG (PACE & ENERGY): fast-paced, engaging, sharp, professional tone. VÀO THẲNG VẤN ĐỀ, tuyệt đối KHÔNG chậm rãi/sâu lắng."
    elif is_story:
        goal_directive = "MỤC TIÊU 'KỂ CHUYỆN / PHIM NGẮN': Xây dựng cao trào, thắt mở nút rõ ràng. Kể chuyện lôi cuốn, chạm vào cảm xúc người xem."
        tone_instruction = "NHỊP ĐỘ VÀ NĂNG LƯỢNG (PACE & ENERGY): expressive, emotional storytelling tone, adaptive pacing. Dẫn dắt cảm xúc tự nhiên."
    elif is_corporate:
        goal_directive = "MỤC TIÊU 'DOANH NGHIỆP / TUYÊN TRUYỀN': Thể hiện sự chuyên nghiệp, quy mô, uy tín của doanh nghiệp/tổ chức. Thông điệp rõ ràng, khúc chiết."
        tone_instruction = "NHỊP ĐỘ VÀ NĂNG LƯỢNG (PACE & ENERGY): confident, professional, authoritative tone, steady pacing."
    else:
        goal_directive = "MỤC TIÊU 'VIRAL / THƯƠNG HIỆU CÁ NHÂN': Cấu trúc kịch bản có Hook cực mạnh ở 3 giây đầu, bắt trend, giữ chân người xem bằng sự tự nhiên và tương tác cao."
        tone_instruction = "NHỊP ĐỘ VÀ NĂNG LƯỢNG (PACE & ENERGY): natural, engaging, dynamic pacing."

    voiceover_instruction = f"""
    7. QUY CHUẨN THUYẾT MINH & ĐỒNG BỘ ÂM THANH (ABSOLUTE AUDIO MATCHING):
       - {goal_directive}
       - CẤM DÙNG GIỌNG THUYẾT MINH PHIM TÀI LIỆU (NO NARRATOR VOICE): Giữa phân cảnh có người và phân cảnh cận sản phẩm (không có người), giọng nói phải là CỦA CÙNG MỘT NGƯỜI (Cùng KOC/Diễn viên đang nói ngoài hình). TUYỆT ĐỐI KHÔNG được chuyển sang giọng đọc phim tài liệu (documentary narrator) đều đều.
       - {tone_instruction} Luôn sử dụng lệnh ép AI giữ nguyên tone này trong mục video_prompt.
       - ĐỒNG NHẤT GIỌNG MIỀN BẮC CHUẨN (HÀ NỘI): Bắt buộc chèn lệnh "strict Northern Vietnamese (Hanoi) accent, absolutely NO Southern or mixed accents" vào MỌI video_prompt để chặn hiện tượng AI tự động chuyển sang giọng Nam.
       - PHIÊN ÂM TIẾNG VIỆT CHUẨN CHO AI (TTS PRONUNCIATION): Trong trường 'voiceover_vi', BẮT BUỘC phải viết rõ cách phát âm tiếng Việt bồi cho các con số, đơn vị đo lường, và từ tiếng Anh để AI Voice không đọc sai hoặc bị ngọng. 
         + Ví dụ: "10.000mAh" -> viết thành "mười nghìn mi li am pe giờ".
         + Ví dụ: "Sale" -> viết thành "seo", "Deal" -> "đi-u", "Voucher" -> "vâu chờ", "Hot" -> "hót", "Size" -> "sái".
    8. QUY CHUẨN TỪ VỰNG DÀNH CHO VIDEO QUAY SẴN (VOD / SHORT VIDEO):
       - Đây KHÔNG PHẢI là video phát trực tiếp. TUYỆT ĐỐI CẤM sử dụng các từ khóa: "livestream", "phiên live", "đang live".
       - Hãy thay thế bằng: "trong video này", "ngay bây giờ", "ngay tại giỏ hàng", "hôm nay".
    """

    master_director_directive = "CHẾ ĐỘ CHUYÊN GIA CAO CẤP: Tối ưu hóa sâu sắc các thông số điện ảnh chuyên sâu (Lighting setup, Lens focal length, Color grading, Camera movement physics) cho Imagen 3 và Veo 3."

    base = f"""
BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL ĐA NĂNG CHO IMAGEN 3 VÀ VEO 3.
PHONG CÁCH KẾT XUẤT THỊ GIÁC: {style.upper()}
ĐỊNH DẠNG KHUNG HÌNH: {format_instruction}
MỤC TIÊU CHIẾN DỊCH: {goal}
{duration_rule}
{master_director_directive}

🛑 QUY TẮC BẮT BUỘC 100% (KHÔNG ĐƯỢC VI PHẠM):
1. QUY TẮC QUỐC TỊCH: Nếu có con người chung chung, BẮT BUỘC chèn "Vietnamese".
{char_rules}
3. MÀN HÌNH SẠCH & GIỮ NGUYÊN LOGO SẢN PHẨM: Tuyệt đối không sinh ra chữ, phụ đề hay watermark rác xung quanh ('no floating text, no subtitles, clean background'). NHƯNG BẮT BUỘC phải giữ nguyên chính xác logo và các dòng chữ có sẵn trên bản thân sản phẩm ('keep exact product logo and typography from reference image').
4. KHÓA KIỂU DÁNG SẢN PHẨM & TỶ LỆ KÍCH THƯỚC (PRODUCT SCALE & OBJECT ANCHOR): Bắt buộc dùng lệnh "featuring the EXACT design, shape, materials, and branding of the PRODUCT REFERENCE IMAGE, maintaining realistic scale and true-to-life proportions" để mô tả sản phẩm. TUYỆT ĐỐI KHÔNG tự bịa ra kiểu dáng hay phóng to sản phẩm sai tỷ lệ thực tế. Bắt buộc phải đánh giá kích thước vật lý dựa trên ảnh tải lên (VD: nhỏ bằng bàn tay, to bằng nửa người, cao đến gối...).
5. CHUYỂN CẢNH THÔNG MINH & NỐI CẢNH DÀI (SMART TRANSITIONS): Cắt cứng dồn dập (Hard Cut) hoặc Chuyển cảnh khớp hành động mượt mà (Match Cut). ĐỐI VỚI CÁC CẢNH DÀI BỊ CẮT NHỎ THÀNH NHIỀU CẢNH 4S/6S/8S: Cảnh sau sẽ phải dùng frame cuối của cảnh trước làm ảnh tham chiếu để tạo video nối tiếp liền mạch.
{voiceover_instruction}
"""
    return base

def call_gemini_api(contents, system_inst):
    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash", contents=contents,
                config=types.GenerateContentConfig(system_instruction=system_inst, response_mime_type="application/json", max_output_tokens=16384, temperature=0.7)
            )
            return clean_and_parse_json(response.text)
        except Exception as e:
            if "429" in str(e): time.sleep(15)
            elif "503" in str(e): time.sleep(3 * (attempt + 1))
            else: raise e
    raise Exception("Lỗi kết nối Gemini API sau nhiều lần thử.")

def generate_char_rules_string(profiles, is_sales_mode=False):
    if not profiles:
        return "2. KHÓA ĐA NHÂN VẬT: Không có nhân vật cụ thể tham chiếu."
        
    rules = "2. KHÓA KHUÔN MẶT KOC VÀ ĐỒNG NHẤT TRANG PHỤC THEO TỪNG KỊCH BẢN:\n   - NGƯỜI DÙNG đã cung cấp ảnh các nhân vật. Bạn PHẢI phân vai tiếng Anh chính xác kèm lệnh khóa như sau:\n"
    for p in profiles:
        rules += f"     + Nhân vật {p['id']}: Đóng vai '{p['role']}'. Lệnh bắt buộc: 'Character {p['id']} ({p['role']}) wearing [trang_phục_đã_chọn_cho_kịch_bản_này] and featuring the exact identity of reference image {p['id']}'.\n"
    rules += "   - KHUÔN MẶT: Bắt buộc dùng lệnh 'featuring the exact identity of reference image X' để AI không tự chế mặt.\n"
    
    if is_sales_mode:
        rules += "   - TRANG PHỤC THỰC TẾ & ĐỒNG NHẤT 100% (NỘI DUNG BÁN HÀNG): App sẽ tự thiết lập 1 bộ trang phục (script_outfit_setup) PHÙ HỢP VỚI THỰC TẾ bối cảnh (Ví dụ: Ở kho xưởng PHẢI LÀ đồng phục thủ kho, áo polo trơn mộc mạc, áo bảo hộ. TUYỆT ĐỐI CẤM mặc áo thun lòe loẹt, đồ đi chơi hay váy vóc diêm dúa sai môi trường). BỘ ĐỒ NÀY PHẢI ĐƯỢC GIỮ NGUYÊN 100% TRONG TOÀN BỘ CÁC CẢNH của kịch bản đó, không cho nhân vật thay đồ giữa chừng."
    else:
        rules += "   - TRANG PHỤC LINH HOẠT THEO NGỮ CẢNH: Trang phục nhân vật có thể thay đổi linh hoạt theo thời gian/không gian của từng phân cảnh (VD: sáng đi làm mặc vest, tối về nhà mặc đồ ngủ) để đảm bảo tính logic câu chuyện."
    
    return rules

# ==============================================================================
# HỆ THỐNG XỬ LÝ LÕI AI (CORE FUNCTIONS)
# ==============================================================================

def add_five_scripts_continuation(current_mode: str, current_style: str, aspect_ratio: str, goal: str, target_duration_mins: float):
    all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    cur_len = len(all_sources)
    product_ctx = st.session_state.get("current_input_context", "Sản phẩm hiện tại")
    dna_data = st.session_state.get("content_analysis", {}) 
    
    is_corporate = "Doanh Nghiệp" in current_mode or "Tuyên Truyền" in current_mode
    is_sales_mode = "Bán Hàng" in current_mode
    is_knowledge = "Chia sẻ kiến thức" in goal or "Review" in goal
    
    if is_corporate:
        extra_rules = "- Bối cảnh không gian văn phòng, nhà xưởng quy mô, dự án thực tế hoặc cộng đồng.\n- Không thúc ép mua hàng."
    elif is_sales_mode:
        extra_rules = "- BẮT BUỘC CHUYỂN ĐỔI GÓC TIẾP CẬN: Hãy tạo 5 kịch bản mới tập trung vào: Review tính năng chi tiết, Đập hộp (Unboxing), Trải nghiệm thực tế (Lifestyle), Feedback khách hàng, Hướng dẫn sử dụng. KHÔNG làm xả kho/kho hàng nữa.\n- TUYỆT ĐỐI KHÔNG ĐƯA MỨC GIÁ CỤ THỂ BẰNG CON SỐ.\n- TUYỆT ĐỐI CẤM SỬ DỤNG TỪ 'LIVESTREAM', 'PHIÊN LIVE'. Dùng 'video này'."
    elif is_knowledge:
        extra_rules = "- VÀO THẲNG VẤN ĐỀ: Bỏ qua hoàn toàn các đoạn chào hỏi, dạo đầu dài dòng. Tập trung 100% vào việc chia sẻ kiến thức hoặc review chuyên sâu."
    else:
        extra_rules = "- Khai thác sâu khía cạnh cảm xúc, trải nghiệm thực tế gia đình/giáo dục."
        
    char_rules_str = generate_char_rules_string(st.session_state.get("character_profiles", []), is_sales_mode)
    realtime_ctx = get_realtime_context()
        
    prompt_more = f"""
    DỮ LIỆU SẢN PHẨM GỐC (DNA): {json.dumps(dna_data, ensure_ascii=False)}
    Ghi chú từ người dùng: "{product_ctx}"
    {realtime_ctx}
    
    Dựa trên thông tin SẢN PHẨM GỐC (DNA) ở trên và kết quả phân tích DNA đã thực hiện cho thể loại '{current_mode}' phong cách '{current_style}'.
    Hãy tạo thêm đúng 5 kịch bản mới (id từ {cur_len + 1} đến {cur_len + 5}) với các key: id, title, setting_style, script_outfit_setup, angle, target_hook, recommended_scenes_count, voice_profile.
    
    QUY ĐỊNH BẮT BUỘC CHO KỊCH BẢN MỚI:
    {extra_rules}
    - Thêm key 'script_outfit_setup': Ghi rõ 1 câu miêu tả trang phục nhân vật PHÙ HỢP NGHIÊM NGẶT THỰC TẾ với bối cảnh của kịch bản này (vd: Áo polo công nhân, Vest công sở...). Bộ đồ này sẽ dùng xuyên suốt kịch bản.
    Xuất JSON chuẩn với key 'script_outlines'.
    """
    try:
        sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins, char_rules_str)
        res = call_gemini_api([prompt_more], sys_inst)
        new_scripts = res.get("script_outlines", [])
        for i, sc in enumerate(new_scripts): sc["id"] = cur_len + i + 1
        st.session_state.expanded_scripts.extend(new_scripts)
        st.session_state.scroll_to_top = True
        st.success("✅ Đã bổ sung 5 kịch bản mới bám sát DNA gốc!")
    except Exception as e:
        st.error(f"❌ Lỗi gọi thêm kịch bản: {e}")

def create_scene_details_for_id(target_id: int, current_mode: str, current_style: str, aspect_ratio: str, goal: str, target_duration_mins: float):
    all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_sources if isinstance(sc, dict) and sc.get("id") == target_id), None)
    if not outline:
        st.error(f"❌ Không tìm thấy thông tin cho kịch bản #{target_id}")
        return
    
    product_ctx = st.session_state.get("current_input_context", "Dự án hiện tại")
    
    # Định tuyến Cảm xúc & Thời lượng (Emotion & Pacing Routing)
    is_sales_mode = "Bán Hàng" in current_mode
    is_knowledge = "Chia sẻ kiến thức" in goal or "Review" in goal
    is_story = "Kể chuyện" in goal or "Phim ngắn" in goal
    is_corporate = "Doanh Nghiệp" in current_mode or "Tuyên Truyền" in current_mode

    if target_duration_mins <= 0.5:
        total_sec = 30
        duration_str = "24s - 35s (Chuyển đổi bán hàng)"
        duration_rule_scene = "Từng phân cảnh CHỈ ĐƯỢC CHỌN mốc: 4s, 6s, hoặc 8s."
    else:
        total_sec = int(target_duration_mins * 60)
        duration_str = f"{total_sec}s ({target_duration_mins} phút)"
        duration_rule_scene = f"TỔNG CỘNG ĐỘ DÀI CÁC CẢNH PHẢI ĐÚNG CHÍNH XÁC {total_sec} GIÂY. QUAN TRỌNG: AI tạo video (Veo 3) chỉ giới hạn sinh video 4s, 6s, 8s. KHÔNG ĐƯỢC phép viết cảnh 10s, 15s. Bạn BẮT BUỘC phải chia những hành động dài thành nhiều cảnh nhỏ 4s/6s/8s nối tiếp nhau."

    if is_sales_mode:
        tone_en = "fast-paced, high-energy, enthusiastic sales tone"
        tone_vn = "nhịp độ nhanh, năng lượng cao, chốt sale"
    elif is_knowledge:
        tone_en = "fast-paced, engaging, sharp, professional tone, absolutely NO slow or overly emotional voice"
        tone_vn = "nhịp độ nhanh, dứt khoát, lôi cuốn, chuyên nghiệp (Tuyệt đối không dùng giọng chậm rãi hay rườm rà)"
    elif is_story:
        tone_en = "expressive, emotional storytelling tone, adaptive pacing"
        tone_vn = "truyền cảm, nhấn nhá theo mạch cảm xúc câu chuyện"
    elif is_corporate:
        tone_en = "confident, professional, authoritative tone, steady pacing"
        tone_vn = "đĩnh đạc, tự tin, chuyên nghiệp, đáng tin cậy"
    else:
        tone_en = "natural, engaging, dynamic pacing"
        tone_vn = "tự nhiên, gần gũi, lôi cuốn, năng lượng linh hoạt"

    # Ép buộc Giới tính phải rõ ràng
    v_profile = outline.get("voice_profile", {})
    if isinstance(v_profile, str):
        fixed_gender = "Nữ"
    elif isinstance(v_profile, dict):
        fixed_gender = v_profile.get("gender", "Nữ")
        if "hay Nữ" in fixed_gender or "/" in fixed_gender or "xác định" in fixed_gender.lower() or not fixed_gender.strip():
            fixed_gender = "Nữ" 
    else:
        fixed_gender = "Nữ"
        
    outfit_setup = outline.get("script_outfit_setup", "casual everyday outfit")
    char_rules_str = generate_char_rules_string(st.session_state.get("character_profiles", []), is_sales_mode)
    realtime_ctx = get_realtime_context()
    
    prompt_detail = f"""
    Ngữ cảnh sản phẩm/dịch vụ: "{product_ctx}"
    Thể loại nội dung: "{current_mode}" | Mục tiêu chiến dịch: "{goal}" | Tỷ lệ khung hình: "{aspect_ratio}"
    {realtime_ctx}
    Ý tưởng kịch bản: ID {target_id} - {outline.get('title')}
    Bối cảnh định hướng: {outline.get('setting_style')} | Góc tiếp cận: {outline.get('angle')} | Hook: {outline.get('target_hook')}
    TRANG PHỤC CỐ ĐỊNH CHO KỊCH BẢN NÀY: {outfit_setup} (Lưu ý: Phải bám sát thực tế bối cảnh).
    
    QUY ĐỊNH ĐẠO DIỄN & LÊN PROMPT TIẾNG ANH (BẮT BUỘC):
    1. KHÓA CỨNG GIỚI TÍNH, TÔNG GIỌNG & NHỊP ĐỘ: Sử dụng 100% giọng đọc của **{fixed_gender}**. Bắt buộc tuân thủ đạo diễn âm thanh: {tone_vn}.
    2. KỶ LUẬT THỜI LƯỢNG VÀ NỐI CẢNH (VEO 3 LIMITATION): Tổng thời lượng mục tiêu là {duration_str}. {duration_rule_scene}
    3. KỸ THUẬT NỐI CẢNH (SEAMLESS CONTINUITY): Đối với các phân cảnh nhỏ được cắt ra từ 1 cảnh dài (để duy trì cùng một hành động/khung hình), tại trường `image_prompt` của cảnh nối tiếp, BẠN CHỈ CẦN GHI LỆNH: "Dùng frame ảnh cuối cùng của phân cảnh trước làm ảnh đầu vào (Image-to-Video) để giữ sự liền mạch tuyệt đối". KHÔNG cần viết lại prompt sinh ảnh mới.
    4. PHIÊN ÂM TIẾNG VIỆT CHUẨN XÁC CHO AI (TTS RULE): BẮT BUỘC viết âm đọc tiếng Việt bồi cho từ khó/tiếng Anh. (Vd: 10.000mAh -> "mười nghìn mi li am pe giờ").
    5. CẤM TỪ LIVESTREAM: TUYỆT ĐỐI KHÔNG dùng từ "livestream", "phiên live".
    6. QUY TRÌNH TRANG PHỤC & KHUÔN MẶT: Nếu là ảnh mới, bắt buộc ép lệnh 'featuring the exact identity of reference image X' và mặc đồ '{outfit_setup}'.
    7. ĐỒNG BỘ GIỌNG ĐỌC NGOÀI HÌNH & MIỀN BẮC (ANTI-SOUTHERN BIAS RULE): Kể cả cảnh cận sản phẩm (không có người), BẮT BUỘC chèn lệnh: "Audio: The exact same {fixed_gender} character speaking. {tone_en}. Strict Northern Vietnamese (Hanoi) accent. ABSOLUTELY NO Southern/Saigon accent. ABSOLUTELY NO documentary narrator voice." vào video_prompt.
    8. KỶ LUẬT CHỐNG VIẾT TẮT (NO SHORTCUT RULE): Bạn TUYỆT ĐỐI KHÔNG ĐƯỢC lười biếng bỏ trống phần `video_prompt`. Mọi `video_prompt` phải lặp lại đầy đủ cấu trúc chỉ đạo âm thanh.
    
    Xuất chuẩn 1 Dict JSON duy nhất:
    {{
      "id": {target_id}, 
      "title": "{outline.get('title')}", 
      "setting_style": "{outline.get('setting_style')}",
      "script_outfit_setup": "{outfit_setup}",
      "voice_profile": {{"gender": "{fixed_gender}", "tone": "{tone_vn}"}},
      "total_estimated_duration": "{duration_str}",
      "scenes": [
        {{
          "scene_number": 1, 
          "duration": "8s", 
          "scene_setting": "Bối cảnh hành động diễn ra dài...", 
          "transition_type": "Mở đầu", 
          "voice_director_vn": "Giọng {fixed_gender} Miền Bắc chuẩn (Hà Nội): {tone_vn} (Nhân vật đang nói)", 
          "voiceover_vi": "Lời thuyết minh tiếng Việt ĐÃ ĐƯỢC PHIÊN ÂM (vd: mười nghìn mi li am pe giờ)", 
          "image_prompt": "Prompt Imagen 3 (tiếng Anh). CÓ NHÂN VẬT THÌ ÉP LỆNH: 'Character X... wearing {outfit_setup} and featuring the exact identity of reference image X'. BẮT BUỘC LỆNH SẢN PHẨM: 'featuring the EXACT design... maintaining realistic scale'", 
          "video_prompt": "Prompt Veo 3 (tiếng Anh). BẮT BUỘC CÓ LỆNH ÂM THANH: 'Audio: The exact same {fixed_gender} character speaking on-camera. {tone_en}. Strict Northern Vietnamese (Hanoi) accent. ABSOLUTELY NO Southern/Saigon accent. Reading: [voiceover_vi]'"
        }},
        {{
          "scene_number": 2,
          "duration": "8s",
          "scene_setting": "Tiếp tục diễn biến kéo dài của cảnh 1 (Nối cảnh để tạo thành 16s)...",
          "transition_type": "Nối liền mạch (Match Cut)",
          "voice_director_vn": "Giọng {fixed_gender} Miền Bắc chuẩn (Hà Nội): {tone_vn}",
          "voiceover_vi": "Lời thuyết minh tiếp theo...",
          "image_prompt": "Dùng frame ảnh cuối cùng của phân cảnh trước (Cảnh 1) làm ảnh đầu vào (Image-to-Video) để giữ sự liền mạch tuyệt đối.",
          "video_prompt": "BẠN PHẢI VIẾT LẠI ĐẦY ĐỦ LỆNH ÂM THANH NHƯ CẢNH 1: 'Audio: The exact same {fixed_gender} character is speaking... {tone_en}... Strict Northern Vietnamese (Hanoi) accent. Reading: [voiceover_vi]'"
        }}
        // TỰ ĐỘNG CHIA & NỐI CÁC CẢNH 3, 4, 5... SAO CHO TỔNG THỜI GIAN CỘNG LẠI BẰNG CHÍNH XÁC QUY ĐỊNH (MỖI CẢNH ĐỀU PHẢI CHỌN ĐÚNG 4s, 6s HOẶC 8s)
      ]
    }}
    """
    try:
        sys_inst = get_system_instructions(current_mode, selected_style, selected_aspect, content_goal, target_duration_mins, char_rules_str)
        res = call_gemini_api([prompt_detail], sys_inst)
        if isinstance(res, list): res = res[0]
        
        st.session_state.generated_details[target_id] = res
        st.session_state.active_script_id = target_id
        st.session_state.scroll_to_top = True
        st.success(f"✅ Đã dựng thành công chi tiết kịch bản #{target_id}!")
    except Exception as e:
        st.error(f"❌ Lỗi dựng chi tiết kịch bản: {e}")

def clone_script_id(target_id, current_mode, current_style, aspect_ratio, goal, target_duration_mins):
    target_script = st.session_state.generated_details[target_id]
    all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    cur_len = len(all_sources)
    is_sales_mode = "Bán Hàng" in current_mode
    char_rules_str = generate_char_rules_string(st.session_state.get("character_profiles", []), is_sales_mode)
    
    p_clone = f"Dựa trên kịch bản: {json.dumps(target_script, ensure_ascii=False)}. Tạo đúng 5 biến thể mới (id từ {cur_len+1} đến {cur_len+5}). Xuất JSON key 'cloned_outlines'."
    sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins, char_rules_str)
    try:
        res_c = call_gemini_api([p_clone], sys_inst)
        cloned_list = res_c.get("cloned_outlines", [])
        for idx_c, cl in enumerate(cloned_list): cl["id"] = cur_len + idx_c + 1
        st.session_state.cloned_scripts.extend(cloned_list)
        st.session_state.scroll_to_top = True
        st.success("✅ Đã nhân bản thành công 5 biến thể mới!")
    except Exception as e:
        st.error(f"❌ Lỗi: {e}")

# ==============================================================================
# 1. KIỂM TRA ĐĂNG NHẬP & BẢO MẬT
# ==============================================================================
st.markdown("""
<div class="header-container">
    <div class="header-badge">🌟 STUDIO VIDEO AI ĐA NĂNG TOÀN DIỆN</div>
    <div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div>
    <div class="sub-title">TikTok Shop, Mẹ & Bé Viral, TVC Điện Ảnh, Phim Đời Sống & Giáo Dục</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.is_logged_in:
    st.info("👈 **Vui lòng đăng nhập ở thanh công cụ bên trái để sử dụng hệ thống.**")
    st.stop() 

# ==============================================================================
# 2. RENDER GIAO DIỆN CẤU HÌNH ĐẦU TIÊN & KHAI BÁO BIẾN TOÀN CỤC
# ==============================================================================
col_mode, col_style = st.columns([1.5, 1])
with col_mode:
    selected_mode = st.selectbox("🎯 Chọn Thể Loại Nội Dung:", options=ALL_MODULES)

# KHAI BÁO CÁC CỜ NHẬN DIỆN (FLAGS) NGAY TẠI ĐÂY
is_sales = "Bán Hàng" in selected_mode
is_corporate = "Doanh Nghiệp" in selected_mode or "Tuyên Truyền" in selected_mode

with col_style:
    selected_style_vn = st.selectbox("🎨 Chọn Phong Cách Hình Ảnh:", options=[
        "Điện Ảnh Chân Thực (Người thật / Siêu thực 8K)", 
        "Hoạt Hình 3D (Kiểu Pixar / Disney)", 
        "Hoạt Hình 2D (Phong cách Ghibli / Anime Nhật Bản)", 
        "Tranh Thủy Mặc Cổ Phong (Truyền thống Á Đông)", 
        "Viễn Tưởng Tương Lai (Cyberpunk / Đèn Neon rực rỡ)", 
        "Phim Cổ Điển Hoài Niệm (Thập niên 80 - 90)", 
        "Studio Tối Giản (Hiện đại, Sạch sẽ, Thương mại)", 
        "Trầm Buồn / Kịch Tính (Tông màu tối, Sınıs động)", 
        "Hoạt Hình Cắt Giấy / Tĩnh Vật (Stop Motion)"
    ])
    
    style_mapping = {
        "Điện Ảnh Chân Thực (Người thật / Siêu thực 8K)": "Cinematic Realism (Người thật / Siêu thực 8K)",
        "Hoạt Hình 3D (Kiểu Pixar / Disney)": "3D Pixar / Disney Animation",
        "Hoạt Hình 2D (Phong cách Ghibli / Anime Nhật Bản)": "2D Ghibli / Anime Art",
        "Tranh Thủy Mặc Cổ Phong (Truyền thống Á Đông)": "Tranh Thủy Mặc Cổ Phong",
        "Viễn Tưởng Tương Lai (Cyberpunk / Đèn Neon rực rỡ)": "Cyberpunk / Sci-Fi Neon",
        "Phim Cổ Điển Hoài Niệm (Thập niên 80 - 90)": "Vintage / Retro Film 1980s-90s",
        "Studio Tối Giản (Hiện đại, Sạch sẽ, Thương mại)": "Minimalist Studio / Commercial Clean",
        "Trầm Buồn / Kịch Tính (Tông màu tối, Sınıs động)": "Dark Moody / Noir",
        "Hoạt Hình Cắt Giấy / Tĩnh Vật (Stop Motion)": "Paper Cut-out / Stop Motion"
    }
    selected_style = style_mapping.get(selected_style_vn, "Cinematic Realism (Người thật / Siêu thực 8K)")

col_ratio, col_goal, col_time = st.columns([1, 1, 1])
with col_ratio:
    aspect_ratio_choice = st.selectbox("Tỷ lệ khung hình video:", ["9:16 (Dọc - TikTok, Reels, Shorts)", "16:9 (Ngang - YouTube, Phim dài, Facebook)"], index=0)
    selected_aspect = "9:16" if "9:16" in aspect_ratio_choice else "16:9"

with col_goal:
    if is_sales:
        content_goal = "Chuyển đổi đơn hàng & Chốt Sale trực tiếp (Sales & Conversion)"
    elif is_corporate:
        content_goal = st.selectbox("Mục đích sản xuất video:", ["Kể chuyện dài tập / Phim tài liệu thương hiệu", "Truyền cảm hứng & Lan tỏa thông điệp xã hội"], index=0)
    else:
        content_goal = st.selectbox("Mục đích sản xuất video:", ["Viral & Xây dựng thương hiệu cá nhân", "Kể chuyện dài tập / Phim ngắn", "Chia sẻ kiến thức / Review chuyên sâu"], index=0)

with col_time:
    if is_sales:
        target_duration_mins = 0.5 
    else:
        target_duration_mins = st.number_input("⏱️ Nhập thời lượng mong muốn (Phút):", min_value=0.5, max_value=30.0, value=1.0, step=0.5)

# CỜ NHẬN DIỆN MỤC TIÊU PHỤ
is_knowledge = "Chia sẻ kiến thức" in content_goal or "Review" in content_goal
is_story = "Kể chuyện" in content_goal or "Phim ngắn" in content_goal

# ==============================================================================
# 3. XỬ LÝ SỰ KIỆN NÚT BẤM (ANTI-STALE UI TRIGGER)
# ==============================================================================
if st.session_state.action_trigger:
    action = st.session_state.action_trigger
    param = st.session_state.action_param
    
    st.session_state.action_trigger = None
    st.session_state.action_param = None
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    if action == "create_detail":
        st.toast(f"⏳ Đang kết nối AI dựng chi tiết kịch bản #{param}...", icon="🎬")
        with st.container(border=True):
            st.markdown(f"<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG XỬ LÝ: Đang dựng chi tiết phân cảnh cho kịch bản #{param}. Quá trình này có thể mất 15-20 giây. Vui lòng đợi...</div>", unsafe_allow_html=True)
            create_scene_details_for_id(param, selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins)
            time.sleep(0.2)
            st.rerun() 
        
    elif action == "clone_script":
        st.toast(f"⏳ Đang nhân bản biến thể cho kịch bản #{param}...", icon="🧬")
        with st.container(border=True):
            st.markdown(f"<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG XỬ LÝ: Đang nhân bản 5 biến thể độc đáo từ kịch bản #{param}. Vui lòng đợi...</div>", unsafe_allow_html=True)
            clone_script_id(param, selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins)
            time.sleep(0.2)
            st.rerun()
        
    elif action == "generate_more":
        st.toast("⏳ Đang suy nghĩ góc tiếp cận mới...", icon="🧠")
        with st.container(border=True):
            st.markdown("<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG XỬ LÝ: Đang phân tích DNA để sáng tạo thêm 5 kịch bản mới. Vui lòng đợi...</div>", unsafe_allow_html=True)
            add_five_scripts_continuation(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins)
            time.sleep(0.2)
            st.rerun()
        
    st.stop() # Dừng toàn bộ code bên dưới để màn hình cũ KHÔNG BỊ VẼ LẠI

# ==============================================================================
# 4. NẾU KHÔNG CÓ HÀNH ĐỘNG NÀO ĐANG CHẠY (RENDER UI THƯỜNG)
# ==============================================================================

with st.expander("💡 Bấm vào đây để xem Bảng Gợi Ý Phối Hợp 'Thể Loại & Phong Cách'", expanded=False):
    st.markdown("""
    <div style="background-color: #f8fafc; padding: 16px; border-radius: 12px; border: 1.5px solid #e2e8f0; font-size: 0.95rem; color: #334155; margin-bottom: 5px;">
        <h4 style="color: #0f172a; margin-top: 0; margin-bottom: 12px; font-size: 1.05rem;">🎯 Cẩm Nang Phối Hợp Sáng Tạo Nội Dung Đa Vũ Trụ</h4>
        <ul style="padding-left: 20px; line-height: 1.8; margin-bottom: 0;">
            <li><b>🛒 TikTok Shop & Bán Hàng:</b> Phù hợp nhất với <code style="color: #e11d48;">Studio Tối Giản (Hiện đại, Sạch sẽ)</code>.</li>
            <li><b>👶 Mẹ & Bé & Cùng Con Học:</b> Tối ưu với <code style="color: #e11d48;">Hoạt Hình Cắt Giấy / Tĩnh Vật</code> hoặc <code style="color: #e11d48;">Hoạt Hình 3D (Kiểu Pixar)</code>.</li>
            <li><b>📺 TVC Quảng Cáo & Thương Hiệu Cao Cấp:</b> Cực kỳ tương thích với <code style="color: #e11d48;">Điện Ảnh Chân Thực (Người thật / Siêu thực 8K)</code>.</li>
            <li><b>🏡 Nhà Cửa, Kiến Trúc & Cảnh Quan:</b> Khuyên dùng <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> hoặc <code style="color: #e11d48;">Studio Tối Giản</code>.</li>
            <li><b>🌿 Du Lịch & Phong Cảnh Đất Nước:</b> Rất hợp với <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> hoặc <code style="color: #e11d48;">Tranh Thủy Mặc Cổ Phong</code>.</li>
            <li><b>🚗 Xe Cộ & Trải Nghiệm Lái:</b> Nên chọn <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> hoặc mang hơi hướng <code style="color: #e11d48;">Phim Cổ Điển Hoài Niệm</code>.</li>
            <li><b>🍲 Ẩm Thực & Đời Sống:</b> Tôn lên vẻ đẹp món ăn với <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> hoặc <code style="color: #e11d48;">Studio Tối Giản</code>.</li>
            <li><b>📖 Đời Sống & Giáo Dục:</b> Khuyên dùng <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> (nếu có KOC) hoặc <code style="color: #e11d48;">Hoạt Hình 2D Ghibli</code>.</li>
            <li><b>🏛️ Lịch Sử & Tín Ngưỡng Di Sản:</b> Đặc biệt hợp với <code style="color: #e11d48;">Tranh Thủy Mặc Cổ Phong</code>.</li>
            <li><b>🧘 Chữa Lành & Phong Cách Sống:</b> Tạo cảm giác nhẹ nhàng với <code style="color: #e11d48;">Hoạt Hình 2D Ghibli</code> hoặc <code style="color: #e11d48;">Trầm Buồn / Kịch Tính</code>.</li>
            <li><b>📢 Tuyên Truyền, Phóng Sự & Thông Điệp Xã Hội:</b> Sử dụng <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> hoặc màu sắc <code style="color: #e11d48;">Trầm Buồn / Kịch Tính</code>.</li>
            <li><b>🏢 Giới Thiệu Doanh Nghiệp & Hồ Sơ Năng Lực:</b> Thể hiện sự chuyên nghiệp bằng <code style="color: #e11d48;">Điện Ảnh Chân Thực</code>.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

if is_sales:
    st.info("💡 **Chế độ Bán Hàng:** Tự động chia số cảnh linh hoạt, trang phục bám sát thực tế kho/xưởng/showroom, chống nhắc 'livestream'.")
else:
    st.info(f"⏱️ **Thời lượng mong muốn:** {target_duration_mins} phút")

st.markdown("---")
input_text = st.text_area("✍️ Tóm tắt ý tưởng, chủ đề hoặc mô tả chi tiết dự án/sản phẩm (Ghi chú rõ thứ tự các ảnh nếu tải nhiều ảnh nhân vật):", height=80)

st.markdown("### 👥 Quản Lý Nguồn Ảnh & Tuyển Diễn Viên (Casting)")
col_p_img, col_c_img = st.columns([1, 1])

with col_p_img:
    st.markdown("**1. 📦 Tải ảnh Sản phẩm / Bối cảnh chính**")
    uploaded_files = st.file_uploader("Chọn nhiều ảnh sản phẩm", type=["jpg", "jpeg", "png"], accept_multiple_files=True, label_visibility="collapsed")

with col_c_img:
    st.markdown("**2. 👤 Số lượng Nhân vật KOC/Gia đình tham chiếu**")
    num_chars = st.number_input("Chọn từ 0 đến 8 nhân vật:", min_value=0, max_value=8, value=0, step=1)

char_inputs = []
if num_chars > 0:
    with st.expander(f"🎭 HỒ SƠ DIỄN VIÊN ({num_chars} Nhân vật) - Kéo thả ảnh và Nhập vai trò", expanded=True):
        n_cols = 4 if num_chars > 2 else 2
        grid_cols = st.columns(n_cols)
        for i in range(num_chars):
            with grid_cols[i % n_cols]:
                with st.container(border=True):
                    st.markdown(f"<div style='color:#d90429; font-weight:800; font-size:14px; margin-bottom:5px;'>👤 Diễn viên {i+1}</div>", unsafe_allow_html=True)
                    c_role = st.text_input("Vai trò", key=f"c_role_{i}", placeholder="Vd: Mẹ 30 tuổi...", label_visibility="collapsed")
                    c_file = st.file_uploader("Ảnh", type=["jpg", "jpeg", "png"], key=f"c_img_{i}", label_visibility="collapsed")
                    if c_file and c_role.strip():
                        char_inputs.append({"id": i+1, "role": c_role.strip(), "file": c_file})

# Xử lý Logic Phân tích chính
if st.button("🚀 Bắt Đầu Phân Tích Chi Tiết & Lên Kịch Bản", type="primary", use_container_width=True, disabled=not (input_text.strip() or uploaded_files or char_inputs)):
    st.toast("⏳ Đang kết nối phân tích DNA... Vui lòng đợi trong giây lát!", icon="🤖")
    with st.spinner("⏳ Đang phân tích DNA chuyên sâu và Gán vai diễn viên..."):
        try:
            profiles_to_save = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
            st.session_state.character_profiles = profiles_to_save
            
            st.session_state.current_input_context = input_text.strip() if input_text else "Phân tích trực tiếp từ hình ảnh đính kèm sản phẩm/dự án."
            char_rules_str = generate_char_rules_string(profiles_to_save, is_sales)
            realtime_ctx = get_realtime_context()
            
            # XỬ LÝ ĐỊNH TUYẾN TÔNG ĐIỆU VÀ CẤU TRÚC KỊCH BẢN TRONG BƯỚC PHÂN TÍCH
            if is_sales:
                tone_suggestion = "Năng lượng cao, chốt sale"
                specific_rules = """
                1. Về Giá cả: TUYỆT ĐỐI KHÔNG ĐƯA MỨC GIÁ CỤ THỂ BẰNG CON SỐ. Chỉ sử dụng: "giá tận xưởng", "deal sốc giới hạn".
                2. BẮT BUỘC TẠO 5 KỊCH BẢN ĐẦU TIÊN: Xoay quanh: Xả kho, Giảm giá, Deal sốc, Siêu sale.
                3. BỐI CẢNH BẮT BUỘC: Kho hàng, Xưởng sản xuất, hoặc Showroom trưng bày. Không làm bối cảnh lifestyle.
                4. TỰ ĐỘNG NHẬN DIỆN GIỚI TÍNH: Dựa vào ảnh KOC, điền CHÍNH XÁC 'Nam' hoặc 'Nữ' vào mục 'gender'.
                5. ƯỚC LƯỢNG KÍCH THƯỚC: Phân tích kích thước thật của sản phẩm từ ảnh để AI không phóng to (vd: nhỏ gọn trong tay).
                6. CẤM TỪ LIVESTREAM: TUYỆT ĐỐI KHÔNG sử dụng các từ "livestream", "phiên live". Đây là video ngắn quay sẵn. Thay bằng "trong video này", "hôm nay".
                """
            elif is_knowledge:
                tone_suggestion = "Nhanh, dứt khoát, lôi cuốn, chuyên nghiệp"
                specific_rules = """
                1. VÀO THẲNG VẤN ĐỀ: Lược bỏ hoàn toàn các phần dạo đầu, chào hỏi dài dòng. Bắt đầu ngay bằng 1 hook đánh thẳng vào kiến thức hoặc review chuyên sâu cần chia sẻ.
                2. TỰ ĐỘNG NHẬN DIỆN GIỚI TÍNH: Dựa vào ảnh KOC, điền CHÍNH XÁC 'Nam' hoặc 'Nữ' vào mục 'gender'.
                3. ƯỚC LƯỢNG KÍCH THƯỚC: Phân tích kích thước thật của sản phẩm/vật thể.
                """
            elif is_story:
                tone_suggestion = "Truyền cảm, nhấn nhá theo mạch cảm xúc"
                specific_rules = """
                1. KỂ CHUYỆN: Xây dựng cao trào, thắt mở nút rõ ràng để giữ chân người xem.
                2. TỰ ĐỘNG NHẬN DIỆN GIỚI TÍNH: Dựa vào ảnh KOC, điền CHÍNH XÁC 'Nam' hoặc 'Nữ' vào mục 'gender'.
                3. ƯỚC LƯỢNG KÍCH THƯỚC: Phân tích kích thước thật của sản phẩm/vật thể.
                """
            elif is_corporate:
                tone_suggestion = "Đĩnh đạc, chuyên nghiệp, đáng tin cậy"
                specific_rules = """
                1. THÔNG ĐIỆP TỔ CHỨC: Thể hiện sự chuyên nghiệp, uy tín. Không thúc ép mua hàng.
                2. TỰ ĐỘNG NHẬN DIỆN GIỚI TÍNH: Dựa vào ảnh KOC, điền CHÍNH XÁC 'Nam' hoặc 'Nữ' vào mục 'gender'.
                3. ƯỚC LƯỢNG KÍCH THƯỚC: Phân tích kích thước thật của sản phẩm/dự án.
                """
            else:
                tone_suggestion = "Tự nhiên, lôi cuốn, tương tác cao"
                specific_rules = """
                1. NỘI DUNG VIRAL: Hook cực mạnh ở 3 giây đầu, bắt trend, tự nhiên và gần gũi.
                2. TỰ ĐỘNG NHẬN DIỆN GIỚI TÍNH: Dựa vào ảnh KOC, điền CHÍNH XÁC 'Nam' hoặc 'Nữ' vào mục 'gender'.
                3. ƯỚC LƯỢNG KÍCH THƯỚC: Phân tích kích thước thật của sản phẩm/vật thể.
                """

            script_outlines_json = f"""
              "script_outlines": [
                {{
                  "id": 1,
                  "title": "Tên kịch bản 1",
                  "setting_style": "Mô tả bối cảnh",
                  "script_outfit_setup": "Mô tả 1 bộ đồ cho nhân vật PHÙ HỢP THỰC TẾ với bối cảnh",
                  "angle": "Góc tiếp cận",
                  "target_hook": "Câu mở đầu mạnh mẽ, thu hút (cấm nhắc livestream nếu là video bán hàng)",
                  "recommended_scenes_count": "Tự động phân bổ linh hoạt",
                  "voice_profile": {{"gender": "[Chỉ điền 'Nam' hoặc 'Nữ']", "age_range": "25-35", "tone": "{tone_suggestion}"}}
                }},
                {{
                  "id": 2,
                  "title": "Tên kịch bản 2",
                  "setting_style": "Mô tả bối cảnh",
                  "script_outfit_setup": "Mô tả 1 bộ đồ cho nhân vật PHÙ HỢP THỰC TẾ",
                  "angle": "Góc tiếp cận",
                  "target_hook": "Câu mở đầu",
                  "recommended_scenes_count": "Tự động phân bổ linh hoạt",
                  "voice_profile": {{"gender": "[Chỉ điền 'Nam' hoặc 'Nữ']", "age_range": "25-35", "tone": "{tone_suggestion}"}}
                }},
                {{
                  "id": 3,
                  "title": "Tên kịch bản 3",
                  "setting_style": "Mô tả bối cảnh",
                  "script_outfit_setup": "Mô tả 1 bộ đồ cho nhân vật PHÙ HỢP THỰC TẾ",
                  "angle": "Góc tiếp cận",
                  "target_hook": "Câu mở đầu",
                  "recommended_scenes_count": "Tự động phân bổ linh hoạt",
                  "voice_profile": {{"gender": "[Chỉ điền 'Nam' hoặc 'Nữ']", "age_range": "25-35", "tone": "{tone_suggestion}"}}
                }},
                {{
                  "id": 4,
                  "title": "Tên kịch bản 4",
                  "setting_style": "Mô tả bối cảnh",
                  "script_outfit_setup": "Mô tả 1 bộ đồ cho nhân vật PHÙ HỢP THỰC TẾ",
                  "angle": "Góc tiếp cận",
                  "target_hook": "Câu mở đầu",
                  "recommended_scenes_count": "Tự động phân bổ linh hoạt",
                  "voice_profile": {{"gender": "[Chỉ điền 'Nam' hoặc 'Nữ']", "age_range": "25-35", "tone": "{tone_suggestion}"}}
                }},
                {{
                  "id": 5,
                  "title": "Tên kịch bản 5",
                  "setting_style": "Mô tả bối cảnh",
                  "script_outfit_setup": "Mô tả 1 bộ đồ cho nhân vật PHÙ HỢP THỰC TẾ",
                  "angle": "Góc tiếp cận",
                  "target_hook": "Câu mở đầu",
                  "recommended_scenes_count": "Tự động phân bổ linh hoạt",
                  "voice_profile": {{"gender": "[Chỉ điền 'Nam' hoặc 'Nữ']", "age_range": "25-35", "tone": "{tone_suggestion}"}}
                }}
              ]
            """
            
            prompt_text = f"""
            Phân tích siêu chuyên sâu chủ đề cho thể loại '{selected_mode}' theo phong cách '{selected_style}'. 
            Thông tin mô tả: "{st.session_state.current_input_context}"
            {realtime_ctx}

            QUY ĐỊNH ĐỘNG VỀ NHẬN DIỆN (RẤT QUAN TRỌNG):
            {specific_rules}

            BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON CHUẨN GỒM CÁC KEY SAU:
            {{
              "content_analysis": {{
                "mechanical_and_accessories": "Mô tả vật thể, thiết kế, quy mô, ƯỚC LƯỢNG KÍCH THƯỚC THỰC TẾ (tương quan với người/cảnh để tránh AI phóng to sai lệch, VD: to bằng lòng bàn tay, nhỏ bằng ngón tay...). (Không gọi tên màu sắc cụ thể).",
                "customer_pain_points": "Phân tích 3 tầng nỗi đau hoặc thách thức thực trạng.",
                "core_desires": "Mong muốn cốt lõi / Sứ mệnh.",
                "emotional_or_usp_hook": "Slogan, USP độc quyền.",
                "visual_physics_rules": "Quy chuẩn vật lý khi chuyển động, ánh sáng.",
                "prompt_dna_lock": "Chuỗi khóa thị giác đồng bộ toàn bộ video. Bắt buộc có lệnh màu sắc 'using the exact same colors and textures as the reference image, maintaining realistic scale and true-to-life proportions'."
              }},
              {script_outlines_json}
            }}
            """
            
            payload = []
            if uploaded_files:
                payload.append("ẢNH SẢN PHẨM / VẬT THỂ THAM CHIẾU:")
                for f in uploaded_files:
                    payload.append(types.Part.from_bytes(data=f.getvalue(), mime_type=f.type if f.type else "image/jpeg"))
            
            if char_inputs:
                for c in char_inputs:
                    payload.append(f"ẢNH NHÂN VẬT THAM CHIẾU {c['id']} - VAI TRÒ: {c['role']}:")
                    payload.append(types.Part.from_bytes(data=c['file'].getvalue(), mime_type=c['file'].type if c['file'].type else "image/jpeg"))
            
            payload.append(prompt_text)
            
            sys_inst = get_system_instructions(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, char_rules_str)
            res = call_gemini_api(payload, sys_inst)
            
            st.session_state.content_analysis = res.get("content_analysis")
            st.session_state.all_scripts = res.get("script_outlines", [])
            st.session_state.cloned_scripts, st.session_state.expanded_scripts, st.session_state.generated_details, st.session_state.active_script_id = [], [], {}, None
            st.session_state.scroll_to_top = True
            st.success("✅ Đã phân tích DNA và khởi tạo dự án thành công!")
            time.sleep(0.3)
            st.rerun()
        except Exception as e:
            st.error(f"❌ Lỗi thực thi: {e}")

if st.session_state.content_analysis and isinstance(st.session_state.content_analysis, dict) and not st.session_state.action_trigger:
    st.divider()
    st.markdown(f"### 🔍 **Phân Tích DNA Chi Tiết Đa Tầng — [{selected_mode.upper()}]**")
    ca = st.session_state.content_analysis
    with st.container(border=True):
        st.markdown("##### 🏭 **1. Thông số Cốt lõi / Đối tượng chính (Đã định chuẩn Kích thước):**")
        st.markdown(f"<div style='line-height: 1.8;'>{format_analysis_field(ca.get('mechanical_and_accessories', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 🎯 **2. Ma trận Nỗi đau / Thách thức thực trạng:**")
        st.markdown(f"<div style='line-height: 1.8;'>{format_analysis_field(ca.get('customer_pain_points', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 💡 **3. Mong muốn cốt lõi / Sứ mệnh & USP:**")
        st.markdown(f"<div style='line-height: 1.8;'>• <b>Mong muốn/Giá trị:</b> {format_analysis_field(ca.get('core_desires', 'N/A'))}<br>• <b>USP / Slogan:</b> {format_analysis_field(ca.get('emotional_or_usp_hook', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### ⚙️ **4. Quy chuẩn bối cảnh / Vật lý điện ảnh:**")
        st.markdown(f"<div style='line-height: 1.8;'>{format_analysis_field(ca.get('visual_physics_rules', 'N/A'))}</div>", unsafe_allow_html=True)
    st.markdown("##### 📌 **Chuỗi khóa thị giác (Visual DNA Lock):**")
    raw_dna = str(ca.get('prompt_dna_lock', 'N/A')).replace('<br>', ' ').replace('<b>', '').replace('</b>', '')
    st.code(raw_dna, language="text")

# ==============================================================================
# GIAI ĐOẠN 1: CHIA 2 VÙNG ĐỘC LẬP CHO DANH SÁCH KỊCH BẢN
# ==============================================================================
all_combined_scripts_list = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts

if all_combined_scripts_list and st.session_state.active_script_id is None and not st.session_state.action_trigger:
    st.divider()
    
    completed_scripts = [sc for sc in all_combined_scripts_list if sc.get("id") in st.session_state.generated_details]
    pending_scripts = [sc for sc in all_combined_scripts_list if sc.get("id") not in st.session_state.generated_details]

    st.markdown("### 🎬 **1. Kịch Bản Đã Hoàn Thiện Chi Tiết (Sẵn Sàng Sản Xuất & Nhân Bản)**")
    if not completed_scripts:
        st.info("💡 Chưa có kịch bản nào được tạo chi tiết. Hãy chọn một kịch bản ở bên dưới để bắt đầu dựng cảnh!")
    else:
        for outline in completed_scripts:
            sc_id = outline.get("id")
            with st.container(border=True):
                col_i1, col_btn1, col_btn2 = st.columns([2.5, 1, 1])
                with col_i1:
                    st.markdown(f"**#{sc_id}. {outline.get('title')}** — <span class='badge-ready'>ĐÃ HOÀN THIỆN</span>", unsafe_allow_html=True)
                    st.caption(f"🏛️ Bối cảnh: {outline.get('setting_style')} | ⚡ Hook: *\"{outline.get('target_hook')}\"*")
                with col_btn1:
                    if st.button("👁️ Xem lại chi tiết", key=f"btn_rev_v1_main_{sc_id}", use_container_width=True):
                        st.session_state.active_script_id = sc_id
                        st.session_state.scroll_to_top = True
                        st.rerun()
                with col_btn2:
                    if st.button("🚀 Nhân bản 5 biến thể", key=f"btn_clone_v1_main_{sc_id}", type="primary", use_container_width=True):
                        st.session_state.action_trigger = "clone_script"
                        st.session_state.action_param = sc_id
                        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### ⏳ **2. Kịch Bản Đang Chờ Tạo Chi Tiết (Ý Tưởng Thực Chiến)**")
    if not pending_scripts:
        st.success("🎉 Tuyệt vời! Tất cả các kịch bản trong danh sách đã được tạo chi tiết thành công.")
    else:
        for outline in pending_scripts:
            sc_id = outline.get("id")
            with st.container(border=True):
                col_i2, col_a2 = st.columns([3, 1.2])
                with col_i2:
                    st.markdown(f"**#{sc_id}. {outline.get('title')}** — <span class='badge-pending'>ĐANG CHỜ</span>", unsafe_allow_html=True)
                    st.caption(f"🏛️ Bối cảnh: {outline.get('setting_style')} | ⚡ Hook: *\"{outline.get('target_hook')}\"*")
                with col_a2:
                    if st.button("✨ Tạo chi tiết ngay", key=f"btn_cre_v2_main_{sc_id}", use_container_width=True):
                        st.session_state.action_trigger = "create_detail"
                        st.session_state.action_param = sc_id
                        st.rerun()

    st.markdown("---")
    if st.button("➕ Gọi Thêm 5 Kịch Bản Khác", key="btn_add_more_1_main", type="primary", use_container_width=True):
        st.session_state.action_trigger = "generate_more"
        st.rerun()

# GIAI ĐOẠN 2: CHI TIẾT KỊCH BẢN & BỐ CỤC ĐIỀU HƯỚNG
if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details and not st.session_state.action_trigger:
    st.divider()

    if st.button("⬅️ Quay lại danh sách kịch bản tổng", key="btn_back_to_list_main"):
        st.session_state.active_script_id = None
        st.session_state.scroll_to_top = True
        st.rerun()

    raw_active_data = st.session_state.generated_details[st.session_state.active_script_id]
    
    if isinstance(raw_active_data, list):
        active_script = raw_active_data[0] if len(raw_active_data) > 0 else {}
    elif isinstance(raw_active_data, dict):
        active_script = raw_active_data
    else:
        active_script = {}

    raw_vp = active_script.get("voice_profile", {}) if isinstance(active_script, dict) else {}
    if isinstance(raw_vp, str):
        vp = {"gender": "Nữ", "tone": raw_vp}
    elif isinstance(raw_vp, dict):
        vp = raw_vp
    else:
        vp = {"gender": "Nữ", "age_range": "25-30", "tone": "Năng lượng cao"}

    script_title = active_script.get('title', 'Kịch bản chi tiết') if isinstance(active_script, dict) else 'Kịch bản chi tiết'
    total_dur = active_script.get('total_estimated_duration', '24s') if isinstance(active_script, dict) else '24s'
    outfit_setup_text = active_script.get('script_outfit_setup', 'Đồng phục bối cảnh')

    st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(script_title).upper()}**")
    st.info(f"⏱️ Thời lượng: **{total_dur}** | 🎙️ Giọng: **{vp.get('gender', 'Nữ')} ({vp.get('tone', 'Truyền cảm')})** | 👔 Trang phục: **{outfit_setup_text}** | 📐 Khung hình: **{selected_aspect}**")

    scenes_list = active_script.get("scenes", []) if isinstance(active_script, dict) else []
    if isinstance(scenes_list, dict): scenes_list = [scenes_list]
    
    for idx, scene in enumerate(scenes_list, start=1):
        if not isinstance(scene, dict): continue
        dur = scene.get("duration", "6s")
        st.markdown(f"#### **📍 Phân cảnh {idx} ({dur}) — [ {scene.get('transition_type', 'Cắt cứng dồn dập')} ]**")
        st.markdown(f"🏛️ **Bối cảnh & Miêu tả:** *{scene.get('scene_setting')}*")
        st.markdown(f"**🎙️ Đạo diễn ngữ điệu:** *{scene.get('voice_director_vn')}*")
        st.markdown(f"**💬 Lời thuyết minh (Voiceover):** `\"{scene.get('voiceover_vi')}\"`")
        
        img_p = scene.get('image_prompt', '')
        if img_p:
            st.markdown(f"**🖼️ Prompt Ảnh (Imagen 3 - {selected_aspect}):**")
            st.code(img_p, language="text")
            safe_copy_button(img_p, f"📋 Sao Chép Prompt Ảnh Cảnh {idx}")
            
        vid_p = scene.get('video_prompt', '')
        st.markdown(f"**🎥 Prompt Video (Veo 3 - Thuyết minh):**")
        st.code(vid_p, language="text")
        safe_copy_button(vid_p, f"📋 Sao Chép Prompt Video Cảnh {idx}")
        st.markdown("---")

    col_left, col_right = st.columns([1.1, 0.9])
    
    with col_left:
        st.markdown("""
        <div class="custom-card" style="background: #f0fdf4; border-color: #86efac;">
            <div style="color: #166534; font-weight: 800; font-size: 1.1rem; margin-bottom: 4px;">🎬 Kịch Bản Đã Hoàn Thiện</div>
            <div style="font-size: 0.82rem; color: #15803d;">Chọn để xem lại hoặc nhân bản nhanh</div>
        </div>
        """, unsafe_allow_html=True)
        
        completed_scripts_in_detail = [sc for sc in all_combined_scripts_list if sc.get("id") in st.session_state.generated_details]
        if not completed_scripts_in_detail:
            st.caption("Chưa có kịch bản nào khác được tạo.")
        else:
            for item in completed_scripts_in_detail:
                it_id = item.get("id")
                is_current = (it_id == st.session_state.active_script_id)
                with st.container(border=True):
                    badge_curr = ' <span class="badge-ready">ĐANG XEM</span>' if is_current else ''
                    st.markdown(f"<b>#{it_id}. {item.get('title')}</b>{badge_curr}", unsafe_allow_html=True)
                    
                    c_rev, c_clone = st.columns(2)
                    with c_rev:
                        if not is_current:
                            if st.button("👁️ Xem lại", key=f"dt_rev_detail_{it_id}", use_container_width=True):
                                st.session_state.active_script_id = it_id
                                st.session_state.scroll_to_top = True
                                st.rerun()
                        else:
                            st.markdown("<div style='text-align: center; color: #15803d; font-size: 12px; font-weight: 700; padding: 6px;'>Đang hiển thị</div>", unsafe_allow_html=True)
                    with c_clone:
                        if st.button("🚀 Nhân bản", key=f"dt_clone_detail_{it_id}", type="primary", use_container_width=True):
                            st.session_state.action_trigger = "clone_script"
                            st.session_state.action_param = it_id
                            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("""
        <div class="custom-card">
            <div class="card-title-add">➕ Vùng Gọi Thêm Kịch Bản Mới</div>
            <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 8px;">Mở rộng thêm ý tưởng từ dữ liệu DNA đã phân tích.</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("➕ Gọi Thêm 5 Tình Huống Kịch Bản Mới", key="btn_add_more_phase2_detail", use_container_width=True):
            st.session_state.action_trigger = "generate_more"
            st.rerun()

    with col_right:
        st.markdown("""
        <div class="custom-card" style="background: #f8fafc;">
            <div style="color: #0f172a; font-weight: 800; font-size: 1.1rem; margin-bottom: 10px;">📋 Kịch Bản Chưa Tạo Chi Tiết</div>
        </div>
        """, unsafe_allow_html=True)

        pending_scripts = [item for item in all_combined_scripts_list if item.get("id") not in st.session_state.generated_details]

        if not pending_scripts:
            st.success("🎉 Tuyệt vời! Tất cả các kịch bản trong danh sách đã được tạo chi tiết thành công.")
        else:
            for item in pending_scripts:
                it_id = item.get("id")
                with st.container(border=True):
                    st.markdown(f"**#{it_id}. {item.get('title')}** — <span class='badge-pending'>CHƯA TẠO</span>", unsafe_allow_html=True)
                    st.caption(f"🏛️ {item.get('setting_style')}")
                    
                    if st.button("✨ Tạo chi tiết ngay", key=f"nav_sc_detail_{it_id}", use_container_width=True):
                        st.session_state.action_trigger = "create_detail"
                        st.session_state.action_param = it_id
                        st.rerun()
