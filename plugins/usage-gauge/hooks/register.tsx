import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Official, Remote, UsageWindow } from '../types'
import {
  backoffMs,
  clampPercent,
  creditsDetail,
  creditsPercent,
  elapsedRatio,
  FIVE_HOUR_MS,
  formatPercent,
  formatRemaining,
  formatTokens,
  gaugeColor,
  gaugeSvg,
  gaugeText,
  hasUsage,
  mergeRemote,
  parseRemote,
  SEVEN_DAY_MS,
} from './format'

// 非公式の OAuth 使用量 API（Fable 週次枠とクレジットを埋める用途）
const USAGE_URL = 'https://api.anthropic.com/api/oauth/usage'
// 公式値と残り時間の表示を更新する間隔
const POLL_MS = 60_000
// 非公式 API を呼ぶ最短の間隔（短いと 429 が返り続ける）
const MIN_FETCH_GAP_MS = 5 * 60_000
// 認証情報が無い環境で、もう一度試すまでの間隔
const NO_AUTH_RETRY_MS = 60 * 60_000
const STORE_KEY = 'collapsed'
const LAST_GOOD_KEY = 'lastRemote'
// デスクトップの1セルあたりのおおよその幅（CSS ピクセル）
const DESKTOP_CELL_PX = 8.5

// 値の形を変えたらタグを変える（古い形の値を初期値扱いにする）
const official = atom({ plugin: 'usage-gauge', key: 'official' } as const, null, {
  shape: 'official-1',
})
const remote = atom({ plugin: 'usage-gauge', key: 'remote' } as const, null, {
  shape: 'remote-1',
})
const now = atom({ plugin: 'usage-gauge', key: 'now' } as const, 0)
const collapsed = atom({ plugin: 'usage-gauge', key: 'collapsed' } as const, null)

// モジュール変数: リロードで初期化されてよい値
let lastFetchAt = 0
let isFetching = false
// 失敗が続いたときの待ち時間と、次に取得してよい時刻
let backoff = 0
let nextAllowedAt = 0

/** 公式値（$.session.usage()）を読み直して $.state に置く */
async function refreshOfficial($: EngineInterface): Promise<void> {
  const usage = await $.session.usage()
  const pick = (kind: string): UsageWindow | undefined => {
    const r = usage.rateLimits.find(x => x.kind === kind)
    return r ? { percent: r.percentUsed, resetsAt: r.resetsAt } : undefined
  }
  const value: Official = {
    ctxTokens: usage.context.tokens,
    ctxWindow: usage.context.window,
    ctxPercent: usage.context.percent,
    fiveHour: pick('five_hour'),
    sevenDay: pick('seven_day'),
  }
  await update($, official, () => value)
}

/**
 * 非公式 API を叩いて $.state に置く。トークンは本体が持ち、mod には渡らない。
 * 失敗したら前回の値を残してエラーを添え、取得の間隔を延ばす。
 */
async function refreshRemote($: EngineInterface): Promise<void> {
  const t = await $.clock.now()
  if (isFetching || t < nextAllowedAt || (lastFetchAt > 0 && t - lastFetchAt < MIN_FETCH_GAP_MS)) return
  isFetching = true
  lastFetchAt = t
  let fresh: Remote | undefined
  let error: string | undefined
  let noAuth = false
  try {
    const auth = await $.session.authorize()
    if (!auth) {
      // API キーやゲートウェイでは取れない。エラーは出さず、しばらく呼ばない
      noAuth = true
    } else {
      const res = await $.http.fetch(USAGE_URL, {
        headers: { 'anthropic-beta': 'oauth-2025-04-20' },
        auth: auth.handle,
      })
      const parsed = res.ok ? parseRemote(JSON.parse(res.text)) : undefined
      if (parsed && hasUsage(parsed)) {
        fresh = parsed
      } else if (res.ok) {
        // 200 でも使用量が読めない応答は、前回値を消さないよう失敗として扱う
        error = '非公式API: 応答に使用量なし'
        backoff = backoffMs(backoff, undefined)
      } else {
        error = `非公式API取得失敗 (${res.status})`
        backoff = backoffMs(backoff, res.headers['retry-after'])
      }
    }
  } catch {
    error = '非公式API取得失敗'
    backoff = backoffMs(backoff, undefined)
  } finally {
    isFetching = false
  }
  if (noAuth) {
    nextAllowedAt = t + NO_AUTH_RETRY_MS
    return
  }
  if (fresh) {
    backoff = 0
    nextAllowedAt = 0
    // 応答に欠けた項目は前回の値を残す（API の変化で一部だけ取れなくなっても消さない）
    const got = fresh
    const merged = await update($, remote, prev => mergeRemote(prev, got))
    // 次回起動や取得失敗のときに使えるよう、最後に取れた値を残す
    await $.store.set(LAST_GOOD_KEY, merged)
  } else {
    nextAllowedAt = t + backoff
    const saved = (await $.store.get(LAST_GOOD_KEY)) as Remote | undefined
    await update($, remote, prev => {
      const { error: _old, ...values } = prev ?? saved ?? {}
      return { ...values, error }
    })
  }
}

