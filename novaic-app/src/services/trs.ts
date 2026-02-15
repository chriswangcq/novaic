/**
 * Tool Result Service (TRS) 客户端
 *
 * 通过 Gateway 代理访问 TRS，按 result_id 拉取工具结果。
 * 图片和文件使用 URL + File Service 展示（不展开 base64）。
 */

import { invoke } from '@tauri-apps/api/core';
import { API_CONFIG } from '../config';

/** TRS content 项 */
export type TrsContentItem =
  | { type: 'text'; text: string; _truncated?: boolean; _truncation?: Record<string, unknown> }
  | { type: 'image'; url: string; mimeType?: string }
  | { type: 'resource'; url: string; mimeType?: string };

/** TRS /full 响应 */
export interface TrsFullResponse {
  success: boolean;
  normalized?: {
    content?: TrsContentItem[];
  };
}

/** TRS /preview 响应 */
export interface TrsPreviewResponse {
  success: boolean;
  result_id?: string;
  summary?: string;
  content_count?: number;
}

/**
 * 获取 result_id 的完整内容（含长文本、图片 URL）
 */
export async function getTrsFull(resultId: string): Promise<TrsFullResponse> {
  const res = await invoke('gateway_get', {
    path: `/api/trs/${resultId}/full`,
  });
  return res as TrsFullResponse;
}

/**
 * 获取 result_id 的预览（摘要）
 */
export async function getTrsPreview(resultId: string, maxTextLen = 500): Promise<TrsPreviewResponse> {
  const res = await invoke('gateway_get', {
    path: `/api/trs/${resultId}/preview?max_text_len=${maxTextLen}`,
  });
  return res as TrsPreviewResponse;
}

/**
 * 将 TRS 返回的 url 转为前端可用的完整 URL（经 Gateway 代理 File Service）
 */
export function toFileUrl(url: string): string {
  if (!url) return '';
  if (url.startsWith('http')) return url;
  const base = API_CONFIG.GATEWAY_URL.replace(/\/$/, '');
  return url.startsWith('/') ? `${base}${url}` : `${base}/${url}`;
}
