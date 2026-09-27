import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
import json
import base64
import os
import re
import time
import ast
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
        pass

# ==============================================================================
# KHỞI TẠO SESSION STATE & GLOBAL TOAST
# ==============================================================================
for key, default_val in [
    ("content_analysis", None), ("all_scripts", []), ("cloned_scripts", []), 
    ("expanded_scripts", []), ("generated_details", {}), ("active_script_id", None), 
    ("projects_library", {}), ("licensed_accounts", load_licensed_accounts()), 
    ("current_input_context", ""), ("is_logged_in", False),
    ("current_user_email", ""), ("active_project_title", "Chiến dịch mới"),
    ("last_loaded_file_id", None), ("file_uploader_key", 0), ("scroll_to_top", False),
    ("action_trigger", None), ("action_param", None), ("character_profiles", []),
    ("main_input_context", ""), ("num_chars_input", 0),
    ("global_toast", ""), ("global_toast_icon", "✅")
]:
    if key not in st.session_state:
        st.session_state[key] = default_val

if st.session_state.global_toast:
    st.toast(st.session_state.global_toast, icon=st.session_state.global_toast_icon)
    st.session_state.global_toast = ""
    st.session_state.global_toast_icon = "✅"

if st.session_state.scroll_to_top:
    components.html("""
        <script>
            function forceScroll() {
                var pDoc = window.parent.document;
                pDoc.body.scrollTop = 0;
                pDoc.documentElement.scrollTop = 0;
                window.parent.scrollTo({top: 0, behavior: 'smooth'});
                pDoc.querySelectorAll('.main, .block-container, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"]').forEach(function(el) {
                    el.scrollTop = 0;
                    el.scrollTo({top: 0, behavior: 'smooth'});
                });
            }
            forceScroll();
            setTimeout(forceScroll, 100);
            setTimeout(forceScroll, 300);
            setTimeout(forceScroll, 600);
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
        st.session_state.global_toast = "Đăng nhập thành công!"
        st.session_state.global_toast_icon = "🔑"
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
            st.session_state.main_input_context = "" 
            st.session_state.num_chars_input = 0 
            
            st.session_state.global_toast = "Đã dọn dẹp và tạo dự án mới!"
            st.session_state.global_toast_icon = "✨"
            time.sleep(0.1)
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
                    "character_profiles": st.session_state.character_profiles,
                    "current_input_context": st.session_state.get("main_input_context", "")
                }
                st.toast("✅ Đã lưu dự án vào bộ nhớ!", icon="💾")

        with col_p2:
            export_data = {
                "title": project_title_input, "mode": st.session_state.get("selected_mode"),
                "style": st.session_state.get("selected_style"), "content_analysis": st.session_state.content_analysis,
                "all_scripts": st.session_state.all_scripts, "cloned_scripts": st.session_state.cloned_scripts,
                "expanded_scripts": st.session_state.expanded_scripts, "generated_details": st.session_state.generated_details,
                "character_profiles": st.session_state.character_profiles,
                "current_input_context": st.session_state.get("main_input_context", "")
            }
            json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 Tải JSON", 
                data=json_str, 
                file_name=f"{project_title_input.replace(' ', '_')}.json", 
                mime="application/json", 
                use_container_width=True,
                on_click=lambda: st.toast("✅ Đang tải file JSON xuống máy!", icon="📥")
            )

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
                st.session_state.main_input_context = p_data.get("current_input_context", "")
                st.session_state.active_script_id = None
                st.session_state.last_loaded_file_id = None
                st.session_state.file_uploader_key += 1
                st.session_state.scroll_to_top = True
                
                st.session_state.global_toast = "Đã mở dự án thành công!"
                st.session_state.global_toast_icon = "📂"
                time.sleep(0.1)
                st.rerun()

        st.markdown("<div style='font-size: 0.85rem; color: #64748b; margin-top: 8px;'>Hoặc tải file dự án từ máy tính:</div>", unsafe_allow_html=True)
        uploaded_project_file = st.file_uploader("📤 Tải file kịch bản (.json)", type=["json"], label_visibility="collapsed", key=f"project_uploader_{st.session_state.file_uploader_key}")
        
        if uploaded_project_file is not None:
            file_identifier = f"{uploaded_project_file.name}_{uploaded_project_file.size}"
            if st.session_state.get("last_loaded_file_id") != file_identifier:
                st.toast("⏳ Đang đọc dữ liệu file...", icon="📂")
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
                    st.session_state.main_input_context = proj_data.get("current_input_context", "")
                    
                    st.session_state.active_script_id = None
                    st.session_state.last_loaded_file_id = file_identifier
                    st.session_state.scroll_to_top = True
                    
                    st.session_state.global_toast = "Đã khôi phục thành công dự án từ file!"
                    st.session_state.global_toast_icon = "🎉"
                    time.sleep(0.1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi đọc file JSON: {e}")

        if st.session_state.current_user_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙️ **Quản Lý Tài Khoản (Quản Trị)**")
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
                        st.session_state.global_toast = f"Đã cấp quyền thành công cho: {new_account_id.strip()}!"
                        st.session_state.global_toast_icon = "✅"
                        st.rerun()

            if st.session_state.licensed_accounts:
                with st.expander(f"📋 Danh sách tài khoản đã cấp ({len(st.session_state.licensed_accounts)})"):
                    for acc, info in list(st.session_state.licensed_accounts.items()):
                        st.markdown(f"**👤 {acc}**")
                        st.caption(f"• Quyền: {', '.join(info.get('roles', []))}<br>• Hết hạn: {info.get('expires_at')}", unsafe_allow_html=True)
                        if acc != ADMIN_EMAIL and st.button(f"🗑️ Xóa {acc}", key=f"del_acc_{acc}"):
                            del st.session_state.licensed_accounts[acc]
                            save_licensed_accounts(st.session_state.licensed_accounts)
                            st.session_state.global_toast = f"Đã xóa tài khoản {acc}!"
                            st.session_state.global_toast_icon = "🗑️"
                            st.rerun()
                        st.markdown("---")

    st.markdown("---")
    st.markdown("""
    <div class="support-box">
        <b style="color: #166534; font-size: 0.95rem;">💬 Cần Hỗ Trợ / Mua Gói?</b><br>
        <p style="font-size: 0.85rem; color: #15803d; margin: 6px 0 8px 0;">Kết nối ngay với chúng tôi:</p>
        <div style="display: flex; justify-content: center; gap: 5px; flex-wrap: wrap;">
            <a href="https://zalo.me/0968484369" target="_blank" style="background: #0068ff; color: white; padding: 5px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 11px;">📱 Zalo</a>
            <a href="https://facebook.com/binhnguyenmedia.vn" target="_blank" style="background: #0866ff; color: white; padding: 5px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 11px;">📘 Facebook</a>
            <a href="https://tiktok.com/@binhnguyenmedia" target="_blank" style="background: #000000; color: white; padding: 5px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 11px;">🎵 TikTok</a>
        </div>
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
            st.session_state.global_toast = "Đã đăng xuất hệ thống!"
            st.session_state.global_toast_icon = "🚪"
            st.rerun()

def safe_copy_button(text_to_copy: str, button_label: str = "📋 Sao Chép Prompt"):
    b64 = base64.b64encode(text_to_copy.encode('utf-8')).decode('utf-8')
    components.html(f"""
    <button onclick='navigator.clipboard.writeText(decodeURIComponent(escape(atob("{b64}"))));this.innerText="✅ Đã sao chép!";setTimeout(()=>this.innerText="{button_label}",2000);' style="background:linear-gradient(135deg, #ff4b4b, #ff7300);color:white;border:none;padding:8px 16px;font-size:13px;font-weight:700;border-radius:6px;cursor:pointer;width:100%;">{button_label}</button>
    """, height=40)

def clean_and_parse_json(text_content: str):
    cleaned = re.sub(r'```(?:json)?', '', text_content).strip()
    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    try:
        parsed = json.loads(cleaned, strict=False)
        return parsed[0] if isinstance(parsed, list) and len(parsed) > 0 else parsed
    except json.JSONDecodeError:
        try:
            py_str = cleaned.replace('true', 'True').replace('false', 'False').replace('null', 'None')
            parsed = ast.literal_eval(py_str)
            return parsed[0] if isinstance(parsed, list) and len(parsed) > 0 else parsed
        except Exception as fallback_e:
            raise Exception("AI vô tình sinh ra định dạng bị lỗi cấu trúc. Vui lòng bấm 'Tạo chi tiết ngay' thêm lần nữa.")

def get_realtime_context():
    now = datetime.now()
    month = now.month
    year = now.year
    if month in [2, 3, 4]: season = "Mùa Xuân"
    elif month in [5, 6, 7]: season = "Mùa Hè"
    elif month in [8, 9, 10]: season = "Mùa Thu (Mùa tựu trường / Back-to-school)"
    else: season = "Mùa Đông (Mùa lễ hội cuối năm / Winter holidays)"
    return f"THỜI GIAN THỰC TẾ: Tháng {month}/{year} ({season}). TƯ DUY ÁP DỤNG MÙA VỤ: Phân tích khách hàng theo mùa vụ nếu phù hợp."

def get_strategy_rules(mode: str, strategy: str, target_audience: str) -> str:
    rules = f"- ĐỐI TƯỢNG MỤC TIÊU CỐT LÕI: Phải nhắm thẳng vào tệp khách hàng: {target_audience}.\n"
    if "Bán Hàng" in mode or "Mẹ & Bé" in mode:
        if "Hỗn hợp" in strategy:
            rules += "- BẮT BUỘC ĐA DẠNG HÓA 5 KỊCH BẢN: 2 kịch bản Bán hàng trực diện (Review/Xưởng) + 3 kịch bản Shoppertainment (Drama đời sống/gia đình bẻ lái chốt sale).\n"
        elif "Drama" in strategy:
            rules += "- CHIẾN LƯỢC 100% DRAMA / TÌNH HUỐNG: Setup các tình huống gia đình, mâu thuẫn, kịch tính hoặc hài hước. Bẻ lái (twist) lồng ghép sản phẩm vào cuối.\n"
        else:
            rules += "- CHIẾN LƯỢC 100% TRỰC DIỆN: Tập trung không gian xưởng, kho, showroom. Xả kho, đập hộp, test sản phẩm khốc liệt.\n"
        rules += "- TỐI ƯU SỐ LƯỢNG CẢNH: Yêu cầu ghi rõ '3 đến 4 phân cảnh' vào recommended_scenes_count để tiết kiệm Credit.\n- TUYỆT ĐỐI CẤM SỬ DỤNG TỪ 'LIVESTREAM', 'PHIÊN LIVE'.\n"
    elif "Lịch Sử" in mode:
        if "Dã sử" in strategy:
            rules += "- CHIẾN LƯỢC DÃ SỬ HÀNH ĐỘNG: Phim hoạt hình. Tập trung vào mâu thuẫn, tranh cãi chiến thuật, hoặc trận chiến. SỬ DỤNG KỸ THUẬT ĐẠO DIỄN: Cắt cảnh luân phiên cận mặt (Shot/Reverse Shot) hoặc Góc chéo vai (Over-the-shoulder). TUYỆT ĐỐI CẤM để 2 nhân vật đánh nhau trực diện trong cùng 1 góc máy rộng. Cảnh quân đội dùng Bóng đen (Silhouettes).\n"
        else:
            rules += "- CHIẾN LƯỢC TÀI LIỆU: Không khí trang nghiêm, hào hùng. Góc máy chậm, Cinematic flycam.\n"
    else:
        rules += f"- CHIẾN LƯỢC: {strategy}. Tạo kịch bản chuyên nghiệp, cuốn hút.\n"
    return rules

def get_system_instructions(mode: str, style: str, aspect_ratio: str, goal: str, target_duration_mins: float, char_rules: str, strategy: str = "", audience: str = "") -> str:
    format_instruction = "9:16 vertical video format, mobile-first framing" if aspect_ratio == "9:16" else "16:9 widescreen cinematic format, professional movie framing"
    
    if target_duration_mins <= 0.5:
        duration_rule = "QUY CHUẨN THỜI LƯỢNG (TỐI ƯU CREDIT): BẮT BUỘC CHỈ ĐƯỢC TẠO TỪ 3 ĐẾN 4 PHÂN CẢNH. Mỗi cảnh chọn mốc 4s, 6s hoặc 8s. (Ví dụ: Hook 8s + Demo 6s + Chốt Sale 8s)."
    else:
        total_seconds = int(target_duration_mins * 60)
        duration_rule = f"QUY CHUẨN THỜI LƯỢNG: Phải chia TỔNG {total_seconds} GIÂY thành nhiều phân cảnh (4s, 6s, 8s)."

    strategy_instructions = get_strategy_rules(mode, strategy, audience)

    voiceover_instruction = f"""
    7. QUY CHUẨN THUYẾT MINH, ĐỒNG BỘ & ÂM THANH NỀN:
       - CẤM DÙNG GIỌNG THUYẾT MINH PHIM TÀI LIỆU ĐỀU ĐỀU (NO NARRATOR VOICE): Giọng nói phải là của NHÂN VẬT (Diễn viên).
       - ÂM THANH NỀN (AMBIENT/FOLEY SOUND): Nếu cảnh quay có hành động thực tế (nấu ăn, gió thổi, gươm giáo va chạm), BẮT BUỘC thêm mô tả âm thanh nền vào video_prompt bằng tiếng Anh (VD: "Background ambient sound: sizzling meat / clashing steel, volume strictly lower than voiceover").
       - PHIÊN ÂM TIẾNG VIỆT CHUẨN KHI ĐỌC: 'Bluetooth' -> 'Bờ lu tút', 'inox 304' -> 'i nốc ba linh tư'. 
       - TUYỆT ĐỐI KHÔNG ĐƯA GIÁ TIỀN BẰNG CON SỐ (như 199k, 50k) VÀO LỜI THOẠI. Chỉ dùng "giá tận xưởng", "deal hời".
    8. BỘ LỌC CHÍNH SÁCH ĐA NỀN TẢNG (COMPLIANCE):
       - TUYỆT ĐỐI KHÔNG DÙNG: "100%", "tuyệt đối", "cam kết", "chắc chắn", "vĩnh viễn", "trị dứt điểm".
       - CẤM TUYÊN BỐ Y TẾ, ĐIỀU TRỊ SAI LỆCH VÀ GIEO RẮC SỢ HÃI: Không dùng "độc hại", "ung thư", "chống cận thị tuyệt đối". THAY BẰNG: "hỗ trợ bảo vệ", "kém an toàn".
       - CẤM TỪ KHÓA ĐIỀU HƯỚNG: "livestream", "phiên live", "inbox riêng", "zalo".
    """

    base = f"""
BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL ĐA NĂNG CHO IMAGEN 3 VÀ VEO 3.
PHONG CÁCH KẾT XUẤT THỊ GIÁC: {style.upper()}
ĐỊNH DẠNG KHUNG HÌNH: {format_instruction}
MỤC TIÊU CHIẾN DỊCH: {goal}
{duration_rule}

🛑 QUY TẮC BẮT BUỘC 100% (KHÔNG ĐƯỢC VI PHẠM):
1. BẮT BUỘC TRẢ VỀ JSON HỢP LỆ. DÙNG DẤU NGOẶC ĐƠN (') ĐỂ TRÍCH DẪN BÊN TRONG CHUỖI. KHÔNG XUỐNG DÒNG (\\n) TRONG CHUỖI.
2. QUY TẮC QUỐC TỊCH: Luôn chèn "Vietnamese" cho nhân vật.
{char_rules}
4. CẤM HIỂN THỊ UI/GIỎ HÀNG (CRITICAL): Mọi `image_prompt` và `video_prompt` ép lệnh "Cinematic shot ONLY. ABSOLUTELY NO UI elements, NO shopping cart icons".
5. CHỐNG BIẾN DẠNG & KHÔNG CHE KHUẤT (NO OCCLUSION & ANTI-MORPHING): Bắt buộc chèn lệnh vào image_prompt: "product is fully visible, strictly NO hands or objects obscuring the main body/details". Trong video_prompt chèn: "product maintains rigid structural integrity, zero shape morphing, action ends with the product fully visible and unoccluded".
6. {strategy_instructions}
7. KỸ THUẬT QUAY PHIM HÀNH ĐỘNG/TRANH CÃI (Nếu có): TUYỆT ĐỐI cấm để 2 người tương tác vật lý trực diện trong cùng 1 khung hình rộng. BẮT BUỘC DÙNG Cắt cảnh luân phiên cận mặt (Shot/Reverse Shot) hoặc Góc máy qua vai (Over-the-shoulder).
8. GIỚI HẠN TỪ VỰNG THUYẾT MINH (VOICE PACING LIMIT): Lời thoại 'voiceover_vi' PHẢI NGẮN GỌN để giữ nhịp. Bắt buộc: Cảnh 4s (12-14 từ); Cảnh 6s (18-21 từ); Cảnh 8s (24-28 từ). 
{voiceover_instruction}
"""
    return base

def generate_char_rules_string(profiles, is_sales_mode=False):
    if not profiles:
        return "3. BẮT BUỘC CÓ MẶT NGƯỜI/NHÂN VẬT TRONG TẤT CẢ CÁC PHÂN CẢNH."
    rules = "3. KHÓA KHUÔN MẶT KOC VÀ ĐỒNG NHẤT TRANG PHỤC:\n"
    for p in profiles:
        safe_role = p['role'].replace('"', "'")
        rules += f"   - Nhân vật {p['id']}: Đóng vai '{safe_role}'. Lệnh bắt buộc trong prompt tiếng Anh: 'Character {p['id']} ({safe_role}) wearing [trang_phục] and featuring the exact identity of reference image {p['id']}'.\n"
    if is_sales_mode:
        rules += "   - ĐỒNG NHẤT TRANG PHỤC 100%: BỘ ĐỒ VÀ MÀU SẮC PHẢI ĐƯỢC GIỮ NGUYÊN 100% TRONG TOÀN BỘ CÁC CẢNH, AI không được tự ý đổi màu áo.\n"
    return rules

# ==============================================================================
# HỆ THỐNG XỬ LÝ LÕI AI (CORE FUNCTIONS)
# ==============================================================================
def call_gemini_with_retry(payload, sys_inst):
    for attempt in range(4):
        try:
            return call_gemini_api(payload, sys_inst)
        except Exception as e:
            if "429" in str(e): time.sleep(15)
            elif "503" in str(e): time.sleep(3 * (attempt + 1))
            else: raise e
    raise Exception("Lỗi kết nối Gemini API. Vui lòng thử lại sau.")

def create_scene_details_for_id(target_id: int, current_mode: str, current_style: str, aspect_ratio: str, goal: str, target_duration_mins: float, current_strategy: str):
    all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_sources if isinstance(sc, dict) and sc.get("id") == target_id), None)
    if not outline: raise Exception(f"Không tìm thấy kịch bản #{target_id}")
    
    product_ctx = st.session_state.get("current_input_context", "Dự án hiện tại").replace('"', "'")
    safe_title = outline.get('title', '').replace('"', "'").replace('\n', ' ')
    safe_setting = outline.get('setting_style', '').replace('"', "'").replace('\n', ' ')
    safe_hook = outline.get('target_hook', '').replace('"', "'").replace('\n', ' ')
    
    is_sales_mode = "Bán Hàng" in current_mode

    if target_duration_mins <= 0.5:
        duration_str = "16s - 32s (Tối ưu Credit Veo 3)"
        duration_rule_scene = "ĐỂ TỐI ƯU CREDIT VEO 3: Bạn BẮT BUỘC CHỈ ĐƯỢC TẠO TỪ 3 ĐẾN 4 PHÂN CẢNH. Mỗi cảnh chọn mốc 4s, 6s, 8s."
    else:
        total_sec = int(target_duration_mins * 60)
        duration_str = f"{total_sec}s ({target_duration_mins} phút)"
        duration_rule_scene = f"TỔNG ĐỘ DÀI CÁC CẢNH PHẢI ĐÚNG {total_sec} GIÂY. Chia nhỏ thành các cảnh 4s, 6s, 8s."

    # Đồng bộ Giới tính Tránh Lỗi Policy
    v_profile = outline.get("voice_profile", {})
    fixed_gender_vi = "Nữ"
    if isinstance(v_profile, str): fixed_gender_vi = "Nữ" if "nữ" in v_profile.lower() else "Nam"
    elif isinstance(v_profile, dict):
        g_val = v_profile.get("gender", "Nữ")
        fixed_gender_vi = "Nữ" if "nữ" in g_val.lower() else "Nam"
        
    gender_en = "male" if fixed_gender_vi.lower() == "nam" else "female"
    outfit_setup = outline.get("script_outfit_setup", "casual everyday outfit").replace('"', "'")
    
    char_rules_str = generate_char_rules_string(st.session_state.get("character_profiles", []), is_sales_mode)
    dna_data = st.session_state.get("content_analysis", {})
    target_audience = dna_data.get("primary_target_audience", "Người dùng")
    
    prompt_detail = f"""
    Ngữ cảnh: "{product_ctx}" | Đối tượng: {target_audience}
    Ý tưởng kịch bản: ID {target_id} - {safe_title} | Bối cảnh: {safe_setting}
    TRANG PHỤC CỐ ĐỊNH: {outfit_setup} | GIỚI TÍNH ĐÃ CHỐT: {fixed_gender_vi} (English: {gender_en})
    CHIẾN LƯỢC: {current_strategy}
    
    QUY ĐỊNH ĐẠO DIỄN (CRITICAL):
    0. KHÓA ĐỒNG BỘ GIỚI TÍNH (POLICY LOCK): Trong `image_prompt` và `video_prompt`, BẮT BUỘC sử dụng chữ '{gender_en} character'. TUYỆT ĐỐI KHÔNG dùng 'Nam character' hay tên riêng để tránh lỗi Deepfake Policy.
    1. KỶ LUẬT THỜI LƯỢNG & SỐ TỪ: Cảnh 4s (12-14 từ); Cảnh 6s (18-21 từ); Cảnh 8s (24-28 từ). {duration_rule_scene}
    2. NỐI LIỀN MẠCH (MATCH CUT): Nếu dùng Match Cut, `image_prompt` BẮT BUỘC chỉ được ghi đúng câu tiếng Việt này: "Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu cho video" (để ẩn nút Copy).
    3. THOẠI SẠCH VÀ LIỀN MẠCH (CLEAN NARRATIVE): Lời thoại `voiceover_vi` PHẢI NỐI CHẶT CHẼ (Thế nhưng, Chưa hết). LỖI TAI HẠI: TUYỆT ĐỐI KHÔNG chứa dấu ngoặc đơn (VD: (Cười), (Thở dài)) bên trong `voiceover_vi`. 
    4. DIỄN XUẤT & ÂM THANH NỀN: Biểu cảm khuôn mặt và âm thanh (Cười, thở dài) miêu tả bằng tiếng Anh trong `video_prompt` (VD: "punctuated by a soft laugh"). Hành động thực tế BẮT BUỘC có Background ambient sound (VD: "sizzling meat / clashing swords, volume strictly lower than voiceover").
    5. KHÔNG CHE KHUẤT (NO OCCLUSION): image_prompt ép lệnh: "product is fully visible, strictly NO hands obscuring the main body". video_prompt ép lệnh: "product maintains rigid structural integrity, action ends with the product fully visible and unoccluded".
    
    Xuất chuẩn 1 Dict JSON duy nhất (Mẫu cấu trúc):
    {{
      "id": {target_id}, 
      "title": "{safe_title}", 
      "setting_style": "{safe_setting}",
      "script_outfit_setup": "{outfit_setup}",
      "voice_profile": {{"gender": "{fixed_gender_vi}", "tone": "nhịp độ nhanh"}},
      "total_estimated_duration": "{duration_str}",
      "scenes": [
        {{
          "scene_number": 1, "duration": "8s", "scene_setting": "Mô tả...", "transition_type": "Mở đầu", 
          "voice_director_vn": "Ngạc nhiên, kèm SFX hít hà", 
          "voiceover_vi": "Lời thoại sạch giới hạn đúng hai mươi sáu từ không ngoặc đơn không số tiền.", 
          "image_prompt": "Prompt tiếng Anh, {gender_en} character, product fully visible strictly NO hands obscuring...", 
          "video_prompt": "Audio: The same {gender_en} character... punctuated by a sharp gasp. Background ambient sound: sizzling meat, volume strictly lower than voiceover. Visual: Cinematic shot ONLY. ABSOLUTELY NO UI elements. Reading: [voiceover_vi]."
        }},
        {{
          "scene_number": 2, "duration": "6s", "scene_setting": "Mô tả...", "transition_type": "Nối liền mạch (Match Cut)", 
          "voice_director_vn": "Nhấn mạnh", 
          "voiceover_vi": "Lời thoại sạch tiếp theo nối mạch.", 
          "image_prompt": "Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu cho video", 
          "video_prompt": "Prompt Video tiếng Anh..."
        }}
      ]
    }}
    """
    sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins, char_rules_str, current_strategy, target_audience)
    res = call_gemini_with_retry([prompt_detail], sys_inst)
    if isinstance(res, list): res = res[0]
    st.session_state.generated_details[target_id] = res

