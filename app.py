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
st.set_page_config(page_title="Universal AI Video Studio Pro", page_icon="🎬", layout="wide")

st.markdown("""
<style>
    .header-container { text-align: center; padding: 1.2rem 1rem 1.8rem 1rem; margin-bottom: 1rem; background: radial-gradient(circle, rgba(255,75,75,0.08) 0%, rgba(255,255,255,0) 70%); border-radius: 16px; }
    .main-title { font-size: 2.35rem !important; font-weight: 900 !important; background: linear-gradient(90deg, #ff0050 0%, #ff5252 50%, #ff7300 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem !important; line-height: 1.25 !important; letter-spacing: -0.5px; }
    .sub-title { font-size: 1.12rem !important; font-weight: 500 !important; color: #4a5568 !important; margin-top: 0.2rem; }
    .header-badge { display: inline-block; background: #fee2e2; color: #b91c1c; font-size: 0.8rem; font-weight: 800; padding: 3px 12px; border-radius: 9999px; margin-bottom: 0.5rem; letter-spacing: 0.5px; border: 1px solid #fca5a5; }
    .custom-card { background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 18px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
    div[data-testid="stButton"] > button { width: 100% !important; border-radius: 8px !important; font-weight: 700 !important; border: none !important; transition: all 0.25s ease-in-out !important; }
    div[data-testid="stButton"] > button[kind="primary"] { background: linear-gradient(135deg, #e63946 0%, #d90429 100%) !important; color: #ffffff !important; box-shadow: 0 4px 10px rgba(230, 57, 70, 0.4) !important; padding: 0.6rem 1rem !important; }
    .badge-pending { color: #d97706; font-weight: 700; background: #fef3c7; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
    .badge-ready { color: #15803d; font-weight: 700; background: #dcfce7; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
    .support-box { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1.5px solid #86efac; border-radius: 12px; padding: 12px; text-align: center; margin-top: 15px; }
    .loading-pulse { animation: pulse 1.5s infinite ease-in-out; color: #d90429; font-weight: 800; text-align: center; padding: 25px; background: #fef2f2; border: 2px dashed #fca5a5; border-radius: 12px; margin: 20px 0; }
    @keyframes pulse { 0% { transform: scale(0.98); opacity: 0.8; } 50% { transform: scale(1.02); opacity: 1; } 100% { transform: scale(0.98); opacity: 0.8; } }
</style>
""", unsafe_allow_html=True)

# Khởi tạo API
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
if not api_key: st.error("Chưa cấu hình khóa GEMINI_API_KEY."); st.stop()
client = genai.Client(api_key=api_key)

ACCOUNTS_FILE = "accounts.json"
ADMIN_EMAIL = "binhnguyenmedia.vn@gmail.com"
ALL_MODULES = ["🛒 TikTok Shop & Bán Hàng", "👶 Mẹ & Bé & Cùng Con Học", "📺 TVC Quảng Cáo & Thương Hiệu", "🏡 Nhà Cửa, Kiến Trúc", "🌿 Du Lịch & Phong Cảnh", "🚗 Xe Cộ & Trải Nghiệm Lái", "🍲 Ẩm Thực & Đời Sống", "📖 Đời Sống & Giáo Dục", "🏛️ Lịch Sử & Tín Ngưỡng Di Sản", "🧘 Chữa Lành & Phong Cách Sống", "📢 Phóng Sự & Thông Điệp Xã Hội", "🏢 Giới Thiệu Doanh Nghiệp"]

def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {ADMIN_EMAIL: {"contact": ADMIN_EMAIL, "roles": ["Tất cả thể loại"], "expires_at": "2099-12-31"}}

# Khởi tạo Session State
for k, v in [("content_analysis", None), ("all_scripts", []), ("cloned_scripts", []), ("expanded_scripts", []), ("generated_details", {}), ("active_script_id", None), ("projects_library", {}), ("licensed_accounts", load_accounts()), ("is_logged_in", False), ("current_user_email", ""), ("active_project_title", "Chiến dịch mới"), ("file_uploader_key", 0), ("scroll_to_top", False), ("action_trigger", None), ("action_param", None), ("character_profiles", [])]:
    if k not in st.session_state: st.session_state[k] = v

if st.session_state.scroll_to_top:
    components.html("<script>window.parent.scrollTo({top: 0, behavior: 'smooth'});</script>", height=0)
    st.session_state.scroll_to_top = False

# ==============================================================================
# HÀM XỬ LÝ LÕI VÀ TIỆN ÍCH (UTILITIES)
# ==============================================================================
def process_login(login_val):
    val = login_val.strip()
    if not val: return
    if val == ADMIN_EMAIL or val in st.session_state.licensed_accounts:
        if val != ADMIN_EMAIL:
            exp = st.session_state.licensed_accounts[val].get("expires_at", "2099-12-31")
            try:
                if datetime.now() > datetime.strptime(exp, "%Y-%m-%d"): st.error(f"❌ Tài khoản hết hạn {exp}!"); return
            except: pass
        st.session_state.is_logged_in, st.session_state.current_user_email = True, val; st.rerun()
    else: st.error("❌ Tài khoản chưa được cấp quyền!")

def format_analysis_field(field_val) -> str:
    if isinstance(field_val, dict): return "<br>".join([f"• <b>{str(k).replace('_', ' ').title()}:</b> {str(v)}" for k, v in field_val.items()])
    elif isinstance(field_val, list): return "<br>".join([f"• {str(i)}" for i in field_val])
    text = re.sub(r'(?i)\bnỗi đau\b\s*[:\.-]?', '', str(field_val).strip().replace('<b>', '').replace('</b>', ''))
    return "".join([f"<div style='margin-top:4px;'>• {l.strip()}</div>" if not l.strip().startswith('•') else f"<div>{l.strip()}</div>" for l in text.split('<br>') if l.strip()])

