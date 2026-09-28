import streamlit as st
from google import genai
from google.genai import types
import json
import re
import time
from datetime import datetime
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
    "🧘 Chữa Lành & Phong Cách Sống", "📢 Phóng Sự & Thông Điệp Xã Hội", "🏢 Giới Thiệu Doanh Nghiệp"
]

# ==============================================================================
# 2. KHỞI TẠO SESSION STATE CHUẨN
# ==============================================================================
if "is_logged_in" not in st.session_state:
    st.session_state.update({
        "is_logged_in": False, "current_user_email": "",
        "licensed_accounts": {ADMIN_EMAIL: {"contact": ADMIN_EMAIL, "roles": ["Tất cả thể loại"], "expires_at": "2099-12-31"}},
        "projects_library": {}, "content_analysis": None,
        "all_scripts": [], "cloned_scripts": [], "expanded_scripts": [],
        "generated_details": {}, "active_script_id": None,
        "character_profiles": [], "file_uploader_key": 0,
        "action_trigger": None, "action_param": None,
        "scroll_to_top": False
    })

# Tính năng Tự động cuộn trang (Auto-scroll) lên đầu để tăng trải nghiệm UX
if st.session_state.get('scroll_to_top', False):
    components.html("<script>window.parent.document.querySelector('.main').scrollTo(0,0);</script>", height=0)
    st.session_state.scroll_to_top = False

# ==============================================================================
# 3. CSS TÙY CHỈNH (GIAO DIỆN HIỆN ĐẠI)
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
# 4. HÀM TIỆN ÍCH & XỬ LÝ CHUỖI
# ==============================================================================
def process_login(login_val):
    login_val = login_val.strip()
    if not login_val:
        st.error("⚠️ Vui lòng nhập tài khoản.")
        return
    acc_info = st.session_state.licensed_accounts.get(login_val)
    if acc_info:
        exp_date = datetime.strptime(acc_info["expires_at"], "%Y-%m-%d")
        if datetime.now() > exp_date: st.error("❌ Tài khoản đã hết hạn.")
        else:
            st.session_state.is_logged_in = True
            st.session_state.current_user_email = login_val
            st.success("✅ Đăng nhập thành công!")
            time.sleep(0.5); st.rerun()
    else: st.error("❌ Không tìm thấy tài khoản. Liên hệ Admin.")

def format_analysis_field(field_val) -> str:
    if isinstance(field_val, dict): return "<br>".join([f"• <b>{str(k).replace('_', ' ').title()}:</b> {str(v)}" for k, v in field_val.items()])
    elif isinstance(field_val, list): return "<br>".join([f"• {str(item)}" for item in field_val])
    text = str(field_val).strip()
    text = re.sub(r'<<\.?', '', text).replace('<b>', '').replace('</b>', '')
    lines = [l.strip() for l in text.split('<br>') if l.strip()]
    formatted = [f"<div style='margin-top: 6px;'>{l}</div>" if l.startswith('•') else f"<div style='margin-left: 15px; margin-top: 4px;'>• {l}</div>" for l in lines if l]
    return "".join(formatted) if formatted else text

def clean_and_parse_json(text_content: str):
    text_content = text_content.strip()
    if text_content.startswith("```json"): text_content = text_content[7:]
    elif text_content.startswith("```"): text_content = text_content[3:]
    if text_content.endswith("```"): text_content = text_content[:-3]
    try: return json.loads(text_content.strip())
    except json.JSONDecodeError:
        text_content = text_content.replace('\n', ' ').replace('\r', '')
        text_content = re.sub(r',\s*}', '}', text_content)
        text_content = re.sub(r',\s*]', ']', text_content)
        try: return json.loads(text_content)
        except Exception as e: raise Exception(f"Lỗi cú pháp JSON từ AI: {e}")

def safe_copy_button(text_to_copy, button_label):
    st.code(text_to_copy, language="text")