async function tick($: EngineInterface): Promise<void> {
  const t = await $.clock.now()
  await update($, now, () => t)
  await refreshOfficial($)
  await refreshRemote($)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const r = await next(e)
    // 非公式 API が取れるまでの間は、前回取れた値を出す
    const saved = (await $.store.get(LAST_GOOD_KEY)) as Remote | undefined
    if (saved) await update($, remote, prev => prev ?? saved)
    // 起動を待たせないよう、初回の取得はタイマーに回す
    $.clock.after(1, () => void tick($))
    $.clock.every(POLL_MS, () => void tick($))
    return r
  })

  on('session.measure', async ($, e, next) => {
    const r = await next(e)
    await refreshOfficial($)
    return r
  })

  on('turn.complete', async ($, e, next) => {
    const r = await next(e)
    // 間引きは refreshRemote の中で行う
    $.clock.after(1, () => void refreshRemote($))
    return r
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey) return next(e)

    const { Box, Text, Button } = $.ui.resolve(e)
    const isDesktop = e.surface === 'desktop'
    const off = await read($, official)
    const rem = await read($, remote)
    await read($, now) // 1分ごとの再描画のために購読する
    const t = await $.clock.now()
    const stored = await read($, collapsed)
    const isCollapsed = stored ?? (await $.store.get(STORE_KEY)) === true

    const fiveHour = off?.fiveHour ?? rem?.fiveHour
    const sevenDay = off?.sevenDay ?? rem?.sevenDay
    const fable = rem?.fable
    const credits = rem?.credits

    const toggle = (
      <Button
        key="toggle"
        label={isCollapsed ? '▸' : '▾'}
        plain
        onPress={async () => {
          // 描画時の値ではなく、押した時点の値から反転する
          const fromStore = (await $.store.get(STORE_KEY)) === true
          const toggled = await update($, collapsed, v => !(v ?? fromStore))
          await $.store.set(STORE_KEY, toggled)
        }}
      />
    )

    if (isCollapsed) {
      const parts = [
        `ctx ${formatPercent(off?.ctxPercent)}`,
        `5h ${formatPercent(fiveHour?.percent)}`,
        `週 ${formatPercent(sevenDay?.percent)}`,
        `Fable ${formatPercent(fable?.percent)}`,
        credits ? creditsDetail(credits) : '$—',
      ]
      return (
        <Box flexDirection="row" gap={1}>
          {toggle}
          <Text dimColor wrap="truncate-end">
            {parts.join(' · ')}
          </Text>
          {rem?.error && <Text dimColor>{rem.error}</Text>}
        </Box>
      )
    }

    // 1行の幅 = ラベル + ゲージ + 割合 + 補足。デスクトップは文字が詰まるので狭めに取る
    const LABEL = isDesktop ? 10 : 12
    const PCT = 5
    const DETAIL = isDesktop ? 13 : 15
    const fixed = LABEL + 1 + PCT + 1 + DETAIL
    const cols = e.props.bodyColumns
    const TOGGLE = 3
    const COL_GAP = 3
    const twoColGauge = Math.min(24, Math.floor((cols - TOGGLE - COL_GAP) / 2) - fixed)
    const isTwoColumns = twoColGauge >= (isDesktop ? 6 : 8)
    const gaugeWidth = isTwoColumns ? twoColGauge : Math.max(6, Math.min(30, cols - TOGGLE - fixed))

    const gauge = (percent: number | undefined, elapsed: number | undefined) => {
      const p = percent === undefined ? 0 : clampPercent(percent)
      if (e.surface === 'desktop') {
        // デスクトップは細いバーを SVG で描く（Box の背景色だと行どうしがつながって見える）
        const { Svg } = $.ui.resolve(e)
        const px = Math.round(gaugeWidth * DESKTOP_CELL_PX)
        return (
          <Box width={gaugeWidth} overflow="hidden">
            <Svg source={gaugeSvg(p, elapsed, px, 12)} alt={formatPercent(percent)} width={px} height={12} />
          </Box>
        )
      }
      return (
        <Box width={gaugeWidth}>
          <Text>
            {gaugeText(p, elapsed, gaugeWidth).map(s =>
              s.kind === 'used' ? (
                <Text color={gaugeColor(p)}>{s.text}</Text>
              ) : s.kind === 'marker' ? (
                <Text color="text">{s.text}</Text>
              ) : (
                <Text dimColor>{s.text}</Text>
              ),
            )}
          </Text>
        </Box>
      )
    }

    const row = (key: string, label: string, percent: number | undefined, detail: string, elapsed?: number) => (
      <Box key={key} flexDirection="row" alignItems="center">
        <Box width={LABEL}>
          <Text wrap="truncate-end">{label}</Text>
        </Box>
        {gauge(percent, elapsed)}
        <Box width={PCT + 1} justifyContent="flex-end">
          <Text tabular>{formatPercent(percent)}</Text>
        </Box>
        <Box width={DETAIL + 1} paddingLeft={1}>
          <Text dimColor wrap="truncate-end">
            {detail}
          </Text>
        </Box>
      </Box>
    )

    const ctxDetail =
      off?.ctxTokens !== undefined && off.ctxWindow
        ? `${formatTokens(off.ctxTokens)}/${formatTokens(off.ctxWindow)}`
        : off?.ctxWindow
          ? `—/${formatTokens(off.ctxWindow)}`
          : ''

    const ctxRow = row('ctx', 'コンテキスト', off?.ctxPercent, ctxDetail)
    const fiveRow = row(
      'five',
      '5時間',
      fiveHour?.percent,
      formatRemaining(fiveHour?.resetsAt, t),
      elapsedRatio(fiveHour?.resetsAt, t, FIVE_HOUR_MS),
    )
    const weekRow = row(
      'week',
      '週間',
      sevenDay?.percent,
      formatRemaining(sevenDay?.resetsAt, t),
      elapsedRatio(sevenDay?.resetsAt, t, SEVEN_DAY_MS),
    )
    const fableRow = row(
      'fable',
      '週間 Fable',
      fable?.percent,
      formatRemaining(fable?.resetsAt, t),
      elapsedRatio(fable?.resetsAt, t, SEVEN_DAY_MS),
    )
    const creditRow = row(
      'credit',
      'クレジット',
      credits ? creditsPercent(credits) : undefined,
      credits ? creditsDetail(credits) : '',
    )

    const body = isTwoColumns ? (
      <Box flexDirection="row" gap={COL_GAP}>
        <Box flexDirection="column">
          {ctxRow}
          {fiveRow}
          {creditRow}
        </Box>
        <Box flexDirection="column">
          {weekRow}
          {fableRow}
        </Box>
      </Box>
    ) : (
      <Box flexDirection="column">
        {ctxRow}
        {fiveRow}
        {weekRow}
        {fableRow}
        {creditRow}
      </Box>
    )

    return (
      <Box flexDirection="column">
        <Box flexDirection="row" alignItems="flex-start" gap={1}>
          {toggle}
          {body}
        </Box>
        {rem?.error && (
          <Text dimColor size="caption">
            {rem.error}
            {rem.fable || rem.credits ? '（前回の値を表示）' : ''}
          </Text>
        )}
      </Box>
    )
  })
}
