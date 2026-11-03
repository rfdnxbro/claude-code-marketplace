// skill-preview: 入力中の /スキル名 や実行されたスキルの SKILL.md を右ペインに表示する

import { atom, read, update } from 'claude-code'
import type { CommandInfo, EngineInterface, Register, Timer } from 'claude-code'

import type { PreviewView, SkillDoc } from '../types'
import {
  docFromFile,
  fieldsOf,
  matchCommands,
  originOfCommand,
  originOfSkillSource,
  shortName,
  slashQuery,
} from './lib.ts'

const PANE = 'skill-preview'
const TITLE = 'スキル'
/** 候補として並べる最大件数 */
const MAX_CANDIDATES = 6
/** キー入力が止まってから引きに行くまでの待ち（ミリ秒） */
const DEBOUNCE_MS = 60
/** $.store に覚えるパスの最大件数 */
const MAX_LEARNED = 500

const EMPTY: PreviewView = { mode: 'empty', candidates: [] }

// 値の形を変えたら shape のタグを変える（古い形の値は初期値扱いになる）
const view = atom({ plugin: 'skill-preview', key: 'view' } as const, EMPTY, {
  shape: 'view-1',
})
const opened = atom({ plugin: 'skill-preview', key: 'opened' } as const, false)

/** 名前 → SKILL.md の索引 */
type Entry = { path: string; origin: string }
type SkillIndex = {
  /** フルネーム（`grilling`、`eli5:eli5`、`frontend:review`）で引く */
  exact: Record<string, Entry>
  /** 同期スキルなど、コロンの後ろの名前だけで引く */
  bare: Record<string, Entry>
}

// モジュール変数はリロードで初期化されてよいものだけを置く
let index: SkillIndex = { exact: {}, bare: {} }
let learned: Record<string, string> = {}
let commands: CommandInfo[] = []
let ready: Promise<void> | undefined
let timer: Timer | undefined
let lastQuery: string | undefined
/** 後から終わった古い読み込みで表示を上書きしないための番号 */
let seq = 0
const docCache = new Map<string, { mtimeMs: number; text: string }>()

// ---------------------------------------------------------------------------
// 索引づくり（session.start で開始し、最初の検索で待つ）

async function listDir($: EngineInterface, dir: string) {
  try {
    return await $.fs.list(dir)
  } catch {
    return []
  }
}

/** ディレクトリか（シンボリックリンクはリンク先で判定） */
async function isDir($: EngineInterface, path: string, kind: string): Promise<boolean> {
  if (kind === 'dir') return true
  if (kind !== 'other') return false
  try {
    return (await $.fs.stat(path)).kind === 'dir'
  } catch {
    return false
  }
}

/** `<dir>/<name>/SKILL.md` を `<prefix><name>` として登録する */
async function addSkills(
  $: EngineInterface,
  table: Record<string, Entry>,
  dir: string,
  prefix: string,
  origin: string,
) {
  const entries = await listDir($, dir)
  const found = await Promise.all(
    entries
      .filter(entry => entry.kind !== 'file' && !entry.name.startsWith('.'))
      .map(async entry => {
        const path = `${dir}/${entry.name}/SKILL.md`
        try {
          return (await $.fs.exists(path)) ? { name: entry.name, path } : undefined
        } catch {
          return undefined
        }
      }),
  )
  for (const hit of found) {
    if (hit && !table[`${prefix}${hit.name}`]) {
      table[`${prefix}${hit.name}`] = { path: hit.path, origin }
    }
  }
}

/** `<dir>/**\/*.md` を `<prefix>sub:name` として登録する（深さ 3 まで） */
async function addCommands(
  $: EngineInterface,
  table: Record<string, Entry>,
  dir: string,
  prefix: string,
  origin: string,
  depth: number,
) {
  if (depth > 3) return
  for (const entry of await listDir($, dir)) {
    if (entry.name.startsWith('.')) continue
    const path = `${dir}/${entry.name}`
    if (entry.name.endsWith('.md') && entry.kind !== 'dir') {
      const name = `${prefix}${entry.name.slice(0, -3)}`
      if (!table[name]) table[name] = { path, origin }
    } else if (await isDir($, path, entry.kind)) {
      await addCommands($, table, path, `${prefix}${entry.name}:`, origin, depth + 1)
    }
  }
}

