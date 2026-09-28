import streamlit as st
from google import genai
from google.genai import types
import json
import re
import time
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# ==============================================================================
# 1. CẤU HÌNH TRANG & BIẾN MÔI TRƯỜNG
# ==============================================================================
st.set_page_config(page_title="Universal AI Video Studio Pro", layout="wide", page_icon="🎬")

API_KEY = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else "ĐIỀN_API_KEY_CỦA_BẠN_VÀO_ĐÂY"
client = genai.Client(api_key=API_KEY)

ADMIN_EMAIL = "admin@binhnguyen.vn"
ALL_MODULES = [
    "🛒 TikTok Shop & Bán Hàng", "👶 Mẹ & Bé & Cùng Con Học", "📺 TVC Quảng Cáo & Thương Hiệu Cao Cấp",
    "🏡 Nhà Cửa, Kiến Trúc & Cảnh Quan", "🌿 Du Lịch & Phong Cảnh Đất Nước", "🚗 Xe Cộ & Trải Nghiệm Lái",
    "🍲 Ẩm Thực & Đời Sống", "📖 Đời Sống & Giáo Dục", "🏛️ Lịch Sử & Tín Ngưỡng Di Sản",
    "🏢 Giới Thiệu Doanh Nghiệp"
]

# ==============================================================================
# 2. KHỞI TẠO SESSION STATE CHUẨN
# ==============================================================================
if "is_logged_in" not in st.session_state:
    st.session_state.update({
        "is_logged_in": False, "current_user_email": "",
        "licensed_accounts": {ADMIN_EMAIL: {"contact": ADMIN_EMAIL, "roles": ["Tất cả"], "expires_at": "2099-12-31"}},
        "projects_library": {}, "content_analysis": None,
        "all_scripts": [], "cloned_scripts": [], "expanded_scripts": [],
        "generated_details": {}, "active_script_id": None,
        "active_project_title": "Chiến dịch mới",
        "character_profiles": [], "file_uploader_key": 0,
        "action_trigger": None, "action_param": None,
        "scroll_to_top": False, "last_loaded_file_id": None
    })

if st.session_state.get('scroll_to_top', False):
    components.html("<script>window.parent.document.querySelector('.main').scrollTo(0,0);</script>", height=0)
    st.session_state.scroll_to_top = False