def add_five_scripts_continuation(current_mode: str, current_style: str, aspect_ratio: str, goal: str, target_duration_mins: float, current_strategy: str):
    all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    cur_len = len(all_sources)
    product_ctx = st.session_state.get("current_input_context", "Sản phẩm hiện tại").replace('"', "'")
    dna_data = st.session_state.get("content_analysis", {}) 
    target_audience = dna_data.get("primary_target_audience", "Người dùng phù hợp")
    
    char_rules_str = generate_char_rules_string(st.session_state.get("character_profiles", []), "Bán Hàng" in current_mode)
    
    prompt_more = f"""
    DỮ LIỆU SẢN PHẨM GỐC: {json.dumps(dna_data, ensure_ascii=False)}
    Ghi chú: "{product_ctx}"
    {get_realtime_context()}
    
    Hãy tạo thêm ĐÚNG 5 kịch bản mới (id từ {cur_len + 1} đến {cur_len + 5}) theo CHIẾN LƯỢC: {current_strategy}.
    
    QUY ĐỊNH:
    - ĐỒNG BỘ GIỚI TÍNH 100%: Giới tính trong `script_outfit_setup` (Nam/Nữ) BẮT BUỘC KHỚP TUYỆT ĐỐI với `gender` trong `voice_profile`.
    - KHÔNG DÙNG GIÁ TIỀN CON SỐ.
    
    Xuất JSON chuẩn với key 'script_outlines'. KHÔNG DÙNG DẤU NGOẶC KÉP CHƯA ESCAPE BÊN TRONG GIÁ TRỊ JSON.
    """
    sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins, char_rules_str, current_strategy, target_audience)
    res = call_gemini_with_retry([prompt_more], sys_inst)
    new_scripts = res.get("script_outlines", [])
    for i, sc in enumerate(new_scripts): sc["id"] = cur_len + i + 1
    st.session_state.expanded_scripts.extend(new_scripts)

