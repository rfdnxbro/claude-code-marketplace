// $ を使わない純粋な処理（入力の解釈・候補の絞り込み・frontmatter の解析）

import type { SkillDoc, SkillField } from '../types'
import { JA_DESCRIPTIONS } from './ja-descriptions.ts'
import type { JaEntry } from './ja-descriptions.ts'

/** 候補として扱うコマンドの形（$.command.list() の要素と同じ） */
export type CommandLike = {
  name: string
  description: string
  source: string
  plugin?: string
}

/**
 * 入力欄の先頭トークン（`/` の後ろ、空白まで）を返す。
 * `/` で始まらなければ undefined。
 */
export function slashQuery(text: string): string | undefined {
  if (!text.startsWith('/')) return undefined
  const match = /^\/(\S*)/.exec(text)

  return match?.[1] ?? ''
}

/** `plugin:skill` のコロンより後ろ（コロンが無ければ全体） */
export function shortName(name: string): string {
  const at = name.lastIndexOf(':')

  return at < 0 ? name : name.slice(at + 1)
}

/**
 * 入力中のトークンに一致するコマンドを、一致の強さ順に最大 limit 件返す。
 * 完全一致 → コロンの後ろの完全一致 → 前方一致 → コロンの後ろの前方一致。
 * 同じ強さの中では一覧（typeahead）の順を保つ。
 */
export function matchCommands<T extends CommandLike>(
  list: readonly T[],
  query: string,
  limit: number,
): T[] {
  const q = query.toLowerCase()
  if (q === '') return []

  const rank = (name: string): number => {
    const full = name.toLowerCase()
    const short = shortName(full)
    if (full === q) return 0
    if (short === q) return 1
    if (full.startsWith(q)) return 2
    if (short.startsWith(q)) return 3

    return -1
  }

  return list
    .map((command, order) => ({ command, order, rank: rank(command.name) }))
    .filter(hit => hit.rank >= 0)
    .sort((a, b) => a.rank - b.rank || a.order - b.order)
    .slice(0, limit)
    .map(hit => hit.command)
}

/** 作業ディレクトリから根までの各ディレクトリ（近い順。ホームはユーザー設定として別に見るので除く） */
export function projectDirs(start: string, home: string): string[] {
  const dirs: string[] = []
  let dir = start
  for (let i = 0; i < 64; i++) {
    if (dir !== home) dirs.push(dir)
    const parent = dir.replace(/\/[^/]*$/, '') || '/'
    if (parent === dir) break
    dir = parent
  }

  return dirs
}

/** $.command.list() の source から出どころの表示を作る */
export function originOfCommand(command: CommandLike, indexed?: string): string {
  if (command.source === 'plugin') {
    return `plugin: ${command.plugin ?? command.name.split(':')[0]}`
  }
  if (command.source === 'builtin') return 'builtin'
  if (command.source === 'mcp') return 'mcp'

  // user はユーザーとプロジェクトを区別しないので、索引で分かればそちらを使う
  return indexed ?? 'user'
}

/** skill.prompt の source から出どころの表示を作る */
export function originOfSkillSource(source: string, pluginName?: string): string {
  switch (source) {
    case 'userSettings':
      return 'user'
    case 'projectSettings':
      return 'project'
    case 'policySettings':
      return 'policy'
    case 'plugin':
      return pluginName ? `plugin: ${pluginName}` : 'plugin'
    case 'built-in':
      return 'builtin'
    case 'syncedSkills':
      return 'synced'
    default:
      return source
  }
}

// ---------------------------------------------------------------------------
// 説明の日本語訳

/** 組み込みのコマンドとスキルの出どころ */
export const BUILTIN = 'builtin'

/** 改行や連続する空白の違いを無視して比べる（SKILL.md の折り返しと一覧の説明を同じに扱う） */
function squash(text: string): string {
  return text.replace(/\s+/g, ' ').trim()
}

/** patternOf で作った正規表現（訳文の表は変わらないので、元の文字列ごとに使い回す） */
const patterns = new Map<string, RegExp>()