type InstalledPlugin = { scope?: string; projectPath?: string; installPath?: string }

/** installed_plugins.json の各プラグインのスキルとコマンドを登録する */
async function addPlugins(
  $: EngineInterface,
  table: Record<string, Entry>,
  configDir: string,
  cwd: string,
) {
  let installed: Record<string, InstalledPlugin[]> = {}
  try {
    const json = JSON.parse(await $.fs.read(`${configDir}/plugins/installed_plugins.json`))
    installed = json?.plugins ?? {}
  } catch {
    return
  }
  await Promise.all(
    Object.entries(installed).map(async ([key, list]) => {
      if (!Array.isArray(list) || list.length === 0) return
      // このプロジェクト向けのもの → ユーザー全体のもの → 先頭、の順に選ぶ
      const chosen =
        list.find(item => item.projectPath === cwd) ??
        list.find(item => item.scope === 'user') ??
        list[0]
      if (!chosen?.installPath) return
      const plugin = key.split('@')[0]
      const origin = `plugin: ${plugin}`
      await addSkills($, table, `${chosen.installPath}/skills`, `${plugin}:`, origin)
      await addCommands($, table, `${chosen.installPath}/commands`, `${plugin}:`, origin, 0)
    }),
  )
}

async function buildIndex($: EngineInterface): Promise<SkillIndex> {
  const home = (await $.env.get('HOME')) ?? ''
  const configDir = (await $.env.get('CLAUDE_CONFIG_DIR')) ?? `${home}/.claude`
  const cwd = await $.session.cwd()
  const built: SkillIndex = { exact: {}, bare: {} }

  // 先に登録したものが優先（プロジェクト → ユーザー → プラグイン）
  await addSkills($, built.exact, `${cwd}/.claude/skills`, '', 'project')
  await addCommands($, built.exact, `${cwd}/.claude/commands`, '', 'project', 0)
  await addSkills($, built.exact, `${configDir}/skills`, '', 'user')
  await addCommands($, built.exact, `${configDir}/commands`, '', 'user', 0)
  await addPlugins($, built.exact, configDir, cwd)

  // アカウントから同期されたスキル（anthropic-skills:* など）は名前の後ろだけで引く
  const syncedRoot = `${configDir}/skills/synced`
  for (const bucket of await listDir($, syncedRoot)) {
    if (bucket.name.startsWith('.')) continue
    await addSkills($, built.bare, `${syncedRoot}/${bucket.name}`, '', 'synced')
  }

  return built
}

async function prepare($: EngineInterface) {
  const stored = await $.store.get('paths')
  if (stored && typeof stored === 'object') learned = stored as Record<string, string>
  index = await buildIndex($)
}

async function ensureReady($: EngineInterface) {
  ready ??= prepare($).catch(() => {
    // 索引が作れなくても、覚えたパスと説明文だけで動く
  })
  await ready
}

// ---------------------------------------------------------------------------
// スキルの読み込み

function resolveEntry(name: string): Entry | undefined {
  const known = learned[name]
  const exact = index.exact[name]
  if (known) return { path: known, origin: exact?.origin ?? '' }
  if (exact) return exact

  return index.bare[shortName(name)]
}

/** ファイルを読む（更新時刻が変わっていなければキャッシュを使う） */
async function readCached($: EngineInterface, path: string): Promise<string> {
  const stat = await $.fs.stat(path)
  const cached = docCache.get(path)
  if (cached && cached.mtimeMs === stat.mtimeMs) return cached.text
  const text = await $.fs.read(path)
  docCache.set(path, { mtimeMs: stat.mtimeMs, text })

  return text
}