def clone_script_id(target_id, current_mode, current_style, aspect_ratio, goal, target_duration_mins, current_strategy):
    target_script = st.session_state.generated_details[target_id]
    all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    cur_len = len(all_sources)
    char_rules_str = generate_char_rules_string(st.session_state.get("character_profiles", []), "Bán Hàng" in current_mode)
    
    p_clone = f"Dựa trên kịch bản gốc: {json.dumps(target_script, ensure_ascii=False)}. Tạo ĐÚNG 5 biến thể mới (id từ {cur_len+1} đến {cur_len+5}). Xuất JSON key 'cloned_outlines'. KHÔNG DÙNG DẤU NGOẶC KÉP CHƯA ESCAPE BÊN TRONG JSON."
    sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins, char_rules_str, current_strategy, "")
    res_c = call_gemini_with_retry([p_clone], sys_inst)
    cloned_list = res_c.get("cloned_outlines", [])
    for idx_c, cl in enumerate(cloned_list): cl["id"] = cur_len + idx_c + 1
    st.session_state.cloned_scripts.extend(cloned_list)

# ==============================================================================
# RENDER GIAO DIỆN CHÍNH
# ==============================================================================
col_mode, col_style = st.columns([1.5, 1])
with col_mode:
    selected_mode = st.selectbox("🎯 Chọn Thể Loại Nội Dung:", options=allowed_modules)