# ==============================================================================
# 5. HỆ THỐNG PROMPT ĐIỀU HƯỚNG LÕI (AI ENGINE RULES)
# ==============================================================================
def get_strategy_rules(mode: str, strategy: str, target_audience: str) -> str:
    rules = f"- ĐỐI TƯỢNG: Kịch bản nhắm thẳng vào tệp khách hàng {target_audience}.\n"
    if "Bán Hàng" in mode or "Mẹ & Bé" in mode:
        if "Review" in strategy: rules += "- CHIẾN LƯỢC REVIEW THỰC TẾ: Ưu tiên góc máy đập hộp, test tính năng chân thực, UGC review.\n"
        elif "Tình huống" in strategy: rules += "- CHIẾN LƯỢC TÌNH HUỐNG/DRAMA: Xây dựng mâu thuẫn đời sống, bẻ lái (twist) lồng ghép sản phẩm vào cuối.\n"
        else: rules += "- CHIẾN LƯỢC GIẢM GIÁ/BÁN HÀNG: Tập trung không gian xưởng, kho, showroom, thúc đẩy xả kho.\n"
    else: rules += f"- CHIẾN LƯỢC: {strategy}. Tạo kịch bản chuyên nghiệp, cuốn hút.\n"
    return rules

def get_system_instructions(mode: str, style: str, aspect_ratio: str, goal: str, target_duration_mins: float, char_rules: str, strategy: str = "", audience: str = "") -> str:
    format_instruction = "9:16 vertical cinematic format, mobile-first framing" if aspect_ratio == "9:16" else "16:9 widescreen cinematic format"
    duration_rule = "THỜI LƯỢNG: Thiết kế kịch bản gồm 3 đến 5 phân cảnh linh hoạt." if target_duration_mins <= 0.5 else f"THỜI LƯỢNG: Phân bổ linh hoạt tổng {int(target_duration_mins * 60)} giây thành nhiều cảnh."
    strategy_instructions = get_strategy_rules(mode, strategy, audience)
    
    return f"""
BẠN LÀ TỔNG ĐẠO DIỄN VIRTUAL ĐA NĂNG CHO CÁC MÔ HÌNH VEO 3, KLING AI VÀ IMAGEN 3.
PHONG CÁCH: {style.upper()} | ĐỊNH DẠNG KHUNG HÌNH: {format_instruction} | MỤC TIÊU: {goal}
{duration_rule}

🛑 QUY TẮC BẮT BUỘC 100% (KHÔNG ĐƯỢC VI PHẠM):
1. TRẢ VỀ CHUẨN JSON. KHÔNG XUỐNG DÒNG BẰNG DẤU ENTER TRONG CHUỖI.
2. NHÂN VẬT & QUỐC TỊCH: Luôn chèn "Vietnamese" cho nhân vật để nhận diện dáng người châu Á.
{char_rules}
4. CẤM HIỂN THỊ UI: Ép lệnh "Cinematic shot ONLY. ABSOLUTELY NO UI elements, NO buttons" vào mọi prompt.
5. VẬT LÝ SẢN PHẨM: Ép lệnh "product is fully visible, strictly NO hands obscuring the main body".
6. {strategy_instructions}
7. BỘ LỌC TỪ KHÓA & COMPLIANCE: Tuyệt đối không dùng giá tiền con số cụ thể (VD: không viết 30k, 100 ngàn). KHÔNG thêm mùa vụ (mùa đông, mùa thu) nếu không có yêu cầu. Dùng từ "mùa cao điểm", "giáp Tết".
"""

def generate_char_rules_string(profiles, is_sales_mode=False):
    if not profiles: return "3. ĐỒNG NHẤT NHÂN VẬT: Bắt buộc có nhân vật thống nhất qua các phân cảnh."
    rules = "3. KHÓA KHUÔN MẶT KOC VÀ ĐỒNG BỘ TRANG PHỤC (IDENTITY LOCK):\n"
    for p in profiles: rules += f"   - Nhân vật {p['id']} (Vai '{p['role'].replace('"', "'")}'): Lệnh ép buộc trong prompt tiếng Anh: 'Character {p['id']} ({p['role']}) maintaining identical facial features, exact hairstyle, body proportions, and the exact same outfit across all scenes'.\n"
    return rules

