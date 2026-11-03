// Claude Desktop アプリが持つ組み込みコマンドの公式の日本語訳を、アプリ内のファイル（asar）から取り出すための純粋な処理。
// 公式訳はリポジトリに同梱せず、使う人のマシンにあるアプリから実行時に読む（register.tsx の loadOfficial）。
// アプリの内部ファイルに依存するので、形式が変わって読めないときはどれも undefined か空を返し、自前訳に任せる

/** asar を探す場所（macOS の Claude Desktop） */
export function asarCandidates(home: string): string[] {
  const relative = 'Claude.app/Contents/Resources/ion-dist.asar'

  return [`/Applications/${relative}`, ...(home ? [`${home}/Applications/${relative}`] : [])]
}

/**
 * `od -An -tu4 -N16 <asar>` の出力（4 つの 32 ビット整数）から、ヘッダーの JSON の長さと
 * ファイル本体の始まり（各ファイルの offset の基準）を求める
 */
export function asarLayout(odOutput: string): { headerLength: number; base: number } | undefined {
  const numbers = odOutput.trim().split(/\s+/).map(Number)
  const [first, pickleSize, , headerLength] = numbers
  if (numbers.length !== 4 || first !== 4 || !pickleSize || !headerLength || headerLength > pickleSize) {
    return undefined
  }

  return { headerLength, base: 8 + pickleSize }
}

/** asar のヘッダー（`head -c` で読んだ先頭部分）から、`i18n/<locale>.json` のバイト範囲を求める */
export function localeFileRange(
  headerText: string,
  base: number,
  locale: string,
): { start: number; end: number } | undefined {
  const open = headerText.indexOf('{')
  const close = headerText.lastIndexOf('}')
  if (open < 0 || close < open) return undefined
  try {
    const header = JSON.parse(headerText.slice(open, close + 1)) as {
      files?: Record<string, { files?: Record<string, { size?: unknown; offset?: unknown }> }>
    }
    const entry = header.files?.i18n?.files?.[`${locale}.json`]
    const offset = Number(entry?.offset)
    const size = Number(entry?.size)
    if (!Number.isFinite(offset) || !Number.isFinite(size) || size <= 0) return undefined

    return { start: base + offset, end: base + offset + size }
  } catch {
    return undefined
  }
}

/** 公式訳の定義（コマンド一覧のキー・英語・ID）を探すための grep の正規表現（ERE） */
export const MESSAGES_PATTERN =
  'btw:\\{defaultMessage:"([^"\\\\]|\\\\.)*",id:"[^"]+"\\}(,[A-Za-z]+:\\{defaultMessage:"([^"\\\\]|\\\\.)*",id:"[^"]+"\\})*'

/** コマンド一覧の定義の1件 */
export type OfficialMessage = { key: string; en: string; id: string }

/** JavaScript の文字列リテラルの中身を戻す（読めなければそのまま） */
function unescapeLiteral(text: string): string {
  try {
    return JSON.parse(`"${text}"`) as string
  } catch {
    return text
  }
}

/** grep で見つけた定義のうち、コマンド一覧のもの（いちばん件数の多いもの）を読む */
export function parseMessages(grepOutput: string): OfficialMessage[] {
  let best: OfficialMessage[] = []
  for (const line of grepOutput.split('\n')) {
    const found = [...line.matchAll(/([A-Za-z]+):\{defaultMessage:"((?:[^"\\]|\\.)*)",id:"([^"]+)"\}/g)].map(
      match => ({ key: match[1] ?? '', en: unescapeLiteral(match[2] ?? ''), id: match[3] ?? '' }),
    )
    if (found.length > best.length) best = found
  }
  // コマンド一覧なら btw を含み、ある程度の件数がある
  return best.length >= 5 && best.some(message => message.key === 'btw') ? best : []
}

/** ERE の特殊文字をエスケープする */
function escapeExtended(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')
}

/** 訳文の JSON（`"<ID>": "<訳>"`）から、指定した ID の行を探すための grep の正規表現（ERE） */
export function idsPattern(ids: readonly string[]): string {
  return `"(${ids.map(escapeExtended).join('|')})": "([^"\\\\]|\\\\.)*"`
}

/** `grep -b -o` の出力（`<バイト位置>:"<ID>": "<訳>"`）のうち、範囲内のものを ID → 訳にする */
export function parseTranslations(
  grepOutput: string,
  range: { start: number; end: number },
): Record<string, string> {
  const out: Record<string, string> = {}
  for (const line of grepOutput.split('\n')) {
    const match = /^(\d+):"([^"]+)": "((?:[^"\\]|\\.)*)"$/.exec(line)
    if (!match) continue
    const offset = Number(match[1])
    if (offset < range.start || offset >= range.end) continue
    out[match[2] ?? ''] = unescapeLiteral(match[3] ?? '')
  }

  return out
}

/** 定義のキー（camelCase）をコマンド名（kebab-case）にする（`addDir` → `add-dir`） */
export function commandNameOfKey(key: string): string {
  return key.replace(/[A-Z]/g, char => `-${char.toLowerCase()}`)
}

/** コマンド名 → 公式の日本語訳 */
export type OfficialLabels = Record<string, string>

/** 定義と訳から、コマンド名 → 公式の日本語訳を作る（訳が無いもの・空のものは入れない） */
export function officialLabelsOf(
  messages: readonly OfficialMessage[],
  translations: Readonly<Record<string, string>>,
): OfficialLabels {
  const out: OfficialLabels = {}
  for (const message of messages) {
    const ja = translations[message.id]?.trim()
    if (ja) out[commandNameOfKey(message.key)] = ja
  }

  return out
}

/** asar の場所と、取り直しが要るかを判断するための大きさ・更新時刻 */
export type AsarStat = { path: string; size: number; mtimeMs: number }

/** $.store に置く公式訳のキャッシュ */
export type OfficialCache = AsarStat & { labels: OfficialLabels }

/** キャッシュが同じ asar（場所・大きさ・更新時刻）から取ったものか */
export function isOfficialCacheFor(value: unknown, asar: AsarStat): value is OfficialCache {
  if (!value || typeof value !== 'object') return false
  const cache = value as Partial<OfficialCache>
  return (
    cache.path === asar.path &&
    cache.size === asar.size &&
    cache.mtimeMs === asar.mtimeMs &&
    !!cache.labels &&
    typeof cache.labels === 'object'
  )
}