# Dynamic Strategy Options
if "Bán Hàng" in selected_mode or "Mẹ & Bé" in selected_mode:
    strat_options = ["Hỗn hợp (2 Trực diện + 3 Drama)", "100% Drama / Shoppertainment", "100% Bán hàng trực diện (Hard Sale)"]
elif "Lịch Sử" in selected_mode:
    strat_options = ["Phim Hoạt hình Dã sử (Có Tranh cãi / Hành động / Chiến tranh)", "Phim Tài liệu / Kể chuyện lịch sử (Trang nghiêm)"]
elif "Doanh Nghiệp" in selected_mode or "Phóng Sự" in selected_mode:
    strat_options = ["Kể chuyện thương hiệu / Phóng sự chuyên sâu", "Trình diễn hình ảnh / Không gian Cinematic (Showcase)"]
else:
    strat_options = ["Viral / Bắt trend giải trí", "Chia sẻ kiến thức / Trải nghiệm thực tế", "Kể chuyện cảm xúc (Storytelling)"]

with col_style:
    selected_style_vn = st.selectbox("🎨 Chọn Phong Cách Hình Ảnh:", options=[
        "Điện Ảnh Chân Thực (Người thật / Siêu thực 8K)", "Hoạt Hình 3D (Kiểu Pixar / Disney)", "Hoạt Hình 2D (Phong cách Ghibli / Anime)", 
        "Tranh Thủy Mặc Cổ Phong (Truyền thống Á Đông)", "Viễn Tưởng Tương Lai (Cyberpunk)", "Studio Tối Giản (Hiện đại, Sạch sẽ)"
    ])
    style_mapping = {"Điện Ảnh Chân Thực (Người thật / Siêu thực 8K)": "Cinematic Realism", "Hoạt Hình 3D (Kiểu Pixar / Disney)": "3D Pixar Animation", "Hoạt Hình 2D (Phong cách Ghibli / Anime)": "2D Ghibli Anime", "Tranh Thủy Mặc Cổ Phong (Truyền thống Á Đông)": "Traditional Ink Wash", "Viễn Tưởng Tương Lai (Cyberpunk)": "Cyberpunk", "Studio Tối Giản (Hiện đại, Sạch sẽ)": "Minimalist Studio"}
    selected_style = style_mapping.get(selected_style_vn, "Cinematic Realism")

