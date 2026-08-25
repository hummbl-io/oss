"""Tests for AgentHub Bridge -- bidirectional sync with Karpathy's AgentHub.

All HTTP calls are mocked. No network access required.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from hummbl_cognition.agenthub_bridge import (
    AgentHubClient,
    AgentHubError,
    AgentHubPost,
    BusMessage,
    SyncState,
    append_bus_message,
    bus_message_to_post_content,
    load_sync_state,
    main,
    post_to_bus_message,
    pull_from_agenthub,
    push_to_agenthub,
    read_bus_lines,
    save_sync_state,
    sync,
)


class TestBusMessage(unittest.TestCase):
    """Test BusMessage data model and serialization."""

    def test_to_tsv_line(self):
        msg = BusMessage(
            timestamp="2026-03-16T10:00:00Z",
            sender="claude-code",
            recipient="all",
            msg_type="STATUS",
            message="bridge test",
        )
        line = msg.to_tsv_line()
        self.assertEqual(
            line,
            "2026-03-16T10:00:00Z\tclaude-code\tall\tSTATUS\tbridge test",
        )

    def test_from_tsv_line(self):
        line = "2026-03-16T10:00:00Z\tclaude-code\tall\tSTATUS\tbridge test"
        msg = BusMessage.from_tsv_line(line)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.timestamp, "2026-03-16T10:00:00Z")
        self.assertEqual(msg.sender, "claude-code")
        self.assertEqual(msg.recipient, "all")
        self.assertEqual(msg.msg_type, "STATUS")
        self.assertEqual(msg.message, "bridge test")

    def test_from_tsv_line_with_tabs_in_message(self):
        # TSV columns are tab-separated. The 5th column is the escaped message.
        # Original code joined parts[4:], new code uses parts[4] + unescape.
        line = "ts\tsender\trecipient\tSTATUS\tpart1 part2"
        msg = BusMessage.from_tsv_line(line)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.message, "part1 part2")

    def test_from_tsv_line_too_short(self):
        line = "2026-03-16T10:00:00Z\tclaude\tall"
        msg = BusMessage.from_tsv_line(line)
        self.assertIsNone(msg)

    def test_to_tsv_escapes_tabs_and_newlines(self):
        msg = BusMessage(
            timestamp="2026-03-16T10:00:00Z",
            sender="claude",
            recipient="all",
            msg_type="STATUS",
            message="line1\nline2\ttab",
        )
        line = msg.to_tsv_line()
        self.assertNotIn("\n", line)
        # Tabs in message are replaced with spaces by escape_message
        self.assertIn("line1\\nline2 tab", line)
        parts = line.split("\t")
        self.assertEqual(len(parts), 5)

    def test_to_agenthub_content(self):
        msg = BusMessage(
            timestamp="2026-03-16T10:00:00Z",
            sender="claude-code",
            recipient="codex",
            msg_type="PROPOSAL",
            message="add agenthub bridge",
        )
        content = msg.to_agenthub_content()
        self.assertIn("[BUS:PROPOSAL]", content)
        self.assertIn("from=claude-code", content)
        self.assertIn("to=codex", content)
        self.assertIn("ts=2026-03-16T10:00:00Z", content)
        self.assertIn("add agenthub bridge", content)

    def test_roundtrip_tsv(self):
        original = BusMessage(
            timestamp="2026-03-16T10:00:00Z",
            sender="agent-x",
            recipient="all",
            msg_type="MILESTONE",
            message="shipped v1.0",
        )
        line = original.to_tsv_line()
        parsed = BusMessage.from_tsv_line(line)
        self.assertEqual(parsed.timestamp, original.timestamp)
        self.assertEqual(parsed.sender, original.sender)
        self.assertEqual(parsed.recipient, original.recipient)
        self.assertEqual(parsed.msg_type, original.msg_type)
        self.assertEqual(parsed.message, original.message)


class TestAgentHubPost(unittest.TestCase):
    """Test AgentHubPost data model."""

    def test_from_dict(self):
        data = {
            "id": 42,
            "channel_id": 1,
            "agent_id": "research-bot",
            "content": "found something interesting",
            "created_at": "2026-03-16T10:00:00",
            "parent_id": None,
        }
        post = AgentHubPost.from_dict(data)
        self.assertEqual(post.id, 42)
        self.assertEqual(post.agent_id, "research-bot")
        self.assertEqual(post.content, "found something interesting")
        self.assertIsNone(post.parent_id)

    def test_from_dict_with_parent(self):
        data = {
            "id": 43,
            "channel_id": 1,
            "agent_id": "reply-bot",
            "content": "I agree",
            "created_at": "2026-03-16T10:01:00",
            "parent_id": 42,
        }
        post = AgentHubPost.from_dict(data)
        self.assertEqual(post.parent_id, 42)

    def test_from_dict_missing_fields(self):
        data = {"id": 1}
        post = AgentHubPost.from_dict(data)
        self.assertEqual(post.id, 1)
        self.assertEqual(post.agent_id, "unknown")
        self.assertEqual(post.content, "")


class TestSyncState(unittest.TestCase):
    """Test SyncState persistence."""

    def test_roundtrip(self):
        state = SyncState(
            last_pulled_post_id=100,
            last_pushed_bus_line=50,
            pushed_post_ids=[10, 20, 30],
            channel="general",
        )
        d = state.to_dict()
        restored = SyncState.from_dict(d)
        self.assertEqual(restored.last_pulled_post_id, 100)
        self.assertEqual(restored.last_pushed_bus_line, 50)
        self.assertEqual(restored.pushed_post_ids, [10, 20, 30])
        self.assertEqual(restored.channel, "general")

    def test_from_dict_defaults(self):
        state = SyncState.from_dict({})
        self.assertEqual(state.last_pulled_post_id, 0)
        self.assertEqual(state.last_pushed_bus_line, 0)
        self.assertEqual(state.pushed_post_ids, [])
        self.assertEqual(state.channel, "")

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.json"
            state = SyncState(last_pulled_post_id=42, channel="test")
            save_sync_state(state, path)

            loaded = load_sync_state(path)
            self.assertEqual(loaded.last_pulled_post_id, 42)
            self.assertEqual(loaded.channel, "test")

    def test_load_missing_file(self):
        state = load_sync_state(Path("/nonexistent/state.json"))
        self.assertEqual(state.last_pulled_post_id, 0)

    def test_load_corrupt_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("not json{{{")
            f.flush()
            name = f.name
        state = load_sync_state(Path(name))
        self.assertEqual(state.last_pulled_post_id, 0)
        os.unlink(name)


class TestMessageMapping(unittest.TestCase):
    """Test bus <-> AgentHub message format conversion."""

    def test_bus_to_post_content(self):
        msg = BusMessage(
            timestamp="2026-03-16T10:00:00Z",
            sender="claude-code",
            recipient="all",
            msg_type="SITREP",
            message="all tests passing",
        )
        content = bus_message_to_post_content(msg)
        self.assertIn("[BUS:SITREP]", content)
        self.assertIn("all tests passing", content)

    def test_post_to_bus_message_native(self):
        """Native AgentHub posts become STATUS messages."""
        post = AgentHubPost(
            id=1,
            channel_id=1,
            agent_id="research-bot",
            content="found a bug in layer 3",
            created_at="2026-03-16T10:00:00",
        )
        msg = post_to_bus_message(post)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.sender, "agenthub:research-bot")
        self.assertEqual(msg.recipient, "all")
        self.assertEqual(msg.msg_type, "STATUS")
        self.assertIn("[agenthub]", msg.message)
        self.assertIn("found a bug", msg.message)

    def test_post_to_bus_message_bridged_returns_none(self):
        """Posts that originated from our bus should return None (echo prevention)."""
        post = AgentHubPost(
            id=2,
            channel_id=1,
            agent_id="hummbl-cognition",
            content="[BUS:STATUS] from=claude-code to=all ts=2026-03-16T10:00:00Z\ntest",
            created_at="2026-03-16T10:01:00",
        )
        msg = post_to_bus_message(post)
        self.assertIsNone(msg)

    def test_post_timestamp_normalization(self):
        """Timestamps without Z suffix get normalized."""
        post = AgentHubPost(
            id=3,
            channel_id=1,
            agent_id="bot",
            content="hello",
            created_at="2026-03-16 10:00:00",
        )
        msg = post_to_bus_message(post)
        self.assertTrue(msg.timestamp.endswith("Z"))

    def test_post_timestamp_iso_format(self):
        post = AgentHubPost(
            id=4,
            channel_id=1,
            agent_id="bot",
            content="hello",
            created_at="2026-03-16T10:00:00",
        )
        msg = post_to_bus_message(post)
        self.assertEqual(msg.timestamp, "2026-03-16T10:00:00Z")


class TestAgentHubClient(unittest.TestCase):
    """Test the HTTP client (all network calls mocked)."""

    def test_missing_api_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            # Ensure AGENTHUB_API_KEY is not set
            env = os.environ.copy()
            env.pop("AGENTHUB_API_KEY", None)
            with patch.dict(os.environ, env, clear=True):
                with self.assertRaises(ValueError) as ctx:
                    AgentHubClient(api_key="")
                self.assertIn("AGENTHUB_API_KEY", str(ctx.exception))

    def test_client_init_with_explicit_params(self):
        client = AgentHubClient(
            base_url="http://hub.test:9090",
            api_key="test-key-123",
            agent_id="test-agent",
        )
        self.assertEqual(client.base_url, "http://hub.test:9090")
        self.assertEqual(client.api_key, "test-key-123")
        self.assertEqual(client.agent_id, "test-agent")

    def test_client_strips_trailing_slash(self):
        client = AgentHubClient(
            base_url="http://hub.test:9090/",
            api_key="key",
        )
        self.assertEqual(client.base_url, "http://hub.test:9090")

    @patch("hummbl_cognition.agenthub_bridge.urllib.request.urlopen")
    def test_list_channels(self, mock_urlopen):
        resp_data = [{"id": 1, "name": "general", "description": ""}]
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(resp_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        client = AgentHubClient(base_url="http://hub.test", api_key="key")
        channels = client.list_channels()
        self.assertEqual(len(channels), 1)
        self.assertEqual(channels[0]["name"], "general")

    @patch("hummbl_cognition.agenthub_bridge.urllib.request.urlopen")
    def test_create_post(self, mock_urlopen):
        resp_data = {
            "id": 99,
            "channel_id": 1,
            "agent_id": "hummbl-cognition",
            "content": "test post",
            "created_at": "2026-03-16T10:00:00",
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(resp_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        client = AgentHubClient(base_url="http://hub.test", api_key="key")
        post = client.create_post("general", "test post")
        self.assertEqual(post.id, 99)
        self.assertEqual(post.content, "test post")

        # Verify request was made with correct auth header
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        self.assertEqual(req.get_header("Authorization"), "Bearer key")

    @patch("hummbl_cognition.agenthub_bridge.urllib.request.urlopen")
    def test_list_posts_with_since_id(self, mock_urlopen):
        resp_data = []
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(resp_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        client = AgentHubClient(base_url="http://hub.test", api_key="key")
        client.list_posts("general", since_id=50)

        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        self.assertIn("since_id=50", req.full_url)

    @patch("hummbl_cognition.agenthub_bridge.urllib.request.urlopen")
    def test_ensure_channel_ignores_409(self, mock_urlopen):
        import urllib.error

        error = urllib.error.HTTPError(
            "http://hub.test/api/channels", 409, "Conflict", {}, None
        )
        mock_urlopen.side_effect = error

        client = AgentHubClient(base_url="http://hub.test", api_key="key")
        # Should not raise
        client.ensure_channel("general")

    @patch("hummbl_cognition.agenthub_bridge.urllib.request.urlopen")
    def test_request_raises_on_500(self, mock_urlopen):
        import io
        import urllib.error

        error = urllib.error.HTTPError(
            "http://hub.test/api/channels", 500, "Internal Server Error",
            {}, io.BytesIO(b"server broke"),
        )
        mock_urlopen.side_effect = error

        client = AgentHubClient(base_url="http://hub.test", api_key="key")
        with self.assertRaises(AgentHubError) as ctx:
            client.list_channels()
        self.assertIn("500", str(ctx.exception))


class TestBusIO(unittest.TestCase):
    """Test bus file reading and writing."""

    def test_read_bus_lines(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tsv", delete=False
        ) as f:
            f.write("ts1\ta\tb\tSTATUS\tmsg1\n")
            f.write("ts2\tc\td\tACK\tmsg2\n")
            f.flush()
            name = f.name
        lines = read_bus_lines(Path(name))
        self.assertEqual(len(lines), 2)
        os.unlink(name)

    def test_read_bus_lines_missing_file(self):
        lines = read_bus_lines(Path("/nonexistent/bus.tsv"))
        self.assertEqual(lines, [])

    def test_append_bus_message_direct(self):
        """Test direct append fallback when bus_writer is not available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus_path = Path(tmpdir) / "bus.tsv"
            msg = BusMessage(
                timestamp="2026-03-16T10:00:00Z",
                sender="agenthub:bot",
                recipient="all",
                msg_type="STATUS",
                message="test",
            )
            # Force ImportError for bus_writer
            with patch(
                "hummbl_cognition.agenthub_bridge.post_message",
                side_effect=ImportError("no bus_writer"),
                create=True,
            ), patch(
                "hummbl_bus.bus_writer.post_message",
                side_effect=ImportError("no bus_writer"),
            ):
                append_bus_message(msg, bus_path)

            content = bus_path.read_text()
            self.assertIn("agenthub:bot", content)
            self.assertIn("STATUS", content)

    def test_append_bus_message_propagates_writer_errors(self):
        """Runtime bus_writer failures should not silently degrade to direct append."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus_path = Path(tmpdir) / "bus.tsv"
            msg = BusMessage(
                timestamp="2026-03-16T10:00:00Z",
                sender="agenthub:bot",
                recipient="all",
                msg_type="STATUS",
                message="test",
            )

            with patch(
                "hummbl_bus.bus_writer.post_message",
                side_effect=RuntimeError("writer failed"),
            ), self.assertRaises(RuntimeError):
                append_bus_message(msg, bus_path)

            self.assertFalse(bus_path.exists())


class TestPullFromAgentHub(unittest.TestCase):
    """Test pulling posts from AgentHub into the bus."""

    def _make_client(self):
        return AgentHubClient(base_url="http://hub.test", api_key="key")

    @patch("hummbl_cognition.agenthub_bridge.urllib.request.urlopen")
    def test_pull_new_posts(self, mock_urlopen):
        posts = [
            {
                "id": 1,
                "channel_id": 1,
                "agent_id": "research-bot",
                "content": "discovered pattern X",
                "created_at": "2026-03-16T10:00:00",
            },
            {
                "id": 2,
                "channel_id": 1,
                "agent_id": "analysis-bot",
                "content": "confirmed pattern X",
                "created_at": "2026-03-16T10:01:00",
            },
        ]
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(posts).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            bus_path = Path(tmpdir) / "bus.tsv"
            bus_path.touch()
            state = SyncState()
            client = self._make_client()

            with patch(
                "hummbl_cognition.agenthub_bridge.append_bus_message"
            ) as mock_append:
                count = pull_from_agenthub(client, "general", bus_path, state)

            self.assertEqual(count, 2)
            self.assertEqual(state.last_pulled_post_id, 2)
            self.assertEqual(mock_append.call_count, 2)

    @patch("hummbl_cognition.agenthub_bridge.urllib.request.urlopen")
    def test_pull_skips_own_posts(self, mock_urlopen):
        posts = [
            {
                "id": 10,
                "channel_id": 1,
                "agent_id": "hummbl-cognition",
                "content": "[BUS:STATUS] from=claude to=all ts=...\ntest",
                "created_at": "2026-03-16T10:00:00",
            },
        ]
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(posts).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            bus_path = Path(tmpdir) / "bus.tsv"
            bus_path.touch()
            state = SyncState(pushed_post_ids=[10])
            client = self._make_client()

            with patch(
                "hummbl_cognition.agenthub_bridge.append_bus_message"
            ) as mock_append:
                count = pull_from_agenthub(client, "general", bus_path, state)

            self.assertEqual(count, 0)
            mock_append.assert_not_called()

    @patch("hummbl_cognition.agenthub_bridge.urllib.request.urlopen")
    def test_pull_skips_bridged_posts(self, mock_urlopen):
        """Posts with [BUS:...] prefix are skipped (echo prevention)."""
        posts = [
            {
                "id": 11,
                "channel_id": 1,
                "agent_id": "some-agent",
                "content": "[BUS:MILESTONE] from=codex to=all ts=...\nshipped",
                "created_at": "2026-03-16T10:00:00",
            },
        ]
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(posts).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            bus_path = Path(tmpdir) / "bus.tsv"
            bus_path.touch()
            state = SyncState()
            client = self._make_client()

            with patch(
                "hummbl_cognition.agenthub_bridge.append_bus_message"
            ) as mock_append:
                count = pull_from_agenthub(client, "general", bus_path, state)

            self.assertEqual(count, 0)
            mock_append.assert_not_called()
            # But state should advance past it
            self.assertEqual(state.last_pulled_post_id, 11)

    @patch("hummbl_cognition.agenthub_bridge.urllib.request.urlopen")
    def test_pull_dry_run(self, mock_urlopen):
        posts = [
            {
                "id": 1,
                "channel_id": 1,
                "agent_id": "bot",
                "content": "hello",
                "created_at": "2026-03-16T10:00:00",
            },
        ]
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(posts).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            bus_path = Path(tmpdir) / "bus.tsv"
            bus_path.touch()
            state = SyncState()
            client = self._make_client()

            with patch(
                "hummbl_cognition.agenthub_bridge.append_bus_message"
            ) as mock_append:
                count = pull_from_agenthub(
                    client, "general", bus_path, state, dry_run=True
                )

            self.assertEqual(count, 1)
            mock_append.assert_not_called()


class TestPushToAgentHub(unittest.TestCase):
    """Test pushing bus messages to AgentHub."""

    def _make_client(self):
        return AgentHubClient(base_url="http://hub.test", api_key="key")

    @patch("hummbl_cognition.agenthub_bridge.urllib.request.urlopen")
    def test_push_new_lines(self, mock_urlopen):
        # create_post response
        resp_data = {
            "id": 100,
            "channel_id": 1,
            "agent_id": "hummbl-cognition",
            "content": "...",
            "created_at": "2026-03-16T10:00:00",
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(resp_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            bus_path = Path(tmpdir) / "bus.tsv"
            bus_path.write_text(
                "2026-03-16T10:00:00Z\tclaude\tall\tSTATUS\thello world\n"
            )
            state = SyncState()
            client = self._make_client()

            count = push_to_agenthub(client, "general", bus_path, state)

            self.assertEqual(count, 1)
            self.assertEqual(state.last_pushed_bus_line, 1)
            self.assertIn(100, state.pushed_post_ids)

    @patch("hummbl_cognition.agenthub_bridge.urllib.request.urlopen")
    def test_push_skips_agenthub_messages(self, mock_urlopen):
        """Messages from agenthub: senders should not be pushed back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus_path = Path(tmpdir) / "bus.tsv"
            bus_path.write_text(
                "2026-03-16T10:00:00Z\tagenthub:bot\tall\tSTATUS\tfrom hub\n"
            )
            state = SyncState()
            client = self._make_client()

            count = push_to_agenthub(client, "general", bus_path, state)

            self.assertEqual(count, 0)
            self.assertEqual(state.last_pushed_bus_line, 1)
            mock_urlopen.assert_not_called()

    def test_push_skips_already_pushed_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bus_path = Path(tmpdir) / "bus.tsv"
            bus_path.write_text(
                "2026-03-16T10:00:00Z\tclaude\tall\tSTATUS\told msg\n"
                "2026-03-16T10:01:00Z\tclaude\tall\tSTATUS\tnew msg\n"
            )
            state = SyncState(last_pushed_bus_line=1)
            client = self._make_client()

            with patch.object(client, "create_post") as mock_create:
                mock_create.return_value = AgentHubPost(
                    id=200, channel_id=1, agent_id="hummbl-cognition",
                    content="...", created_at="2026-03-16T10:01:00",
                )
                count = push_to_agenthub(client, "general", bus_path, state)

            self.assertEqual(count, 1)
            self.assertEqual(state.last_pushed_bus_line, 2)

    def test_push_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bus_path = Path(tmpdir) / "bus.tsv"
            bus_path.write_text(
                "2026-03-16T10:00:00Z\tclaude\tall\tSTATUS\ttest\n"
            )
            state = SyncState()
            client = self._make_client()

            with patch.object(client, "create_post") as mock_create:
                count = push_to_agenthub(
                    client, "general", bus_path, state, dry_run=True
                )

            self.assertEqual(count, 1)
            mock_create.assert_not_called()

    def test_push_caps_pushed_post_ids(self):
        """pushed_post_ids should not grow unboundedly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus_path = Path(tmpdir) / "bus.tsv"
            lines = [
                f"2026-03-16T10:{i:02d}:00Z\tclaude\tall\tSTATUS\tmsg{i}\n"
                for i in range(10)
            ]
            bus_path.write_text("".join(lines))
            state = SyncState(pushed_post_ids=list(range(995)))
            client = self._make_client()

            post_id = 1000
            def mock_create(channel, content, parent_id=None):
                nonlocal post_id
                post_id += 1
                return AgentHubPost(
                    id=post_id, channel_id=1, agent_id="hummbl-cognition",
                    content=content, created_at="2026-03-16T10:00:00",
                )

            with patch.object(client, "create_post", side_effect=mock_create):
                push_to_agenthub(client, "general", bus_path, state)

            # Should have been trimmed after exceeding 1000
            self.assertLessEqual(len(state.pushed_post_ids), 510)

    @patch("hummbl_cognition.agenthub_bridge.urllib.request.urlopen")
    def test_push_stops_on_error(self, mock_urlopen):
        """On HTTP error, push stops and does not advance past the failed line."""
        mock_urlopen.side_effect = AgentHubError("connection refused")

        with tempfile.TemporaryDirectory() as tmpdir:
            bus_path = Path(tmpdir) / "bus.tsv"
            bus_path.write_text(
                "2026-03-16T10:00:00Z\tclaude\tall\tSTATUS\tmsg1\n"
                "2026-03-16T10:01:00Z\tclaude\tall\tSTATUS\tmsg2\n"
            )
            state = SyncState()
            client = self._make_client()

            with patch.object(
                client, "create_post", side_effect=AgentHubError("fail")
            ):
                count = push_to_agenthub(client, "general", bus_path, state)

            self.assertEqual(count, 0)
            # Should not have advanced past the failed line
            self.assertEqual(state.last_pushed_bus_line, 0)


class TestSync(unittest.TestCase):
    """Test the top-level sync function."""

    @patch("hummbl_cognition.agenthub_bridge.AgentHubClient")
    @patch("hummbl_cognition.agenthub_bridge._resolve_bus_path")
    @patch("hummbl_cognition.agenthub_bridge._resolve_state_path")
    @patch("hummbl_cognition.agenthub_bridge.load_sync_state")
    @patch("hummbl_cognition.agenthub_bridge.save_sync_state")
    @patch("hummbl_cognition.agenthub_bridge.pull_from_agenthub")
    @patch("hummbl_cognition.agenthub_bridge.push_to_agenthub")
    def test_sync_both(
        self, mock_push, mock_pull, mock_save, mock_load,
        mock_state_path, mock_bus_path, mock_client_cls,
    ):
        mock_bus_path.return_value = Path("/tmp/bus.tsv")
        mock_state_path.return_value = Path("/tmp/state.json")
        mock_load.return_value = SyncState()
        mock_pull.return_value = 3
        mock_push.return_value = 2

        result = sync(
            channel="general",
            direction="both",
            api_key="test-key",
        )

        self.assertEqual(result, {"pulled": 3, "pushed": 2})
        mock_pull.assert_called_once()
        mock_push.assert_called_once()
        mock_save.assert_called_once()

    @patch("hummbl_cognition.agenthub_bridge.AgentHubClient")
    @patch("hummbl_cognition.agenthub_bridge._resolve_bus_path")
    @patch("hummbl_cognition.agenthub_bridge._resolve_state_path")
    @patch("hummbl_cognition.agenthub_bridge.load_sync_state")
    @patch("hummbl_cognition.agenthub_bridge.save_sync_state")
    @patch("hummbl_cognition.agenthub_bridge.pull_from_agenthub")
    @patch("hummbl_cognition.agenthub_bridge.push_to_agenthub")
    def test_sync_pull_only(
        self, mock_push, mock_pull, mock_save, mock_load,
        mock_state_path, mock_bus_path, mock_client_cls,
    ):
        mock_bus_path.return_value = Path("/tmp/bus.tsv")
        mock_state_path.return_value = Path("/tmp/state.json")
        mock_load.return_value = SyncState()
        mock_pull.return_value = 5

        result = sync(channel="general", direction="pull", api_key="test-key")

        self.assertEqual(result["pulled"], 5)
        self.assertEqual(result["pushed"], 0)
        mock_push.assert_not_called()

    @patch("hummbl_cognition.agenthub_bridge.AgentHubClient")
    @patch("hummbl_cognition.agenthub_bridge._resolve_bus_path")
    @patch("hummbl_cognition.agenthub_bridge._resolve_state_path")
    @patch("hummbl_cognition.agenthub_bridge.load_sync_state")
    @patch("hummbl_cognition.agenthub_bridge.save_sync_state")
    @patch("hummbl_cognition.agenthub_bridge.pull_from_agenthub")
    @patch("hummbl_cognition.agenthub_bridge.push_to_agenthub")
    def test_sync_dry_run_does_not_save(
        self, mock_push, mock_pull, mock_save, mock_load,
        mock_state_path, mock_bus_path, mock_client_cls,
    ):
        mock_bus_path.return_value = Path("/tmp/bus.tsv")
        mock_state_path.return_value = Path("/tmp/state.json")
        mock_load.return_value = SyncState()
        mock_pull.return_value = 0
        mock_push.return_value = 0

        sync(channel="general", direction="both", api_key="key", dry_run=True)

        mock_save.assert_not_called()


class TestCLI(unittest.TestCase):
    """Test CLI argument parsing and dispatch."""

    def test_no_command_returns_2(self):
        result = main([])
        self.assertEqual(result, 2)

    @patch("hummbl_cognition.agenthub_bridge.show_status")
    def test_status_command(self, mock_status):
        mock_status.return_value = 0
        result = main(["status"])
        self.assertEqual(result, 0)
        mock_status.assert_called_once()

    @patch("hummbl_cognition.agenthub_bridge.sync")
    def test_sync_command(self, mock_sync):
        mock_sync.return_value = {"pulled": 1, "pushed": 2}
        result = main([
            "--api-key", "test-key",
            "sync", "--channel", "general", "--direction", "both",
        ])
        self.assertEqual(result, 0)
        mock_sync.assert_called_once()
        call_kwargs = mock_sync.call_args
        self.assertEqual(call_kwargs[1]["channel"], "general")  # keyword arg
        self.assertEqual(call_kwargs[1]["direction"], "both")

    @patch("hummbl_cognition.agenthub_bridge.sync")
    def test_sync_error_returns_1(self, mock_sync):
        mock_sync.side_effect = AgentHubError("connection refused")
        result = main([
            "--api-key", "key",
            "sync", "--channel", "general",
        ])
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
