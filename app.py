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
# 1. CẤU HÌNH GIAO DIỆN & CSS CHUYÊN NGHIỆP
# ==============================================================================
st.set_page_config(
    page_title="Universal AI Video Studio Pro & License Manager",
    page_icon="🎬",
    layout="wide"
)

st.markdown("""
<style>
    .header-container { text-align: center; padding: 1.2rem 1rem 1.8rem 1rem; margin-bottom: 1rem; background: radial-gradient(circle, rgba(255,75,75,0.08) 0%, rgba(255,255,255,0) 70%); border-radius: 16px; }
    .main-title { font-size: 2.35rem !important; font-weight: 900 !important; background: linear-gradient(90deg, #ff0050 0%, #ff5252 50%, #ff7300 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem !important; line-height: 1.25 !important; letter-spacing: -0.5px; }
    .sub-title { font-size: 1.12rem !important; font-weight: 500 !important; color: #4a5568 !important; margin-top: 0.2rem; }
    .header-badge { display: inline-block; background: #fee2e2; color: #b91c1c; font-size: 0.8rem; font-weight: 800; padding: 3px 12px; border-radius: 9999px; margin-bottom: 0.5rem; letter-spacing: 0.5px; border: 1px solid #fca5a5; }
    div[data-testid="stSelectbox"] label p { font-size: 1.15rem !important; font-weight: 800 !important; color: #1e293b !important; }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div { font-size: 1.1rem !important; font-weight: 700 !important; min-height: 52px !important; background-color: #ffffff !important; border: 2px solid #cbd5e1 !important; border-radius: 10px !important; }
    .custom-card { background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
    .card-title-add { color: #d97706; font-weight: 800; font-size: 1.2rem; margin-bottom: 6px; }
    div[data-testid="stButton"] > button { width: 100% !important; border-radius: 8px !important; font-weight: 700 !important; border: none !important; transition: all 0.25s ease-in-out !important; }
    div[data-testid="stButton"] > button[kind="secondary"] { background: linear-gradient(135deg, #ff4b4b 0%, #ff7300 100%) !important; color: #ffffff !important; box-shadow: 0 3px 8px rgba(255, 75, 75, 0.35) !important; padding: 0.55rem 1rem !important; }
    div[data-testid="stButton"] > button[kind="secondary"]:hover { background: linear-gradient(135deg, #e63946 0%, #e85d04 100%) !important; box-shadow: 0 5px 14px rgba(255, 75, 75, 0.5) !important; transform: translateY(-1px) !important; }
    div[data-testid="stButton"] > button[kind="primary"] { background: linear-gradient(135deg, #e63946 0%, #d90429 100%) !important; color: #ffffff !important; box-shadow: 0 4px 10px rgba(230, 57, 70, 0.4) !important; padding: 0.6rem 1rem !important; }
    .badge-pending { color: #d97706; font-weight: 700; background: #fef3c7; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
    .badge-ready { color: #15803d; font-weight: 700; background: #dcfce7; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
    .support-box { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1.5px solid #86efac; border-radius: 12px; padding: 12px; text-align: center; margin-top: 15px; }
    @keyframes pulse { 0% { transform: scale(0.98); opacity: 0.8; } 50% { transform: scale(1.02); opacity: 1; } 100% { transform: scale(0.98); opacity: 0.8; } }
    .loading-pulse { animation: pulse 1.5s infinite ease-in-out; color: #d90429; font-weight: 800; text-align: center; padding: 25px; background: #fef2f2; border: 2px dashed #fca5a5; border-radius: 12px; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. KHỞI TẠO API & HẰNG SỐ
# ==============================================================================
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
if not api_key:
    st.error("Chưa cấu hình khóa GEMINI_API_KEY trong phần cấu hình bảo mật (Secrets).")
    st.stop()

client = genai.Client(api_key=api_key)

ACCOUNTS_FILE = "accounts.json"
ADMIN_EMAIL = "binhnguyenmedia.vn@gmail.com"
ALL_MODULES = [
    "🛒 TikTok Shop & Bán Hàng", "👶 Mẹ & Bé & Cùng Con Học", "📺 TVC Quảng Cáo & Thương Hiệu Cao Cấp",
    "🏡 Nhà Cửa, Kiến Trúc & Cảnh Quan", "🌿 Du Lịch & Phong Cảnh Đất Nước", "🚗 Xe Cộ & Trải Nghiệm Lái",
    "🍲 Ẩm Thực & Đời Sống", "📖 Đời Sống & Giáo Dục", "🏛️ Lịch Sử & Tín Ngưỡng Di Sản", 
    "🧘 Chữa Lành & Phong Cách Sống", "📢 Phóng Sự & Thông Điệp Xã Hội", "🏢 Giới Thiệu Doanh Nghiệp"
]

def load_licensed_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    default_accounts = {
        ADMIN_EMAIL: {"contact": ADMIN_EMAIL, "roles": ["Tất cả thể loại"], "expires_at": "2099-12-31"}
    }
    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_accounts, f, ensure_ascii=False, indent=2)
    except: pass
    return default_accounts

# ==============================================================================
# 3. KHỞI TẠO SESSION STATE (BỘ NHỚ TẠM)
# ==============================================================================
default_states = {
    "content_analysis": None, "all_scripts": [], "cloned_scripts": [], 
    "expanded_scripts": [], "generated_details": {}, "active_script_id": None, 
    "projects_library": {}, "licensed_accounts": load_licensed_accounts(), 
    "current_input_context": "", "is_logged_in": False, "current_user_email": "", 
    "active_project_title": "Chiến dịch mới", "last_loaded_file_id": None, 
    "file_uploader_key": 0, "scroll_to_top": False, "action_trigger": None, 
    "action_param": None, "character_profiles": [], "main_input_context": "", 
    "num_chars_input": 0, "global_toast": "", "global_toast_icon": "✅"
}

for key, default_val in default_states.items():
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
            }
            forceScroll();
            setTimeout(forceScroll, 100);
            setTimeout(forceScroll, 300);
        </script>
    """, height=0)
    st.session_state.scroll_to_top = False

# ==============================================================================
# 4. HÀM TIỆN ÍCH (UTILITIES) & XỬ LÝ CHUỖI
# ==============================================================================
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

def clean_and_parse_json(text_content: str):
    cleaned = text_content.replace("```json", "").replace("```", "").strip()
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

def safe_copy_button(text_to_copy: str, button_label: str = "📋 Sao Chép"):
    b64 = base64.b64encode(text_to_copy.encode('utf-8')).decode('utf-8')
    components.html(f"""
    <button onclick='navigator.clipboard.writeText(decodeURIComponent(escape(atob("{b64}"))));this.innerText="✅ Đã sao chép!";setTimeout(()=>this.innerText="{button_label}",2000);' style="background:linear-gradient(135deg, #ff4b4b, #ff7300);color:white;border:none;padding:8px 16px;font-size:13px;font-weight:700;border-radius:6px;cursor:pointer;width:100%;">{button_label}</button>
    """, height=40)

def get_realtime_context():
    now = datetime.now()
    seasons = {2:"Xuân", 3:"Xuân", 4:"Xuân", 5:"Hè", 6:"Hè", 7:"Hè", 8:"Thu", 9:"Thu", 10:"Thu", 11:"Đông", 12:"Đông", 1:"Đông"}
    season = seasons.get(now.month, "Mùa Xuân")
    return f"THỜI GIAN THỰC TẾ: Tháng {now.month}/{now.year} (Mùa {season}). TƯ DUY ÁP DỤNG MÙA VỤ: Phân tích khách hàng theo mùa vụ nếu phù hợp."