col_strat, col_ratio, col_time = st.columns([1.5, 1, 1])
with col_strat: selected_strategy = st.selectbox("🧠 Chiến lược Kịch bản (AI Strategy):", options=strat_options)
with col_ratio: selected_aspect = "9:16" if "9:16" in st.selectbox("Tỷ lệ khung hình:", ["9:16 (Dọc - TikTok, Reels)", "16:9 (Ngang - YouTube, Facebook)"]) else "16:9"
with col_time: target_duration_mins = 0.5 if "Bán Hàng" in selected_mode else st.number_input("⏱️ Thời lượng mong muốn (Phút):", min_value=0.5, max_value=30.0, value=1.0, step=0.5)

content_goal = "Sales & Conversion" if "Bán Hàng" in selected_mode else ("Brand Awareness" if "Doanh Nghiệp" in selected_mode else "Viral & Education")

# ==============================================================================
# XỬ LÝ SỰ KIỆN NÚT BẤM (ANTI-STALE UI TRIGGER)
# ==============================================================================
if st.session_state.action_trigger:
    action = st.session_state.action_trigger
    param = st.session_state.action_param
    st.session_state.action_trigger, st.session_state.action_param = None, None
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    if action == "create_detail":
        st.toast(f"⏳ Đang dựng chi tiết kịch bản #{param}...", icon="🎬")
        with st.container(border=True):
            st.markdown(f"<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG XỬ LÝ...</div>", unsafe_allow_html=True)
            try:
                create_scene_details_for_id(int(param), selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, selected_strategy)
                st.session_state.active_script_id = int(param)
                st.session_state.global_toast, st.session_state.global_toast_icon = f"Đã dựng thành công kịch bản #{param}!", "✅"
                st.session_state.scroll_to_top = True
            except Exception as e: st.error(f"❌ Lỗi: {e}")
            time.sleep(0.2)
            st.rerun() 
            
    elif action == "clone_script":
        st.toast(f"⏳ Đang nhân bản biến thể cho kịch bản #{param}...", icon="🧬")
        with st.container(border=True):
            st.markdown(f"<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG XỬ LÝ...</div>", unsafe_allow_html=True)
            try:
                clone_script_id(int(param), selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, selected_strategy)
                st.session_state.global_toast, st.session_state.global_toast_icon = f"Đã nhân bản kịch bản #{param}!", "🧬"
                st.session_state.scroll_to_top = True
            except Exception as e: st.error(f"❌ Lỗi: {e}")
            time.sleep(0.2)
            st.rerun()
            
    elif action == "generate_more":
        st.toast("⏳ Đang sáng tạo kịch bản mới...", icon="🧠")
        with st.container(border=True):
            st.markdown("<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG PHÂN TÍCH DNA...</div>", unsafe_allow_html=True)
            try:
                strat_to_use = param if param else selected_strategy
                add_five_scripts_continuation(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, strat_to_use)
                st.session_state.global_toast, st.session_state.global_toast_icon = "Đã bổ sung kịch bản mới!", "🧠"
                st.session_state.scroll_to_top = True
            except Exception as e: st.error(f"❌ Lỗi: {e}")
            time.sleep(0.2)
            st.rerun()
    st.stop()

