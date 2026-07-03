from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from datetime import datetime
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
    "1.0.0",
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
        """
        if not config.arknight_name_file.exists():
            return {}
        try:
            with config.arknight_name_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            logger.warning("明日方舟绑定 JSON 无效，将使用空数据。")
            return {}
        if isinstance(data, dict):
            return data
        return {}

    def _write_bindings(self, data: dict[str, Any]) -> None:
        """将账号绑定数据写入插件 JSON 文件。

        Args:
            data: AstrBot 发送者 ID 到森空岛绑定数据的映射。
        """
        with config.arknight_name_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

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
        status = payload.get("status")
        code = payload.get("code")
        if status not in (None, 0):
            message = payload.get("msg") or payload.get("message") or "未知错误"
            raise ValueError(f"{api_name}失败：{message}")
        if code not in (None, 0):
            message = payload.get("message") or payload.get("msg") or "未知错误"
            raise ValueError(f"{api_name}失败：{message}")
        return payload.get("data", payload)

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
            return self._extract_data(payload_data, api_name)
        except (OSError, TimeoutError) as exc:
            raise ValueError(f"{api_name}失败：网络请求异常：{exc}") from exc

        try:
            payload_data = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"{api_name}失败：接口返回不是有效 JSON"
            ) from exc
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
        account_token = login_data.get("token")
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
        grant_code = grant_data.get("code")
        if not grant_code:
            raise ValueError("鹰角授权失败：未返回授权 code")

        cred_data = await self._post_json(
            config.CRED_URL,
            {"code": grant_code, "kind": 1},
            "森空岛凭据生成",
        )
        cred = cred_data.get("cred")
        skland_token = cred_data.get("token", "")
        if not cred:
            raise ValueError("森空岛凭据生成失败：未返回 cred")
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
        cred = str(binding.get("cred", ""))
        token = binding.get("token")
        if not token:
            raise ValueError("森空岛请求签名失败：缺少 token")

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
        secret = (
            f"{parsed_url.path}{parsed_url.query}"
            f"{timestamp}{header_ca_str}"
        )
        hex_secret = hmac.new(
            str(token).encode("utf-8"),
            secret.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        signature = hashlib.md5(hex_secret.encode("utf-8")).hexdigest()
        return {
            **config.SKLAND_SIGN_HEADERS,
            "cred": cred,
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
        if isinstance(value, (int, float)):
            timestamp = value / 1000 if value > 10_000_000_000 else value
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
        text = str(value)
        if text.isdigit():
            timestamp = int(text)
            timestamp = timestamp / 1000 if timestamp > 10_000_000_000 else timestamp
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
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
        for game in games:
            if game.get("appCode") != config.ARKNIGHTS_APP_CODE:
                continue
            roles = game.get("bindingList", [])
            if roles:
                return roles[0]
        raise ValueError(
            "森空岛角色绑定查询失败："
            "未找到已绑定的明日方舟角色"
        )

    async def _get_player_info(self, binding: dict[str, Any]) -> dict[str, Any]:
        """从森空岛获取明日方舟玩家信息。

        Args:
            binding: 已存储的账号绑定数据。

        Returns:
            森空岛玩家信息数据。

        Raises:
            ValueError: 当请求失败时抛出。
        """
        uid = str(binding.get("uid", ""))
        if not uid:
            raise ValueError("查询失败：未找到已绑定的明日方舟 UID")

        params = {"uid": uid, "appCode": config.ARKNIGHTS_APP_CODE}
        data = await self._get_json(
            config.PLAYER_URL,
            self._skland_headers(binding, config.PLAYER_URL, params),
            "森空岛基础信息查询",
            params,
        )
        return data if isinstance(data, dict) else {"raw": data}

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
        nickname = (
            self._find_value(player_info, ("nickName", "nickname", "name"))
            or binding.get("nickName")
            or "未返回"
        )
        level = self._find_value(player_info, ("level", "playerLevel")) or "未返回"
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
            "avatar_url": avatar_url,
            "channel_name": binding.get("channelName") or "未返回",
        }

        text = (
            "明日方舟基础信息\n"
            f"游戏昵称：{nickname}\n"
            f"玩家等级：{level}\n"
            f"注册日期：{registered_at}\n"
            f"主线进度：{mainline}\n"
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

        uid = str(role.get("uid", ""))
        if not uid:
            yield event.plain_result(
                "绑定失败：森空岛未返回明日方舟 UID"
            )
            return

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

        role_name = role.get("nickName") or uid
        channel_name = role.get("channelName", "未知渠道")
        yield event.plain_result(
            f"绑定成功：{role_name}（{channel_name}，UID：{uid}）"
        )

    @filter.command("查询基础信息")
    async def check_arknight_information(self, event: AstrMessageEvent):
        """查询发送者的明日方舟基础玩家信息。

        Args:
            event: AstrBot 消息事件。
        """
        user_id = event.get_sender_id()
        data = self._read_bindings()
        binding = data.get(user_id)
        if not binding:
            yield event.plain_result(
                "你还没有绑定账号，请先私聊发送：\n"
                f"{config.BIND_FORMAT}"
            )
            return
        if isinstance(binding, str):
            yield event.plain_result(
                "当前绑定数据是旧格式，"
                "无法调用森空岛官方 API 查询。"
                "请重新私聊发送：\n"
                f"{config.BIND_FORMAT}"
            )
            return

        try:
            player_info = await self._get_player_info(binding)
        except ValueError as exc:
            logger.warning(f"查询明日方舟基础信息失败：{exc}")
            yield event.plain_result(str(exc))
            return

        text, card_data = self._format_player_info(binding, player_info)
        try:
            image = await self.html_render(
                config.TMPL,
                card_data,
                return_url=True,
                options={
                    "full_page": True,
                    "type": "png",
                    "viewport": {"width": 1280, "height": 720},
                },
            )
        except Exception as exc:
            logger.warning(f"渲染明日方舟基础信息图片失败：{exc}")
            yield event.plain_result(
                f"抱歉，查询失败，请稍后重试"
            )

        yield event.image_result(image)

    async def terminate(self):
        """在 AstrBot 卸载插件前清理插件资源。"""
