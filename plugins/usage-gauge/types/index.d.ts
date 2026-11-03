/** 使用率と、枠がリセットされる時刻（ISO 8601） */
export type UsageWindow = { percent: number; resetsAt?: string }

/** クレジット（extra usage）の使用額と月の上限（米ドル） */
export type Credits = {
  used: number
  limit?: number
  percent?: number
  enabled: boolean
}

/** 公式 API（$.session.usage()）から取った値 */
export type Official = {
  ctxTokens?: number
  ctxWindow?: number
  ctxPercent?: number
  fiveHour?: UsageWindow
  sevenDay?: UsageWindow
}

/** 非公式の OAuth 使用量 API から取った値 */
export type Remote = {
  fable?: UsageWindow
  credits?: Credits
  fiveHour?: UsageWindow
  sevenDay?: UsageWindow
  error?: string
}

declare module 'claude-code' {
  interface PluginState {
    'usage-gauge': {
      official: Shaped<Official | null>
      remote: Shaped<Remote | null>
      /** 残り時間の表示を進めるための現在時刻（ミリ秒） */
      now: number
      /** 折りたたみ状態。null は「$.store の値に従う」 */
      collapsed: boolean | null
    }
  }
}