async function loadFile(
  $: EngineInterface,
  name: string,
  origin: string,
  path: string,
  fallback: SkillDoc,
): Promise<SkillDoc> {
  try {
    return docFromFile(name, origin, path, await readCached($, path))
  } catch (error) {
    return { ...fallback, path, error: `読み込めませんでした: ${String(error).slice(0, 200)}` }
  }
}

async function loadCommand($: EngineInterface, command: CommandInfo): Promise<SkillDoc> {
  const entry = resolveEntry(command.name)
  const origin = originOfCommand(command, entry?.origin || undefined)
  const fallback: SkillDoc = {
    name: command.name,
    origin,
    description: command.description || undefined,
    fields: [],
  }
  if (!entry) return fallback

  return loadFile($, command.name, origin, entry.path, fallback)
}

// ---------------------------------------------------------------------------
// 表示の更新

async function openOnce($: EngineInterface) {
  if (await read($, opened)) return
  await update($, opened, () => true)
  await $.ui.open({ id: PANE, title: TITLE })
}

/** 入力中のトークンから候補を引き、先頭をプレビューする */
async function showQuery($: EngineInterface, query: string) {
  const mine = ++seq
  await ensureReady($)
  commands = await $.command.list()
  const hits = matchCommands(commands, query, MAX_CANDIDATES)
  if (mine !== seq) return

  const first = hits[0]
  if (!first) {
    await update($, view, (current): PreviewView =>
      current.mode === 'empty' ? current : { mode: 'typing', query, candidates: [] },
    )
    return
  }

  const doc = await loadCommand($, first)
  if (mine !== seq) return
  await update($, view, (): PreviewView => ({
    mode: 'typing',
    query,
    candidates: hits.map(hit => ({
      name: hit.name,
      origin: originOfCommand(hit, resolveEntry(hit.name)?.origin || undefined),
    })),
    selected: first.name,
    doc,
  }))
  await openOnce($)
}

/** 候補の Button から別のスキルに切り替える */
async function pick($: EngineInterface, name: string) {
  const mine = ++seq
  const command = commands.find(item => item.name === name) ?? {
    name,
    description: '',
    source: 'user' as const,
  }
  const doc = await loadCommand($, command)
  if (mine !== seq) return
  await update($, view, (current): PreviewView => ({ ...current, selected: name, doc }))
}

type SkillRun = {
  skill: string
  path?: string
  source: string
  pluginName?: string
  frontmatter: Record<string, unknown>
}

/** スキルが実行されたときに、そのスキルを「実行中」として表示する */
async function showRun($: EngineInterface, run: SkillRun) {
  const mine = ++seq
  timer?.cancel()
  lastQuery = undefined

  const origin = originOfSkillSource(run.source, run.pluginName)
  const { description, fields } = fieldsOf(Object.entries(run.frontmatter ?? {}))
  const fallback: SkillDoc = { name: run.skill, origin, description, fields }
  let doc = fallback
  if (run.path) {
    if (learned[run.skill] !== run.path) {
      learned = Object.fromEntries(
        [...Object.entries(learned).filter(([key]) => key !== run.skill), [run.skill, run.path]].slice(
          -MAX_LEARNED,
        ),
      )
      await $.store.set('paths', learned)
    }
    doc = await loadFile($, run.skill, origin, run.path, fallback)
  }
  if (mine !== seq) return
  await update($, view, (): PreviewView => ({
    mode: 'running',
    candidates: [],
    selected: run.skill,
    doc,
  }))
  await openOnce($)
}