# ==============================================================================
# RENDER UI THƯỜNG
# ==============================================================================
st.markdown("---")
input_text = st.text_area("✍️ Tóm tắt ý tưởng, chủ đề hoặc mô tả chi tiết dự án/sản phẩm:", height=80, key="main_input_context")

col_p_img, col_c_img = st.columns([1, 1])
with col_p_img: uploaded_files = st.file_uploader("📦 Tải ảnh Sản phẩm / Bối cảnh chính", type=["jpg", "jpeg", "png"], accept_multiple_files=True, label_visibility="collapsed", key=f"main_uploader_{st.session_state.file_uploader_key}")
with col_c_img: num_chars = st.number_input("👤 Số lượng Nhân vật tham chiếu", min_value=0, max_value=8, step=1, key="num_chars_input")

char_inputs = []
if num_chars > 0:
    with st.expander(f"🎭 HỒ SƠ DIỄN VIÊN ({num_chars})", expanded=True):
        n_cols = 4 if num_chars > 2 else 2
        grid_cols = st.columns(n_cols)
        for i in range(num_chars):
            with grid_cols[i % n_cols]:
                with st.container(border=True):
                    st.markdown(f"<div style='color:#d90429; font-weight:800; font-size:14px; margin-bottom:5px;'>Diễn viên {i+1}</div>", unsafe_allow_html=True)
                    c_role = st.text_input("Vai trò", key=f"c_role_{i}_{st.session_state.file_uploader_key}", placeholder="Vd: Mẹ 30 tuổi...", label_visibility="collapsed")
                    c_file = st.file_uploader("Ảnh", type=["jpg", "jpeg", "png"], key=f"c_img_{i}_{st.session_state.file_uploader_key}", label_visibility="collapsed")
                    if c_file and c_role.strip(): char_inputs.append({"id": i+1, "role": c_role.strip(), "file": c_file})

