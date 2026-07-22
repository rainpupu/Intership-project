/**
 * Agent 对话 API — 共享会话管理器
 * 使用 fetch 直接请求，避免 axios proxy 兼容问题
 */

export interface AgentMessage {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  createdAt: string;
}

// 全局共享会话 ID（所有组件共用同一个）
let _sessionId: number | null = null;
let _sessionPromise: Promise<number> | null = null;

/** 获取或创建会话 */
async function ensureSession(): Promise<number> {
  if (_sessionId) return _sessionId;
  if (!_sessionPromise) {
    _sessionPromise = fetch('/api/chat/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: 1, title: '智能对话' }),
    }).then(r => r.json()).then(d => {
      _sessionId = d.id;
      return d.id;
    }).catch(e => {
      _sessionPromise = null;
      throw e;
    });
  }
  return _sessionPromise;
}

/**
 * 发送消息（SSE 流式）
 */
export async function sendAgentMessageStream(
  message: string,
  callbacks: {
    onToken?: (token: string) => void;
    onToolCall?: (tool: string, input: string) => void;
    onToolResult?: (output: string) => void;
    onDone?: (fullContent: string) => void;
    onError?: (error: string) => void;
  }
): Promise<void> {
  const { onToken, onToolCall, onToolResult, onDone, onError } = callbacks;

  try {
    const sid = await ensureSession();
    const url = `/api/chat/sessions/${sid}/messages`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      onError?.(`请求失败: ${response.status}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) { onError?.('无法读取响应流'); return; }

    const decoder = new TextDecoder();
    let buffer = '';
    let fullContent = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          const data = JSON.parse(line.slice(6));
          switch (data.type) {
            case 'token':
              fullContent += data.content;
              onToken?.(data.content);
              break;
            case 'tool_call':
              onToolCall?.(data.tool, data.input);
              break;
            case 'tool_result':
              onToolResult?.(data.output);
              break;
            case 'done':
              onDone?.(fullContent);
              break;
            case 'error':
              onError?.(data.content);
              break;
          }
        } catch { /* ignore */ }
      }
    }
  } catch (e: any) {
    onError?.(`连接错误: ${e.message}`);
  }
}

// 向后兼容
export function sendAgentMessage(_content: string): Promise<AgentMessage> {
  return Promise.resolve({
    id: `legacy-${Date.now()}`,
    role: 'assistant',
    content: '正在接入智能体...',
    createdAt: new Date().toISOString(),
  });
}
