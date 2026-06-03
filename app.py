import streamlit as st
from groq import Groq
from supabase import create_client
import json
import uuid
from datetime import datetime

# --- ページ設定 ---
st.set_page_config(page_title="こころのあいだ", page_icon="images/logo_side.png", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;500&display=swap');

    .main { background-color: #FAF7F2; }
    section[data-testid="stSidebar"] { background-color: #FAF7F2; }

    .stButton>button {
        border-radius: 20px;
        background-color: #FFFDF8;
        color: #6B5043;
        border: 1px solid #E8D8C4;
        font-weight: 400;
        padding: 6px 20px;
    }
    .stButton>button:hover {
        background-color: #F5EDE4;
        color: #4A2C1A;
        border: 1px solid #D9C4B0;
    }
    div[data-testid="stFormSubmitButton"] > button,
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #E8A87C;
        color: #4A2C1A;
        border: none;
        font-weight: 500;
    }
    .app-title {
        font-family: 'Noto Serif JP', Georgia, serif;
        font-size: 26px;
        font-weight: 500;
        color: #3D2B1F;
        margin-bottom: 2px;
    }
    .app-caption {
        font-size: 13px;
        color: #9C7B6A;
        margin-bottom: 0px;
    }
    .divider {
        border: none;
        border-top: 1px dashed #D9C4B0;
        margin: 16px 0;
    }
    .concept-card {
        background-color: #FFFDF8;
        border: 1.5px solid #E8D8C4;
        border-radius: 14px;
        padding: 18px 20px;
        margin: 12px 0 16px 0;
    }
    .concept-title {
        font-family: 'Noto Serif JP', Georgia, serif;
        font-size: 14px;
        font-weight: 500;
        color: #3D2B1F;
        margin-bottom: 10px;
    }
    .concept-body {
        font-size: 13px;
        color: #6B5043;
        line-height: 1.85;
        margin-bottom: 14px;
    }
    .step-row {
        display: flex;
        gap: 10px;
        align-items: flex-start;
        margin-bottom: 8px;
    }
    .step-num {
        min-width: 22px;
        height: 22px;
        background: #E8A87C;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        color: #4A2C1A;
        font-weight: 500;
    }
    .step-text {
        font-size: 13px;
        color: #6B5043;
        line-height: 1.6;
        padding-top: 2px;
    }
    .post-card {
        background-color: #FFFDF8;
        border: 1.5px solid #E8D8C4;
        border-left: 4px solid #E8A87C;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 14px;
    }
    .badge-position {
        display: inline-block;
        font-size: 11px;
        background: #FAF0E8;
        color: #B07050;
        padding: 3px 10px;
        border-radius: 20px;
        margin-left: 6px;
        vertical-align: middle;
    }
    .badge-anon {
        display: inline-block;
        font-size: 11px;
        background: #F0F0F0;
        color: #888;
        padding: 3px 10px;
        border-radius: 20px;
        margin-left: 6px;
        vertical-align: middle;
    }
    .tag-pill {
        display: inline-block;
        font-size: 11px;
        background: #FDE8D8;
        color: #993C1D;
        padding: 3px 10px;
        border-radius: 20px;
        margin-right: 4px;
        margin-bottom: 4px;
    }
    .section-header {
        font-family: 'Noto Serif JP', Georgia, serif;
        font-size: 18px;
        font-weight: 500;
        color: #3D2B1F;
        margin-bottom: 12px;
    }
    .chat-user {
        background-color: #F5EDE4;
        padding: 12px 16px;
        border-radius: 15px 15px 4px 15px;
        margin: 8px 0;
        text-align: right;
        color: #4A2C1A;
        font-size: 14px;
    }
    .chat-ai {
        background-color: #FFFDF8;
        padding: 12px 16px;
        border-radius: 15px 15px 15px 4px;
        margin: 8px 0;
        border-left: 3px solid #E8A87C;
        color: #4A2C1A;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- テーマアイコン ---
THEME_ICONS = {"親子関係": "●", "子育て": "●", "受験・進路": "●"}

# --- Supabase設定 ---
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- 端末ID生成（LocalStorageで永続化） ---
if "device_id" not in st.session_state:
    st.session_state.device_id = str(uuid.uuid4())

import streamlit.components.v1 as components

if "device_id_loaded" not in st.session_state:
    stored_id = st.query_params.get("did", None)
    if stored_id:
        st.session_state.device_id = stored_id
        st.session_state.device_id_loaded = True
    else:
        st.session_state.device_id_loaded = False

components.html(f"""
<script>
(function() {{
    let id = localStorage.getItem('kokoro_device_id');
    if (!id) {{
        id = '{st.session_state.device_id}';
        localStorage.setItem('kokoro_device_id', id);
    }}
    const current = new URLSearchParams(window.parent.location.search).get('did');
    if (current !== id) {{
        const url = new URL(window.parent.location.href);
        url.searchParams.set('did', id);
        window.parent.history.replaceState(null, '', url.toString());
        window.parent.location.reload();
    }}
}})();
</script>
""", height=0)

# --- 投稿の読み込み ---
def load_posts():
    try:
        supabase = get_supabase()
        res = supabase.table("posts").select("*").order("created_at", desc=True).execute()
        posts = []
        for p in res.data:
            posts.append({
                "id": p["id"],
                "title": p["title"] or "名もなき感情",
                "author": p["author"] or "",
                "isAnonymous": p["is_anonymous"],
                "position": p["position"],
                "theme": p["theme"],
                "whatHappened": p["what_happened"],
                "howFelt": p["how_felt"],
                "reallyWanted": p["really_wanted"] or "",
                "hardestMoment": p["hardest_moment"] or "",
                "tags": p["tags"] or [],
                "createdAt": str(p["created_at"]),
                "device_id": p["device_id"]
            })
        return posts
    except Exception as e:
        st.error(f"データの読み込みに失敗しました: {e}")
        return []

# --- 投稿の保存 ---
def save_post(post):
    try:
        supabase = get_supabase()
        supabase.table("posts").insert({
            "id": post["id"],
            "device_id": post["device_id"],
            "title": post["title"],
            "author": post["author"],
            "is_anonymous": post["isAnonymous"],
            "position": post["position"],
            "theme": post["theme"],
            "what_happened": post["whatHappened"],
            "how_felt": post["howFelt"],
            "really_wanted": post["reallyWanted"],
            "hardest_moment": post["hardestMoment"],
            "tags": post["tags"],
            "created_at": post["createdAt"]
        }).execute()
        return True
    except Exception as e:
        st.error(f"保存に失敗しました: {e}")
        return False

# --- 投稿の更新 ---
def update_post(post):
    try:
        supabase = get_supabase()
        supabase.table("posts").update({
            "title": post["title"],
            "author": post["author"],
            "is_anonymous": post["isAnonymous"],
            "position": post["position"],
            "theme": post["theme"],
            "what_happened": post["whatHappened"],
            "how_felt": post["howFelt"],
            "really_wanted": post["reallyWanted"],
            "hardest_moment": post["hardestMoment"],
        }).eq("id", post["id"]).execute()
        return True
    except Exception as e:
        st.error(f"更新に失敗しました: {e}")
        return False

# --- 投稿の削除 ---
def delete_post(post_id):
    try:
        supabase = get_supabase()
        supabase.table("posts").delete().eq("id", post_id).execute()
        return True
    except Exception as e:
        st.error(f"削除に失敗しました: {e}")
        return False

# --- 関数: 投稿報告 ---
def report_post(post_id, reason):
    try:
        supabase = get_supabase()
        supabase.table("reports").insert({
            "post_id": post_id,
            "reason": reason
        }).execute()
        return True
    except Exception as e:
        st.error(f"報告に失敗しました: {e}")
        return False

# --- 関数: 報告一覧取得 ---
def load_reports():
    try:
        supabase = get_supabase()
        res = supabase.table("reports").select("*, posts(title, position, theme, what_happened, how_felt, really_wanted, hardest_moment)").order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        return []

# --- 関数: AI分析 ---
def analyze_post(post):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    position = post['position']
    other = "子ども" if position == "親" else "親"
    prompt = f"""
    以下の親子関係の悩みを分析し、日本語のJSON形式のみで出力してください。
    前置きや説明文は一切不要です。JSONだけを返してください。

    投稿者の立場: {position}
    テーマ: {post['theme']}
    内容: {post['whatHappened']}
    感情: {post['howFelt']}
    本当はどうしてほしかったか: {post.get('reallyWanted', '未回答')}
    一番つらかった瞬間: {post.get('hardestMoment', '未回答')}

    【重要な指針】
    このアプリの目的は「{position}」の気持ちをまず受け止め、整理してあげることです。
    以下の順番で分析してください：
    1. まず投稿者（{position}）の気持ちを温かく受け止める
    2. 相手（{other}）の立場・気持ちを想像させる
    3. 具体的な次の一歩を提案する

    アドバイスはすべて投稿者（{position}）本人に向けて書いてください。

    以下のキーを持つJSONを返してください（日本語で回答）。

    {{
      "your_feelings": "投稿者（{position}）の気持ちをそのまま温かく受け止める言葉。「あなたは〜と感じていたんですね」「それは辛かったですね」のように共感を示す。2〜3文",
      "hidden_feelings": "投稿者（{position}）の表面の感情の奥にある本当の気持ち。「本当は〜してほしかったのではないでしょうか」のような形で具体的に",
      "other_perspective": "相手（{other}）はなぜそう言ったのか・そう行動したのかを、相手の立場から想像して説明する。相手を責めるのではなく、背景にある気持ちを伝える",
      "how_to_talk": "投稿者（{position}）が相手（{other}）に話しかけるときの具体的な言葉や文例。そのまま使えるような自然な表現で",
      "actionable_hints": ["投稿者（{position}）が今すぐできる具体的な行動1", "投稿者（{position}）が今すぐできる具体的な行動2", "投稿者（{position}）が今すぐできる具体的な行動3"]
    }}
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "あなたは親子関係の悩みに寄り添うカウンセラーです。必ずJSON形式のみで回答してください。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

# --- 関数: AIチャット ---
def chat_with_ai(post, analysis, chat_history, user_message):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    system_prompt = f"""
あなたは親子関係の悩みに深く寄り添う、温かいカウンセラーです。
1. 【具体的なアドバイス】実際に使える言葉や行動を提案する
2. 【次のアクションを一緒に考える】「次に何ができそうか」を一緒に考える
3. 【相手の気持ちを代弁する】親/子どもの立場から気持ちを言語化する

立場: {post['position']} / テーマ: {post['theme']}
何があったか: {post['whatHappened']}
どう感じたか: {post['howFelt']}
本当はどうしてほしかったか: {post.get('reallyWanted', '')}
一番つらかった瞬間: {post.get('hardestMoment', '')}

分析結果:
- 整理: {analysis.get('overview', '')}
- 隠れた気持ち: {analysis.get('hidden_feelings', '')}

返答は200〜300文字程度の自然な日本語で、温かいトーンで。
"""
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

# --- カードHTML生成 ---
def render_post_card(post):
    tags_html = ''.join([f'<span class="tag-pill">#{t}</span>' for t in post.get('tags', [])])
    anon_badge = '<span class="badge-anon">匿名</span>' if post.get('isAnonymous') else ''
    author_text = f'<span style="font-size:12px;color:#9C7B6A;margin-left:4px;">{post.get("author","")}</span>' if post.get("author") and not post.get("isAnonymous") else ''
    preview = post['whatHappened'][:45] + '...' if len(post['whatHappened']) > 45 else post['whatHappened']

    if post["position"] == "親":
        card_bg = "#FDF0EB"
        card_border = "#E8A882"
        card_left = "#C4622A"
        badge_bg = "#F5C8B0"
        badge_color = "#7A3010"
    else:
        card_bg = "#FFFDF8"
        card_border = "#F0D0A0"
        card_left = "#E8A840"
        badge_bg = "#FDE8C0"
        badge_color = "#8A5800"

    position_badge = f'<span style="background:{badge_bg};color:{badge_color};font-size:11px;padding:3px 12px;border-radius:20px;font-weight:500;white-space:nowrap;">{post["position"]}</span>'

    import html as html_lib
    safe_title = html_lib.escape(post['title'])
    safe_preview = html_lib.escape(preview)
    is_en = st.session_state.get("lang") == "en"
    if is_en:
        safe_title = translate_to_english(post['title'])
        safe_preview = translate_to_english(preview)
        position_label = "Parent" if post["position"] == "親" else "Child"
        position_badge = f'<span style="background:{badge_bg};color:{badge_color};font-size:11px;padding:3px 12px;border-radius:20px;font-weight:500;white-space:nowrap;">{position_label}</span>'
    else:
        safe_preview_text = safe_preview

    tags_section = f'<div style="margin-bottom:10px;">{tags_html}</div>' if tags_html else ''
    display_title = safe_title if is_en else safe_title
    display_preview = safe_preview if is_en else safe_preview
    return f"""
    <div style="background:{card_bg};border:1.5px solid {card_border};border-left:4px solid {card_left};border-radius:14px;padding:18px;margin-bottom:14px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
            <div style="font-family:'Noto Serif JP',Georgia,serif;font-size:15px;font-weight:500;color:#3D2B1F;">{display_title}{anon_badge}{author_text}</div>
            {position_badge}
        </div>
        <div style="font-size:12px;color:#B07050;margin-bottom:8px;">{post['theme']} &nbsp;·&nbsp; {post['createdAt']}</div>
        <div style="font-size:13px;color:#6B5043;line-height:1.7;margin-bottom:10px;">{display_preview}</div>
        {tags_section}
    </div>
    """

# --- パスワード認証 ---
def check_password():
    if st.session_state.get("authenticated"):
        return True

    st.markdown("""
    <div style="max-width:380px; margin:80px auto 0 auto;">
        <div style="text-align:center; margin-bottom:32px;">
    """, unsafe_allow_html=True)

    try:
        st.image("images/logo.png", width=90)
    except:
        pass

    st.markdown("""
        <div style="font-family:Georgia,serif;font-size:24px;font-weight:500;color:#3D2B1F;margin-top:12px;">こころのあいだ</div>
        <div style="font-size:13px;color:#9C7B6A;margin-top:4px;margin-bottom:32px;">こころのあいだを、ことばにする。</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        password = st.text_input("パスワード", type="password", placeholder="パスワードを入力してください")
        submitted = st.form_submit_button("ログイン", use_container_width=True)
        if submitted:
            if password == st.secrets.get("APP_PASSWORD", ""):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("パスワードが違います")
    return False

if not check_password():
    st.stop()

# --- 翻訳関数 ---
def translate_to_english(text):
    if not text:
        return text
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a translator. Translate the following Japanese text to natural English. Return only the translated text, nothing else."},
                {"role": "user", "content": text}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except:
        return text

def t(text):
    """テキストを現在の言語に応じて返す"""
    if st.session_state.get("lang") == "en":
        return translate_to_english(text)
    return text

# --- サイドバーメニュー ---
with st.sidebar:
    try:
        st.image("images/logo_side.png", width=60)
    except:
        pass
    st.markdown('<div style="font-family:Georgia,serif;font-size:16px;font-weight:500;color:#3D2B1F;margin-bottom:4px;">こころのあいだ</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#9C7B6A;margin-bottom:16px;">こころのあいだを、ことばにする。</div>', unsafe_allow_html=True)
    st.markdown('<hr style="border:none;border-top:1px dashed #D9C4B0;margin:8px 0 16px 0;">', unsafe_allow_html=True)

    # 言語切り替え
    if "lang" not in st.session_state:
        st.session_state.lang = "ja"
    col_ja, col_en = st.columns(2)
    with col_ja:
        if st.button("日本語", use_container_width=True, key="lang_ja",
                     type="primary" if st.session_state.lang == "ja" else "secondary"):
            st.session_state.lang = "ja"
            st.rerun()
    with col_en:
        if st.button("English", use_container_width=True, key="lang_en",
                     type="primary" if st.session_state.lang == "en" else "secondary"):
            st.session_state.lang = "en"
            st.rerun()

    st.markdown('<hr style="border:none;border-top:1px dashed #D9C4B0;margin:12px 0;">', unsafe_allow_html=True)

    is_en = st.session_state.get("lang") == "en"
    menu_items = [
        ("Home" if is_en else "ホーム", "home"),
        ("About" if is_en else "はじめに", "about"),
        ("How to Use" if is_en else "使い方ガイド", "guide"),
        ("Privacy" if is_en else "プライバシーについて", "privacy"),
        ("FAQ" if is_en else "よくある質問", "faq"),
    ]
    for label, view_name in menu_items:
        if st.button(label, key=f"menu_{view_name}", use_container_width=True):
            st.session_state.view = view_name
            st.rerun()

    st.markdown('<hr style="border:none;border-top:1px dashed #D9C4B0;margin:16px 0 12px 0;">', unsafe_allow_html=True)

    if st.session_state.get("is_admin"):
        st.markdown('<div style="font-size:12px;color:#E8A87C;text-align:center;margin-bottom:8px;">管理者モード中</div>', unsafe_allow_html=True)
        if st.button("報告一覧を見る", use_container_width=True, key="admin_reports_btn"):
            st.session_state.view = "admin_reports"
            st.rerun()
        if st.button("管理者ログアウト", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()
    else:
        with st.expander("管理者ログイン"):
            admin_code = st.text_input("管理者コード", type="password", key="admin_code_input")
            if st.button("ログイン", key="admin_login", use_container_width=True):
                if admin_code == st.secrets.get("ADMIN_PASSWORD", ""):
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("コードが違います")

# --- 画面遷移制御 ---
if "view" not in st.session_state:
    st.session_state.view = "home"

# =============================
# 画面: はじめに
# =============================
if st.session_state.view == "about":
    is_en = st.session_state.get("lang") == "en"
    if is_en:
        st.markdown('<div class="section-header">About This App</div>', unsafe_allow_html=True)
        st.markdown("""
    <div class="concept-card" style="border-left:4px solid #E8A87C;">
        <div class="concept-title">What This App Is For</div>
        <div class="concept-body">
            This app is a place to share <strong style="color:#3D2B1F;">concerns that both parents and children can understand from each other's perspective</strong>.<br><br>
            For example: "I can't talk to my child about their future" or "My parents don't understand how I feel" — please share <strong style="color:#3D2B1F;">misunderstandings and communication struggles between parent and child</strong>.<br><br>
            Topics like financial issues or work stress that children may not relate to are not suited for this app.<br>
            Try to share <strong style="color:#3D2B1F;">concerns that both sides can imagine from their own perspective</strong>.
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">Why This App Was Created</div>
        <div class="concept-body">
            The parent-child relationship may be the closest — and the most difficult — relationship in the world.<br><br>
            You love them, but your feelings don't get through.<br>
            You want to be understood, but you're not.<br>
            In these moments of disconnect, unspoken feelings keep building up——<br><br>
            "Kokoro no Aida" is a place to <strong style="color:#3D2B1F;">put those unspoken feelings into words</strong>.
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">Who Is This App For?</div>
        <div class="concept-body">
            · Parents who struggle to express their feelings to their children<br>
            · Children who feel misunderstood by their parents<br>
            · Anyone who wants to improve their family relationships<br><br>
            It doesn't matter which side you're on. Both parents and children can use this app from their own perspective.
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">How to Use AI</div>
        <div class="concept-body">
            The AI in this app is not here to give you answers.<br><br>
            It receives your words, helps explore hidden feelings, and imagines the other person's perspective——<br>
            Use it as a "mirror" for that purpose.<br><br>
            AI is not a counselor. But it can help you sort through feelings you've been holding alone.
        </div>
    </div>
    <div class="concept-card" style="border-left:4px solid #C4A882;">
        <div class="concept-title">Reading Others' Posts</div>
        <div class="concept-body">
            Other people's posts are shown on the home page too.<br>
            There's a reason for that.<br><br>
            <strong style="color:#3D2B1F;">Realizing you're not alone</strong><br>
            Just knowing others share similar struggles can lighten your heart a little.<br><br>
            <strong style="color:#3D2B1F;">Practice seeing the other side</strong><br>
            A child reading a parent's post, a parent reading a child's——<br>
            Encountering feelings from a different perspective deepens understanding.<br><br>
            <strong style="color:#3D2B1F;">Finding the courage to write</strong><br>
            Seeing others write honestly may inspire you to do the same.<br><br>
            If you're concerned about privacy, please use Anonymous mode.
        </div>
    </div>
    """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="section-header">はじめに・このアプリについて</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="concept-card" style="border-left:4px solid #E8A87C;">
        <div class="concept-title">このアプリで書いてほしいこと</div>
        <div class="concept-body">
            このアプリは、<strong style="color:#3D2B1F;">親と子ども、お互いの目線から見られる悩み</strong>を書く場所です。<br><br>
            たとえば「子どもと進路について話し合えない」「親に気持ちをわかってもらえない」など、<strong style="color:#3D2B1F;">親子のすれ違いやコミュニケーションの悩み</strong>を共有してください。<br><br>
            お金の問題・仕事の悩みなど、子どもの視点からは理解しにくい内容はこのアプリには向いていません。<br>
            「親ならどう感じるか」「子どもならどう思うか」——<strong style="color:#3D2B1F;">お互いの立場から想像できる悩み</strong>を書いてみてください。
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">このアプリが生まれた理由</div>
        <div class="concept-body">
            親子の関係は、世界でいちばん近くて、いちばん難しい関係かもしれません。<br><br>
            愛しているのに、うまく伝わらない。<br>
            わかってほしいのに、わかってもらえない。<br>
            そんなすれ違いの中で、ことばにできない気持ちが積もっていく——<br><br>
            「こころのあいだ」は、そんな<strong style="color:#3D2B1F;">こころのあいだにあるものを、ことばにするための場所</strong>です。
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">誰のためのアプリ？</div>
        <div class="concept-body">
            ・子どもに気持ちをうまく伝えられない親<br>
            ・親にわかってもらえないと感じている子ども<br>
            ・家族との関係を少しでもよくしたいと思っている人<br><br>
            立場は関係ありません。親でも、子どもでも、どちらの視点からも使えます。
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">AIとどう向き合うか</div>
        <div class="concept-body">
            このアプリのAIは、答えを出すためのものではありません。<br><br>
            あなたの言葉を受け取り、隠れた気持ちを一緒に探し、相手の視点を想像する——<br>
            そのための「鏡」として使ってください。<br><br>
            AIはカウンセラーではありません。でも、ひとりで抱えていた気持ちを整理する手助けはできます。
        </div>
    </div>
    <div class="concept-card" style="border-left:4px solid #C4A882;">
        <div class="concept-title">他の人の投稿を読むということ</div>
        <div class="concept-body">
            このアプリでは、他の人の投稿もトップページに表示されます。<br>
            それには理由があります。<br><br>
            <strong style="color:#3D2B1F;">「自分だけじゃない」と気づける</strong><br>
            似たような悩みを抱えている人がいると知るだけで、こころが少し軽くなることがあります。<br><br>
            <strong style="color:#3D2B1F;">相手の立場を想像する練習になる</strong><br>
            親の投稿を読む子ども、子どもの投稿を読む親——<br>
            自分とは違う立場の気持ちに触れることで、相手への理解が深まります。<br><br>
            <strong style="color:#3D2B1F;">言葉にする勇気をもらえる</strong><br>
            他の人が正直に書いた言葉を見て、「自分も書いてみよう」と思えることがあります。<br><br>
            プライバシーが気になる方は、匿名モードでの投稿をご利用ください。
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================
# 画面: 使い方ガイド
# =============================
elif st.session_state.view == "guide":
    is_en = st.session_state.get("lang") == "en"
    if is_en:
        st.markdown('<div class="section-header">How to Use</div>', unsafe_allow_html=True)
        st.markdown("""
    <div class="concept-card">
        <div class="concept-title">Basic Steps (3 Steps)</div>
        <div class="step-row"><div class="step-num">1</div><div class="step-text"><strong style="color:#3D2B1F;">Write Your Heart</strong><br>Write what happened (facts) and how you felt (emotions). It's okay if it's not perfect — just write what comes to mind.</div></div>
        <div class="step-row"><div class="step-num">2</div><div class="step-text"><strong style="color:#3D2B1F;">Reflect with AI</strong><br>AI will analyze your post and return hidden feelings, perspectives from both sides, and hints to improve the relationship.</div></div>
        <div class="step-row"><div class="step-num">3</div><div class="step-text"><strong style="color:#3D2B1F;">Chat with AI</strong><br>Based on the analysis, you can freely talk with AI. Ask anything you're curious about.</div></div>
    </div>
    <div class="concept-card" style="border-left:4px solid #E8A87C;">
        <div class="concept-title">The Importance of Journaling</div>
        <div class="concept-body">
            Worries that stay only in your head tend to grow bigger and bigger.<br>
            When you're feeling emotional or can't shake a feeling of unease——<br>
            that's exactly when putting it into words matters most.<br><br>
            Writing allows you to see your feelings from a slight distance.<br>
            The realization "Ah, so that's how I was feeling" leads to clarity in your heart.<br><br>
            It doesn't have to be perfect. It doesn't have to be the right words.<br>
            Just try starting by writing something down.
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">Tips for Writing</div>
        <div class="concept-body">
            <strong style="color:#3D2B1F;">Separate facts from feelings</strong><br>
            Writing "what happened" and "how I felt" separately is the key.<br><br>
            <strong style="color:#3D2B1F;">Ask yourself: what did I really want?</strong><br>
            Answering this helps reveal your true needs.<br><br>
            <strong style="color:#3D2B1F;">Pinpoint the hardest moment</strong><br>
            Writing specifically about "that one word" or "that one moment" deepens the AI analysis.
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">How to Use AI Chat</div>
        <div class="concept-body">
            After the AI analysis, you can talk freely with AI.<br><br>
            <strong style="color:#3D2B1F;">Ask about the other person's feelings</strong>: "What do you think my parent was feeling when they said that?"<br>
            <strong style="color:#3D2B1F;">Ask how to communicate</strong>: "How should I approach this conversation?"<br>
            <strong style="color:#3D2B1F;">Think about next steps</strong>: "What do you think I should do first?"<br><br>
            AI won't judge you. It simply stays by your side and thinks things through together.
        </div>
    </div>
    """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="section-header">使い方ガイド</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="concept-card">
        <div class="concept-title">基本の使い方（3ステップ）</div>
        <div class="step-row"><div class="step-num">1</div><div class="step-text"><strong style="color:#3D2B1F;">こころを書き出す</strong><br>何があったか（事実）と、どう感じたか（感情）を書きます。うまく書けなくても大丈夫。思いつくままに。</div></div>
        <div class="step-row"><div class="step-num">2</div><div class="step-text"><strong style="color:#3D2B1F;">AIと見つめ直す</strong><br>AIがあなたの投稿を分析します。隠れた気持ち、親の視点・子の視点、関係をよくするヒントが返ってきます。</div></div>
        <div class="step-row"><div class="step-num">3</div><div class="step-text"><strong style="color:#3D2B1F;">AIとチャットする</strong><br>分析結果をもとに、AIと自由に対話できます。気になることを何でも聞いてみましょう。</div></div>
    </div>
    <div class="concept-card" style="border-left:4px solid #E8A87C;">
        <div class="concept-title">ジャーナリングの大切さ</div>
        <div class="concept-body">
            頭の中だけにある悩みは、どんどん大きくなりがちです。<br>
            感情的になっているとき、モヤモヤが晴れないとき——<br>
            そんなときこそ、ことばにして外に出すことが大切です。<br><br>
            書くことで、自分の気持ちを少し離れたところから見られるようになります。<br>
            「あ、自分はこう感じていたんだ」という気づきが、こころの整理につながります。<br><br>
            完璧な文章でなくていいです。正しい言葉でなくていいです。<br>
            ただ、書いてみることから始めてみてください。
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">投稿のコツ・書き方のポイント</div>
        <div class="concept-body">
            <strong style="color:#3D2B1F;">事実と感情を分けて書く</strong><br>
            「何があったか」と「どう感じたか」は別々に書くのがポイントです。<br><br>
            <strong style="color:#3D2B1F;">「本当はどうしてほしかった？」を意識する</strong><br>
            この問いに答えることで、自分の本当のニーズが見えてきます。<br><br>
            <strong style="color:#3D2B1F;">一番つらかった瞬間を特定する</strong><br>
            漠然とした辛さより、「あの一言」「あの瞬間」を具体的に書くと、AIの分析がより深くなります。
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">AIチャットの活用法</div>
        <div class="concept-body">
            AI分析が終わった後、チャットで自由に話しかけられます。<br><br>
            <strong style="color:#3D2B1F;">相手の気持ちを聞く</strong>：「親はどんな気持ちで言ったんだと思う？」<br>
            <strong style="color:#3D2B1F;">伝え方を相談する</strong>：「どう話しかければうまく伝わる？」<br>
            <strong style="color:#3D2B1F;">次の一歩を考える</strong>：「まず何をすればいいと思う？」<br><br>
            AIは批判しません。ただ、あなたの気持ちに寄り添って一緒に考えます。
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================
# 画面: プライバシー
# =============================
elif st.session_state.view == "privacy":
    is_en = st.session_state.get("lang") == "en"
    if is_en:
        st.markdown('<div class="section-header">Privacy</div>', unsafe_allow_html=True)
        st.markdown("""
    <div class="concept-card">
        <div class="concept-title">Information We Collect</div>
        <div class="concept-body">
            This app only saves the post content you enter.<br><br>
            · Post title, body, and emotions<br>
            · Your chosen position and theme<br>
            · Your name (only if you choose to enter it)<br>
            · An anonymous ID to identify your device<br><br>
            <strong style="color:#3D2B1F;">We do not collect any personal information such as email addresses, phone numbers, or full names.</strong>
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">Where Data Is Stored</div>
        <div class="concept-body">
            Post data is stored in Supabase (a US-based cloud service).<br>
            Data is encrypted and will never be shared with third parties.
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">Data Sent to AI</div>
        <div class="concept-body">
            When you use the "Reflect with AI" feature, your post content is sent to Groq's AI.<br>
            This only happens when you press the button.<br>
            Your content will not be used as AI training data.
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">Deleting Posts</div>
        <div class="concept-body">
            You can delete your posts at any time. Deleted posts are permanently removed and cannot be recovered.
        </div>
    </div>
    """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="section-header">プライバシーについて</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="concept-card">
        <div class="concept-title">取得する情報</div>
        <div class="concept-body">
            このアプリが保存するのは、あなたが入力した投稿内容のみです。<br><br>
            ・投稿のタイトル・本文・感情<br>
            ・あなたが選んだ立場・テーマ<br>
            ・任意で入力したお名前（入力した場合のみ）<br>
            ・端末を識別するための匿名ID<br><br>
            <strong style="color:#3D2B1F;">メールアドレス・電話番号・氏名などの個人情報は一切取得しません。</strong>
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">データの保存先</div>
        <div class="concept-body">
            投稿データはSupabase（アメリカのクラウドサービス）に保存されます。<br>
            データは暗号化されて保存され、第三者に共有されることはありません。
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">AIへのデータ送信</div>
        <div class="concept-body">
            「AIと見つめ直す」機能を使うと、投稿内容がGroq社のAIに送信されます。<br>
            AIへの送信はあなたがボタンを押したときのみ行われます。<br>
            AIによって学習データとして使用されることはありません。
        </div>
    </div>
    <div class="concept-card">
        <div class="concept-title">投稿の削除</div>
        <div class="concept-body">
            投稿はいつでも削除できます。削除した投稿は完全に消去され、復元できません。
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================
# 画面: FAQ
# =============================
elif st.session_state.view == "faq":
    is_en = st.session_state.get("lang") == "en"
    if is_en:
        st.markdown('<div class="section-header">FAQ</div>', unsafe_allow_html=True)
        faqs_en = [
            ("Can others see my posts?", "Currently, all posts are shown on the home page. Using Anonymous mode hides your name. We recommend posting anonymously if you're concerned about privacy."),
            ("Will my posts disappear if I close the browser?", "Posts are saved to a database, so they won't disappear when you close the browser. However, 'My Page' is managed by device ID, so it may not show on a different browser or device."),
            ("Is AI a real counselor?", "AI is not a counselor. It's a tool to help you organize your feelings. For serious concerns, we recommend consulting a professional."),
            ("Can I edit or delete posts?", "Yes. Use the 'Edit' or 'Delete' buttons on the post card. Deleted posts cannot be recovered."),
            ("What is Anonymous mode?", "Checking 'Post anonymously' when creating a post will show 'Anonymous' instead of your name."),
            ("Is it free to use?", "Yes, it's completely free."),
        ]
        for q, a in faqs_en:
            st.markdown(f"""
            <div class="concept-card" style="margin-bottom:10px;">
                <div style="font-size:14px;font-weight:500;color:#3D2B1F;margin-bottom:8px;">Q. {q}</div>
                <div style="font-size:13px;color:#6B5043;line-height:1.7;">A. {a}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="section-header">よくある質問</div>', unsafe_allow_html=True)
        faqs = [
        ("投稿は他の人に見られますか？", "現在このアプリはトップページにすべての投稿が表示される仕様です。匿名モードを使うと名前は表示されません。気になる方は匿名での投稿をおすすめします。"),
        ("ブラウザを閉じたら投稿は消えますか？", "投稿はデータベースに保存されるため、ブラウザを閉じても消えません。ただし「マイページ」は端末IDで管理しているため、別のブラウザや端末では表示されないことがあります。"),
        ("AIは本物のカウンセラーですか？", "AIはカウンセラーではありません。気持ちの整理を手助けするツールです。深刻な悩みについては、専門家への相談をおすすめします。"),
        ("投稿を編集・削除できますか？", "はい、できます。投稿カードの「編集」「削除」ボタンから操作できます。削除した投稿は元に戻せません。"),
        ("匿名モードとは何ですか？", "投稿時に「匿名にする」にチェックを入れると、投稿者名が「匿名」と表示されます。"),
        ("無料で使えますか？", "はい、完全無料で使えます。"),
    ]
    for q, a in faqs:
        st.markdown(f"""
        <div class="concept-card" style="margin-bottom:10px;">
            <div style="font-size:14px;font-weight:500;color:#3D2B1F;margin-bottom:8px;">Q. {q}</div>
            <div style="font-size:13px;color:#6B5043;line-height:1.7;">A. {a}</div>
        </div>
        """, unsafe_allow_html=True)

# =============================
# 画面: ホーム
# =============================
elif st.session_state.view == "home":
    is_en = st.session_state.get("lang") == "en"
    try:
        col_logo, col_title = st.columns([1, 4])
        with col_logo:
            st.markdown("""<style>[data-testid="stImage"] img { background-color: #FAF7F2 !important; border-radius: 12px; }</style>""", unsafe_allow_html=True)
            st.image("images/logo.png", width=100)
        with col_title:
            title_text = "Kokoro no Aida" if is_en else "こころのあいだ"
            caption_text = "Putting words to what lies between hearts." if is_en else "こころのあいだを、ことばにする。"
            st.markdown(f"""<div style="display:flex; flex-direction:column; justify-content:flex-end; height:100%; padding-left:4px; margin-top:38px;"><div class="app-title">{title_text}</div><div class="app-caption">{caption_text}</div></div>""", unsafe_allow_html=True)
    except:
        st.markdown('<div class="app-title">こころのあいだ</div>', unsafe_allow_html=True)
        st.markdown('<div class="app-caption">こころのあいだを、ことばにする。</div>', unsafe_allow_html=True)

    st.markdown("""
    <style>
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #E8A87C !important;
        color: #4A2C1A !important;
        border: none !important;
        font-weight: 500 !important;
        min-height: 46px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col_nav1, col_nav2 = st.columns([1, 1])
    with col_nav1:
        btn_write = "Write Your Heart" if is_en else "こころを書き出す"
        if st.button(btn_write, use_container_width=True, key="nav_create", type="primary"):
            st.session_state.view = "create"
            st.rerun()
    with col_nav2:
        btn_my = "My Page" if is_en else "マイページ"
        if st.button(btn_my, use_container_width=True, key="nav_mypage", type="primary"):
            st.session_state.view = "mypage"
            st.rerun()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # --- テーマフィルター（複数選択・折りたたみ） ---
    all_themes = ["親子関係", "子育て", "受験・進路", "学校生活", "友達関係", "習い事・スポーツ", "スマホ・ゲーム", "兄弟・姉妹関係", "将来の夢"]
    if "selected_themes" not in st.session_state:
        st.session_state.selected_themes = []

    selected = st.session_state.selected_themes
    label = "カテゴリで絞り込む" if not selected else f"絞り込み中: {' / '.join(selected)}"

    with st.expander(label):
        st.caption("複数選択できます。もう一度押すと解除されます。")
        cols = st.columns(3)
        for i, theme in enumerate(all_themes):
            with cols[i % 3]:
                is_sel = theme in selected
                btn_label = f"✓ {theme}" if is_sel else theme
                if st.button(btn_label, key=f"filter_{theme}", use_container_width=True):
                    if is_sel:
                        st.session_state.selected_themes.remove(theme)
                    else:
                        st.session_state.selected_themes.append(theme)
                    st.rerun()
        if selected:
            if st.button("すべてクリア", use_container_width=True, key="filter_clear"):
                st.session_state.selected_themes = []
                st.rerun()

    if selected:
        st.markdown(
            '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">' +
            ''.join([f'<span style="background:#E8A87C;color:#4A2C1A;font-size:11px;padding:3px 10px;border-radius:20px;font-weight:500;">{t}</span>' for t in selected]) +
            '</div>',
            unsafe_allow_html=True
        )

    posts = load_posts()
    if st.session_state.selected_themes:
        posts = [p for p in posts if p['theme'] in st.session_state.selected_themes]
    for post in posts:
        st.markdown(render_post_card(post), unsafe_allow_html=True)
        is_mine = post.get("device_id") == st.session_state.device_id
        is_admin = st.session_state.get("is_admin", False)
        if is_mine or is_admin:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                if st.button("AI分析を見る", key=f"detail_{post['id']}"):
                    st.session_state.selected_post = post
                    st.session_state.analysis_result = None
                    st.session_state.chat_history = []
                    st.session_state.view = "detail"
                    st.rerun()
            with col2:
                if st.button("編集", key=f"edit_{post['id']}"):
                    st.session_state.selected_post = post
                    st.session_state.view = "edit"
                    st.rerun()
            with col3:
                if st.button("削除", key=f"delete_{post['id']}"):
                    st.session_state.delete_target_id = post['id']
                    st.session_state.view = "confirm_delete"
                    st.rerun()
        else:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                if st.button("AI分析を見る", key=f"detail_{post['id']}"):
                    st.session_state.selected_post = post
                    st.session_state.analysis_result = None
                    st.session_state.chat_history = []
                    st.session_state.view = "detail"
                    st.rerun()
            with col_b:
                if st.button("報告する", key=f"report_{post['id']}"):
                    st.session_state.report_target_id = post['id']
                    st.session_state.view = "report"
                    st.rerun()
        st.markdown('<div style="margin-bottom:8px;"></div>', unsafe_allow_html=True)

# =============================
# 画面: 報告
# =============================
elif st.session_state.view == "report":
    target_id = st.session_state.get("report_target_id")
    st.markdown('<div class="section-header">投稿を報告する</div>', unsafe_allow_html=True)
    st.caption("不適切な投稿を管理者に報告します。")

    reason = st.selectbox("報告理由", [
        "攻撃的・暴力的な表現",
        "誹謗中傷・個人攻撃",
        "差別的な表現",
        "スパム・無関係な内容",
        "その他"
    ])
    detail = st.text_area("詳細（任意）", placeholder="気になった点を具体的に書いてください")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("報告を送信する", type="primary", use_container_width=True):
            full_reason = f"{reason}{'：' + detail if detail else ''}"
            if report_post(target_id, full_reason):
                st.success("報告を受け付けました。ご協力ありがとうございます。")
                import time
                time.sleep(1.5)
                st.session_state.view = "home"
                st.rerun()
    with col2:
        if st.button("キャンセル", use_container_width=True):
            st.session_state.view = "home"
            st.rerun()

# =============================
# 画面: 新規投稿
# =============================
elif st.session_state.view == "create":
    st.markdown('<div class="section-header">こころを書き出す</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#FFF5EE;border:1.5px solid #F0CDB0;border-left:4px solid #E8A87C;border-radius:12px;padding:14px 16px;margin-bottom:16px;">
        <div style="font-size:13px;font-weight:500;color:#3D2B1F;margin-bottom:6px;">書く前にご確認ください</div>
        <div style="font-size:13px;color:#6B5043;line-height:1.8;">
            このアプリは<strong style="color:#3D2B1F;">親子のすれ違いやコミュニケーションの悩み</strong>を共有する場所です。<br>
            親・子ども、<strong style="color:#3D2B1F;">お互いの立場から想像できる悩み</strong>を書いてください。<br>
            <span style="color:#B07050;font-size:12px;">※ お金・仕事など、子どもの視点から理解しにくい内容はご遠慮ください。</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("思いつくままに、ゆっくり書いてみてください。")

    with st.form("post_form"):
        title = st.text_input("タイトル（任意）")
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        col_name, col_anon = st.columns([3, 1])
        with col_name:
            author = st.text_input("お名前（任意）", placeholder="例：Kokoro")
        with col_anon:
            st.write("")
            st.write("")
            is_anonymous = st.checkbox("匿名にする")
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        position = st.selectbox("あなたの立場", ["親", "子ども"])
        theme = st.selectbox("テーマ", ["親子関係", "子育て", "受験・進路", "学校生活", "友達関係", "習い事・スポーツ", "スマホ・ゲーム", "兄弟・姉妹関係", "将来の夢"])
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        happened = st.text_area("何がありましたか？（事実）", placeholder="どんなことが起きたか、できるだけ具体的に。")
        felt = st.text_area("どう感じましたか？（感情）", placeholder="そのとき、どんな気持ちになりましたか？")
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.caption("もう少し深く教えてください（任意）")
        really_wanted = st.text_area("本当はどうしてほしかったですか？", placeholder="例：ただ話を聞いてほしかった…")
        hardest_moment = st.text_area("一番つらかった瞬間はどこですか？", placeholder="例：○○と言われたとき…")

        submitted = st.form_submit_button("静かに投稿する")
        if submitted:
            new_post = {
                "id": str(uuid.uuid4()),
                "title": title if title else "名もなき感情",
                "author": author,
                "isAnonymous": is_anonymous,
                "position": position,
                "theme": theme,
                "whatHappened": happened,
                "howFelt": felt,
                "reallyWanted": really_wanted,
                "hardestMoment": hardest_moment,
                "tags": [],
                "createdAt": str(datetime.now().date()),
                "device_id": st.session_state.device_id
            }
            if save_post(new_post):
                st.session_state.view = "home"
                st.rerun()

    if st.button("キャンセルして戻る"):
        st.session_state.view = "home"
        st.rerun()

# =============================
# 画面: 編集
# =============================
elif st.session_state.view == "edit":
    post = st.session_state.selected_post
    st.markdown('<div class="section-header">投稿を編集する</div>', unsafe_allow_html=True)

    with st.form("edit_form"):
        title = st.text_input("タイトル", value=post['title'])
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        col_name, col_anon = st.columns([3, 1])
        with col_name:
            author = st.text_input("お名前（任意）", value=post.get('author', ''))
        with col_anon:
            st.write("")
            st.write("")
            is_anonymous = st.checkbox("匿名にする", value=post.get('isAnonymous', False))
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        position = st.selectbox("あなたの立場", ["親", "子ども"], index=["親", "子ども"].index(post['position']))
        themes = ["親子関係", "子育て", "受験・進路", "学校生活", "友達関係", "習い事・スポーツ", "スマホ・ゲーム", "兄弟・姉妹関係", "将来の夢"]
        theme = st.selectbox("テーマ", themes, index=themes.index(post['theme']) if post['theme'] in themes else 0)
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        happened = st.text_area("何がありましたか？（事実）", value=post['whatHappened'])
        felt = st.text_area("どう感じましたか？（感情）", value=post['howFelt'])
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.caption("もう少し深く教えてください（任意）")
        really_wanted = st.text_area("本当はどうしてほしかったですか？", value=post.get('reallyWanted', ''))
        hardest_moment = st.text_area("一番つらかった瞬間はどこですか？", value=post.get('hardestMoment', ''))

        submitted = st.form_submit_button("保存する")
        if submitted:
            updated = {**post, "title": title if title else "名もなき感情", "author": author, "isAnonymous": is_anonymous, "position": position, "theme": theme, "whatHappened": happened, "howFelt": felt, "reallyWanted": really_wanted, "hardestMoment": hardest_moment}
            if update_post(updated):
                st.success("保存しました！")
                st.session_state.view = "home"
                st.rerun()

    if st.button("キャンセルして戻る"):
        st.session_state.view = "home"
        st.rerun()

# =============================
# 画面: 削除確認
# =============================
elif st.session_state.view == "confirm_delete":
    target_id = st.session_state.get("delete_target_id")
    posts = load_posts()
    target_post = next((p for p in posts if p['id'] == target_id), None)

    st.markdown('<div class="section-header">投稿を削除しますか？</div>', unsafe_allow_html=True)
    if target_post:
        st.warning(f"「{target_post['title']}」を削除します。この操作は元に戻せません。")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("削除する", type="primary"):
            if delete_post(target_id):
                st.session_state.view = "home"
                st.rerun()
    with col2:
        if st.button("キャンセル"):
            st.session_state.view = "home"
            st.rerun()

# =============================
# 画面: マイページ
# =============================
# =============================
# 画面: 管理者ページ（報告一覧）
# =============================
elif st.session_state.view == "admin_reports":
    if not st.session_state.get("is_admin"):
        st.session_state.view = "home"
        st.rerun()

    if st.button("← ホームへ戻る"):
        st.session_state.view = "home"
        st.rerun()

    st.markdown('<div class="section-header">報告された投稿</div>', unsafe_allow_html=True)

    reports = load_reports()
    if not reports:
        st.info("報告はまだありません。")
    else:
        st.markdown(f'<div style="font-size:13px;color:#9C7B6A;margin-bottom:12px;">報告数：{len(reports)}件</div>', unsafe_allow_html=True)
        for r in reports:
            post_info = r.get("posts", {}) or {}
            title = post_info.get("title", "不明")
            position = post_info.get("position", "")
            theme = post_info.get("theme", "")
            what_happened = post_info.get("what_happened", "") or ""
            how_felt = post_info.get("how_felt", "") or ""
            really_wanted = post_info.get("really_wanted", "") or ""
            hardest_moment = post_info.get("hardest_moment", "") or ""

            import html as html_lib
            st.markdown(f"""
            <div style="background:#FFF5EE;border:1.5px solid #F0CDB0;border-left:4px solid #E8A87C;border-radius:12px;padding:16px;margin-bottom:10px;">
                <div style="font-size:14px;font-weight:500;color:#3D2B1F;margin-bottom:4px;">{html_lib.escape(title)}</div>
                <div style="font-size:12px;color:#B07050;margin-bottom:10px;">{position} · {theme}</div>
                <div style="font-size:12px;color:#9C7B6A;margin-bottom:2px;">何があったか</div>
                <div style="font-size:13px;color:#4A2C1A;line-height:1.7;margin-bottom:8px;">{html_lib.escape(what_happened)}</div>
                <div style="font-size:12px;color:#9C7B6A;margin-bottom:2px;">どう感じたか</div>
                <div style="font-size:13px;color:#4A2C1A;line-height:1.7;margin-bottom:8px;">{html_lib.escape(how_felt)}</div>
                {f'<div style="font-size:12px;color:#9C7B6A;margin-bottom:2px;">本当はどうしてほしかったか</div><div style="font-size:13px;color:#4A2C1A;line-height:1.7;margin-bottom:8px;">{html_lib.escape(really_wanted)}</div>' if really_wanted else ''}
                {f'<div style="font-size:12px;color:#9C7B6A;margin-bottom:2px;">一番つらかった瞬間</div><div style="font-size:13px;color:#4A2C1A;line-height:1.7;margin-bottom:8px;">{html_lib.escape(hardest_moment)}</div>' if hardest_moment else ''}
                <div style="font-size:12px;background:#FDE8D8;color:#993C1D;padding:4px 10px;border-radius:8px;display:inline-block;margin-top:4px;">報告理由：{html_lib.escape(r.get('reason', ''))}</div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("投稿を削除する", key=f"admin_del_{r['id']}", type="primary", use_container_width=True):
                    if r.get("post_id"):
                        delete_post(r["post_id"])
                        st.success("削除しました")
                        st.rerun()
            with col2:
                if st.button("問題なし（報告を消す）", key=f"admin_ok_{r['id']}", use_container_width=True):
                    try:
                        supabase = get_supabase()
                        supabase.table("reports").delete().eq("id", r["id"]).execute()
                        st.rerun()
                    except:
                        pass

elif st.session_state.view == "mypage":
    st.markdown('<div class="section-header">マイページ</div>', unsafe_allow_html=True)
    st.caption("この端末から投稿した記録です。")

    all_posts = load_posts()
    my_posts = [p for p in all_posts if p.get("device_id") == st.session_state.device_id]

    if not my_posts:
        st.markdown("""<div style="background:#FFFDF8; border:1.5px solid #E8D8C4; border-radius:14px; padding:24px; text-align:center; color:#9C7B6A; font-size:14px; line-height:1.8;">まだ投稿がありません。<br>「こころを書き出す」から最初の一歩を。</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="font-size:13px; color:#9C7B6A; margin-bottom:12px;">投稿数：{len(my_posts)}件</div>', unsafe_allow_html=True)
        for post in my_posts:
            st.markdown(render_post_card(post), unsafe_allow_html=True)
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                if st.button("AI分析を見る", key=f"my_detail_{post['id']}"):
                    st.session_state.selected_post = post
                    st.session_state.analysis_result = None
                    st.session_state.chat_history = []
                    st.session_state.view = "detail"
                    st.rerun()
            with col2:
                if st.button("編集", key=f"my_edit_{post['id']}"):
                    st.session_state.selected_post = post
                    st.session_state.view = "edit"
                    st.rerun()
            with col3:
                if st.button("削除", key=f"my_delete_{post['id']}"):
                    st.session_state.delete_target_id = post['id']
                    st.session_state.view = "confirm_delete"
                    st.rerun()

# =============================
# 画面: 詳細・分析・チャット
# =============================
elif st.session_state.view == "detail":
    post = st.session_state.selected_post

    if st.button("← 一覧へ戻る", use_container_width=True):
        st.session_state.view = "home"
        st.rerun()
    is_mine = post.get("device_id") == st.session_state.device_id
    is_admin = st.session_state.get("is_admin", False)
    if is_mine or is_admin:
        col_edit, col_delete = st.columns([1, 1])
        with col_edit:
            if st.button("編集", use_container_width=True):
                st.session_state.view = "edit"
                st.rerun()
        with col_delete:
            if st.button("削除", use_container_width=True):
                st.session_state.delete_target_id = post['id']
                st.session_state.view = "confirm_delete"
                st.rerun()

    is_en = st.session_state.get("lang") == "en"
    anon_badge = '<span class="badge-anon">Anonymous</span>' if (post.get('isAnonymous') and is_en) else ('<span class="badge-anon">匿名</span>' if post.get('isAnonymous') else '')
    author_text = f'<span style="font-size:12px;color:#9C7B6A;margin-left:4px;">{post.get("author","")}</span>' if post.get("author") and not post.get("isAnonymous") else ''

    display_title = translate_to_english(post["title"]) if is_en else post["title"]
    display_position = ("Parent" if post["position"] == "親" else "Child") if is_en else post["position"]
    display_what = translate_to_english(post["whatHappened"]) if is_en else post["whatHappened"]
    display_felt = translate_to_english(post["howFelt"]) if is_en else post["howFelt"]
    display_wanted = translate_to_english(post.get("reallyWanted","")) if is_en else post.get("reallyWanted","")
    display_hardest = translate_to_english(post.get("hardestMoment","")) if is_en else post.get("hardestMoment","")

    label_what = "What happened" if is_en else "何があったか"
    label_felt = "How I felt" if is_en else "どう感じたか"
    label_wanted = "What I really wanted" if is_en else "本当はどうしてほしかったか"
    label_hardest = "The hardest moment" if is_en else "一番つらかった瞬間"
    btn_ai = "Reflect with AI" if is_en else "AIと見つめ直す"
    spinner_msg = "Weaving words..." if is_en else "言葉を紡いでいます..."
    chat_intro = "Analysis complete. Feel free to ask anything." if is_en else "分析が終わりました。気になること、もっと深めたいこと、何でも話しかけてみてください。一緒に考えます。"

    st.markdown(f'<div class="section-header">{display_title}{anon_badge}{author_text}</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:13px;color:#B07050;margin-bottom:12px;">{post["theme"]} &nbsp;·&nbsp; {display_position} &nbsp;·&nbsp; {post["createdAt"]}</div>', unsafe_allow_html=True)

    st.markdown(f'<div style="background:#FFFDF8;border:1.5px solid #E8D8C4;border-left:4px solid #E8A87C;border-radius:12px;padding:16px;margin-bottom:10px;"><div style="font-size:12px;color:#9C7B6A;margin-bottom:4px;">{label_what}</div><div style="font-size:14px;color:#3D2B1F;line-height:1.7;">{display_what}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background:#FFFDF8;border:1.5px solid #E8D8C4;border-left:4px solid #C4A882;border-radius:12px;padding:16px;margin-bottom:10px;"><div style="font-size:12px;color:#9C7B6A;margin-bottom:4px;">{label_felt}</div><div style="font-size:14px;color:#3D2B1F;line-height:1.7;">{display_felt}</div></div>', unsafe_allow_html=True)
    if post.get('reallyWanted'):
        st.markdown(f'<div style="background:#FFFDF8;border:1.5px solid #E8D8C4;border-left:4px solid #D9B8A0;border-radius:12px;padding:16px;margin-bottom:10px;"><div style="font-size:12px;color:#9C7B6A;margin-bottom:4px;">{label_wanted}</div><div style="font-size:14px;color:#3D2B1F;line-height:1.7;">{display_wanted}</div></div>', unsafe_allow_html=True)
    if post.get('hardestMoment'):
        st.markdown(f'<div style="background:#FFFDF8;border:1.5px solid #E8D8C4;border-left:4px solid #D9B8A0;border-radius:12px;padding:16px;margin-bottom:10px;"><div style="font-size:12px;color:#9C7B6A;margin-bottom:4px;">{label_hardest}</div><div style="font-size:14px;color:#3D2B1F;line-height:1.7;">{display_hardest}</div></div>', unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if st.session_state.analysis_result is None:
        if st.button(btn_ai):
            with st.spinner(spinner_msg):
                result = analyze_post(post)
                if "error" in result:
                    st.error(f"分析に失敗しました: {result['error']}")
                else:
                    st.session_state.analysis_result = result
                    st.session_state.chat_history = [{"role": "assistant", "content": chat_intro}]
                    st.rerun()

    if st.session_state.analysis_result:
        result = st.session_state.analysis_result
        # 1. あなたの気持ちを受け止める
        lbl_your = "Your Feelings" if is_en else "あなたの気持ち"
        lbl_hidden = "What You Really Feel" if is_en else "奥にある本当の気持ち"
        lbl_other = "Why the Other Person Did That" if is_en else "相手はなぜそうしたのか"
        lbl_how = "Try Saying This" if is_en else "次にこう話しかけてみましょう"
        lbl_hints = "What You Can Do Now" if is_en else "今すぐできること"

        # 英語モードの場合は分析結果も翻訳
        def tr(text):
            if is_en and text:
                return translate_to_english(text)
            return text

        if result.get("your_feelings"):
            st.markdown(f'<div style="background:#FFF5EE;border:1.5px solid #F0CDB0;border-left:4px solid #E8A87C;border-radius:12px;padding:18px;margin-bottom:12px;"><div style="font-size:13px;font-weight:500;color:#3D2B1F;margin-bottom:8px;">{lbl_your}</div><div style="font-size:15px;color:#4A2C1A;line-height:1.9;">{tr(result.get("your_feelings",""))}</div></div>', unsafe_allow_html=True)

        if result.get("hidden_feelings"):
            st.markdown(f'<div style="background:#FFFDF8;border:1.5px solid #E8D8C4;border-radius:12px;padding:16px;margin-bottom:12px;"><div style="font-size:13px;font-weight:500;color:#3D2B1F;margin-bottom:6px;">{lbl_hidden}</div><div style="font-size:14px;color:#4A2C1A;line-height:1.7;">{tr(result.get("hidden_feelings",""))}</div></div>', unsafe_allow_html=True)

        if result.get("other_perspective"):
            st.markdown(f'<div style="background:#F5F0FF;border:1.5px solid #D8C8F0;border-radius:12px;padding:16px;margin-bottom:12px;"><div style="font-size:13px;font-weight:500;color:#5A3E8A;margin-bottom:6px;">{lbl_other}</div><div style="font-size:14px;color:#3D2B5A;line-height:1.7;">{tr(result.get("other_perspective",""))}</div></div>', unsafe_allow_html=True)

        if result.get("how_to_talk"):
            st.markdown(f'<div style="background:#FFF8F0;border:1.5px solid #F0D0A0;border-left:4px solid #E8A87C;border-radius:12px;padding:16px;margin-bottom:12px;"><div style="font-size:13px;font-weight:500;color:#3D2B1F;margin-bottom:6px;">{lbl_how}</div><div style="font-size:14px;color:#4A2C1A;line-height:1.9;">{tr(result.get("how_to_talk",""))}</div></div>', unsafe_allow_html=True)

        hints = result.get('actionable_hints', [])
        if hints:
            hints_html = ''.join([f'<div style="display:flex;gap:8px;margin-bottom:8px;"><span style="color:#E8A87C;font-weight:500;">·</span><span style="font-size:14px;color:#4A2C1A;line-height:1.7;">{tr(h)}</span></div>' for h in hints])
            st.markdown(f'<div style="background:#FFFDF8;border:1.5px solid #E8D8C4;border-radius:12px;padding:16px;margin-top:4px;"><div style="font-size:13px;font-weight:500;color:#3D2B1F;margin-bottom:10px;">{lbl_hints}</div>{hints_html}</div>', unsafe_allow_html=True)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:15px;font-weight:500;color:#3D2B1F;margin-bottom:4px;">AIとさらに話してみる</div>', unsafe_allow_html=True)
        st.caption("気持ちを深堀りしたり、具体的なアドバイスを聞いたり、自由に話しかけてください。")

        for msg in st.session_state.chat_history:
            if msg["role"] == "assistant":
                st.markdown(f'<div class="chat-ai">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-user">{msg["content"]}</div>', unsafe_allow_html=True)

        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("メッセージを入力...", placeholder="例：相手にどう伝えればいいですか？")
            send = st.form_submit_button("送る")
            if send and user_input.strip():
                with st.spinner("考えています..."):
                    ai_response = chat_with_ai(post, result, st.session_state.chat_history, user_input)
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                    st.rerun()