# Dùng replace an toàn thay vì regex phức tạp để tránh lỗi SyntaxError unterminated string
def clean_and_parse_json(text_content):
    cleaned = text_content.replace("```json", "").replace("```", "").strip()
    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    if match: cleaned = match.group(0)
    try: return json.loads(cleaned, strict=False)
    except: return ast.literal_eval(cleaned.replace('true', 'True').replace('false', 'False').replace('null', 'None'))

def safe_copy_button(text_to_copy: str, label: str):
    b64 = base64.b64encode(text_to_copy.encode('utf-8')).decode('utf-8')
    components.html(f"<button onclick='navigator.clipboard.writeText(decodeURIComponent(escape(atob(\"{b64}\"))));this.innerText=\"✅ Đã copy!\";setTimeout(()=>this.innerText=\"{label}\",2000);' style='background:linear-gradient(135deg,#ff4b4b,#ff7300);color:white;border:none;padding:8px 16px;font-size:13px;font-weight:700;border-radius:6px;cursor:pointer;width:100%;'>{label}</button>", height=40)

def get_realtime_context():
    now = datetime.now()
    seasons = {2:"Xuân",3:"Xuân",4:"Xuân", 5:"Hè",6:"Hè",7:"Hè", 8:"Thu",9:"Thu",10:"Thu", 11:"Đông",12:"Đông",1:"Đông"}
    return f"THỜI GIAN: Tháng {now.month}/{now.year} (Mùa {seasons.get(now.month)}). Phân tích khách hàng theo mùa vụ nếu phù hợp."

# ==============================================================================
# HỆ THỐNG PROMPT & ĐIỀU KHIỂN AI
# ==============================================================================
def get_strategy_rules(mode, strategy, aud):
    r = f"- ĐỐI TƯỢNG CỐT LÕI: Nhắm thẳng vào {aud}.\n"
    if "Bán Hàng" in mode or "Mẹ & Bé" in mode:
        if "Hỗn hợp" in strategy: r += "- CƠ CẤU: Trực diện (Review) + Shoppertainment (Drama đời sống bẻ lái chốt sale).\n"
        elif "Drama" in strategy: r += "- CƠ CẤU 100% DRAMA: Tình huống mâu thuẫn gia đình/đời sống. Bẻ lái lồng sản phẩm.\n"
        else: r += "- CƠ CẤU 100% TRỰC DIỆN: Kho xưởng, đập hộp, test sản phẩm khốc liệt.\n"
        r += "- TỐI ƯU CẢNH: Yêu cầu '3-4 phân cảnh' để tiết kiệm Credit. CẤM TỪ 'LIVESTREAM'. KHÔNG DÙNG GIÁ TIỀN SỐ.\n"
    elif "Lịch Sử" in mode and "Dã sử" in strategy:
        r += "- CƠ CẤU DÃ SỬ: Tranh cãi, hành động. KỸ THUẬT: BẮT BUỘC dùng Shot/Reverse Shot (Cắt luân phiên) hoặc Góc chéo vai. Cấm 2 người đánh nhau trực diện trong 1 góc rộng. Dùng Bóng đen (Silhouettes) cho quân đội.\n"
    return r

def get_sys_inst(mode, style, aspect, goal, dur, rules, strat, aud):
    d_rule = "BẮT BUỘC CHỈ TẠO 3 ĐẾN 4 PHÂN CẢNH (Mỗi cảnh 4s, 6s, 8s)." if dur <= 0.5 else f"TỔNG ĐỘ DÀI {int(dur * 60)} GIÂY."
    return f"""BẠN LÀ TỔNG ĐẠO DIỄN CHO IMAGEN 3 VÀ VEO 3. PHONG CÁCH: {style.upper()} | KHUNG HÌNH: {"9:16 vertical" if aspect=="9:16" else "16:9 widescreen"}. {d_rule}
    🛑 QUY TẮC CRITICAL:
    1. TRẢ VỀ JSON HỢP LỆ. DÙNG NGOẶC ĐƠN (') TRONG CHUỖI. KHÔNG XUỐNG DÒNG.
    2. QUỐC TỊCH: Luôn chèn "Vietnamese".
    {rules}
    3. CẤM HIỂN THỊ UI/GIỎ HÀNG. 4. KHÔNG CHE KHUẤT (NO OCCLUSION): image_prompt ép "product is fully visible, strictly NO hands obscuring". video_prompt ép "product maintains rigid structural integrity, action ends with product fully visible and unoccluded".
    5. {get_strategy_rules(mode, strat, aud)}
    6. VOICE PACING & THOẠI SẠCH: 4s(12-14 từ); 6s(18-21 từ); 8s(24-28 từ). Lời thoại voiceover_vi PHẢI SẠCH, TUYỆT ĐỐI KHÔNG chứa ngoặc đơn (VD: (Cười)) và KHÔNG giá tiền.
    7. SFX: Âm thanh nền (sizzling meat...) BẮT BUỘC miêu tả bằng tiếng Anh trong video_prompt."""

def get_char_rules(profiles, is_sales):
    if not profiles: return "BẮT BUỘC CÓ NHÂN VẬT."
    r = "KHÓA KHUÔN MẶT:\n"
    for p in profiles: r += f"   - Nhân vật {p['id']}: 'Character {p['id']} ({p['role']}) wearing [trang_phục] and featuring exact identity of reference image {p['id']}'.\n"
    if is_sales: r += "   - ĐỒNG NHẤT 100%: GIỮ NGUYÊN MÀU SẮC TRANG PHỤC TRONG MỌI CẢNH.\n"
    return r

