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
            "expires_at": "2099-12-31",
            "credits": 9999
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

def deduct_user_credit(email, amount=1):
    if email == ADMIN_EMAIL:
        return True
    if email in st.session_state.licensed_accounts:
        curr_cred = st.session_state.licensed_accounts[email].get("credits", 10)
        if curr_cred >= amount:
            st.session_state.licensed_accounts[email]["credits"] = curr_cred - amount
            save_licensed_accounts(st.session_state.licensed_accounts)
            return True
    return False

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
    ("global_toast", ""), ("global_toast_icon", "✅"),
    ("narrator_mode", "Nhân vật xuất hiện nói chuyện (On-camera)"),
    ("extra_angle_type", "⚡ Dạng Flash Sale & Deal hời (Tập trung chốt đơn)"),
    ("extra_num_chars", 1),
    ("extra_duration_mins", 1.0)
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

# ==============================================================================
# HÀM HỖ TRỢ API TẠO ẢNH VÀ VIDEO TRỰC TIẾP
# ==============================================================================
def generate_image_with_imagen(prompt_text, aspect_ratio_str="9:16"):
    try:
        result = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt_text,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="9:16" if "9:16" in aspect_ratio_str else "16:9"
            )
        )
        for generated_image in result.generated_images:
            return generated_image.image.image_bytes
    except Exception as e:
        st.error(f"Lỗi tạo ảnh: {e}")
    return None

