// ja-reply-guard: Claude の返答が英語だらけになったとき、日本語で書くよう促す mod
//
// - ターンの途中: ステップの可視テキスト（ターン内の累積）が英語だらけなら、
//   以降は日本語で書くよう指示する行を会話に差し込む（1ターンに1回まで）
// - ターンの最後: 最終回答が英語だらけなら、日本語で書き直す依頼を送る
//   （人が次のプロンプトを送るまで1回まで。書き直しのターンにまた依頼してループしないため）
// - ユーザーが英語を求めたとき（明示した、または英語で書いた）とサブエージェントは対象外
import type { PromptOrigin, Register } from 'claude-code'

import { isEnglishHeavy, userWantsEnglish } from './lang.ts'

/** ターンの途中で差し込む指示 */
export const STEP_NOTE = '以降の返答は日本語で書いてください。コード・コマンド・識別子は原文のままで構いません。'

/** ターンの最後に送る書き直しの依頼 */
export const REWRITE_PROMPT =
  '直前の返答が英語になっていました。同じ内容を日本語で書き直してください。コード・コマンド・識別子は原文のままで構いません。'

/** 人が送ったとみなすプロンプトの出どころ */
const HUMAN_ORIGINS: ReadonlySet<PromptOrigin['kind']> = new Set(['composer', 'bridge', 'sdk', 'channel', 'slack-ping'])

/** メインの会話の、いま進んでいるターン */
type TurnInfo = {
  /** このターンで指示を差し込んだか */
  isNoted: boolean
  /** このターンのステップの可視テキストを連結したもの */
  prose: string
}

export const register: Register = on => {
  /** 人が最後に送ったプロンプト（スラッシュコマンドは引数） */
  let lastPrompt = ''
  /** 人が次のプロンプトを送るまでに、まだ書き直しを依頼してよいか */
  let canRequestRewrite = true
  let turn: TurnInfo | undefined

  on('prompt.submit', ($, e, next) => {
    if (HUMAN_ORIGINS.has(e.origin.kind)) {
      lastPrompt = e.command ? e.command.args : e.text
      canRequestRewrite = true
    }

    return next(e)
  })

  on('turn.start', ($, e, next) => {
    if (e.agentId === undefined) turn = { isNoted: false, prose: '' }

    return next(e)
  })

  on('turn.step', async function* ($, e, next) {
    const response = yield* next(e)
    if (e.agentId !== undefined || turn === undefined) return response

    turn.prose += `\n${response.answer}`
    // 最後のステップ（ツール呼び出しなし）はターンの最後の書き直しに任せる
    if (turn.isNoted || response.toolUses.length === 0) return response
    if (userWantsEnglish(lastPrompt) || !isEnglishHeavy(turn.prose)) return response

    turn.isNoted = true
    await $.session.append({ message: { type: 'user', content: [{ type: 'text', text: STEP_NOTE }] } })
    $.ui.toast('返答が英語になっていたので、日本語で書くよう指示しました')

    return response
  })

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    if (e.agentId !== undefined) return result

    const info = turn
    turn = undefined
    // 始まりを見ていないターン（リロード直後など）は、書き直しのターンかもしれないので触らない
    if (info === undefined || !canRequestRewrite || e.reason !== 'answer') return result
    if (userWantsEnglish(lastPrompt) || !isEnglishHeavy(e.answer)) return result

    canRequestRewrite = false
    // セッションが空いてから新しいターンとして始まる。待つとこのターンが終わらないので待たない
    void $.prompt.submit({ text: REWRITE_PROMPT })
    $.ui.toast('返答が英語になっていたので、日本語での書き直しを依頼しました')

    return result
  })
}