# ==============================================================================
# 6. GỌI API GEMINI VÀ XỬ LÝ LÕI KỊCH BẢN (FINAL MASTER BUILD)
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
    if not outline: raise Exception(f"Không tìm thấy ID #{target_id} trong bộ nhớ.")
    
    product_ctx = st.session_state.get("current_input_context", "Dự án hiện tại").replace('"', "'")
    safe_title = outline.get('title', '').replace('"', "'").replace('\n', ' ')
    safe_setting = outline.get('setting_style', '').replace('"', "'").replace('\n', ' ')
    
    duration_str = "16s - 32s (Tối ưu Credit Veo 3)" if target_duration_mins <= 0.5 else f"{int(target_duration_mins * 60)}s ({target_duration_mins} phút)"

    # Xây dựng định danh chống sai lệch nhân vật
    profiles = st.session_state.get("character_profiles", [])
    if profiles:
        identity_lock_rules = " AND ".join([f"Character {p['id']} ({p['role']}) maintaining identical facial features, exact hairstyle, body proportions, and the exact same outfit across all scenes" for p in profiles])
        profiles_desc = "DANH SÁCH DIỄN VIÊN ĐÃ ĐĂNG KÝ (GIỮ NGUYÊN 100% DIỆN MẠO, TÓC, TRANG PHỤC):\n" + "\n".join([f"- Diễn viên {p['id']}: Vai '{p['role']}'" for p in profiles])
    else:
        identity_lock_rules = "Consistent characters with fixed facial structure and unchanging outfits"
        profiles_desc = "DANH SÁCH DIỄN VIÊN: Kịch bản đồng nhất nhân vật linh hoạt."

    char_rules_str = generate_char_rules_string(profiles, "Bán Hàng" in current_mode)
    dna_data = st.session_state.get("content_analysis", {})
    target_audience = dna_data.get("primary_target_audience", "Người dùng mục tiêu")
    
    # Prompt lõi tối ưu Đạo diễn đa nhân vật, bối cảnh đồng nhất, audio-first
    prompt_detail = f"""
    Ngữ cảnh gốc: "{product_ctx}" | Khách hàng mục tiêu: {target_audience}
    Kịch bản: ID {target_id} - {safe_title} | Bối cảnh không gian gốc: {safe_setting}
    CHIẾN LƯỢC KỊCH BẢN: {current_strategy}
    {profiles_desc}
    
    🛑 5 QUY CHUẨN ĐẠO DIỄN QUỐC TẾ BẮT BUỘC (CRITICAL):
    1. ĐỒNG BỘ BỐI CẢNH (SCENE CONTINUITY): Các phân cảnh PHẢI GIỮ NGUYÊN BỐI CẢNH KHÔNG GIAN, ánh sáng và bố cục ({safe_setting}). Nhân vật bị ép giữ diện mạo qua chuỗi khóa: [{identity_lock_rules}].
    2. KHÓA MÀU SẢN PHẨM THỰC TẾ: Sản phẩm phải khớp chính xác màu từ ảnh tham chiếu gốc (`the physical product matching the exact color, material, and branding from the uploaded product reference image`). CẤM TỰ TƯỞNG TƯỢNG MÀU.
    3. TỐI ƯU AUDIO FIRST (TÁCH BIỆT THOẠI VÀ VIDEO PROMPT): Mảng `dialogues` chứa lời thoại tiếng Việt có ngữ điệu. TRONG `video_prompt`, TUYỆT ĐỐI KHÔNG lặp lại nguyên văn lời thoại, chỉ cần ghi: `Speaking in Vietnamese with expressive emotion` kết hợp miêu tả hành động mấp máy môi, cử chỉ và âm thanh nền (ambient sound).
    4. CẤU TRÚC LINH HOẠT 3-5 CẢNH: Dựa vào tình huống thực tế, hãy viết 3, 4, hoặc 5 phân cảnh phù hợp để đẩy cao trào và chốt sale, cảnh 1 bắt buộc có Hook giữ chân.
    5. KHÔNG DÙNG CON SỐ GIÁ TIỀN VÀ MÙA VỤ: Dùng từ "mùa cao điểm", "giá cực tốt".
    
    Xuất 1 Dict JSON CHUẨN (KHÔNG DÙNG DẤU BA CHẤM, ĐIỀN KÍN CHỮ):
    {{
      "id": {target_id}, "title": "{safe_title}", "setting_style": "{safe_setting}",
      "script_outfit_setup": "Trang phục cố định không đổi theo hồ sơ nhân vật",
      "voice_profile": {{"gender": "Hỗn hợp Nam/Nữ", "tone": "Biểu cảm thực tế, dồn dập"}},
      "total_estimated_duration": "{duration_str}",
      "scenes": [
        {{
          "scene_number": 1, "duration": "8s", 
          "scene_setting": "[Mô tả chi tiết bối cảnh không gian cố định, góc quay và vấn đề/hook mở đầu]", 
          "transition_type": "Mở đầu (Hook giật gân)", 
          "voice_director_vn": "[Chỉ đạo giọng đọc: bức xúc, hoặc bất ngờ, năng lượng cao]", 
          "dialogues": [ {{"speaker": "Nhân vật A", "dialogue": "[Thoại tiếng Việt chạm đúng nỗi đau, có cảm thán !]"}} ],
          "image_prompt": "A 9:16 vertical cinematic shot featuring {identity_lock_rules} inside the exact same consistent environment ({safe_setting}). The physical product matching the exact color, material, and branding from the uploaded product reference image is featured. Cinematic shot ONLY. ABSOLUTELY NO UI elements.", 
          "video_prompt": "Audio: Characters speaking on-camera in Vietnamese with expressive emotional tone. Background ambient sound: realistic room tone. Visual: Cinematic multi-character shot showing {identity_lock_rules} maintaining identical outfits within the consistent environment ({safe_setting}). Product maintains rigid structural integrity."
        }},
        {{
          "scene_number": 2, "duration": "6s", 
          "scene_setting": "[Giữ nguyên bối cảnh không gian, chuyển góc máy cận để phân tích/trải nghiệm]", 
          "transition_type": "Cắt cứng (Hard Cut)", 
          "voice_director_vn": "[Chỉ đạo giọng đọc: phân tích, tự tin]", 
          "dialogues": [ {{"speaker": "Nhân vật B", "dialogue": "[Thoại đưa ra giải pháp/tính năng giải quyết vấn đề]"}} ],
          "image_prompt": "A 9:16 close-up shot featuring {identity_lock_rules} within the same consistent environment ({safe_setting}) and the physical product matching the exact reference. Product fully visible, strictly NO hands obscuring. Cinematic shot ONLY. NO UI elements.", 
          "video_prompt": "Audio: Character speaking on-camera in Vietnamese with confident tone. Background ambient sound: subtle environment noise. Visual: Cinematic shot featuring {identity_lock_rules} in the same setup ({safe_setting}). NO UI elements. Product maintains rigid structural integrity."
        }},
        {{
          "scene_number": 3, "duration": "8s", 
          "scene_setting": "[Giữ nguyên không gian, góc máy thuyết phục chốt sale]", 
          "transition_type": "Nối liền mạch (Match Cut)", 
          "voice_director_vn": "[Chỉ đạo giọng đọc: kích cầu, chuyên nghiệp]", 
          "dialogues": [ {{"speaker": "Nhân vật chính", "dialogue": "[Thoại chốt deal năng lượng cao, không nói giá số cụ thể]"}} ],
          "image_prompt": "Dùng ảnh cuối của cảnh trước làm ảnh tham chiếu", 
          "video_prompt": "Audio: Character speaking on-camera in Vietnamese with high conversion tone. Background ambient sound: upbeat subtle noise. Visual: Cinematic shot featuring {identity_lock_rules} and the physical product matching exact reference in the same consistent environment ({safe_setting}). NO UI elements."
        }}
      ]
    }}
    LƯU Ý: HÃY TẠO TỪ 3 ĐẾN 5 CẢNH (CÓ THỂ THÊM SCENE 4, 5 NẾU KỊCH BẢN DÀI). VIẾT NỘI DUNG THAY THẾ TOÀN BỘ NGOẶC VUÔNG [...].
    """
    sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins, char_rules_str, current_strategy, target_audience)
    res = call_gemini_with_retry([prompt_detail], sys_inst)
    if isinstance(res, list): res = res[0]
    st.session_state.generated_details[target_id] = res