// ---------------------------------------------------------------------------

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'skill-preview',
      description: 'スキル説明ペインを開く（スキル名を渡すとそのスキルを表示）',
      argumentHint: '[スキル名]',
    })
    // 索引づくりは待たずに始める（最初の検索で待つ）
    void ensureReady($)

    return next(e)
  })

  on('command.run', { command: 'skill-preview' }, async ($, e) => {
    await update($, opened, () => true)
    await $.ui.open({ id: PANE, title: TITLE })
    const name = e.args.trim().replace(/^\//, '')
    if (name !== '') await showQuery($, name)

    return { text: 'スキル説明ペインを開きました。' }
  })

  // キー入力ごと（上限 50 ms）。ここではファイルを読まず、タイマーで後から引く
  on('prompt.edit', async ($, e, next) => {
    const box = await next(e)
    const query = slashQuery(box.text)
    if (query === undefined || query === '') {
      // `/` で始まらなくなったら直前の表示を残す
      lastQuery = undefined
      return box
    }
    if (query !== lastQuery) {
      lastQuery = query
      timer?.cancel()
      timer = $.clock.after(DEBOUNCE_MS, () => {
        void showQuery($, query)
      })
    }

    return box
  })

  on('skill.prompt', async ($, e, next) => {
    const result = await next(e)
    try {
      await showRun($, {
        skill: e.skill,
        path: e.path,
        source: e.source,
        pluginName: e.pluginName,
        frontmatter: e.frontmatter as Record<string, unknown>,
      })
    } catch {
      // 表示に失敗してもスキルの実行は止めない
    }

    return result
  })

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    // サブエージェントのターンでは切り替えない
    if (e.agentId !== undefined) return result
    await update($, view, (current): PreviewView =>
      current.mode === 'running' ? { ...current, mode: 'ran' } : current,
    )

    return result
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button, Markdown } = $.ui.resolve(e)
    const current = await read($, view)
    const doc = current.doc

    if (current.mode === 'empty') {
      return (
        <Box flexDirection="column">
          <Text dimColor>
            入力欄に「/」に続けてスキル名を入力すると、ここにそのスキルの SKILL.md を表示します。
          </Text>
        </Box>
      )
    }

    const status =
      current.mode === 'running'
        ? '▶ 実行中'
        : current.mode === 'ran'
          ? '✓ 直前に実行'
          : `入力中のプレビュー（/${current.query ?? ''}）`

    return (
      <Box flexDirection="column" gap={1}>
        <Box flexDirection="column">
          <Text color={current.mode === 'running' ? 'success' : undefined} dimColor={current.mode !== 'running'}>
            {status}
          </Text>
          {doc ? (
            <Text bold>
              /{doc.name} <Text dimColor>{doc.origin}</Text>
            </Text>
          ) : (
            <Text dimColor>一致するスキルはありません。</Text>
          )}
        </Box>

        {current.candidates.length > 1 && (
          <Box flexDirection="row" flexWrap="wrap" columnGap={1} rowGap={0}>
            {current.candidates.map(candidate =>
              candidate.name === current.selected ? (
                <Button key={`pick:${candidate.name}`} variant="primary" onPress={() => void pick($, candidate.name)}>
                  {candidate.name}
                </Button>
              ) : (
                <Button key={`pick:${candidate.name}`} onPress={() => void pick($, candidate.name)}>
                  {candidate.name}
                </Button>
              ),
            )}
          </Box>
        )}

        {doc?.description && <Text>{doc.description}</Text>}

        {doc && doc.fields.length > 0 && (
          <Box flexDirection="column">
            {doc.fields.map(field => (
              <Text>
                <Text bold>{field.key}</Text>: {field.value}
              </Text>
            ))}
          </Box>
        )}

        {doc?.path && <Text dimColor>{doc.path}</Text>}
        {doc?.error && <Text color="error">{doc.error}</Text>}

        {doc && (doc.body ? (
          <Markdown text={doc.body} />
        ) : (
          !doc.error && (
            <Text dimColor>
              {doc.path ? '本文はありません。' : 'SKILL.md が見つからないため、説明文だけを表示しています。'}
            </Text>
          )
        ))}
      </Box>
    )
  })
}