# ==============================================================================
# 5. HỆ THỐNG PROMPT ĐIỀU HƯỚNG AI (AI ENGINE)
# ==============================================================================
def get_strategy_rules(mode: str, strategy: str, target_audience: str) -> str:
    rules = f"- ĐỐI TƯỢNG MỤC TIÊU CỐT LÕI: Phải nhắm thẳng vào tệp khách hàng: {target_audience}.\n"
    if "Bán Hàng" in mode or "Mẹ & Bé" in mode:
        if "Hỗn hợp" in strategy:
            rules += "- BẮT BUỘC ĐA DẠNG HÓA CƠ CẤU KỊCH BẢN: Kết hợp kịch bản Bán hàng trực diện (Review/Xưởng) + kịch bản Shoppertainment (Drama đời sống/gia đình bẻ lái chốt sale).\n"
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
       - TUYỆT ĐỐI KHÔNG ĐƯA GIÁ TIỀN BẰNG CON SỐ (như 199k, 50k) VÀO LỜI THOẠI. Chỉ dùng "giá tận xưởng", "deal hời" hoặc "giá cực tốt".
    8. BỘ LỌC CHÍNH SÁCH ĐA NỀN TẢNG (COMPLIANCE):
       - TUYỆT ĐỐI KHÔNG DÙNG: "100%", "tuyệt đối", "cam kết", "chắc chắn", "vĩnh viễn", "trị dứt điểm".
       - CẤM TUYÊN BỐ Y TẾ, ĐIỀU TRỊ SAI LỆCH VÀ GIEO RẮC SỢ HÃI: Không dùng "độc hại", "ung thư", "chống cận thị tuyệt đối". THAY BẰNG: "hỗ trợ bảo vệ", "kém an toàn".
       - CẤM TỪ KHÓA ĐIỀU HƯỚNG: "livestream", "phiên live", "inbox riêng", "zalo".
    9. QUY CHUẨN ĐẠO DIỄN CẮT CẢNH LUÂN PHIÊN (SHOT/REVERSE SHOT CHO DRAMA):
       - Trong các cảnh đối thoại đa nhân vật, TUYỆT ĐỐI KHÔNG để tất cả cùng nói một lúc. 
       - Phân chia: Cảnh 1 tập trung vào Nhân vật A nói (Cận cảnh mặt A). Cảnh tiếp theo chuyển góc sang Nhân vật B phản hồi (Cận cảnh mặt B hoặc góc qua vai).
       - Việc này giúp mô hình AI tạo video tập trung xử lý một khuôn mặt độc lập, loại bỏ hoàn toàn lỗi biến dạng (morphing) và lệch khẩu hình tiếng Việt.
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
# 6. GỌI API GEMINI VÀ XỬ LÝ LÕI KỊCH BẢN (KHÔNG VIẾT TẮT)
# ==============================================================================
def call_gemini_with_retry(payload, sys_inst):
    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash", 
                contents=payload, 
                config=types.GenerateContentConfig(
                    system_instruction=sys_inst, 
                    response_mime_type="application/json"
                )
            )
            return clean_and_parse_json(response.text)
        except Exception as e:
            if "429" in str(e): time.sleep(15)
            elif "503" in str(e): time.sleep(3 * (attempt + 1))
            else: time.sleep(4)
    raise Exception("Lỗi kết nối Gemini API. Vui lòng thử lại sau.")

