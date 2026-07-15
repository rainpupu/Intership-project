export interface AgentMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
}

export function sendAgentMessage(content: string): Promise<AgentMessage> {
  const reply = content.includes('重点关注')
    ? '目前狸花弟弟和奶盖需要重点关注，建议优先复查健康状态并补充近照。'
    : '我已根据当前 Mock 档案为你整理建议：优先关注性格亲人、健康良好、待领养的猫咪。';

  return Promise.resolve({
    id: `assistant-${Date.now()}`,
    role: 'assistant',
    content: reply,
    createdAt: new Date().toISOString(),
  });
}
