#!/usr/bin/env python3

from pathlib import Path
import subprocess
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[3]
MODULE_URI = (ROOT / ".pi/extensions/subagent/live-output.mjs").as_uri()


def run_node(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class PiSubagentLiveOutputTests(unittest.TestCase):
    def test_json_events_expose_visible_progress_without_thinking(self) -> None:
        script = textwrap.dedent(
            f"""
            import assert from "node:assert/strict";
            import {{
              applySubagentEvent,
              getDisplayItems,
              getResultOutput,
              isFailedResult,
            }} from {MODULE_URI!r};

            const result = {{
              agent: "worker",
              exitCode: -1,
              messages: [],
              stderr: "",
              usage: {{
                input: 0,
                output: 0,
                cacheRead: 0,
                cacheWrite: 0,
                cost: 0,
                contextTokens: 0,
                turns: 0,
              }},
            }};

            assert.equal(applySubagentEvent(result, {{
              type: "message_update",
              assistantMessageEvent: {{ type: "thinking_delta", delta: "private reasoning" }},
            }}), false);
            assert.deepEqual(getDisplayItems(result), []);

            assert.equal(applySubagentEvent(result, {{
              type: "message_update",
              assistantMessageEvent: {{ type: "text_delta", delta: "正在" }},
            }}), true);
            applySubagentEvent(result, {{
              type: "message_update",
              assistantMessageEvent: {{ type: "text_delta", delta: "检查" }},
            }});
            assert.deepEqual(getDisplayItems(result), [
              {{ type: "text", text: "正在检查", streaming: true }},
            ]);

            const assistant = {{
              id: "assistant-1",
              role: "assistant",
              model: "test-model",
              stopReason: "toolUse",
              usage: {{
                input: 10,
                output: 5,
                cacheRead: 3,
                cacheWrite: 2,
                totalTokens: 20,
                cost: {{ total: 0.25 }},
              }},
              content: [
                {{ type: "thinking", thinking: "must stay hidden" }},
                {{ type: "text", text: "开始读取文件" }},
                {{ type: "toolCall", name: "read", arguments: {{ path: "README.md" }} }},
              ],
            }};
            assert.equal(applySubagentEvent(result, {{ type: "message_end", message: assistant }}), true);
            assert.equal(result.streamingText, "");
            assert.equal(result.usage.turns, 1);
            assert.equal(result.usage.input, 10);
            assert.equal(result.usage.output, 5);
            assert.equal(result.usage.cacheRead, 3);
            assert.equal(result.usage.cacheWrite, 2);
            assert.equal(result.usage.contextTokens, 20);
            assert.equal(result.usage.cost, 0.25);
            assert.equal(result.model, "test-model");
            assert.deepEqual(getDisplayItems(result), [
              {{ type: "text", text: "开始读取文件" }},
              {{ type: "toolCall", name: "read", args: {{ path: "README.md" }} }},
            ]);

            assert.equal(applySubagentEvent(result, {{ type: "agent_settled" }}), true);
            assert.equal(result.settled, true);
            result.exitCode = 0;
            result.stopReason = "stop";
            assert.equal(isFailedResult(result), false);
            assert.equal(getResultOutput(result), "开始读取文件");

            result.exitCode = 1;
            result.errorMessage = "child failed";
            assert.equal(isFailedResult(result), true);
            assert.equal(getResultOutput(result), "child failed");
            """
        )
        result = run_node(script)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_extension_wires_foreground_and_background_live_updates(self) -> None:
        source = (ROOT / ".pi/extensions/subagent/index.ts").read_text()
        self.assertIn("applySubagentEvent", source)
        self.assertIn("onUpdate?.({", source)
        self.assertIn("updateBackgroundUi(ctx, backgroundJobs)", source)
        self.assertIn('pi.on("session_shutdown"', source)
        self.assertIn("SHUTDOWN_WAIT_MS", source)
        self.assertIn("job.process?.stdout?.destroy()", source)
        self.assertIn('placement: "belowEditor"', source)
        self.assertNotIn("detached: true", source)

        adapter = (ROOT / ".pi/APPEND_SYSTEM.md").read_text()
        self.assertIn("streams visible progress in the TUI", adapter)
        self.assertIn("complete JSON event and stderr streams", adapter)


if __name__ == "__main__":
    unittest.main()