def create_scene_details_for_id(target_id: int, current_mode: str, current_style: str, aspect_ratio: str, goal: str, target_duration_mins: float, current_strategy: str):
    all_sources = (st.session_state.all_scripts or []) + (st.session_state.cloned_scripts or []) + (st.session_state.expanded_scripts or [])
    outline = next((sc for sc in all_sources if isinstance(sc, dict) and int(sc.get("id", 0)) == int(target_id)), None)
    if not outline: raise Exception(f"Không tìm thấy kịch bản #{target_id} trong bộ nhớ.")
    
    product_ctx = st.session_state.get("current_input_context", "Dự án hiện tại").replace('"', "'")
    safe_title = outline.get('title', '').replace('"', "'").replace('\n', ' ')
    safe_setting = outline.get('setting_style', '').replace('"', "'").replace('\n', ' ')
    
    is_sales_mode = "Bán Hàng" in current_mode

    if target_duration_mins <= 0.5:
        duration_str = "16s - 32s (Tối ưu Credit Veo 3)"
    else:
        total_sec = int(target_duration_mins * 60)
        duration_str = f"{total_sec}s ({target_duration_mins} phút)"

    profiles = st.session_state.get("character_profiles", [])
    profiles_desc = ""
    if profiles:
        profiles_desc = "DANH SÁCH DIỄN VIÊN ĐÃ ĐĂNG KÝ (GIỮ NGUYÊN IDENTITY TỪ ẢNH THAM CHIẾU):\n"
        for p in profiles:
            profiles_desc += f"- Diễn viên {p['id']}: Đóng vai '{p['role']}'. Lệnh bắt buộc trong prompt: 'Character {p['id']} ({p['role']}) featuring exact identity of reference image {p['id']}'.\n"
    else:
        profiles_desc = "DANH SÁCH DIỄN VIÊN: Kịch bản đa nhân vật linh hoạt theo bối cảnh."

    char_rules_str = generate_char_rules_string(profiles, is_sales_mode)
    dna_data = st.session_state.get("content_analysis", {})
    target_audience = dna_data.get("primary_target_audience", "Người dùng")
    
    prompt_detail = f"""
    Ngữ cảnh: "{product_ctx}" | Đối tượng: {target_audience}
    Ý tưởng kịch bản: ID {target_id} - {safe_title} | Bối cảnh: {safe_setting}
    CHIẾN LƯỢC: {current_strategy}
    {profiles_desc}
    
    QUY ĐỊNH ĐẠO DIỄN NÂNG CAO CHO ĐA NHÂN VẬT & VOICE TIẾNG VIỆT (CRITICAL):
    1. ĐỐI THOẠI ĐA NHÂN VẬT (MULTI-CHARACTER DIALOGUE): Phân cảnh bắt buộc có sự tương tác qua lại giữa các nhân vật. Mỗi câu thoại trong mảng `dialogues` phải gắn với tên nhân vật phát ngôn.
    2. TÍCH HỢP VOICE TIẾNG VIỆT TRONG VIDEO PROMPT: Trong `video_prompt`, BẮT BUỘC phải trích dẫn lại chính xác nội dung câu thoại tiếng Việt bằng cú pháp: `Speaking in Vietnamese: "[Nội dung câu thoại]"`, giúp Veo 3 tạo âm thanh và khẩu hình chuẩn xác.
    3. KỶ LUẬT SỐ TỪ THUYẾT MINH: Tổng số từ của tất cả nhân vật trong 1 cảnh chuẩn nhịp: Cảnh 4s (12-14 từ); Cảnh 6s (18-21 từ); Cảnh 8s (24-28 từ). TUYỆT ĐỐI KHÔNG chứa dấu ngoặc đơn và KHÔNG dùng con số giá tiền cụ thể.
    4. ĐẠO DIỄN GÓC MÁY & KHÔNG CHE KHUẤT (NO OCCLUSION): Dùng kỹ thuật Cắt cảnh luân phiên (Shot/Reverse Shot). Sản phẩm trung tâm phải luôn rõ ràng, không bị tay che khuất.
    
    Xuất chuẩn 1 Dict JSON duy nhất (Mẫu cấu trúc PHẢI CÓ TỪ 3 ĐẾN 4 SCENE, ĐƯỢC VIẾT ĐẦY ĐỦ 100% NỘI DUNG VÀO CÁC NGOẶC VUÔNG [...], TUYỆT ĐỐI KHÔNG DÙNG DẤU BA CHẤM):
    {{
      "id": {target_id}, 
      "title": "{safe_title}", 
      "setting_style": "{safe_setting}",
      "script_outfit_setup": "Trang phục đồng bộ theo từng nhân vật trong hồ sơ",
      "voice_profile": {{"gender": "Hỗn hợp Nam/Nữ", "tone": "Đa nhân vật biểu cảm chân thực"}},
      "total_estimated_duration": "{duration_str}",
      "scenes": [
        {{
          "scene_number": 1, 
          "duration": "8s", 
          "scene_setting": "[Mô tả chi tiết bối cảnh và vị trí đứng của các nhân vật tham gia cảnh này]", 
          "transition_type": "Mở đầu tình huống", 
          "voice_director_vn": "[Chỉ đạo diễn xuất, ví dụ: Không khí căng thẳng, dồn dập]", 
          "dialogues": [
            {{"speaker": "Nhân vật A", "dialogue": "[Câu thoại thứ nhất của nhân vật A bằng tiếng Việt]"}},
            {{"speaker": "Nhân vật B", "dialogue": "[Câu thoại đáp trả của nhân vật B bằng tiếng Việt]"}}
          ],
          "image_prompt": "A 9:16 vertical cinematic shot showing Character A and Character B in {safe_setting}. Product is fully visible. Cinematic shot ONLY. ABSOLUTELY NO UI elements.", 
          "video_prompt": "Audio: Characters speaking on-camera in Vietnamese. Character A says: '[Điền câu thoại của Nhân vật A vào đây]'. Character B replies: '[Điền câu thoại của Nhân vật B vào đây]'. Background ambient sound: realistic room tone, volume strictly lower than voiceover. Visual: Cinematic multi-character shot. ABSOLUTELY NO UI elements. Product maintains rigid structural integrity, action ends fully visible."
        }},
        {{
          "scene_number": 2, 
          "duration": "6s", 
          "scene_setting": "[Mô tả góc máy cận cảnh phản ứng của nhân vật hoặc chi tiết sản phẩm]", 
          "transition_type": "Cắt cứng (Hard Cut)", 
          "voice_director_vn": "[Chỉ đạo diễn xuất tiếp theo]", 
          "dialogues": [
            {{"speaker": "Nhân vật A", "dialogue": "[Lời thoại tiếp theo bằng tiếng Việt]"}}
          ],
          "image_prompt": "A 9:16 close-up shot of the interaction. Product is fully visible, strictly NO hands obscuring the main body. Cinematic shot ONLY. ABSOLUTELY NO UI elements.", 
          "video_prompt": "Audio: Character speaking on-camera in Vietnamese, saying: '[Điền câu thoại của nhân vật vào đây]'. Background ambient sound: subtle environment noise, volume strictly lower than voiceover. Visual: Cinematic shot ONLY. ABSOLUTELY NO UI elements. Product maintains rigid structural integrity."
        }},
        {{
          "scene_number": 3, 
          "duration": "8s", 
          "scene_setting": "[Mô tả không gian kết luận hoặc bẻ lái chốt sale]", 
          "transition_type": "Nối liền mạch (Match Cut)", 
          "voice_director_vn": "[Chỉ đạo chốt sale năng lượng]", 
          "dialogues": [
            {{"speaker": "Nhân vật chính", "dialogue": "[Lời thoại chốt sale bằng tiếng Việt không dùng giá tiền số]"}}
          ],
          "image_prompt": "Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu cho video", 
          "video_prompt": "Audio: Character speaking on-camera in Vietnamese with high conversion tone, saying: '[Điền câu thoại chốt sale vào đây]'. Background ambient sound: upbeat subtle noise, volume strictly lower than voiceover. Visual: Cinematic shot ONLY. ABSOLUTELY NO UI elements. Product maintains rigid structural integrity, action ends with the product fully visible and unoccluded."
        }}
      ]
    }}
    LƯU Ý CỰC KỲ QUAN TRỌNG: BẠN PHẢI VIẾT NỘI DUNG THAY THẾ CHO TOÀN BỘ CÁC ĐOẠN TRONG NGOẶC VUÔNG [...].
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
    
    Xuất JSON chuẩn với key 'script_outlines' chứa ĐẦY ĐỦ 5 OBJECT. PHẢI ĐIỀN ĐỦ THÔNG TIN VÀO CÁC NGOẶC VUÔNG [...], TUYỆT ĐỐI KHÔNG SỬ DỤNG DẤU BA CHẤM "...":
    {{
      "script_outlines": [
        {{
          "id": {cur_len + 1},
          "title": "[Điền tên kịch bản 1]",
          "setting_style": "[Điền mô tả bối cảnh 1]",
          "script_outfit_setup": "[Điền mô tả màu sắc trang phục 1]",
          "angle": "[Điền góc tiếp cận 1]",
          "target_hook": "[Điền câu mở đầu 1]",
          "recommended_scenes_count": "3 đến 4 phân cảnh",
          "voice_profile": {{"gender": "[Nam hoặc Nữ]", "tone": "năng lượng"}}
        }},
        {{
          "id": {cur_len + 2},
          "title": "[Điền tên kịch bản 2]",
          "setting_style": "[Điền mô tả bối cảnh 2]",
          "script_outfit_setup": "[Điền mô tả màu sắc trang phục 2]",
          "angle": "[Điền góc tiếp cận 2]",
          "target_hook": "[Điền câu mở đầu 2]",
          "recommended_scenes_count": "3 đến 4 phân cảnh",
          "voice_profile": {{"gender": "[Nam hoặc Nữ]", "tone": "năng lượng"}}
        }},
        {{
          "id": {cur_len + 3},
          "title": "[Điền tên kịch bản 3]",
          "setting_style": "[Điền mô tả bối cảnh 3]",
          "script_outfit_setup": "[Điền mô tả màu sắc trang phục 3]",
          "angle": "[Điền góc tiếp cận 3]",
          "target_hook": "[Điền câu mở đầu 3]",
          "recommended_scenes_count": "3 đến 4 phân cảnh",
          "voice_profile": {{"gender": "[Nam hoặc Nữ]", "tone": "năng lượng"}}
        }},
        {{
          "id": {cur_len + 4},
          "title": "[Điền tên kịch bản 4]",
          "setting_style": "[Điền mô tả bối cảnh 4]",
          "script_outfit_setup": "[Điền mô tả màu sắc trang phục 4]",
          "angle": "[Điền góc tiếp cận 4]",
          "target_hook": "[Điền câu mở đầu 4]",
          "recommended_scenes_count": "3 đến 4 phân cảnh",
          "voice_profile": {{"gender": "[Nam hoặc Nữ]", "tone": "năng lượng"}}
        }},
        {{
          "id": {cur_len + 5},
          "title": "[Điền tên kịch bản 5]",
          "setting_style": "[Điền mô tả bối cảnh 5]",
          "script_outfit_setup": "[Điền mô tả màu sắc trang phục 5]",
          "angle": "[Điền góc tiếp cận 5]",
          "target_hook": "[Điền câu mở đầu 5]",
          "recommended_scenes_count": "3 đến 4 phân cảnh",
          "voice_profile": {{"gender": "[Nam hoặc Nữ]", "tone": "năng lượng"}}
        }}
      ]
    }}
    LƯU Ý: KHÔNG DÙNG DẤU NGOẶC KÉP CHƯA ESCAPE BÊN TRONG GIÁ TRỊ JSON.
    """
    sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins, char_rules_str, current_strategy, target_audience)
    res = call_gemini_with_retry([prompt_more], sys_inst)
    new_scripts = res.get("script_outlines", [])
    for i, sc in enumerate(new_scripts): sc["id"] = cur_len + i + 1
    st.session_state.expanded_scripts.extend(new_scripts)