if st.button("🚀 Bắt Đầu Phân Tích Chi Tiết & Lên Kịch Bản", type="primary", use_container_width=True, disabled=not (input_text.strip() or uploaded_files or char_inputs)):
    with st.spinner("⏳ Đang phân tích DNA chuyên sâu..."):
        try:
            st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
            st.session_state.current_input_context = input_text.strip() if input_text else "Phân tích từ hình ảnh."
            safe_input_context = st.session_state.current_input_context.replace('"', "'").replace('\n', ' ')
            char_rules_str = generate_char_rules_string(st.session_state.character_profiles, "Bán Hàng" in selected_mode)
            
            script_outlines_json = """
              "script_outlines": [
                {"id": 1, "title": "Tên kịch bản 1", "setting_style": "Mô tả bối cảnh", "script_outfit_setup": "Mô tả 1 bộ đồ cho nhân vật (GHI RÕ MÀU SẮC)", "angle": "Góc tiếp cận", "target_hook": "Câu mở đầu mạnh mẽ", "recommended_scenes_count": "3 đến 4 cảnh", "voice_profile": {"gender": "[Chỉ điền 'Nam' hoặc 'Nữ']", "tone": "năng lượng"}},
                {"id": 2, "title": "Tên kịch bản 2", "setting_style": "...", "script_outfit_setup": "...", "angle": "...", "target_hook": "...", "recommended_scenes_count": "3 đến 4 cảnh", "voice_profile": {"gender": "Nữ", "tone": "năng lượng"}},
                {"id": 3, "title": "Tên kịch bản 3", "setting_style": "...", "script_outfit_setup": "...", "angle": "...", "target_hook": "...", "recommended_scenes_count": "3 đến 4 cảnh", "voice_profile": {"gender": "Nam", "tone": "năng lượng"}},
                {"id": 4, "title": "Tên kịch bản 4", "setting_style": "...", "script_outfit_setup": "...", "angle": "...", "target_hook": "...", "recommended_scenes_count": "3 đến 4 cảnh", "voice_profile": {"gender": "Nữ", "tone": "năng lượng"}},
                {"id": 5, "title": "Tên kịch bản 5", "setting_style": "...", "script_outfit_setup": "...", "angle": "...", "target_hook": "...", "recommended_scenes_count": "3 đến 4 cảnh", "voice_profile": {"gender": "Nam", "tone": "năng lượng"}}
              ]
            """
            
            prompt_text = f"""
            Phân tích chuyên sâu cho thể loại '{selected_mode}' - Chiến lược: '{selected_strategy}'.
            Thông tin: "{safe_input_context}". {get_realtime_context()}
            QUY ĐỊNH (CRITICAL): Giới tính trong `script_outfit_setup` PHẢI KHỚP với `gender` trong `voice_profile`. KHÔNG DÙNG GIÁ TIỀN CON SỐ.
            TRẢ VỀ JSON CHUẨN GỒM KEY 'content_analysis' VÀ 'script_outlines':
            {{
              "content_analysis": {{
                "primary_target_audience": "Tệp khách hàng tiềm năng nhất.",
                "mechanical_and_accessories": "Kiểu dáng, màu sắc, TỶ LỆ KÍCH THƯỚC thực tế.",
                "customer_pain_points": "Nỗi đau khách hàng.", "core_desires": "Mong muốn cốt lõi.", "emotional_or_usp_hook": "USP / Slogan.",
                "visual_physics_rules": "Quy chuẩn vật lý.", "prompt_dna_lock": "Khóa thị giác đồng bộ."
              }},
              {script_outlines_json}
            }}
            """
            payload = []
            if uploaded_files:
                payload.append("ẢNH THAM CHIẾU:")
                for f in uploaded_files: payload.append(types.Part.from_bytes(data=f.getvalue(), mime_type=f.type or "image/jpeg"))
            if char_inputs:
                for c in char_inputs:
                    payload.append(f"ẢNH NHÂN VẬT {c['id']} - VAI TRÒ: {c['role']}:")
                    payload.append(types.Part.from_bytes(data=c['file'].getvalue(), mime_type=c['file'].type or "image/jpeg"))
            payload.append(prompt_text)
            
            res = call_gemini_with_retry(payload, get_system_instructions(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, char_rules_str, selected_strategy, "Người dùng"))
            
            st.session_state.content_analysis = res.get("content_analysis")
            st.session_state.all_scripts = res.get("script_outlines", [])
            st.session_state.cloned_scripts, st.session_state.expanded_scripts, st.session_state.generated_details, st.session_state.active_script_id = [], [], {}, None
            st.session_state.scroll_to_top = True
            st.session_state.global_toast, st.session_state.global_toast_icon = "Đã khởi tạo dự án!", "✅"
            time.sleep(0.1)
            st.rerun()
        except Exception as e: st.error(f"❌ Lỗi thực thi: {e}")

