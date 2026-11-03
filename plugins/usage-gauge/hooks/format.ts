import type { Credits, Remote, UsageWindow } from '../types'

export const FIVE_HOUR_MS = 5 * 60 * 60 * 1000
export const SEVEN_DAY_MS = 7 * 24 * 60 * 60 * 1000

/** ゲージの色: 70% 未満は緑、70〜90% は黄、90% 以上は赤 */
export function gaugeColor(percent: number): 'success' | 'warning' | 'error' {
  if (percent >= 90) return 'error'
  if (percent >= 70) return 'warning'
  return 'success'
}

export function clampPercent(percent: number): number {
  if (!Number.isFinite(percent)) return 0
  return Math.max(0, Math.min(100, percent))
}

/** 割合の表示（整数に丸める） */
export function formatPercent(percent: number | undefined): string {
  if (percent === undefined || !Number.isFinite(percent)) return '—'
  return `${Math.round(percent)}%`
}

/** トークン数の表示: 401900 → 401.9k、1000000 → 1M */
export function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${trim(n / 1_000_000)}M`
  if (n >= 1_000) return `${trim(n / 1_000)}k`
  return String(n)
}

function trim(x: number): string {
  return (Math.round(x * 10) / 10).toString()
}

/** リセットまでの残り時間: あと2日22時間 / あと4時間12分 / あと12分 */
export function formatRemaining(resetsAt: string | undefined, now: number): string {
  if (!resetsAt) return ''
  const ms = Date.parse(resetsAt) - now
  if (!Number.isFinite(ms)) return ''
  if (ms <= 0) return 'まもなくリセット'
  const totalMin = Math.floor(ms / 60_000)
  const days = Math.floor(totalMin / (60 * 24))
  const hours = Math.floor((totalMin % (60 * 24)) / 60)
  const mins = totalMin % 60
  if (days > 0) return `あと${days}日${hours}時間`
  if (hours > 0) return `あと${hours}時間${mins}分`
  return `あと${mins}分`
}

/** 枠の経過割合（0〜1）: 1 - 残り/枠の長さ */
export function elapsedRatio(
  resetsAt: string | undefined,
  now: number,
  windowMs: number,
): number | undefined {
  if (!resetsAt) return undefined
  const left = Date.parse(resetsAt) - now
  if (!Number.isFinite(left)) return undefined
  return Math.max(0, Math.min(1, 1 - left / windowMs))
}

// ゲージ（SVG）の色。テーマに依らず読める中間色にする
const SVG_COLORS = { success: '#3fb950', warning: '#d29922', error: '#f85149' } as const
const SVG_TRACK = '#8b949e55'
const SVG_MARKER = '#8b949e'

/** デスクトップ用の細いゲージ。経過の目盛りは縦線で重ねる */
export function gaugeSvg(percent: number, elapsed: number | undefined, width: number, height: number): string {
  const barH = 6
  const y = (height - barH) / 2
  const fill = Math.round((clampPercent(percent) / 100) * width)
  const color = SVG_COLORS[gaugeColor(percent)]
  const parts = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`,
    `<rect x="0" y="${y}" width="${width}" height="${barH}" rx="3" fill="${SVG_TRACK}"/>`,
  ]
  if (fill > 0) parts.push(`<rect x="0" y="${y}" width="${fill}" height="${barH}" rx="3" fill="${color}"/>`)
  if (elapsed !== undefined) {
    const x = Math.max(1, Math.min(width - 1, Math.round(elapsed * width)))
    parts.push(`<rect x="${x - 1}" y="0" width="2" height="${height}" rx="1" fill="${SVG_MARKER}"/>`)
  }
  parts.push('</svg>')
  return parts.join('')
}

/** ターミナル用のゲージ: 使った分を太線、残りを細線、経過の位置に縦線を置く */
export type GaugeSegment = { kind: 'used' | 'rest' | 'marker'; text: string }

export function gaugeText(percent: number, elapsed: number | undefined, width: number): GaugeSegment[] {
  const fill = Math.round((clampPercent(percent) / 100) * width)
  const at = elapsed === undefined ? -1 : Math.min(width - 1, Math.round(elapsed * width))
  // 1セルずつ種類を決め、同じ種類が続く区間をまとめる
  const out: GaugeSegment[] = []
  for (let i = 0; i < width; i++) {
    const kind: GaugeSegment['kind'] = i === at ? 'marker' : i < fill ? 'used' : 'rest'
    const ch = kind === 'used' ? '━' : kind === 'rest' ? '─' : i < fill ? '┃' : '│'
    const last = out[out.length - 1]
    if (last && last.kind === kind) last.text += ch
    else out.push({ kind, text: ch })
  }
  return out
}

/** 金額の表示: 0 → $0、12.5 → $12.50 */
export function formatDollars(x: number): string {
  return Number.isInteger(x) ? `$${x}` : `$${x.toFixed(2)}`
}

export function creditsDetail(c: Credits): string {
  // 無効なら上限が残っていても使えないので、上限は出さない
  if (!c.enabled) return `${formatDollars(c.used)} 無効`
  if (c.limit !== undefined) return `${formatDollars(c.used)}/${formatDollars(c.limit)}`
  return `${formatDollars(c.used)}/上限なし`
}

// ---- 非公式 API の応答の読み取り ----

type Json = Record<string, unknown>

function obj(v: unknown): Json | undefined {
  return v !== null && typeof v === 'object' && !Array.isArray(v) ? (v as Json) : undefined
}

function num(v: unknown): number | undefined {
  return typeof v === 'number' && Number.isFinite(v) ? v : undefined
}

function str(v: unknown): string | undefined {
  return typeof v === 'string' ? v : undefined
}

/** `{ amount_minor, exponent }` を米ドルに直す */
function money(v: unknown): number | undefined {
  const o = obj(v)
  const minor = num(o?.amount_minor)
  if (minor === undefined) return undefined
  return minor / 10 ** (num(o?.exponent) ?? 2)
}

function parseWindow(v: unknown): UsageWindow | undefined {
  const o = obj(v)
  const percent = num(o?.utilization)
  if (percent === undefined) return undefined
  return { percent, resetsAt: str(o?.resets_at) }
}

/**
 * `GET /api/oauth/usage` の応答から、Fable 週次枠・クレジット・5時間・週間を取り出す。
 * 確認済みのキー: limits[].kind / scope.model.display_name / percent / resets_at、
 * spend.used.{amount_minor,exponent} / spend.limit / spend.percent / spend.enabled
 */
export function parseRemote(body: unknown): Remote {
  const root = obj(body) ?? {}
  const out: Remote = {}

  const limits = Array.isArray(root.limits) ? root.limits : []
  for (const item of limits) {
    const l = obj(item)
    const name = str(obj(obj(l?.scope)?.model)?.display_name)
    const percent = num(l?.percent)
    if (l?.kind === 'weekly_scoped' && name && /fable/i.test(name) && percent !== undefined) {
      out.fable = { percent, resetsAt: str(l.resets_at) }
    }
  }

  const spend = obj(root.spend)
  if (spend) {
    out.credits = {
      used: money(spend.used) ?? 0,
      limit: money(spend.limit),
      percent: num(spend.percent),
      enabled: spend.enabled === true,
    }
  }

  out.fiveHour = parseWindow(root.five_hour)
  out.sevenDay = parseWindow(root.seven_day)
  return out
}