def clone_script_id(target_id, current_mode, current_style, aspect_ratio, goal, target_duration_mins, current_strategy):
    target_script = st.session_state.generated_details[target_id]
    cur_len = len(st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts)
    char_rules_str = generate_char_rules_string(st.session_state.get("character_profiles", []), "Bán Hàng" in current_mode)
    
    prompt = f"""
    Dựa trên kịch bản gốc: {json.dumps(target_script, ensure_ascii=False)}. 
    Tạo ĐÚNG 5 biến thể mới (id từ {cur_len+1} đến {cur_len+5}). 
    
    Xuất JSON key 'cloned_outlines' chứa ĐẦY ĐỦ 5 OBJECT. PHẢI ĐIỀN ĐỦ THÔNG TIN VÀO CÁC NGOẶC VUÔNG [...], TUYỆT ĐỐI KHÔNG SỬ DỤNG DẤU BA CHẤM "...":
    {{
      "cloned_outlines": [
        {{
          "id": {cur_len + 1},
          "title": "[Điền tên biến thể 1]",
          "setting_style": "[Điền bối cảnh 1]",
          "script_outfit_setup": "[Điền trang phục 1]",
          "angle": "[Điền góc tiếp cận 1]",
          "target_hook": "[Điền hook 1]",
          "recommended_scenes_count": "3 đến 4 phân cảnh",
          "voice_profile": {{"gender": "[Nam hoặc Nữ]", "tone": "năng lượng"}}
        }},
        {{
          "id": {cur_len + 2},
          "title": "[Điền tên biến thể 2]",
          "setting_style": "[Điền bối cảnh 2]",
          "script_outfit_setup": "[Điền trang phục 2]",
          "angle": "[Điền góc tiếp cận 2]",
          "target_hook": "[Điền hook 2]",
          "recommended_scenes_count": "3 đến 4 phân cảnh",
          "voice_profile": {{"gender": "[Nam hoặc Nữ]", "tone": "năng lượng"}}
        }},
        {{
          "id": {cur_len + 3},
          "title": "[Điền tên biến thể 3]",
          "setting_style": "[Điền bối cảnh 3]",
          "script_outfit_setup": "[Điền trang phục 3]",
          "angle": "[Điền góc tiếp cận 3]",
          "target_hook": "[Điền hook 3]",
          "recommended_scenes_count": "3 đến 4 phân cảnh",
          "voice_profile": {{"gender": "[Nam hoặc Nữ]", "tone": "năng lượng"}}
        }},
        {{
          "id": {cur_len + 4},
          "title": "[Điền tên biến thể 4]",
          "setting_style": "[Điền bối cảnh 4]",
          "script_outfit_setup": "[Điền trang phục 4]",
          "angle": "[Điền góc tiếp cận 4]",
          "target_hook": "[Điền hook 4]",
          "recommended_scenes_count": "3 đến 4 phân cảnh",
          "voice_profile": {{"gender": "[Nam hoặc Nữ]", "tone": "năng lượng"}}
        }},
        {{
          "id": {cur_len + 5},
          "title": "[Điền tên biến thể 5]",
          "setting_style": "[Điền bối cảnh 5]",
          "script_outfit_setup": "[Điền trang phục 5]",
          "angle": "[Điền góc tiếp cận 5]",
          "target_hook": "[Điền hook 5]",
          "recommended_scenes_count": "3 đến 4 phân cảnh",
          "voice_profile": {{"gender": "[Nam hoặc Nữ]", "tone": "năng lượng"}}
        }}
      ]
    }}
    LƯU Ý: KHÔNG DÙNG DẤU NGOẶC KÉP CHƯA ESCAPE BÊN TRONG JSON VALUE.
    """
    sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins, char_rules_str, current_strategy, "")
    res_c = call_gemini_with_retry([prompt], sys_inst)
    cloned_list = res_c.get("cloned_outlines", [])
    for idx_c, cl in enumerate(cloned_list): cl["id"] = cur_len + idx_c + 1
    st.session_state.cloned_scripts.extend(cloned_list)

    # ==============================================================================
# 7. THANH BÊN (SIDEBAR) - QUẢN LÝ TÀI KHOẢN, DỰ ÁN & ADMIN
# ==============================================================================
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
            st.session_state.action_trigger = None
            st.session_state.action_param = None
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
                    "title": project_title_input, "mode": st.session_state.get("selected_mode", ""),
                    "style": st.session_state.get("selected_style", ""), "content_analysis": st.session_state.content_analysis,
                    "all_scripts": st.session_state.all_scripts, "cloned_scripts": st.session_state.cloned_scripts,
                    "expanded_scripts": st.session_state.expanded_scripts, "generated_details": st.session_state.generated_details,
                    "character_profiles": st.session_state.character_profiles,
                    "current_input_context": st.session_state.get("main_input_context", "")
                }
                st.toast("✅ Đã lưu dự án vào bộ nhớ!", icon="💾")

        with col_p2:
            export_data = {
                "title": project_title_input, "mode": st.session_state.get("selected_mode", ""),
                "style": st.session_state.get("selected_style", ""), "content_analysis": st.session_state.content_analysis,
                "all_scripts": st.session_state.all_scripts, "cloned_scripts": st.session_state.cloned_scripts,
                "expanded_scripts": st.session_state.expanded_scripts, "generated_details": st.session_state.generated_details,
                "character_profiles": st.session_state.character_profiles,
                "current_input_context": st.session_state.get("main_input_context", "")
            }
            json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
            st.download_button(label="📥 Tải JSON", data=json_str, file_name=f"{project_title_input.replace(' ', '_')}.json", mime="application/json", use_container_width=True)

        if st.session_state.projects_library:
            proj_keys = list(st.session_state.projects_library.keys())
            selected_load_id = st.selectbox("📂 Chọn dự án đã lưu:", options=proj_keys, format_func=lambda x: st.session_state.projects_library[x]["title"])
            if st.button("📂 Mở Dự Án Này", use_container_width=True):
                p_data = st.session_state.projects_library[selected_load_id]
                st.session_state.active_project_title = p_data.get("title", "Dự án tải lên")
                st.session_state.content_analysis = p_data.get("content_analysis")
                st.session_state.all_scripts = p_data.get("all_scripts", [])
                st.session_state.cloned_scripts = p_data.get("cloned_scripts", [])
                st.session_state.expanded_scripts = p_data.get("expanded_scripts", [])
                st.session_state.generated_details = p_data.get("generated_details", {})
                st.session_state.character_profiles = p_data.get("character_profiles", [])
                st.session_state.main_input_context = p_data.get("current_input_context", "")
                st.session_state.active_script_id = None
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
            <b style="color: #166534; font-size: 0.95rem;">💬 Cần Hỗ Trợ Dịch Vụ?</b><br>
            <div style="display: flex; justify-content: center; gap: 5px; flex-wrap: wrap; margin-top: 8px;">
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

# ==============================================================================
# 8. TIÊU ĐỀ CHÍNH VÀ KIỂM TRA ĐĂNG NHẬP
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
# 9. GIAO DIỆN CẤU HÌNH VÀ XỬ LÝ SỰ KIỆN (ACTION TRIGGERS)
# ==============================================================================
allowed_modules = ALL_MODULES
user_email = st.session_state.get("current_user_email", "")
if user_email and user_email != ADMIN_EMAIL:
    user_roles = st.session_state.licensed_accounts.get(user_email, {}).get("roles", [])
    if "Tất cả thể loại" not in user_roles:
        allowed_modules = [m for m in ALL_MODULES if m in user_roles]
        if not allowed_modules: allowed_modules = [ALL_MODULES[0]]