def add_five_scripts_continuation(current_mode: str, current_style: str, aspect_ratio: str, goal: str, target_duration_mins: float, current_strategy: str):
    all_sources = (st.session_state.all_scripts or []) + (st.session_state.cloned_scripts or []) + (st.session_state.expanded_scripts or [])
    cur_len = len(all_sources)
    product_ctx = st.session_state.get("current_input_context", "").replace('"', "'")
    dna_data = st.session_state.get("content_analysis", {}) 
    char_rules_str = generate_char_rules_string(st.session_state.get("character_profiles", []), "Bán Hàng" in current_mode)
    
    prompt_more = f"""
    DỮ LIỆU SẢN PHẨM GỐC: {json.dumps(dna_data, ensure_ascii=False)} | Ghi chú: "{product_ctx}"
    Hãy tạo thêm ĐÚNG 5 kịch bản mới (id từ {cur_len + 1} đến {cur_len + 5}) theo CHIẾN LƯỢC: {current_strategy}.
    - Không dùng giá tiền con số.
    
    Xuất JSON chuẩn với key 'script_outlines' chứa 5 OBJECT (KHÔNG DÙNG DẤU BA CHẤM):
    {{
      "script_outlines": [
        {{"id": {cur_len + 1}, "title": "[Tên]", "setting_style": "[Bối cảnh cố định]", "script_outfit_setup": "[Đồng phục]", "angle": "[Góc tiếp cận]", "target_hook": "[Hook]", "recommended_scenes_count": "Linh hoạt 3-5 cảnh", "voice_profile": {{"gender": "Nam/Nữ", "tone": "Năng lượng"}}}},
        {{"id": {cur_len + 2}, "title": "[Tên]", "setting_style": "[Bối cảnh cố định]", "script_outfit_setup": "[Đồng phục]", "angle": "[Góc tiếp cận]", "target_hook": "[Hook]", "recommended_scenes_count": "Linh hoạt 3-5 cảnh", "voice_profile": {{"gender": "Nam/Nữ", "tone": "Năng lượng"}}}},
        {{"id": {cur_len + 3}, "title": "[Tên]", "setting_style": "[Bối cảnh cố định]", "script_outfit_setup": "[Đồng phục]", "angle": "[Góc tiếp cận]", "target_hook": "[Hook]", "recommended_scenes_count": "Linh hoạt 3-5 cảnh", "voice_profile": {{"gender": "Nam/Nữ", "tone": "Năng lượng"}}}},
        {{"id": {cur_len + 4}, "title": "[Tên]", "setting_style": "[Bối cảnh cố định]", "script_outfit_setup": "[Đồng phục]", "angle": "[Góc tiếp cận]", "target_hook": "[Hook]", "recommended_scenes_count": "Linh hoạt 3-5 cảnh", "voice_profile": {{"gender": "Nam/Nữ", "tone": "Năng lượng"}}}},
        {{"id": {cur_len + 5}, "title": "[Tên]", "setting_style": "[Bối cảnh cố định]", "script_outfit_setup": "[Đồng phục]", "angle": "[Góc tiếp cận]", "target_hook": "[Hook]", "recommended_scenes_count": "Linh hoạt 3-5 cảnh", "voice_profile": {{"gender": "Nam/Nữ", "tone": "Năng lượng"}}}}
      ]
    }}
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
    
    prompt = f"Dựa trên kịch bản gốc: {json.dumps(target_script, ensure_ascii=False)}. Tạo ĐÚNG 5 biến thể mới (id từ {cur_len+1} đến {cur_len+5}). Xuất JSON key 'cloned_outlines' chứa 5 OBJECT đầy đủ."
    sys_inst = get_system_instructions(current_mode, current_style, aspect_ratio, goal, target_duration_mins, char_rules_str, current_strategy, "")
    res_c = call_gemini_with_retry([prompt], sys_inst)
    cloned_list = res_c.get("cloned_outlines", [])
    for idx_c, cl in enumerate(cloned_list): cl["id"] = cur_len + idx_c + 1
    st.session_state.cloned_scripts.extend(cloned_list)

# ==============================================================================
# 7. THANH BÊN (SIDEBAR UI)
# ==============================================================================
with st.sidebar:
    if not st.session_state.is_logged_in:
        st.markdown("### 🔐 **Đăng Nhập Hệ Thống**")
        with st.form("login_form"):
            login_input = st.text_input("Nhập Email / SĐT:")
            if st.form_submit_button("🔑 Đăng Nhập", use_container_width=True): process_login(login_input)
    
    if st.session_state.is_logged_in:
        st.markdown("### 🗂️ **Quản Lý Dự Án**")
        if st.button("➕ Tạo Dự Án Mới", type="primary", use_container_width=True):
            st.session_state.content_analysis = None
            st.session_state.all_scripts, st.session_state.cloned_scripts, st.session_state.expanded_scripts = [], [], []
            st.session_state.generated_details, st.session_state.character_profiles = {}, []
            st.session_state.active_script_id = None
            st.session_state.scroll_to_top = True
            st.rerun()
        if st.button("🚪 Đăng Xuất", use_container_width=True):
            st.session_state.is_logged_in = False
            st.rerun()

# ==============================================================================
# 8. TIÊU ĐỀ & TÙY CHỈNH KỊCH BẢN CHÍNH
# ==============================================================================
st.markdown("""
<div class="header-container">
    <div class="main-title">🎬 Hệ Thống Kịch Bản Đa Vũ Trụ Pro</div>
    <div class="sub-title">Tối Ưu Chuyển Đổi, Đồng Nhất Tuyệt Đối Nhân Vật & Bối Cảnh AI</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.is_logged_in:
    st.info("👈 Vui lòng đăng nhập ở thanh công cụ bên trái để kích hoạt hệ thống.")
    st.stop()

