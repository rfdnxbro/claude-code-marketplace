import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Official, UsageWindow } from '../types'
import {
  clampPercent,
  creditsDetail,
  elapsedRatio,
  FIVE_HOUR_MS,
  formatPercent,
  formatRemaining,
  formatTokens,
  gaugeColor,
  gaugeSvg,
  gaugeText,
  parseRemote,
  SEVEN_DAY_MS,
} from './format'

// 非公式の OAuth 使用量 API（Fable 週次枠とクレジットを埋める用途）
const USAGE_URL = 'https://api.anthropic.com/api/oauth/usage'
// 公式値と残り時間の表示を更新する間隔
const POLL_MS = 60_000
// 非公式 API を呼ぶ最短の間隔（短いと 429 が返り続ける）
const MIN_FETCH_GAP_MS = 5 * 60_000
// 取得に失敗して Retry-After も無いとき、次に試すまでの間隔
const RETRY_MS = 15 * 60_000
// 認証情報が無い環境で、もう一度試すまでの間隔
const NO_AUTH_RETRY_MS = 60 * 60_000
const STORE_KEY = 'collapsed'
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
const collapsed = atom({ plugin: 'usage-gauge', key: 'collapsed' } as const, false)

// 次に非公式 API を呼んでよい時刻（モジュール変数: リロードで初期化されてよい）
let nextFetchAt = 0

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
 * 失敗したら前回の値（$.state に残っている）にエラーを添え、しばらく呼ばない。
 */
async function refreshRemote($: EngineInterface): Promise<void> {
  const t = await $.clock.now()
  if (t < nextFetchAt) return
  // 呼ぶ前に先へ進めておき、取得中に重ねて呼ばないようにする
  nextFetchAt = t + MIN_FETCH_GAP_MS
  let error = '非公式API取得失敗'
  try {
    const auth = await $.session.authorize()
    if (!auth) {
      // API キーやゲートウェイでは取れない。エラーは出さず、しばらく呼ばない
      nextFetchAt = t + NO_AUTH_RETRY_MS
      return
    }
    const res = await $.http.fetch(USAGE_URL, {
      headers: { 'anthropic-beta': 'oauth-2025-04-20' },
      auth: auth.handle,
    })
    if (res.ok) {
      const fresh = parseRemote(JSON.parse(res.text))
      await update($, remote, () => fresh)
      return
    }
    error = `非公式API取得失敗 (${res.status})`
    // Retry-After（秒）があればそれに従う。429 では "0" が返るので、そのときは既定の間隔にする
    const sec = Number(res.headers['retry-after'])
    nextFetchAt = t + (sec > 0 ? Math.max(MIN_FETCH_GAP_MS, sec * 1000) : RETRY_MS)
  } catch {
    nextFetchAt = t + RETRY_MS
  }
  await update($, remote, prev => ({ ...prev, error }))
}

async function tick($: EngineInterface): Promise<void> {
  const t = await $.clock.now()
  await update($, now, () => t)
  // 片方が失敗しても、もう片方は更新する
  await Promise.allSettled([refreshOfficial($), refreshRemote($)])
}

/** 開閉状態を $.store から $.state に写す（$.state は /clear などで初期値に戻るため） */
async function loadCollapsed($: EngineInterface): Promise<void> {
  const stored = (await $.store.get(STORE_KEY)) === true
  await update($, collapsed, () => stored)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const r = await next(e)
    await loadCollapsed($)
    // 起動を待たせないよう、初回の取得はタイマーに回す
    $.clock.after(1, () => void tick($))
    $.clock.every(POLL_MS, () => void tick($))
    return r
  })

  // /clear・/resume・/branch の後は session.start が来ず $.state が初期値に戻るので、ここで埋め直す
  on('classic.SessionStart', async ($, e, next) => {
    const r = await next(e)
    await loadCollapsed($)
    // 非公式 API の値が消えていたら、間引きを待たずに取り直す
    if (!(await read($, remote))) nextFetchAt = 0
    $.clock.after(1, () => void tick($))
    return r
  })

  on('session.measure', async ($, e, next) => {
    const r = await next(e)
    await refreshOfficial($)
    return r
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey) return next(e)

    const els = $.ui.resolve(e)
    const { Box, Text, Button } = els
    const isDesktop = e.surface === 'desktop'
    const off = await read($, official)
    const rem = await read($, remote)
    // 1分ごとに進む時刻を購読して、残り時間を描き直す
    const t = await read($, now)
    const isCollapsed = await read($, collapsed)

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
          const toggled = await update($, collapsed, v => !v)
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
      if ('Svg' in els) {
        // デスクトップは細いバーを SVG で描く（Box の背景色だと行どうしがつながって見える）
        const { Svg } = els
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
    const creditRow = row('credit', 'クレジット', credits?.percent, credits ? creditsDetail(credits) : '')

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