col_mode, col_style = st.columns([1.5, 1])
with col_mode:
    selected_mode = st.selectbox("🎯 Chọn Thể Loại Nội Dung:", options=allowed_modules, key="selected_mode")

# Phân luồng Chiến lược tự động theo Thể loại
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
    ], key="selected_style")
    style_mapping = {"Điện Ảnh Chân Thực (Người thật / Siêu thực 8K)": "Cinematic Realism", "Hoạt Hình 3D (Kiểu Pixar / Disney)": "3D Pixar Animation", "Hoạt Hình 2D (Phong cách Ghibli / Anime)": "2D Ghibli Anime", "Tranh Thủy Mặc Cổ Phong (Truyền thống Á Đông)": "Traditional Ink Wash", "Viễn Tưởng Tương Lai (Cyberpunk)": "Cyberpunk", "Studio Tối Giản (Hiện đại, Sạch sẽ)": "Minimalist Studio"}
    selected_style = style_mapping.get(selected_style_vn, "Cinematic Realism")

col_strat, col_ratio, col_time = st.columns([1.5, 1, 1])
with col_strat: selected_strategy = st.selectbox("🧠 Chiến lược Kịch bản (AI Strategy):", options=strat_options)
with col_ratio: selected_aspect = "9:16" if "9:16" in st.selectbox("Tỷ lệ khung hình:", ["9:16 (Dọc - TikTok, Reels)", "16:9 (Ngang - YouTube, Facebook)"]) else "16:9"
with col_time: target_duration_mins = 0.5 if "Bán Hàng" in selected_mode else st.number_input("⏱️ Thời lượng mong muốn (Phút):", min_value=0.5, max_value=30.0, value=1.0, step=0.5)

content_goal = "Sales & Conversion" if "Bán Hàng" in selected_mode else ("Brand Awareness" if "Doanh Nghiệp" in selected_mode else "Viral & Education")

# Xử lý Trigger Nút bấm (Tránh lỗi stale data của Streamlit)
if st.session_state.action_trigger:
    action = st.session_state.action_trigger
    param = st.session_state.action_param
    st.session_state.action_trigger, st.session_state.action_param = None, None
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    if action == "create_detail":
        st.toast(f"⏳ Đang dựng chi tiết kịch bản #{param}...", icon="🎬")
        with st.container(border=True):
            st.markdown(f"<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG XỬ LÝ: Đang dựng chi tiết phân cảnh cho kịch bản #{param}. Vui lòng đợi...</div>", unsafe_allow_html=True)
            try:
                create_scene_details_for_id(int(param), selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, selected_strategy)
                st.session_state.active_script_id = int(param)
                st.session_state.global_toast, st.session_state.global_toast_icon = f"Đã dựng thành công kịch bản #{param}!", "✅"
                st.session_state.scroll_to_top = True
                time.sleep(0.2); st.rerun() # Chỉ rerun khi THÀNH CÔNG
            except Exception as e: 
                st.error(f"❌ Lỗi: {e}")
                if st.button("🔄 Quay lại"): st.rerun()
                
    elif action == "clone_script":
        st.toast(f"⏳ Đang nhân bản biến thể cho kịch bản #{param}...", icon="🧬")
        with st.container(border=True):
            st.markdown(f"<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG XỬ LÝ: Đang nhân bản 5 biến thể độc đáo từ kịch bản #{param}. Vui lòng đợi...</div>", unsafe_allow_html=True)
            try:
                clone_script_id(int(param), selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, selected_strategy)
                st.session_state.global_toast, st.session_state.global_toast_icon = f"Đã nhân bản kịch bản #{param}!", "🧬"
                st.session_state.scroll_to_top = True
                time.sleep(0.2); st.rerun()
            except Exception as e: 
                st.error(f"❌ Lỗi: {e}")
                if st.button("🔄 Quay lại"): st.rerun()
                
    elif action == "generate_more":
        st.toast("⏳ Đang sáng tạo kịch bản mới...", icon="🧠")
        with st.container(border=True):
            st.markdown("<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG XỬ LÝ: Phân tích DNA để sáng tạo thêm 5 kịch bản mới. Vui lòng đợi...</div>", unsafe_allow_html=True)
            try:
                strat_to_use = param if param else selected_strategy
                add_five_scripts_continuation(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, strat_to_use)
                st.session_state.global_toast, st.session_state.global_toast_icon = "Đã bổ sung kịch bản mới!", "🧠"
                st.session_state.scroll_to_top = True
                time.sleep(0.2); st.rerun()
            except Exception as e: 
                st.error(f"❌ Lỗi: {e}")
                if st.button("🔄 Quay lại"): st.rerun()
    st.stop()

