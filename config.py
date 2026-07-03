from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent
arknight_name_file = PLUGIN_DIR / "Arknight_name_data.json"

HYPERGRYPH_APP_CODE = "4ca99fa6b56cc2ba"
ARKNIGHTS_APP_CODE = "arknights"

TOKEN_URL = "https://as.hypergryph.com/user/auth/v1/token_by_phone_password"
GRANT_URL = "https://as.hypergryph.com/user/oauth2/v2/grant"
CRED_URL = "https://zonai.skland.com/api/v1/user/auth/generate_cred_by_code"
BINDING_URL = "https://zonai.skland.com/api/v1/game/player/binding"
PLAYER_URL = "https://zonai.skland.com/api/v1/game/player/info"

REQUEST_TIMEOUT = 15
SKLAND_USER_AGENT = (
    "Skland/1.32.1 (com.hypergryph.skland; build:103201004; "
    "Android 33; ) Okhttp/4.11.0"
)
DEFAULT_HEADERS = {
    "User-Agent": SKLAND_USER_AGENT,
    "Content-Type": "application/json",
}
SKLAND_SIGN_HEADERS = {
    "User-Agent": SKLAND_USER_AGENT,
    "Connection": "close",
}

BIND_FORMAT = "/绑定账号 手机号 密码"
BIND_PROMPT = (
    "绑定需要使用森空岛账号的私密信息，请在私聊中发送：\n"
    f"{BIND_FORMAT}\n"
    "示例：绑定账号 13800138000 你的密码\n"
    "插件只会保存查询所需的森空岛凭据和角色 UID，"
    "不会保存密码。"
)
TMPL = '''
<div style="
    width: 1280px;
    min-height: 720px;
    padding: 56px;
    background: #f4f7fb;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: #1f2933;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: center;
">
    <div style="
        display: flex;
        align-items: center;
        gap: 36px;
        padding: 42px;
        border-radius: 22px;
        background: #ffffff;
        box-shadow: 0 18px 48px rgba(31, 41, 51, 0.12);
    ">
        <div style="
            width: 188px;
            height: 188px;
            border-radius: 28px;
            overflow: hidden;
            background: #e5e9ef;
            flex-shrink: 0;
        ">
            {% if avatar_url %}
            <img src="{{ avatar_url }}" style="
                width: 100%;
                height: 100%;
                object-fit: cover;
                display: block;
            ">
            {% else %}
            <div style="
                width: 100%;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 28px;
                color: #6b7280;
            ">头像</div>
            {% endif %}
        </div>

        <div style="flex: 1; min-width: 0;">
            <div style="
                font-size: 28px;
                color: #64748b;
                margin-bottom: 12px;
            "></div>

            <div style="
                font-size: 58px;
                font-weight: 800;
                color: #111827;
                line-height: 1.2;
                word-break: break-all;
            ">{{ nickname }}</div>

            {% if uid %}
            <div style="
                margin-top: 18px;
                font-size: 30px;
                color: #64748b;
            ">UID：{{ uid }}</div>
            {% endif %}
        </div>
    </div>

    <div style="
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 22px;
        margin-top: 28px;
    ">
        <div style="
            padding: 30px;
            border-radius: 20px;
            background: #ffffff;
            box-shadow: 0 10px 28px rgba(31, 41, 51, 0.08);
        ">
            <div style="font-size: 26px; color: #64748b;">玩家等级</div>
            <div style="margin-top: 14px; font-size: 46px; font-weight: 800;">
                {{ level }}
            </div>
        </div>

        <div style="
            padding: 30px;
            border-radius: 20px;
            background: #ffffff;
            box-shadow: 0 10px 28px rgba(31, 41, 51, 0.08);
        ">
            <div style="font-size: 26px; color: #64748b;">注册日期</div>
            <div style="margin-top: 14px; font-size: 42px; font-weight: 750;">
                {{ registered_at }}
            </div>
        </div>

        <div style="
            padding: 30px;
            border-radius: 20px;
            background: #ffffff;
            box-shadow: 0 10px 28px rgba(31, 41, 51, 0.08);
        ">
            <div style="font-size: 26px; color: #64748b;">主线进度</div>
            <div style="margin-top: 14px; font-size: 42px; font-weight: 750;">
                {{ mainline }}
            </div>
        </div>

        <div style="
            padding: 30px;
            border-radius: 20px;
            background: #ffffff;
            box-shadow: 0 10px 28px rgba(31, 41, 51, 0.08);
        ">
            <div style="font-size: 26px; color: #64748b;">渠道</div>
            <div style="margin-top: 14px; font-size: 42px; font-weight: 750;">
                {{ channel_name or '未返回' }}
            </div>
        </div>
    </div>
</div>
'''
