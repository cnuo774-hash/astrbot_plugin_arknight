from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import math
import re
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from urllib import error, parse, request

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from . import config


@register(
    "Arknight_helper",
    "bsnqwq",
    "一个帮助查询明日方舟信息的插件",
    "1.1.0",
)
class MyPlugin(Star):
    def __init__(self, context: Context):
        """初始化插件实例。

        Args:
            context: AstrBot 插件上下文。
        """
        super().__init__(context)

    async def initialize(self):
        """在 AstrBot 加载插件后执行初始化。"""

    def _read_bindings(self) -> dict[str, Any]:
        """从插件 JSON 文件读取账号绑定数据。

        Returns:
            AstrBot 发送者 ID 到森空岛绑定数据的映射。

        Raises:
            ValueError: If the binding file is unreadable or malformed.
        """
        if not config.arknight_name_file.exists():
            return {}
        try:
            contents = config.arknight_name_file.read_text(encoding="utf-8")
            data = json.loads(contents) if contents.strip() else {}
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                "读取账号绑定数据失败，请检查绑定文件，原数据已保留。"
            ) from exc
        if isinstance(data, dict):
            return data
        raise ValueError("账号绑定数据格式异常，请检查绑定文件，原数据已保留。")

    def _write_bindings(self, data: dict[str, Any]) -> None:
        """将账号绑定数据写入插件 JSON 文件。

        Args:
            data: AstrBot 发送者 ID 到森空岛绑定数据的映射。

        Raises:
            ValueError: If the binding file cannot be saved.
        """
        temporary_path = None
        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=config.arknight_name_file.parent,
                prefix=f".{config.arknight_name_file.name}.",
                delete=False,
            ) as f:
                temporary_path = Path(f.name)
                json.dump(data, f, ensure_ascii=False, indent=2)
            temporary_path.replace(config.arknight_name_file)
        except OSError as exc:
            raise ValueError(
                "保存账号绑定数据失败，请检查绑定文件的写入权限。"
            ) from exc
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    logger.warning("清理临时账号绑定文件失败。")

    def _extract_data(self, payload: dict[str, Any], api_name: str) -> Any:
        """校验 API 响应并返回 data 字段。

        Args:
            payload: 鹰角或森空岛返回的 JSON 响应。
            api_name: 用于错误提示的接口名称。

        Returns:
            响应中的 data 数据。

        Raises:
            ValueError: 当接口返回错误状态时抛出。
        """
        if not isinstance(payload, dict):
            raise ValueError(f"{api_name}失败：接口响应格式异常")
        status = payload.get("status")
        code = payload.get("code")
        if status not in (None, 0):
            message = payload.get("msg") or payload.get("message") or "未知错误"
            raise ValueError(f"{api_name}失败：{message}")
        if code not in (None, 0):
            message = payload.get("message") or payload.get("msg") or "未知错误"
            raise ValueError(f"{api_name}失败：{message}")
        if "data" not in payload or payload["data"] is None:
            raise ValueError(f"{api_name}失败：接口未返回 data 数据")
        return payload["data"]

    async def _post_json(
        self,
        url: str,
        payload: dict[str, Any],
        api_name: str,
    ) -> Any:
        """向接口发送 JSON 请求并返回 data 数据。

        Args:
            url: API 接口地址。
            payload: JSON 请求体。
            api_name: 用于错误提示的接口名称。

        Returns:
            校验后的接口 data 数据。

        Raises:
            ValueError: 当请求失败或响应无效时抛出。
        """
        return await asyncio.to_thread(
            self._request_json,
            "POST",
            url,
            api_name,
            config.DEFAULT_HEADERS,
            payload,
            None,
        )

    async def _get_json(
        self,
        url: str,
        headers: dict[str, str],
        api_name: str,
        params: dict[str, str] | None = None,
    ) -> Any:
        """从接口获取 JSON 并返回 data 数据。

        Args:
            url: API 接口地址。
            headers: 包含森空岛凭据的请求头。
            api_name: 用于错误提示的接口名称。
            params: 可选查询参数。

        Returns:
            校验后的接口 data 数据。

        Raises:
            ValueError: 当请求失败或响应无效时抛出。
        """
        return await asyncio.to_thread(
            self._request_json,
            "GET",
            url,
            api_name,
            headers,
            None,
            params,
        )

    def _request_json(
        self,
        method: str,
        url: str,
        api_name: str,
        headers: dict[str, str],
        payload: dict[str, Any] | None,
        params: dict[str, str] | None,
    ) -> Any:
        """发送 HTTP 请求并返回校验后的 JSON 数据。

        Args:
            method: HTTP 请求方法。
            url: API 接口地址。
            api_name: 用于错误提示的接口名称。
            headers: 请求头。
            payload: 可选 JSON 请求体。
            params: 可选查询参数。

        Returns:
            校验后的接口 data 数据。

        Raises:
            ValueError: 当请求失败或响应 JSON 无效时抛出。
        """
        if params:
            url = f"{url}?{parse.urlencode(params)}"
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = request.Request(url, data=body, headers=headers, method=method)

        try:
            with request.urlopen(req, timeout=config.REQUEST_TIMEOUT) as response:
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            try:
                payload_data = json.loads(response_body)
            except json.JSONDecodeError as json_exc:
                raise ValueError(f"{api_name}失败：HTTP {exc.code}") from json_exc
            self._extract_data(payload_data, api_name)
            raise ValueError(f"{api_name}失败：HTTP {exc.code}") from exc
        except (OSError, TimeoutError) as exc:
            raise ValueError(f"{api_name}失败：网络请求异常：{exc}") from exc
        except UnicodeError as exc:
            raise ValueError(f"{api_name}失败：接口响应编码异常") from exc

        try:
            payload_data = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{api_name}失败：接口返回不是有效 JSON") from exc
        return self._extract_data(payload_data, api_name)

    async def _create_skland_credential(
        self,
        phone: str,
        password: str,
    ) -> dict[str, str]:
        """通过鹰角手机号和密码登录生成森空岛凭据。

        Args:
            phone: 鹰角账号手机号。
            password: 鹰角账号密码。

        Returns:
            包含森空岛凭据的字典。

        Raises:
            ValueError: 当登录或授权失败时抛出。
        """
        login_data = await self._post_json(
            config.TOKEN_URL,
            {
                "phone": phone,
                "password": password,
                "appCode": config.HYPERGRYPH_APP_CODE,
            },
            "鹰角账号登录",
        )
        account_token = (
            login_data.get("token") if isinstance(login_data, dict) else None
        )
        if not account_token:
            raise ValueError("鹰角账号登录失败：未返回登录 token")

        grant_data = await self._post_json(
            config.GRANT_URL,
            {
                "appCode": config.HYPERGRYPH_APP_CODE,
                "token": account_token,
                "type": 0,
            },
            "鹰角授权",
        )
        grant_code = grant_data.get("code") if isinstance(grant_data, dict) else None
        if not grant_code:
            raise ValueError("鹰角授权失败：未返回授权 code")

        cred_data = await self._post_json(
            config.CRED_URL,
            {"code": grant_code, "kind": 1},
            "森空岛凭据生成",
        )
        cred = cred_data.get("cred") if isinstance(cred_data, dict) else None
        skland_token = cred_data.get("token") if isinstance(cred_data, dict) else None
        if not cred or not skland_token:
            raise ValueError("森空岛凭据生成失败：未返回完整的 cred 和 token")
        return {"cred": cred, "token": skland_token}

    def _skland_headers(
        self,
        binding: dict[str, Any],
        url: str,
        params: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """根据已存储的绑定数据构造森空岛签名请求头。

        Args:
            binding: 已存储的账号绑定数据。
            url: API 接口地址。
            params: 可选查询参数。

        Returns:
            森空岛官方 API 签名请求头。

        Raises:
            ValueError: 当凭据缺少签名所需 token 时抛出。
        """
        cred = binding.get("cred")
        token = binding.get("token")
        if not cred or not token:
            raise ValueError("森空岛凭据不完整，请重新私聊绑定账号。")

        signed_url = url
        if params:
            signed_url = f"{url}?{parse.urlencode(params)}"
        parsed_url = parse.urlparse(signed_url)
        timestamp = int(datetime.now().timestamp()) - 1
        header_for_sign = {
            "platform": "",
            "timestamp": str(timestamp),
            "dId": "",
            "vName": "",
        }
        header_ca_str = json.dumps(header_for_sign, separators=(",", ":"))
        secret = f"{parsed_url.path}{parsed_url.query}{timestamp}{header_ca_str}"
        hex_secret = hmac.new(
            str(token).encode("utf-8"),
            secret.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        signature = hashlib.md5(hex_secret.encode("utf-8")).hexdigest()
        return {
            **config.SKLAND_SIGN_HEADERS,
            "cred": str(cred),
            "sign": signature,
            **header_for_sign,
        }

    def _find_value(self, data: Any, keys: tuple[str, ...]) -> Any:
        """在嵌套接口数据中查找第一个匹配字段值。

        Args:
            data: 森空岛返回的类 JSON 数据。
            keys: 候选字段名。

        Returns:
            第一个匹配到的值；未找到时返回 None。
        """
        if isinstance(data, dict):
            for key in keys:
                if key in data and data[key] not in (None, ""):
                    return data[key]
            for value in data.values():
                found = self._find_value(value, keys)
                if found not in (None, ""):
                    return found
        elif isinstance(data, list):
            for item in data:
                found = self._find_value(item, keys)
                if found not in (None, ""):
                    return found
        return None

    def _extract_avatar_url(self, value: Any) -> str:
        """从嵌套头像字段中提取头像 URL。

        Args:
            value: 头像相关 JSON 值。

        Returns:
            可用的头像 URL；未找到时返回空字符串。
        """
        if isinstance(value, str):
            return value if value.startswith(("http://", "https://")) else ""
        if isinstance(value, dict):
            for key in ("url", "uri", "avatarUrl", "imageUrl", "icon"):
                url = self._extract_avatar_url(value.get(key))
                if url:
                    return url
            for nested_value in value.values():
                url = self._extract_avatar_url(nested_value)
                if url:
                    return url
        if isinstance(value, list):
            for item in value:
                url = self._extract_avatar_url(item)
                if url:
                    return url
        return ""

    def _format_date(self, value: Any) -> str:
        """将森空岛时间戳类数据格式化为日期。

        Args:
            value: 时间戳、ISO 字符串或日期类值。

        Returns:
            可读的日期字符串。
        """
        if value in (None, ""):
            return "未返回"
        text = str(value)
        if isinstance(value, (int, float)) or text.isdigit():
            try:
                timestamp = float(value)
                if timestamp > 10_000_000_000:
                    timestamp /= 1000
                return datetime.fromtimestamp(timestamp, config.GAME_TIMEZONE).strftime(
                    "%Y-%m-%d"
                )
            except (OverflowError, OSError, ValueError):
                return "未返回"
        return text.split("T", 1)[0]

    async def _get_arknights_role(
        self,
        credential: dict[str, str],
    ) -> dict[str, Any]:
        """从森空岛获取第一个已绑定的明日方舟角色。

        Args:
            credential: 森空岛凭据。

        Returns:
            选中的明日方舟角色数据。

        Raises:
            ValueError: 当没有绑定明日方舟角色时抛出。
        """
        data = await self._get_json(
            config.BINDING_URL,
            self._skland_headers(credential, config.BINDING_URL),
            "森空岛角色绑定查询",
        )

        games = data.get("list", []) if isinstance(data, dict) else []
        games = games if isinstance(games, list) else []
        for game in games:
            if (
                not isinstance(game, dict)
                or game.get("appCode") != config.ARKNIGHTS_APP_CODE
            ):
                continue
            roles = game.get("bindingList", [])
            if isinstance(roles, list) and roles and isinstance(roles[0], dict):
                return roles[0]
        raise ValueError("森空岛角色绑定查询失败：未找到已绑定的明日方舟角色")

    async def _get_player_info(self, binding: dict[str, Any]) -> dict[str, Any]:
        """从森空岛获取明日方舟玩家信息。

        Args:
            binding: 已存储的账号绑定数据。

        Returns:
            森空岛玩家信息数据。

        Raises:
            ValueError: 当请求失败时抛出。
        """
        uid = str(binding.get("uid") or "")
        if not uid:
            raise ValueError("查询失败：未找到已绑定的明日方舟 UID")

        params = {"uid": uid, "appCode": config.ARKNIGHTS_APP_CODE}
        data = await self._get_json(
            config.PLAYER_URL,
            self._skland_headers(binding, config.PLAYER_URL, params),
            "森空岛基础信息查询",
            params,
        )
        if not isinstance(data, dict):
            raise ValueError("森空岛基础信息查询失败：接口数据格式异常")
        return data

    async def _get_skland_user_id(self, binding: dict[str, Any]) -> str:
        """从森空岛获取账号 userId。

        Args:
            binding: 已存储的账号绑定数据。

        Returns:
            森空岛账号 userId。

        Raises:
            ValueError: 当接口未返回 userId 时抛出。
        """
        data = await self._get_json(
            config.USER_ID_URL,
            self._skland_headers(binding, config.USER_ID_URL),
            "森空岛账号 ID 查询",
        )
        teenager = data.get("teenager") if isinstance(data, dict) else None
        user_id = teenager.get("userId") if isinstance(teenager, dict) else None
        if not user_id:
            raise ValueError("森空岛账号 ID 查询失败：未返回 userId")
        return str(user_id)

    async def _get_rogue_record(
        self,
        binding: dict[str, Any],
        topic_id: str,
    ) -> dict[str, Any]:
        """从森空岛获取肉鸽战绩数据。

        Args:
            binding: 已存储的账号绑定数据。
            topic_id: 肉鸽主题 ID。

        Returns:
            森空岛肉鸽战绩数据。

        Raises:
            ValueError: 当缺少 UID 或请求失败时抛出。
        """
        uid = str(binding.get("uid") or "")
        if not uid:
            raise ValueError("查询失败：未找到已绑定的明日方舟 UID")
        user_id = await self._get_skland_user_id(binding)
        params = {
            "uid": uid,
            "targetUserId": user_id,
            "topicId": topic_id,
        }
        data = await self._get_json(
            config.ROGUE_URL,
            self._skland_headers(binding, config.ROGUE_URL, params),
            "森空岛肉鸽战绩查询",
            params,
        )
        if not isinstance(data, dict):
            raise ValueError("森空岛肉鸽战绩查询失败：接口数据格式异常")
        return data

    def _format_rogue_record(
        self,
        topic_name: str,
        topic_id: str,
        rogue_data: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """Format rogue record data for text fallback and image rendering.

        Args:
            topic_name: User input topic name.
            topic_id: Rogue topic ID.
            rogue_data: Skland rogue API data.

        Returns:
            Text fallback and template data for rendering.

        Raises:
            ValueError: If the API returns a different rogue topic.
        """
        topics_raw = rogue_data.get("topics")
        topics_raw = topics_raw if isinstance(topics_raw, list) else []
        topics_raw = [item for item in topics_raw if isinstance(item, dict)]
        selected_topic = next(
            (item for item in topics_raw if item.get("id") == topic_id), {}
        )
        selected_ids = {item.get("id") for item in topics_raw if item.get("isSelected")}
        if (topics_raw and not selected_topic) or (
            selected_ids and topic_id not in selected_ids
        ):
            raise ValueError(
                f"森空岛未返回请求主题 {topic_id} 的战绩，请稍后重试或查询其他主题。"
            )

        history = rogue_data.get("history")
        history = history if isinstance(history, dict) else {}
        career = rogue_data.get("career")
        career = career if isinstance(career, dict) else {}
        all_data = rogue_data.get("all")
        all_data = all_data if isinstance(all_data, dict) else {}
        game_user_info = rogue_data.get("gameUserInfo")
        game_user_info = game_user_info if isinstance(game_user_info, dict) else {}

        clear_info = career.get("clearInfo")
        clear_info = clear_info if isinstance(clear_info, dict) else {}
        medal = history.get("medal")
        medal = medal if isinstance(medal, dict) else {}
        medal_current = medal.get("current")
        medal_count = medal.get("count")
        medal_text = "未返回"
        if medal_current not in (None, "") and medal_count not in (None, ""):
            medal_text = f"{medal_current}/{medal_count}"

        topic_display_name = selected_topic.get("name") or config.ROGUE_TOPIC_NAMES.get(
            topic_id, topic_name
        )
        hero_pic = selected_topic.get("pic") or selected_topic.get("titlePic") or ""
        mode = history.get("mode")
        if mode in (None, ""):
            mode = clear_info.get("difficulty")
        grade = history.get("modeGrade")
        if grade in (None, ""):
            grade = clear_info.get("grade")
        records_raw = history.get("records")
        records_raw = records_raw if isinstance(records_raw, list) else []
        records_raw = [record for record in records_raw if isinstance(record, dict)]

        def display(value: Any) -> str:
            """Format a metric while retaining zero values.

            Args:
                value: API metric value.

            Returns:
                Metric text or a placeholder for missing values.
            """
            if value in (None, ""):
                return "未返回"
            return str(value)

        hero_metrics = [
            {
                "name": "难度等级",
                "value": display(grade),
                "color": "#f3b563",
            },
            {
                "name": "本期积分",
                "value": display(history.get("score")),
                "color": "#d94d3f",
            },
            {
                "name": "里程碑",
                "value": display(history.get("bpLevel")),
                "color": "#5bbf8a",
            },
            {"name": "勋章收集", "value": medal_text, "color": "#8fb6ff"},
            {
                "name": "最近记录",
                "value": display(len(records_raw)),
                "color": "#d8d1c4",
            },
            {
                "name": "最高通关",
                "value": display(clear_info.get("difficulty")),
                "color": "#c78ad9",
            },
        ]

        topics = []
        for item in topics_raw:
            item_id = item.get("id") or ""
            topics.append(
                {
                    "id": item_id,
                    "name": item.get("name") or item_id or "未知主题",
                    "pic": item.get("pic") or item.get("titlePic") or "",
                    "selected": item_id == topic_id,
                }
            )

        records = []
        for record in records_raw[:5]:
            start_ts = record.get("startTs")
            end_ts = record.get("endTs")
            duration = "未知用时"
            try:
                start = float(start_ts)
                end = float(end_ts)
                if start > 10_000_000_000:
                    start /= 1000
                if end > 10_000_000_000:
                    end /= 1000
                seconds = max(0, int(end - start))
                hours = seconds // 3600
                minutes = seconds % 3600 // 60
                remain_seconds = seconds % 60
                duration = f"{hours:02d}:{minutes:02d}:{remain_seconds:02d}"
            except (TypeError, ValueError, OverflowError):
                pass

            band = record.get("band")
            band_name = band.get("name") if isinstance(band, dict) else ""
            last_chars = record.get("lastChars")
            last_chars = last_chars if isinstance(last_chars, list) else []
            char_names = []
            for char in last_chars[:6]:
                if not isinstance(char, dict):
                    continue
                char_name = char.get("name") or "未知干员"
                phase = char.get("evolvePhase")
                level = char.get("level")
                if phase in (None, "") or level in (None, ""):
                    char_names.append(char_name)
                else:
                    char_names.append(f"{char_name} 精{phase} Lv.{level}")
            try:
                battles = sum(
                    int(record.get(key) or 0)
                    for key in ("cntBattleNormal", "cntBattleElite", "cntBattleBoss")
                )
            except (TypeError, ValueError, OverflowError):
                battles = "未返回"
            records.append(
                {
                    "date": self._format_date(end_ts),
                    "band": band_name or "未知分队",
                    "stage": record.get("lastStage") or "未知节点",
                    "result": (
                        "已通关"
                        if record.get("success") in (True, 1, "1")
                        else "未通关"
                    ),
                    "grade": display(record.get("modeGrade")),
                    "score": display(record.get("score")),
                    "duration": duration,
                    "zones": display(record.get("cntCrossedZone")),
                    "nodes": display(record.get("cntArrivedNode")),
                    "battles": battles,
                    "relics": display(record.get("cntGainRelicItem")),
                    "recruits": display(record.get("cntRecruitUpgrade")),
                    "chars": " / ".join(char_names) or "未返回干员",
                }
            )

        chars = []
        chars_raw = history.get("chars")
        chars_raw = chars_raw if isinstance(chars_raw, list) else []
        for char in chars_raw[:8]:
            if not isinstance(char, dict):
                continue
            char_name = char.get("name") or "未知干员"
            phase = char.get("evolvePhase")
            level = char.get("level")
            if phase in (None, "") or level in (None, ""):
                chars.append(char_name)
            else:
                chars.append(f"{char_name} 精{phase} Lv.{level}")

        career_metrics = [
            {"name": "投资", "value": display(career.get("invest"))},
            {"name": "源石锭", "value": display(career.get("gold"))},
            {"name": "经过节点", "value": display(career.get("node"))},
            {"name": "消耗希望", "value": display(career.get("hope"))},
            {"name": "晋升次数", "value": display(career.get("upgrade"))},
            {"name": "收藏品", "value": display(career.get("relic"))},
            {"name": "远行次数", "value": display(career.get("travel"))},
            {"name": "累计步数", "value": display(career.get("step"))},
        ]
        if topic_id == "rogue_6":
            career_metrics = [
                {"name": label, "value": display(career.get(key))}
                for label, key in (
                    ("非林间空地节点", "node"),
                    ("消耗希望", "hope"),
                    ("晋升次数", "upgrade"),
                    ("先行一步次数", "expedition"),
                    ("培育种子次数", "scrapIdentify"),
                    ("消耗行动力", "moveCostAp"),
                    ("徒步跋涉次数", "moveWalk"),
                    ("加工品移动次数", "moveVehicle"),
                    ("迁走居民据点", "settleSavage"),
                    ("抵御流窜居民", "settleBandit"),
                    ("误入奇境次数", "teleportIn"),
                )
            ]
            for section, fields in (
                (
                    "scrap",
                    (("出售零件数", "recycle"), ("零件售卖收益", "profit")),
                ),
                (
                    "weather",
                    (("理想域节点数", "node"), ("消除实托邦次数", "negativeClear")),
                ),
            ):
                values = career.get(section)
                values = values if isinstance(values, dict) else {}
                career_metrics.extend(
                    {"name": label, "value": display(values.get(key))}
                    for label, key in fields
                )

        popular_items = []
        for label, key in (
            ("支援道具", "activeTool"),
            ("常用收藏", "relic"),
            ("灾厄年代", "disaster"),
        ):
            values = all_data.get(key)
            if not isinstance(values, list) or not values:
                continue
            names = [
                item.get("name")
                for item in values[:3]
                if isinstance(item, dict) and item.get("name")
            ]
            if names:
                popular_items.append(f"全服{label}: {'、'.join(names)}")
        if topic_id == "rogue_6":
            scrap = career.get("scrap")
            scrap = scrap if isinstance(scrap, dict) else {}
            weather = career.get("weather")
            weather = weather if isinstance(weather, dict) else {}
            for label, values in (
                ("个人常用加工品", scrap.get("top3Use")),
                ("个人常遇实托邦", weather.get("top3")),
            ):
                if isinstance(values, list):
                    names = [
                        str(item["name"])
                        for item in values[:3]
                        if isinstance(item, dict) and item.get("name")
                    ]
                    if names:
                        popular_items.append(f"{label}: {'、'.join(names)}")

        profession_names = {
            "CASTER": "术师",
            "MEDIC": "医疗",
            "PIONEER": "先锋",
            "SNIPER": "狙击",
            "SPECIAL": "特种",
            "SUPPORT": "辅助",
            "TANK": "重装",
            "WARRIOR": "近卫",
        }
        character_data = all_data.get("character")
        if isinstance(character_data, dict):
            for profession, value in character_data.items():
                if len(popular_items) >= 11:
                    break
                if not isinstance(value, dict):
                    continue
                char_list = value.get("list")
                if not isinstance(char_list, list) or not char_list:
                    continue
                char = char_list[0]
                if isinstance(char, dict) and char.get("name"):
                    profession_text = profession_names.get(profession, profession)
                    popular_items.append(f"全服{profession_text}: {char['name']}")

        endings = []
        ending_data = all_data.get("endings")
        if isinstance(ending_data, dict):
            for key in sorted(
                ending_data,
                key=lambda item: int(item) if item.isdigit() else 0,
            ):
                value = ending_data.get(key)
                try:
                    percent = float(value)
                except (TypeError, ValueError):
                    continue
                if not math.isfinite(percent):
                    continue
                endings.append(
                    {
                        "name": f"通关 {key} 个结局",
                        "value": f"{percent:g}",
                        "width": min(100, max(0, percent)),
                    }
                )

        card_data = {
            "topic_name": topic_display_name,
            "topic_id": topic_id,
            "hero_pic": hero_pic,
            "mode": display(mode),
            "player_name": game_user_info.get("name") or "未返回",
            "player_level": display(game_user_info.get("level")),
            "avatar_url": self._extract_avatar_url(game_user_info.get("avatar")),
            "medal_text": f"勋章 {medal_text}",
            "hero_metrics": hero_metrics,
            "topics": topics,
            "record_count": len(records_raw),
            "records": records,
            "career_metrics": career_metrics,
            "chars": chars,
            "popular_items": popular_items,
            "endings": endings,
        }

        lines = [
            f"明日方舟肉鸽战绩（{topic_display_name} / {topic_id}）",
            f"玩家：{card_data['player_name']} Lv.{card_data['player_level']}",
            f"难度：{display(mode)} {display(grade)}",
            f"积分：{display(history.get('score'))}",
            f"里程碑：{display(history.get('bpLevel'))}",
            f"勋章：{medal_text}",
            "生涯累计：",
            *(f"- {item['name']}：{item['value']}" for item in career_metrics),
        ]
        if records:
            lines.append("最近探索：")
            for record in records[:3]:
                lines.append(
                    f"- {record['date']} / {record['band']} / "
                    f"{record['stage']} / {record['result']} / "
                    f"难度 {record['grade']} / {record['score']} 分 / {record['duration']}"
                )
        else:
            lines.append("暂无最近探索记录，请确认该主题已有游玩记录并已同步至森空岛。")
        if popular_items:
            lines.extend(["偏好统计：", *popular_items])
        return "\n".join(lines), card_data

    def _format_player_info(
        self,
        binding: dict[str, Any],
        player_info: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """将森空岛玩家信息格式化为聊天输出。

        Args:
            binding: 已存储的账号绑定数据。
            player_info: 森空岛玩家信息数据。

        Returns:
            包含兜底文本输出和模板数据的元组。
        """
        status = player_info.get("status")
        status = status if isinstance(status, dict) else {}
        nickname = (
            self._find_value(status, ("nickName", "nickname", "name"))
            or binding.get("nickName")
            or self._find_value(player_info, ("nickName", "nickname", "name"))
            or "未返回"
        )
        level = self._find_value(status, ("level", "playerLevel"))
        if level in (None, ""):
            level = self._find_value(player_info, ("level", "playerLevel"))
        if level in (None, ""):
            level = "未返回"
        registered_at = self._format_date(
            self._find_value(
                player_info,
                ("registerTs", "registerTime", "registeredAt", "createTime"),
            )
        )
        mainline = (
            self._find_value(
                player_info,
                ("mainline", "mainLine", "mainStageProgress", "progress"),
            )
            or "未返回"
        )
        ap = status.get("ap") or self._find_value(player_info, ("ap",))
        recovery_time = "未返回"
        if isinstance(ap, dict):
            current_ap = ap.get("current")
            max_ap = ap.get("max")
            complete_recovery_time = ap.get("completeRecoveryTime")
            if complete_recovery_time not in (None, ""):
                try:
                    timestamp = float(complete_recovery_time)
                    if timestamp > 10_000_000_000:
                        timestamp /= 1000
                    if timestamp <= datetime.now().timestamp() or (
                        max_ap is not None
                        and current_ap is not None
                        and int(current_ap) >= int(max_ap)
                    ):
                        recovery_time = "已回满"
                    else:
                        recovery_time = datetime.fromtimestamp(
                            timestamp, config.GAME_TIMEZONE
                        ).strftime("%Y-%m-%d %H:%M")
                except (TypeError, ValueError, OverflowError, OSError):
                    pass
        char_count = self._find_value(status, ("charCnt", "charCount"))
        if char_count in (None, ""):
            char_count = self._find_value(player_info, ("charCnt", "charCount"))
        if char_count in (None, ""):
            char_count = "未返回"
        skin_count = self._find_value(status, ("skinCnt", "skinCount"))
        if skin_count in (None, ""):
            skin_count = self._find_value(player_info, ("skinCnt", "skinCount"))
        if skin_count in (None, ""):
            skin_count = "未返回"
        assist_chars = self._find_value(player_info, ("assistChars",))
        assist_chars = assist_chars if isinstance(assist_chars, list) else []
        char_info_map = self._find_value(player_info, ("charInfoMap",))
        char_info_map = char_info_map if isinstance(char_info_map, dict) else {}
        equipment_info_map = self._find_value(player_info, ("equipmentInfoMap",))
        equipment_info_map = (
            equipment_info_map if isinstance(equipment_info_map, dict) else {}
        )
        assist_data = []
        for index, assist in enumerate(assist_chars[:3], start=1):
            if not isinstance(assist, dict):
                continue
            char_id = str(assist.get("charId") or "")
            char_info = char_info_map.get(char_id, {})
            if not isinstance(char_info, dict):
                char_info = {}
            char_name = char_info.get("name") or char_id or "未返回"
            evolve_phase = assist.get("evolvePhase")
            if evolve_phase in (0, "0"):
                phase = "精零"
            elif evolve_phase in (1, "1"):
                phase = "精一"
            elif evolve_phase in (2, "2"):
                phase = "精二"
            else:
                phase = "精英化未知"
            level_text = f"{phase} Lv.{assist.get('level', '未知')}"
            potential = assist.get("potentialRank")
            potential_text = "潜能未知"
            if potential not in (None, ""):
                potential_text = f"潜能 {int(potential) + 1}"

            default_skill_id = assist.get("defaultSkillId")
            selected_skill = {}
            skills = assist.get("skills")
            if isinstance(skills, list):
                for skill in skills:
                    if isinstance(skill, dict) and skill.get("id") == default_skill_id:
                        selected_skill = skill
                        break
                if not selected_skill and skills and isinstance(skills[0], dict):
                    selected_skill = skills[0]
            specialize_level = selected_skill.get("specializeLevel")
            if specialize_level not in (None, "") and int(specialize_level) > 0:
                skill_text = f"技能专精 {specialize_level}"
            else:
                skill_text = f"技能等级 {assist.get('mainSkillLvl', '未知')}"

            equip_id = assist.get("defaultEquipId") or ""
            equip = assist.get("equip")
            if isinstance(equip, dict):
                equip_id = equip.get("id") or equip_id
            elif isinstance(equip, list):
                for item in equip:
                    if isinstance(item, dict) and item.get("id") == equip_id:
                        equip_id = item.get("id") or equip_id
                        break
            equip_info = equipment_info_map.get(equip_id, {})
            equip_text = "模组 无"
            if isinstance(equip_info, dict) and equip_id:
                equip_text = equip_info.get("typeName") or "模组 已装备"
            assist_data.append(
                {
                    "index": index,
                    "name": char_name,
                    "level": level_text,
                    "potential": potential_text,
                    "skill": skill_text,
                    "equip": equip_text,
                }
            )
        avatar_value = self._find_value(
            player_info,
            ("avatar", "avatarUrl", "avatarImage", "icon"),
        )
        avatar_url = self._extract_avatar_url(avatar_value)
        card_data = {
            "nickname": nickname,
            "uid": binding.get("uid", ""),
            "level": level,
            "registered_at": registered_at,
            "mainline": mainline,
            "recovery_time": recovery_time,
            "char_count": char_count,
            "skin_count": skin_count,
            "assist_chars": assist_data,
            "avatar_url": avatar_url,
            "channel_name": binding.get("channelName") or "未返回",
        }

        text = (
            "明日方舟基础信息\n"
            f"游戏昵称：{nickname}\n"
            f"玩家等级：{level}\n"
            f"注册日期：{registered_at}\n"
            f"主线进度：{mainline}\n"
            f"理智恢复时间：{recovery_time}\n"
            f"干员数：{char_count}\n"
            f"时装数：{skin_count}\n"
            "助战干员："
            f"{'、'.join(item['name'] for item in assist_data) or '未返回'}\n"
            f"头像：{avatar_url or '未返回'}"
        )
        return text, card_data

    @filter.command("绑定账号")
    async def bind_arknight_account(
        self,
        event: AstrMessageEvent,
        phone: str,
        password: str,
    ):
        """将发送者绑定到森空岛明日方舟账号。

        Args:
            event: AstrBot 消息事件。
            phone: 森空岛账号手机号。
            password: 森空岛账号密码。
        """
        user_id = event.get_sender_id()
        try:
            credential = await self._create_skland_credential(phone, password)
            role = await self._get_arknights_role(credential)
        except ValueError as exc:
            logger.warning(f"绑定明日方舟账号失败：{exc}")
            yield event.plain_result(str(exc))
            return

        uid = str(role.get("uid") or "")
        if not uid:
            yield event.plain_result("绑定失败：森空岛未返回明日方舟 UID")
            return

        try:
            data = self._read_bindings()
            data[user_id] = {
                "uid": uid,
                "nickName": role.get("nickName", ""),
                "channelName": role.get("channelName", ""),
                "cred": credential["cred"],
                "token": credential.get("token", ""),
                "updatedAt": datetime.now().isoformat(timespec="seconds"),
            }
            self._write_bindings(data)
        except ValueError as exc:
            logger.warning(f"保存明日方舟账号绑定失败：{exc}")
            yield event.plain_result(str(exc))
            return

        role_name = role.get("nickName") or uid
        channel_name = role.get("channelName", "未知渠道")
        yield event.plain_result(f"绑定成功：{role_name}（{channel_name}，UID：{uid}）")

    @filter.command("查询基础信息")
    async def check_arknight_information(self, event: AstrMessageEvent):
        """查询发送者的明日方舟基础玩家信息。

        Args:
            event: AstrBot 消息事件。
        """
        user_id = event.get_sender_id()
        try:
            data = self._read_bindings()
        except ValueError as exc:
            yield event.plain_result(str(exc))
            return
        binding = data.get(user_id)
        if not binding:
            yield event.plain_result(
                f"你还没有绑定账号，请先发送：\n{config.BIND_FORMAT}"
            )
            return
        if not isinstance(binding, dict):
            yield event.plain_result(
                "当前绑定数据是旧格式，"
                "无法调用森空岛官方 API 查询。"
                "请重新私聊发送：\n"
                f"{config.BIND_FORMAT}"
            )
            return

        yield event.plain_result("正在查询，请稍后...")
        try:
            player_info = await self._get_player_info(binding)
            text, card_data = self._format_player_info(binding, player_info)
        except ValueError as exc:
            logger.warning(f"查询明日方舟基础信息失败：{exc}")
            yield event.plain_result(str(exc))
            return

        try:
            image = await self.html_render(
                config.TMPL,
                card_data,
                return_url=True,
                options={
                    "full_page": True,
                    "type": "png",
                    "viewport": {"width": 1280, "height": 480},
                },
            )
        except Exception as exc:
            logger.warning(f"渲染明日方舟基础信息图片失败：{exc}")
            yield event.plain_result(f"图片渲染服务暂时不可用，先返回文字版：\n{text}")
            return

        yield event.image_result(image)

    @filter.command("查询肉鸽")
    async def check_rogue_record(
        self,
        event: AstrMessageEvent,
        topic: str = "默认",
    ):
        """查询发送者的明日方舟集成战略战绩。

        Args:
            event: AstrBot 消息事件。
            topic: 可选肉鸽主题名或原始 topicId。
        """
        user_id = event.get_sender_id()
        try:
            data = self._read_bindings()
        except ValueError as exc:
            yield event.plain_result(str(exc))
            return
        binding = data.get(user_id)
        if not binding:
            yield event.plain_result(
                f"你还没有绑定账号，请先发送：\n{config.BIND_FORMAT}"
            )
            return
        if not isinstance(binding, dict):
            yield event.plain_result(
                "当前绑定数据是旧格式，无法调用森空岛官方 API 查询。"
                "请重新发送：\n"
                f"{config.BIND_FORMAT}"
            )
            return

        topic_name = topic.strip() or "默认"
        topic_id = config.ROGUE_TOPICS.get(topic_name, topic_name)
        if not re.fullmatch(r"rogue_[1-9]\d*", topic_id):
            yield event.plain_result(
                f"未知肉鸽主题：{topic_name}\n{config.ROGUE_COMMAND_HELP}"
            )
            return
        yield event.plain_result("正在查询，请稍后...")
        try:
            rogue_data = await self._get_rogue_record(binding, topic_id)
            text, card_data = self._format_rogue_record(
                topic_name, topic_id, rogue_data
            )
        except ValueError as exc:
            logger.warning(f"查询明日方舟肉鸽战绩失败：{exc}")
            yield event.plain_result(str(exc))
            return

        try:
            image = await self.html_render(
                config.ROGUE_TMPL,
                card_data,
                return_url=True,
                options={
                    "full_page": True,
                    "type": "png",
                    "viewport": {"width": 1280, "height": 1100},
                },
            )
        except Exception as exc:
            logger.warning(f"渲染明日方舟肉鸽战绩图片失败：{exc}")
            yield event.plain_result(f"图片渲染服务暂时不可用，先返回文字版：\n{text}")
            return

        yield event.image_result(image)

    @filter.command("帮助")
    async def help(self, event: AstrMessageEvent):
        """发送明日方舟助手命令帮助。

        Args:
            event: AstrBot 消息事件。
        """
        yield event.plain_result(
            "明日方舟助手命令\n"
            f"{config.BIND_FORMAT}\n"
            "/查询基础信息\n"
            f"{config.ROGUE_COMMAND_HELP}\n"
            "肉鸽默认查询沉沦者的黑流树海，也可使用完整主题名或 rogue_6。\n"
            "/帮助\n"
            "绑定会使用森空岛账号登录，只保存查询所需凭据和角色 UID。"
        )

    async def terminate(self):
        """在 AstrBot 卸载插件前清理插件资源。"""
