import { expect, test } from 'claude-code/testing'
import type { Engine } from 'claude-code/testing'
import type { On, PromptOrigin, TurnStepToolUse } from 'claude-code'

import { REWRITE_PROMPT, STEP_NOTE } from './register.ts'

const ENGLISH =
  'Let me look at the configuration first, then I will check how the handler reads the values and whether the cache is refreshed.'
const JAPANESE = 'まず設定を確認してから、ハンドラーが値をどう読むか、キャッシュが更新されるかを調べます。'
const TOOL: readonly TurnStepToolUse[] = [{ name: 'Read', input: { file_path: '/a' } }]

/** エンジン役が記録したもの */
type Recorded = {
  /** $.session.append で差し込まれたテキスト */
  appends: string[]
  /** $.prompt.submit で送られたプロンプト（テストからの送信を含む） */
  submits: { text: string; origin: PromptOrigin }[]
  toasts: string[]
  /** 次の turn.step でモデルが返すもの */
  reply: { answer: string; toolUses: readonly TurnStepToolUse[] }
}

/** エンジン役の hook を差し込む */
function engine(on: On): Recorded {
  const rec: Recorded = { appends: [], submits: [], toasts: [], reply: { answer: '', toolUses: [] } }

  on('session.append', (_$, e, next) => {
    for (const block of e.message.content) if (block.type === 'text' && typeof block.text === 'string') rec.appends.push(block.text)

    return next(e)
  })
  on('prompt.submit', (_$, e) => {
    rec.submits.push({ text: e.text, origin: e.origin })

    return { text: e.text }
  })
  on('ui.toast', (_$, e) => {
    rec.toasts.push(e.text)

    return { value: undefined }
  })
  on('turn.start', (_$, e) => ({ turnId: e.turnId }))
  on('turn.step', async function* (_$, e) {
    return { turnId: e.turnId, index: e.index, answer: rec.reply.answer, toolUses: rec.reply.toolUses, stopReason: 'end_turn', usage: null }
  })
  on('turn.complete', (_$, e) => ({ text: e.answer }))

  return rec
}

/** モデルのステップを1回進める */
async function step($: Engine, rec: Recorded, turnId: string, index: number, answer: string, toolUses = TOOL, agentId?: string) {
  rec.reply = { answer, toolUses }
  const stream = $.turn.step({ turnId, index, model: 'opus', messageCount: 1, ...(agentId === undefined ? {} : { agentId }) })
  for await (const _chunk of stream) {
    // 中身は読まない
  }

  return stream.result
}

/** ターンを終える */
function complete($: Engine, turnId: string, answer: string, reason: 'answer' | 'aborted' = 'answer', agentId?: string) {
  return $.turn.complete({
    answer,
    durationMs: 1,
    isAborted: reason === 'aborted',
    turnId,
    reason,
    ...(agentId === undefined ? {} : { agentId }),
  })
}

/** 人が入力欄から送ったプロンプト */
function typed($: Engine, text: string) {
  return $.prompt.submit({ text, wait: false, origin: { kind: 'composer' } })
}

/** mod が待たずに送ったものが届くのを待つ */
async function settle() {
  for (let i = 0; i < 20; i++) await Promise.resolve()
}

/** 送られたプロンプトのうち、この mod のもの */
function rewrites(rec: Recorded): string[] {
  return rec.submits.filter(s => s.origin.kind === 'plugin').map(s => s.text)
}

test('ターンの途中で英語だらけになると、日本語の指示を1回だけ差し込む', async ($, on) => {
  const rec = engine(on)
  await typed($, 'この関数を直して')
  await $.turn.start({ text: 'この関数を直して', turnId: 't1' })

  await step($, rec, 't1', 0, ENGLISH)
  await step($, rec, 't1', 1, ENGLISH)

  expect(rec.appends).toEqual([STEP_NOTE])
  expect(rec.toasts.length).toBe(1)
})

