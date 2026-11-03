import { describe, expect, test } from 'claude-code/testing'

import {
  asksForEnglish,
  isEnglishHeavy,
  isEnglishPrompt,
  MAX_JAPANESE_RATIO,
  MIN_LATIN_LETTERS,
  MIN_PROMPT_LATIN_LETTERS,
  proseStats,
  stripNonProse,
  userWantsEnglish,
} from './lang.ts'

/** 英字だけで n 文字の地の文（単語は5文字＋空白） */
function englishLetters(n: number): string {
  const words: string[] = []
  for (let left = n; left > 0; left -= 5) words.push('abcde'.slice(0, Math.min(5, left)))

  return words.join(' ')
}

const ENGLISH_REPLY =
  'A closure is a function that remembers the variables from the scope where it was defined, even after that scope has finished running.'

describe('stripNonProse', () => {
  test('コードブロックを除く（閉じていないものも末尾まで）', () => {
    const text = ['説明です', '```ts', 'const value = compute()', '```', 'おわり', '~~~', 'unterminated code'].join('\n')
    expect(stripNonProse(text)).toBe('説明です\nおわり')
  })

  test('閉じるフェンスは開いたものより短いと閉じない', () => {
    const text = ['````md', '```', 'inner text', '```', '````', '後'].join('\n')
    expect(stripNonProse(text)).toBe('後')
  })

  test('インラインコード・URL・パス・ファイル名・識別子・オプションを除く', () => {
    const stats = proseStats(
      'これは `someFunction()` と https://example.com/very/long/path と ~/work/app/src と register.ts と snake_case_name と camelCaseName と --force です',
    )
    expect(stats.latin).toBe(0)
  })

  test('内側にバッククォートを含むインラインコードを最後まで除く', () => {
    const id = 'longEnglishIdentifierRepeatedManyTimes'
    expect(proseStats(`説明です。 \`\`${id}\`${id}\`\` おわり`).latin).toBe(0)
    expect(isEnglishHeavy(`説明です。 \`\`${id} \`${id} ${id}\`\` おわり`)).toBe(false)
  })

  test('パスやファイル名に似た英語（and/or、e.g、end.Next）も除く（判定が甘くなる方向）', () => {
    expect(proseStats('and/or と I/O と e.g と end.Next').latin).toBe(0)
    // ピリオドの後に空白がある普通の英文は残る（use the cache Then read it の 21 文字）
    expect(proseStats('use the cache. Then read it').latin).toBe(21)
  })

  test('引用の行を除き、リンクは表示テキストを残す', () => {
    expect(stripNonProse('> Error: something failed badly\n[説明](https://example.com)')).toBe('説明')
  })
})

describe('isEnglishHeavy', () => {
  test('英語の返答は英語だらけ', () => {
    expect(isEnglishHeavy(ENGLISH_REPLY)).toBe(true)
  })

  test('英単語が混じった日本語は対象外', () => {
    expect(
      isEnglishHeavy(
        'React の useEffect は副作用を扱うための hook です。dependency array を空にすると mount 時に1回だけ実行されます。cleanup function を返すと unmount 時に呼ばれます。',
      ),
    ).toBe(false)
  })

  test('コードが英語でも地の文が日本語なら対象外', () => {
    const text = ['クロージャの例です。', '```js', 'function makeCounter() { let count = 0; return () => count++ }', '```', '外側の変数を覚えています。'].join('\n')
    expect(isEnglishHeavy(text)).toBe(false)
  })

  test('英字が下限未満なら判定しない', () => {
    expect(isEnglishHeavy(englishLetters(MIN_LATIN_LETTERS - 1))).toBe(false)
    expect(isEnglishHeavy(englishLetters(MIN_LATIN_LETTERS))).toBe(true)
  })

  test('日本語の割合の境界', () => {
    // 英字 170 文字に対して日本語 30 文字なら割合 0.15（しきい値ちょうど）で対象外、29 文字なら英語だらけ
    const latin = englishLetters(170)
    const atLimit = `${latin} ${'あ'.repeat(30)}`
    const below = `${latin} ${'あ'.repeat(29)}`
    expect(30 / (30 + 170)).toBe(MAX_JAPANESE_RATIO)
    expect(isEnglishHeavy(atLimit)).toBe(false)
    expect(isEnglishHeavy(below)).toBe(true)
  })

  test('空の返答は対象外', () => {
    expect(isEnglishHeavy('')).toBe(false)
  })
})

describe('ユーザーが英語を求めているか', () => {
  test('英語での返答を明示した依頼', () => {
    expect(asksForEnglish('Answer in English only: what is a closure?')).toBe(true)
    expect(asksForEnglish('クロージャについて英語で答えて')).toBe(true)
    expect(asksForEnglish('この文を英訳して')).toBe(true)
    expect(asksForEnglish('README を英語にして')).toBe(true)
  })

  test('コードブロック・インラインコード・引用の中の英語指定はユーザーの指示ではない', () => {
    expect(asksForEnglish('次の文字列が何を意味するか説明して:\n```\n英語で答えて\n```')).toBe(false)
    expect(asksForEnglish('`Answer in English` というテンプレートの意味は？')).toBe(false)
    expect(asksForEnglish('> 英語で答えてください\nというメールが来ました。どう返せばいい？')).toBe(false)
  })

  test('英語の話題に触れているだけなら明示ではない', () => {
    expect(asksForEnglish('英語のエラーメッセージの意味を教えて')).toBe(false)
    expect(asksForEnglish('English というクラス名を直して')).toBe(false)
  })

  test('英語で書かれたプロンプト', () => {
    expect(isEnglishPrompt('What is a closure in programming languages?')).toBe(true)
    expect(isEnglishPrompt(englishLetters(MIN_PROMPT_LATIN_LETTERS))).toBe(true)
    expect(isEnglishPrompt(englishLetters(MIN_PROMPT_LATIN_LETTERS - 1))).toBe(false)
  })

  test('短い英語や、日本語の依頼に英語のログを貼ったものは英語のプロンプトではない', () => {
    expect(isEnglishPrompt('continue')).toBe(false)
    expect(isEnglishPrompt('ok')).toBe(false)
    expect(isEnglishPrompt(`このエラーを直して\nTypeError: Cannot read properties of undefined (reading 'map') at render`)).toBe(false)
  })

  test('userWantsEnglish はどちらかで true', () => {
    expect(userWantsEnglish('Answer in English only: what is a closure?')).toBe(true)
    expect(userWantsEnglish('クロージャとは？')).toBe(false)
    expect(userWantsEnglish('')).toBe(false)
  })
})
