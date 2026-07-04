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
USER_ID_URL = "https://zonai.skland.com/api/v1/user/teenager"
ROGUE_URL = "https://zonai.skland.com/api/v1/game/arknights/rogue"

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
ROGUE_TOPICS = {
    "傀影": "rogue_1",
    "水月": "rogue_2",
    "萨米": "rogue_3",
    "萨卡兹": "rogue_4",
    "岁": "rogue_5",
    "界园": "rogue_5",
    "默认": "rogue_4",
}
BIND_PROMPT = (
    "绑定需要使用森空岛账号的私密信息，请在私聊中发送：\n"
    f"{BIND_FORMAT}\n"
    "示例：绑定账号 13800138000 你的密码\n"
    "插件只会保存查询所需的森空岛凭据和角色 UID，"
    "不会保存密码。"
)
TMPL = '''
<style>
html, body {
    margin: 0;
    padding: 0;
    background: #15171b;
}
</style>
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

        <div style="
            padding-top: 4px;
        ">
            <div style="
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 14px;
            ">
                <div style="
                    color: #e2e8f0;
                    font-size: 24px;
                    font-weight: 820;
                ">助战干员</div>
                <div style="
                    color: #64748b;
                    font-size: 18px;
                    font-weight: 700;
                ">SUPPORT UNITS</div>
            </div>

            <div style="
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
            ">
                {% for assist in assist_chars %}
                <div style="
                    padding: 18px 20px;
                    border-radius: 8px;
                    background: #20252d;
                    border: 1px solid rgba(148, 163, 184, 0.22);
                    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
                ">
                    <div style="
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        gap: 12px;
                    ">
                        <div style="
                            min-width: 0;
                            color: #ffffff;
                            font-size: 28px;
                            font-weight: 850;
                            line-height: 1.15;
                            overflow: hidden;
                            text-overflow: ellipsis;
                            white-space: nowrap;
                        ">{{ assist.name }}</div>
                        <div style="
                            flex-shrink: 0;
                            color: #38bdf8;
                            font-size: 20px;
                            font-weight: 800;
                        ">#{{ assist.index }}</div>
                    </div>

                    <div style="
                        margin-top: 12px;
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 8px;
                    ">
                        <div style="font-size: 18px; color: #cbd5e1;">{{ assist.level }}</div>
                        <div style="font-size: 18px; color: #cbd5e1;">{{ assist.potential }}</div>
                        <div style="
                            grid-column: span 2;
                            font-size: 18px;
                            color: #cbd5e1;
                        ">{{ assist.skill }}</div>
                    </div>

                    <div style="
                        margin-top: 10px;
                        padding-top: 10px;
                        border-top: 1px solid rgba(148, 163, 184, 0.16);
                        color: #94a3b8;
                        font-size: 18px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                    ">{{ assist.equip }}</div>
                </div>
                {% endfor %}

                {% if not assist_chars %}
                <div style="
                    grid-column: span 3;
                    padding: 18px 20px;
                    border-radius: 8px;
                    background: #20252d;
                    color: #94a3b8;
                    font-size: 22px;
                ">未返回助战干员信息</div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
'''

