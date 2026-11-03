// ja-reply-guard: Claude の返答が英語だらけになったとき、日本語で書くよう促す mod
//
// - ターンの途中: ステップの可視テキスト（ターン内の累積）が英語だらけなら、
//   以降は日本語で書くよう指示する行を会話に差し込む（1ターンに1回まで）
// - ターンの最後: 最終回答が英語だらけなら、日本語で書き直す依頼を送る
//   （書き直し依頼から始まったターンには再依頼しない）
// - ユーザーが英語を求めたとき（明示した、または英語で書いた）とサブエージェントは対象外
import type { PromptOrigin, Register } from 'claude-code'

import { isEnglishHeavy, userWantsEnglish } from './lang.ts'

const MOD = 'ja-reply-guard'

/** ターンの途中で差し込む指示 */
export const STEP_NOTE = '以降の返答は日本語で書いてください。コード・コマンド・識別子は原文のままで構いません。'

/** ターンの最後に送る書き直しの依頼 */
export const REWRITE_PROMPT =
  '直前の返答が英語になっていました。同じ内容を日本語で書き直してください。コード・コマンド・識別子は原文のままで構いません。'

/** 人が送ったとみなすプロンプトの出どころ */
const HUMAN_ORIGINS: ReadonlySet<PromptOrigin['kind']> = new Set(['composer', 'bridge', 'sdk', 'channel', 'slack-ping'])

/** メインの会話の、いま進んでいるターン */
type TurnInfo = {
  turnId: string
  /** この mod の書き直し依頼から始まったターンか */
  isRewrite: boolean
  /** このターンで指示を差し込んだか */
  isNoted: boolean
  /** このターンのステップの可視テキストを連結したもの */
  prose: string
}

export const register: Register = on => {
  /** 人が最後に送ったプロンプト（スラッシュコマンドは引数） */
  let lastPrompt = ''
  /** 次に始まるメインのターンが書き直し依頼のものか */
  let isRewriteNext = false
  let turn: TurnInfo | undefined

  on('prompt.submit', ($, e, next) => {
    const origin = e.origin
    if (origin.kind === 'plugin' && origin.name === MOD) isRewriteNext = true
    else if (HUMAN_ORIGINS.has(origin.kind)) lastPrompt = e.command ? e.command.args : e.text

    return next(e)
  })

  on('turn.start', ($, e, next) => {
    if (e.agentId === undefined) {
      turn = {
        turnId: e.turnId,
        isRewrite: isRewriteNext || e.text.includes(REWRITE_PROMPT),
        isNoted: false,
        prose: '',
      }
      isRewriteNext = false
    }

    return next(e)
  })

  on('turn.step', async function* ($, e, next) {
    const response = yield* next(e)
    if (e.agentId !== undefined || turn?.turnId !== e.turnId) return response

    turn.prose += `\n${response.answer}`
    // 最後のステップ（ツール呼び出しなし）はターンの最後の書き直しに任せる
    if (turn.isNoted || response.toolUses.length === 0) return response
    if (userWantsEnglish(lastPrompt) || !isEnglishHeavy(turn.prose)) return response

    turn.isNoted = true
    const appended = await $.session.append({
      message: { type: 'user', content: [{ type: 'text', text: STEP_NOTE }] },
    })
    $.ui.toast(appended.deny ? `日本語の指示を差し込めませんでした: ${appended.deny}` : '返答が英語になっていたので、日本語で書くよう指示しました')

    return response
  })

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    if (e.agentId !== undefined) return result

    const info = turn?.turnId === e.turnId ? turn : undefined
    turn = undefined
    // 始まりを見ていないターン（リロード直後など）は書き直しかどうか分からないので触らない
    if (info === undefined || info.isRewrite || e.reason !== 'answer') return result
    if (userWantsEnglish(lastPrompt) || !isEnglishHeavy(e.answer)) return result

    // セッションが空いてから新しいターンとして始まる。待つとこのターンが終わらないので待たない
    void $.prompt.submit({ text: REWRITE_PROMPT }).then(sent => {
      if (sent.drop !== undefined) $.ui.toast(`書き直しを依頼できませんでした: ${sent.drop}`)
    })
    $.ui.toast('返答が英語になっていたので、日本語での書き直しを依頼しました')

    return result
  })
}
