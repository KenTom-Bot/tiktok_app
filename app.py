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
    .badge-dynamic { color: #1e40af; font-weight: 700; background: #dbeafe; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
    
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
    st.error("Chưa cấu hình khóa GEMINI_API_KEY trong phần cấu hình bảo mật (Secrets).")
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
for key, default_val in [
    ("content_analysis", None), ("all_scripts", []), ("cloned_scripts", []), 
    ("expanded_scripts", []), ("generated_details", {}), ("active_script_id", None), 
    ("projects_library", {}), ("licensed_accounts", load_licensed_accounts()), 
    ("current_input_context", ""), ("admin_toast_msg", ""), ("is_logged_in", False),
    ("current_user_email", "")
]:
    if key not in st.session_state:
        st.session_state[key] = default_val

if ADMIN_EMAIL not in st.session_state.licensed_accounts:
    st.session_state.licensed_accounts[ADMIN_EMAIL] = {
        "contact": ADMIN_EMAIL, "roles": ["Tất cả thể loại"], "expires_at": "2099-12-31"
    }
    save_licensed_accounts(st.session_state.licensed_accounts)

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

# ==============================================================================
# SIDEBAR - ĐĂNG NHẬP, QUẢN TRỊ & QUẢN LÝ DỰ ÁN ĐẦY ĐỦ
# ==============================================================================
with st.sidebar:
    st.markdown("### 🔐 **Đăng Nhập Hệ Thống**")
    if not st.session_state.is_logged_in:
        with st.form("login_form"):
            login_input = st.text_input("Nhập Email / SĐT:", placeholder="vd: user@gmail.com")
            if st.form_submit_button("🔑 Đăng Nhập", use_container_width=True):
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
        st.markdown("### ⚙️ **Quản Lý Tài Khoản (Quản Trị)**")
        if st.session_state.admin_toast_msg:
            st.success(st.session_state.admin_toast_msg)
            st.session_state.admin_toast_msg = ""

        with st.form("add_license_form"):
            st.markdown("<b>➕ Cấp Quyền Tài Khoản Mới</b>", unsafe_allow_html=True)
            new_account_id = st.text_input("Email / SĐT khách hàng:")
            assigned_modules = st.multiselect("Phân quyền chức năng:", options=[
                "🛒 TikTok Shop & Bán Hàng", "👶 Mẹ & Bé & Cùng Con Học", "📺 TVC Quảng Cáo & Thương Hiệu",
                "🏡 Nhà Cửa & Kiến Trúc", "🌿 Du Lịch & Phong Cảnh", "🚗 Xe Cộ & Trải Nghiệm Lái",
                "🍲 Ẩm Thực & Đời Sống", "📖 Đời Sống & Giáo Dục", "🏛️ Lịch Sử & Tín Ngưỡng Di Sản", "🧘 Chữa Lành & Lifestyle"
            ], default=["🛒 TikTok Shop & Bán Hàng"])
            duration_option = st.selectbox("Thời hạn:", options=["Dùng thử 3 ngày", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm", "2 Năm", "3 Năm", "5 Năm", "10 Năm", "Vĩnh viễn (Trọn đời)"], index=0)
            
            if st.form_submit_button("💾 Lưu / Cấp Quyền Mới", use_container_width=True):
                if new_account_id.strip():
                    if "Vĩnh viễn" in duration_option:
                        expiry_date = "2099-12-31"
                    elif "Dùng thử" in duration_option:
                        expiry_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                    else:
                        month_map = {"1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365, "2 Năm": 730, "3 Năm": 1095, "5 Năm": 1825, "10 Năm": 3650}
                        days_add = month_map.get(duration_option, 30)
                        expiry_date = (datetime.now() + timedelta(days=days_add)).strftime("%Y-%m-%d")

                    st.session_state.licensed_accounts[new_account_id.strip()] = {
                        "contact": new_account_id.strip(), "roles": assigned_modules, "expires_at": expiry_date
                    }
                    save_licensed_accounts(st.session_state.licensed_accounts)
                    st.session_state.admin_toast_msg = f"✅ Đã cấp quyền thành công cho tài khoản: {new_account_id.strip()}!"
                    st.rerun()

        if st.session_state.licensed_accounts:
            with st.expander(f"📋 Danh sách tài khoản đã cấp ({len(st.session_state.licensed_accounts)})"):
                for acc, info in list(st.session_state.licensed_accounts.items()):
                    st.markdown(f"**👤 {acc}**")
                    st.caption(f"• Quyền: {', '.join(info.get('roles', []))}<br>• Hết hạn: {info.get('expires_at')}", unsafe_allow_html=True)
                    if acc != ADMIN_EMAIL:
                        if st.button(f"🗑️ Xóa {acc}", key=f"del_acc_{acc}"):
                            del st.session_state.licensed_accounts[acc]
                            save_licensed_accounts(st.session_state.licensed_accounts)
                            st.session_state.admin_toast_msg = f"Đã xóa tài khoản {acc}!"
                            st.rerun()
                    st.markdown("---")

    if st.session_state.is_logged_in:
        st.markdown("---")
        st.markdown("### 🗂️ **Quản Lý Dự Án**")
        project_title_input = st.text_input("Tên dự án hiện tại:", value=st.session_state.get("active_project_title", "Chiến dịch mới"))
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("💾 Lưu Dự Án", use_container_width=True):
                if st.session_state.all_scripts:
                    p_id = f"proj_{int(time.time())}"
                    st.session_state.projects_library[p_id] = {
                        "title": project_title_input, "mode": st.session_state.get("selected_mode"),
                        "style": st.session_state.get("selected_style"), "content_analysis": st.session_state.content_analysis,
                        "all_scripts": st.session_state.all_scripts, "cloned_scripts": st.session_state.cloned_scripts,
                        "expanded_scripts": st.session_state.expanded_scripts, "generated_details": st.session_state.generated_details
                    }
                    st.success("✅ Đã lưu vào bộ nhớ ứng dụng!")
        with col_p2:
            if st.session_state.all_scripts:
                export_data = {
                    "title": project_title_input, "mode": st.session_state.get("selected_mode"),
                    "style": st.session_state.get("selected_style"), "content_analysis": st.session_state.content_analysis,
                    "all_scripts": st.session_state.all_scripts, "cloned_scripts": st.session_state.cloned_scripts,
                    "expanded_scripts": st.session_state.expanded_scripts, "generated_details": st.session_state.generated_details
                }
                json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
                st.download_button(label="📥 Tải File JSON", data=json_str, file_name=f"{project_title_input.replace(' ', '_')}.json", mime="application/json", use_container_width=True)

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
                st.success("✅ Đã mở dự án thành công!")
                st.rerun()

        st.markdown("<div style='font-size: 0.85rem; color: #64748b; margin-top: 8px;'>Hoặc tải file dự án cũ từ máy tính:</div>", unsafe_allow_html=True)
        uploaded_project_file = st.file_uploader("📤 Chọn file kịch bản (.json)", type=["json"], label_visibility="collapsed")
        if uploaded_project_file is not None:
            try:
                file_bytes = uploaded_project_file.getvalue()
                loaded_proj = json.loads(file_bytes.decode("utf-8"))
                if "all_scripts" in loaded_proj:
                    st.session_state.active_project_title = loaded_proj.get("title", "Dự án tải lên")
                    st.session_state.content_analysis = loaded_proj.get("content_analysis")
                    st.session_state.all_scripts = loaded_proj.get("all_scripts", [])
                    st.session_state.cloned_scripts = loaded_proj.get("cloned_scripts", [])
                    st.session_state.expanded_scripts = loaded_proj.get("expanded_scripts", [])
                    st.session_state.generated_details = {int(k): v for k, v in loaded_proj.get("generated_details", {}).items()}
                    st.success("🎉 Đã khôi phục thành công dự án từ file!")
                    st.rerun()
                else:
                    st.error("❌ Định dạng file JSON không hợp lệ!")
            except Exception as e:
                st.error(f"❌ Lỗi đọc file: {e}")

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

def format_analysis_field(field_val) -> str:
    if isinstance(field_val, dict):
        return "<br>".join([f"• <b>{str(k).replace('_', ' ').title()}:</b> {str(v)}" for k, v in field_val.items()])
    elif isinstance(field_val, list):
        return "<br>".join([f"• {str(item)}" for item in field_val])
    
    text = str(field_val).strip()
    text = re.sub(r'<<\.?', '', text)
    text = text.replace('<b>', '').replace('</b>', '')
    
    lines = text.split('\n')
    processed_lines = []
    for line in lines:
        line_clean = line.strip()
        if not line_clean: continue
        sub_parts = re.split(r'(?=\s*(?:\d+\.|Tông màu|Kích thước|Trọng lượng|Thao tác|Bộ phụ kiện|Chất liệu)\b)', line_clean)
        for part in sub_parts:
            p_clean = part.strip()
            if p_clean: processed_lines.append(p_clean)

    formatted_output = []
    for idx, line in enumerate(processed_lines):
        if idx > 0 or re.match(r'^(\d+[\.\)]|[-•])\s*', line):
            formatted_output.append(f"<div style='margin-left: 15px; margin-top: 6px;'>• {line.lstrip('1234567890. ')}</div>")
        else:
            formatted_output.append(f"<div style='margin-top: 4px;'>{line}</div>")
            
    return "".join(formatted_output) if formatted_output else text

def get_system_instructions(mode: str, style: str, aspect_ratio: str, goal: str, target_duration_mins: float = 0.5) -> str:
    is_sales = ("Bán Hàng" in mode or "Sales" in goal)
    format_instruction = "9:16 vertical video format, mobile-first framing" if aspect_ratio == "9:16" else "16:9 widescreen cinematic format, professional movie framing"
    
    if is_sales:
        duration_rule = "QUY CHUẨN THỜI LƯỢNG BÁN HÀNG (24s - 35s): Phân rã thành 4 đến 6 phân cảnh (4s, 6s, 8s), nhịp độ cực nhanh, tập trung dồn dập vào hook, test thực tế và chốt đơn."
    else:
        total_seconds = int(target_duration_mins * 60)
        duration_rule = f"QUY CHUẨN THỜI LƯỢNG KỂ CHUYỆN / REVIEW DÀI ({target_duration_mins} phút / {total_seconds} giây): Xây dựng cốt truyện có chiều sâu, chia theo cấu trúc Hồi/Chương (Act & Chapter), số lượng phân cảnh trải đều toàn bộ thời lượng."

    outfit_rule = """
    2. QUY CHUẨN TRANG PHỤC CỐ ĐỊNH (SALES OUTFIT LOCK): Nhân vật BẮT BUỘC mặc CÙNG MỘT BỘ TRANG PHỤC cố định xuyên suốt tất cả các cảnh để tối ưu nhận diện thương hiệu và chốt đơn.
    """ if is_sales else """
    2. QUY CHUẨN TRANG PHỤC LINH HOẠT THEO THỜI GIAN/BỐI CẢNH: Nếu kịch bản có mốc thời gian mới (ví dụ: ngày hôm sau, đổi bối cảnh), nhân vật ĐƯỢC PHÉP thay đổi trang phục mới phù hợp, nhưng KHUÔN MẶT và vóc dáng cốt lõi giữ nguyên 100%.
    """

    master_director_directive = "CHẾ ĐỘ CHUYÊN GIA CAO CẤP: Tối ưu hóa sâu sắc các thông số điện ảnh chuyên sâu (Lighting setup, Lens focal length, Color grading, Camera movement physics) cho Imagen 3 và Veo 3 để mọi người dùng dù không biết gì vẫn tạo ra video đạt chuẩn Hollywood."

    base = f"""
BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL ĐA NĂNG CHO IMAGEN 3 VÀ VEO 3.
PHONG CÁCH KẾT XUẤT THỊ GIÁC: {style.upper()}
ĐỊNH DẠNG KHUNG HÌNH: {format_instruction}
MỤC TIÊU CHIẾN DỊCH: {goal}
{duration_rule}
{master_director_directive}

🛑 QUY TẮC BẮT BUỘC 100% (KHÔNG ĐƯỢC VI PHẠM):
1. KHÓA CỨNG KHUÔN MẶT & VÓC DÁNG (IDENTITY ANCHOR): Nhân vật 100% người Việt Nam, biểu cảm chân thực, hình thể chuẩn xác, có mô tả nhận diện riêng và giữ nguyên 100% qua mọi cảnh.
{outfit_rule}
3. MÀN HÌNH SẠCH (ZERO TEXT LOCK): Trong mọi 'image_prompt', bắt buộc cài đặt lệnh chống chữ: 'no text, zero typography, clean screen, no watermarks, no logos'.
4. KHÓA MÀU SẢN PHẨM & VẬT LÝ HÚT/THỔI: Giữ nguyên 100% màu sắc sản phẩm gốc từ ảnh tham chiếu (Anti-Color Shift), mô tả đúng hướng luồng khí hút bụi đi ngược vào đầu vòi và xoáy trực tiếp vào cốc chứa rác trong suốt.
5. CHUYỂN CẢNH THÔNG MINH (SMART TRANSITIONS): 
   - 'Cắt cứng dồn dập (Hard Cut)': Dùng cho hành động nhanh, dồn dập, chốt sale.
   - 'Chuyển cảnh khớp hành động mượt mà (Match Cut)': Dùng để nối tiếp hành động hoặc hình khối uyển chuyển giữa các cảnh.
   - 'Chuyển cảnh bước ngoặt thời gian (Time-jump)': Dùng khi sang ngày mới hoặc đổi bối cảnh lớn.
   Mỗi cảnh ưu tiên dùng mốc 4s, 6s, 8s.
6. CHIẾN LƯỢC GIỮ CHÂN NGƯỜI XEM (GOLDEN HOOK & RETENTION): Phân cảnh số 1 phải có hook giật gân, câu hỏi kích thích tò mò hoặc hành động thị giác mạnh mẽ trong 3 giây đầu để giữ chân tuyệt đối.
7. VOICE & KHẨU HÌNH: 100% video prompt có lồng tiếng Việt miền Bắc chuẩn Hà Nội (~3 từ/s) kèm chỉ đạo khẩu hình khớp nhân vật.
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

def add_five_scripts_continuation(current_mode: str, current_style: str, aspect_ratio: str, goal: str, target_duration_mins: float):
    with st.spinner("⏳ Đang khai thác thêm 5 góc tiếp cận độc quyền bám sát sản phẩm & kho xưởng..."):
        all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
        cur_len = len(all_sources)
        product_ctx = st.session_state.get("current_input_context", "Sản phẩm hiện tại")
        
        prompt_more = f"""
        Dựa trên sản phẩm: "{product_ctx}" và kết quả phân tích DNA đã thực hiện cho thể loại '{current_mode}' phong cách '{current_style}'.
        Hãy tạo thêm đúng 5 kịch bản mới (id từ {cur_len + 1} đến {cur_len + 5}) với các key: id, title, setting_style, angle, target_hook, recommended_scenes_count, voice_profile.
        
        QUY ĐỊNH BẮT BUỘC CHO KỊCH BẢN MỚI:
        - Phải bám sát thực chiến sản phẩm, tập trung mạnh vào bối cảnh xưởng sản xuất, kho hàng tổng hoặc showroom trưng bày trực tiếp.
        - Phải xoay quanh chiến lược kích cầu: Giá tận gốc tại kho, deal sốc giới hạn giờ, bóc tách triệt để tính năng cơ khí và phụ kiện.
        Xuất JSON chuẩn với key 'script_outlines'.
        """
        try:
            res = call_gemini_api([prompt_more], get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins))
            new_scripts = res.get("script_outlines", [])
            for i, sc in enumerate(new_scripts): sc["id"] = cur_len + i + 1
            st.session_state.expanded_scripts.extend(new_scripts)
            st.success("✅ Đã bổ sung 5 kịch bản mới bám sát sản phẩm & kho xưởng!")
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi gọi thêm kịch bản: {e}")

def create_scene_details_for_id(target_id: int, current_mode: str, current_style: str, aspect_ratio: str, goal: str, target_duration_mins: float):
    all_sources = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts
    outline = next((sc for sc in all_sources if isinstance(sc, dict) and sc.get("id") == target_id), None)
    if not outline: return
    
    product_ctx = st.session_state.get("current_input_context", "Sản phẩm hiện tại")
    ca_data = st.session_state.get("content_analysis", {})
    exact_color_spec = ca_data.get("mechanical_and_accessories", "Giữ nguyên màu sắc chuẩn xác từ ảnh thực tế") if isinstance(ca_data, dict) else "Giữ nguyên màu sắc"
    
    total_sec = int(target_duration_mins * 60)
    duration_str = f"{total_sec}s ({target_duration_mins} phút)" if target_duration_mins > 0.5 else "24s - 35s (Chuyển đổi bán hàng)"
    
    with st.spinner(f"🎬 Đang dựng chi tiết cảnh quay #{target_id} (Thời lượng: {duration_str} | Khung hình {aspect_ratio})..."):
        prompt_detail = f"""
        Sản phẩm gốc & MÃ MÀU THỰC TẾ: "{exact_color_spec}" (Ngữ cảnh: {product_ctx})
        Thể loại nội dung: "{current_mode}" | Mục tiêu chiến dịch: "{goal}" | Tỷ lệ khung hình: "{aspect_ratio}" | Tổng thời lượng yêu cầu: {duration_str}
        Ý tưởng kịch bản: ID {target_id} - {outline.get('title')}
        Bối cảnh định hướng: {outline.get('setting_style')} | Góc tiếp cận: {outline.get('angle')} | Hook: {outline.get('target_hook')}
        
        QUY ĐỊNH ĐẠO DIỄN BẮT BUỘC CHO CÁC CẢNH:
        1. PHÂN RÃ THỜI LƯỢNG & SỐ PHÂN CẢNH: 
           - Nếu là Bán hàng (Sales): Tổng thời lượng từ 24s - 35s chia thành 4 đến 6 phân cảnh.
           - Nếu là Kể chuyện dài tập / Review chuyên sâu: Tổng thời lượng khớp chính xác {total_sec} giây, số lượng phân cảnh phải đủ nhiều để trải đều toàn bộ thời lượng.
        2. CHUYỂN CẢNH THÔNG MINH: AI tự quyết định `transition_type` phù hợp ('Cắt cứng dồn dập - Hard Cut', 'Chuyển cảnh khớp hành động mượt mà - Match Cut', hoặc 'Chuyển cảnh bước ngoặt thời gian - Time-jump').
        3. NHÂN VẬT & TRANG PHỤC: Giữ nguyên 100% khuôn mặt, biểu cảm và vóc dáng nhân vật người Việt Nam xuyên suốt. Nếu nội dung Bán hàng, bắt buộc mặc cùng một bộ trang phục cố định. Nếu nội dung Khác, được phép đổi trang phục theo mốc thời gian/bối cảnh.
        4. KHÓA MÀU SẢN PHẨM & VẬT LÝ HÚT BỤI: Giữ nguyên màu sản phẩm gốc, hướng hút bụi xoáy thẳng vào cốc trong suốt.
        5. MÀN HÌNH SẠCH & VOICE MIỀN BẮC: Ảnh sạch tuyệt đối, không có chữ (`no text, zero typography, clean screen`). Tích hợp lồng tiếng miền Bắc trong `video_prompt`.
        6. THAM CHIẾU KHUNG HÌNH (FRAME CHAINING): Đối với các phân cảnh nối tiếp, chú ý giữ tính liên tục tuyệt đối về không gian và hành động của sản phẩm.
        
        Xuất chuẩn 1 Dict JSON duy nhất:
        {{
          "id": {target_id}, 
          "title": "{outline.get('title')}", 
          "setting_style": "{outline.get('setting_style')}",
          "voice_profile": {json.dumps(outline.get('voice_profile', {}), ensure_ascii=False)},
          "total_estimated_duration": "{duration_str}",
          "scenes": [
            {{
              "scene_number": 1, 
              "duration": "6s", 
              "scene_setting": "Bối cảnh thực tế", 
              "transition_type": "Cắt cứng dồn dập (Hard Cut) hoặc Chuyển cảnh khớp hành động mượt mà (Match Cut)", 
              "voice_director_vn": "Chỉ đạo ngữ điệu miền Bắc", 
              "voiceover_vi": "Lời thoại miền Bắc", 
              "image_prompt": "Prompt Imagen 3 ({aspect_ratio}) hiển thị nhân vật nữ người Việt Nam (giữ nguyên khuôn mặt), trang phục phù hợp quy định, giữ nguyên màu sắc sản phẩm gốc, màn hình sạch, no text, clean screen", 
              "video_prompt": "Prompt Veo 3 miêu tả chuyển động, hành động hút bụi đúng chiều vật lý, đọc lời thoại miền Bắc khớp khẩu hình"
            }}
          ]
        }}
        """
        try:
            sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins)
            res = call_gemini_api([prompt_detail], sys_inst)
            if isinstance(res, list): res = res[0]
            st.session_state.generated_details[target_id] = res
            st.session_state.active_script_id = target_id
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi dựng chi tiết kịch bản: {e}")
            
# ==============================================================================
# GIAO DIỆN CHÍNH
# ==============================================================================
st.markdown("""
<div class="header-container">
    <div class="header-badge">🌟 STUDIO VIDEO AI ĐA NĂNG TOÀN DIỆN</div>
    <div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Nhà Ken Tôm</div>
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
        "🍲 Ẩm Thực & Đời Sống", "📖 Đời Sống & Giáo Dục", "🏛️ Lịch Sử & Tín Ngưỡng Di Sản", "🧘 Chữa Lành & Phong Cách Sống"
    ])
with col_style:
    selected_style = st.selectbox("🎨 Chọn Phong Cách Hình Ảnh:", options=[
        "Cinematic Realism (Người thật / Siêu thực 8K)", "3D Pixar / Disney Animation", "2D Ghibli / Anime Art",
        "Tranh Thủy Mặc Cổ Phong", "Cyberpunk / Sci-Fi Neon", "Vintage / Retro Film 1980s-90s",
        "Minimalist Studio / Commercial Clean", "Dark Moody / Noir", "Paper Cut-out / Stop Motion"
    ])

# BẢNG CẨM NANG PHỐI HỢP THỂ LOẠI & PHONG CÁCH
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
st.markdown("### 📐 Cấu Hình Khung Hình, Mục Đích & Thời Lượng Chiến Dịch")

col_ratio, col_goal, col_time = st.columns([1, 1, 1])
with col_ratio:
    aspect_ratio_choice = st.selectbox(
        "Tỷ lệ khung hình video:",
        ["9:16 (Dọc - TikTok, Reels, Shorts)", "16:9 (Ngang - YouTube, Phim dài, Facebook)"],
        index=0
    )
    selected_aspect = "9:16" if "9:16" in aspect_ratio_choice else "16:9"

with col_goal:
    if selected_mode == "🛒 TikTok Shop & Bán Hàng":
        content_goal = "Chuyển đổi đơn hàng & Chốt Sale trực tiếp (Sales & Conversion)"
        st.info("💡 **Chế độ Bán Hàng:** 24s-35s (4-6 phân cảnh), trang phục cố định 100%.")
    else:
        content_goal_options = [
            "Viral & Xây dựng thương hiệu cá nhân (Personal Branding)",
            "Kể chuyện dài tập / Phim ngắn (Long-form Storytelling)",
            "Chia sẻ kiến thức / Review chuyên sâu (Education & Deep Review)"
        ]
        content_goal = st.selectbox("Mục đích sản xuất video:", content_goal_options, index=0)

with col_time:
    if selected_mode == "🛒 TikTok Shop & Bán Hàng":
        target_duration_mins = 0.5 
        st.info("⏱️ **Thời lượng Bán Hàng:** Tự động tối ưu 24s - 35s.")
    else:
        target_duration_mins = st.number_input("⏱️ Nhập thời lượng mong muốn (Phút):", min_value=0.5, max_value=30.0, value=1.0, step=0.5)

st.markdown("---")
input_text = st.text_area("✍️ Tóm tắt ý tưởng, chủ đề hoặc mô tả chi tiết sản phẩm:", height=100)
uploaded_files = st.file_uploader("🖼️ Tải ảnh tham chiếu (Tùy chọn):", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if st.button("🚀 Bắt Đầu Phân Tích Chi Tiết Sản Phẩm & Lên Kịch Bản", type="primary", use_container_width=True, disabled=not (input_text.strip() or uploaded_files)):
    with st.spinner("⏳ Đang phân tích..."):
        try:
            st.session_state.current_input_context = input_text.strip() if input_text else "Phân tích trực tiếp từ hình ảnh đính kèm sản phẩm."
            
            prompt_text = f"""
            Phân tích siêu chuyên sâu sản phẩm/chủ đề bất kỳ cho thể loại '{selected_mode}' theo phong cách '{selected_style}'. 
            Thông tin mô tả từ người dùng: "{st.session_state.current_input_context}"

            QUY ĐỊNH ĐỘNG VỀ NHẬN DIỆN SẢN PHẨM (RẤT QUAN TRỌNG):
            1. Tự động quét màu sắc thực tế: Phải phân tích kỹ hình ảnh hoặc thông tin mô tả do người dùng cung cấp để xác định CHÍNH XÁC màu sắc chủ đạo (Hero Color), độ bóng/nhám, chất liệu thực tế của chính sản phẩm đó.
            2. Bóc tách cơ khí & cấu tạo linh hoạt: Tự động nhận diện vị trí các nút bấm, cổng sạc, màn hình LED, chất liệu và phụ kiện đi kèm.
            3. Khóa thị giác (Visual DNA Lock): Thiết lập chuỗi khóa thị giác đồng bộ để các prompt ảnh (Imagen 3) và video (Veo 3) tái tạo giống hệt sản phẩm thật ngoài đời.

            BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON CHUẨN GỒM CÁC KEY SAU:
            {{
              "content_analysis": {{
                "mechanical_and_accessories": "Mô tả chuẩn xác màu sắc thực tế của sản phẩm (Hero Color), chất liệu nhám/bóng, vị trí nút bấm, cổng sạc, trọng lượng, kích thước và trọn bộ phụ kiện kèm theo.",
                "customer_pain_points": "Phân tích 3 tầng nỗi đau của khách hàng (Chức năng, Tài chính - giá hời tại xưởng, Cảm xúc).",
                "core_desires": "Mong muốn cốt lõi và khao khát lớn nhất của khách hàng khi mua sản phẩm này.",
                "emotional_or_usp_hook": "Slogan, USP độc quyền hoặc câu hook giật gân chốt đơn.",
                "visual_physics_rules": "Quy chuẩn vật lý khi chuyển động đặc thù của sản phẩm (lực hút, độ đàn hồi, hiệu ứng ánh sáng, v.v.).",
                "prompt_dna_lock": "Chuỗi khóa thị giác đồng bộ toàn bộ video, bắt buộc ghim chính xác màu sắc thực tế và đặc điểm nhận diện."
              }},
              "script_outlines": [
                {{
                  "id": 1,
                  "title": "Tên kịch bản 1",
                  "setting_style": "Bối cảnh xưởng/kho/showroom",
                  "angle": "Góc tiếp cận chuyển đổi",
                  "target_hook": "Câu mở đầu giật gân",
                  "recommended_scenes_count": "5",
                  "voice_profile": {{"gender": "Nữ", "age_range": "25-30", "tone": "Năng lượng cao"}}
                }},
                {{
                  "id": 2,
                  "title": "Tên kịch bản 2",
                  "setting_style": "Bối cảnh xưởng/kho/showroom",
                  "angle": "Góc tiếp cận",
                  "target_hook": "Câu mở đầu",
                  "recommended_scenes_count": "5",
                  "voice_profile": {{"gender": "Nam", "age_range": "28-35", "tone": "Trầm ấm"}}
                }},
                {{
                  "id": 3,
                  "title": "Tên kịch bản 3",
                  "setting_style": "Bối cảnh xưởng/kho/showroom",
                  "angle": "Góc tiếp cận",
                  "target_hook": "Câu mở đầu",
                  "recommended_scenes_count": "5",
                  "voice_profile": {{"gender": "Nữ", "age_range": "25-30", "tone": "Hào hứng"}}
                }},
                {{
                  "id": 4,
                  "title": "Tên kịch bản 4",
                  "setting_style": "Bối cảnh xưởng/kho/showroom",
                  "angle": "Góc tiếp cận",
                  "target_hook": "Câu mở đầu",
                  "recommended_scenes_count": "5",
                  "voice_profile": {{"gender": "Nam", "age_range": "25-30", "tone": "Thuyết phục"}}
                }},
                {{
                  "id": 5,
                  "title": "Tên kịch bản 5",
                  "setting_style": "Bối cảnh xưởng/kho/showroom",
                  "angle": "Góc tiếp cận",
                  "target_hook": "Câu mở đầu",
                  "recommended_scenes_count": "5",
                  "voice_profile": {{"gender": "Nữ", "age_range": "28-35", "tone": "Tin cậy"}}
                }}
              ]
            }}
            """
            
            payload = []
            if uploaded_files:
                for f in uploaded_files:
                    payload.append(types.Part.from_bytes(data=f.getvalue(), mime_type=f.type if f.type else "image/jpeg"))
            payload.append(prompt_text)
            
            res = call_gemini_api(payload, get_system_instructions(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins))
            
            st.session_state.content_analysis = res.get("content_analysis")
            st.session_state.all_scripts = res.get("script_outlines", [])
            st.session_state.cloned_scripts, st.session_state.expanded_scripts, st.session_state.generated_details, st.session_state.active_script_id = [], [], {}, None
            st.success("✅ Đã quét màu sắc thực tế và phân tích DNA thành công!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Lỗi thực thi: {e}")

# Hiển thị DNA Phân tích
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
    raw_dna = str(ca.get('prompt_dna_lock', 'N/A')).replace('<br>', ' ').replace('<b>', '').replace('</b>', '')
    st.code(raw_dna, language="text")

# GIAI ĐOẠN 1: DANH SÁCH KỊCH BẢN BAN ĐẦU
all_combined_scripts_list = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts

if all_combined_scripts_list and st.session_state.active_script_id is None:
    st.divider()
    st.markdown(f"### 📋 **Danh Sách Ma Trận Kịch Bản Thực Chiến**")
    for outline in all_combined_scripts_list:
        sc_id = outline.get("id")
        col_info, col_act = st.columns([3, 1.2])
        with col_info:
            raw_scenes_count = outline.get("recommended_scenes_count", "5")
            scenes_display_text = f"{raw_scenes_count} Phân cảnh" if str(raw_scenes_count).isdigit() else str(raw_scenes_count)
            pacing_badge = f'<span class="badge-dynamic">🎬 {scenes_display_text}</span>'
            
            is_gen = sc_id in st.session_state.generated_details
            badge = '<span class="badge-ready">ĐÃ TẠO CHI TIẾT</span>' if is_gen else '<span class="badge-pending">CHƯA TẠO CHI TIẾT</span>'
            
            st.markdown(f"**{sc_id}. {outline.get('title')}** — {badge} {pacing_badge}", unsafe_allow_html=True)
            st.caption(f"🏛️ Bối cảnh: {outline.get('setting_style')} | ⚡ Hook: *\"{outline.get('target_hook')}\"*")
        with col_act:
            btn_lbl = "👁️ Xem chi tiết" if is_gen else "✨ Tạo chi tiết kịch bản này"
            if st.button(btn_lbl, key=f"btn_init_{sc_id}", use_container_width=True):
                if is_gen:
                    st.session_state.active_script_id = sc_id
                    st.rerun()
                else:
                    create_scene_details_for_id(sc_id, selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins)
    st.markdown("---")
    if st.button("➕ Gọi Thêm 5 Kịch Bản Khác", key="btn_add_more_1", type="primary", use_container_width=True):
        add_five_scripts_continuation(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins)

# GIAI ĐOẠN 2: CHI TIẾT KỊCH BẢN & BỐ CỤC ĐIỀU HƯỚNG
if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details:
    st.divider()
    raw_active_data = st.session_state.generated_details[st.session_state.active_script_id]
    
    if isinstance(raw_active_data, list):
        active_script = raw_active_data[0] if len(raw_active_data) > 0 else {}
    elif isinstance(raw_active_data, dict):
        active_script = raw_active_data
    else:
        active_script = {}

    raw_vp = active_script.get("voice_profile", {}) if isinstance(active_script, dict) else {}
    vp = raw_vp if isinstance(raw_vp, dict) else {"gender": "Nữ", "age_range": "25-30", "tone": "Năng lượng cao"}

    script_title = active_script.get('title', 'Kịch bản chi tiết') if isinstance(active_script, dict) else 'Kịch bản chi tiết'
    total_dur = active_script.get('total_estimated_duration', '24s') if isinstance(active_script, dict) else '24s'

    st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(script_title).upper()}**")
    st.info(f"⏱️ Tổng thời lượng: **{total_dur}** | 🎙️ Giọng: **{vp.get('gender', 'Nữ')} miền Bắc ({vp.get('age_range', '25-30')})** | 📐 Khung hình: **{selected_aspect}**")

    scenes_list = active_script.get("scenes", []) if isinstance(active_script, dict) else []
    if isinstance(scenes_list, dict): scenes_list = [scenes_list]
    
    for idx, scene in enumerate(scenes_list, start=1):
        if not isinstance(scene, dict): continue
        dur = scene.get("duration", "6s")
        st.markdown(f"#### **📍 Phân cảnh {idx} ({dur}) — [ {scene.get('transition_type', 'Cắt cứng dồn dập')} ]**")
        st.markdown(f"🏛️ **Bối cảnh & Biểu cảm nhân vật:** *{scene.get('scene_setting')}*")
        st.markdown(f"**🎙️ Đạo diễn ngữ điệu:** *{scene.get('voice_director_vn')}*")
        st.markdown(f"**💬 Lời thoại:** `\"{scene.get('voiceover_vi')}\"`")
        
        img_p = scene.get('image_prompt', '')
        if img_p:
            st.markdown(f"**🖼️ Prompt Ảnh (Imagen 3 - {selected_aspect}):**")
            st.code(img_p, language="text")
            safe_copy_button(img_p, f"📋 Sao Chép Prompt Ảnh Cảnh {idx}")
            
        vid_p = scene.get('video_prompt', '')
        st.markdown(f"**🎥 Prompt Video (Veo 3):**")
        st.code(vid_p, language="text")
        safe_copy_button(vid_p, f"📋 Sao Chép Prompt Video Cảnh {idx}")
        st.markdown("---")

    st.markdown("### ⚡ **Khu Vực Quản Trị & Mở Rộng Kịch Bản**")
    col_left, col_right = st.columns([1.1, 0.9])

    with col_left:
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
                    try:
                        target_script = st.session_state.generated_details[selected_win_id]
                        cur_len = len(all_combined_scripts_list)
                        p_clone = f"Dựa trên kịch bản: {json.dumps(target_script, ensure_ascii=False)}. Tạo đúng 5 biến thể mới (id từ {cur_len+1} đến {cur_len+5}). Xuất JSON key 'cloned_outlines'."
                        res_c = call_gemini_api([p_clone], get_system_instructions(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins))
                        cloned_list = res_c.get("cloned_outlines", [])
                        for idx_c, cl in enumerate(cloned_list): cl["id"] = cur_len + idx_c + 1
                        st.session_state.cloned_scripts.extend(cloned_list)
                        st.success("✅ Đã nhân bản thành công!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="custom-card">
            <div class="card-title-add">➕ Vùng Gọi Thêm Kịch Bản Mới</div>
            <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 8px;">Mở rộng thêm ý tưởng từ dữ liệu DNA đã phân tích.</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("➕ Gọi Thêm 5 Tình Huống Kịch Bản Mới", key="btn_add_more_phase2", use_container_width=True):
            add_five_scripts_continuation(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins)

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
                st.markdown(f"• **#{it_id}. {item.get('title')}** — <span class='badge-pending'>CHƯA TẠO</span>", unsafe_allow_html=True)
                
                if st.button("✨ Tạo chi tiết ngay", key=f"nav_sc_{it_id}", use_container_width=True):
                    create_scene_details_for_id(it_id, selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins)
                st.markdown("<hr style='margin: 6px 0;'>", unsafe_allow_html=True)