col_mode, col_style = st.columns([1.5, 1])
with col_mode: selected_mode = st.selectbox("🎯 Chọn Thể Loại Nội Dung:", options=ALL_MODULES, key="selected_mode")

# Logic cập nhật chuẩn xác tên các nút Chiến lược
if "Bán Hàng" in selected_mode or "Mẹ & Bé" in selected_mode:
    strat_options = ["Review thực tế", "Tình huống", "Giảm giá/bán hàng"]
else:
    strat_options = ["Viral / Bắt trend giải trí", "Chia sẻ kiến thức", "Kể chuyện cảm xúc (Storytelling)"]

with col_style:
    selected_style_vn = st.selectbox("🎨 Phong Cách Hình Ảnh:", options=["Điện Ảnh Chân Thực (Cinematic Realism)", "Hoạt Hình 3D", "Studio Tối Giản"])
    selected_style = "Cinematic Realism"

col_strat, col_ratio, col_time = st.columns([1.5, 1, 1])
with col_strat: selected_strategy = st.selectbox("🧠 Chiến lược Kịch bản:", options=strat_options)
with col_ratio: selected_aspect = "9:16" if "9:16" in st.selectbox("Tỷ lệ khung hình:", ["9:16 (Dọc TikTok/Reels)", "16:9 (Ngang YouTube)"]) else "16:9"
with col_time: target_duration_mins = st.number_input("⏱️ Thời lượng (Phút):", min_value=0.5, max_value=30.0, value=1.0, step=0.5)
content_goal = "Sales & Conversion"