def call_ai(payload, sys_inst):
    for _ in range(3):
        try: return clean_and_parse_json(client.models.generate_content(model="gemini-3.6-flash", contents=payload, config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json")).text)
        except Exception: time.sleep(3)
    raise Exception("Lỗi kết nối Gemini API.")

def get_json_template_5_scripts(start_id, key_name="script_outlines"):
    objs = [f'{{"id": {start_id+i}, "title": "[Tên]", "setting_style": "[Bối cảnh]", "script_outfit_setup": "[Đồ]", "angle": "[Góc]", "target_hook": "[Hook]", "recommended_scenes_count": "3-4 cảnh", "voice_profile": {{"gender": "[Nam/Nữ]", "tone": "năng lượng"}}}}' for i in range(5)]
    return f'{{ "{key_name}": [\n' + ",\n".join(objs) + '\n] }'

# ==============================================================================
# HÀM XỬ LÝ LÕI KỊCH BẢN (CREATE/CLONE)
# ==============================================================================
def create_scene_details(t_id, mode, style, aspect, goal, dur, strat):
    all_sc = st.session_state.all_scripts + st.session_state.expanded_scripts + st.session_state.cloned_scripts
    out = next((s for s in all_sc if s.get("id") == t_id), None)
    if not out: return
    g_vi = "Nữ" if "nữ" in str(out.get("voice_profile", {})).lower() else "Nam"
    g_en = "female" if g_vi == "Nữ" else "male"
    
    ctx = st.session_state.get("current_input_context", "").replace('"', "'")
    aud = st.session_state.get("content_analysis", {}).get("primary_target_audience", "Người dùng")
    c_rules = get_char_rules(st.session_state.get("character_profiles", []), "Bán Hàng" in mode)
    
    prompt = f"""
    ID {t_id}: {out.get('title')}. Bối cảnh: {out.get('setting_style')}. ĐỒ: {out.get('script_outfit_setup')}. GIỚI TÍNH: {g_vi} ({g_en}). CHIẾN LƯỢC: {strat}
    CRITICAL: 1. Prompt Anh BẮT BUỘC dùng '{g_en} character'. KHÔNG dùng tên riêng 'Nam/Nữ'.
    2. MATCH CUT: image_prompt CHỈ GHI ĐÚNG 1 CÂU TIẾNG VIỆT: "Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu cho video".
    3. THOẠI SẠCH 100%: KHÔNG NGOẶC ĐƠN, KHÔNG GIÁ TIỀN.
    TẠO TỐI THIỂU 3-4 SCENE, ĐIỀN ĐỦ VÀO [...], KHÔNG DÙNG DẤU BA CHẤM:
    {{
      "id": {t_id}, "title": "{out.get('title')}", "setting_style": "{out.get('setting_style')}", "script_outfit_setup": "{out.get('script_outfit_setup')}", "total_estimated_duration": "24s",
      "voice_profile": {{"gender": "{g_vi}", "tone": "nhịp độ nhanh"}},
      "scenes": [
        {{ "scene_number": 1, "duration": "8s", "scene_setting": "[Mô tả]", "transition_type": "Mở đầu", "voice_director_vn": "[Cảm xúc]", "voiceover_vi": "[Thoại sạch không ngoặc đơn 26 từ]", "image_prompt": "[Prompt tiếng Anh chứa {g_en} character và No Occlusion rule]", "video_prompt": "Audio: {g_en} character speaking... Background ambient sound: [Tiếng ồn]... Visual: Cinematic... Reading: [Thoại]... Product maintains rigid structural integrity, action ends with product fully visible and unoccluded." }},
        {{ "scene_number": 2, "duration": "6s", "scene_setting": "[Mô tả]", "transition_type": "Cắt cứng (Hard Cut)", "voice_director_vn": "[Cảm xúc]", "voiceover_vi": "[Thoại 20 từ nối mạch]", "image_prompt": "[Prompt tiếng Anh chứa {g_en} character]", "video_prompt": "[Prompt Video tiếng Anh...]" }},
        {{ "scene_number": 3, "duration": "8s", "scene_setting": "[Mô tả]", "transition_type": "Nối liền mạch (Match Cut)", "voice_director_vn": "[Cảm xúc]", "voiceover_vi": "[Thoại chốt sale 26 từ]", "image_prompt": "Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu cho video", "video_prompt": "[Prompt Video tiếng Anh...]" }}
      ]
    }}
    """
    res = call_ai([prompt], get_sys_inst(mode, style, aspect, goal, dur, c_rules, strat, aud))
    st.session_state.generated_details[t_id] = res[0] if isinstance(res, list) else res

def add_or_clone_scripts(mode, style, aspect, goal, dur, strat, is_clone=False, t_id=None):
    cur_len = len(st.session_state.all_scripts + st.session_state.expanded_scripts + st.session_state.cloned_scripts)
    c_rules = get_char_rules(st.session_state.get("character_profiles", []), "Bán Hàng" in mode)
    aud = st.session_state.get("content_analysis", {}).get("primary_target_audience", "Người dùng")
    
    base_p = f"TẠO THÊM 5 KỊCH BẢN (id {cur_len+1} đến {cur_len+5}). CRITICAL: Giới tính `script_outfit_setup` KHỚP `gender`. KHÔNG DÙNG GIÁ TIỀN."
    if is_clone: base_p = f"Dựa trên kịch bản gốc: {json.dumps(st.session_state.generated_details[t_id], ensure_ascii=False)}. " + base_p
    
    prompt = base_p + "\nXUẤT ĐẦY ĐỦ 5 OBJECT THEO JSON MẪU (THAY THẾ [...], KHÔNG DÙNG DẤU BA CHẤM):\n" + get_json_template_5_scripts(cur_len+1, "cloned_outlines" if is_clone else "script_outlines")
    res = call_ai([prompt], get_sys_inst(mode, style, aspect, goal, dur, c_rules, strat, aud))
    
    key = "cloned_outlines" if is_clone else "script_outlines"
    news = res.get(key, [])
    for i, sc in enumerate(news): sc["id"] = cur_len + i + 1
    if is_clone: st.session_state.cloned_scripts.extend(news)
    else: st.session_state.expanded_scripts.extend(news)

# ==============================================================================
# SIDEBAR UI (QUẢN LÝ DỰ ÁN)
# ==============================================================================
with st.sidebar:
    if not st.session_state.is_logged_in:
        st.markdown("### 🔐 Đăng Nhập")
        with st.form("login"):
            em = st.text_input("Email:")
            if st.form_submit_button("Vào Hệ Thống"): process_login(em)
    else:
        st.markdown("### 🗂️ Quản Lý Dự Án")
        if st.button("➕ Dự Án Mới", type="primary"):
            st.session_state.content_analysis = None; st.session_state.active_script_id = None; st.session_state.generated_details = {}
            for k in ["all_scripts", "cloned_scripts", "expanded_scripts", "character_profiles"]: st.session_state[k] = []
            st.session_state.file_uploader_key += 1; st.session_state.scroll_to_top = True; st.rerun()
            
        p_name = st.text_input("Tên dự án:", st.session_state.active_project_title)
        c1, c2 = st.columns(2)
        if c1.button("💾 Lưu"):
            st.session_state.projects_library[f"p_{time.time()}"] = {"title": p_name, "mode": st.session_state.get("selected_mode"), "analysis": st.session_state.content_analysis, "scripts": st.session_state.all_scripts, "details": st.session_state.generated_details}
            st.toast("✅ Đã lưu!")
        c2.download_button("📥 Tải", json.dumps({"title": p_name, "analysis": st.session_state.content_analysis, "scripts": st.session_state.all_scripts, "details": st.session_state.generated_details}, ensure_ascii=False), f"{p_name}.json", "application/json")
        
        up_file = st.file_uploader("📤 Mở file", type=["json"], label_visibility="collapsed")
        if up_file:
            data = json.loads(up_file.getvalue())
            st.session_state.content_analysis, st.session_state.all_scripts = data.get("analysis"), data.get("scripts", [])
            st.session_state.generated_details = {int(k): v for k, v in data.get("details", {}).items()}
            st.session_state.active_script_id = None; st.session_state.scroll_to_top = True; st.rerun()

        if st.session_state.current_user_email == ADMIN_EMAIL:
            st.markdown("---"); st.markdown("### ⚙️ Admin")
            with st.form("admin"):
                acc = st.text_input("Cấp quyền Email:")
                if st.form_submit_button("Lưu"):
                    st.session_state.licensed_accounts[acc.strip()] = {"expires_at": "2099-12-31", "roles": ALL_MODULES}
                    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f: json.dump(st.session_state.licensed_accounts, f)
                    st.rerun()
        
        st.markdown("---")
        st.markdown("""<div class="support-box"><b style="color:#166534;">💬 Hỗ Trợ Dịch Vụ</b><div style="display:flex; justify-content:center; gap:5px; margin-top:5px;"><a href="[https://zalo.me/0968484369](https://zalo.me/0968484369)" style="background:#0068ff; color:white; padding:5px; border-radius:5px; font-size:11px; text-decoration:none;">Zalo</a><a href="[https://facebook.com/binhnguyenmedia.vn](https://facebook.com/binhnguyenmedia.vn)" style="background:#0866ff; color:white; padding:5px; border-radius:5px; font-size:11px; text-decoration:none;">FB</a><a href="[https://tiktok.com/@binhnguyenmedia](https://tiktok.com/@binhnguyenmedia)" style="background:#000; color:white; padding:5px; border-radius:5px; font-size:11px; text-decoration:none;">TikTok</a></div><div style="margin-top:5px; font-weight:bold; font-size:12px; color:#166534;">Hotline: 096 8484 369</div></div>""", unsafe_allow_html=True)
        if st.button("🚪 Đăng Xuất"): st.session_state.is_logged_in = False; st.rerun()

# ==============================================================================
# HEADER & MAIN UI
# ==============================================================================
st.markdown("""<div class="header-container"><div class="header-badge">🌟 STUDIO VIDEO AI ĐA NĂNG TOÀN DIỆN</div><div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div></div>""", unsafe_allow_html=True)
if not st.session_state.is_logged_in: st.info("👈 Vui lòng đăng nhập."); st.stop()

roles = st.session_state.licensed_accounts.get(st.session_state.current_user_email, {}).get("roles", [])
modules = ALL_MODULES if "Tất cả thể loại" in roles else [m for m in ALL_MODULES if m in roles]

cm, cs = st.columns([1.5, 1])
with cm: sel_mode = st.selectbox("🎯 Thể Loại:", modules, key="selected_mode")

if "Bán Hàng" in sel_mode or "Mẹ & Bé" in sel_mode: strats = ["Hỗn hợp (2 Trực diện + 3 Drama)", "100% Drama / Shoppertainment", "100% Bán hàng trực diện (Hard Sale)"]
elif "Lịch Sử" in sel_mode: strats = ["Phim Hoạt hình Dã sử (Có Tranh cãi / Hành động / Chiến tranh)", "Phim Tài liệu / Kể chuyện lịch sử (Trang nghiêm)"]
else: strats = ["Kể chuyện thương hiệu / Phóng sự", "Trình diễn hình ảnh", "Viral / Bắt trend", "Chia sẻ kiến thức"]

with cs: sel_style = st.selectbox("🎨 Phong Cách:", ["Điện Ảnh Chân Thực", "Hoạt Hình 3D", "Hoạt Hình 2D", "Tranh Thủy Mặc", "Cyberpunk", "Studio Tối Giản"])

cst, cr, ct = st.columns([1.5, 1, 1])
with cst: sel_strat = st.selectbox("🧠 Chiến lược:", strats)
with cr: sel_aspect = "9:16" if "9:16" in st.selectbox("Tỷ lệ:", ["9:16 (Dọc)", "16:9 (Ngang)"]) else "16:9"
with ct: t_dur = 0.5 if "Bán Hàng" in sel_mode else st.number_input("⏱️ Phút:", 0.5, 30.0, 1.0, 0.5)

# TRIGGER XỬ LÝ (ACTION PROCESSOR)
if st.session_state.action_trigger:
    act, prm = st.session_state.action_trigger, st.session_state.action_param
    st.session_state.action_trigger = None
    with st.container(border=True):
        if act == "create_detail":
            st.markdown("<div class='loading-pulse'>⏳ ĐANG DỰNG CHI TIẾT CẢNH...</div>", unsafe_allow_html=True)
            create_scene_details(int(prm), sel_mode, sel_style, sel_aspect, "Sales", t_dur, sel_strat)
            st.session_state.active_script_id = int(prm)
        elif act == "clone_script":
            st.markdown("<div class='loading-pulse'>⏳ ĐANG NHÂN BẢN BIẾN THỂ...</div>", unsafe_allow_html=True)
            add_or_clone_scripts(sel_mode, sel_style, sel_aspect, "Sales", t_dur, sel_strat, True, int(prm))
        elif act == "generate_more":
            st.markdown("<div class='loading-pulse'>⏳ ĐANG SÁNG TẠO KỊCH BẢN MỚI...</div>", unsafe_allow_html=True)
            add_or_clone_scripts(sel_mode, sel_style, sel_aspect, "Sales", t_dur, prm if prm else sel_strat, False, None)
    st.session_state.scroll_to_top = True; st.rerun()

# KHU VỰC NHẬP LIỆU PHÂN TÍCH
with st.expander("💡 Bảng Gợi Ý Phối Hợp 'Thể Loại & Phong Cách'", expanded=False):
    st.markdown("""<div style="background:#f8fafc; padding:16px; border-radius:12px; font-size:0.95rem;">
    <ul style="padding-left:20px; line-height:1.8;">
        <li><b>🛒 TikTok Shop:</b> Hợp nhất với <code style="color:#e11d48;">Studio Tối Giản</code>.</li>
        <li><b>👶 Mẹ & Bé:</b> Tối ưu với <code style="color:#e11d48;">Hoạt Hình 3D</code>.</li>
        <li><b>📺 TVC / Du Lịch / Nhà Cửa / Giáo Dục:</b> Tương thích <code style="color:#e11d48;">Điện Ảnh Chân Thực</code>.</li>
        <li><b>🏛️ Lịch Sử:</b> Đặc biệt hợp <code style="color:#e11d48;">Tranh Thủy Mặc Cổ Phong</code> hoặc Hoạt hình 2D/3D.</li>
        <li><b>🧘 Chữa Lành:</b> Tương thích <code style="color:#e11d48;">Hoạt Hình 2D (Ghibli)</code>.</li>
    </ul></div>""", unsafe_allow_html=True)
st.markdown("---")

input_txt = st.text_area("✍️ Tóm tắt ý tưởng, chủ đề hoặc mô tả chi tiết:")
ci1, ci2 = st.columns([1, 1])
with ci1: up_files = st.file_uploader("📦 Ảnh Sản phẩm / Bối cảnh", type=["jpg", "png"], accept_multiple_files=True, label_visibility="collapsed")
with ci2: n_char = st.number_input("👤 Số Diễn viên", 0, 8, 0)

chars = []
if n_char > 0:
    with st.expander("🎭 HỒ SƠ DIỄN VIÊN", expanded=True):
        g_cols = st.columns(min(n_char, 4))
        for i in range(n_char):
            with g_cols[i % 4]:
                r = st.text_input("Vai trò", key=f"r_{i}", placeholder="Mẹ 30 tuổi...")
                f = st.file_uploader("Ảnh", type=["jpg", "png"], key=f"f_{i}")
                if f and r: chars.append({"id": i+1, "role": r, "file": f})

if st.button("🚀 Bắt Đầu Phân Tích & Lên Kịch Bản", type="primary", use_container_width=True, disabled=not(input_txt or up_files or chars)):
    with st.spinner("⏳ Đang phân tích DNA..."):
        st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in chars]
        st.session_state.current_input_context = input_txt
        c_rules = get_char_rules(st.session_state.character_profiles, "Bán Hàng" in sel_mode)
        
        prompt = f"""Phân tích: "{input_txt}". Chiến lược: {sel_strat}. {get_realtime_context()}
        XUẤT JSON GỒM 'content_analysis' VÀ 'script_outlines'. PHẢI CÓ ĐỦ 5 OBJECT KỊCH BẢN (KHÔNG DÙNG DẤU BA CHẤM):
        {{
          "content_analysis": {{"primary_target_audience": "[Khách hàng]", "mechanical_and_accessories": "[Sản phẩm]", "customer_pain_points": "[Nỗi đau]", "core_desires": "[Mong muốn]", "emotional_or_usp_hook": "[USP]", "visual_physics_rules": "[Vật lý]", "prompt_dna_lock": "[Khóa DNA]"}},
          "script_outlines": [
            {{"id": 1, "title": "[Tên]", "setting_style": "[Mô tả]", "script_outfit_setup": "[Đồ]", "angle": "[Góc]", "target_hook": "[Hook]", "recommended_scenes_count": "3-4 cảnh", "voice_profile": {{"gender": "Nữ", "tone": "năng lượng"}}}},
            {{"id": 2, "title": "[Tên]", "setting_style": "[Mô tả]", "script_outfit_setup": "[Đồ]", "angle": "[Góc]", "target_hook": "[Hook]", "recommended_scenes_count": "3-4 cảnh", "voice_profile": {{"gender": "Nam", "tone": "năng lượng"}}}},
            {{"id": 3, "title": "[Tên]", "setting_style": "[Mô tả]", "script_outfit_setup": "[Đồ]", "angle": "[Góc]", "target_hook": "[Hook]", "recommended_scenes_count": "3-4 cảnh", "voice_profile": {{"gender": "Nữ", "tone": "năng lượng"}}}},
            {{"id": 4, "title": "[Tên]", "setting_style": "[Mô tả]", "script_outfit_setup": "[Đồ]", "angle": "[Góc]", "target_hook": "[Hook]", "recommended_scenes_count": "3-4 cảnh", "voice_profile": {{"gender": "Nữ", "tone": "năng lượng"}}}},
            {{"id": 5, "title": "[Tên]", "setting_style": "[Mô tả]", "script_outfit_setup": "[Đồ]", "angle": "[Góc]", "target_hook": "[Hook]", "recommended_scenes_count": "3-4 cảnh", "voice_profile": {{"gender": "Nam", "tone": "năng lượng"}}}}
          ]
        }}
        BẠN PHẢI ĐIỀN THÔNG TIN THAY CHO CÁC DẤU [...]."""
        payload = [types.Part.from_bytes(data=f.getvalue(), mime_type="image/jpeg") for f in up_files] if up_files else []
        for c in chars: payload.append(types.Part.from_bytes(data=c['file'].getvalue(), mime_type="image/jpeg"))
        payload.append(prompt)
        
        res = call_ai(payload, get_sys_inst(sel_mode, sel_style, sel_aspect, "Sales", t_dur, c_rules, sel_strat, "Người dùng"))
        st.session_state.content_analysis, st.session_state.all_scripts = res.get("content_analysis"), res.get("script_outlines", [])
        st.session_state.scroll_to_top = True; st.rerun()

# ==============================================================================
# KẾT QUẢ & UI CHIA CỘT
# ==============================================================================
if st.session_state.content_analysis and not st.session_state.action_trigger:
    st.divider()
    ca = st.session_state.content_analysis
    st.markdown(f"### 🔍 **Phân Tích DNA Chi Tiết**")
    with st.container(border=True): st.markdown(f"**🎯 Tệp khách hàng:** {ca.get('primary_target_audience', 'N/A')}<br>**⚠️ Nỗi đau:** {ca.get('customer_pain_points', 'N/A')}<br>**💡 USP:** {ca.get('emotional_or_usp_hook', 'N/A')}", unsafe_allow_html=True)

all_com = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts

# PHASE 1: DANH SÁCH TỔNG (CHƯA XEM CHI TIẾT)
if all_com and not st.session_state.active_script_id:
    st.divider()
    c_list = [s for s in all_com if s.get("id") in st.session_state.generated_details]
    p_list = [s for s in all_com if s.get("id") not in st.session_state.generated_details]
    
    st.markdown("### 🎬 Kịch Bản Đã Hoàn Thiện")
    if not c_list: st.caption("Chưa có kịch bản nào được dựng.")
    for o in c_list:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1: st.markdown(f"**#{o['id']}. {o['title']}** — <span class='badge-ready'>ĐÃ DỰNG</span>", unsafe_allow_html=True)
            with c2: 
                if st.button("👁️ Xem chi tiết", key=f"v_{o['id']}"): st.session_state.active_script_id = o['id']; st.session_state.scroll_to_top = True; st.rerun()
            with c3:
                if st.button("🚀 Nhân bản", key=f"c_{o['id']}"): st.session_state.action_trigger, st.session_state.action_param = "clone_script", o['id']; st.rerun()

    st.markdown("### ⏳ Ý Tưởng Đang Chờ")
    for o in p_list:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1.2])
            with c1: st.markdown(f"**#{o['id']}. {o['title']}** — <span class='badge-pending'>ĐỢI DỰNG</span>", unsafe_allow_html=True)
            with c2: 
                if st.button("✨ Dựng Cảnh Ngay", key=f"g_{o['id']}"): st.session_state.action_trigger, st.session_state.action_param = "create_detail", o['id']; st.rerun()

    st.markdown("---"); st.markdown("### 🔄 Gọi Thêm Kịch Bản")
    if "Bán Hàng" in sel_mode or "Mẹ & Bé" in sel_mode:
        cb1, cb2, cb3 = st.columns(3)
        if cb1.button("➕ Hỗn hợp", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Hỗn hợp"; st.rerun()
        if cb2.button("➕ Drama", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Drama"; st.rerun()
        if cb3.button("➕ Trực diện", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Trực diện"; st.rerun()
    elif "Lịch Sử" in sel_mode:
        cb1, cb2 = st.columns(2)
        if cb1.button("➕ Tài Liệu", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Tài liệu"; st.rerun()
        if cb2.button("➕ Dã Sử", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Dã sử"; st.rerun()
    else:
        if st.button("➕ Tạo thêm", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", sel_strat; st.rerun()

# PHASE 2: HIỂN THỊ CHI TIẾT (CHIA 2 CỘT QUẢN LÝ NHANH BÊN DƯỚI)
if st.session_state.active_script_id:
    st.divider()
    if st.button("⬅️ Quay lại danh sách tổng"): st.session_state.active_script_id = None; st.session_state.scroll_to_top = True; st.rerun()
    
    act = st.session_state.generated_details[st.session_state.active_script_id]
    st.markdown(f"### 🎬 CHI TIẾT: {act.get('title')}")
    st.info(f"⏱️ Thời lượng: {act.get('total_estimated_duration')}")

    for idx, sc in enumerate(act.get("scenes", []), 1):
        st.markdown(f"#### 📍 Phân cảnh {idx} ({sc.get('duration')}) — {sc.get('transition_type')}")
        st.markdown(f"**💬 Lời thoại Sạch:** `{sc.get('voiceover_vi')}`")
        
        img_p = sc.get('image_prompt', '')
        st.markdown("**🖼️ Prompt Ảnh:**")
        if "dùng ảnh cuối" in img_p.lower(): st.info("🔄 Dùng ảnh cuối cảnh trước làm tham chiếu để nối mạch.")
        else: st.code(img_p, language="text"); safe_copy_button(img_p, f"📋 Copy Ảnh {idx}")
            
        st.markdown("**🎥 Prompt Video:**")
        vid_p = sc.get('video_prompt', '')
        st.code(vid_p, language="text"); safe_copy_button(vid_p, f"📋 Copy Video {idx}")
        st.markdown("---")

    cl, cr = st.columns([1.1, 0.9])
    with cl:
        st.markdown("<div style='background:#f0fdf4; padding:10px; border-radius:10px; font-weight:bold; color:#166534; margin-bottom:10px;'>🎬 Đã Hoàn Thiện Khác</div>", unsafe_allow_html=True)
        for sc in [s for s in all_com if s.get("id") in st.session_state.generated_details]:
            with st.container(border=True):
                is_curr = (sc['id'] == st.session_state.active_script_id)
                st.markdown(f"**#{sc['id']}. {sc['title']}** {'(ĐANG XEM)' if is_curr else ''}")
                cx1, cx2 = st.columns(2)
                if not is_curr and cx1.button("👁️ Xem", key=f"sv_{sc['id']}"): st.session_state.active_script_id = sc['id']; st.session_state.scroll_to_top = True; st.rerun()
                if cx2.button("🚀 Nhân bản", key=f"sc_{sc['id']}"): st.session_state.action_trigger, st.session_state.action_param = "clone_script", sc['id']; st.rerun()
        if st.button("➕ Gọi Thêm Kịch Bản Mới", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", sel_strat; st.rerun()

    with cr:
        st.markdown("<div style='background:#f8fafc; padding:10px; border-radius:10px; font-weight:bold; color:#0f172a; margin-bottom:10px;'>📋 Đang Chờ Dựng</div>", unsafe_allow_html=True)
        for sc in [s for s in all_com if s.get("id") not in st.session_state.generated_details]:
            with st.container(border=True):
                st.markdown(f"**#{sc['id']}. {sc['title']}**")
                if st.button("✨ Dựng Cảnh", key=f"sg_{sc['id']}"): st.session_state.action_trigger, st.session_state.action_param = "create_detail", sc['id']; st.rerun()
    # ==============================================================================
# PHẦN 5: GIAO DIỆN CHÍNH, XỬ LÝ SỰ KIỆN VÀ HIỂN THỊ KẾT QUẢ ĐA TẦNG
# ==============================================================================
# 1. Phân quyền hiển thị Thể loại Nội dung
allowed_modules = ALL_MODULES
user_email = st.session_state.get("current_user_email", "")
if user_email and user_email != ADMIN_EMAIL:
    user_roles = st.session_state.licensed_accounts.get(user_email, {}).get("roles", [])
    if "Tất cả thể loại" not in user_roles:
        allowed_modules = [m for m in ALL_MODULES if m in user_roles]
        if not allowed_modules: allowed_modules = [ALL_MODULES[0]]

col_mode, col_style = st.columns([1.5, 1])
with col_mode:
    selected_mode = st.selectbox("🎯 Chọn Thể Loại Nội Dung:", options=allowed_modules)

# Lựa chọn Chiến lược Động (Dynamic Strategy Options) tùy theo Thể loại
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
# 2. XỬ LÝ SỰ KIỆN NÚT BẤM (ACTION TRIGGERS) - Ngăn giao diện bị load lại liên tục
# ==============================================================================
if st.session_state.action_trigger:
    action = st.session_state.action_trigger
    param = st.session_state.action_param
    st.session_state.action_trigger, st.session_state.action_param = None, None
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    if action == "create_detail":
        st.toast(f"⏳ Đang dựng chi tiết kịch bản #{param}...", icon="🎬")
        with st.container(border=True):
            st.markdown(f"<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG XỬ LÝ: Dựng chi tiết phân cảnh cho ý tưởng #{param}...</div>", unsafe_allow_html=True)
            try:
                create_scene_details_for_id(int(param), selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, selected_strategy)
                st.session_state.active_script_id = int(param)
                st.session_state.global_toast, st.session_state.global_toast_icon = f"Đã dựng thành công kịch bản #{param}!", "✅"
                st.session_state.scroll_to_top = True
            except Exception as e: st.error(f"❌ Lỗi: {e}")
            time.sleep(0.2); st.rerun() 
            
    elif action == "clone_script":
        st.toast(f"⏳ Đang nhân bản biến thể cho kịch bản #{param}...", icon="🧬")
        with st.container(border=True):
            st.markdown(f"<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG XỬ LÝ: Sáng tạo 5 biến thể độc đáo từ gốc #{param}...</div>", unsafe_allow_html=True)
            try:
                clone_script_id(int(param), selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, selected_strategy)
                st.session_state.global_toast, st.session_state.global_toast_icon = f"Đã nhân bản kịch bản #{param}!", "🧬"
                st.session_state.scroll_to_top = True
            except Exception as e: st.error(f"❌ Lỗi: {e}")
            time.sleep(0.2); st.rerun()
            
    elif action == "generate_more":
        st.toast("⏳ Đang sáng tạo kịch bản mới...", icon="🧠")
        with st.container(border=True):
            st.markdown("<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG XỬ LÝ: Kích hoạt Phân tích DNA để mở rộng kịch bản...</div>", unsafe_allow_html=True)
            try:
                strat_to_use = param if param else selected_strategy
                add_five_scripts_continuation(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, strat_to_use)
                st.session_state.global_toast, st.session_state.global_toast_icon = "Đã bổ sung kịch bản mới!", "🧠"
                st.session_state.scroll_to_top = True
            except Exception as e: st.error(f"❌ Lỗi: {e}")
            time.sleep(0.2); st.rerun()
    st.stop()

# ==============================================================================
# 3. KHU VỰC NHẬP LIỆU (ĐẦU VÀO)
# ==============================================================================
with st.expander("💡 Bấm vào đây để xem Bảng Gợi Ý Phối Hợp 'Thể Loại & Phong Cách'", expanded=False):
    st.markdown("""
    <div style="background-color: #f8fafc; padding: 16px; border-radius: 12px; border: 1.5px solid #e2e8f0; font-size: 0.95rem; color: #334155; margin-bottom: 5px;">
        <h4 style="color: #0f172a; margin-top: 0; margin-bottom: 12px; font-size: 1.05rem;">🎯 Cẩm Nang Phối Hợp Sáng Tạo Nội Dung Đa Vũ Trụ</h4>
        <ul style="padding-left: 20px; line-height: 1.8; margin-bottom: 0;">
            <li><b>🛒 TikTok Shop & Bán Hàng:</b> Phù hợp nhất với <code style="color: #e11d48;">Studio Tối Giản (Hiện đại, Sạch sẽ)</code>.</li>
            <li><b>👶 Mẹ & Bé & Cùng Con Học:</b> Tối ưu với <code style="color: #e11d48;">Hoạt Hình 3D (Kiểu Pixar)</code>.</li>
            <li><b>📺 TVC / Du Lịch / Nhà Cửa:</b> Cực kỳ tương thích với <code style="color: #e11d48;">Điện Ảnh Chân Thực (8K)</code>.</li>
            <li><b>🏛️ Lịch Sử & Tín Ngưỡng Di Sản:</b> Đặc biệt hợp với <code style="color: #e11d48;">Tranh Thủy Mặc Cổ Phong</code>.</li>
            <li><b>🧘 Chữa Lành & Phong Cách Sống:</b> Tạo cảm giác nhẹ nhàng với <code style="color: #e11d48;">Hoạt Hình 2D Ghibli</code>.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
st.markdown("---")

input_text = st.text_area("✍️ Tóm tắt ý tưởng, chủ đề hoặc mô tả chi tiết dự án/sản phẩm:", height=80, key="main_input_context")

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
    st.toast("⏳ Đang kết nối phân tích DNA...", icon="🤖")
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
                "mechanical_and_accessories": "Kiểu dáng, chất liệu",
                "customer_pain_points": "Nỗi đau khách hàng",
                "core_desires": "Mong muốn cốt lõi",
                "emotional_or_usp_hook": "Slogan, USP",
                "visual_physics_rules": "Quy chuẩn vật lý",
                "prompt_dna_lock": "Khóa thị giác"
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
# 4. HIỂN THỊ KẾT QUẢ VÀ UI ĐIỀU HƯỚNG KỊCH BẢN (CHIA CỘT)
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

all_combined_scripts_list = st.session_state.all_scripts + st.session_state.cloned_scripts + st.session_state.expanded_scripts

# GIAI ĐOẠN 1: KHI CHƯA XEM KỊCH BẢN CHI TIẾT
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

    # KHU VỰC GỌI THÊM ĐỘNG
    st.markdown("---")
    st.markdown("### 🔄 Gọi Thêm Kịch Bản Mới (Mở Rộng Tự Động)")
    if "Bán Hàng" in selected_mode or "Mẹ & Bé" in selected_mode:
        cb1, cb2, cb3 = st.columns(3)
        with cb1:
            if st.button("➕ 5 Kịch bản Hỗn hợp", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Hỗn hợp (2 Trực diện + 3 Drama)"; st.rerun()
        with cb2:
            if st.button("➕ 5 Kịch bản Drama/Giải trí", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "100% Drama / Shoppertainment"; st.rerun()
        with cb3:
            if st.button("➕ 5 Kịch bản Bán Hàng Trực diện", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "100% Bán hàng trực diện (Hard Sale)"; st.rerun()
    elif "Lịch Sử" in selected_mode:
        cb1, cb2 = st.columns(2)
        with cb1:
            if st.button("➕ 5 Kịch bản Phim Tài Liệu", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Phim Tài liệu / Kể chuyện lịch sử (Trang nghiêm)"; st.rerun()
        with cb2:
            if st.button("➕ 5 Kịch bản Hoạt Hình Dã Sử", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Phim Hoạt hình Dã sử (Có Tranh cãi / Hành động / Chiến tranh)"; st.rerun()
    else:
        if st.button("➕ Gọi Thêm 5 Kịch Bản Mới", type="primary", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", selected_strategy; st.rerun()

# GIAI ĐOẠN 2: KHI ĐÃ CHỌN XEM KỊCH BẢN CHI TIẾT (UI ĐIỀU HƯỚNG CHIA CỘT)
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
        st.markdown(f"**💬 Lời thuyết minh (Thoại sạch):** `\"{scene.get('voiceover_vi')}\"`")
        
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
        if st.button("➕ Gọi Thêm Tình Huống Kịch Bản Mới", key="btn_add_more_phase2_detail", use_container_width=True):
            st.session_state.action_trigger, st.session_state.action_param = "generate_more", selected_strategy
            st.rerun()

    with col_right:
        st.markdown("""
        <div class="custom-card" style="background: #f8fafc;">
            <div style="color: #0f172a; font-weight: 800; font-size: 1.1rem; margin-bottom: 10px;">📋 Kịch Bản Chưa Tạo Chi Tiết</div>
        </div>
        """, unsafe_allow_html=True)
        pending_scripts_in_detail = [item for item in all_combined_scripts_list if int(item.get("id", 0)) not in st.session_state.generated_details]
        if not pending_scripts_in_detail: st.success("🎉 Tuyệt vời! Tất cả các kịch bản trong danh sách đã được tạo chi tiết.")
        else:
            for item in pending_scripts_in_detail:
                it_id = int(item.get("id", 0))
                with st.container(border=True):
                    st.markdown(f"**#{it_id}. {item.get('title')}** — <span class='badge-pending'>CHƯA TẠO</span>", unsafe_allow_html=True)
                    st.caption(f"🏛️ {item.get('setting_style')}")
                    if st.button("✨ Tạo chi tiết ngay", key=f"nav_sc_detail_{it_id}", use_container_width=True):
                        st.session_state.action_trigger, st.session_state.action_param = "create_detail", it_id
                        st.rerun()
