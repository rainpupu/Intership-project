/**
 * Markdown 渲染工具
 *
 * Day11 对话页面中渲染 AI 返回的 Markdown 内容
 */
import MarkdownIt from 'markdown-it'

// 创建 markdown-it 实例（禁用 HTML 标签以保障安全）
const md = new MarkdownIt({
  html: false,        // 禁用 HTML 标签
  linkify: true,      // 自动识别 URL
  typographer: true,  // 智能排版
  breaks: true,       // \n 转换为 <br>
})

/**
 * 将 Markdown 文本渲染为 HTML
 * @param {string} text - Markdown 文本
 * @returns {string} HTML 字符串
 */
export function renderMarkdown(text) {
  if (!text) return ''
  return md.render(text)
}

export default md
