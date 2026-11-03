// 返答が「英語だらけ」か、ユーザーが英語を求めているかを判定する純粋関数

/** 地の文の英字がこれ未満の文章は判定しない（短い返答は対象外） */
export const MIN_LATIN_LETTERS = 80

/** 地の文の日本語文字の割合（日本語文字 ÷（日本語文字＋英字））がこれ未満なら英語だらけ */
export const MAX_JAPANESE_RATIO = 0.15

/** プロンプトが英語で書かれているとみなす、地の文の英字の下限 */
export const MIN_PROMPT_LATIN_LETTERS = 20

/** プロンプトの地の文に日本語文字がこれ以上あれば、日本語のプロンプトとみなす */
export const MIN_PROMPT_JAPANESE = 2

const JAPANESE = /[぀-ゟ゠-ヿㇰ-ㇿ㐀-䶿一-鿿豈-﫿ｦ-ﾟ]/gu
const LATIN = /[A-Za-z]/g

/** 行の中で地の文から外す部分 */
const NON_PROSE: readonly RegExp[] = [
  // インラインコード
  /`[^`\n]+`/g,
  // URL
  /\b[A-Za-z][A-Za-z0-9+.-]*:\/\/\S+/g,
  // ファイルパス（区切りを含むもの）
  /(?:~|\.{1,2})?[/\\]?(?:[\w.@-]+[/\\])+[\w.@-]*/g,
  // 拡張子付きのファイル名（register.ts など）
  /\b[\w-]+\.[A-Za-z][A-Za-z0-9]{0,5}\b/g,
]

/** 英語での返答を明示的に求める言い回し */
const ASKS_FOR_ENGLISH = /英語で|英訳|英文で|\bin English\b/i

/** コードブロック・インラインコード・URL・ファイルパス・引用（`>` の行。ツール出力の貼り付けなど）を除いた地の文を返す */
export function stripNonProse(text: string): string {
  const kept: string[] = []
  let inFence = false

  for (const line of text.split('\n')) {
    if (/^\s*(```|~~~)/.test(line)) {
      inFence = !inFence
      continue
    }
    if (inFence || /^\s*>/.test(line)) continue

    kept.push(NON_PROSE.reduce((prose, pattern) => prose.replace(pattern, ' '), line))
  }

  return kept.join('\n')
}

/** 地の文（コードなどを除いた後）の日本語文字と英字の数 */
export function proseStats(text: string): { japanese: number; latin: number } {
  const prose = stripNonProse(text)

  return { japanese: prose.match(JAPANESE)?.length ?? 0, latin: prose.match(LATIN)?.length ?? 0 }
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

/** プロンプトが英語での返答を明示的に求めているか */
export function asksForEnglish(prompt: string): boolean {
  return ASKS_FOR_ENGLISH.test(prompt)
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