# ==============================================================================
# 9. ĐIỀU HƯỚNG TRIGGER (NÚT BẤM)
# ==============================================================================
if st.session_state.action_trigger:
    action, param = st.session_state.action_trigger, st.session_state.action_param
    st.session_state.action_trigger, st.session_state.action_param = None, None
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    if action == "create_detail":
        with st.container(border=True):
            st.markdown(f"<div class='loading-pulse'>⏳ HỆ THỐNG ĐANG DỰNG CHI TIẾT KỊCH BẢN #{param}...</div>", unsafe_allow_html=True)
            try:
                create_scene_details_for_id(int(param), selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, selected_strategy)
                st.session_state.active_script_id = int(param)
                st.session_state.scroll_to_top = True
                time.sleep(0.2); st.rerun()
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                if st.button("🔄 Quay lại"): st.rerun()
                
    elif action == "clone_script":
        with st.container(border=True):
            st.markdown(f"<div class='loading-pulse'>⏳ ĐANG NHÂN BẢN 5 BIẾN THỂ TỪ KỊCH BẢN #{param}...</div>", unsafe_allow_html=True)
            try:
                clone_script_id(int(param), selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, selected_strategy)
                st.session_state.scroll_to_top = True
                time.sleep(0.2); st.rerun()
            except Exception as e: st.error(f"❌ Lỗi: {e}")
                
    elif action == "generate_more":
        with st.container(border=True):
            st.markdown("<div class='loading-pulse'>⏳ ĐANG SÁNG TẠO THÊM 5 KỊCH BẢN MỚI...</div>", unsafe_allow_html=True)
            try:
                add_five_scripts_continuation(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, param or selected_strategy)
                st.session_state.scroll_to_top = True
                time.sleep(0.2); st.rerun()
            except Exception as e: st.error(f"❌ Lỗi: {e}")
    st.stop()

