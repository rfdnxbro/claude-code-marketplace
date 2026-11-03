import { expect, mock, test } from 'claude-code/testing'
import type { Engine } from 'claude-code/testing'
import type { On } from 'claude-code'

import { creditsDetail, elapsedRatio, formatRemaining, formatTokens, gaugeColor, parseRemote } from './format'

const NOW = Date.parse('2026-11-03T06:00:00Z')

const BAND = {
  plugin: 'usage-gauge',
  component: 'AbovePrompt',
  props: {
    hasSurvey: false,
    isWorking: false,
    maxRows: 20,
    bodyColumns: 140,
    scroll: { offset: 0, bodyRows: 20 },
    view: {},
  },
} as const

// 公式 API（$.session.usage()）の値
const USAGE = {
  startedAt: NOW,
  context: { tokens: 401_900, window: 1_000_000, percent: 40 },
  rateLimits: [
    { kind: 'five_hour', percentUsed: 5, resetsAt: '2026-11-03T10:12:30Z' },
    { kind: 'seven_day', percentUsed: 32, resetsAt: '2026-11-06T04:00:00Z' },
  ],
  cost: { usd: 1.5 },
}

// 非公式 API の応答（実機で確認したキー構造に合わせた架空の値）
const BODY = {
  five_hour: { utilization: 6, resets_at: '2026-11-03T10:12:00Z' },
  seven_day: { utilization: 33, resets_at: '2026-11-06T04:00:00Z' },
  extra_usage: { is_enabled: true, monthly_limit: 20000, used_credits: 0, utilization: 0, decimal_places: 2 },
  limits: [
    { kind: 'session', percent: 6, resets_at: '2026-11-03T10:12:00Z', scope: null },
    { kind: 'weekly_all', percent: 33, resets_at: '2026-11-06T04:00:00Z', scope: null },
    {
      kind: 'weekly_scoped',
      percent: 4,
      resets_at: '2026-11-06T04:00:00Z',
      scope: { model: { id: null, display_name: 'Fable' }, surface: null },
    },
  ],
  spend: {
    used: { amount_minor: 0, currency: 'USD', exponent: 2 },
    limit: { amount_minor: 20000, currency: 'USD', exponent: 2 },
    percent: 0,
    enabled: true,
  },
}

/** エンジン役の hook を差し込み、セッションを始めて初回取得まで進める */
async function start($: Engine, on: On, fetchStatus = 200) {
  const clock = mock.clock(on, { now: NOW })
  mock.store(on)
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.usage', () => ({ value: USAGE }))
  on('session.authorize', () => ({ value: { handle: 'h', kind: 'bearer' } }))
  on('http.fetch', () => ({
    value: {
      status: fetchStatus,
      ok: fetchStatus === 200,
      headers: {},
      text: fetchStatus === 200 ? JSON.stringify(BODY) : '',
    },
  }))
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })
  await clock.advance(1)
  return clock
}

test('全5項目のゲージを描く（どのサーフェスでも）', async ($, on) => {
  await start($, on)
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface })
    for (const label of ['コンテキスト', '5時間', '週間', '週間 Fable', 'クレジット']) {
      expect((await ui.find({ type: 'Text', text: label }))?.text).toBe(label)
    }
    expect((await ui.find({ type: 'Text', text: '401.9k/1M' }))?.text).toBe('401.9k/1M')
    expect((await ui.find({ type: 'Text', text: 'あと4時間12分' }))?.text).toBe('あと4時間12分')
    expect((await ui.find({ type: 'Text', text: '$0/$200' }))?.text).toBe('$0/$200')
    // 5時間・週間は公式値を優先する
    expect((await ui.find({ type: 'Text', text: '5%' }))?.text).toBe('5%')
    expect((await ui.find({ type: 'Text', text: '32%' }))?.text).toBe('32%')
    expect((await ui.find({ type: 'Text', text: '4%' }))?.text).toBe('4%')
    await ui.unmount()
  }
})

test('トグルで1行の要約に折りたたみ、もう一度押すと開く', async ($, on) => {
  await start($, on)
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface })
    await ui.press({ key: 'toggle' })
    const summary = await ui.find({ type: 'Text', text: /^ctx / })
    expect(summary?.text).toBe('ctx 40% · 5h 5% · 週 32% · Fable 4% · $0/$200')
    expect(await ui.find({ type: 'Text', text: 'コンテキスト' })).toBeUndefined()
    await ui.press({ key: 'toggle' })
    expect((await ui.find({ type: 'Text', text: 'コンテキスト' }))?.text).toBe('コンテキスト')
    await ui.unmount()
  }
})

test('非公式 API が失敗したら公式値だけで描き、薄字で知らせる', async ($, on) => {
  await start($, on, 500)
  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  expect((await ui.find({ type: 'Text', text: /非公式API取得失敗/ }))?.text).toBe('非公式API取得失敗 (500)')
  expect((await ui.find({ type: 'Text', text: '40%' }))?.text).toBe('40%')
  expect((await ui.find({ type: 'Text', text: '—' }))?.text).toBe('—')
  await ui.unmount()
})

test('アンケートが出ている間は帯を譲る', async ($, on) => {
  // エンジン役: 帯を譲られたらアンケートを描く
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>survey</Text>
  })
  await start($, on)
  const ui = await $.ui.mount({ ...BAND, surface: 'desktop', props: { ...BAND.props, hasSurvey: true } })
  expect(await ui.find({ type: 'Text', text: 'コンテキスト' })).toBeUndefined()
  expect((await ui.find({ type: 'Text', text: 'survey' }))?.text).toBe('survey')
  await ui.unmount()
})

test('狭い幅でも全項目を1列で描く', async ($, on) => {
  await start($, on)
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal', props: { ...BAND.props, bodyColumns: 60 } })
  expect((await ui.find({ type: 'Text', text: 'クレジット' }))?.text).toBe('クレジット')
  expect((await ui.find({ type: 'Text', text: '週間 Fable' }))?.text).toBe('週間 Fable')
  await ui.unmount()
})

test('表示用の関数', async () => {
  expect(gaugeColor(69)).toBe('success')
  expect(gaugeColor(70)).toBe('warning')
  expect(gaugeColor(90)).toBe('error')
  expect(formatTokens(401_900)).toBe('401.9k')
  expect(formatTokens(1_000_000)).toBe('1M')
  expect(formatRemaining('2026-11-06T04:00:00Z', NOW)).toBe('あと2日22時間')
  expect(formatRemaining('2026-11-03T06:12:30Z', NOW)).toBe('あと12分')
  // 5時間枠の残り4時間12分 → 経過は 48 / 300
  expect(Math.round((elapsedRatio('2026-11-03T10:12:00Z', NOW, 5 * 3600_000) ?? 0) * 300)).toBe(48)
  expect(creditsDetail({ used: 0, limit: 200, enabled: true })).toBe('$0/$200')
  expect(creditsDetail({ used: 0, enabled: false })).toBe('$0 無効')
})

test('非公式 API の応答から Fable 枠とクレジットを読む', async () => {
  const r = parseRemote(BODY)
  expect(r.fable).toEqual({ percent: 4, resetsAt: '2026-11-06T04:00:00Z' })
  expect(r.credits).toEqual({ used: 0, limit: 200, percent: 0, enabled: true })
  expect(parseRemote({}).fable).toBeUndefined()
})