ROGUE_TMPL = '''
<style>
html, body {
    margin: 0;
    padding: 0;
    background: #101113;
}
.rogue-wrap {
    width: 1280px;
    padding: 28px;
    box-sizing: border-box;
    background: #101113;
    color: #f7f7f4;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.rogue-hero {
    position: relative;
    min-height: 300px;
    overflow: hidden;
    border-radius: 8px;
    background: #24201d;
    border: 1px solid rgba(255, 255, 255, 0.16);
}
.rogue-hero-img {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0.74;
}
.rogue-hero-shade {
    position: absolute;
    inset: 0;
    background:
        linear-gradient(90deg, rgba(16, 17, 19, 0.98) 0%, rgba(16, 17, 19, 0.72) 45%, rgba(16, 17, 19, 0.18) 100%),
        linear-gradient(0deg, rgba(16, 17, 19, 0.72) 0%, rgba(16, 17, 19, 0.10) 72%);
}
.rogue-hero-content {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: 1.35fr 0.9fr;
    gap: 24px;
    padding: 28px;
}
.rogue-label {
    font-size: 20px;
    color: #f3b563;
    font-weight: 850;
    letter-spacing: 0;
}
.rogue-title {
    margin-top: 8px;
    font-size: 54px;
    line-height: 1.05;
    font-weight: 900;
    color: #ffffff;
    word-break: break-word;
}
.rogue-subtitle {
    margin-top: 12px;
    font-size: 24px;
    color: #d6d3cc;
    font-weight: 650;
}
.rogue-player {
    margin-top: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.rogue-avatar {
    width: 76px;
    height: 76px;
    border-radius: 8px;
    object-fit: cover;
    background: #2b2d31;
    border: 2px solid rgba(255, 255, 255, 0.28);
}
.rogue-player-name {
    font-size: 28px;
    font-weight: 850;
}
.rogue-player-meta {
    margin-top: 4px;
    font-size: 20px;
    color: #c9c4bb;
}
.metric-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    align-content: start;
}
.metric {
    min-height: 88px;
    padding: 16px;
    box-sizing: border-box;
    background: rgba(20, 22, 24, 0.84);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-left: 5px solid #f3b563;
}
.metric-name {
    font-size: 18px;
    color: #aaa69d;
    font-weight: 700;
}
.metric-value {
    margin-top: 8px;
    font-size: 30px;
    line-height: 1.05;
    font-weight: 900;
    color: #ffffff;
    word-break: break-word;
}
.section {
    margin-top: 18px;
}
.section-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 10px;
}
.section-title {
    font-size: 26px;
    font-weight: 900;
    color: #ffffff;
}
.section-note {
    font-size: 18px;
    color: #8f918e;
    font-weight: 750;
}
.topic-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
}
.topic {
    overflow: hidden;
    border-radius: 8px;
    min-height: 154px;
    background: #232426;
    border: 2px solid rgba(255, 255, 255, 0.12);
}
.topic.selected {
    border-color: #f3b563;
}
.topic img {
    width: 100%;
    height: 100px;
    display: block;
    object-fit: cover;
}
.topic-name {
    padding: 10px 12px 4px;
    font-size: 18px;
    line-height: 1.2;
    font-weight: 850;
    color: #ffffff;
}
.topic-id {
    padding: 0 12px 10px;
    font-size: 15px;
    color: #a6a39c;
}
.body-grid {
    display: grid;
    grid-template-columns: 1.18fr 0.82fr;
    gap: 16px;
    align-items: start;
}
.panel {
    border-radius: 8px;
    background: #1b1d1f;
    border: 1px solid rgba(255, 255, 255, 0.12);
    padding: 16px;
    box-sizing: border-box;
}
.record-list {
    display: grid;
    gap: 12px;
}
.record {
    padding: 14px;
    border-radius: 8px;
    background: #242628;
    border-left: 5px solid #d94d3f;
}
.record-top {
    display: flex;
    justify-content: space-between;
    gap: 14px;
    align-items: flex-start;
}
.record-title {
    font-size: 23px;
    line-height: 1.18;
    color: #ffffff;
    font-weight: 900;
}
.record-time {
    flex-shrink: 0;
    font-size: 17px;
    color: #b8b2a8;
    font-weight: 700;
}
.record-meta {
    margin-top: 7px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}
.pill {
    padding: 5px 8px;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.08);
    color: #d6d1c8;
    font-size: 16px;
    font-weight: 700;
}
.record-chars {
    margin-top: 10px;
    color: #f3b563;
    font-size: 17px;
    line-height: 1.35;
    font-weight: 750;
}
.mini-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
}
.mini {
    min-height: 76px;
    padding: 12px;
    border-radius: 8px;
    background: #242628;
    box-sizing: border-box;
}
.mini-name {
    font-size: 16px;
    color: #9b9d99;
    font-weight: 700;
}
.mini-value {
    margin-top: 6px;
    font-size: 25px;
    color: #ffffff;
    font-weight: 900;
    word-break: break-word;
}
.chip-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}
.chip {
    padding: 8px 10px;
    border-radius: 6px;
    background: #242628;
    color: #f0ede6;
    font-size: 17px;
    line-height: 1.25;
    font-weight: 750;
}
.ending-row {
    display: grid;
    grid-template-columns: 72px 1fr 62px;
    align-items: center;
    gap: 10px;
    margin-top: 9px;
}
.ending-name {
    color: #c8c4ba;
    font-size: 16px;
    font-weight: 800;
}
.ending-bar {
    height: 12px;
    border-radius: 6px;
    background: #2c2e30;
    overflow: hidden;
}
.ending-fill {
    height: 100%;
    border-radius: 6px;
    background: #f3b563;
}
.ending-value {
    color: #ffffff;
    font-size: 16px;
    text-align: right;
    font-weight: 850;
}
</style>
<div class="rogue-wrap">
    <div class="rogue-hero">
        {% if hero_pic %}
        <img class="rogue-hero-img" src="{{ hero_pic }}">
        {% endif %}
        <div class="rogue-hero-shade"></div>
        <div class="rogue-hero-content">
            <div>
                <div class="rogue-label">INTEGRATED STRATEGIES</div>
                <div class="rogue-title">{{ topic_name }}</div>
                <div class="rogue-subtitle">{{ mode }} · {{ topic_id }}</div>
                <div class="rogue-player">
                    {% if avatar_url %}
                    <img class="rogue-avatar" src="{{ avatar_url }}">
                    {% else %}
                    <div class="rogue-avatar"></div>
                    {% endif %}
                    <div>
                        <div class="rogue-player-name">{{ player_name }}</div>
                        <div class="rogue-player-meta">Lv.{{ player_level }} · {{ medal_text }}</div>
                    </div>
                </div>
            </div>
            <div class="metric-grid">
                {% for metric in hero_metrics %}
                <div class="metric" style="border-left-color: {{ metric.color }};">
                    <div class="metric-name">{{ metric.name }}</div>
                    <div class="metric-value">{{ metric.value }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-head">
            <div class="section-title">肉鸽主题</div>
            <div class="section-note">森空岛一次返回的全部主题封面</div>
        </div>
        <div class="topic-grid">
            {% for topic in topics %}
            <div class="topic{% if topic.selected %} selected{% endif %}">
                {% if topic.pic %}
                <img src="{{ topic.pic }}">
                {% endif %}
                <div class="topic-name">{{ topic.name }}</div>
                <div class="topic-id">{{ topic.id }}</div>
            </div>
            {% endfor %}
        </div>
    </div>

    <div class="section body-grid">
        <div class="panel">
            <div class="section-head">
                <div class="section-title">最近探索</div>
                <div class="section-note">{{ record_count }} 条记录</div>
            </div>
            <div class="record-list">
                {% for record in records %}
                <div class="record">
                    <div class="record-top">
                        <div>
                            <div class="record-title">{{ record.band }} · {{ record.stage }}</div>
                            <div class="record-meta">
                                <span class="pill">{{ record.result }}</span>
                                <span class="pill">难度 {{ record.grade }}</span>
                                <span class="pill">{{ record.score }} 分</span>
                                <span class="pill">{{ record.duration }}</span>
                            </div>
                        </div>
                        <div class="record-time">{{ record.date }}</div>
                    </div>
                    <div class="record-meta">
                        <span class="pill">层数 {{ record.zones }}</span>
                        <span class="pill">节点 {{ record.nodes }}</span>
                        <span class="pill">战斗 {{ record.battles }}</span>
                        <span class="pill">收藏 {{ record.relics }}</span>
                        <span class="pill">招募 {{ record.recruits }}</span>
                    </div>
                    <div class="record-chars">{{ record.chars }}</div>
                </div>
                {% endfor %}
                {% if not records %}
                <div class="record">
                    <div class="record-title">未返回最近探索记录</div>
                </div>
                {% endif %}
            </div>
        </div>

        <div>
            <div class="panel">
                <div class="section-head">
                    <div class="section-title">生涯累计</div>
                    <div class="section-note">CAREER</div>
                </div>
                <div class="mini-grid">
                    {% for metric in career_metrics %}
                    <div class="mini">
                        <div class="mini-name">{{ metric.name }}</div>
                        <div class="mini-value">{{ metric.value }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="panel section">
                <div class="section-head">
                    <div class="section-title">常用干员</div>
                    <div class="section-note">OPERATORS</div>
                </div>
                <div class="chip-list">
                    {% for char in chars %}
                    <div class="chip">{{ char }}</div>
                    {% endfor %}
                    {% if not chars %}
                    <div class="chip">未返回</div>
                    {% endif %}
                </div>
            </div>

            <div class="panel section">
                <div class="section-head">
                    <div class="section-title">偏好统计</div>
                    <div class="section-note">POPULAR</div>
                </div>
                <div class="chip-list">
                    {% for item in popular_items %}
                    <div class="chip">{{ item }}</div>
                    {% endfor %}
                    {% if not popular_items %}
                    <div class="chip">未返回</div>
                    {% endif %}
                </div>
            </div>

            <div class="panel section">
                <div class="section-head">
                    <div class="section-title">结局占比</div>
                    <div class="section-note">ENDING RATE</div>
                </div>
                {% for ending in endings %}
                <div class="ending-row">
                    <div class="ending-name">{{ ending.name }}</div>
                    <div class="ending-bar">
                        <div class="ending-fill" style="width: {{ ending.width }}%;"></div>
                    </div>
                    <div class="ending-value">{{ ending.value }}%</div>
                </div>
                {% endfor %}
                {% if not endings %}
                <div class="chip">未返回</div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
'''