# ==============================================================================
# 10. KHU VỰC NHẬP LIỆU (TÓM TẮT & HÌNH ẢNH)
# ==============================================================================
input_text = st.text_area("✍️ Tóm tắt ý tưởng, chủ đề hoặc mô tả dự án/sản phẩm:", height=80, key="main_input_context")
col_p_img, col_c_img = st.columns([1, 1])
with col_p_img: uploaded_files = st.file_uploader("📦 Tải ảnh Sản phẩm (Làm gốc tham chiếu)", type=["jpg", "png"], accept_multiple_files=True)
with col_c_img: num_chars = st.number_input("👤 Số lượng Diễn viên tham chiếu", min_value=0, max_value=8, step=1)

char_inputs = []
if num_chars > 0:
    grid_cols = st.columns(min(num_chars, 4))
    for i in range(num_chars):
        with grid_cols[i % 4]:
            with st.container(border=True):
                c_role = st.text_input(f"Vai trò DV {i+1}", placeholder="VD: Nữ MC KOC")
                c_file = st.file_uploader(f"Ảnh DV {i+1}", type=["jpg", "png"], key=f"c_img_{i}")
                if c_file and c_role.strip(): char_inputs.append({"id": i+1, "role": c_role.strip(), "file": c_file})

if st.button("🚀 Phân Tích DNA & Lên Ý Tưởng", type="primary", use_container_width=True, disabled=not (input_text.strip() or uploaded_files)):
    with st.spinner("⏳ Đang phân tích chuyên sâu..."):
        try:
            st.session_state.character_profiles = [{"id": c["id"], "role": c["role"]} for c in char_inputs]
            st.session_state.current_input_context = input_text.strip()
            char_rules_str = generate_char_rules_string(st.session_state.character_profiles, "Bán Hàng" in selected_mode)
            
            prompt_text = f"""Phân tích chuyên sâu '{selected_mode}' - {selected_strategy}. Mô tả: "{st.session_state.current_input_context}". TUYỆT ĐỐI KHÔNG đưa giá tiền con số. Xuất JSON gồm `content_analysis` (chi tiết target audience, pain points, hooks...) và `script_outlines` (mảng 5 object)."""
            payload = []
            if uploaded_files:
                payload.append("ẢNH SẢN PHẨM:")
                for f in uploaded_files: payload.append(types.Part.from_bytes(data=f.getvalue(), mime_type=f.type or "image/jpeg"))
            if char_inputs:
                for c in char_inputs:
                    payload.append(f"ẢNH NHÂN VẬT {c['id']} ({c['role']}):")
                    payload.append(types.Part.from_bytes(data=c['file'].getvalue(), mime_type=c['file'].type or "image/jpeg"))
            payload.append(prompt_text)
            
            res = call_gemini_with_retry(payload, get_system_instructions(selected_mode, selected_style, selected_aspect, content_goal, target_duration_mins, char_rules_str, selected_strategy, "Người tiêu dùng"))
            st.session_state.content_analysis = res.get("content_analysis")
            st.session_state.all_scripts = res.get("script_outlines", [])
            st.session_state.cloned_scripts, st.session_state.expanded_scripts, st.session_state.generated_details, st.session_state.active_script_id = [], [], {}, None
            st.session_state.scroll_to_top = True; st.rerun()
        except Exception as e: st.error(f"❌ Lỗi: {e}")

