from __future__ import annotations

import importlib.util
import io
import logging
import sys
import tempfile
import types
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

PLUGIN_DIR = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "arknight_test_plugin"
package = types.ModuleType(PACKAGE_NAME)
package.__path__ = [str(PLUGIN_DIR)]
framework = {
    name: types.ModuleType(name)
    for name in ("astrbot", "astrbot.api", "astrbot.api.event", "astrbot.api.star")
}
framework["astrbot.api"].logger = logging.getLogger("arknight_tests")
framework["astrbot.api.event"].AstrMessageEvent = object
framework["astrbot.api.event"].filter = types.SimpleNamespace(
    command=lambda name: lambda method: method
)
framework["astrbot.api.star"].Context = object
framework["astrbot.api.star"].Star = type(
    "Star", (), {"__init__": lambda self, context: None}
)
framework["astrbot.api.star"].register = lambda *args: lambda cls: cls
spec = importlib.util.spec_from_file_location(
    f"{PACKAGE_NAME}.main", PLUGIN_DIR / "main.py"
)
main = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {PACKAGE_NAME: package, **framework}):
    spec.loader.exec_module(main)
config = main.config


class PluginTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.plugin = main.MyPlugin(None)
        self.binding = {"uid": "123", "cred": "test-cred", "token": "test-token"}
        self.event = Mock()
        self.event.get_sender_id.return_value = "sender"
        self.event.plain_result.side_effect = lambda text: text
        self.event.image_result.side_effect = lambda image: ("image", image)
        self.rogue = {
            "topics": [
                {"id": "rogue_5", "name": "岁的界园志异", "isSelected": False},
                {
                    "id": "rogue_6",
                    "name": "沉沦者的黑流树海",
                    "pic": "https://example.com/rogue6.png",
                    "isSelected": True,
                },
            ],
            "history": {
                "mode": "常规行动",
                "modeGrade": 0,
                "score": 0,
                "bpLevel": 0,
                "medal": {"current": 0, "count": 10},
                "records": [
                    {
                        "startTs": 1784289600,
                        "endTs": 1784293261,
                        "success": True,
                        "band": {"name": "研究分队"},
                        "lastStage": "测试节点",
                        "modeGrade": 0,
                        "score": 100,
                        "cntBattleNormal": "4",
                        "cntBattleElite": 2,
                        "cntBattleBoss": 1,
                        "lastChars": [{"name": "阿米娅", "evolvePhase": 0, "level": 1}],
                    }
                ],
            },
            "career": {
                "clearInfo": {"difficulty": "常规行动", "grade": 8},
                "node": 0,
                "hope": 50,
                "upgrade": 2,
                "expedition": 3,
                "scrapIdentify": 4,
                "moveCostAp": 123,
                "moveWalk": 10,
                "moveVehicle": 5,
                "settleSavage": 4,
                "settleBandit": 2,
                "teleportIn": 1,
                "scrap": {
                    "recycle": 6,
                    "profit": 30,
                    "top3Use": [{"name": "测试加工品"}],
                },
                "weather": {"node": 7, "negativeClear": 8},
            },
            "gameUserInfo": {"name": "博士", "level": 120},
            "all": {
                "endings": {"1": 75.5, "2": 24.5},
                "relic": [{"name": "测试收藏品"}],
            },
        }

    def test_new_theme_aliases_and_full_names(self):
        for alias in ("黑流树海", "黑流", "树海", "沉沦者", "沉沦者的黑流树海", "默认"):
            with self.subTest(alias=alias):
                self.assertEqual(config.ROGUE_TOPICS[alias], "rogue_6")
        for topic_id, name in config.ROGUE_TOPIC_NAMES.items():
            self.assertEqual(config.ROGUE_TOPICS[name], topic_id)
        self.assertEqual(config.ROGUE_TOPICS["萨卡兹"], "rogue_4")

    def test_new_career_metrics_and_text_fallback(self):
        text, card = self.plugin._format_rogue_record("黑流", "rogue_6", self.rogue)
        metrics = {item["name"]: item["value"] for item in card["career_metrics"]}
        self.assertEqual(metrics["消耗行动力"], "123")
        self.assertEqual(metrics["非林间空地节点"], "0")
        self.assertEqual(metrics["加工品移动次数"], "5")
        self.assertEqual(metrics["先行一步次数"], "3")
        self.assertEqual(metrics["培育种子次数"], "4")
        self.assertEqual(metrics["出售零件数"], "6")
        self.assertEqual(metrics["零件售卖收益"], "30")
        self.assertEqual(metrics["消除实托邦次数"], "8")
        self.assertIn("消耗行动力：123", text)
        self.assertIn("个人常用加工品: 测试加工品", text)
        self.assertIn("全服常用收藏: 测试收藏品", text)

    def test_zero_difficulty_is_preserved(self):
        text, card = self.plugin._format_rogue_record("黑流", "rogue_6", self.rogue)
        self.assertEqual(card["hero_metrics"][0]["value"], "0")
        self.assertEqual(card["hero_metrics"][1]["value"], "0")
        self.assertEqual(card["medal_text"], "勋章 0/10")
        self.assertIn("难度：常规行动 0", text)

    def test_all_old_themes_keep_career_metrics(self):
        for topic_id in config.ROGUE_TOPIC_NAMES:
            if topic_id == "rogue_6":
                continue
            with self.subTest(topic_id=topic_id):
                data = deepcopy(self.rogue)
                data["topics"] = [{"id": topic_id, "isSelected": True}]
                data["career"].update(invest=0, gold=5, travel=10, step=11)
                _, card = self.plugin._format_rogue_record(topic_id, topic_id, data)
                metrics = {
                    item["name"]: item["value"] for item in card["career_metrics"]
                }
                self.assertEqual(metrics["投资"], "0")
                self.assertEqual(metrics["累计步数"], "11")
                self.assertNotIn("消耗行动力", metrics)
                self.assertEqual(card["topic_name"], config.ROGUE_TOPIC_NAMES[topic_id])

    def test_only_requested_theme_is_highlighted(self):
        data = deepcopy(self.rogue)
        data["topics"][0]["isSelected"] = True
        _, card = self.plugin._format_rogue_record("黑流", "rogue_6", data)
        self.assertEqual([item["selected"] for item in card["topics"]], [False, True])
        self.assertEqual(card["hero_pic"], "https://example.com/rogue6.png")

    def test_api_selected_theme_mismatch_is_rejected(self):
        data = deepcopy(self.rogue)
        data["topics"][0]["isSelected"] = True
        data["topics"][1]["isSelected"] = False
        with self.assertRaisesRegex(ValueError, "未返回请求主题 rogue_6"):
            self.plugin._format_rogue_record("黑流", "rogue_6", data)

    def test_missing_requested_theme_is_rejected(self):
        data = deepcopy(self.rogue)
        data["topics"] = data["topics"][:1]
        with self.assertRaises(ValueError):
            self.plugin._format_rogue_record("黑流", "rogue_6", data)

    def test_empty_records_do_not_dump_raw_data(self):
        data = deepcopy(self.rogue)
        data["history"]["records"] = []
        data["privateField"] = "must-not-be-displayed"
        text, card = self.plugin._format_rogue_record("黑流", "rogue_6", data)
        self.assertIn("暂无最近探索记录", text)
        self.assertNotIn("must-not-be-displayed", text)
        self.assertEqual(card["record_count"], 0)

    def test_duration_accepts_seconds_and_milliseconds(self):
        for multiplier in (1, 1000):
            with self.subTest(multiplier=multiplier):
                data = deepcopy(self.rogue)
                record = data["history"]["records"][0]
                record["startTs"] *= multiplier
                record["endTs"] *= multiplier
                _, card = self.plugin._format_rogue_record("黑流", "rogue_6", data)
                self.assertEqual(card["records"][0]["duration"], "01:01:01")
                self.assertEqual(card["records"][0]["battles"], 7)

    def test_malformed_optional_rogue_fields_do_not_crash(self):
        data = deepcopy(self.rogue)
        data["history"]["records"].insert(0, None)
        record = data["history"]["records"][1]
        record.update(startTs="bad", endTs=10**30, cntBattleNormal="bad")
        data["history"]["chars"] = {"invalid": True}
        data["career"].update(scrap=[], weather=None)
        data["all"]["endings"].update({"3": "nan", "4": "inf", "5": "bad"})
        _, card = self.plugin._format_rogue_record("黑流", "rogue_6", data)
        self.assertEqual(card["record_count"], 1)
        self.assertEqual(card["records"][0]["duration"], "未知用时")
        self.assertEqual(card["records"][0]["date"], "未返回")
        self.assertEqual(card["records"][0]["battles"], "未返回")
        self.assertEqual(len(card["endings"]), 2)

    def test_dates_use_china_timezone(self):
        for timestamp in (1609434000, 1609434000000, "1609434000"):
            self.assertEqual(self.plugin._format_date(timestamp), "2021-01-01")

    def test_player_zero_counts_and_status_level(self):
        text, card = self.plugin._format_player_info(
            self.binding,
            {
                "chars": [{"name": "干员", "level": 90}],
                "status": {"name": "博士", "level": 0, "charCnt": 0, "skinCnt": 0},
            },
        )
        self.assertEqual(card["nickname"], "博士")
        self.assertEqual(card["level"], 0)
        self.assertEqual(card["char_count"], 0)
        self.assertEqual(card["skin_count"], 0)
        self.assertIn("时装数：0", text)

    def test_invalid_ap_timestamp_does_not_crash(self):
        _, card = self.plugin._format_player_info(
            self.binding, {"status": {"ap": {"completeRecoveryTime": "invalid"}}}
        )
        self.assertEqual(card["recovery_time"], "未返回")

    def test_api_non_object_or_missing_data_is_rejected(self):
        for payload in ([], None, {"code": 0}, {"code": 0, "data": None}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.plugin._extract_data(payload, "测试")
        self.assertEqual(self.plugin._extract_data({"code": 0, "data": {}}, "测试"), {})

    def test_http_error_cannot_be_reported_as_success(self):
        exc = HTTPError(
            config.ROGUE_URL, 500, "Error", {}, io.BytesIO(b'{"code":0,"data":{}}')
        )
        with patch.object(main.request, "urlopen", side_effect=exc):
            with self.assertRaisesRegex(ValueError, "HTTP 500"):
                self.plugin._request_json(
                    "GET", config.ROGUE_URL, "测试", {}, None, None
                )

    def test_http_business_error_is_preserved(self):
        exc = HTTPError(
            config.ROGUE_URL,
            401,
            "Unauthorized",
            {},
            io.BytesIO(b'{"code":10001,"message":"expired"}'),
        )
        with patch.object(main.request, "urlopen", side_effect=exc):
            with self.assertRaisesRegex(ValueError, "expired"):
                self.plugin._request_json(
                    "GET", config.ROGUE_URL, "测试", {}, None, None
                )

    def test_query_parameters_reach_http_request(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b'{"code":0,"data":{}}'
        with patch.object(main.request, "urlopen", return_value=response) as fetch:
            self.plugin._request_json(
                "GET",
                config.ROGUE_URL,
                "测试",
                {},
                None,
                {"uid": "123", "targetUserId": "456", "topicId": "rogue_6"},
            )
        url = fetch.call_args.args[0].full_url
        self.assertEqual(parse_qs(urlparse(url).query)["topicId"], ["rogue_6"])

    def test_incomplete_credentials_require_rebinding(self):
        for binding in ({"cred": "cred"}, {"token": "token"}):
            with (
                self.subTest(binding=binding),
                self.assertRaisesRegex(ValueError, "重新"),
            ):
                self.plugin._skland_headers(binding, config.ROGUE_URL)

    def test_empty_and_corrupt_binding_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bindings.json"
            with patch.object(config, "arknight_name_file", path):
                self.assertEqual(self.plugin._read_bindings(), {})
                path.write_text("", encoding="utf-8")
                self.assertEqual(self.plugin._read_bindings(), {})
                for contents in ("{broken", "[]"):
                    path.write_text(contents, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        self.plugin._read_bindings()
                    self.assertEqual(path.read_text(encoding="utf-8"), contents)

    def test_atomic_binding_write_preserves_original_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bindings.json"
            original = '{"old": {"uid": "1"}}'
            path.write_text(original, encoding="utf-8")
            with patch.object(config, "arknight_name_file", path):
                with patch.object(Path, "replace", side_effect=OSError("failed")):
                    with self.assertRaises(ValueError):
                        self.plugin._write_bindings({"new": self.binding})
                self.assertEqual(path.read_text(encoding="utf-8"), original)
                self.assertEqual(list(Path(directory).iterdir()), [path])
                self.plugin._write_bindings({"new": self.binding})
                self.assertEqual(self.plugin._read_bindings(), {"new": self.binding})

    async def test_default_query_returns_new_theme_image(self):
        self.plugin._read_bindings = Mock(return_value={"sender": self.binding})
        self.plugin._get_rogue_record = AsyncMock(return_value=self.rogue)
        self.plugin.html_render = AsyncMock(return_value="image-url")
        messages = [item async for item in self.plugin.check_rogue_record(self.event)]
        self.plugin._get_rogue_record.assert_awaited_once_with(self.binding, "rogue_6")
        self.assertEqual(messages[-1], ("image", "image-url"))

    async def test_query_aliases_and_raw_topic_ids(self):
        self.plugin._read_bindings = Mock(return_value={"sender": self.binding})
        self.plugin.html_render = AsyncMock(return_value="image-url")
        for topic, topic_id in (
            ("黑流树海", "rogue_6"),
            (" 沉沦者的黑流树海 ", "rogue_6"),
            ("rogue_6", "rogue_6"),
            ("萨米", "rogue_3"),
            ("rogue_7", "rogue_7"),
        ):
            with self.subTest(topic=topic):
                self.plugin._get_rogue_record = AsyncMock(return_value={})
                messages = [
                    item
                    async for item in self.plugin.check_rogue_record(self.event, topic)
                ]
                self.plugin._get_rogue_record.assert_awaited_once_with(
                    self.binding, topic_id
                )
                self.assertEqual(messages[-1], ("image", "image-url"))

    async def test_unknown_topic_does_not_call_api(self):
        self.plugin._read_bindings = Mock(return_value={"sender": self.binding})
        self.plugin._get_rogue_record = AsyncMock()
        messages = [
            item
            async for item in self.plugin.check_rogue_record(self.event, "错误主题")
        ]
        self.assertIn("未知肉鸽主题", messages[-1])
        self.plugin._get_rogue_record.assert_not_awaited()

    async def test_image_failure_returns_new_theme_text(self):
        self.plugin._read_bindings = Mock(return_value={"sender": self.binding})
        self.plugin._get_rogue_record = AsyncMock(return_value=self.rogue)
        self.plugin.html_render = AsyncMock(side_effect=RuntimeError("unavailable"))
        messages = [item async for item in self.plugin.check_rogue_record(self.event)]
        self.assertIn("图片渲染服务暂时不可用", messages[-1])
        self.assertIn("消耗行动力：123", messages[-1])

    async def test_mismatched_theme_returns_friendly_error(self):
        data = deepcopy(self.rogue)
        data["topics"] = data["topics"][:1]
        self.plugin._read_bindings = Mock(return_value={"sender": self.binding})
        self.plugin._get_rogue_record = AsyncMock(return_value=data)
        self.plugin.html_render = AsyncMock()
        messages = [item async for item in self.plugin.check_rogue_record(self.event)]
        self.assertIn("未返回请求主题 rogue_6", messages[-1])
        self.plugin.html_render.assert_not_awaited()

    async def test_binding_read_failures_return_friendly_errors(self):
        self.plugin._read_bindings = Mock(side_effect=ValueError("绑定文件损坏"))
        for command in (
            self.plugin.check_rogue_record,
            self.plugin.check_arknight_information,
        ):
            messages = [item async for item in command(self.event)]
            self.assertEqual(messages, ["绑定文件损坏"])

    async def test_non_object_bindings_require_rebinding(self):
        for binding in ("old-uid", ["invalid"]):
            self.plugin._read_bindings = Mock(return_value={"sender": binding})
            messages = [
                item async for item in self.plugin.check_rogue_record(self.event)
            ]
            self.assertIn("旧格式", messages[-1])

    async def test_rogue_request_uses_new_id_and_signed_headers(self):
        self.plugin._get_skland_user_id = AsyncMock(return_value="456")
        self.plugin._get_json = AsyncMock(return_value=self.rogue)
        result = await self.plugin._get_rogue_record(self.binding, "rogue_6")
        self.assertIs(result, self.rogue)
        url, headers, _, params = self.plugin._get_json.call_args.args
        self.assertEqual(url, config.ROGUE_URL)
        self.assertEqual(
            params, {"uid": "123", "targetUserId": "456", "topicId": "rogue_6"}
        )
        self.assertEqual(headers["cred"], "test-cred")
        self.assertEqual(len(headers["sign"]), 32)
        self.assertTrue(headers["timestamp"].isdigit())

    async def test_missing_uid_does_not_call_user_id_api(self):
        self.plugin._get_skland_user_id = AsyncMock()
        for uid in (None, ""):
            with self.assertRaisesRegex(ValueError, "UID"):
                await self.plugin._get_rogue_record(
                    {**self.binding, "uid": uid}, "rogue_6"
                )
        self.plugin._get_skland_user_id.assert_not_awaited()

    async def test_help_documents_new_default(self):
        messages = [item async for item in self.plugin.help(self.event)]
        self.assertIn("黑流树海", messages[0])
        self.assertIn("rogue_6", messages[0])

    def test_templates_render_with_strict_variables(self):
        try:
            from jinja2 import Environment, StrictUndefined
        except ImportError:
            self.skipTest("Install Jinja2 to validate HTML templates")
        environment = Environment(undefined=StrictUndefined, autoescape=True)
        _, rogue_card = self.plugin._format_rogue_record("黑流", "rogue_6", self.rogue)
        html = environment.from_string(config.ROGUE_TMPL).render(rogue_card)
        self.assertIn("沉沦者的黑流树海", html)
        self.assertIn("消耗行动力", html)
        self.assertEqual(html.count('class="topic selected"'), 1)
        _, player_card = self.plugin._format_player_info(self.binding, {})
        html = environment.from_string(config.TMPL).render(player_card)
        self.assertIn("明日方舟基础信息", html)


if __name__ == "__main__":
    unittest.main()
