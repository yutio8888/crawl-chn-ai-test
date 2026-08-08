function textParts(message) {
  if (!message || message.role !== "assistant" || !Array.isArray(message.content)) return [];
  return message.content
    .filter((part) => part && part.type === "text" && typeof part.text === "string")
    .map((part) => part.text);
}

function pushMessageOnce(messages, message) {
  const last = messages[messages.length - 1];
  if (last === message) return;
  if (last?.id && message?.id && last.id === message.id) return;
  messages.push(message);
}

/**
 * Apply one JSON-mode Pi event to a mutable subagent result.
 * Returns true only when user-visible progress changed. Thinking events are
 * intentionally ignored.
 */
export function applySubagentEvent(result, event) {
  if (!result || !event || typeof event !== "object") return false;

  if (event.type === "message_update") {
    const update = event.assistantMessageEvent;
    if (!update || typeof update !== "object") return false;
    if (update.type === "text_start") {
      result.streamingText = "";
      return false;
    }
    if (update.type === "text_delta" && typeof update.delta === "string") {
      result.streamingText = (result.streamingText || "") + update.delta;
      return true;
    }
    if (update.type === "text_end" && typeof update.content === "string") {
      result.streamingText = update.content;
      return true;
    }
    return false;
  }

  if (event.type === "message_end" && event.message) {
    const message = event.message;
    pushMessageOnce(result.messages, message);
    if (message.role !== "assistant") return false;

    result.streamingText = "";
    result.usage.turns += 1;
    const usage = message.usage;
    if (usage) {
      result.usage.input += usage.input || 0;
      result.usage.output += usage.output || 0;
      result.usage.cacheRead += usage.cacheRead || 0;
      result.usage.cacheWrite += usage.cacheWrite || 0;
      result.usage.cost += usage.cost?.total || 0;
      result.usage.contextTokens = usage.totalTokens || 0;
    }
    if (!result.model && message.model) result.model = message.model;
    if (message.stopReason) result.stopReason = message.stopReason;
    if (message.errorMessage) result.errorMessage = message.errorMessage;
    return true;
  }

  // Compatibility with older JSON event streams that emitted tool results
  // separately instead of as message_end events.
  if (event.type === "tool_result_end" && event.message) {
    pushMessageOnce(result.messages, event.message);
    return false;
  }

  if (event.type === "agent_settled") {
    result.settled = true;
    return true;
  }

  return false;
}

export function getFinalOutput(messages) {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const parts = textParts(messages[i]);
    if (parts.length > 0) return parts.join("\n");
  }
  return "";
}

export function isFailedResult(result) {
  return result.exitCode !== 0 || result.stopReason === "error" || result.stopReason === "aborted";
}

export function getResultOutput(result) {
  if (isFailedResult(result)) {
    return result.errorMessage || result.stderr || getFinalOutput(result.messages) || "(no output)";
  }
  return getFinalOutput(result.messages) || "(no output)";
}

export function getDisplayItems(result) {
  const items = [];
  for (const message of result.messages) {
    if (!message || message.role !== "assistant" || !Array.isArray(message.content)) continue;
    for (const part of message.content) {
      if (part?.type === "text" && typeof part.text === "string" && part.text.trim()) {
        items.push({ type: "text", text: part.text });
      } else if (part?.type === "toolCall" && typeof part.name === "string") {
        items.push({
          type: "toolCall",
          name: part.name,
          args: part.arguments && typeof part.arguments === "object" ? part.arguments : {},
        });
      }
    }
  }
  if (typeof result.streamingText === "string" && result.streamingText.trim()) {
    items.push({ type: "text", text: result.streamingText, streaming: true });
  }
  return items;
}