# ==============================================================================
# 11. KHU VỰC HIỂN THỊ KẾT QUẢ ĐẦU RA
# ==============================================================================
if st.session_state.content_analysis and not st.session_state.action_trigger:
    st.divider()
    
    # BẢNG PHÂN TÍCH DNA (Đã khôi phục và tinh chỉnh UI)
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
                if c2.button("👁️ Xem chi tiết", key=f"btn_v1_{sc['id']}", use_container_width=True):
                    st.session_state.action_trigger, st.session_state.action_param = "view_detail", sc['id']; st.session_state.active_script_id = sc['id']; st.session_state.scroll_to_top = True; st.rerun()
                if c3.button("🚀 Nhân bản", key=f"btn_c1_{sc['id']}", use_container_width=True):
                    st.session_state.action_trigger, st.session_state.action_param = "clone_script", sc['id']; st.rerun()

        st.markdown("### ⏳ Ý Tưởng Đang Chờ (Chưa Dựng Chi Tiết)")
        for sc in pending_scripts:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**#{sc['id']}. {sc.get('title')}**")
                if c2.button("✨ Tạo chi tiết ngay", key=f"btn_p1_{sc['id']}", type="primary", use_container_width=True):
                    st.session_state.action_trigger, st.session_state.action_param = "create_detail", sc['id']; st.rerun()

        st.markdown("---")
        st.markdown("### ➕ Mở Rộng Thêm Kịch Bản Mới")
        if "Bán Hàng" in selected_mode or "Mẹ & Bé" in selected_mode:
            cb1, cb2, cb3 = st.columns(3)
            if cb1.button("➕ 5 Kịch bản Review", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Review thực tế"; st.rerun()
            if cb2.button("➕ 5 Kịch bản Tình huống", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Tình huống"; st.rerun()
            if cb3.button("➕ 5 Kịch bản Giảm giá", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Giảm giá/bán hàng"; st.rerun()
        else:
            if st.button("➕ Gọi Thêm 5 Kịch Bản Mới", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", selected_strategy; st.rerun()

    # GIAI ĐOẠN 2: CHI TIẾT KỊCH BẢN ĐÃ CHỌN
    if st.session_state.active_script_id and st.session_state.active_script_id in st.session_state.generated_details:
        if st.button("⬅️ Quay lại danh sách tổng", use_container_width=False):
            st.session_state.active_script_id = None; st.session_state.scroll_to_top = True; st.rerun()

        raw_data = st.session_state.generated_details[st.session_state.active_script_id]
        active_script = raw_data[0] if isinstance(raw_data, list) else raw_data
        st.markdown(f"### 🎬 KỊCH BẢN CHI TIẾT: {str(active_script.get('title')).upper()}")
        
        for idx, scene in enumerate(active_script.get("scenes", []), start=1):
            if not isinstance(scene, dict): continue
            st.markdown(f"#### 📍 Phân cảnh {idx} ({scene.get('duration', '6s')}) — [ {scene.get('transition_type', 'Cắt cảnh')} ]")
            st.markdown(f"🏛️ **Bối cảnh:** *{scene.get('scene_setting')}*")
            st.markdown(f"**🎙️ Yêu cầu Đạo diễn Voice:** *{scene.get('voice_director_vn')}*")
            
            dialogues = scene.get("dialogues", [])
            full_voice = ""
            if dialogues:
                st.markdown("**💬 Lời Thoại (Dùng để thu âm):**")
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
                if st.button("➕ Review", key="g2_rev", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Review thực tế"; st.rerun()
                if st.button("➕ Tình huống", key="g2_dra", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Tình huống"; st.rerun()
                if st.button("➕ Giảm giá", key="g2_sale", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", "Giảm giá/bán hàng"; st.rerun()
            else:
                if st.button("➕ Gọi Thêm 5 Kịch Bản", key="g2_def", use_container_width=True): st.session_state.action_trigger, st.session_state.action_param = "generate_more", selected_strategy; st.rerun()
        
        with col_right:
            st.markdown("### 📋 Kịch Bản Chưa Render Chi Tiết")
            for item in [sc for sc in all_combined_scripts_list if int(sc.get("id", 0)) not in st.session_state.generated_details]:
                if st.button(f"✨ Tạo #{item['id']}: {item['title'][:30]}...", key=f"nav_{item['id']}", use_container_width=True):
                    st.session_state.action_trigger, st.session_state.action_param = "create_detail", item['id']; st.rerun()