# ==============================================================================
# 3. CSS TÙY CHỈNH
# ==============================================================================
st.markdown("""
<style>
    .header-container { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 1.5rem; border-radius: 12px; text-align: center; color: white; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    .main-title { font-size: 2rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin: 0; background: linear-gradient(to right, #60a5fa, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .sub-title { font-size: 1rem; font-weight: 500; color: #94a3b8; margin-top: 5px; }
    .badge-ready { background-color: #16a34a; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .badge-pending { background-color: #f59e0b; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .loading-pulse { animation: pulse 1.5s infinite; color: #2563eb; font-weight: bold; text-align: center; padding: 10px; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. HÀM TIỆN ÍCH & XỬ LÝ CHUỖI CỰC MẠNH (CHỐNG LỖI JSON)
# ==============================================================================
def process_login(login_val):
    login_val = login_val.strip()
    if not login_val: return st.error("⚠️ Vui lòng nhập tài khoản.")
    acc = st.session_state.licensed_accounts.get(login_val)
    if acc and datetime.now() <= datetime.strptime(acc["expires_at"], "%Y-%m-%d"):
        st.session_state.update({"is_logged_in": True, "current_user_email": login_val})
        st.success("✅ Đăng nhập thành công!"); time.sleep(0.5); st.rerun()
    else: st.error("❌ Tài khoản không tồn tại hoặc đã hết hạn.")

def format_analysis_field(field_val) -> str:
    if isinstance(field_val, dict): return "<br>".join([f"• <b>{k.replace('_', ' ').title()}:</b> {v}" for k, v in field_val.items()])
    elif isinstance(field_val, list): return "<br>".join([f"• {item}" for item in field_val])
    text = re.sub(r'<<\.?', '', str(field_val).strip()).replace('<b>', '').replace('</b>', '')
    lines = [l.strip() for l in text.split('<br>') if l.strip()]
    return "".join([f"<div style='margin-top: 6px;'>{l}</div>" if l.startswith('•') else f"<div style='margin-left: 15px; margin-top: 4px;'>• {l}</div>" for l in lines]) if lines else text

def clean_and_parse_json(text_content: str):
    text = text_content.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx != -1 and end_idx != -1:
        text = text[start_idx:end_idx+1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        text = text.replace('\n', ' ').replace('\r', '')
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        try: return json.loads(text)
        except Exception as e: raise Exception(f"Lỗi cú pháp JSON từ AI: {e}")

def safe_copy_button(text_to_copy, label):
    st.code(text_to_copy, language="text")

# ==============================================================================
# 5. HỆ THỐNG PROMPT LÕI (CHUYÊN GIA ĐẠO DIỄN)
# ==============================================================================
def get_strategy_rules(mode: str, strategy: str, target_audience: str) -> str:
    rules = f"- ĐỐI TƯỢNG: Kịch bản nhắm thẳng vào tệp khách hàng {target_audience}.\n"
    if "Bán Hàng" in mode or "Mẹ & Bé" in mode:
        if "Review" in strategy: rules += "- CHIẾN LƯỢC REVIEW THỰC TẾ: Đập hộp, test tính năng chân thực, góc máy KOC.\n"
        elif "Tình huống" in strategy: rules += "- CHIẾN LƯỢC TÌNH HUỐNG: Mâu thuẫn đời sống gia đình/công sở, twist chốt sale cuối.\n"
        else: rules += "- CHIẾN LƯỢC GIẢM GIÁ/BÁN HÀNG: Tập trung xưởng, showroom, thúc đẩy xả kho.\n"
    else: rules += f"- CHIẾN LƯỢC: {strategy}. Tạo kịch bản chuyên nghiệp.\n"
    return rules

def get_system_instructions(mode, style, aspect_ratio, goal, target_duration_mins, char_rules, strategy, audience):
    fmt = "9:16 vertical cinematic format" if aspect_ratio == "9:16" else "16:9 widescreen cinematic format"
    dur = "THỜI LƯỢNG: 3 đến 5 phân cảnh linh hoạt." if target_duration_mins <= 0.5 else f"THỜI LƯỢNG: Phân bổ tổng {int(target_duration_mins * 60)} giây."
    strat_rules = get_strategy_rules(mode, strategy, audience)
    
    return f"""
BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL ĐA NĂNG CHO VEO 3 VÀ IMAGEN 3.
PHONG CÁCH: {style.upper()} | KHUNG HÌNH: {fmt} | MỤC TIÊU: {goal}
{dur}

🛑 QUY TẮC BẮT BUỘC 100%:
1. TRẢ VỀ CHUẨN JSON. KHÔNG XUỐNG DÒNG BẰNG DẤU ENTER TRONG CHUỖI.
2. NHÂN VẬT & QUỐC TỊCH: Luôn chèn "Vietnamese" cho nhân vật để chuẩn diện mạo.
{char_rules}
4. CẤM HIỂN THỊ UI: Ép lệnh "Cinematic shot ONLY. ABSOLUTELY NO UI elements".
5. {strat_rules}
6. TỪ KHÓA AN TOÀN: Tuyệt đối không dùng giá tiền số (VD: 100k, 50 ngàn). Không tự thêm mùa vụ (thu, đông). Dùng "mùa cao điểm", "chương trình siêu ưu đãi".
7. BẢO TOÀN SẢN PHẨM KHỐI (MACRO LOCK): Đối với sản phẩm vật lý (tẩu sạc, thiết bị nhỏ), BẮT BUỘC áp dụng góc máy MACRO SHOT hoặc EXTREME CLOSE-UP. Kèm lệnh "strictly NO hands obscuring" để giữ hình khối không bị méo.
8. CHUẨN SỐ TỪ: Cảnh 4s (12-14 từ); Cảnh 6s (18-21 từ); Cảnh 8s (24-28 từ) để khớp audio.
"""

def generate_char_rules_string(profiles, is_sales_mode):
    if not profiles: return "3. ĐỒNG NHẤT NHÂN VẬT: Bắt buộc có nhân vật thống nhất qua các cảnh."
    rules = "3. KHÓA KHUÔN MẶT VÀ TRANG PHỤC (IDENTITY LOCK):\n"
    for p in profiles: rules += f"   - NV {p['id']} (Vai '{p['role']}'): Prompt bắt buộc: 'Character {p['id']} ({p['role']}) maintaining identical facial features, exact hairstyle, body proportions, and the exact same outfit across all scenes'.\n"
    return rules

# ==============================================================================
# 6. GỌI API GEMINI VÀ XỬ LÝ LÕI KỊCH BẢN
# ==============================================================================
def call_gemini_with_retry(payload, sys_inst):
    for attempt in range(4):
        try:
            res = client.models.generate_content(
                model="gemini-3.6-flash", contents=payload, 
                config=types.GenerateContentConfig(system_instruction=sys_inst, response_mime_type="application/json")
            )
            return clean_and_parse_json(res.text)
        except Exception as e:
            if "429" in str(e): time.sleep(15)
            elif "503" in str(e): time.sleep(3 * (attempt + 1))
            else: time.sleep(4)
    raise Exception(f"Lỗi kết nối AI: {e}")

def create_scene_details_for_id(target_id: int, current_mode: str, current_style: str, aspect_ratio: str, goal: str, target_duration_mins: float, current_strategy: str):
    all_sources = (st.session_state.all_scripts or []) + (st.session_state.cloned_scripts or []) + (st.session_state.expanded_scripts or [])
    outline = next((sc for sc in all_sources if isinstance(sc, dict) and int(sc.get("id", 0)) == int(target_id)), None)
    if not outline: raise Exception(f"Không tìm thấy ID #{target_id}.")
    
    product_ctx = st.session_state.get("current_input_context", "Dự án hiện tại").replace('"', "'")
    safe_title = outline.get('title', '').replace('"', "'").replace('\n', ' ')
    safe_setting = outline.get('setting_style', '').replace('"', "'").replace('\n', ' ')
    duration_str = "16s - 32s (Tối ưu Credit)" if target_duration_mins <= 0.5 else f"{int(target_duration_mins * 60)}s"

    profiles = st.session_state.get("character_profiles", [])
    if profiles:
        identity_lock_rules = " AND ".join([f"Character {p['id']} ({p['role']}) maintaining identical facial features, exact hairstyle, body proportions, and the exact same outfit across all scenes" for p in profiles])
        profiles_desc = "DANH SÁCH DIỄN VIÊN:\n" + "\n".join([f"- NV {p['id']}: Vai '{p['role']}'" for p in profiles])
    else:
        identity_lock_rules = "Consistent characters with fixed facial structure and unchanging outfits"
        profiles_desc = "Kịch bản đồng nhất nhân vật linh hoạt."

    char_rules_str = generate_char_rules_string(profiles, "Bán Hàng" in current_mode)
    dna_data = st.session_state.get("content_analysis", {})
    target_audience = dna_data.get("primary_target_audience", "Người dùng mục tiêu")
    
    prompt_detail = f"""
    Ngữ cảnh: "{product_ctx}" | Khách hàng: {target_audience}
    Kịch bản: ID {target_id} - {safe_title} | Bối cảnh gốc: {safe_setting}
    CHIẾN LƯỢC: {current_strategy}
    {profiles_desc}
    
    🛑 7 QUY CHUẨN ĐẠO DIỄN VÀ GÓC MÁY QUỐC TẾ BẮT BUỘC:
    1. ĐỒNG BỘ BỐI CẢNH (SCENE CONTINUITY): Các phân cảnh PHẢI GIỮ NGUYÊN BỐI CẢNH ({safe_setting}). Nhân vật khóa bằng: [{identity_lock_rules}].
    2. KHÓA MÀU/HÌNH KHỐI SẢN PHẨM: Khớp tuyệt đối ảnh gốc (`the physical product matching the exact geometric shape, color, and material from the reference image`).
    3. GÓC MÁY TỰ ĐỘNG CHUẨN XÁC: 
       - Review: Cảnh 1 (Medium Shot). Cảnh 2,3 (Extreme Close-up / Macro Shot để quay rõ từng chi tiết sản phẩm, không thấy mặt người). Cảnh cuối (Medium Shot).
       - Tình huống: Over-the-shoulder và Close-up luân phiên.
    4. TỐI ƯU AUDIO FIRST: TRONG `video_prompt`, TUYỆT ĐỐI KHÔNG lặp lại thoại tiếng Việt, chỉ ghi: `Speaking in Vietnamese with expressive emotion` kết hợp khẩu hình và ambient sound.
    5. CẤU TRÚC: 3-5 phân cảnh linh hoạt.
    6. AN TOÀN TỪ KHÓA: Không dùng giá tiền cụ thể.
    7. KHÔNG CHẠM VÀO SẢN PHẨM (NO OCCLUSION): Trong các cảnh Macro/Cận cảnh, luôn kèm lệnh `strictly NO hands obscuring` để giữ hình khối sản phẩm hoàn hảo, không bị biến dạng bởi tay người.
    
    Xuất 1 Dict JSON CHUẨN (ĐIỀN KÍN CHỮ):
    {{
      "id": {target_id}, "title": "{safe_title}", "setting_style": "{safe_setting}",
      "script_outfit_setup": "Trang phục cố định", "voice_profile": {{"gender": "Hỗn hợp Nam/Nữ", "tone": "Dồn dập"}},
      "total_estimated_duration": "{duration_str}",
      "scenes": [
        {{
          "scene_number": 1, "duration": "8s", "scene_setting": "[Mô tả bối cảnh, góc quay Medium Shot]", "transition_type": "Mở đầu (Hook)", 
          "voice_director_vn": "[Chỉ đạo giọng]", "dialogues": [ {{"speaker": "Nhân vật A", "dialogue": "[Thoại chạm nỗi đau]"}} ],
          "image_prompt": "A 9:16 [Điền: Medium Shot] featuring {identity_lock_rules} in ({safe_setting}). Physical product matching exact reference. Cinematic ONLY. NO UI.", 
          "video_prompt": "Audio: Speaking in Vietnamese. Ambient sound: room tone. Visual: Cinematic [Điền: Medium Shot] showing {identity_lock_rules} in ({safe_setting})."
        }},
        {{
          "scene_number": 2, "duration": "6s", "scene_setting": "[Giữ bối cảnh, góc máy Macro Shot / Extreme Close-up test tính năng]", "transition_type": "Cắt cứng", 
          "voice_director_vn": "[Chỉ đạo giọng]", "dialogues": [ {{"speaker": "Nhân vật B", "dialogue": "[Thoại giải pháp]"}} ],
          "image_prompt": "A 9:16 [Điền: Macro Shot / Extreme Close-up] of physical product matching exact reference in ({safe_setting}). Fully visible, strictly NO hands obscuring. NO UI.", 
          "video_prompt": "Audio: Speaking in Vietnamese. Visual: [Điền góc máy Macro] focusing purely on product details. Product maintains absolute rigid structural integrity without morphing."
        }}
      ]
    }}
    LƯU Ý: TẠO TỪ 3 ĐẾN 5 CẢNH. VIẾT THAY THẾ TOÀN BỘ NGOẶC VUÔNG [...].
    """
    sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins, char_rules_str, current_strategy, target_audience)
    res = call_gemini_with_retry([prompt_detail], sys_inst)
    st.session_state.generated_details[target_id] = res[0] if isinstance(res, list) else res

def add_five_scripts_continuation(current_mode, current_style, aspect_ratio, goal, target_duration_mins, current_strategy):
    all_sources = (st.session_state.all_scripts or []) + (st.session_state.cloned_scripts or []) + (st.session_state.expanded_scripts or [])
    cur_len = len(all_sources)
    product_ctx = st.session_state.get("current_input_context", "").replace('"', "'")
    dna_data = st.session_state.get("content_analysis", {}) 
    char_rules_str = generate_char_rules_string(st.session_state.get("character_profiles", []), "Bán Hàng" in current_mode)
    
    prompt_more = f"""
    DỮ LIỆU SẢN PHẨM: {json.dumps(dna_data, ensure_ascii=False)} | "{product_ctx}"
    Tạo thêm ĐÚNG 5 kịch bản mới (id từ {cur_len + 1} đến {cur_len + 5}) theo CHIẾN LƯỢC: {current_strategy}. KHÔNG dùng giá tiền.
    Xuất JSON chuẩn với key 'script_outlines' chứa 5 OBJECT có đầy đủ: id, title, setting_style, script_outfit_setup, angle, target_hook, recommended_scenes_count, voice_profile.
    """
    sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins, char_rules_str, current_strategy, "")
    res = call_gemini_with_retry([prompt_more], sys_inst)
    new_scripts = res.get("script_outlines", [])
    for i, sc in enumerate(new_scripts): sc["id"] = cur_len + i + 1
    st.session_state.expanded_scripts.extend(new_scripts)

def clone_script_id(target_id, current_mode, current_style, aspect_ratio, goal, target_duration_mins, current_strategy):
    target_script = st.session_state.generated_details[target_id]
    cur_len = len((st.session_state.all_scripts or []) + (st.session_state.cloned_scripts or []) + (st.session_state.expanded_scripts or []))
    char_rules_str = generate_char_rules_string(st.session_state.get("character_profiles", []), "Bán Hàng" in current_mode)
    prompt = f"Dựa trên kịch bản gốc: {json.dumps(target_script, ensure_ascii=False)}. Tạo ĐÚNG 5 biến thể mới (id từ {cur_len+1} đến {cur_len+5}). Xuất JSON key 'cloned_outlines'."
    sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins, char_rules_str, current_strategy, "")
    res_c = call_gemini_with_retry([prompt], sys_inst)
    cloned_list = res_c.get("cloned_outlines", [])
    for idx_c, cl in enumerate(cloned_list): cl["id"] = cur_len + idx_c + 1
    st.session_state.cloned_scripts.extend(cloned_list)

# ==============================================================================
# 7. THANH BÊN (SIDEBAR UI) - ĐẦY ĐỦ QUẢN LÝ DỰ ÁN & ADMIN
# ==============================================================================
with st.sidebar:
    if not st.session_state.is_logged_in:
        st.markdown("### 🔐 **Đăng Nhập Hệ Thống**")
        with st.form("login_form"):
            login_input = st.text_input("Nhập Email / SĐT:", placeholder="vd: admin@binhnguyen.vn")
            if st.form_submit_button("🔑 Đăng Nhập", use_container_width=True): process_login(login_input)
    
    if st.session_state.is_logged_in:
        st.markdown("### 🗂️ **Quản Lý Dự Án**")
        if st.button("➕ Tạo Dự Án Mới", type="primary", use_container_width=True):
            st.session_state.update({"content_analysis": None, "all_scripts": [], "cloned_scripts": [], "expanded_scripts": [], "generated_details": {}, "character_profiles": [], "active_script_id": None, "active_project_title": "Chiến dịch mới"})
            st.session_state.file_uploader_key += 1; st.session_state.scroll_to_top = True; st.rerun()

        project_title_input = st.text_input("Tên dự án hiện tại:", value=st.session_state.get("active_project_title", "Chiến dịch mới"))
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("💾 Lưu Dự Án", use_container_width=True):
                st.session_state.projects_library[f"proj_{int(time.time())}"] = {
                    "title": project_title_input, "mode": st.session_state.get("selected_mode", ""), "content_analysis": st.session_state.content_analysis,
                    "all_scripts": st.session_state.all_scripts, "cloned_scripts": st.session_state.cloned_scripts,
                    "expanded_scripts": st.session_state.expanded_scripts, "generated_details": st.session_state.generated_details,
                    "character_profiles": st.session_state.character_profiles
                }
                st.success("✅ Đã lưu!")
        with col_p2:
            export_data = {"title": project_title_input, "content_analysis": st.session_state.content_analysis, "all_scripts": st.session_state.all_scripts, "cloned_scripts": st.session_state.cloned_scripts, "expanded_scripts": st.session_state.expanded_scripts, "generated_details": st.session_state.generated_details, "character_profiles": st.session_state.character_profiles}
            json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
            st.download_button("📥 Tải JSON", data=json_str, file_name=f"{project_title_input.replace(' ', '_')}.json", mime="application/json", use_container_width=True)

        if st.session_state.projects_library:
            proj_keys = list(st.session_state.projects_library.keys())
            selected_load_id = st.selectbox("📂 Chọn dự án đã lưu:", options=proj_keys, format_func=lambda x: st.session_state.projects_library[x]["title"])
            if st.button("📂 Mở Dự Án Này", use_container_width=True):
                p_data = st.session_state.projects_library[selected_load_id]
                st.session_state.update({"active_project_title": p_data.get("title", "Load"), "content_analysis": p_data.get("content_analysis"), "all_scripts": p_data.get("all_scripts", []), "cloned_scripts": p_data.get("cloned_scripts", []), "expanded_scripts": p_data.get("expanded_scripts", []), "generated_details": p_data.get("generated_details", {}), "character_profiles": p_data.get("character_profiles", []), "active_script_id": None, "scroll_to_top": True}); st.rerun()

        st.markdown("<div style='font-size: 0.85rem; color: #64748b; margin-top: 8px;'>Hoặc tải file dự án (.json):</div>", unsafe_allow_html=True)
        uploaded_project_file = st.file_uploader("📤 Tải file kịch bản", type=["json"], label_visibility="collapsed", key=f"project_uploader_{st.session_state.file_uploader_key}")
        if uploaded_project_file is not None:
            file_identifier = f"{uploaded_project_file.name}_{uploaded_project_file.size}"
            if st.session_state.get("last_loaded_file_id") != file_identifier:
                try:
                    p_data = json.loads(uploaded_project_file.getvalue().decode("utf-8"))
                    st.session_state.update({"active_project_title": p_data.get("title", "Load"), "content_analysis": p_data.get("content_analysis", None), "all_scripts": p_data.get("all_scripts", []), "expanded_scripts": p_data.get("expanded_scripts", []), "cloned_scripts": p_data.get("cloned_scripts", []), "generated_details": {int(k): v for k, v in p_data.get("generated_details", {}).items()}, "character_profiles": p_data.get("character_profiles", []), "active_script_id": None, "last_loaded_file_id": file_identifier, "scroll_to_top": True}); st.rerun()
                except Exception as e: st.error(f"❌ Lỗi đọc file JSON: {e}")

        if st.session_state.current_user_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙️ **Quản Lý Tài Khoản (Admin)**")
            with st.form("add_license_form"):
                new_acc = st.text_input("Email / SĐT khách hàng mới:")
                if st.form_submit_button("➕ Cấp Quyền Dùng Thử", use_container_width=True) and new_acc.strip():
                    st.session_state.licensed_accounts[new_acc.strip()] = {"expires_at": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")}
                    st.success(f"Đã cấp quyền: {new_acc.strip()}"); time.sleep(0.5); st.rerun()

        st.markdown("---")
        if st.button("🚪 Đăng Xuất", use_container_width=True): st.session_state.is_logged_in = False; st.rerun()

# ==============================================================================
# 8. GIAO DIỆN CHÍNH (MAIN UI)
# ==============================================================================
st.markdown("""
<div class="header-container">
    <div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div>
    <div class="sub-title">Tối Ưu Chuyển Đổi, Đồng Nhất Tuyệt Đối Nhân Vật, Bối Cảnh & Sản Phẩm</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.is_logged_in: st.info("👈 Vui lòng đăng nhập ở thanh công cụ bên trái."); st.stop()

col_mode, col_style = st.columns([1.5, 1])
with col_mode: selected_mode = st.selectbox("🎯 Chọn Thể Loại Nội Dung:", options=ALL_MODULES, key="selected_mode")

strat_options = ["Review thực tế", "Tình huống", "Giảm giá/bán hàng"] if "Bán Hàng" in selected_mode or "Mẹ & Bé" in selected_mode else ["Viral / Bắt trend giải trí", "Chia sẻ kiến thức", "Kể chuyện cảm xúc (Storytelling)"]

with col_style: selected_style = st.selectbox("🎨 Phong Cách Hình Ảnh:", options=["Cinematic Realism", "Hoạt Hình 3D", "Studio Tối Giản"])

col_strat, col_ratio, col_time = st.columns([1.5, 1, 1])
with col_strat: selected_strategy = st.selectbox("🧠 Chiến lược Kịch bản:", options=strat_options)
with col_ratio: selected_aspect = "9:16" if "9:16" in st.selectbox("Tỷ lệ khung hình:", ["9:16 (Dọc TikTok/Reels)", "16:9 (Ngang YouTube)"]) else "16:9"
with col_time: target_duration_mins = st.number_input("⏱️ Thời lượng (Phút):", min_value=0.5, max_value=30.0, value=1.0, step=0.5)
content_goal = "Sales & Conversion"

# ==============================================================================
# 9. XỬ LÝ TRIGGER (NÚT BẤM)
# ==============================================================================
# LƯU Ý QUAN TRỌNG: Lỗi màn hình trắng trước đây đã được sửa triệt để bằng cách không dùng action_trigger cho nút "Xem chi tiết"
if st.session_state.action_trigger in ["create_detail", "clone_script", "generate_more"]:
    action = st.session_state.action_trigger
    param = st.session_state.action_param
    st.session_state.action_trigger, st.session_state.action_param = None, None
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown(f"<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG KẾT NỐI AI... VUI LÒNG ĐỢI!</div>", unsafe_allow_html=True)
        try:
            if action == "create_detail":
                create_scene_details_for_id(int(param), selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, selected_strategy)
                st.session_state.active_script_id = int(param)
            elif action == "clone_script":
                clone_script_id(int(param), selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, selected_strategy)
            elif action == "generate_more":
                add_five_scripts_continuation(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, param or selected_strategy)
            
            st.session_state.scroll_to_top = True; time.sleep(0.2); st.rerun()
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")
            if st.button("🔄 Thử lại ngay"): st.rerun()
    st.stop()

# ==============================================================================
# 10. KHU VỰC NHẬP LIỆU
# ==============================================================================
input_text = st.text_area("✍️ Tóm tắt ý tưởng, chủ đề hoặc mô tả dự án/sản phẩm:", height=80, key="main_input_context")
col_p_img, col_c_img = st.columns([1, 1])
with col_p_img: uploaded_files = st.file_uploader("📦 Tải ảnh Sản phẩm (Bắt buộc để Khóa Hình Khối Macro)", type=["jpg", "png"], accept_multiple_files=True)
with col_c_img: 
    num_chars = st.number_input("👤 Số lượng Diễn viên tham chiếu", min_value=0, max_value=8, step=1)
    char_inputs = []
    if num_chars > 0:
        grid_cols = st.columns(min(num_chars, 4))
        for i in range(num_chars):
            with grid_cols[i % 4].container(border=True):
                c_role = st.text_input(f"Vai trò DV {i+1}", placeholder="VD: Nữ MC KOC")
                c_file = st.file_uploader(f"Ảnh DV {i+1}", type=["jpg", "png"], key=f"c_img_{i}")
                if c_file and c_role.strip(): char_inputs.append({"id": i+1, "role": c_role.strip(), "file": c_file})

if st.button("🚀 Phân Tích DNA & Lên Ý Tưởng", type="primary", use_container_width=True, disabled=not (input_text.strip() or uploaded_files)):
    with st.spinner("⏳ Đang phân tích chuyên sâu..."):
        try:
            st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
            st.session_state.current_input_context = input_text.strip()
            char_rules_str = generate_char_rules_string(st.session_state.character_profiles, "Bán Hàng" in selected_mode)
            
            payload = ["ẢNH SẢN PHẨM:"] + [types.Part.from_bytes(data=f.getvalue(), mime_type=f.type or "image/jpeg") for f in (uploaded_files or [])]
            for c in char_inputs: payload.extend([f"ẢNH NHÂN VẬT {c['id']} ({c['role']}):", types.Part.from_bytes(data=c['file'].getvalue(), mime_type=c['file'].type or "image/jpeg")])
            payload.append(f"Phân tích '{selected_mode}' - {selected_strategy}. Mô tả: '{st.session_state.current_input_context}'. KHÔNG dùng giá tiền cụ thể. Xuất JSON content_analysis và script_outlines (5 object).")
            
            res = call_gemini_with_retry(payload, get_system_instructions(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, char_rules_str, selected_strategy, "Người tiêu dùng"))
            st.session_state.update({"content_analysis": res.get("content_analysis"), "all_scripts": res.get("script_outlines", []), "cloned_scripts": [], "expanded_scripts": [], "generated_details": {}, "active_script_id": None, "scroll_to_top": True}); st.rerun()
        except Exception as e: st.error(f"❌ Lỗi: {e}")

# ==============================================================================
# 11. KHU VỰC HIỂN THỊ KẾT QUẢ ĐẦU RA
# ==============================================================================
if st.session_state.content_analysis and not st.session_state.action_trigger:
    st.divider()
    dna = st.session_state.content_analysis
    st.markdown(f"### 🔍 Phân Tích DNA Dự Án Đa Tầng — [ {selected_mode} ]")
    with st.expander("Bấm để xem/ẩn chi tiết Định hướng Kịch bản", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**🎯 1. Chân dung Khách hàng & Nỗi đau:**<br><div style='line-height: 1.8;'>• <b>Tệp chính:</b> {dna.get('primary_target_audience', 'N/A')}<br>• <b>Nỗi đau/Vấn đề:</b> {format_analysis_field(dna.get('customer_pain_points', 'N/A'))}</div>", unsafe_allow_html=True)
            st.markdown(f"**💎 2. Giá trị cốt lõi & Giải pháp:**<br><div style='line-height: 1.8;'>{format_analysis_field(dna.get('product_core_value_proposition', 'N/A'))}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"**🪝 3. Chuỗi Hook & Thông điệp:**<br><div style='line-height: 1.8;'>• <b>Móc câu (Hook):</b> {format_analysis_field(dna.get('recommended_hook_angles', 'N/A'))}<br>• <b>Thông điệp chính:</b> {format_analysis_field(dna.get('key_messaging_pillars', 'N/A'))}</div>", unsafe_allow_html=True)
            st.markdown(f"**📌 4. Khóa thị giác (Visual DNA Lock):**<br><div style='line-height: 1.8;'>{format_analysis_field(dna.get('visual_identity_cues', 'N/A'))}</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    all_combined_scripts_list = (st.session_state.all_scripts or []) + (st.session_state.cloned_scripts or []) + (st.session_state.expanded_scripts or [])

    if all_combined_scripts_list and st.session_state.active_script_id is None:
        completed_scripts = [sc for sc in all_combined_scripts_list if int(sc.get("id", 0)) in st.session_state.generated_details]
        pending_scripts = [sc for sc in all_combined_scripts_list if int(sc.get("id", 0)) not in st.session_state.generated_details]

        st.markdown("### 🎬 Kịch Bản Đã Hoàn Thiện")
        for sc in completed_scripts:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2.5, 1, 1])
                c1.markdown(f"**#{sc['id']}. {sc.get('title')}** — <span class='badge-ready'>SẴN SÀNG</span>", unsafe_allow_html=True)
                # Sửa lỗi màn hình trắng: Truyền thẳng state và rerun không qua action_trigger
                if c2.button("👁️ Xem chi tiết", key=f"btn_v1_{sc['id']}", use_container_width=True): 
                    st.session_state.update({"active_script_id": sc['id'], "scroll_to_top": True}); st.rerun()
                if c3.button("🚀 Nhân bản", key=f"btn_c1_{sc['id']}", use_container_width=True): 
                    st.session_state.update({"action_trigger": "clone_script", "action_param": sc['id']}); st.rerun()

        st.markdown("### ⏳ Ý Tưởng Đang Chờ (Chưa Dựng Chi Tiết)")
        for sc in pending_scripts:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**#{sc['id']}. {sc.get('title')}**")
                if c2.button("✨ Tạo chi tiết ngay", key=f"btn_p1_{sc['id']}", type="primary", use_container_width=True): 
                    st.session_state.update({"action_trigger": "create_detail", "action_param": sc['id']}); st.rerun()

        st.markdown("---")
        st.markdown("### ➕ Mở Rộng Thêm Kịch Bản Mới")
        if "Bán Hàng" in selected_mode or "Mẹ & Bé" in selected_mode:
            cb1, cb2, cb3 = st.columns(3)
            if cb1.button("➕ 5 Kịch bản Review", use_container_width=True): st.session_state.update({"action_trigger": "generate_more", "action_param": "Review thực tế"}); st.rerun()
            if cb2.button("➕ 5 Kịch bản Tình huống", use_container_width=True): st.session_state.update({"action_trigger": "generate_more", "action_param": "Tình huống"}); st.rerun()
            if cb3.button("➕ 5 Kịch bản Giảm giá", use_container_width=True): st.session_state.update({"action_trigger": "generate_more", "action_param": "Giảm giá/bán hàng"}); st.rerun()
        else:
            if st.button("➕ Gọi Thêm 5 Kịch Bản Mới", use_container_width=True): st.session_state.update({"action_trigger": "generate_more", "action_param": selected_strategy}); st.rerun()

    if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details:
        if st.button("⬅️ Quay lại danh sách tổng", use_container_width=False): st.session_state.update({"active_script_id": None, "scroll_to_top": True}); st.rerun()

        raw_data = st.session_state.generated_details[st.session_state.active_script_id]
        active_script = raw_data[0] if isinstance(raw_data, list) else raw_data
        st.markdown(f"### 🎬 KỊCH BẢN CHI TIẾT: {str(active_script.get('title')).upper()}")
        
        for idx, scene in enumerate(active_script.get("scenes", []), start=1):
            if not isinstance(scene, dict): continue
            st.markdown(f"#### 📍 Phân cảnh {idx} ({scene.get('duration', '6s')}) — [ {scene.get('transition_type', 'Cắt cảnh')} ]")
            st.markdown(f"🏛️ **Bối cảnh & Góc máy:** *{scene.get('scene_setting')}*")
            st.markdown(f"**🎙️ Đạo diễn Voice:** *{scene.get('voice_director_vn')}*")
            
            dialogues = scene.get("dialogues", [])
            full_voice = ""
            if dialogues:
                st.markdown("**💬 Lời Thoại (Dùng để thu âm Audio-First):**")
                for d in dialogues:
                    spk, line = d.get("speaker", ""), d.get("dialogue", "")
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;• 🗣️ <b>{spk}:</b> `\"{line}\"`", unsafe_allow_html=True)
                    full_voice += f"{spk}: {line}\n"
                safe_copy_button(full_voice.strip(), f"📋 Copy Thoại Cảnh {idx}")

            st.markdown("**🖼️ Prompt Sinh Ảnh (Imagen 3 / Midjourney):**")
            st.code(scene.get('image_prompt', ''), language="text")
            st.markdown("**🎥 Prompt Chuyển Động (Veo 3 / Kling):**")
            st.code(scene.get('video_prompt', ''), language="text")
            st.markdown("---")

        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.markdown("### ➕ Gọi Thêm Ý Tưởng Mới")
            if "Bán Hàng" in selected_mode or "Mẹ & Bé" in selected_mode:
                if st.button("➕ Review", key="g2_rev", use_container_width=True): st.session_state.update({"action_trigger": "generate_more", "action_param": "Review thực tế"}); st.rerun()
                if st.button("➕ Tình huống", key="g2_dra", use_container_width=True): st.session_state.update({"action_trigger": "generate_more", "action_param": "Tình huống"}); st.rerun()
                if st.button("➕ Giảm giá", key="g2_sale", use_container_width=True): st.session_state.update({"action_trigger": "generate_more", "action_param": "Giảm giá/bán hàng"}); st.rerun()
            else:
                if st.button("➕ Gọi Thêm 5 Kịch Bản", key="g2_def", use_container_width=True): st.session_state.update({"action_trigger": "generate_more", "action_param": selected_strategy}); st.rerun()
        
        with col_right:
            st.markdown("### 📋 Kịch Bản Chưa Render Chi Tiết")
            for item in [sc for sc in all_combined_scripts_list if int(sc.get("id", 0)) not in st.session_state.generated_details]:
                if st.button(f"✨ Tạo #{item['id']}: {item['title'][:30]}...", key=f"nav_{item['id']}", use_container_width=True): st.session_state.update({"action_trigger": "create_detail", "action_param": item['id']}); st.rerun()
    
