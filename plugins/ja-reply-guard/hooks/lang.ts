// 返答が「英語だらけ」か、ユーザーが英語を求めているかを判定する純粋関数

/** 地の文の英字がこれ未満の文章は判定しない（短い返答は対象外） */
export const MIN_LATIN_LETTERS = 80

/** 地の文の日本語文字の割合（日本語文字 ÷（日本語文字＋英字））がこれ未満なら英語だらけ */
export const MAX_JAPANESE_RATIO = 0.15

/** プロンプトが英語で書かれているとみなす、地の文の英字の下限 */
export const MIN_PROMPT_LATIN_LETTERS = 20

/** プロンプトの地の文に日本語文字がこれ以上あれば、日本語のプロンプトとみなす */
export const MIN_PROMPT_JAPANESE = 2

/** 地の文の文字数 */
export type ProseStats = {
  /** ひらがな・カタカナ・漢字の数 */
  japanese: number
  /** A-Z / a-z の数 */
  latin: number
}

const JAPANESE = /[぀-ゟ゠-ヿㇰ-ㇿ㐀-䶿一-鿿豈-﫿ｦ-ﾟ]/gu
const LATIN = /[A-Za-z]/g

/** 行単位で消す・置き換える、地の文ではない部分 */
const INLINE_PATTERNS: readonly RegExp[] = [
  // インラインコード（`a` や ``a`b``）。開閉は同じ長さのバッククォート列で、より長い列の一部ではない
  /(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)/g,
  // HTML タグ
  /<\/?[A-Za-z][^>\n]*>/g,
  // URL
  /\b[A-Za-z][A-Za-z0-9+.-]*:\/\/\S+/g,
  // メールアドレス
  /\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b/g,
  // ファイルパス（区切りを含むもの）
  /(?:~|\.{1,2})?[/\\]?(?:[\w.@-]+[/\\])+[\w.@-]*/g,
  // 拡張子付きのファイル名（register.ts など）
  /\b[\w-]+\.[A-Za-z][A-Za-z0-9]{0,5}\b/g,
  // snake_case・camelCase・PascalCase の識別子
  /\b\w*_\w*\b/g,
  /\b[a-z]+[A-Z]\w*\b/g,
  /\b[A-Z][a-z]+[A-Z]\w*\b/g,
  // コマンドのオプション（--force、-v）
  /(?:^|\s)--?[A-Za-z][\w-]*/g,
]

/**
 * コードブロック・インラインコード・URL・ファイルパス・識別子・引用（`>` の行）を除いた地の文を返す
 */
export function stripNonProse(text: string): string {
  const kept: string[] = []
  let fence: string | undefined

  for (const line of text.split('\n')) {
    const opener = /^\s*(`{3,}|~{3,})/.exec(line)?.[1]
    if (fence !== undefined) {
      // 閉じるフェンスは開いたものと同じ文字で、同じ長さ以上
      if (opener !== undefined && opener[0] === fence[0] && opener.length >= fence.length) fence = undefined
      continue
    }
    if (opener !== undefined) {
      fence = opener
      continue
    }
    // 引用（ツール出力の貼り付けなど）
    if (/^\s*>/.test(line)) continue

    let prose = line.replace(/\[([^\]\n]*)\]\([^)\n]*\)/g, '$1')
    for (const pattern of INLINE_PATTERNS) prose = prose.replace(pattern, ' ')
    kept.push(prose)
  }

  return kept.join('\n')
}

/** 文字列の日本語文字と英字の数を数える */
export function measure(text: string): ProseStats {
  return {
    japanese: text.match(JAPANESE)?.length ?? 0,
    latin: text.match(LATIN)?.length ?? 0,
  }
}

/** 地の文の統計（コードなどを除いた後） */
export function proseStats(text: string): ProseStats {
  return measure(stripNonProse(text))
}

/**
 * 返答が「英語だらけ」か
 *
 * 地の文に英字が {@link MIN_LATIN_LETTERS} 以上あり、日本語文字の割合が {@link MAX_JAPANESE_RATIO} 未満のとき true。
 * 短い返答や、英単語が混じっているだけの日本語は false。
 */
export function isEnglishHeavy(text: string): boolean {
  const { japanese, latin } = proseStats(text)
  if (latin < MIN_LATIN_LETTERS) return false

  return japanese / (japanese + latin) < MAX_JAPANESE_RATIO
}

/** 英語での返答を明示的に求める言い回し */
const ASKS_FOR_ENGLISH: readonly RegExp[] = [
  /英語で(?:答|返|書|回|説明|話|教|お願い|頼|記述|出力|レス|やり取り|会話)/,
  /英語に(?:して|直|訳|翻訳|変)/,
  /英訳/,
  /英文で/,
  /\b(?:in|into|to)\s+English\b/i,
  /\bEnglish\s+(?:only|please)\b/i,
  /\b(?:speak|use|write)\s+English\b/i,
]

/**
 * プロンプトが英語での返答を明示的に求めているか
 *
 * コードブロックや引用の中の「英語で答えて」は、貼り付けた文字列でありユーザーの指示ではないので見ない。
 */
export function asksForEnglish(prompt: string): boolean {
  const prose = stripNonProse(prompt)

  return ASKS_FOR_ENGLISH.some(pattern => pattern.test(prose))
}

/**
 * プロンプトが英語で書かれているか
 *
 * 地の文に日本語文字がほぼ無く（{@link MIN_PROMPT_JAPANESE} 未満）、英字が {@link MIN_PROMPT_LATIN_LETTERS} 以上あるとき true。
 * 日本語の依頼に英語のログを貼っただけのものは、日本語文字があるので false。
 */
export function isEnglishPrompt(prompt: string): boolean {
  const { japanese, latin } = proseStats(prompt)

  return japanese < MIN_PROMPT_JAPANESE && latin >= MIN_PROMPT_LATIN_LETTERS
}

/** ユーザーが英語での返答を求めている（明示している、または英語で書いている）か */
export function userWantsEnglish(prompt: string): boolean {
  return asksForEnglish(prompt) || isEnglishPrompt(prompt)
}
