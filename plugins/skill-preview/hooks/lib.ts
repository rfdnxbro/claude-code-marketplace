// $ を使わない純粋な処理（入力の解釈・候補の絞り込み・出どころと訳の判定・frontmatter の解析）

import type { SkillDoc, SkillField } from '../types'
import { JA_DESCRIPTIONS } from './ja-descriptions.ts'
import type { JaEntry } from './ja-descriptions.ts'
import type { OfficialLabels } from './official.ts'

/** 候補として扱うコマンドの形（$.command.list() の要素と同じ） */
export type CommandLike = {
  name: string
  description: string
  source: string
  plugin?: string
}

/** command.describe で受け取ったコマンド（description は書き換える前の原文） */
export type DescribedCommand = CommandLike & { isHidden: boolean }

/** 訳文の表（テストで差し替えられるようにする） */
type Table = Readonly<Record<string, readonly JaEntry[]>>

function hasOwn(object: object, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(object, key)
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

// ---------------------------------------------------------------------------
// 出どころ（command.describe と skill.prompt の情報は入口で CommandLike の source / plugin に揃える）

/** 訳の対象にする Anthropic 提供のプラグイン（plugin.json の author が Anthropic のもの） */
export const ANTHROPIC_PLUGINS: readonly string[] = [
  'anthropic-skills',
  'code-review',
  'commit-commands',
  'cowork-plugin-management',
]

/** command.describe の provider（組み込みは `engine`、プラグインは `<名前>@<マーケットプレイス>`）を source / plugin にする */
export function sourceOfProvider(provider: { plugin: string }): Pick<CommandLike, 'source' | 'plugin'> {
  if (provider.plugin === 'engine') return { source: 'builtin' }
  // ユーザー・プロジェクトのコマンドは `user` / `project` で届く
  if (provider.plugin === 'user' || provider.plugin === 'project') return { source: 'user' }

  return { source: 'plugin', plugin: provider.plugin.split('@')[0] ?? provider.plugin }
}

/** skill.prompt の source（`built-in`、`plugin`、`syncedSkills`、`userSettings` など）を source / plugin にする */
export function sourceOfSkillRun(
  skill: string,
  source: string,
  pluginName?: string,
): Pick<CommandLike, 'source' | 'plugin'> {
  if (source === 'built-in') return { source: 'builtin' }
  if (source === 'mcp') return { source: 'mcp' }
  // 同期スキルは `anthropic-skills:<name>` の名前で届く
  const plugin = pluginName ?? (skill.includes(':') ? skill.slice(0, skill.indexOf(':')) : undefined)
  if ((source === 'plugin' || source === 'syncedSkills') && plugin) return { source: 'plugin', plugin }

  return { source: 'user' }
}

/** 出どころの表示（user はユーザーとプロジェクトを区別しないので、索引で分かればそちらを使う） */
export function originOfCommand(command: CommandLike, indexed?: string): string {
  if (command.source === 'plugin') return `plugin: ${command.plugin ?? command.name.split(':')[0]}`
  if (command.source === 'builtin' || command.source === 'mcp') return command.source

  return indexed ?? 'user'
}

/** 訳の対象なら出どころ（組み込みは `builtin`、Anthropic 提供のプラグインはその名前）を、対象外なら undefined を返す */
export function ownerOfCommand(command: CommandLike): string | undefined {
  if (command.source === 'builtin') return command.name.includes(':') ? undefined : 'builtin'
  if (command.source !== 'plugin') return undefined
  const plugin = command.plugin ?? command.name.split(':')[0] ?? ''

  return ANTHROPIC_PLUGINS.includes(plugin) && command.name.startsWith(`${plugin}:`) ? plugin : undefined
}

// ---------------------------------------------------------------------------
// 説明の日本語訳

/** 改行や連続する空白の違いを無視して比べる（SKILL.md の折り返しと一覧の説明を同じに扱う） */
function squash(text: string): string {
  return text.replace(/\s+/g, ' ').trim()
}

/** `{}` を可変部分とみなして英語の原文と照合し、一致すれば可変部分を入れた訳を返す */
function translate(description: string, entries: readonly JaEntry[]): string | undefined {
  const text = squash(description)
  for (const entry of entries) {
    const parts = squash(entry.en)
      .split('{}')
      .map(part => part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    const match = new RegExp(`^${parts.join('(.+?)')}$`).exec(text)
    if (!match) continue
    let i = 1

    return entry.ja.replace(/\{\}/g, () => match[i++] ?? '')
  }

  return undefined
}

/**
 * 表示する日本語の説明を選ぶ。公式訳（組み込みだけ。Claude Desktop アプリが持つもので、手を加えずに返す）→
 * 同梱の自前訳（英語の原文が同梱時と一致するときだけ）の順。どちらも使えなければ undefined（元の説明を出す）
 */
export function japaneseDescription(
  command: CommandLike,
  official: Readonly<OfficialLabels> = {},
  table: Table = JA_DESCRIPTIONS,
): string | undefined {
  const owner = ownerOfCommand(command)
  if (owner === undefined) return undefined
  if (owner === 'builtin' && hasOwn(official, command.name)) return official[command.name]
  const entries = hasOwn(table, command.name) ? table[command.name] : undefined

  return entries ? translate(command.description, entries) : undefined
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
 * 訳の対象なのに訳が使えないもの（公式訳が無く、同梱の訳も無いか英語の原文が同梱時と一致しない）を返す。
 * 説明が空のもの、もともと日本語のものは数えない
 */
export function findUntranslated(
  list: readonly CommandLike[],
  official?: Readonly<OfficialLabels>,
  table?: Table,
): Untranslated[] {
  return list
    .filter(
      command =>
        ownerOfCommand(command) !== undefined &&
        command.description.trim() !== '' &&
        !isMostlyJapanese(command.description) &&
        japaneseDescription(command, official, table) === undefined,
    )
    .map(command => ({
      name: command.name,
      source: command.source,
      ...(command.plugin === undefined ? {} : { plugin: command.plugin }),
      description: command.description,
    }))
}

/**
 * $.command.list() と、command.describe で受け取ったコマンドを合わせる。
 * $.command.list() に無い組み込み（`/btw`、`/help` など）も補い、隠しコマンドは外す。
 * 説明は command.describe で受け取った書き換え前の原文を使う（訳と未訳の判定を原文で行うため）
 */
export function mergeCommands(
  list: readonly CommandLike[],
  described: Readonly<Record<string, DescribedCommand>>,
): CommandLike[] {
  const merged: CommandLike[] = []
  const listed = new Set<string>()
  for (const command of list) {
    listed.add(command.name)
    const known = hasOwn(described, command.name) ? described[command.name] : undefined
    if (known?.isHidden) continue
    merged.push(known ? { ...command, description: known.description } : command)
  }
  for (const { isHidden, ...command } of Object.values(described)) {
    if (!isHidden && !listed.has(command.name)) merged.push(command)
  }

  return merged
}

/** 未訳の一覧を、Claude にそのまま貼って訳を頼める形にする */
export function formatUntranslated(items: readonly Untranslated[]): string {
  if (items.length === 0) return '未訳の説明はありません。'

  return [
    `skill-preview の未訳の説明が ${items.length} 件あります。`,
    'plugins/skill-preview/README.md の「訳文の更新手順」に従って、plugins/skill-preview/hooks/ja-descriptions.ts に訳を足してください。',
    '',
    '```json',
    JSON.stringify(items, null, 2),
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
