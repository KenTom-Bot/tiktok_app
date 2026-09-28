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
    "🛒 TikTok Shop & Bán Hàng", 
    "👶 Mẹ & Bé & Cùng Con Học", 
    "📺 TVC Quảng Cáo & Thương Hiệu Cao Cấp",
    "🏡 Nhà Cửa, Kiến Trúc & Cảnh Quan", 
    "🌿 Du Lịch & Phong Cảnh Đất Nước", 
    "🚗 Xe Cộ & Trải Nghiệm Lái",
    "🍲 Ẩm Thực & Đời Sống", 
    "📖 Đời Sống & Giáo Dục", 
    "🏛️ Lịch Sử & Tín Ngưỡng Di Sản",
    "🏢 Giới Thiệu Doanh Nghiệp"
]

# ==============================================================================
# 2. KHỞI TẠO SESSION STATE CHUẨN
# ==============================================================================
if "is_logged_in" not in st.session_state:
    st.session_state.update({
        "is_logged_in": False, 
        "current_user_email": "",
        "licensed_accounts": {
            ADMIN_EMAIL: {
                "contact": ADMIN_EMAIL, 
                "roles": ["Tất cả thể loại"], 
                "expires_at": "2099-12-31"
            }
        },
        "projects_library": {}, 
        "content_analysis": None,
        "all_scripts": [], 
        "cloned_scripts": [], 
        "expanded_scripts": [],
        "generated_details": {}, 
        "active_script_id": None,
        "active_project_title": "Chiến dịch mới", 
        "character_profiles": [],
        "file_uploader_key": 0, 
        "action_trigger": None, 
        "action_param": None,
        "scroll_to_top": False, 
        "last_loaded_file_id": None
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
    .loading-pulse { animation: pulse 1.5s infinite; color: #2563eb; font-weight: bold; text-align: center; padding: 10px; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. HÀM TIỆN ÍCH & LỌC JSON CHỐNG LỖI CỰC MẠNH
# ==============================================================================
def process_login(login_val):
    login_val = login_val.strip()
    if not login_val: 
        st.error("⚠️ Vui lòng nhập tài khoản.")
        return
    acc = st.session_state.licensed_accounts.get(login_val)
    if acc and datetime.now() <= datetime.strptime(acc["expires_at"], "%Y-%m-%d"):
        st.session_state.update({"is_logged_in": True, "current_user_email": login_val})
        st.success("✅ Đăng nhập thành công!")
        time.sleep(0.5)
        st.rerun()
    else: 
        st.error("❌ Tài khoản không tồn tại hoặc đã hết hạn.")

def format_analysis_field(field_val) -> str:
    if isinstance(field_val, dict): 
        return "<br>".join([f"• <b>{str(k).replace('_', ' ').title()}:</b> {str(v)}" for k, v in field_val.items()])
    elif isinstance(field_val, list): 
        return "<br>".join([f"• {str(item)}" for item in field_val])
    
    text = str(field_val).strip()
    text = re.sub(r'<<\.?', '', text).replace('<b>', '').replace('</b>', '')
    lines = [l.strip() for l in text.split('<br>') if l.strip()]
    return "".join([f"<div style='margin-top: 6px;'>{l}</div>" if l.startswith('•') else f"<div style='margin-left: 15px; margin-top: 4px;'>• {l}</div>" for l in lines]) if lines else text

def clean_and_parse_json(text_content: str):
    text = text_content.strip()
    # Tìm kiếm khối JSON thực sự để loại bỏ rác AI sinh ra
    start_idx_dict = text.find('{')
    start_idx_list = text.find('[')
    
    if start_idx_dict != -1 and start_idx_list != -1:
        start_idx = min(start_idx_dict, start_idx_list)
    elif start_idx_dict != -1:
        start_idx = start_idx_dict
    else:
        start_idx = start_idx_list

    end_idx_dict = text.rfind('}')
    end_idx_list = text.rfind(']')
    
    if end_idx_dict != -1 and end_idx_list != -1:
        end_idx = max(end_idx_dict, end_idx_list)
    elif end_idx_dict != -1:
        end_idx = end_idx_dict
    else:
        end_idx = end_idx_list

    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
        text = text[start_idx:end_idx+1]
        
    try: 
        return json.loads(text)
    except Exception as e: 
        raise Exception(f"Lỗi đọc JSON từ AI: {e}\nNội dung lỗi: {text[:100]}...")

def safe_copy_button(text_to_copy, label):
    st.code(text_to_copy, language="text")

# ==============================================================================
# 5. HỆ THỐNG PROMPT LÕI (AI ENGINE RULES)
# ==============================================================================
def get_strategy_rules(mode: str, strategy: str, target_audience: str) -> str:
    rules = f"- ĐỐI TƯỢNG: Nhắm vào tệp {target_audience}.\n"
    if "Bán Hàng" in mode or "Mẹ & Bé" in mode:
        if "Review" in strategy: 
            rules += "- CHIẾN LƯỢC REVIEW: Đập hộp, test tính năng chân thực, UGC review.\n"
        elif "Tình huống" in strategy: 
            rules += "- CHIẾN LƯỢC TÌNH HUỐNG/DRAMA: Mâu thuẫn đời sống, bẻ lái lồng ghép sản phẩm.\n"
        else: 
            rules += "- CHIẾN LƯỢC BÁN HÀNG: Tập trung xưởng, kho, showroom, thúc đẩy xả kho.\n"
    else: 
        rules += f"- CHIẾN LƯỢC: {strategy}. Tạo kịch bản cuốn hút.\n"
    return rules

def get_system_instructions(mode, style, aspect_ratio, goal, target_duration_mins, char_rules, strategy, audience, audio_mode):
    fmt = "9:16 vertical cinematic format" if aspect_ratio == "9:16" else "16:9 widescreen format"
    dur = "THỜI LƯỢNG: 3-5 phân cảnh linh hoạt." if target_duration_mins <= 0.5 else f"THỜI LƯỢNG: {int(target_duration_mins * 60)} GIÂY chia phân cảnh linh hoạt."
    strategy_instructions = get_strategy_rules(mode, strategy, audience)
    
    audio_rule = ""
    if audio_mode == "Nhân vật thoại trực tiếp":
        audio_rule = '8. TRỰC TIẾP LIP-SYNC: Trong `video_prompt`, BẮT BUỘC chèn lại nguyên văn thoại tiếng Việt (Ví dụ: `Character speaking in Vietnamese: "..."`) để AI khớp khẩu hình.'
    else:
        audio_rule = '8. AUDIO-FIRST (LỒNG TIẾNG SAU): Trong `video_prompt`, TUYỆT ĐỐI KHÔNG ghi lại thoại tiếng Việt. Chỉ miêu tả: `Speaking in Vietnamese with expressive emotion`.'

    return f"""
BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL ĐA NĂNG.
PHONG CÁCH: {style.upper()} | KHUNG HÌNH: {fmt} | MỤC TIÊU: {goal}
{dur}

🛑 QUY TẮC BẮT BUỘC:
1. TRẢ VỀ JSON HỢP LỆ. KHÔNG XUỐNG DÒNG (\\n) TRONG CHUỖI.
2. LUÔN CHÈN "Vietnamese" cho nhân vật.
{char_rules}
4. CẤM HIỂN THỊ UI: Ép lệnh "Cinematic shot ONLY. ABSOLUTELY NO UI elements".
5. BẢO TOÀN SẢN PHẨM KHỐI LƯỢNG NHỎ (MACRO LOCK): Đối với sản phẩm kích thước nhỏ/kỹ thuật, BẮT BUỘC phải dùng góc máy MACRO SHOT hoặc EXTREME CLOSE-UP. Kèm lệnh "strictly NO hands obscuring" để giữ hình khối không bị méo.
6. {strategy_instructions}
7. BỘ LỌC TỪ KHÓA: Cấm giá tiền cụ thể. Không bịa mùa vụ. Dùng "mùa cao điểm".
{audio_rule}
"""

def generate_char_rules_string(profiles, is_sales_mode=False):
    if not profiles: 
        return "3. ĐỒNG NHẤT NHÂN VẬT: Bắt buộc có nhân vật thống nhất."
    
    rules = "3. KHÓA KHUÔN MẶT KOC VÀ TRANG PHỤC:\n"
    for p in profiles: 
        # Fix lỗi cú pháp Python: tách hàm replace ra ngoài chuỗi f-string
        role_clean = p['role'].replace('"', "'")
        rules += f"   - Nhân vật {p['id']} ('{role_clean}'): Lệnh prompt 'Character {p['id']} ({role_clean}) maintaining identical facial features, exact hairstyle, body proportions, and the exact same outfit across all scenes'.\n"
    return rules

# ==============================================================================
# 6. GỌI API GEMINI VÀ XỬ LÝ LÕI KỊCH BẢN
# ==============================================================================
def call_gemini_with_retry(payload, sys_inst):
    for attempt in range(4):
        try:
            res = client.models.generate_content(
                model="gemini-3.6-flash", 
                contents=payload, 
                config=types.GenerateContentConfig(
                    system_instruction=sys_inst, 
                    response_mime_type="application/json"
                )
            )
            return clean_and_parse_json(res.text)
        except Exception as e:
            if "429" in str(e): 
                time.sleep(15)
            elif "503" in str(e): 
                time.sleep(3 * (attempt + 1))
            else: 
                time.sleep(4)
    raise Exception("Lỗi kết nối Gemini API. Vui lòng thử lại.")

def create_scene_details_for_id(target_id: int, current_mode: str, current_style: str, aspect_ratio: str, goal: str, target_duration_mins: float, current_strategy: str, audio_mode: str):
    all_sources = (st.session_state.all_scripts or []) + (st.session_state.cloned_scripts or []) + (st.session_state.expanded_scripts or [])
    outline = next((sc for sc in all_sources if isinstance(sc, dict) and int(sc.get("id", 0)) == int(target_id)), None)
    if not outline: raise Exception(f"Không tìm thấy kịch bản #{target_id}.")
    
    product_ctx = st.session_state.get("current_input_context", "").replace('"', "'")
    safe_title = outline.get('title', '').replace('"', "'").replace('\n', ' ')
    safe_setting = outline.get('setting_style', '').replace('"', "'").replace('\n', ' ')
    duration_str = "16s - 32s (Tối ưu Credit)" if target_duration_mins <= 0.5 else f"{int(target_duration_mins * 60)}s"

    profiles = st.session_state.get("character_profiles", [])
    if profiles:
        identity_lock_rules = " AND ".join([f"Character {p['id']} ({p['role']}) maintaining identical facial features, exact hairstyle, body proportions, and the exact same outfit across all scenes" for p in profiles])
        profiles_desc = f"DANH SÁCH DIỄN VIÊN ĐÃ ĐĂNG KÝ:\n" + "\n".join([f"- Diễn viên {p['id']}: '{p['role']}'" for p in profiles])
    else:
        identity_lock_rules = "Consistent characters with fixed facial structure and unchanging outfits"
        profiles_desc = "Đồng nhất nhân vật qua các cảnh."

    char_rules_str = generate_char_rules_string(profiles, "Bán Hàng" in current_mode)
    dna_data = st.session_state.get("content_analysis", {})
    target_audience = dna_data.get("primary_target_audience", "Người dùng")
    
    prompt_detail = f"""
    Ngữ cảnh: "{product_ctx}" | Khách hàng: {target_audience}
    Kịch bản: ID {target_id} - {safe_title} | Bối cảnh gốc: {safe_setting}
    CHIẾN LƯỢC: {current_strategy} | CHẾ ĐỘ ÂM THANH: {audio_mode}
    {profiles_desc}
    
    🛑 QUY ĐỊNH TỐI CAO ĐỂ TẠO VIDEO TRIỆU VIEW:
    1. ĐỒNG BỘ TUYỆT ĐỐI BỐI CẢNH: Mọi phân cảnh PHẢI GIỮ NGUYÊN BỐI CẢNH ({safe_setting}). Nhân vật khóa bằng: [{identity_lock_rules}].
    2. KHÓA GÓC MÁY TỰ ĐỘNG: Cảnh test tính năng sản phẩm bắt buộc phải chuyển sang MACRO SHOT hoặc EXTREME CLOSE-UP để mô hình AI vẽ sắc nét sản phẩm.
    3. QUY TẮC ÂM THANH: Phải viết lệnh theo chuẩn của `{audio_mode}`.
    4. KHÓA MÀU SẮC THỰC TẾ: Sản phẩm khớp chính xác hình khối, màu sắc từ ảnh tham chiếu gốc.
    
    Xuất 1 Dict JSON (KHÔNG DÙNG DẤU BA CHẤM):
    {{
      "id": {target_id}, "title": "{safe_title}", "setting_style": "{safe_setting}",
      "script_outfit_setup": "Trang phục cố định theo hồ sơ",
      "voice_profile": {{"gender": "Hỗn hợp Nam/Nữ", "tone": "Biểu cảm thực tế, dồn dập"}},
      "total_estimated_duration": "{duration_str}",
      "scenes": [
        {{
          "scene_number": 1, "duration": "8s", 
          "scene_setting": "[Mô tả bối cảnh không gian cố định và nỗi đau mở đầu]", 
          "transition_type": "Mở đầu (Hook)", 
          "voice_director_vn": "[Giọng bức xúc, thực tế]", 
          "dialogues": [ {{"speaker": "Nhân vật A", "dialogue": "[Thoại mở đầu phản ánh nỗi đau]"}} ],
          "image_prompt": "A 9:16 [Điền: Medium Shot / Wide Shot] featuring {identity_lock_rules} inside the exact same consistent environment ({safe_setting}). The physical product matching the exact reference is featured. Cinematic ONLY. NO UI.", 
          "video_prompt": "[Viết Video Prompt tuân thủ nghiêm ngặt Luật Chế độ Âm thanh (Lip-sync hoặc Audio-first). Kèm mô tả hành động]"
        }},
        {{
          "scene_number": 2, "duration": "6s", 
          "scene_setting": "[Mô tả giữ nguyên không gian, chuyển Macro/Extreme Close-up test giải pháp]", 
          "transition_type": "Cắt cứng (Hard Cut)", 
          "voice_director_vn": "[Giọng phân tích, tự tin]", 
          "dialogues": [ {{"speaker": "Nhân vật B", "dialogue": "[Thoại đưa ra giải pháp]"}} ],
          "image_prompt": "A 9:16 [Điền: Extreme Close-up / Macro Shot] featuring the physical product matching the exact reference in ({safe_setting}). Product fully visible, strictly NO hands obscuring. Cinematic ONLY. NO UI.", 
          "video_prompt": "[Viết Video Prompt. Chú ý quay rõ sản phẩm, không biến dạng hình khối]"
        }}
      ]
    }}
    LƯU Ý: TẠO 3-5 SCENE TÙY Ý TƯỞNG. ĐIỀN ĐẦY ĐỦ CÁC NGOẶC VUÔNG [...].
    """
    sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins, char_rules_str, current_strategy, target_audience, audio_mode)
    res = call_gemini_with_retry([prompt_detail], sys_inst)
    st.session_state.generated_details[target_id] = res[0] if isinstance(res, list) else res

def add_five_scripts_continuation(current_mode, current_style, aspect_ratio, goal, target_duration_mins, current_strategy, audio_mode):
    all_sources = (st.session_state.all_scripts or []) + (st.session_state.cloned_scripts or []) + (st.session_state.expanded_scripts or [])
    cur_len = len(all_sources)
    product_ctx = st.session_state.get("current_input_context", "").replace('"', "'")
    dna_data = st.session_state.get("content_analysis", {}) 
    char_rules_str = generate_char_rules_string(st.session_state.get("character_profiles", []), "Bán Hàng" in current_mode)
    
    prompt_more = f"""
    DỮ LIỆU SẢN PHẨM GỐC: {json.dumps(dna_data, ensure_ascii=False)} | Ghi chú: "{product_ctx}"
    Hãy tạo thêm ĐÚNG 5 kịch bản mới (id từ {cur_len + 1} đến {cur_len + 5}) theo CHIẾN LƯỢC: {current_strategy}.
    
    Xuất JSON chuẩn với key 'script_outlines' chứa 5 OBJECT:
    {{
      "script_outlines": [
        {{"id": {cur_len + 1}, "title": "[Tên]", "setting_style": "[Bối cảnh]", "script_outfit_setup": "[Đồ]", "angle": "[Góc]", "target_hook": "[Hook]", "recommended_scenes_count": "Linh hoạt 3-5 cảnh", "voice_profile": {{"gender": "Nam/Nữ", "tone": "Năng lượng"}}}}
      ]
    }}
    """
    sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins, char_rules_str, current_strategy, "", audio_mode)
    res = call_gemini_with_retry([prompt_more], sys_inst)
    new_scripts = res.get("script_outlines", [])
    for i, sc in enumerate(new_scripts): 
        sc["id"] = cur_len + i + 1
    st.session_state.expanded_scripts.extend(new_scripts)

def clone_script_id(target_id, current_mode, current_style, aspect_ratio, goal, target_duration_mins, current_strategy, audio_mode):
    target_script = st.session_state.generated_details[target_id]
    cur_len = len((st.session_state.all_scripts or []) + (st.session_state.cloned_scripts or []) + (st.session_state.expanded_scripts or []))
    char_rules_str = generate_char_rules_string(st.session_state.get("character_profiles", []), "Bán Hàng" in current_mode)
    prompt = f"Dựa trên kịch bản gốc: {json.dumps(target_script, ensure_ascii=False)}. Tạo ĐÚNG 5 biến thể mới (id từ {cur_len+1} đến {cur_len+5}). Xuất JSON key 'cloned_outlines'."
    sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins, char_rules_str, current_strategy, "", audio_mode)
    res_c = call_gemini_with_retry([prompt], sys_inst)
    cloned_list = res_c.get("cloned_outlines", [])
    for idx_c, cl in enumerate(cloned_list): 
        cl["id"] = cur_len + idx_c + 1
    st.session_state.cloned_scripts.extend(cloned_list)

