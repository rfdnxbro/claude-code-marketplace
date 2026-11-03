// $ を使わない純粋な処理（入力の解釈・候補の絞り込み・frontmatter の解析）

import type { SkillDoc, SkillField } from '../types'

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

type Frontmatter = { entries: [string, string][]; body: string }

/** 引用符を外す */
function unquote(value: string): string {
  const v = value.trim()
  if (v.length >= 2 && ((v[0] === '"' && v.endsWith('"')) || (v[0] === "'" && v.endsWith("'")))) {
    return v.slice(1, -1)
  }

  return v
}

/**
 * SKILL.md を frontmatter と本文に分ける。
 * frontmatter は表示に使うだけなので、トップレベルの `key: value`、
 * ブロックスカラー（`|` `>`）、リスト（`- item`）だけを簡易に読む。
 */
export function parseFrontmatter(source: string): Frontmatter {
  const text = source.replace(/^﻿/, '').replace(/\r\n?/g, '\n')
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