if st.session_state.content_analysis and not st.session_state.action_trigger:
    st.divider()
    ca = st.session_state.content_analysis
    st.markdown(f"### 🔍 **Phân Tích DNA Chi Tiết Đa Tầng**")
    with st.container(border=True):
        st.markdown(f"**🎯 1. Tệp khách hàng & Nỗi đau:**<br><div style='line-height:1.6; font-size: 14px;'>• Tệp chính: {ca.get('primary_target_audience', 'N/A')}<br>{format_analysis_field(ca.get('customer_pain_points', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(f"**🏭 2. Thông số Sản phẩm:**<br><div style='line-height:1.6; font-size: 14px;'>{format_analysis_field(ca.get('mechanical_and_accessories', 'N/A'))}</div>", unsafe_allow_html=True)

# ==============================================================================
# HIỂN THỊ DANH SÁCH & CHI TIẾT
# ==============================================================================
all_combined = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts

if all_combined and st.session_state.active_script_id is None and not st.session_state.action_trigger:
    st.divider()
    completed, pending = [], []
    for sc in all_combined:
        if int(sc.get("id", 0)) in st.session_state.generated_details: completed.append(sc)
        else: pending.append(sc)

    st.markdown("### 🎬 **1. Kịch Bản Đã Hoàn Thiện (Sẵn Sàng Sản Xuất)**")
    if not completed: st.info("💡 Chọn một ý tưởng bên dưới để dựng chi tiết cảnh quay.")
    else:
        for outline in completed:
            sc_id = int(outline.get("id", 0))
            with st.container(border=True):
                c1, c2, c3 = st.columns([2.5, 1, 1])
                with c1: st.markdown(f"**#{sc_id}. {outline.get('title')}** — <span class='badge-ready'>ĐÃ HOÀN THIỆN</span><br><span style='font-size:13px;color:#64748b;'>{outline.get('setting_style')}</span>", unsafe_allow_html=True)
                with c2: 
                    if st.button("👁️ Xem chi tiết", key=f"v_{sc_id}", use_container_width=True):
                        st.session_state.action_trigger, st.session_state.action_param = "view_detail", sc_id
                        st.session_state.active_script_id = sc_id
                        st.session_state.scroll_to_top = True
                        st.rerun()
                with c3:
                    if st.button("🚀 Nhân bản 5 bản", key=f"c_{sc_id}", type="primary", use_container_width=True):
                        st.session_state.action_trigger, st.session_state.action_param = "clone_script", sc_id
                        st.rerun()

    st.markdown("### ⏳ **2. Ý Tưởng Đang Chờ Dựng Cảnh**")
    if not pending: st.success("Tất cả đã hoàn thiện!")
    else:
        for outline in pending:
            sc_id = int(outline.get("id", 0))
            with st.container(border=True):
                c1, c2 = st.columns([3, 1.2])
                with c1: st.markdown(f"**#{sc_id}. {outline.get('title')}** — <span class='badge-pending'>ĐANG CHỜ</span><br><span style='font-size:13px;color:#64748b;'>{outline.get('setting_style')}</span>", unsafe_allow_html=True)
                with c2:
                    if st.button("✨ Dựng Cảnh Ngay", key=f"g_{sc_id}", use_container_width=True):
                        st.session_state.action_trigger, st.session_state.action_param = "create_detail", sc_id
                        st.rerun()

    # Nút gọi thêm động (Dynamic Buttons)
    st.markdown("---")
    st.markdown("### 🔄 Gọi Thêm Kịch Bản (Mở Rộng Ý Tưởng)")
    if "Bán Hàng" in selected_mode or "Mẹ & Bé" in selected_mode:
        cb1, cb2, cb3 = st.columns(3)
        with cb1:
            if st.button("➕ 5 Kịch bản Hỗn hợp", use_container_width=True):
                st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Hỗn hợp (2 Trực diện + 3 Drama)"
                st.rerun()
        with cb2:
            if st.button("➕ 5 Kịch bản Drama/Giải trí", use_container_width=True):
                st.session_state.action_trigger, st.session_state.action_param = "generate_more", "100% Drama / Shoppertainment"
                st.rerun()
        with cb3:
            if st.button("➕ 5 Kịch bản Bán Hàng Trực diện", use_container_width=True):
                st.session_state.action_trigger, st.session_state.action_param = "generate_more", "100% Bán hàng trực diện (Hard Sale)"
                st.rerun()
    elif "Lịch Sử" in selected_mode:
        cb1, cb2 = st.columns(2)
        with cb1:
            if st.button("➕ 5 Kịch bản Phim Tài Liệu", use_container_width=True):
                st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Phim Tài liệu / Kể chuyện lịch sử (Trang nghiêm)"
                st.rerun()
        with cb2:
            if st.button("➕ 5 Kịch bản Hoạt Hình Dã Sử (Hành động)", use_container_width=True):
                st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Phim Hoạt hình Dã sử (Có Tranh cãi / Hành động / Chiến tranh)"
                st.rerun()
    else:
        if st.button("➕ Gọi Thêm 5 Kịch Bản Mới", type="primary", use_container_width=True):
            st.session_state.action_trigger, st.session_state.action_param = "generate_more", selected_strategy
            st.rerun()

if st.session_state.active_script_id and not st.session_state.action_trigger:
    st.divider()
    if st.button("⬅️ Quay lại danh sách tổng"):
        st.session_state.active_script_id = None
        st.session_state.scroll_to_top = True
        st.rerun()

    active_script = st.session_state.generated_details.get(st.session_state.active_script_id, {})
    vp = active_script.get("voice_profile", {"gender": "Nữ", "tone": "Truyền cảm"}) if isinstance(active_script.get("voice_profile"), dict) else {"gender": "Nữ", "tone": "Truyền cảm"}

    st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {active_script.get('title')}**")
    st.info(f"⏱️ {active_script.get('total_estimated_duration', '24s')} | 🎙️ Giọng: **{vp.get('gender')} ({vp.get('tone')})** | 👔 Trang phục: **{active_script.get('script_outfit_setup', 'Mặc định')}**")

    for idx, scene in enumerate(active_script.get("scenes", []), start=1):
        dur = scene.get("duration", "6s")
        st.markdown(f"#### **📍 Phân cảnh {idx} ({dur}) — [ {scene.get('transition_type', 'Cắt cứng')} ]**")
        st.markdown(f"🏛️ **Bối cảnh & Miêu tả:** *{scene.get('scene_setting')}*")
        st.markdown(f"**🎙️ Đạo diễn diễn xuất:** *{scene.get('voice_director_vn')}*")
        st.markdown(f"**💬 Lời thuyết minh (Thoại sạch):** `\"{scene.get('voiceover_vi')}\"`")
        
        img_p = scene.get('image_prompt', '')
        st.markdown(f"**🖼️ Prompt Ảnh (Imagen 3 - {selected_aspect}):**")
        if "dùng ảnh cuối của cảnh trước" in img_p.lower() or "dùng frame ảnh cuối" in img_p.lower():
            st.info("🔄 Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu (Image-to-Video) để giữ liền mạch khung hình.")
        else:
            st.code(img_p, language="text")
            safe_copy_button(img_p, f"📋 Sao Chép Prompt Ảnh {idx}")
            
        vid_p = scene.get('video_prompt', '')
        st.markdown(f"**🎥 Prompt Video (Veo 3):**")
        st.code(vid_p, language="text")
        safe_copy_button(vid_p, f"📋 Sao Chép Prompt Video {idx}")
        st.markdown("---")