# ==============================================================================
# 7. THANH BÊN (SIDEBAR UI)
# ==============================================================================
with st.sidebar:
    if not st.session_state.is_logged_in:
        st.markdown("### 🔐 **Đăng Nhập Hệ Thống**")
        with st.form("login_form"):
            login_input = st.text_input("Nhập Email / SĐT:", placeholder="vd: admin@binhnguyen.vn")
            if st.form_submit_button("🔑 Đăng Nhập", use_container_width=True): 
                process_login(login_input)
    
    if st.session_state.is_logged_in:
        st.markdown("### 🗂️ **Quản Lý Dự Án**")
        if st.button("➕ Tạo Dự Án Mới", type="primary", use_container_width=True):
            st.session_state.update({
                "content_analysis": None, "all_scripts": [], "cloned_scripts": [], 
                "expanded_scripts": [], "generated_details": {}, "character_profiles": [], 
                "active_script_id": None, "active_project_title": "Chiến dịch mới"
            })
            st.session_state.file_uploader_key += 1
            st.session_state.scroll_to_top = True
            st.rerun()

        project_title_input = st.text_input("Tên dự án hiện tại:", value=st.session_state.get("active_project_title", "Chiến dịch mới"))
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("💾 Lưu Dự Án", use_container_width=True):
                st.session_state.projects_library[f"proj_{int(time.time())}"] = {
                    "title": project_title_input, "mode": st.session_state.get("selected_mode", ""), 
                    "content_analysis": st.session_state.content_analysis,
                    "all_scripts": st.session_state.all_scripts, "cloned_scripts": st.session_state.cloned_scripts,
                    "expanded_scripts": st.session_state.expanded_scripts, "generated_details": st.session_state.generated_details,
                    "character_profiles": st.session_state.character_profiles
                }
                st.success("✅ Đã lưu!")
        with col_p2:
            export_data = {
                "title": project_title_input, "content_analysis": st.session_state.content_analysis, 
                "all_scripts": st.session_state.all_scripts, "cloned_scripts": st.session_state.cloned_scripts, 
                "expanded_scripts": st.session_state.expanded_scripts, "generated_details": st.session_state.generated_details, 
                "character_profiles": st.session_state.character_profiles
            }
            st.download_button("📥 Tải JSON", data=json.dumps(export_data, ensure_ascii=False, indent=2), file_name=f"{project_title_input.replace(' ', '_')}.json", mime="application/json", use_container_width=True)

        if st.session_state.projects_library:
            selected_load_id = st.selectbox("📂 Chọn dự án đã lưu:", options=list(st.session_state.projects_library.keys()), format_func=lambda x: st.session_state.projects_library[x]["title"])
            if st.button("📂 Mở Dự Án Này", use_container_width=True):
                p_data = st.session_state.projects_library[selected_load_id]
                st.session_state.update({
                    "active_project_title": p_data.get("title", "Dự án tải lên"), "content_analysis": p_data.get("content_analysis"), 
                    "all_scripts": p_data.get("all_scripts", []), "cloned_scripts": p_data.get("cloned_scripts", []), 
                    "expanded_scripts": p_data.get("expanded_scripts", []), "generated_details": p_data.get("generated_details", {}), 
                    "character_profiles": p_data.get("character_profiles", []), "active_script_id": None, "scroll_to_top": True
                })
                st.rerun()

        st.markdown("<div style='font-size: 0.85rem; color: #64748b; margin-top: 8px;'>Hoặc tải file dự án (.json):</div>", unsafe_allow_html=True)
        uploaded_project_file = st.file_uploader("📤 Tải file kịch bản", type=["json"], label_visibility="collapsed", key=f"project_uploader_{st.session_state.file_uploader_key}")
        if uploaded_project_file is not None:
            file_identifier = f"{uploaded_project_file.name}_{uploaded_project_file.size}"
            if st.session_state.get("last_loaded_file_id") != file_identifier:
                try:
                    loaded_proj = json.loads(uploaded_project_file.getvalue().decode("utf-8"))
                    st.session_state.update({
                        "active_project_title": loaded_proj.get("title", "Dự án tải lên"), "content_analysis": loaded_proj.get("content_analysis", None), 
                        "all_scripts": loaded_proj.get("all_scripts", []), "expanded_scripts": loaded_proj.get("expanded_scripts", []), 
                        "cloned_scripts": loaded_proj.get("cloned_scripts", []), "generated_details": {int(k): v for k, v in loaded_proj.get("generated_details", {}).items()}, 
                        "character_profiles": loaded_proj.get("character_profiles", []), "active_script_id": None, 
                        "last_loaded_file_id": file_identifier, "scroll_to_top": True
                    })
                    st.rerun()
                except Exception as e: 
                    st.error(f"❌ Lỗi đọc file JSON: {e}")

        # KHU VỰC QUẢN TRỊ ADMIN (Khôi phục toàn bộ chức năng chọn quyền và hạn dùng)
        if st.session_state.current_user_email == ADMIN_EMAIL:
            st.markdown("---")
            st.markdown("### ⚙️ **Quản Lý Tài Khoản (Admin)**")
            with st.form("add_license_form"):
                new_account_id = st.text_input("Email / SĐT khách hàng mới:")
                selected_roles = st.multiselect("Cấp quyền Thể loại:", ["Tất cả thể loại"] + ALL_MODULES, default=["Tất cả thể loại"])
                days_active = st.number_input("Số ngày sử dụng:", min_value=1, value=30)
                
                if st.form_submit_button("➕ Cấp Quyền Dùng Thử", use_container_width=True):
                    if new_account_id.strip():
                        expires_at = (datetime.now() + timedelta(days=days_active)).strftime("%Y-%m-%d")
                        st.session_state.licensed_accounts[new_account_id.strip()] = {
                            "contact": new_account_id.strip(), 
                            "roles": selected_roles, 
                            "expires_at": expires_at
                        }
                        st.success(f"Đã cấp quyền: {new_account_id.strip()} - Hạn: {expires_at}")
                        time.sleep(0.5)
                        st.rerun()

        # KHUNG LIÊN HỆ ĐÃ ĐƯỢC KHÔI PHỤC
        st.markdown("---")
        st.markdown("""
        <div style="background: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; text-align: center;">
            <b style="color: #0f172a; font-size: 1rem;">💬 Hỗ Trợ Dịch Vụ 24/7</b><br>
            <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 12px;">Liên hệ ngay nếu cần nâng cấp tài khoản!</div>
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <a href="https://zalo.me/0968484369" target="_blank" style="background: #0068ff; color: white; padding: 8px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 13px;">💬 Zalo: 096 8484 369</a>
                <a href="#" target="_blank" style="background: #1877F2; color: white; padding: 8px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 13px;">📘 Trực tuyến Facebook</a>
                <a href="#" target="_blank" style="background: #000000; color: white; padding: 8px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 13px;">🎵 Theo dõi TikTok</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🚪 Đăng Xuất", use_container_width=True):
            st.session_state.is_logged_in = False
            st.rerun()

# ==============================================================================
# 8. TIÊU ĐỀ & TÙY CHỈNH KỊCH BẢN CHÍNH
# ==============================================================================
st.markdown("""
<div class="header-container">
    <div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div>
    <div class="sub-title">Tối Ưu Chuyển Đổi, Đồng Nhất Tuyệt Đối Nhân Vật & Sản Phẩm</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.is_logged_in:
    st.info("👈 Vui lòng đăng nhập ở thanh công cụ bên trái để kích hoạt hệ thống.")
    st.stop()

col_mode, col_style = st.columns([1.5, 1])
with col_mode: 
    selected_mode = st.selectbox("🎯 Chọn Thể Loại Nội Dung:", options=ALL_MODULES, key="selected_mode")

# Đổi đúng tên chiến lược theo yêu cầu
if "Bán Hàng" in selected_mode or "Mẹ & Bé" in selected_mode:
    strat_options = ["Review thực tế", "Tình huống", "Giảm giá/bán hàng"]
else:
    strat_options = ["Viral / Bắt trend giải trí", "Chia sẻ kiến thức", "Kể chuyện cảm xúc (Storytelling)"]

with col_style:
    # ĐÃ KHÔI PHỤC ĐẦY ĐỦ CÁC PHONG CÁCH VÀ FIX LỖI HARDCODE
    style_mapping = {
        "Điện Ảnh Chân Thực (Cinematic Realism)": "Cinematic Realism",
        "Hoạt Hình 3D (3D Animation)": "3D Animation",
        "Studio Tối Giản (Minimalist)": "Minimalist Studio",
        "Phóng Sự Tài Liệu (Documentary)": "Documentary style",
        "Góc Nhìn KOC (POV/UGC)": "POV UGC style"
    }
    selected_style_vn = st.selectbox("🎨 Phong Cách Hình Ảnh:", options=list(style_mapping.keys()))
    selected_style = style_mapping[selected_style_vn] # Trả về đúng prompt tiếng Anh cho AI

    st.markdown("""
    <div style="font-size: 0.85rem; color: #64748b; padding-top: 4px;">
    <b>💡 Mẹo Đạo Diễn:</b><br>
    - <b>Cinematic:</b> TVC, Du lịch, Review cao cấp.<br>
    - <b>Góc Nhìn KOC:</b> Đập hộp, TikTok Shop thực chiến.<br>
    - <b>Hoạt Hình 3D:</b> Mẹ & Bé, Kể chuyện.
    </div>
    """, unsafe_allow_html=True)

col_strat, col_ratio, col_time, col_audio = st.columns([1.5, 1, 1, 1.2])
with col_strat: 
    selected_strategy = st.selectbox("🧠 Chiến lược Kịch bản:", options=strat_options)
with col_ratio: 
    selected_aspect = "9:16" if "9:16" in st.selectbox("Tỷ lệ khung hình:", ["9:16 (Dọc TikTok/Reels)", "16:9 (Ngang YouTube)"]) else "16:9"
with col_time: 
    # CHỈ RIÊNG TIKTOK SHOP MỚI KHÓA 3-5 CẢNH, CÁC THỂ LOẠI KHÁC TỰ DO CHỌN PHÚT
    if selected_mode == "🛒 TikTok Shop & Bán Hàng":
        st.markdown("<div style='margin-top: 28px; font-weight: bold; color: #d97706;'>⏱️ Tối ưu: 3-5 cảnh (20-30s)</div>", unsafe_allow_html=True)
        target_duration_mins = 0.5 
    else:
        target_duration_mins = st.number_input("⏱️ Thời lượng (Phút):", min_value=0.5, max_value=30.0, value=1.0, step=0.5)
with col_audio: 
    selected_audio_mode = st.selectbox("🎙️ Chế độ Âm thanh:", ["Nhân vật thoại trực tiếp", "Lồng tiếng sau (Voiceover)"])
content_goal = "Sales & Conversion"

# ==============================================================================
# 9. XỬ LÝ TRIGGER (ĐÃ FIX LỖI MÀN HÌNH TRẮNG BẰNG CÁCH CHUYỂN VIEW_DETAIL RA NGOÀI)
# ==============================================================================
if st.session_state.action_trigger in ["create_detail", "clone_script", "generate_more"]:
    action = st.session_state.action_trigger
    param = st.session_state.action_param
    st.session_state.action_trigger, st.session_state.action_param = None, None
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown(f"<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG XỬ LÝ AI... VUI LÒNG ĐỢI!</div>", unsafe_allow_html=True)
        try:
            if action == "create_detail":
                create_scene_details_for_id(int(param), selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, selected_strategy, selected_audio_mode)
                st.session_state.active_script_id = int(param)
            elif action == "clone_script":
                clone_script_id(int(param), selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, selected_strategy, selected_audio_mode)
            elif action == "generate_more":
                add_five_scripts_continuation(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, param or selected_strategy, selected_audio_mode)
            
            st.session_state.scroll_to_top = True
            time.sleep(0.2)
            st.rerun()
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")
            if st.button("🔄 Thử lại ngay"): 
                st.rerun()
    st.stop()

# ==============================================================================
# 10. KHU VỰC NHẬP LIỆU
# ==============================================================================
input_text = st.text_area("✍️ Tóm tắt ý tưởng, chủ đề hoặc mô tả dự án/sản phẩm:", height=80, key="main_input_context")
col_p_img, col_c_img = st.columns([1, 1])
with col_p_img: 
    uploaded_files = st.file_uploader("📦 Tải ảnh Sản phẩm (Làm gốc tham chiếu Khóa Hình Khối)", type=["jpg", "png"], accept_multiple_files=True)
with col_c_img: 
    num_chars = st.number_input("👤 Số lượng Diễn viên tham chiếu", min_value=0, max_value=8, step=1)
    char_inputs = []
    if num_chars > 0:
        grid_cols = st.columns(min(num_chars, 4))
        for i in range(num_chars):
            with grid_cols[i % 4].container(border=True):
                c_role = st.text_input(f"Vai trò DV {i+1}", placeholder="VD: Nữ MC KOC")
                c_file = st.file_uploader(f"Ảnh DV {i+1}", type=["jpg", "png"], key=f"c_img_{i}")
                if c_file and c_role.strip(): 
                    char_inputs.append({"id": i+1, "role": c_role.strip(), "file": c_file})

if st.button("🚀 Phân Tích DNA & Lên Ý Tưởng", type="primary", use_container_width=True, disabled=not (input_text.strip() or uploaded_files)):
    with st.spinner("⏳ Đang phân tích chuyên sâu..."):
        try:
            st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
            st.session_state.current_input_context = input_text.strip()
            char_rules_str = generate_char_rules_string(st.session_state.character_profiles, "Bán Hàng" in selected_mode)
            
            payload = ["ẢNH SẢN PHẨM:"] + [types.Part.from_bytes(data=f.getvalue(), mime_type=f.type or "image/jpeg") for f in (uploaded_files or [])]
            for c in char_inputs: 
                payload.extend([f"ẢNH NHÂN VẬT {c['id']} ({c['role']}):", types.Part.from_bytes(data=c['file'].getvalue(), mime_type=c['file'].type or "image/jpeg")])
            payload.append(f"Phân tích '{selected_mode}' - {selected_strategy}. Mô tả: '{st.session_state.current_input_context}'. KHÔNG dùng giá tiền cụ thể. Xuất JSON content_analysis và script_outlines (5 object).")
            
            res = call_gemini_with_retry(payload, get_system_instructions(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, char_rules_str, selected_strategy, "Người tiêu dùng", selected_audio_mode))
            st.session_state.update({
                "content_analysis": res.get("content_analysis"), 
                "all_scripts": res.get("script_outlines", []), 
                "cloned_scripts": [], 
                "expanded_scripts": [], 
                "generated_details": {}, 
                "active_script_id": None, 
                "scroll_to_top": True
            })
            st.rerun()
        except Exception as e: 
            st.error(f"❌ Lỗi: {e}")

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

    # GIAI ĐOẠN 1: TỔNG QUAN DANH SÁCH KỊCH BẢN
    if all_combined_scripts_list and st.session_state.active_script_id is None:
        completed_scripts = [sc for sc in all_combined_scripts_list if int(sc.get("id", 0)) in st.session_state.generated_details]
        pending_scripts = [sc for sc in all_combined_scripts_list if int(sc.get("id", 0)) not in st.session_state.generated_details]

        st.markdown("### 🎬 Kịch Bản Đã Hoàn Thiện")
        for sc in completed_scripts:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2.5, 1, 1])
                c1.markdown(f"**#{sc['id']}. {sc.get('title')}** — <span class='badge-ready'>SẴN SÀNG</span>", unsafe_allow_html=True)
                # Dùng update state trực tiếp cho View Detail để không kẹt Trigger
                if c2.button("👁️ Xem chi tiết", key=f"btn_v1_{sc['id']}", use_container_width=True): 
                    st.session_state.update({"active_script_id": sc['id'], "scroll_to_top": True})
                    st.rerun()
                if c3.button("🚀 Nhân bản", key=f"btn_c1_{sc['id']}", use_container_width=True): 
                    st.session_state.update({"action_trigger": "clone_script", "action_param": sc['id']})
                    st.rerun()

        st.markdown("### ⏳ Ý Tưởng Đang Chờ (Chưa Dựng Chi Tiết)")
        for sc in pending_scripts:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**#{sc['id']}. {sc.get('title')}**")
                if c2.button("✨ Tạo chi tiết ngay", key=f"btn_p1_{sc['id']}", type="primary", use_container_width=True): 
                    st.session_state.update({"action_trigger": "create_detail", "action_param": sc['id']})
                    st.rerun()

        st.markdown("---")
        st.markdown("### ➕ Mở Rộng Thêm Kịch Bản Mới")
        if "Bán Hàng" in selected_mode or "Mẹ & Bé" in selected_mode:
            cb1, cb2, cb3 = st.columns(3)
            if cb1.button("➕ 5 Kịch bản Review", use_container_width=True): 
                st.session_state.update({"action_trigger": "generate_more", "action_param": "Review thực tế"}); st.rerun()
            if cb2.button("➕ 5 Kịch bản Tình huống", use_container_width=True): 
                st.session_state.update({"action_trigger": "generate_more", "action_param": "Tình huống"}); st.rerun()
            if cb3.button("➕ 5 Kịch bản Giảm giá", use_container_width=True): 
                st.session_state.update({"action_trigger": "generate_more", "action_param": "Giảm giá/bán hàng"}); st.rerun()
        else:
            if st.button("➕ Gọi Thêm 5 Kịch Bản Mới", use_container_width=True): 
                st.session_state.update({"action_trigger": "generate_more", "action_param": selected_strategy}); st.rerun()

    # GIAI ĐOẠN 2: CHI TIẾT KỊCH BẢN ĐÃ CHỌN
    if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details:
        if st.button("⬅️ Quay lại danh sách tổng", use_container_width=False): 
            st.session_state.update({"active_script_id": None, "scroll_to_top": True})
            st.rerun()

        raw_data = st.session_state.generated_details[st.session_state.active_script_id]
        active_script = raw_data[0] if isinstance(raw_data, list) else raw_data
        st.markdown(f"### 🎬 KỊCH BẢN CHI TIẾT: {str(active_script.get('title')).upper()}")
        
        for idx, scene in enumerate(active_script.get("scenes", []), start=1):
            if not isinstance(scene, dict): continue
            st.markdown(f"#### 📍 Phân cảnh {idx} ({scene.get('duration', '6s')}) — [ {scene.get('transition_type', 'Cắt cảnh')} ]")
            st.markdown(f"🏛️ **Bối cảnh & Góc máy:** *{scene.get('scene_setting')}*")
            st.markdown(f"**🎙️ Yêu cầu Đạo diễn Voice:** *{scene.get('voice_director_vn')}*")
            
            dialogues = scene.get("dialogues", [])
            full_voice = ""
            if dialogues:
                st.markdown("**💬 Lời Thoại (Dùng để thu âm hoặc Lip-sync):**")
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
                if st.button("➕ Review", key="g2_rev", use_container_width=True): 
                    st.session_state.update({"action_trigger": "generate_more", "action_param": "Review thực tế"}); st.rerun()
                if st.button("➕ Tình huống", key="g2_dra", use_container_width=True): 
                    st.session_state.update({"action_trigger": "generate_more", "action_param": "Tình huống"}); st.rerun()
                if st.button("➕ Giảm giá", key="g2_sale", use_container_width=True): 
                    st.session_state.update({"action_trigger": "generate_more", "action_param": "Giảm giá/bán hàng"}); st.rerun()
            else:
                if st.button("➕ Gọi Thêm 5 Kịch Bản", key="g2_def", use_container_width=True): 
                    st.session_state.update({"action_trigger": "generate_more", "action_param": selected_strategy}); st.rerun()
        
        with col_right:
            st.markdown("### 📋 Kịch Bản Chưa Render Chi Tiết")
            for item in [sc for sc in all_combined_scripts_list if int(sc.get("id", 0)) not in st.session_state.generated_details]:
                if st.button(f"✨ Tạo #{item['id']}: {item['title'][:30]}...", key=f"nav_{item['id']}", use_container_width=True): 
                    st.session_state.update({"action_trigger": "create_detail", "action_param": item['id']}); st.rerun()