def generate_video_with_veo(image_bytes, video_prompt_text):
    try:
        operation = client.models.generate_videos(
            model='veo-2.0-generate-001',
            prompt=video_prompt_text,
            image=types.Image.from_bytes(data=image_bytes),
            config=types.GenerateVideosConfig(
                fps=24,
                duration_seconds=5
            )
        )
        while not operation.done:
            time.sleep(10)
            operation = client.operations.get(operation)
        
        video_result = operation.response
        return video_result.generated_videos[0].video.video_bytes
    except Exception as e:
        st.error(f"Lỗi tạo video: {e}")
    return None

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
                init_credits = st.number_input("Tặng Credit khởi tạo:", min_value=1, max_value=1000, value=20)
                
                if st.form_submit_button("💾 Lưu / Cấp Quyền Mới", use_container_width=True):
                    if new_account_id.strip():
                        expiry_date = "2099-12-31" if "Vĩnh viễn" in duration_option else (datetime.now() + timedelta(days=3 if "Dùng thử" in duration_option else {"1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730, "3 Năm": 1095, "5 Năm": 1825, "10 Năm": 3650}.get(duration_option, 30))).strftime("%Y-%m-%d")
                        st.session_state.licensed_accounts[new_account_id.strip()] = {"contact": new_account_id.strip(), "roles": assigned_modules, "expires_at": expiry_date, "credits": int(init_credits)}
                        save_licensed_accounts(st.session_state.licensed_accounts)
                        
                        st.session_state.global_toast = f"Đã cấp quyền thành công cho: {new_account_id.strip()}!"
                        st.session_state.global_toast_icon = "✅"
                        st.rerun()

            if st.session_state.licensed_accounts:
                with st.expander(f"📋 Danh sách tài khoản đã cấp ({len(st.session_state.licensed_accounts)})"):
                    for acc, info in list(st.session_state.licensed_accounts.items()):
                        st.markdown(f"**👤 {acc}**")
                        st.caption(f"• Quyền: {', '.join(info.get('roles', []))}<br>• Hết hạn: {info.get('expires_at')}<br>• Credit: {info.get('credits', 10)}", unsafe_allow_html=True)
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
            <a href="https://facebook.com/your_facebook" target="_blank" style="background: #0866ff; color: white; padding: 5px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 11px;">📘 Facebook</a>
            <a href="https://tiktok.com/@your_tiktok" target="_blank" style="background: #000000; color: white; padding: 5px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 11px;">🎵 TikTok</a>
        </div>
        <div style="font-weight: 700; color: #166534; font-size: 12px; margin-top: 8px;">📞 Hotline: 096 8484 369</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.is_logged_in:
        st.markdown("---")
        st.markdown("### 👤 **Thông Tin Tài Khoản**")
        st.success(f"Đang đăng nhập: **{st.session_state.current_user_email}**")
        
        # Hiển thị số dư Credit khả dụng
        user_info = st.session_state.licensed_accounts.get(st.session_state.current_user_email, {})
        current_credits = user_info.get("credits", 10)
        st.metric(label="💎 Số Dư Credit Khả Dụng", value=f"{current_credits} Credits")
        
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
            raise Exception("AI vô tình sinh ra định dạng bị lỗi cấu trúc. Dữ liệu đã bị chặn lại. Vui lòng bấm 'Tạo chi tiết ngay' thêm lần nữa.")

def get_realtime_context():
    now = datetime.now()
    month = now.month
    year = now.year
    if month in [2, 3, 4]: season = "Mùa Xuân"
    elif month in [5, 6, 7]: season = "Mùa Hè"
    elif month in [8, 9, 10]: season = "Mùa Thu (Mùa tựu trường / Back-to-school)"
    else: season = "Mùa Đông (Mùa lễ hội cuối năm / Winter holidays)"
    return f"THỜI GIAN THỰC TẾ: Tháng {month}/{year} ({season}). TƯ DUY ÁP DỤNG MÙA VỤ (CRITICAL): BẠN PHẢI PHÂN TÍCH SẢN PHẨM THỰC TẾ. CHỈ áp dụng bối cảnh mùa vụ/thời gian này vào Hook hoặc Lý do mua hàng NẾU nó thực sự giải quyết nỗi đau hoặc kích thích mong muốn của khách hàng cho RIÊNG sản phẩm này. NẾU sản phẩm KHÔNG LIÊN QUAN đến mùa vụ, HÃY BỎ QUA HOÀN TOÀN yếu tố thời gian và tập trung 100% vào USP/Nỗi đau cốt lõi."

def get_system_instructions(mode: str, style: str, aspect_ratio: str, goal: str, target_duration_mins: float = 0.5, char_rules: str = "", narrator_mode: str = "") -> str:
    is_sales = ("Bán Hàng" in mode or "Sales" in goal)
    is_knowledge = "Chia sẻ kiến thức" in goal or "Review" in goal
    is_story = "Kể chuyện" in goal or "Phim ngắn" in goal
    is_corporate = "Doanh Nghiệp" in mode or "Tuyên Truyền" in mode
    
    format_instruction = "9:16 vertical video format, mobile-first framing" if aspect_ratio == "9:16" else "16:9 widescreen cinematic format, professional movie framing"
    
    total_seconds = int(target_duration_mins * 60)
    if is_sales:
        duration_rule = "QUY CHUẨN THỜI LƯỢNG BÁN HÀNG TIKTOK (TỐI ƯU CREDIT): BẮT BUỘC CHỈ ĐƯỢC TẠO TỪ 3 ĐẾN 4 PHÂN CẢNH. Mỗi cảnh chọn mốc 4s, 6s hoặc 8s. Cấu trúc nén thông minh: Hook mạnh (Nỗi đau / Vấn đề) -> Demo/Giải pháp -> CTA chốt đơn."
    else:
        duration_rule = f"QUY CHUẨN THỜI LƯỢNG KỂ CHUYỆN / REVIEW DÀI ({target_duration_mins} phút / {total_seconds} giây): Xây dựng cốt truyện có chiều sâu. Vì AI Video (Veo 3) chỉ sinh được video dài tối đa 4s, 6s, 8s, nên bạn BẮT BUỘC phải chia TỔNG {total_seconds} GIÂY thành nhiều phân cảnh nhỏ (chỉ được chọn mốc 4s, 6s hoặc 8s mỗi cảnh)."

    if is_sales:
        goal_directive = "MỤC TIÊU 'BÁN HÀNG': Kịch bản đánh thẳng vào nỗi đau thực tế đời sống, đưa giải pháp và Kêu gọi hành động (CTA) dồn dập."
        tone_instruction = "NHỊP ĐỘ VÀ NĂNG LƯỢNG (PACE & ENERGY): fast-paced, high-energy, enthusiastic sales tone."
    elif is_knowledge:
        goal_directive = "MỤC TIÊU 'CHIA SẺ KIẾN THỨC / REVIEW': Kịch bản phải VÀO THẲNG TRỌNG TÂM ngay giây đầu tiên, lược bỏ hoàn toàn các phần dạo đầu, chào hỏi dài dòng."
        tone_instruction = "NHỊP ĐỘ VÀ NĂNG LƯỢNG (PACE & ENERGY): fast-paced, engaging, sharp, professional tone."
    elif is_story:
        goal_directive = "MỤC TIÊU 'KỂ CHUYỆN / PHIM NGẮN': Xây dựng cao trào, thắt mở nút rõ ràng. Kể chuyện lôi cuốn, chạm cảm xúc."
        tone_instruction = "NHỊP ĐỘ VÀ NĂNG LƯỢNG (PACE & ENERGY): expressive, emotional storytelling tone."
    elif is_corporate:
        goal_directive = "MỤC TIÊU 'DOANH NGHIỆP / TUYÊN TRUYỀN': Thể hiện sự chuyên nghiệp, uy tín của doanh nghiệp/tổ chức."
        tone_instruction = "NHỊP ĐỘ VÀ NĂNG LƯỢNG (PACE & ENERGY): confident, professional, authoritative tone."
    else:
        goal_directive = "MỤC TIÊU 'VIRAL / THƯƠNG HIỆU CÁ NHÂN': Cấu trúc kịch bản có Hook cực mạnh ở 3 giây đầu."
        tone_instruction = "NHỊP ĐỘ VÀ NĂNG LƯỢNG (PACE & ENERGY): natural, engaging, dynamic pacing."

    is_offscreen_narrator = ("Lồng tiếng ngoài" in narrator_mode)
    
    if is_offscreen_narrator:
        voiceover_instruction = f"""
        7. QUY CHUẨN THUYẾT MINH NGOÀI (OFF-SCREEN NARRATOR):
            - {goal_directive}
            - SỬ DỤNG GIỌNG ĐỌC LỒNG TIẾNG NGOÀI (OFF-SCREEN NARRATOR): Giọng đọc là người dẫn chuyện không xuất hiện nói trước ống kính. Visual tập trung 100% vào bối cảnh, con người và hành động thực tế (B-roll footage/Documentary style).
            - NGẮT NHỊP & CẢM XÚC THUYẾT MINH (PAUSE & RHYTHM): Trong câu thoại `voiceover_vi`, BẮT BUỘC phải khéo léo chèn các dấu phẩy (,), dấu chấm lửng (...) hoặc dấu gạch ngang (-) tại các nhịp nghỉ hợp lý để TTS tự ngắt nghỉ có cảm xúc.
            - PHIÊN ÂM TIẾNG VIỆT CHUẨN KHI ĐỌC: Viết rõ cách đọc tiếng Việt bồi. VD: 'Bluetooth' -> 'Bờ lu tút'. TUYỆT ĐỐI KHÔNG ĐƯA GIÁ TIỀN CỤ THỂ VÀO THOẠI.
        8. BỘ LỌC CHÍNH SÁCH ĐA NỀN TẢNG:
            - TUYỆT ĐỐI KHÔNG DÙNG TỪ NGỮ CỰC ĐOAN: Cấm dùng "100%", "tuyệt đối", "cam kết", "chắc chắn", "vĩnh viễn".
            - CẤM TUYÊN BỐ Y TẾ SAI LỆCH VÀ GIEO RẮC SỢ HÃI: Không dùng từ "độc hại", "ung thư". Thay bằng: "hỗ trợ bảo vệ", "kém an toàn".
            - CẤM KHAN HIẾM GIẢ & ĐIỀU HƯỚNG: Không dùng số lượng tồn kho ảo. Cấm tuyệt đối: "livestream", "phiên live", "inbox riêng", "zalo".
        """
    else:
        voiceover_instruction = f"""
        7. QUY CHUẨN THUYẾT MINH, ĐỒNG BỘ & ÂM THANH NỀN:
            - {goal_directive}
            - CẤM DÙNG GIỌNG THUYẾT MINH PHIM TÀI LIỆU: Giọng nói phải là CỦA CÙNG MỘT NGƯỜI (KOC/Diễn viên) xuất hiện trực tiếp trước ống kính. 
            - NGẮT NHỊP & CẢM XÚC THUYẾT MINH (PAUSE & RHYTHM): Trong câu thoại `voiceover_vi`, BẮT BUỘC chủ động chèn các dấu phẩy (,), dấu chấm lửng (...) hoặc dấu gạch ngang (-) để tạo quãng nghỉ lấy hơi, giúp nhân vật đọc có ngữ điệu cuốn hút, tự nhiên và có cảm xúc hơn.
            - ÂM THANH NỀN (AMBIENT/FOLEY SOUND): Nếu cảnh quay có hành động thực tế, thêm mô tả âm thanh nền vào video_prompt bằng tiếng Anh (VD: "Background ambient sound: sizzling meat, volume strictly lower than voiceover").
            - ĐỒNG NHẤT GIỌNG MIỀN BẮC CHUẨN (HÀ NỘI): Chèn lệnh "strict standard Northern Vietnamese (Hanoi) accent".
            - PHIÊN ÂM TIẾNG VIỆT CHUẨN KHI ĐỌC: VD: 'Bluetooth' -> 'Bờ lu tút'. TUYỆT ĐỐI KHÔNG ĐƯA GIÁ TIỀN CỤ THỂ VÀO THOẠI.
        8. BỘ LỌC CHÍNH SÁCH ĐA NỀN TẢNG:
            - TUYỆT ĐỐI KHÔNG DÙNG TỪ NGỮ CỰC ĐOAN: Cấm dùng "100%", "tuyệt đối", "cam kết", "chắc chắn", "vĩnh viễn".
            - CẤM TUYÊN BỐ Y TẾ SAI LỆCH VÀ GIEO RẮC SỢ HÃI: Không dùng từ "độc hại", "ung thư".
            - CẤM KHAN HIẾM GIẢ & ĐIỀU HƯỚNG: Không dùng số lượng tồn kho ảo. Cấm tuyệt đối: "livestream", "phiên live", "inbox riêng", "zalo".
        """

    master_director_directive = "CHẾ ĐỘ CHUYÊN GIA CAO CẤP: Tối ưu hóa sâu sắc các thông số điện ảnh chuyên sâu (Lighting setup, Lens focal length, Color grading) cho Imagen 3 và Veo 3."

    base = f"""
BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL ĐA NĂNG CHO IMAGEN 3 VÀ VEO 3.
PHONG CÁCH KẾT XUẤT THỊ GIÁC: {style.upper()}
ĐỊNH DẠNG KHUNG HÌNH: {format_instruction}
MỤC TIÊU CHIẾN DỊCH: {goal}
{duration_rule}
{master_director_directive}

🛑 QUY TẮC BẮT BUỘC 100% (KHÔNG ĐƯỢC VI PHẠM):
1. LƯU Ý QUAN TRỌNG VỀ JSON: BẮT BUỘC TRẢ VỀ JSON HỢP LỆ. DÙNG DẤU NGOẶC ĐƠN (') ĐỂ TRÍCH DẪN BÊN TRONG CHUỖI.
2. QUY TẮC QUỐC TỊCH: Nếu có con người chung chung, BẮT BUỘC chèn "Vietnamese".
{char_rules}
4. CẤM HIỂN THỊ UI/GIỎ HÀNG KHI KÊU GỌI HÀNH ĐỘNG (CRITICAL): Mọi `image_prompt` và `video_prompt` phải ép lệnh "Cinematic shot ONLY. ABSOLUTELY NO UI elements, NO shopping cart icons, NO on-screen text or social media overlays".
5. ĐỊNH VỊ TỆP KHÁCH HÀNG: Bắt buộc kịch bản phải xoay quanh tệp khách hàng có NHU CẦU CAO NHẤT.
6. CHỐNG BIẾN DẠNG SẢN PHẨM & KHÓA MÀU (ANTI-MORPHING & COLOR LOCK): Miêu tả chính xác màu sắc từ ảnh gốc. Ép lệnh "product maintains rigid structural integrity, zero shape morphing, strictly identical to reference" vào video_prompt.
6.1. ĐỒNG NHẤT BỐI CẢNH 100% (MASTER ENVIRONMENT LOCK - RẤT QUAN TRỌNG CHO NHIỀU NHÂN VẬT): 
    - Nếu kịch bản diễn ra tại một không gian cố định (như bàn ăn lẩu, phòng khách, phòng ngủ), MỌI `image_prompt` và `video_prompt` của TẤT CẢ các cảnh trong cùng một kịch bản BẮT BUỘC phải giữ nguyên chuỗi mô tả không gian gốc (Master Setting) để tuyệt đối không bị trôi cảnh, đổi quán hay đổi phòng.
6.2. ĐỒNG NHẤT TRANG PHỤC TOÀN DIỆN (FULL OUTFIT LOCK):
    - Cấu hình trang phục trong `script_outfit_setup` phải miêu tả đầy đủ cả Áo, Quần/Váy và Giày với màu sắc cụ thể. Mọi prompt ảnh/video phải giữ nguyên toàn bộ bộ đồ này từ đầu đến cuối kịch bản.
7. CƠ CHẾ NHÂN VẬT: {"Cho phép cảnh quay phong cách tài liệu/B-roll (Off-screen narrator)." if is_offscreen_narrator else "Bắt buộc mọi phân cảnh đều có sự hiện diện và tương tác của nhân vật."}
8. CHUYỂN CẢNH ĐỘNG & NEO KHUNG HÌNH (MATCH CUT): 
    - Luân phiên [Cắt cứng (Hard Cut)] và [Nối liền mạch (Match Cut)]. 
    - ĐẶC BIỆT LƯU Ý: Nếu cảnh là [ Nối liền mạch (Match Cut) ], phần `image_prompt` BẮT BUỘC phải ghi chính xác tuyệt đối cụm từ: "Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu cho video" (tuyệt đối không tự bịa prompt ảnh mới cho cảnh Match Cut).
9. GIỚI HẠN TỪ VỰNG THUYẾT MINH (VOICE PACING LIMIT): Kịch bản giọng đọc 'voiceover_vi' PHẢI NGẮN GỌN, CÓ DẤU NGẮT NGHỈ CẢM XÚC. Tuân thủ: Cảnh 4s (tối đa 14 từ); Cảnh 6s (tối đa 20 từ); Cảnh 8s (tối đa 26 từ).
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
        return "3. NHÂN VẬT & DIỄN VIÊN THAM CHIẾU: Xây dựng nhân vật linh hoạt theo kịch bản."
        
    rules = "3. KHÓA KHUÔN MẶT KOC VÀ ĐỒNG NHẤT TRANG PHỤC:\n    - Người dùng đã cung cấp ảnh các nhân vật. Bạn PHẢI phân vai tiếng Anh chính xác kèm lệnh khóa:\n"
    for p in profiles:
        safe_role = p['role'].replace('"', "'")
        rules += f"     + Nhân vật {p['id']}: Đóng vai '{safe_role}'. Lệnh bắt buộc: 'Character {p['id']} ({safe_role}) featuring the exact identity of reference image {p['id']}'.\n"
    rules += "    - KHUÔN MẶT: Bắt buộc dùng lệnh 'featuring the exact identity of reference image X' để AI giữ đúng khuôn mặt.\n"
    if is_sales_mode:
        rules += "    - TRANG PHỤC TOÀN DIỆN (FULL OUTFIT LOCK): Thiết lập miêu tả chi tiết cả Áo, Quần/Váy và Giày trong `script_outfit_setup` và giữ nguyên 100% trong toàn bộ các cảnh."
    else:
        rules += "    - TRANG PHỤC LINH HOẠT THEO NGỮ CẢNH: Thay đổi trang phục logic theo thời gian/không gian của từng phân cảnh."
    return rules

# ==============================================================================
# HỆ THỐNG XỬ LÝ LÕI AI (CORE FUNCTIONS)
# ==============================================================================

def add_five_scripts_continuation(current_mode: str, current_style: str, aspect_ratio: str, goal: str, target_duration_mins: float, custom_angle_type: str = "", extra_num_chars: int = 1, extra_duration_mins: float = 1.0):
    all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    cur_len = len(all_sources)
    product_ctx = st.session_state.get("current_input_context", "Sản phẩm hiện tại").replace('"', "'")
    dna_data = st.session_state.get("content_analysis", {}) 
    target_audience = dna_data.get("primary_target_audience", "Người dùng phù hợp")
    
    is_corporate = "Doanh Nghiệp" in current_mode or "Tuyên Truyền" in current_mode
    is_sales_mode = "Bán Hàng" in current_mode
    is_knowledge = "Chia sẻ kiến thức" in goal or "Review" in goal
    
    total_sec = int(extra_duration_mins * 60)
    duration_rule_extra = f"THỜI LƯỢNG MONG MUỐN CHO KỊCH BẢN NÀY: {extra_duration_mins} phút ({total_sec} giây). Bắt buộc phân bổ số lượng cảnh tổng cộng khớp với thời lượng này."

    angle_direction_rule = f"ĐỊNH HƯỚNG CHIẾN LƯỢC: Tập trung hoàn toàn theo thể loại: '{custom_angle_type}'." if custom_angle_type else ""
    char_count_rule = f"SỐ LƯỢNG NHÂN VẬT: Bắt buộc mỗi kịch bản phải có sự tham gia tương tác của đúng {extra_num_chars} nhân vật cùng xuất hiện chung trong bối cảnh cố định." if extra_num_chars > 1 else "Kịch bản tập trung vào 1 nhân vật chính xuyên suốt."

    if is_corporate:
        extra_rules = "- Bối cảnh không gian văn phòng, nhà xưởng quy mô hoặc dự án thực tế.\n- Không thúc ép mua hàng."
    elif is_sales_mode:
        extra_rules = f"- ĐỐI TƯỢNG: Phải tập trung vào tệp khách hàng: {target_audience}.\n{angle_direction_rule}\n{char_count_rule}\n- {duration_rule_extra}\n- TUYỆT ĐỐI KHÔNG ĐƯA MỨC GIÁ CỤ THỂ BẰNG CON SỐ."
    elif is_knowledge:
        extra_rules = f"- ĐỐI TƯỢNG: {target_audience}.\n{angle_direction_rule}\n{char_count_rule}\n- {duration_rule_extra}\n- VÀO THẲNG VẤN ĐỀ: Bỏ qua hoàn toàn đoạn chào hỏi dài dòng."
    else:
        extra_rules = f"- ĐỐI TƯỢNG: {target_audience}.\n{angle_direction_rule}\n{char_count_rule}\n- {duration_rule_extra}\n- Khai thác sâu khía cạnh cảm xúc, trải nghiệm thực tế."
        
    char_rules_str = generate_char_rules_string(st.session_state.get("character_profiles", []), is_sales_mode)
    realtime_ctx = get_realtime_context()
        
    prompt_more = f"""
    DỮ LIỆU SẢN PHẨM GỐC (DNA): {json.dumps(dna_data, ensure_ascii=False)}
    Ghi chú từ người dùng: "{product_ctx}"
    {realtime_ctx}
    
    Hãy tạo thêm đúng 5 kịch bản mới (id từ {cur_len + 1} đến {cur_len + 5}) với các key: id, title, setting_style, script_outfit_setup, angle, target_hook, recommended_scenes_count, voice_profile.
    
    QUY ĐỊNH BẮT BUỘC CHO KỊCH BẢN MỚI:
    {extra_rules}
    - Thêm key 'script_outfit_setup': Ghi rõ miêu tả trang phục toàn diện bao gồm Áo, Quần/Váy và Giày (BẮT BUỘC CHỈ ĐỊNH RÕ MÀU SẮC).
    - ĐỒNG BỘ GIỚI TÍNH 100% (CRITICAL): Giới tính nhân vật trong `script_outfit_setup` phải khớp tuyệt đối với `gender` trong `voice_profile`.
    Xuất JSON chuẩn với key 'script_outlines'.
    LƯU Ý CỰC KỲ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG DÙNG DẤU NGOẶC KÉP CHƯA ESCAPE (") HOẶC XUỐNG DÒNG BÊN TRONG CÁC GIÁ TRỊ JSON.
    """
    sys_inst = get_system_instructions(current_mode, selected_style, aspect_ratio, goal, extra_duration_mins, char_rules_str, st.session_state.narrator_mode)
    res = call_gemini_api([prompt_more], sys_inst)
    new_scripts = res.get("script_outlines", [])
    for i, sc in enumerate(new_scripts): sc["id"] = cur_len + i + 1
    st.session_state.expanded_scripts.extend(new_scripts)

def create_scene_details_for_id(target_id: int, current_mode: str, current_style: str, aspect_ratio: str, goal: str, target_duration_mins: float):
    all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_sources if isinstance(sc, dict) and sc.get("id") == target_id), None)
    if not outline:
        raise Exception(f"Không tìm thấy thông tin cho kịch bản #{target_id}")
    
    product_ctx = st.session_state.get("current_input_context", "Dự án hiện tại").replace('"', "'")
    safe_title = outline.get('title', '').replace('"', "'").replace('\n', ' ')
    safe_setting = outline.get('setting_style', '').replace('"', "'").replace('\n', ' ')
    safe_angle = outline.get('angle', '').replace('"', "'").replace('\n', ' ')
    safe_hook = outline.get('target_hook', '').replace('"', "'").replace('\n', ' ')
    
    is_sales_mode = "Bán Hàng" in current_mode
    is_knowledge = "Chia sẻ kiến thức" in goal or "Review" in goal
    is_story = "Kể chuyện" in goal or "Phim ngắn" in goal
    is_corporate = "Doanh Nghiệp" in current_mode or "Tuyên Truyền" in current_mode

    total_sec = int(target_duration_mins * 60)
    duration_str = f"{total_sec}s ({target_duration_mins} phút)"
    duration_rule_scene = f"TỔNG CỘNG ĐỘ DÀI CÁC CẢNH PHẢI ĐÚNG CHÍNH XÁC {total_sec} GIÂY. Chia nhỏ kịch bản thành các cảnh 4s, 6s hoặc 8s."

    v_profile = outline.get("voice_profile", {})
    if isinstance(v_profile, str):
        fixed_gender_vi = "Nữ" if "nữ" in v_profile.lower() else "Nam"
    elif isinstance(v_profile, dict):
        gender_val = v_profile.get("gender", "Nữ")
        if "hay Nữ" in gender_val or "/" in gender_val or "xác định" in gender_val.lower() or not gender_val.strip():
            fixed_gender_vi = "Nữ" 
        else:
            fixed_gender_vi = "Nữ" if "nữ" in gender_val.lower() else "Nam"
    else:
        fixed_gender_vi = "Nữ"
        
    gender_en = "male" if fixed_gender_vi.lower() == "nam" else "female"
    outfit_setup = outline.get("script_outfit_setup", "casual everyday outfit").replace('"', "'")
    char_rules_str = generate_char_rules_string(st.session_state.get("character_profiles", []), is_sales_mode)
    realtime_ctx = get_realtime_context()
    dna_data = st.session_state.get("content_analysis", {})
    mechanical_dna = dna_data.get("mechanical_and_accessories", "Sản phẩm")
    target_audience = dna_data.get("primary_target_audience", "Người dùng phù hợp")
    
    is_offscreen_narrator = ("Lồng tiếng ngoài" in st.session_state.narrator_mode)

    if is_offscreen_narrator:
        video_audio_prompt_rule = f"Prompt Video Veo 3 (tiếng Anh) - LỒNG TIẾNG NGOÀI: 'Audio: Cinematic background ambient sound matching the scene. Visual: Cinematic B-roll footage showing {{Master Environment Key}} and full outfit ({outfit_setup})... product maintains rigid structural integrity, zero shape morphing, action ends with the product fully visible and unoccluded. Cinematic shot ONLY. ABSOLUTELY NO UI elements.'"
        voice_director_rule = f"Giọng đọc ngoài (Off-screen narrator) Miền Bắc chuẩn (Hà Nội)... (Truyền cảm, chuyên nghiệp)"
    else:
        video_audio_prompt_rule = f"Prompt Video Veo 3 (tiếng Anh) - TRỰC TIẾP TRƯỚC ỐNG KÍNH: 'Audio: The exact same {gender_en} character speaking on-camera showing [BIỂU CẢM], punctuated by sharp expression. fast-paced, high-energy, enthusiastic sales tone. Strict standard Northern Vietnamese (Hanoi) accent. Background ambient sound: [Tiếng động môi trường nếu có]. Visual: Cinematic shot ONLY. ABSOLUTELY NO UI elements. Reading: [voiceover_vi]. Scene maintains the exact same {{Master Environment Key}} and full outfit ({outfit_setup}). Product maintains rigid structural integrity, zero shape morphing, action ends with the product fully visible and unoccluded.'"
        voice_director_rule = f"Giọng {fixed_gender_vi} Miền Bắc chuẩn (Hà Nội)... (BẮT BUỘC GHI RÕ HÀNH ĐỘNG KHUÔN MẶT)"

    prompt_detail = f"""
    Ngữ cảnh sản phẩm/dịch vụ: "{product_ctx}"
    Phân tích Gốc: {mechanical_dna}
    Đối tượng mục tiêu: {target_audience}
    Thể loại nội dung: "{current_mode}" | Mục tiêu chiến dịch: "{goal}" | Tỷ lệ khung hình: "{aspect_ratio}"
    {realtime_ctx}
    Ý tưởng kịch bản: ID {target_id} - {safe_title}
    Bối cảnh định hướng: {safe_setting} | Góc tiếp cận: {safe_angle} | Hook: {safe_hook}
    TRANG PHỤC TOÀN DIỆN CỐ ĐỊNH CHO KỊCH BẢN NÀY: {outfit_setup}
    GIỚI TÍNH ĐÃ CHỐT: {fixed_gender_vi} (English mapping: {gender_en})
    
    QUY ĐỊNH ĐẠO DIỄN LÊN PROMPT & KHÓA BỐI CẢNH (MASTER ENVIRONMENT & FULL OUTFIT LOCK):
    0. THIẾT LẬP KHÓA BỐI CẢNH GỐC: Tự định nghĩa một chuỗi mô tả không gian cố định bằng tiếng Anh cho kịch bản này (Ví dụ: "inside a cozy warm-lit Vietnamese family living room with wooden dining table and steaming hotpot"). Đảm bảo chuỗi này PHẢI XUẤT HIỆN TRONG TẤT CẢ các image_prompt và video_prompt.
    1. KỶ LUẬT THỜI LƯỢNG & NHỊP ĐỘ (VOICE PACING): SỐ TỪ trong `voiceover_vi` KHÔNG ĐƯỢC QUÁ NGẮN HOẶC QUÁ DÀI. Áp dụng: Cảnh 4s (12-14 từ); Cảnh 6s (18-21 từ); Cảnh 8s (24-28 từ). {duration_rule_scene}
    2. NGẮT NHỊP & CẢM XÚC THUYẾT MINH (PAUSE & RHYTHM): Trong `voiceover_vi`, BẮT BUỘC khéo léo chèn dấu phẩy (,), dấu chấm lửng (...) hoặc dấu gạch ngang (-) để tạo quãng nghỉ lấy hơi, giúp nhân vật đọc có ngữ điệu cuốn hút, tự nhiên và có cảm xúc hơn.
    3. CHUYỂN CẢNH ĐỘNG & NEO KHUNG HÌNH (MATCH CUT): 
       - Cảnh 1 bắt buộc là Wide Shot quy tụ đủ nhân vật làm mỏ neo. 
       - Nếu phân cảnh là [ Nối liền mạch (Match Cut) ], phần `image_prompt` BẮT BUỘC phải ghi chính xác tuyệt đối cụm từ: "Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu cho video" (TUYỆT ĐỐI KHÔNG tự bịa prompt ảnh mới cho cảnh Match Cut).
    4. MẠCH THOẠI SẠCH VÀ LIỀN MẠCH: Lời thoại nối liền bằng từ nối tò mò (VD: "Thế nhưng...", "Chưa hết đâu!"). TUYỆT ĐỐI KHÔNG chứa dấu ngoặc đơn (như `(Cười)`) bên trong `voiceover_vi`.
    5. DIỄN XUẤT, SFX & ÂM THANH NỀN: Biểu cảm phi ngôn ngữ miêu tả bằng tiếng Anh. Thêm âm thanh môi trường nếu có hành động thực tế.
    6. CHỐNG BIẾN DẠNG & KHÔNG CHE KHUẤT: Lệnh "product is fully visible, strictly NO hands or objects obscuring the main body" trong image_prompt.
    7. TỶ LỆ KÍCH THƯỚC: Thiết lập hệ quy chiếu vật lý rõ ràng.
    8. CHÍNH SÁCH TIKTOK: Không từ đe dọa, không cam kết 100%, không số lượng tồn kho ảo, không UI icon.
    
    Xuất chuẩn 1 Dict JSON duy nhất:
    {{
      "id": {target_id}, 
      "title": "{safe_title}", 
      "setting_style": "{safe_setting}",
      "script_outfit_setup": "{outfit_setup}",
      "voice_profile": {{"gender": "{fixed_gender_vi}", "tone": "nhịp độ nhanh, dồn dập"}},
      "total_estimated_duration": "{duration_str}",
      "scenes": [
        {{
          "scene_number": 1, 
          "duration": "8s", 
          "scene_setting": "Mô tả bối cảnh góc toàn cảnh quy tụ các nhân vật...", 
          "transition_type": "Mở đầu (Master Anchor Shot)", 
          "voice_director_vn": "{voice_director_rule}", 
          "voiceover_vi": "U là trời..., chiếc máy chiếu này nhỏ gọn lắm nhé! Mà chiếu lên nét căng đét luôn..., xem phim ở phòng ngủ cứ gọi là đỉnh chóp.", 
          "image_prompt": "Prompt Imagen 3 (tiếng Anh). Bao gồm Master Setting. ÉP LỆNH: '{gender_en} character... wearing {outfit_setup}...'. ÉP KÍCH THƯỚC: 'featuring the EXACT product which fits exactly in the palm, fully visible, strictly NO hands obscuring'.", 
          "video_prompt": "{video_audio_prompt_rule}"
        }},
        {{
          "scene_number": 2, 
          "duration": "6s", 
          "scene_setting": "Mô tả góc máy cận cảnh...", 
          "transition_type": "Cắt cứng (Hard Cut)", 
          "voice_director_vn": "{voice_director_rule}", 
          "voiceover_vi": "Nhưng đừng lo..., vì hôm nay mình đã mang đến giải pháp đỉnh cao giải quyết triệt để vấn đề rồi đây.", 
          "image_prompt": "Viết PROMPT ẢNH HOÀN TOÀN MỚI có chứa Master Setting.", 
          "video_prompt": "{video_audio_prompt_rule}"
        }},
        {{
          "scene_number": 3, 
          "duration": "8s", 
          "scene_setting": "Mô tả trải nghiệm và Call-to-action...", 
          "transition_type": "Nối liền mạch (Match Cut)", 
          "voice_director_vn": "{voice_director_rule}", 
          "voiceover_vi": "Mà cái hay nhất là sản phẩm này đang có deal cực hời..., mọi người hãy nhanh tay chốt đơn ngay kẻo lỡ nhé!", 
          "image_prompt": "Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu cho video", 
          "video_prompt": "{video_audio_prompt_rule}"
        }}
      ]
    }}
    LƯU Ý CỰC KỲ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG DÙNG DẤU NGOẶC KÉP HOẶC DẤU XUỐNG DÒNG (\\n) BÊN TRONG CÁC GIÁ TRỊ STRING CỦA JSON.
    """
    sys_inst = get_system_instructions(current_mode, selected_style, aspect_ratio, goal, target_duration_mins, char_rules_str, st.session_state.narrator_mode)
    res = call_gemini_api([prompt_detail], sys_inst)
    if isinstance(res, list): res = res[0]
    st.session_state.generated_details[target_id] = res

def clone_script_id(target_id, current_mode, current_style, aspect_ratio, goal, target_duration_mins):
    target_script = st.session_state.generated_details[target_id]
    all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    cur_len = len(all_sources)
    is_sales_mode = "Bán Hàng" in current_mode
    char_rules_str = generate_char_rules_string(st.session_state.get("character_profiles", []), is_sales_mode)
    
    p_clone = f"Dựa trên kịch bản: {json.dumps(target_script, ensure_ascii=False)}. Tạo đúng 5 biến thể mới (id từ {cur_len+1} đến {cur_len+5}). Xuất JSON key 'cloned_outlines'. LƯU Ý: TUYỆT ĐỐI KHÔNG DÙNG DẤU NGOẶC KÉP CHƯA ESCAPE HOẶC DẤU XUỐNG DÒNG BÊN TRONG JSON VALUE."
    sys_inst = get_system_instructions(current_mode, selected_style, aspect_ratio, goal, target_duration_mins, char_rules_str, st.session_state.narrator_mode)
    res_c = call_gemini_api([p_clone], sys_inst)
    cloned_list = res_c.get("cloned_outlines", [])
    for idx_c, cl in enumerate(cloned_list): cl["id"] = cur_len + idx_c + 1
    st.session_state.cloned_scripts.extend(cloned_list)

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

allowed_modules = ALL_MODULES
user_email = st.session_state.get("current_user_email", "")
if user_email and user_email != ADMIN_EMAIL:
    user_roles = st.session_state.licensed_accounts.get(user_email, {}).get("roles", [])
    if "Tất cả thể loại" not in user_roles:
        allowed_modules = [m for m in ALL_MODULES if m in user_roles]
        if not allowed_modules: 
            allowed_modules = [ALL_MODULES[0]]

col_mode, col_style = st.columns([1.5, 1])
with col_mode:
    selected_mode = st.selectbox("🎯 Chọn Thể Loại Nội Dung:", options=allowed_modules)

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

st.session_state.narrator_mode = st.selectbox(
    "🎙️ Lựa chọn loại hình thuyết minh cho Video:",
    options=[
        "Nhân vật xuất hiện nói chuyện (On-camera)",
        "🎙️ Lồng tiếng ngoài chuyên nghiệp (Off-screen Narrator / B-roll Phóng sự)"
    ],
    index=0
)

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
            try:
                create_scene_details_for_id(int(param), selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins)
                st.session_state.active_script_id = int(param)
                st.session_state.global_toast = f"Đã dựng thành công chi tiết kịch bản #{param}!"
                st.session_state.global_toast_icon = "✅"
                st.session_state.scroll_to_top = True
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
            time.sleep(0.2)
            st.rerun() 
        
    elif action == "clone_script":
        st.toast(f"⏳ Đang nhân bản biến thể cho kịch bản #{param}...", icon="🧬")
        with st.container(border=True):
            st.markdown(f"<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG XỬ LÝ: Đang nhân bản 5 biến thể độc đáo từ kịch bản #{param}. Vui lòng đợi...</div>", unsafe_allow_html=True)
            try:
                clone_script_id(int(param), selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins)
                st.session_state.global_toast = f"Đã nhân bản thành công kịch bản #{param}!"
                st.session_state.global_toast_icon = "🧬"
                st.session_state.scroll_to_top = True
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
            time.sleep(0.2)
            st.rerun()
        
    elif action == "generate_more":
        st.toast("⏳ Đang suy nghĩ góc tiếp cận mới...", icon="🧠")
        with st.container(border=True):
            st.markdown("<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG XỬ LÝ: Đang phân tích DNA để sáng tạo thêm 5 kịch bản mới. Vui lòng đợi...</div>", unsafe_allow_html=True)
            try:
                add_five_scripts_continuation(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, st.session_state.extra_angle_type, st.session_state.extra_num_chars, st.session_state.extra_duration_mins)
                st.session_state.global_toast = "Đã phân tích DNA và bổ sung thêm kịch bản mới!"
                st.session_state.global_toast_icon = "🧠"
                st.session_state.scroll_to_top = True
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
            time.sleep(0.2)
            st.rerun()
        
    st.stop()

# ==============================================================================
# 4. NẾU KHÔNG CÓ HÀNH ĐỘNG NÀO ĐANG CHẠY (RENDER UI THƯỜNG)
# ==============================================================================

with st.expander("💡 Bấm vào đây để xem Bảng Gợi Ý Phối Hợp 'Thể Loại & Phong Cách'", expanded=False):
    st.markdown("""
    <div style="background-color: #f8fafc; padding: 16px; border-radius: 12px; border: 1.5px solid #e2e8f0; font-size: 0.95rem; color: #334155; margin-bottom: 5px;">
        <h4 style="color: #0f172a; margin-top: 0; margin-bottom: 12px; font-size: 1.05rem;">🎯 Cẩm Nang Phối Hợp Sáng Tạo Nội Dung Đa Vũ Trụ</h4>
        <ul style="padding-left: 20px; line-height: 1.8; margin-bottom: 0;">
            <li><b>🛒 TikTok Shop & Bán Hàng:</b> Phù hợp nhất với <code style="color: #e11d48;">Studio Tối Giản (Hiện đại, Sạch sẽ, Thương mại)</code>.</li>
            <li><b>👶 Mẹ & Bé & Cùng Con Học:</b> Tối ưu với <code style="color: #e11d48;">Hoạt Hình Cắt Giấy / Tĩnh Vật</code> hoặc <code style="color: #e11d48;">Hoạt Hình 3D (Kiểu Pixar / Disney)</code>.</li>
            <li><b>📺 TVC Quảng Cáo & Thương Hiệu Cao Cấp:</b> Cực kỳ tương thích với <code style="color: #e11d48;">Điện Ảnh Chân Thực (Người thật / Siêu thực 8K)</code>.</li>
            <li><b>🏡 Nhà Cửa, Kiến Trúc & Cảnh Quan:</b> Khuyên dùng <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> hoặc <code style="color: #e11d48;">Studio Tối Giản</code>.</li>
            <li><b>🌿 Du Lịch & Phong Cảnh Đất Nước:</b> Rất hợp với <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> hoặc <code style="color: #e11d48;">Tranh Thủy Mặc Cổ Phong (Truyền thống Á Đông)</code>.</li>
            <li><b>🚗 Xe Cộ & Trải Nghiệm Lái:</b> Nên chọn <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> hoặc mang hơi hướng <code style="color: #e11d48;">Phim Cổ Điển Hoài Niệm (Thập niên 80 - 90)</code>.</li>
            <li><b>🍲 Ẩm Thực & Đời Sống:</b> Tôn lên vẻ đẹp món ăn với <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> hoặc <code style="color: #e11d48;">Studio Tối Giản</code>.</li>
            <li><b>📖 Đời Sống & Giáo Dục:</b> Khuyên dùng <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> (nếu có KOC) hoặc <code style="color: #e11d48;">Hoạt Hình 2D (Phong cách Ghibli / Anime Nhật Bản)</code>.</li>
            <li><b>🏛️ Lịch Sử & Tín Ngưỡng Di Sản:</b> Đặc biệt hợp với <code style="color: #e11d48;">Tranh Thủy Mặc Cổ Phong</code> hoặc <code style="color: #e11d48;">Phim Cổ Điển Hoài Niệm</code>.</li>
            <li><b>🧘 Chữa Lành & Phong Cách Sống:</b> Tạo cảm giác nhẹ nhàng với <code style="color: #e11d48;">Hoạt Hình 2D Ghibli</code> hoặc <code style="color: #e11d48;">Trầm Buồn / Kịch Tính (Tông màu tối)</code>.</li>
            <li><b>📢 Tuyên Truyền, Phóng Sự & Thông Điệp Xã Hội:</b> Sử dụng <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> hoặc màu sắc <code style="color: #e11d48;">Trầm Buồn / Kịch Tính</code>.</li>
            <li><b>🏢 Giới Thiệu Doanh Nghiệp & Hồ Sơ Năng Lực:</b> Thể hiện sự chuyên nghiệp bằng <code style="color: #e11d48;">Điện Ảnh Chân Thực (8K)</code> hoặc <code style="color: #e11d48;">Studio Tối Giản (Thương mại)</code>.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

if is_sales:
    st.info("💡 **Chế độ Bán Hàng Shoppertainment:** Kịch bản xây dựng dựa trên cấu trúc Problem (Nỗi đau) -> Solution (Giải pháp) -> CTA chốt đơn. An toàn chính sách tuyệt đối.")
else:
    st.info(f"⏱️ **Thời lượng mong muốn:** {target_duration_mins} phút")

st.markdown("---")
input_text = st.text_area("✍️ Tóm tắt ý tưởng, chủ đề hoặc mô tả chi tiết dự án/sản phẩm (Ghi chú rõ thứ tự các ảnh nếu tải nhiều ảnh nhân vật):", height=80, key="main_input_context")

st.markdown("### 👥 Quản Lý Nguồn Ảnh & Tuyển Diễn Viên (Casting)")
col_p_img, col_c_img = st.columns([1, 1])

with col_p_img:
    st.markdown("**1. 📦 Tải ảnh Sản phẩm / Bối cảnh chính**")
    uploaded_files = st.file_uploader("Chọn nhiều ảnh sản phẩm", type=["jpg", "jpeg", "png"], accept_multiple_files=True, label_visibility="collapsed", key=f"main_uploader_{st.session_state.file_uploader_key}")

with col_c_img:
    st.markdown("**2. 👤 Số lượng Nhân vật KOC/Gia đình tham chiếu**")
    num_chars = st.number_input("Chọn từ 0 đến 8 nhân vật:", min_value=0, max_value=8, step=1, key="num_chars_input")

char_inputs = []
if num_chars > 0:
    with st.expander(f"🎭 HỒ SƠ DIỄN VIÊN ({num_chars} Nhân vật) - Kéo thả ảnh và Nhập vai trò", expanded=True):
        n_cols = 4 if num_chars > 2 else 2
        grid_cols = st.columns(n_cols)
        for i in range(num_chars):
            with grid_cols[i % n_cols]:
                with st.container(border=True):
                    st.markdown(f"<div style='color:#d90429; font-weight:800; font-size:14px; margin-bottom:5px;'>👤 Diễn viên {i+1}</div>", unsafe_allow_html=True)
                    c_role = st.text_input("Vai trò", key=f"c_role_{i}_{st.session_state.file_uploader_key}", placeholder="Vd: Mẹ 30 tuổi...", label_visibility="collapsed")
                    c_file = st.file_uploader("Ảnh", type=["jpg", "jpeg", "png"], key=f"c_img_{i}_{st.session_state.file_uploader_key}", label_visibility="collapsed")
                    if c_file and c_role.strip():
                        char_inputs.append({"id": i+1, "role": c_role.strip(), "file": c_file})

# Xử lý Logic Phân tích chính
if st.button("🚀 Bắt Đầu Phân Tích Chi Tiết & Kịch Bản", type="primary", use_container_width=True, disabled=not (input_text.strip() or uploaded_files or char_inputs)):
    st.toast("⏳ Đang kết nối phân tích DNA... Vui lòng đợi trong giây lát!", icon="🤖")
    with st.spinner("⏳ Đang phân tích DNA chuyên sâu và Gán vai diễn viên..."):
        try:
            profiles_to_save = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
            st.session_state.character_profiles = profiles_to_save
            
            st.session_state.current_input_context = input_text.strip() if input_text else "Phân tích trực tiếp từ hình ảnh đính kèm sản phẩm/dự án."
            safe_input_context = st.session_state.current_input_context.replace('"', "'").replace('\n', ' ')
            
            char_rules_str = generate_char_rules_string(profiles_to_save, is_sales)
            realtime_ctx = get_realtime_context()
            
            if is_sales:
                tone_suggestion = "Năng lượng cao, chốt sale"
                specific_rules = """
                1. Về Giá cả: TUYỆT ĐỐI KHÔNG ĐƯA MỨC GIÁ CỤ THỂ BẰNG CON SỐ. Chỉ sử dụng: "giá tận xưởng", "deal hời giới hạn".
                2. CHIẾN LƯỢC KỊCH BẢN (PAS & SHOPPERTAINMENT): Phân bổ 5 kịch bản theo công thức Problem -> Solution -> CTA.
                3. ĐỊNH VỊ TỆP KHÁCH HÀNG: Bắt buộc kịch bản phải xoay quanh tệp khách hàng có NHU CẦU CAO NHẤT.
                4. BỘ LỌC CHÍNH SÁCH TUYỆT ĐỐI: Không từ đe dọa, không cam kết 100%, không số lượng tồn kho ảo, không từ điều hướng như livestream.
                """
            elif is_knowledge:
                tone_suggestion = "Nhanh, dứt khoát, lôi cuốn, chuyên nghiệp"
                specific_rules = "1. VÀO THẲNG VẤN ĐỀ: Bỏ qua hoàn toàn đoạn chào hỏi dài dòng."
            elif is_story:
                tone_suggestion = "Truyền cảm, nhấn nhá theo mạch cảm xúc"
                specific_rules = "1. KỂ CHUYỆN: Xây dựng cao trào, thắt mở nút rõ ràng."
            elif is_corporate:
                tone_suggestion = "Đĩnh đạc, chuyên nghiệp, đáng tin cậy"
                specific_rules = "1. THÔNG ĐIỆP TỔ CHỨC: Thể hiện sự chuyên nghiệp, uy tín."
            else:
                tone_suggestion = "Tự nhiên, lôi cuốn, tương tác cao"
                specific_rules = "1. NỘI DUNG VIRAL: Hook cực mạnh ở 3 giây đầu."

            script_outlines_json = f"""
              "script_outlines": [
                {{
                  "id": 1,
                  "title": "Tên kịch bản 1 (Tình huống đời sống & Nỗi đau PAS)",
                  "setting_style": "Mô tả bối cảnh không gian cố định",
                  "script_outfit_setup": "Mô tả trang phục toàn diện bao gồm Áo, Quần/Váy và Giày (BẮT BUỘC CHỈ ĐỊNH RÕ MÀU SẮC)",
                  "angle": "Góc tiếp cận",
                  "target_hook": "Câu mở đầu mạnh mẽ, thu hút",
                  "recommended_scenes_count": "Tự động phân bổ linh hoạt",
                  "voice_profile": {{"gender": "Nữ", "age_range": "25-35", "tone": "{tone_suggestion}"}}
                }},
                {{
                  "id": 2,
                  "title": "Tên kịch bản 2 (Giải pháp đột phá & Trải nghiệm)",
                  "setting_style": "Mô tả bối cảnh không gian cố định",
                  "script_outfit_setup": "Mô tả trang phục toàn diện (BẮT BUỘC CHỈ ĐỊNH RÕ MÀU SẮC)",
                  "angle": "Góc tiếp cận",
                  "target_hook": "Câu mở đầu",
                  "recommended_scenes_count": "Tự động phân bổ linh hoạt",
                  "voice_profile": {{"gender": "Nam", "age_range": "25-35", "tone": "{tone_suggestion}"}}
                }},
                {{
                  "id": 3,
                  "title": "Tên kịch bản 3 (Review bóc trần / Thử thách)",
                  "setting_style": "Mô tả bối cảnh không gian cố định",
                  "script_outfit_setup": "Mô tả trang phục toàn diện (BẮT BUỘC CHỈ ĐỊNH RÕ MÀU SẮC)",
                  "angle": "Góc tiếp cận",
                  "target_hook": "Câu mở đầu",
                  "recommended_scenes_count": "Tự động phân bổ linh hoạt",
                  "voice_profile": {{"gender": "Nữ", "age_range": "25-35", "tone": "{tone_suggestion}"}}
                }},
                {{
                  "id": 4,
                  "title": "Tên kịch bản 4 (Tình huống hài hước / Plot Twist)",
                  "setting_style": "Mô tả bối cảnh không gian cố định",
                  "script_outfit_setup": "Mô tả trang phục toàn diện (BẮT BUỘC CHỈ ĐỊNH RÕ MÀU SẮC)",
                  "angle": "Góc tiếp cận",
                  "target_hook": "Câu mở đầu",
                  "recommended_scenes_count": "Tự động phân bổ linh hoạt",
                  "voice_profile": {{"gender": "Nam", "age_range": "25-35", "tone": "{tone_suggestion}"}}
                }},
                {{
                  "id": 5,
                  "title": "Tên kịch bản 5 (Flash Sale & Deal hời giới hạn)",
                  "setting_style": "Mô tả bối cảnh không gian cố định",
                  "script_outfit_setup": "Mô tả trang phục toàn diện (BẮT BUỘC CHỈ ĐỊNH RÕ MÀU SẮC)",
                  "angle": "Góc tiếp cận",
                  "target_hook": "Câu mở đầu",
                  "recommended_scenes_count": "Tự động phân bổ linh hoạt",
                  "voice_profile": {{"gender": "Nữ", "age_range": "25-35", "tone": "{tone_suggestion}"}}
                }}
              ]
            """
            
            prompt_text = f"""
            Phân tích siêu chuyên sâu chủ đề cho thể loại '{selected_mode}' theo phong cách '{selected_style}'. 
            Thông tin mô tả: "{safe_input_context}"
            {realtime_ctx}

            QUY ĐỊNH ĐỘNG VỀ NHẬN DIỆN:
            {specific_rules}

            BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON CHUẨN GỒM CÁC KEY SAU:
            {{
              "content_analysis": {{
                "primary_target_audience": "Nhận diện TỆP KHÁCH HÀNG CÓ NHU CẦU MUA CAO NHẤT.",
                "mechanical_and_accessories": "Phân tích CHÍNH XÁC KIỂU DÁNG, CHẤT LIỆU VÀ MÀU SẮC THỰC TẾ TỪ ẢNH.",
                "customer_pain_points": "Phân tích 3 tầng nỗi đau.",
                "core_desires": "Mong muốn cốt lõi.",
                "emotional_or_usp_hook": "Slogan, USP độc quyền.",
                "visual_physics_rules": "Quy chuẩn vật lý khi chuyển động.",
                "prompt_dna_lock": "Chuỗi khóa thị giác đồng bộ toàn bộ video."
              }},
              {script_outlines_json}
            }}
            LƯU Ý: TUYỆT ĐỐI KHÔNG DÙNG DẤU NGOẶC KÉP BÊN TRONG GIÁ TRỊ STRING CỦA JSON.
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
            
            sys_inst = get_system_instructions(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, char_rules_str, st.session_state.narrator_mode)
            res = call_gemini_api(payload, sys_inst)
            
            st.session_state.content_analysis = res.get("content_analysis")
            st.session_state.all_scripts = res.get("script_outlines", [])
            st.session_state.cloned_scripts, st.session_state.expanded_scripts, st.session_state.generated_details, st.session_state.active_script_id = [], [], {}, None
            st.session_state.scroll_to_top = True
            
            st.session_state.global_toast = "Đã phân tích DNA và khởi tạo dự án thành công!"
            st.session_state.global_toast_icon = "✅"
            time.sleep(0.1)
            st.rerun()
        except Exception as e:
            st.error(f"❌ Lỗi thực thi: {e}")

if st.session_state.content_analysis and isinstance(st.session_state.content_analysis, dict) and not st.session_state.action_trigger:
    st.divider()
    st.markdown(f"### 🔍 **Phân Tích DNA Chi Tiết Đa Tầng — [{selected_mode.upper()}]**")
    ca = st.session_state.content_analysis
    with st.container(border=True):
        st.markdown("##### 🎯 **1. Chân dung Khách hàng & Nỗi đau:**")
        st.markdown(f"<div style='line-height: 1.8;'>• <b>Tệp khách hàng mục tiêu:</b> {format_analysis_field(ca.get('primary_target_audience', 'N/A'))}<br>{format_analysis_field(ca.get('customer_pain_points', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 🏭 **2. Thông số Cốt lõi:**")
        st.markdown(f"<div style='line-height: 1.8;'>{format_analysis_field(ca.get('mechanical_and_accessories', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("##### 💡 **3. Mong muốn cốt lõi & USP:**")
        st.markdown(f"<div style='line-height: 1.8;'>• <b>Mong muốn:</b> {format_analysis_field(ca.get('core_desires', 'N/A'))}<br>• <b>USP:</b> {format_analysis_field(ca.get('emotional_or_usp_hook', 'N/A'))}</div>", unsafe_allow_html=True)
    st.markdown("##### 📌 **Chuỗi khóa thị giác (Visual DNA Lock):**")
    raw_dna = str(ca.get('prompt_dna_lock', 'N/A')).replace('<br>', ' ').replace('<b>', '').replace('</b>', '')
    st.code(raw_dna, language="text")

# ==============================================================================
# GIAI ĐOẠN 1: CHIA 2 VÙNG ĐỘC LẬP CHO DANH SÁCH KỊCH BẢN
# ==============================================================================
all_combined_scripts_list = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts

if all_combined_scripts_list and st.session_state.active_script_id is None and not st.session_state.action_trigger:
    st.divider()
    
    completed_scripts = []
    pending_scripts = []
    for sc in all_combined_scripts_list:
        sc_id = int(sc.get("id", 0))
        if sc_id in st.session_state.generated_details:
            completed_scripts.append(sc)
        else:
            pending_scripts.append(sc)

    st.markdown("### 🎬 **1. Kịch Bản Đã Hoàn Thiện Chi Tiết (Sẵn Sàng Sản Xuất & Nhân Bản)**")
    if not completed_scripts:
        st.info("💡 Chưa có kịch bản nào được tạo chi tiết.")
    else:
        for outline in completed_scripts:
            sc_id = int(outline.get("id", 0))
            with st.container(border=True):
                col_i1, col_btn1, col_btn2 = st.columns([2.5, 1, 1])
                with col_i1:
                    st.markdown(f"**#{sc_id}. {outline.get('title')}** — <span class='badge-ready'>ĐÃ HOÀN THIỆN</span>", unsafe_allow_html=True)
                    st.caption(f"🏛️ Bối cảnh: {outline.get('setting_style')} | ⚡ Hook: *\"{outline.get('target_hook')}\"*")
                with col_btn1:
                    if st.button("👁️ Xem lại chi tiết", key=f"btn_rev_v1_main_{sc_id}", use_container_width=True):
                        st.session_state.active_script_id = sc_id
                        st.session_state.scroll_to_top = True
                        st.session_state.global_toast = f"Đang xem chi tiết kịch bản #{sc_id}"
                        st.session_state.global_toast_icon = "👁️"
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
            sc_id = int(outline.get("id", 0))
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
    
    # Giao diện tùy chọn Thể loại, Số lượng nhân vật & Thời lượng khi gọi thêm kịch bản mới
    with st.container(border=True):
        st.markdown("##### ➕ **Tùy Chỉnh & Gọi Thêm Kịch Bản Mới Theo Thể Loại, Nhân Vật & Thời Lượng**")
        col_g1, col_g2, col_g3 = st.columns([2, 1, 1])
        with col_g1:
            st.session_state.extra_angle_type = st.selectbox(
                "Chọn định hướng chiến lược cho 5 kịch bản gọi thêm:",
                options=[
                    "⚡ Dạng Flash Sale & Deal hời (Tập trung chốt đơn)",
                    "🎭 Dạng Tình huống đời sống / Nỗi đau (PAS)",
                    "🔍 Dạng Review thực chiến & Thử thách độ bền",
                    "💡 Dạng Mẹo vặt / Chia sẻ kiến thức hữu ích",
                    "😂 Dạng Tình huống hài hước / Bẻ lái (Plot Twist)"
                ],
                key="extra_angle_selectbox_main"
            )
        with col_g2:
            st.session_state.extra_num_chars = st.number_input(
                "Số lượng nhân vật:",
                min_value=1, max_value=4, value=1, step=1,
                key="extra_num_chars_main",
                help="Chọn 2 trở lên để AI viết kịch bản dạng tương tác đối thoại."
            )
        with col_g3:
            st.session_state.extra_duration_mins = st.number_input(
                "Thời lượng (Phút):",
                min_value=0.5, max_value=5.0, value=1.0, step=0.5,
                key="extra_duration_mins_main",
                help="Chọn thời lượng tổng cộng cho kịch bản."
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Gọi Thêm 5 Kịch Bản Theo Định Hướng Này", key="btn_add_more_1_main", type="primary", use_container_width=True):
            st.session_state.action_trigger = "generate_more"
            st.rerun()

# ==============================================================================
# GIAI ĐOẠN 2: CHI TIẾT KỊCH BẢN & GIAO DIỆN CHIA ĐÔI MÀN HÌNH (SPLIT-SCREEN)
# ==============================================================================
if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details and not st.session_state.action_trigger:
    st.divider()

    if st.button("⬅️ Quay lại danh sách kịch bản tổng", key="btn_back_to_list_main"):
        st.session_state.active_script_id = None
        st.session_state.scroll_to_top = True
        st.session_state.global_toast = "Đã quay lại danh sách kịch bản!"
        st.session_state.global_toast_icon = "⬅️"
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
        vp = {"gender": "Nữ", "age_range": "25-30", "tone": "Truyền cảm"}

    script_title = active_script.get('title', 'Kịch bản chi tiết') if isinstance(active_script, dict) else 'Kịch bản chi tiết'
    total_dur = active_script.get('total_estimated_duration', '24s') if isinstance(active_script, dict) else '24s'
    outfit_setup_text = active_script.get('script_outfit_setup', 'Đồng phục bối cảnh')

    st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(script_title).upper()}**")
    st.info(f"⏱️️ Thời lượng: **{total_dur}** | 🎙️ Giọng: **{vp.get('gender', 'Nữ')} ({vp.get('tone', 'Truyền cảm')})** | 👔 Trang phục toàn diện: **{outfit_setup_text}** | 📐 Khung hình: **{selected_aspect}**")

    # BẢNG ĐIỀU PHỐI SẢN XUẤT HÀNG LOẠT (BATCH PRODUCTION)
    with st.container(border=True):
        st.markdown("##### ⚡ **Bảng Điều Phối Sản Xuất Hàng Loạt Trực Tiếp (API Studio)**")
        scenes_list = active_script.get("scenes", []) if isinstance(active_script, dict) else []
        if isinstance(scenes_list, dict): scenes_list = [scenes_list]

        if st.button("🚀 Render Hàng Loạt Tất Cả Ảnh (-5 Credits)", key="btn_batch_img_top", type="primary", use_container_width=True):
            user_email_curr = st.session_state.current_user_email
            valid_scenes_count = sum(1 for sc in scenes_list if sc.get('image_prompt') and "dùng ảnh cuối của cảnh trước" not in sc.get('image_prompt', '').lower())
            
            if deduct_user_credit(user_email_curr, amount=valid_scenes_count):
                progress_bar = st.progress(0)
                total_sc = len(scenes_list)
                for idx_b, sc_b in enumerate(scenes_list, start=1):
                    img_p_b = sc_b.get('image_prompt', '')
                    if img_p_b and "dùng ảnh cuối của cảnh trước" not in img_p_b.lower():
                        img_bytes_b = generate_image_with_imagen(img_p_b, selected_aspect)
                        if img_bytes_b:
                            st.session_state[f"img_bytes_{st.session_state.active_script_id}_{idx_b}"] = img_bytes_b
                    progress_bar.progress(idx_b / total_sc)
                st.success(f"✅ Đã hoàn tất render hàng loạt ảnh (-{valid_scenes_count} Credits)!")
                time.sleep(0.3)
                st.rerun()
            else:
                st.error("❌ Tài khoản của bạn không đủ credit để thực hiện render hàng loạt!")

    # HIỂN THỊ CÁC PHÂN CẢNH THEO GIAO DIỆN CHIA ĐÔI MÀN HÌNH (SPLIT-SCREEN)
    for idx, scene in enumerate(scenes_list, start=1):
        if not isinstance(scene, dict): continue
        dur = scene.get("duration", "6s")
        st.markdown(f"#### **📍 Phân cảnh {idx} ({dur}) — [ {scene.get('transition_type', 'Cắt cứng dồn dập')} ]**")
        
        # Chia đôi màn hình: Cột trái (Kịch bản & Sửa Voiceover), Cột phải (Media Workspace)
        col_script, col_media = st.columns([1, 1], gap="medium")
        
        with col_script:
            with st.container(border=True):
                st.markdown(f"<b style='color: #d90429;'>📝 Kịch bản & Tinh chỉnh Voiceover Cảnh {idx}</b>", unsafe_allow_html=True)
                st.markdown(f"🏛️ **Bối cảnh:** *{scene.get('scene_setting')}*")
                st.markdown(f"**🎙️ Ngữ điệu & SFX:** *{scene.get('voice_director_vn')}*")
                
                # --- CHO PHÉP CHỈNH SỬA TRỰC TIẾP LỜI THOẠI (VOICEOVER) ---
                current_vo_key = f"vo_text_{st.session_state.active_script_id}_{idx}"
                if current_vo_key not in st.session_state:
                    st.session_state[current_vo_key] = scene.get('voiceover_vi', '')
                
                edited_voiceover = st.text_area(
                    "💬 Chỉnh sửa lời thoại (Voiceover):",
                    value=st.session_state[current_vo_key],
                    key=f"input_vo_{st.session_state.active_script_id}_{idx}",
                    height=70,
                    help="Bạn có thể sửa lại câu từ, dấu ngắt nghỉ hoặc tiếng địa phương trực tiếp tại đây trước khi mang đi lồng tiếng."
                )
                st.session_state[current_vo_key] = edited_voiceover
                
                img_p = scene.get('image_prompt', '')
                if img_p:
                    st.markdown(f"**🖼️ Prompt Ảnh (Imagen 3):**")
                    if "dùng ảnh cuối của cảnh trước" in img_p.lower() or "dùng frame ảnh cuối" in img_p.lower():
                        st.info("🔗 Dùng frame cuối của cảnh trước (Match Cut).")
                    else:
                        st.code(img_p, language="text")
                        safe_copy_button(img_p, f"📋 Sao Chép Prompt Ảnh {idx}")
                
                vid_p = scene.get('video_prompt', '')
                st.markdown(f"**🎥 Prompt Video (Veo 3):**")
                st.code(vid_p, language="text")
                safe_copy_button(vid_p, f"📋 Sao Chép Prompt Video {idx}")

        with col_media:
            with st.container(border=True):
                st.markdown(f"<b style='color: #166534;'>🎬 Không Gian Sản Xuất Media Cảnh {idx}</b>", unsafe_allow_html=True)
                
                # 1. Phần tạo Ảnh trực tiếp
                img_p = scene.get('image_prompt', '')
                img_key = f"img_bytes_{st.session_state.active_script_id}_{idx}"
                
                if img_p and "dùng ảnh cuối của cảnh trước" not in img_p.lower():
                    if st.button(f"🎨 [API] Tạo Ảnh Ngay (-1 Credit)", key=f"btn_gen_img_{idx}"):
                        user_email_curr = st.session_state.current_user_email
                        if deduct_user_credit(user_email_curr, amount=1):
                            with st.spinner("⏳ Đang kết nối Imagen 3 để vẽ ảnh..."):
                                img_bytes = generate_image_with_imagen(img_p, selected_aspect)
                                if img_bytes:
                                    st.session_state[img_key] = img_bytes
                                    st.success("✅ Đã tạo ảnh thành công (-1 Credit)!")
                                    st.rerun()
                        else:
                            st.error("❌ Bạn đã hết credit!")
                
                # Hiển thị ảnh nếu có
                if img_key in st.session_state:
                    st.image(st.session_state[img_key], caption=f"Ảnh kết xuất Cảnh {idx}", use_column_width=True)

                st.markdown("---")

                # 2. Phần tạo Video trực tiếp
                vid_key = f"vid_bytes_{st.session_state.active_script_id}_{idx}"
                img_key_ref = f"img_bytes_{st.session_state.active_script_id}_{idx}"
                
                if st.button(f"🎬 [API] Tạo Video Veo Ngay (-3 Credits)", key=f"btn_gen_vid_{idx}", type="primary"):
                    source_img = st.session_state.get(img_key_ref)
                    if not source_img and idx > 1:
                        prev_img_key = f"img_bytes_{st.session_state.active_script_id}_{idx-1}"
                        source_img = st.session_state.get(prev_img_key)
                        
                    if source_img:
                        user_email_curr = st.session_state.current_user_email
                        if deduct_user_credit(user_email_curr, amount=3):
                            with st.spinner("⏳ Đang kết nối Veo 3 để dựng video (1-2 phút)..."):
                                vid_bytes = generate_video_with_veo(source_img, vid_p)
                                if vid_bytes:
                                    st.session_state[vid_key] = vid_bytes
                                    st.success("✅ Đã render video thành công (-3 Credits)!")
                                    st.rerun()
                        else:
                            st.error("❌ Không đủ credit (Cần 3 credits)!")
                    else:
                        st.warning("⚠️ Vui lòng tạo ảnh cho cảnh này trước!")
                
                # Hiển thị video nếu có
                if vid_key in st.session_state:
                    st.video(st.session_state[vid_key])
                    st.download_button(
                        label=f"📥 Tải Video Cảnh {idx} (.mp4)",
                        data=st.session_state[vid_key],
                        file_name=f"scene_{idx}_veo3.mp4",
                        mime="video/mp4",
                        key=f"dl_vid_{idx}"
                    )

        st.markdown("---")

    col_left, col_right = st.columns([1.1, 0.9])
    
    with col_left:
        st.markdown("""
        <div class="custom-card" style="background: #f0fdf4; border-color: #86efac;">
            <div style="color: #166534; font-weight: 800; font-size: 1.1rem; margin-bottom: 4px;">🎬 Kịch Bản Đã Hoàn Thiện</div>
            <div style="font-size: 0.82rem; color: #15803d;">Chọn để xem lại hoặc nhân bản nhanh</div>
        </div>
        """, unsafe_allow_html=True)
        
        completed_scripts_in_detail = []
        for sc in all_combined_scripts_list:
            sc_id = int(sc.get("id", 0))
            if sc_id in st.session_state.generated_details:
                completed_scripts_in_detail.append(sc)
                
        if not completed_scripts_in_detail:
            st.caption("Chưa có kịch bản nào khác được tạo.")
        else:
            for item in completed_scripts_in_detail:
                it_id = int(item.get("id", 0))
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
                                st.session_state.global_toast = f"Đang hiển thị kịch bản #{it_id}"
                                st.session_state.global_toast_icon = "👁️"
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

        st.session_state.extra_angle_type = st.selectbox(
            "Chọn thể loại kịch bản gọi thêm:",
            options=[
                "⚡ Dạng Flash Sale & Deal hời (Tập trung chốt đơn)",
                "🎭 Dạng Tình huống đời sống / Nỗi đau (PAS)",
                "🔍 Dạng Review thực chiến & Thử thách độ bền",
                "💡 Dạng Mẹo vặt / Chia sẻ kiến thức hữu ích",
                "😂 Dạng Tình huống hài hước / Bẻ lái (Plot Twist)"
            ],
            key="extra_angle_selectbox_detail"
        )
        st.session_state.extra_num_chars = st.number_input(
            "Số lượng nhân vật tham gia:",
            min_value=1, max_value=4, value=1, step=1,
            key="extra_num_chars_detail"
        )
        st.session_state.extra_duration_mins = st.number_input(
            "Thời lượng mong muốn (Phút):",
            min_value=0.5, max_value=5.0, value=1.0, step=0.5,
            key="extra_duration_mins_detail"
        )
        if st.button("🚀 Gọi Thêm 5 Tình Huống Kịch Bản Mới", key="btn_add_more_phase2_detail", type="primary", use_container_width=True):
            st.session_state.action_trigger = "generate_more"
            st.rerun()

    with col_right:
        st.markdown("""
        <div class="custom-card" style="background: #f8fafc;">
            <div style="color: #0f172a; font-weight: 800; font-size: 1.1rem; margin-bottom: 10px;">📋 Kịch Bản Chưa Tạo Chi Tiết</div>
        </div>
        """, unsafe_allow_html=True)

        pending_scripts = []
        for item in all_combined_scripts_list:
            if int(item.get("id", 0)) not in st.session_state.generated_details:
                pending_scripts.append(item)

        if not pending_scripts:
            st.success("🎉 Tuyệt vời! Tất cả các kịch bản trong danh sách đã được tạo chi tiết thành công.")
        else:
            for item in pending_scripts:
                it_id = int(item.get("id", 0))
                with st.container(border=True):
                    st.markdown(f"**#{it_id}. {item.get('title')}** — <span class='badge-pending'>CHƯA TẠO</span>", unsafe_allow_html=True)
                    st.caption(f"🏛️ {item.get('setting_style')}")
                    if st.button("✨ Tạo chi tiết ngay", key=f"nav_sc_detail_{it_id}", use_container_width=True):
                        st.session_state.action_trigger = "create_detail"
                        st.session_state.action_param = it_id
                        st.rerun()