# ==============================================================================
# 10. KHU VỰC NHẬP LIỆU PHÂN TÍCH (BẢNG CẨM NANG ĐẦY ĐỦ 12 THỂ LOẠI)
# ==============================================================================
with st.expander("💡 Bấm vào đây để xem Bảng Gợi Ý Phối Hợp 'Thể Loại & Phong Cách'", expanded=False):
    st.markdown("""
    <div style="background-color: #f8fafc; padding: 16px; border-radius: 12px; border: 1.5px solid #e2e8f0; font-size: 0.95rem; color: #334155; margin-bottom: 5px;">
        <h4 style="color: #0f172a; margin-top: 0; margin-bottom: 12px; font-size: 1.05rem;">🎯 Cẩm Nang Phối Hợp Sáng Tạo Nội Dung Đa Vũ Trụ</h4>
        <ul style="padding-left: 20px; line-height: 1.8; margin-bottom: 0;">
            <li><b>🛒 TikTok Shop & Bán Hàng:</b> Phù hợp nhất với <code style="color: #e11d48;">Studio Tối Giản (Hiện đại, Sạch sẽ)</code>.</li>
            <li><b>👶 Mẹ & Bé & Cùng Con Học:</b> Tối ưu với <code style="color: #e11d48;">Hoạt Hình 3D (Kiểu Pixar / Disney)</code>.</li>
            <li><b>📺 TVC Quảng Cáo & Thương Hiệu Cao Cấp:</b> Cực kỳ tương thích với <code style="color: #e11d48;">Điện Ảnh Chân Thực (Người thật / Siêu thực 8K)</code>.</li>
            <li><b>🏡 Nhà Cửa, Kiến Trúc & Cảnh Quan:</b> Khuyên dùng <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> hoặc <code style="color: #e11d48;">Studio Tối Giản</code>.</li>
            <li><b>🌿 Du Lịch & Phong Cảnh Đất Nước:</b> Rất hợp với <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> hoặc <code style="color: #e11d48;">Tranh Thủy Mặc Cổ Phong</code>.</li>
            <li><b>🚗 Xe Cộ & Trải Nghiệm Lái:</b> Nên chọn <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> mang hơi hướng Cinematic.</li>
            <li><b>🍲 Ẩm Thực & Đời Sống:</b> Tôn lên vẻ đẹp món ăn với <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> hoặc <code style="color: #e11d48;">Studio Tối Giản</code>.</li>
            <li><b>📖 Đời Sống & Giáo Dục:</b> Khuyên dùng <code style="color: #e11d48;">Điện Ảnh Chân Thực</code> hoặc <code style="color: #e11d48;">Hoạt Hình 2D Ghibli</code>.</li>
            <li><b>🏛️ Lịch Sử & Tín Ngưỡng Di Sản:</b> Đặc biệt hợp với <code style="color: #e11d48;">Tranh Thủy Mặc Cổ Phong</code> hoặc Hoạt hình 2D/3D.</li>
            <li><b>🧘 Chữa Lành & Phong Cách Sống:</b> Tạo cảm giác nhẹ nhàng với <code style="color: #e11d48;">Hoạt Hình 2D Ghibli</code>.</li>
            <li><b>📢 Phóng Sự & Thông Điệp Xã Hội:</b> Sử dụng <code style="color: #e11d48;">Điện Ảnh Chân Thực</code>.</li>
            <li><b>🏢 Giới Thiệu Doanh Nghiệp:</b> Thể hiện sự chuyên nghiệp bằng <code style="color: #e11d48;">Điện Ảnh Chân Thực</code>.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
st.markdown("---")

input_text = st.text_area("✍️ Tóm tắt ý tưởng, chủ đề hoặc mô tả chi tiết dự án/sản phẩm (Ghi chú rõ thứ tự các ảnh nếu tải nhiều ảnh nhân vật):", height=80, key="main_input_context")

col_p_img, col_c_img = st.columns([1, 1])
with col_p_img: uploaded_files = st.file_uploader("📦 Tải ảnh Sản phẩm / Bối cảnh chính", type=["jpg", "jpeg", "png"], accept_multiple_files=True, label_visibility="collapsed", key=f"main_uploader_{st.session_state.file_uploader_key}")
with col_c_img: num_chars = st.number_input("👤 Số lượng Nhân vật tham chiếu", min_value=0, max_value=8, step=1, key="num_chars_input")

char_inputs = []
if num_chars > 0:
    with st.expander(f"🎭 HỒ SƠ DIỄN VIÊN ({num_chars}) - Kéo thả ảnh và Nhập vai trò", expanded=True):
        n_cols = 4 if num_chars > 2 else 2
        grid_cols = st.columns(n_cols)
        for i in range(num_chars):
            with grid_cols[i % n_cols]:
                with st.container(border=True):
                    st.markdown(f"<div style='color:#d90429; font-weight:800; font-size:14px; margin-bottom:5px;'>👤 Diễn viên {i+1}</div>", unsafe_allow_html=True)
                    c_role = st.text_input("Vai trò", key=f"c_role_{i}_{st.session_state.file_uploader_key}", placeholder="Vd: Mẹ 30 tuổi...", label_visibility="collapsed")
                    c_file = st.file_uploader("Ảnh", type=["jpg", "jpeg", "png"], key=f"c_img_{i}_{st.session_state.file_uploader_key}", label_visibility="collapsed")
                    if c_file and c_role.strip(): char_inputs.append({"id": i+1, "role": c_role.strip(), "file": c_file})

if st.button("🚀 Bắt Đầu Phân Tích Chi Tiết & Lên Kịch Bản", type="primary", use_container_width=True, disabled=not (input_text.strip() or uploaded_files or char_inputs)):
    st.toast("⏳ Đang kết nối phân tích DNA... Vui lòng đợi trong giây lát!", icon="🤖")
    with st.spinner("⏳ Đang phân tích DNA chuyên sâu và Gán vai diễn viên..."):
        try:
            st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
            st.session_state.current_input_context = input_text.strip() if input_text else "Phân tích trực tiếp từ hình ảnh đính kèm sản phẩm/dự án."
            safe_input_context = st.session_state.current_input_context.replace('"', "'").replace('\n', ' ')
            char_rules_str = generate_char_rules_string(st.session_state.character_profiles, "Bán Hàng" in selected_mode)
            
            prompt_text = f"""
            Phân tích siêu chuyên sâu chủ đề cho thể loại '{selected_mode}' - Chiến lược: '{selected_strategy}'. 
            Thông tin mô tả: "{safe_input_context}". {get_realtime_context()}

            QUY ĐỊNH ĐỘNG VỀ NHẬN DIỆN (CRITICAL):
            1. ĐỒNG BỘ GIỚI TÍNH: Giới tính `script_outfit_setup` PHẢI KHỚP với `gender` trong `voice_profile`.
            2. Về Giá cả: TUYỆT ĐỐI KHÔNG ĐƯA MỨC GIÁ CỤ THỂ BẰNG CON SỐ.

            BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON CHUẨN. BẠN PHẢI TẠO ĐỦ 5 OBJECT KỊCH BẢN (Tuyệt đối không dùng dấu ba chấm "..."):
            {{
              "content_analysis": {{
                "primary_target_audience": "Tệp khách hàng mục tiêu",
                "mechanical_and_accessories": "Kiểu dáng, chất liệu, kích thước",
                "customer_pain_points": "Nỗi đau khách hàng",
                "core_desires": "Mong muốn cốt lõi",
                "emotional_or_usp_hook": "Slogan, USP",
                "visual_physics_rules": "Quy chuẩn vật lý ánh sáng",
                "prompt_dna_lock": "Khóa thị giác đồng nhất"
              }},
              "script_outlines": [
                {{"id": 1, "title": "[Điền]", "setting_style": "[Điền]", "script_outfit_setup": "[Điền màu sắc đồ]", "angle": "[Điền]", "target_hook": "[Điền]", "recommended_scenes_count": "3 đến 4 cảnh", "voice_profile": {{"gender": "[Nam hoặc Nữ]", "tone": "năng lượng"}}}},
                {{"id": 2, "title": "[Điền]", "setting_style": "[Điền]", "script_outfit_setup": "[Điền màu sắc đồ]", "angle": "[Điền]", "target_hook": "[Điền]", "recommended_scenes_count": "3 đến 4 cảnh", "voice_profile": {{"gender": "[Nam hoặc Nữ]", "tone": "năng lượng"}}}},
                {{"id": 3, "title": "[Điền]", "setting_style": "[Điền]", "script_outfit_setup": "[Điền màu sắc đồ]", "angle": "[Điền]", "target_hook": "[Điền]", "recommended_scenes_count": "3 đến 4 cảnh", "voice_profile": {{"gender": "[Nam hoặc Nữ]", "tone": "năng lượng"}}}},
                {{"id": 4, "title": "[Điền]", "setting_style": "[Điền]", "script_outfit_setup": "[Điền màu sắc đồ]", "angle": "[Điền]", "target_hook": "[Điền]", "recommended_scenes_count": "3 đến 4 cảnh", "voice_profile": {{"gender": "[Nam hoặc Nữ]", "tone": "năng lượng"}}}},
                {{"id": 5, "title": "[Điền]", "setting_style": "[Điền]", "script_outfit_setup": "[Điền màu sắc đồ]", "angle": "[Điền]", "target_hook": "[Điền]", "recommended_scenes_count": "3 đến 4 cảnh", "voice_profile": {{"gender": "[Nam hoặc Nữ]", "tone": "năng lượng"}}}}
              ]
            }}
            LƯU Ý: KHÔNG DÙNG DẤU NGOẶC KÉP (\") BÊN TRONG CÁC VALUE. PHẢI ĐIỀN ĐỦ VÀO CÁC NGOẶC VUÔNG [...].
            """
            
            payload = []
            if uploaded_files:
                payload.append("ẢNH SẢN PHẨM / VẬT THỂ THAM CHIẾU:")
                for f in uploaded_files: payload.append(types.Part.from_bytes(data=f.getvalue(), mime_type=f.type or "image/jpeg"))
            if char_inputs:
                for c in char_inputs:
                    payload.append(f"ẢNH NHÂN VẬT THAM CHIẾU {c['id']} - VAI TRÒ: {c['role']}:")
                    payload.append(types.Part.from_bytes(data=c['file'].getvalue(), mime_type=c['file'].type or "image/jpeg"))
            payload.append(prompt_text)
            
            res = call_gemini_with_retry(payload, get_system_instructions(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, char_rules_str, selected_strategy, "Người dùng"))
            
            st.session_state.content_analysis = res.get("content_analysis")
            st.session_state.all_scripts = res.get("script_outlines", [])
            st.session_state.cloned_scripts, st.session_state.expanded_scripts, st.session_state.generated_details, st.session_state.active_script_id = [], [], {}, None
            st.session_state.scroll_to_top = True
            st.session_state.global_toast, st.session_state.global_toast_icon = "Đã phân tích DNA thành công!", "✅"
            time.sleep(0.1); st.rerun()
        except Exception as e: st.error(f"❌ Lỗi thực thi: {e}")

# ==============================================================================
# 11. HIỂN THỊ KẾT QUẢ VÀ BỐ CỤC CHIA CỘT THÔNG MINH
# ==============================================================================
if st.session_state.content_analysis and not st.session_state.action_trigger:
    st.divider()
    ca = st.session_state.content_analysis
    st.markdown(f"### 🔍 **Phân Tích DNA Chi Tiết Đa Tầng — [{selected_mode.upper()}]**")
    with st.container(border=True):
        st.markdown(f"**🎯 1. Chân dung Khách hàng & Nỗi đau:**<br><div style='line-height: 1.8;'>• <b>Tệp chính:</b> {ca.get('primary_target_audience', 'N/A')}<br>{format_analysis_field(ca.get('customer_pain_points', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(f"**🏭 2. Thông số Cốt lõi & Kích thước:**<br><div style='line-height: 1.8;'>{format_analysis_field(ca.get('mechanical_and_accessories', 'N/A'))}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(f"**💡 3. Mong muốn & USP/Slogan:**<br><div style='line-height: 1.8;'>• <b>Giá trị:</b> {ca.get('core_desires', 'N/A')}<br>• <b>Slogan:</b> {ca.get('emotional_or_usp_hook', 'N/A')}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(f"**⚙️ 4. Quy chuẩn bối cảnh / Vật lý điện ảnh:**<br><div style='line-height: 1.8;'>{format_analysis_field(ca.get('visual_physics_rules', 'N/A'))}</div>", unsafe_allow_html=True)
    st.markdown("**📌 Chuỗi khóa thị giác (Visual DNA Lock):**")
    st.code(str(ca.get('prompt_dna_lock', 'N/A')).replace('<br>', ' ').replace('<b>', '').replace('</b>', ''), language="text")

all_combined_scripts_list = (st.session_state.all_scripts or []) + (st.session_state.cloned_scripts or []) + (st.session_state.expanded_scripts or [])

# --- GIAI ĐOẠN 1: MÀN HÌNH DANH SÁCH TỔNG QUAN ---
if all_combined_scripts_list and st.session_state.active_script_id is None and not st.session_state.action_trigger:
    st.divider()
    completed_scripts, pending_scripts = [], []
    for sc in all_combined_scripts_list:
        if int(sc.get("id", 0)) in st.session_state.generated_details: completed_scripts.append(sc)
        else: pending_scripts.append(sc)

    st.markdown("### 🎬 **1. Kịch Bản Đã Hoàn Thiện Chi Tiết (Sẵn Sàng Sản Xuất)**")
    if not completed_scripts: st.info("💡 Chưa có kịch bản nào được tạo chi tiết. Hãy chọn một ý tưởng ở bên dưới để bắt đầu dựng cảnh!")
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
                        st.session_state.action_trigger, st.session_state.action_param = "view_detail", sc_id
                        st.session_state.active_script_id = sc_id
                        st.session_state.scroll_to_top = True; st.rerun()
                with col_btn2:
                    if st.button("🚀 Nhân bản 5 bản", key=f"btn_clone_v1_main_{sc_id}", type="primary", use_container_width=True):
                        st.session_state.action_trigger, st.session_state.action_param = "clone_script", sc_id
                        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### ⏳ **2. Kịch Bản Đang Chờ Tạo Chi Tiết (Ý Tưởng Thực Chiến)**")
    if not pending_scripts: st.success("🎉 Tuyệt vời! Tất cả các kịch bản trong danh sách đã được tạo chi tiết thành công.")
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
                        st.session_state.action_trigger, st.session_state.action_param = "create_detail", sc_id
                        st.rerun()

    # --- KHU VỰC GỌI THÊM CÁC TÌNH HUỐNG MỚI ĐỘNG (GIAI ĐOẠN 1) ---
    st.markdown("---")
    st.markdown("### 🔄 Gọi Thêm Kịch Bản Mới (Mở Rộng Ý Tưởng)")
    if "Bán Hàng" in selected_mode or "Mẹ & Bé" in selected_mode:
        cb1, cb2, cb3 = st.columns(3)
        with cb1:
            if st.button("➕ 5 Kịch bản Hỗn hợp", key="gen_mix_p1", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Hỗn hợp (2 Trực diện + 3 Drama)"; st.rerun()
        with cb2:
            if st.button("➕ 5 Kịch bản Drama/Giải trí", key="gen_drama_p1", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "100% Drama / Shoppertainment"; st.rerun()
        with cb3:
            if st.button("➕ 5 Kịch bản Trực diện", key="gen_hard_p1", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "100% Bán hàng trực diện (Hard Sale)"; st.rerun()
    elif "Lịch Sử" in selected_mode:
        cb1, cb2 = st.columns(2)
        with cb1:
            if st.button("➕ 5 Kịch bản Phim Tài Liệu", key="gen_doc_p1", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Phim Tài liệu / Kể chuyện lịch sử (Trang nghiêm)"; st.rerun()
        with cb2:
            if st.button("➕ 5 Kịch bản Hoạt Hình Dã Sử", key="gen_ani_p1", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Phim Hoạt hình Dã sử (Có Tranh cãi / Hành động / Chiến tranh)"; st.rerun()
    else:
        if st.button("➕ Gọi Thêm 5 Kịch Bản Mới", key="gen_def_p1", type="primary", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", selected_strategy; st.rerun()

# --- GIAI ĐOẠN 2: MÀN HÌNH CHI TIẾT & ĐIỀU HƯỚNG CHIA CỘT ---
if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details and not st.session_state.action_trigger:
    st.divider()
    if st.button("⬅️ Quay lại danh sách kịch bản tổng", key="btn_back_to_list_main"):
        st.session_state.active_script_id = None
        st.session_state.scroll_to_top = True
        st.session_state.global_toast, st.session_state.global_toast_icon = "Đã quay lại danh sách kịch bản!", "⬅️"
        st.rerun()

    raw_active_data = st.session_state.generated_details[st.session_state.active_script_id]
    active_script = raw_active_data[0] if isinstance(raw_active_data, list) and len(raw_active_data) > 0 else (raw_active_data if isinstance(raw_active_data, dict) else {})
    vp = active_script.get("voice_profile", {"gender": "Nữ", "tone": "Truyền cảm"}) if isinstance(active_script.get("voice_profile"), dict) else {"gender": "Nữ", "tone": "Truyền cảm"}

    st.markdown(f"### 🎬 **KỊCH BẢN CHI TIẾT: {str(active_script.get('title', 'Kịch bản')).upper()}**")
    st.info(f"⏱️ Thời lượng: **{active_script.get('total_estimated_duration', '24s')}** | 🎙️ Giọng: **{vp.get('gender', 'Nữ')} ({vp.get('tone', 'Truyền cảm')})** | 👔 Trang phục: **{active_script.get('script_outfit_setup', 'Đồng phục')}** | 📐 Khung hình: **{selected_aspect}**")

    # HIỂN THỊ CÁC PHÂN CẢNH Ở TRÊN CÙNG
    scenes_list = active_script.get("scenes", []) if isinstance(active_script, dict) else []
    if isinstance(scenes_list, dict): scenes_list = [scenes_list]
    for idx, scene in enumerate(scenes_list, start=1):
        if not isinstance(scene, dict): continue
        dur = scene.get("duration", "6s")
        st.markdown(f"#### **📍 Phân cảnh {idx} ({dur}) — [ {scene.get('transition_type', 'Cắt cứng')} ]**")
        st.markdown(f"🏛️ **Bối cảnh & Miêu tả:** *{scene.get('scene_setting')}*")
        st.markdown(f"**🎙️ Đạo diễn diễn xuất:** *{scene.get('voice_director_vn')}*")
        
        # Hỗ trợ hiển thị đa nhân vật thoại (dialogues) hoặc thoại đơn (voiceover_vi)
        dialogues_data = scene.get("dialogues", [])
        if dialogues_data and isinstance(dialogues_data, list):
            st.markdown("**💬 Đối thoại đa nhân vật:**")
            for d in dialogues_data:
                speaker_name = d.get("speaker", "Nhân vật")
                line = d.get("dialogue", "")
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;• 🗣️ <b>{speaker_name}:</b> `\"{line}\"`", unsafe_allow_html=True)
        else:
            legacy_voice = scene.get("voiceover_vi", "")
            st.markdown(f"**💬 Lời thuyết minh:** `\"{legacy_voice}\"`")
        
        img_p = scene.get('image_prompt', '')
        if img_p:
            st.markdown(f"**🖼️ Prompt Ảnh (Imagen 3 - {selected_aspect}):**")
            if "dùng ảnh cuối của cảnh trước" in img_p.lower() or "dùng frame ảnh cuối" in img_p.lower():
                st.info("🔄 Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu cho video để nối liền mạch hành động (Match Cut).")
            else:
                st.code(img_p, language="text")
                safe_copy_button(img_p, f"📋 Sao Chép Prompt Ảnh Cảnh {idx}")
            
        vid_p = scene.get('video_prompt', '')
        st.markdown(f"**🎥 Prompt Video (Veo 3 - Thuyết minh):**")
        st.code(vid_p, language="text")
        safe_copy_button(vid_p, f"📋 Sao Chép Prompt Video Cảnh {idx}")
        st.markdown("---")

        # Thêm nút bấm hỗ trợ xuất nhanh lời thoại từng cảnh
        dialogues_data = scene.get("dialogues", [])
        if dialogues_data and isinstance(dialogues_data, list):
            st.markdown("**💬 Đối thoại đa nhân vật:**")
            full_scene_voice = ""
            for d in dialogues_data:
                speaker_name = d.get("speaker", "Nhân vật")
                line = d.get("dialogue", "")
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;• 🗣️ <b>{speaker_name}:</b> `\"{line}\"`", unsafe_allow_html=True)
                full_scene_voice += f"{speaker_name}: {line} "
            
            # Nút copy nhanh toàn bộ đoạn hội thoại của cảnh này để làm lồng tiếng / voiceover
            safe_copy_button(full_scene_voice.strip(), f"📋 Copy Toàn Bộ Thoại Cảnh {idx}")

    # CHIA CỘT HIỂN THỊ DANH SÁCH BÊN DƯỚI ĐỂ ĐIỀU HƯỚNG NHANH
    col_left, col_right = st.columns([1.1, 0.9])
    
    with col_left:
        st.markdown("""
        <div class="custom-card" style="background: #f0fdf4; border-color: #86efac;">
            <div style="color: #166534; font-weight: 800; font-size: 1.1rem; margin-bottom: 4px;">🎬 Kịch Bản Đã Hoàn Thiện Khác</div>
            <div style="font-size: 0.82rem; color: #15803d;">Chọn để xem lại hoặc nhân bản nhanh</div>
        </div>
        """, unsafe_allow_html=True)
        
        completed_scripts_in_detail = [sc for sc in all_combined_scripts_list if int(sc.get("id", 0)) in st.session_state.generated_details]
        if not completed_scripts_in_detail: st.caption("Chưa có kịch bản nào khác được tạo.")
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
                                st.session_state.scroll_to_top = True; st.rerun()
                        else:
                            st.markdown("<div style='text-align: center; color: #15803d; font-size: 12px; font-weight: 700; padding: 6px;'>Đang hiển thị</div>", unsafe_allow_html=True)
                    with c_clone:
                        if st.button("🚀 Nhân bản", key=f"dt_clone_detail_{it_id}", type="primary", use_container_width=True):
                            st.session_state.action_trigger, st.session_state.action_param = "clone_script", it_id
                            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="custom-card">
            <div class="card-title-add">➕ Vùng Gọi Thêm Kịch Bản Mới</div>
            <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 8px;">Mở rộng thêm ý tưởng từ dữ liệu DNA đã phân tích.</div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- KHU VỰC GỌI THÊM ĐỘNG BÊN TRONG CỘT TRÁI (GIAI ĐOẠN 2) ---
        if "Bán Hàng" in selected_mode or "Mẹ & Bé" in selected_mode:
            cb1, cb2, cb3 = st.columns(3)
            with cb1:
                if st.button("➕ Hỗn hợp", key="gen_mix_p2", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Hỗn hợp (2 Trực diện + 3 Drama)"; st.rerun()
            with cb2:
                if st.button("➕ Drama", key="gen_drama_p2", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "100% Drama / Shoppertainment"; st.rerun()
            with cb3:
                if st.button("➕ Trực diện", key="gen_hard_p2", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "100% Bán hàng trực diện (Hard Sale)"; st.rerun()
        elif "Lịch Sử" in selected_mode:
            cb1, cb2 = st.columns(2)
            with cb1:
                if st.button("➕ Phim Tài Liệu", key="gen_doc_p2", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Phim Tài liệu / Kể chuyện lịch sử (Trang nghiêm)"; st.rerun()
            with cb2:
                if st.button("➕ Hoạt Hình Dã Sử", key="gen_ani_p2", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Phim Hoạt hình Dã sử (Có Tranh cãi / Hành động / Chiến tranh)"; st.rerun()
        else:
            if st.button("➕ Gọi Thêm 5 Kịch Bản Mới", key="gen_def_p2", type="primary", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", selected_strategy; st.rerun()

    with col_right:
        st.markdown("""
        <div class="custom-card" style="background: #f8fafc;">
            <div style="color: #0f172a; font-weight: 800; font-size: 1.1rem; margin-bottom: 10px;">📋 Kịch Bản Chưa Tạo Chi Tiết</div>
        </div>
        """, unsafe_allow_html=True)
        pending_scripts_in_detail = [item for item in all_combined_scripts_list if int(item.get("id", 0)) not in st.session_state.generated_details]
        if not pending_scripts_in_detail: st.success("🎉 Tuyệt vời! Tất cả các kịch bản trong danh sách đã được tạo chi tiết thành công.")
        else:
            for item in pending_scripts_in_detail:
                it_id = int(item.get("id", 0))
                with st.container(border=True):
                    st.markdown(f"**#{it_id}. {item.get('title')}** — <span class='badge-pending'>CHƯA TẠO</span>", unsafe_allow_html=True)
                    st.caption(f"🏛️ {item.get('setting_style')}")
                    if st.button("✨ Tạo chi tiết ngay", key=f"nav_sc_detail_{it_id}", use_container_width=True):
                        st.session_state.action_trigger, st.session_state.action_param = "create_detail", it_id
                        st.rerun()
