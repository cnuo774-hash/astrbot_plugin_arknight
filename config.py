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
    padding: 36px;
    background: #15171b;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: #f8fafc;
    box-sizing: border-box;
">
    <div style="
        display: flex;
        flex-direction: column;
        gap: 24px;
    ">
        <div style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 28px;
            padding-bottom: 20px;
            border-bottom: 2px solid rgba(148, 163, 184, 0.22);
        ">
            <div style="
                display: flex;
                align-items: center;
                gap: 24px;
                min-width: 0;
            ">
                <div style="
                    width: 128px;
                    height: 128px;
                    border-radius: 8px;
                    overflow: hidden;
                    background: #2b3038;
                    border: 3px solid rgba(226, 232, 240, 0.55);
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
                        font-size: 22px;
                        color: #94a3b8;
                    ">头像</div>
                    {% endif %}
                </div>

                <div style="min-width: 0;">
                    <div style="
                        font-size: 22px;
                        color: #38bdf8;
                        font-weight: 700;
                        letter-spacing: 0;
                    ">RHODES ISLAND TERMINAL</div>
                    <div style="
                        margin-top: 8px;
                        font-size: 46px;
                        font-weight: 850;
                        line-height: 1.12;
                        color: #ffffff;
                        word-break: break-all;
                    ">{{ nickname }}</div>
                    <div style="
                        margin-top: 10px;
                        font-size: 24px;
                        color: #cbd5e1;
                    ">UID {{ uid }} · {{ channel_name or '未返回' }}</div>
                </div>
            </div>

            <div style="
                flex-shrink: 0;
                text-align: right;
                color: #94a3b8;
                font-size: 22px;
                line-height: 1.45;
            ">
                <div style="color: #e2e8f0; font-weight: 800;">明日方舟基础信息</div>
                <div>DATA SNAPSHOT</div>
            </div>
        </div>

        <div style="
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        ">
            <div style="
                padding: 20px;
                border-radius: 8px;
                background: #232832;
                border-left: 6px solid #38bdf8;
            ">
                <div style="font-size: 22px; color: #94a3b8;">玩家等级</div>
                <div style="margin-top: 10px; font-size: 38px; font-weight: 850;">
                    {{ level }}
                </div>
            </div>

            <div style="
                padding: 20px;
                border-radius: 8px;
                background: #232832;
                border-left: 6px solid #22c55e;
            ">
                <div style="font-size: 22px; color: #94a3b8;">注册日期</div>
                <div style="margin-top: 10px; font-size: 31px; font-weight: 780;">
                    {{ registered_at }}
                </div>
            </div>

            <div style="
                padding: 20px;
                border-radius: 8px;
                background: #232832;
                border-left: 6px solid #f59e0b;
            ">
                <div style="font-size: 22px; color: #94a3b8;">主线进度</div>
                <div style="margin-top: 10px; font-size: 31px; font-weight: 780;">
                    {{ mainline }}
                </div>
            </div>

            <div style="
                padding: 20px;
                border-radius: 8px;
                background: #232832;
                border-left: 6px solid #a78bfa;
            ">
                <div style="font-size: 22px; color: #94a3b8;">渠道</div>
                <div style="margin-top: 10px; font-size: 31px; font-weight: 780;">
                    {{ channel_name or '未返回' }}
                </div>
            </div>

            <div style="
                grid-column: span 2;
                padding: 20px;
                border-radius: 8px;
                background: #232832;
                border-left: 6px solid #ef4444;
            ">
                <div style="font-size: 22px; color: #94a3b8;">理智恢复时间</div>
                <div style="margin-top: 10px; font-size: 34px; font-weight: 820;">
                    {{ recovery_time }}
                </div>
            </div>

            <div style="
                padding: 20px;
                border-radius: 8px;
                background: #232832;
                border-left: 6px solid #06b6d4;
            ">
                <div style="font-size: 22px; color: #94a3b8;">干员数</div>
                <div style="margin-top: 10px; font-size: 38px; font-weight: 850;">
                    {{ char_count }}
                </div>
            </div>

            <div style="
                padding: 20px;
                border-radius: 8px;
                background: #232832;
                border-left: 6px solid #ec4899;
            ">
                <div style="font-size: 22px; color: #94a3b8;">时装数</div>
                <div style="margin-top: 10px; font-size: 38px; font-weight: 850;">
                    {{ skin_count }}
                </div>
            </div>
        </div>
    </div>
</div>
'''