test('短い英語のつぶやきも、ターン内で積み重なると差し込む', async ($, on) => {
  const rec = engine(on)
  await $.turn.start({ text: '', turnId: 't1' })

  await step($, rec, 't1', 0, 'Let me check the file.')
  expect(rec.appends).toEqual([])
  await step($, rec, 't1', 1, 'Now I will read the tests to see how this is used.')
  await step($, rec, 't1', 2, 'The handler looks fine, so the bug must be in the caller.')

  expect(rec.appends).toEqual([STEP_NOTE])
})

test('日本語の途中経過や、ツール呼び出しのない最後のステップでは差し込まない', async ($, on) => {
  const rec = engine(on)
  await $.turn.start({ text: '', turnId: 't1' })

  await step($, rec, 't1', 0, JAPANESE)
  await step($, rec, 't1', 1, ENGLISH, [])

  expect(rec.appends).toEqual([])
})

test('最終回答が英語だらけなら書き直しを依頼し、その書き直しのターンには再依頼しない', async ($, on) => {
  const rec = engine(on)
  await typed($, 'クロージャとは？')
  await $.turn.start({ text: 'クロージャとは？', turnId: 't1' })
  await step($, rec, 't1', 0, ENGLISH, [])
  await complete($, 't1', ENGLISH)
  await settle()

  expect(rewrites(rec)).toEqual([REWRITE_PROMPT])
  expect(rec.toasts.length).toBe(1)

  // 書き直しのターンも英語のままだった
  await $.turn.start({ text: REWRITE_PROMPT, turnId: 't2' })
  await step($, rec, 't2', 0, ENGLISH, [])
  await complete($, 't2', ENGLISH)
  await settle()

  expect(rewrites(rec)).toEqual([REWRITE_PROMPT])
})

test('書き直しの後の普通のターンでは、また依頼する', async ($, on) => {
  const rec = engine(on)
  await $.turn.start({ text: '', turnId: 't1' })
  await complete($, 't1', ENGLISH)
  await settle()
  await $.turn.start({ text: REWRITE_PROMPT, turnId: 't2' })
  await complete($, 't2', JAPANESE)

  await typed($, '次の質問です')
  await $.turn.start({ text: '次の質問です', turnId: 't3' })
  await complete($, 't3', ENGLISH)
  await settle()

  expect(rewrites(rec)).toEqual([REWRITE_PROMPT, REWRITE_PROMPT])
})

test('ユーザーが英語を求めたときは何もしない', async ($, on) => {
  const rec = engine(on)
  for (const prompt of ['Answer in English only: what is a closure?', 'クロージャについて英語で答えて', 'What is a closure in programming languages?']) {
    await typed($, prompt)
    await $.turn.start({ text: prompt, turnId: prompt })
    await step($, rec, prompt, 0, ENGLISH)
    await complete($, prompt, ENGLISH)
    await settle()

    expect(rec.appends).toEqual([])
    expect(rewrites(rec)).toEqual([])
  }
})

test('短い返答・日本語の返答・中断されたターンには何もしない', async ($, on) => {
  const rec = engine(on)
  const cases: [string, 'answer' | 'aborted'][] = [
    ['Done.', 'answer'],
    [JAPANESE, 'answer'],
    [ENGLISH, 'aborted'],
  ]
  for (const [i, [answer, reason]] of cases.entries()) {
    await $.turn.start({ text: '', turnId: `t${i}` })
    await complete($, `t${i}`, answer, reason)
  }
  await settle()

  expect(rewrites(rec)).toEqual([])
})

test('サブエージェントのステップと回答は対象外', async ($, on) => {
  const rec = engine(on)
  await $.turn.start({ text: '', turnId: 'main' })
  await $.turn.start({ text: 'investigate', turnId: 'sub', agentId: 'a1' })
  await step($, rec, 'sub', 0, ENGLISH, TOOL, 'a1')
  await complete($, 'sub', ENGLISH, 'answer', 'a1')
  await settle()

  expect(rec.appends).toEqual([])
  expect(rewrites(rec)).toEqual([])
})

test('始まりを見ていないターン（リロード直後など）には何もしない', async ($, on) => {
  const rec = engine(on)
  await step($, rec, 'unknown', 0, ENGLISH)
  await complete($, 'unknown', ENGLISH)
  await settle()

  expect(rec.appends).toEqual([])
  expect(rewrites(rec)).toEqual([])
})