/** `{}` を可変部分とみなした正規表現（空白は squash 済みの文字列に合わせる） */
function patternOf(text: string): RegExp {
  const cached = patterns.get(text)
  if (cached) return cached
  const parts = squash(text)
    .split('{}')
    .map(part => part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  const pattern = new RegExp(`^${parts.join('(.+?)')}$`)
  patterns.set(text, pattern)

  return pattern
}

/** 訳文の `{}` に原文から取った可変部分を順に入れる */
function fill(template: string, values: readonly string[]): string {
  let i = 0

  return template.replace(/\{\}/g, () => values[i++] ?? '')
}

/** コマンド名の持ち主（`plugin:name` ならプラグイン名、コロンが無ければ組み込み） */
function ownerOfName(name: string): string {
  const at = name.indexOf(':')

  return at < 0 ? BUILTIN : name.slice(0, at)
}

/**
 * 説明の日本語訳を返す。owner は説明の出どころ（組み込みなら BUILTIN、プラグインならその名前）。
 * 訳が無いとき、出どころが訳の対象と違うとき、原文が訳の元にした英語と一致しない
 * （Claude Code の更新で説明が変わった）ときは undefined を返す。
 * すでに訳文になっている説明（command.describe で書き換えた後の一覧の説明）はそのまま返す。
 */
export function translateDescription(
  name: string,
  description: string | undefined,
  owner: string | undefined,
  table: Readonly<Record<string, readonly JaEntry[]>> = JA_DESCRIPTIONS,
): string | undefined {
  if (description === undefined || owner === undefined || owner !== ownerOfName(name)) return undefined
  const entries = Object.prototype.hasOwnProperty.call(table, name) ? table[name] : undefined
  if (!entries) return undefined

  const text = squash(description)
  for (const entry of entries) {
    const match = patternOf(entry.en).exec(text)
    if (match) return fill(entry.ja, match.slice(1))
  }
  for (const entry of entries) {
    if (patternOf(entry.ja).test(text)) return description
  }

  return undefined
}

/** 訳があれば訳を、無ければ元の説明を返す */
export function localizeDescription(
  name: string,
  description: string | undefined,
  owner: string | undefined,
  table?: Readonly<Record<string, readonly JaEntry[]>>,
): string | undefined {
  return translateDescription(name, description, owner, table) ?? description
}

/** $.command.list() の要素から説明の出どころを決める（ユーザーと MCP のものは訳さない） */
export function ownerOfCommand(command: CommandLike): string | undefined {
  if (command.source === 'builtin') return BUILTIN
  if (command.source === 'plugin') return command.plugin ?? ownerOfName(command.name)

  return undefined
}

/**
 * command.describe の provider（`{ plugin: 'engine' }` か `<名前>@<マーケットプレイス>`）から出どころを決める。
 * Anthropic 提供のプラグインと同じ名前でも、Anthropic のマーケットプレイス以外から入ったものは
 * `<名前>@<マーケットプレイス>` のまま返し、訳の対象にしない
 */
export function ownerOfProvider(provider: { plugin: string }): string {
  if (provider.plugin === 'engine') return BUILTIN
  const at = provider.plugin.indexOf('@')
  if (at < 0) return provider.plugin
  const name = provider.plugin.slice(0, at)
  const marketplace = provider.plugin.slice(at + 1)
  const official = Object.prototype.hasOwnProperty.call(ANTHROPIC_MARKETPLACES, name)
    ? ANTHROPIC_MARKETPLACES[name]
    : undefined
  if (official && !official.includes(marketplace)) return provider.plugin

  return name
}

/** skill.prompt の source から説明の出どころを決める */
export function ownerOfSkillRun(skill: string, source: string, pluginName?: string): string | undefined {
  if (source === 'built-in') return BUILTIN
  if (source === 'plugin') return pluginName ?? ownerOfName(skill)
  // 同期スキルは `anthropic-skills:<name>` の名前で届く
  if (source === 'syncedSkills' && skill.includes(':')) return ownerOfName(skill)

  return undefined
}

/**
 * 訳の対象にする Anthropic 提供のプラグイン（plugin.json の author が Anthropic のもの）と、
 * それを配るマーケットプレイス（`inline` は Claude Desktop・claude.ai のアカウントから配られるもの）
 */
export const ANTHROPIC_MARKETPLACES: Readonly<Record<string, readonly string[]>> = {
  'anthropic-skills': ['inline'],
  'code-review': ['claude-plugins-official'],
  'commit-commands': ['claude-plugins-official'],
  'cowork-plugin-management': ['inline', 'knowledge-work-plugins'],
}

/**
 * 訳の対象にする Anthropic 提供のプラグインの名前。組み込み（BUILTIN）とあわせて、未訳を数える範囲にもなる。
 * $.command.list() にはマーケットプレイスが含まれないので、右ペインと未訳の数え方は名前だけで判定する
 */
export const ANTHROPIC_PLUGINS: readonly string[] = Object.keys(ANTHROPIC_MARKETPLACES)

/** 訳の対象の出どころか */
export function isTranslatable(owner: string | undefined): boolean {
  return owner === BUILTIN || (owner !== undefined && ANTHROPIC_PLUGINS.includes(owner))
}

/**
 * 日本語が主体の説明か。もともと日本語の説明は訳さない。
 * 日本語の文字（ひらがな・カタカナ・漢字）1文字は英単語1語ほどの情報を持つので、2倍に数えて英字の数と比べる。
 * 英語が主体の説明に日本語の語が混じっているだけなら false（未訳として数える）
 */
export function isMostlyJapanese(text: string): boolean {
  const japanese = text.match(/[\u3040-\u30ff\u4e00-\u9fff]/g)?.length ?? 0
  const latin = text.match(/[A-Za-z]/g)?.length ?? 0

  return japanese > 0 && japanese * 2 >= latin
}

/** 日本語訳が無く、英語のまま表示しているコマンド */
export type Untranslated = { name: string; source: string; plugin?: string; description: string }

/**
 * コマンド一覧のうち、訳の対象なのに訳が使えないもの（訳が無い、または英語の原文が
 * 同梱時と一致しない）を返す。説明が空のもの、もともと日本語のものは数えない
 */
export function findUntranslated(
  list: readonly CommandLike[],
  table?: Readonly<Record<string, readonly JaEntry[]>>,
): Untranslated[] {
  return list
    .filter(command => {
      const owner = ownerOfCommand(command)
      if (!isTranslatable(owner) || command.description.trim() === '' || isMostlyJapanese(command.description)) {
        return false
      }

      return translateDescription(command.name, command.description, owner, table) === undefined
    })
    .map(command => ({
      name: command.name,
      source: command.source,
      ...(command.plugin === undefined ? {} : { plugin: command.plugin }),
      description: command.description,
    }))
}

/** 未訳の一覧を、Claude にそのまま貼って訳を頼める形にする */
export function formatUntranslated(items: readonly Untranslated[]): string {
  if (items.length === 0) return '未訳の説明はありません。'
  const json = JSON.stringify(items, null, 2)

  return [
    `skill-preview の未訳の説明が ${items.length} 件あります。`,
    'plugins/skill-preview/hooks/ja-descriptions.ts の JA_DESCRIPTIONS に、各コマンドの { en, ja } を追加・更新してください。',
    'en には下の description をそのまま写してください。ja は README の「訳文の文体」に従ってください:',
    '- 文末はである調（「〜する。」）にし、ですます調（〜します。〜です。）は使わない。すべての文を「。」で終える',
    '- 体言止めにせず、名詞で終わる文は動詞で終える（例: 「〜の指針と基本。」→「〜の指針と基本を示す。」）。文末に括弧書きの補足を置くときも、括弧の前の本文は動詞で終える',
    '- 起動条件を含む長い説明も要約せず忠実に訳し、「トリガー:」などのラベルとトリガー語の列挙も残す',
    '- 固有名詞・コマンド名・ツール名・ファイル名は原文のままにする',
    '終わったら plugins/skill-preview/.claude-plugin/plugin.json の version を上げてください。',
    '',
    '```json',
    json,
    '```',
  ].join('\n')
}

// ---------------------------------------------------------------------------
// frontmatter

type Frontmatter = { entries: [string, string][]; body: string }

/** 引用符を外す（二重引用符の中の `\"` `\\` と、一重引用符の中の `''` も戻す） */
function unquote(value: string): string {
  const v = value.trim()
  if (v.length >= 2 && v[0] === '"' && v.endsWith('"')) return v.slice(1, -1).replace(/\\(["\\])/g, '$1')
  if (v.length >= 2 && v[0] === "'" && v.endsWith("'")) return v.slice(1, -1).replace(/''/g, "'")

  return v
}

/**
 * SKILL.md を frontmatter と本文に分ける。
 * frontmatter は表示に使うだけなので、トップレベルの `key: value`、
 * ブロックスカラー（`|` `>`）、リスト（`- item`）だけを簡易に読む。
 */
export function parseFrontmatter(source: string): Frontmatter {
  const text = source.replace(/^\uFEFF/, '').replace(/\r\n?/g, '\n')
  const open = /^---[ \t]*\n/.exec(text)
  if (!open) return { entries: [], body: text }

  const rest = text.slice(open[0].length)
  const close = /^---[ \t]*$/m.exec(rest)
  if (!close) return { entries: [], body: text }

  const lines = rest.slice(0, close.index).split('\n')
  const body = rest.slice(close.index + close[0].length).replace(/^\n+/, '')
  const entries: [string, string][] = []

  const isContinuation = (line: string | undefined): line is string =>
    line !== undefined && (line.trim() === '' || /^\s/.test(line))

  for (let i = 0; i < lines.length; i++) {
    const match = /^([A-Za-z0-9_-]+):(.*)$/.exec(lines[i] ?? '')
    if (!match) continue

    const key = match[1] ?? ''
    const raw = (match[2] ?? '').trim()
    const block: string[] = []
    for (let next = lines[i + 1]; isContinuation(next); next = lines[i + 1]) {
      block.push(next)
      i++
    }
    while (block.length > 0 && (block[block.length - 1] ?? '').trim() === '') block.pop()

    let value: string
    if (/^[|>][-+]?$/.test(raw)) {
      const indent = Math.min(
        ...block.filter(line => line.trim() !== '').map(line => line.length - line.trimStart().length),
      )
      const inner = block.map(line => line.slice(Number.isFinite(indent) ? indent : 0))
      value = raw[0] === '|' ? inner.join('\n') : inner.join(' ').replace(/\s+/g, ' ')
    } else if (raw === '' && block.length > 0) {
      value = block
        .map(line => line.trim().replace(/^-\s*/, ''))
        .filter(line => line !== '')
        .map(unquote)
        .join(', ')
    } else {
      value = [unquote(raw), ...block.map(line => line.trim())].filter(Boolean).join(' ')
    }
    entries.push([key, value.trim()])
  }

  return { entries, body }
}

/** 制御文字を落とす（Markdown が受け付けるのは改行とタブだけ） */
export function clean(text: string): string {
  // eslint-disable-next-line no-control-regex
  return text.replace(/\r\n?/g, '\n').replace(/[\x00-\x08\x0b-\x1f\x7f]/g, '')
}

const MAX_BODY = 60000
const MAX_FIELD = 400

/** frontmatter のオブジェクト（skill.prompt の e.frontmatter）を表示用の項目にする */
export function fieldsOf(entries: readonly (readonly [string, unknown])[]): {
  description?: string
  fields: SkillField[]
} {
  let description: string | undefined
  const fields: SkillField[] = []
  for (const [key, value] of entries) {
    if (value === undefined || value === null) continue
    const text = clean(
      typeof value === 'string'
        ? value
        : Array.isArray(value)
          ? value.map(String).join(', ')
          : typeof value === 'object'
            ? JSON.stringify(value)
            : String(value),
    )
    if (key === 'description') description = text
    else if (key !== 'name') fields.push({ key, value: text.slice(0, MAX_FIELD) })
  }

  return { description, fields }
}

/** SKILL.md の中身から表示用の SkillDoc を作る */
export function docFromFile(name: string, origin: string, path: string, source: string): SkillDoc {
  const { entries, body } = parseFrontmatter(source)
  const { description, fields } = fieldsOf(entries)
  const trimmed = clean(body).trim()

  return {
    name,
    origin,
    path,
    description,
    fields,
    body:
      trimmed.length > MAX_BODY
        ? `${trimmed.slice(0, MAX_BODY)}\n\n…（${trimmed.length - MAX_BODY} 文字省略）`
        : trimmed,
  }
}
