// skill-preview: 入力中の /スキル名 や実行されたスキルの SKILL.md を右ペインに表示し、組み込み・Anthropic 提供の説明を日本語訳で出す

import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, Timer } from 'claude-code'

import type { DescribedCommand, PreviewView, SkillDoc } from '../types'
import type { CommandLike } from './lib.ts'
import {
  docFromFile,
  fieldsOf,
  findUntranslated,
  formatUntranslated,
  localizeDescription,
  matchCommands,
  mergeCommands,
  originOfCommand,
  originOfSkillSource,
  ownerOfCommand,
  ownerOfProvider,
  ownerOfSkillRun,
  projectDirs,
  shortName,
  slashQuery,
  preferredDescription,
} from './lib.ts'
import {
  MESSAGES_PATTERN,
  asarCandidates,
  asarLayout,
  desktopConfigPath,
  idsPattern,
  isJapaneseLocale,
  isOfficialCacheFor,
  localeFileRange,
  localeOfAppleLanguages,
  localeOfConfig,
  officialLabelsOf,
  parseMessages,
  parseTranslations,
} from './official.ts'
import type { AsarStat, OfficialLabels } from './official.ts'

const PANE = 'skill-preview'
const TITLE = 'スキル'
/** 候補として並べる最大件数 */
const MAX_CANDIDATES = 6
/** キー入力が止まってから引きに行くまでの待ち（ミリ秒） */
const DEBOUNCE_MS = 60
/** 入力欄が空になってから入力中のプレビューを閉じるまでの待ち（ミリ秒）。送信直後のスキル実行を待つ */
const CLOSE_DELAY_MS = 300
/** 未訳の一覧を出すコマンド */
const UNTRANSLATED_COMMAND = 'skill-preview-untranslated'
/** $.store に覚えるパスの最大件数 */
const MAX_LEARNED = 500
/** 実行して分かったパスを置く $.store のキー（作業ディレクトリごとに覚える） */
const LEARNED_KEY = 'learned-paths'
/** Desktop アプリから取り出した公式訳のキャッシュを置く $.store のキー */
const OFFICIAL_KEY = 'official-labels'
/** 公式訳の訳文のファイル（asar の中の `i18n/<これ>.json`） */
const OFFICIAL_LOCALE_FILE = 'ja-JP'
/** 公式訳を取り出すコマンド1回の時間の上限（ミリ秒）。asar 全体を grep するので長めにする */
const OFFICIAL_TIMEOUT_MS = 60000
/** command.describe で受け取ったコマンドを $.state に書くまでの待ち（ミリ秒）。まとめて書く */
const DESCRIBED_FLUSH_MS = 200

const EMPTY: PreviewView = { mode: 'empty', candidates: [] }

// 値の形を変えたら shape のタグを変える（古い形の値は初期値扱いになる）
const view = atom({ plugin: 'skill-preview', key: 'view' } as const, EMPTY, {
  shape: 'view-1',
})
/** 訳の対象なのに英語のまま表示しているコマンドの数 */
const untranslated = atom({ plugin: 'skill-preview', key: 'untranslated' } as const, 0)
/** command.describe で受け取ったコマンド（$.command.list() に無い組み込みを補うため） */
const NO_DESCRIBED: Record<string, DescribedCommand> = {}
const described = atom({ plugin: 'skill-preview', key: 'described' } as const, NO_DESCRIBED, {
  shape: 'described-1',
})

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
/** 実行して分かったパス（キーは `<作業ディレクトリ>\n<スキル名>`） */
let learned: Record<string, string> = {}
/** 索引を作った作業ディレクトリ（learned のキーに使う） */
let cwd = ''
let commands: CommandLike[] = []
/** Desktop アプリの公式訳（コマンド名 → 日本語）。読めないときは空 */
let official: OfficialLabels = {}
/** まだ $.state に書いていない command.describe の受け取り分 */
let pendingDescribed: Record<string, DescribedCommand> = {}
let describedTimer: Timer | undefined
let ready: Promise<void> | undefined
let timer: Timer | undefined
let closeTimer: Timer | undefined
let lastQuery: string | undefined
/** 入力欄の `/スキル名` から引いたプレビューを出しているか */
let previewing = false
/** 入力中のプレビューを手で閉じられたか（入力欄が `/` で始まらなくなるまで開き直さない） */
let dismissed = false
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

/** スキルを探すときに入らないディレクトリ */
const SKIP_DIRS = new Set(['node_modules'])
/** スキルを探す深さの上限（`skills/` 直下を 0 とする） */
const MAX_SKILL_DEPTH = 3

function addEntry(table: Record<string, Entry>, name: string, entry: Entry) {
  if (!table[name]) table[name] = entry
}

/**
 * `<dir>/**\/<name>/SKILL.md` を `<prefix><name>` として登録する。
 * ネストしたスキル（`category/name/SKILL.md`）は `<prefix>category:name` でも引けるようにする。
 * 浅いものを先に登録する（同名なら浅い方が勝つ）。exclude は `dir` 直下で入らない名前
 */
async function addSkills(
  $: EngineInterface,
  table: Record<string, Entry>,
  dir: string,
  prefix: string,
  origin: string,
  exclude: readonly string[] = [],
) {
  let level: { dir: string; parents: string[] }[] = [{ dir, parents: [] }]
  for (let depth = 0; depth <= MAX_SKILL_DEPTH && level.length > 0; depth++) {
    const nextLevel: { dir: string; parents: string[] }[] = []
    for (const { dir: current, parents } of level) {
      const entries = (await listDir($, current)).filter(
        entry =>
          entry.kind !== 'file' &&
          !entry.name.startsWith('.') &&
          !SKIP_DIRS.has(entry.name) &&
          !(depth === 0 && exclude.includes(entry.name)),
      )
      const found = await Promise.all(
        entries.map(async entry => {
          const path = `${current}/${entry.name}`
          try {
            if (await $.fs.exists(`${path}/SKILL.md`)) return { entry, path, isSkill: true }
          } catch {
            // 読めないものはスキルではないとみなす
          }

          return { entry, path, isSkill: false }
        }),
      )
      for (const { entry, path, isSkill } of found) {
        if (isSkill) {
          const skill: Entry = { path: `${path}/SKILL.md`, origin }
          addEntry(table, `${prefix}${entry.name}`, skill)
          if (parents.length > 0) addEntry(table, `${prefix}${[...parents, entry.name].join(':')}`, skill)
        } else if (await isDir($, path, entry.kind)) {
          nextLevel.push({ dir: path, parents: [...parents, entry.name] })
        }
      }
    }
    level = nextLevel
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

async function buildIndex($: EngineInterface, cwd: string): Promise<SkillIndex> {
  const home = (await $.env.get('HOME')) ?? ''
  const configDir = (await $.env.get('CLAUDE_CONFIG_DIR')) ?? `${home}/.claude`
  const built: SkillIndex = { exact: {}, bare: {} }

  // 先に登録したものが優先（プロジェクト（近い順）→ ユーザー → プラグイン）
  for (const dir of projectDirs(cwd, home)) {
    await addSkills($, built.exact, `${dir}/.claude/skills`, '', 'project')
    await addCommands($, built.exact, `${dir}/.claude/commands`, '', 'project', 0)
  }
  // 同期スキルは下で別に引くので、ユーザーのスキルとしては数えない
  await addSkills($, built.exact, `${configDir}/skills`, '', 'user', ['synced'])
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
  const stored = await $.store.get(LEARNED_KEY)
  if (stored && typeof stored === 'object') learned = stored as Record<string, string>
  cwd = await $.session.cwd()
  index = await buildIndex($, cwd)
}

async function ensureReady($: EngineInterface) {
  ready ??= prepare($).catch(() => {
    // 索引が作れなくても、覚えたパスと説明文だけで動く
  })
  await ready
}

// ---------------------------------------------------------------------------
// スキルの読み込み

function learnedKey(name: string): string {
  return `${cwd}\n${name}`
}

/** 今のプロジェクトの索引を優先し、索引に無いものだけ実行して分かったパスで補う */
function resolveEntry(name: string): Entry | undefined {
  const exact = index.exact[name]
  if (exact) return exact
  const known = learned[learnedKey(name)]
  if (known) return { path: known, origin: '' }

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

/** 説明を公式訳か自前訳に置き換える（どちらも使えないときはそのまま） */
function localizeDoc(doc: SkillDoc, owner: string | undefined): SkillDoc {
  const description = localizeDescription(doc.name, doc.description, owner, official)

  return description === doc.description ? doc : { ...doc, description }
}

async function loadCommand($: EngineInterface, command: CommandLike): Promise<SkillDoc> {
  const entry = resolveEntry(command.name)
  const origin = originOfCommand(command, entry?.origin || undefined)
  const owner = ownerOfCommand(command)
  const fallback = localizeDoc(
    { name: command.name, origin, description: command.description || undefined, fields: [] },
    owner,
  )
  if (!entry) return fallback

  return localizeDoc(await loadFile($, command.name, origin, entry.path, fallback), owner)
}

// ---------------------------------------------------------------------------
// 表示の更新

/** ペインが閉じていれば開く */
async function ensureOpen($: EngineInterface) {
  if (dismissed) return
  if ((await $.ui.panes()).some(pane => pane.id === PANE)) return
  await $.ui.open({ id: PANE, title: TITLE })
}

function cancelClose() {
  closeTimer?.cancel()
  closeTimer = undefined
}

/** 入力中のプレビューを閉じる（実行中・直前に実行の表示は残す） */
async function closePreview($: EngineInterface) {
  if ((await read($, view)).mode !== 'typing') return
  await $.ui.close({ id: PANE })
}

/** 入力欄の中身が変わったとき（編集・送信・クリア・履歴の呼び出し） */
function onBoxText($: EngineInterface, text: string) {
  const query = slashQuery(text)
  if (query === undefined) {
    // `/` で始まらなくなったら（空になったら）入力中のプレビューを閉じる
    lastQuery = undefined
    timer?.cancel()
    dismissed = false
    if (previewing) {
      previewing = false
      // 読み込み途中のプレビューで開き直さない
      seq++
      cancelClose()
      closeTimer = $.clock.after(CLOSE_DELAY_MS, () => {
        closeTimer = undefined
        void closePreview($)
      })
    }
    return
  }

  cancelClose()
  // `/` だけのときは直前の表示を残す
  if (query === '' || query === lastQuery) return
  lastQuery = query
  timer?.cancel()
  timer = $.clock.after(DEBOUNCE_MS, () => {
    void showQuery($, query, true)
  })
}

/** $.command.list() と、command.describe で受け取ったコマンド（一覧に無い組み込みも含む）を合わせた一覧 */
async function listCommands($: EngineInterface): Promise<CommandLike[]> {
  return mergeCommands(await $.command.list(), await read($, described))
}

/** コマンド一覧から未訳の数を数え直す（変わったときだけ書く） */
async function countUntranslated($: EngineInterface, list: readonly CommandLike[]) {
  const count = findUntranslated(list, { official }).length
  if ((await read($, untranslated)) !== count) await update($, untranslated, (): number => count)
}

/** 未訳を数え直す（失敗しても他の表示は止めない） */
async function refreshUntranslated($: EngineInterface) {
  try {
    await countUntranslated($, await listCommands($))
  } catch {
    // 数えられなくても、入力時にまた数える
  }
}

/** command.describe で受け取ったコマンドを覚える（まとめて $.state に書く） */
function rememberDescribed($: EngineInterface, name: string, command: DescribedCommand) {
  pendingDescribed[name] = command
  describedTimer?.cancel()
  describedTimer = $.clock.after(DESCRIBED_FLUSH_MS, () => {
    describedTimer = undefined
    void flushDescribed($)
  })
}

async function flushDescribed($: EngineInterface) {
  const batch = pendingDescribed
  pendingDescribed = {}
  await update($, described, (current): Record<string, DescribedCommand> => ({ ...current, ...batch }))
  await refreshUntranslated($)
}

// ---------------------------------------------------------------------------
// Desktop アプリの公式訳（実行時にアプリ内のファイルから読む。リポジトリには同梱しない）

/** Desktop の UI の言語（設定ファイルに無ければ macOS の言語設定） */
async function desktopLocale($: EngineInterface, home: string): Promise<string | undefined> {
  try {
    const locale = localeOfConfig(await $.fs.read(desktopConfigPath(home)))
    if (locale) return locale
  } catch {
    // 設定ファイルが無ければ OS の言語を見る
  }
  try {
    const result = await $.process.run(['/usr/bin/defaults', 'read', '-g', 'AppleLanguages'], { timeoutMs: 5000 })
    if (result.exitCode === 0) return localeOfAppleLanguages(result.stdout)
  } catch {
    // macOS 以外など
  }

  return undefined
}

/** Desktop アプリの asar を探す */
async function findAsar($: EngineInterface, home: string): Promise<AsarStat | undefined> {
  for (const path of asarCandidates(home)) {
    try {
      const stat = await $.fs.stat(path)
      if (stat.kind === 'file') return { path, size: stat.size, mtimeMs: stat.mtimeMs }
    } catch {
      // 次の場所を見る
    }
  }

  return undefined
}

/**
 * asar から組み込みコマンドの公式の日本語訳を取り出す。
 * cacheable は結果を $.store に覚えてよいか。形式が変わって読めないときは空を覚えてアプリの更新まで取り直さず、
 * コマンドの失敗や出力の切り詰め（一時的な失敗かもしれない）のときは覚えずに次の起動で取り直す
 */
async function extractOfficial(
  $: EngineInterface,
  path: string,
): Promise<{ labels: OfficialLabels; cacheable: boolean }> {
  const failed = { labels: {}, cacheable: false }
  const unreadable = { labels: {}, cacheable: true }
  const init = { timeoutMs: OFFICIAL_TIMEOUT_MS, env: { LC_ALL: 'C' } }
  const od = await $.process.run(['/usr/bin/od', '-An', '-tu4', '-N16', path], init)
  if (od.exitCode !== 0) return failed
  const layout = asarLayout(od.stdout)
  if (!layout) return unreadable

  const head = await $.process.run(['/usr/bin/head', '-c', String(16 + layout.headerLength), path], init)
  if (head.exitCode !== 0 || head.isStdoutTruncated) return failed
  const range = localeFileRange(head.stdout, layout.base, OFFICIAL_LOCALE_FILE)
  if (!range) return unreadable

  // grep の終了コードは 0 が一致あり、1 が一致なし（形式が変わった）、2 以上が失敗
  const defs = await $.process.run(['/usr/bin/grep', '-a', '-o', '-E', MESSAGES_PATTERN, path], init)
  if (defs.exitCode > 1 || defs.isStdoutTruncated) return failed
  const messages = parseMessages(defs.stdout)
  if (messages.length === 0) return unreadable

  const ids = messages.map(message => message.id)
  const found = await $.process.run(['/usr/bin/grep', '-a', '-o', '-b', '-E', idsPattern(ids), path], init)
  if (found.exitCode > 1 || found.isStdoutTruncated) return failed

  return { labels: officialLabelsOf(messages, parseTranslations(found.stdout, range)), cacheable: true }
}

/**
 * 公式訳を読み込む。asar の大きさ・更新時刻と UI の言語が前回と同じなら $.store のキャッシュを使う。
 * アプリが無い・形式が変わって読めない・UI が日本語でない・macOS 以外のときは空にして、自前訳に任せる
 */
async function loadOfficial($: EngineInterface) {
  const before = JSON.stringify(official)
  try {
    const home = (await $.env.get('HOME')) ?? ''
    const locale = await desktopLocale($, home)
    const asar = isJapaneseLocale(locale) ? await findAsar($, home) : undefined
    if (!asar || locale === undefined) {
      official = {}
    } else {
      const cached = await $.store.get(OFFICIAL_KEY)
      if (isOfficialCacheFor(cached, asar, locale)) {
        official = cached.labels
      } else {
        const extracted = await extractOfficial($, asar.path)
        official = extracted.labels
        // 形式が変わって読めなかったときも空のまま覚え、アプリが更新されるまで取り直さない
        if (extracted.cacheable) await $.store.set(OFFICIAL_KEY, { ...asar, locale, labels: official })
      }
    }
  } catch {
    official = {}
  }
  if (JSON.stringify(official) === before) return
  // 公式訳が変わったら、候補リストの説明と未訳の数を引き直す
  $.ui.invalidate('command.describe')
  await refreshUntranslated($)
}

/** トークンから候補を引き、先頭をプレビューする（fromInput: 入力欄から引いたか） */
async function showQuery($: EngineInterface, query: string, fromInput: boolean) {
  const mine = ++seq
  await ensureReady($)
  commands = await listCommands($)
  await countUntranslated($, commands)
  const hits = matchCommands(commands, query, MAX_CANDIDATES)
  if (mine !== seq) return

  const first = hits[0]
  if (!first) {
    if (fromInput) previewing = true
    // 入力中に一致しないときは、まだ何も出していない表示と実行中・直前に実行の表示を残す
    await update($, view, (current): PreviewView =>
      fromInput && current.mode !== 'typing' ? current : { mode: 'typing', query, candidates: [] },
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
  if (fromInput) previewing = true
  await ensureOpen($)
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
  cancelClose()
  lastQuery = undefined
  previewing = false
  dismissed = false

  const origin = originOfSkillSource(run.source, run.pluginName)
  const owner = ownerOfSkillRun(run.skill, run.source, run.pluginName)
  const { description, fields } = fieldsOf(Object.entries(run.frontmatter ?? {}))
  const fallback = localizeDoc({ name: run.skill, origin, description, fields }, owner)
  let doc = fallback
  if (run.path) {
    await ensureReady($)
    const key = learnedKey(run.skill)
    if (learned[key] !== run.path) {
      learned = Object.fromEntries(
        [...Object.entries(learned).filter(([k]) => k !== key), [key, run.path]].slice(-MAX_LEARNED),
      )
      await $.store.set(LEARNED_KEY, learned)
    }
    doc = localizeDoc(await loadFile($, run.skill, origin, run.path, fallback), owner)
  }
  if (mine !== seq) return
  await update($, view, (): PreviewView => ({
    mode: 'running',
    candidates: [],
    selected: run.skill,
    doc,
  }))
  await ensureOpen($)
}

// ---------------------------------------------------------------------------

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'skill-preview',
      description: 'スキル説明ペインを開く（スキル名を渡すとそのスキルを表示）',
      argumentHint: '[スキル名]',
    })
    await $.command.register({
      name: UNTRANSLATED_COMMAND,
      description: '組み込み・Anthropic 提供の説明のうち、日本語訳が無く英語のままのものを一覧する',
    })
    // 読み込み前にキャッシュされた英語の説明を、日本語訳で引き直してもらう
    $.ui.invalidate('command.describe')
    // 索引づくりは待たずに始める（最初の検索で待つ）
    void ensureReady($)
    void refreshUntranslated($)
    void loadOfficial($)

    return next(e)
  })

  on('command.run', { command: 'skill-preview' }, async ($, e) => {
    // 送信で入力欄が空になって閉じかけていても、コマンドで開いたものは残す
    cancelClose()
    previewing = false
    dismissed = false
    await $.ui.open({ id: PANE, title: TITLE })
    const name = e.args.trim().replace(/^\//, '')
    if (name !== '') await showQuery($, name, false)

    return { text: 'スキル説明ペインを開きました。' }
  })

  // 未訳の一覧を、Claude に貼って訳を頼める形で出す（クリップボードにもコピーする）
  on('command.run', { command: UNTRANSLATED_COMMAND }, async $ => {
    const list = await listCommands($)
    await countUntranslated($, list)
    const items = findUntranslated(list, { official })
    const text = formatUntranslated(items)
    if (items.length === 0) return { text }
    const copied = await $.ui.copy({ text })

    return { text: copied.isCopied ? `${text}\n\n（クリップボードにもコピーしました）` : text }
  })

  // 候補リストと /help の説明を日本語訳に置き換える（原文が訳の元と違えば英語のまま）
  on('command.describe', async ($, e, next) => {
    const owner = ownerOfProvider(e.provider)
    // 書き換える前の原文を覚える（$.command.list() に無い組み込みを右ペインと未訳の数え方で補う）
    rememberDescribed($, e.command, { description: e.description, owner, isHidden: e.isHidden })
    const result = await next(e)
    // 公式訳 → 自前訳の順で選ぶ（Desktop は一部の組み込みに自前の日本語を出すが、ターミナルでも同じ訳にする）
    const ja = preferredDescription(e.command, result.description, owner, official)

    return ja === undefined || ja === result.description ? result : { ...result, description: ja }
  })

  // キー入力ごと（上限 50 ms）。ここではファイルを読まず、タイマーで後から引く
  on('prompt.edit', async ($, e, next) => {
    const box = await next(e)
    onBoxText($, box.text)

    return box
  })

  // 編集以外で入力欄が変わったとき（送信・クリア・履歴の呼び出しなど）
  on('prompt.change', async ($, e, next) => {
    const result = await next(e)
    onBoxText($, e.text)

    return result
  })

  // 入力中のプレビューを手で閉じたら、入力欄が `/` で始まらなくなるまで開き直さない
  on('ui.close', async ($, e, next) => {
    if (e.id === PANE && e.origin.kind === 'person' && previewing) dismissed = true

    return next(e)
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
    const missing = await read($, untranslated)
    const doc = current.doc
    // 未訳があるときだけ控えめに知らせる
    const notice =
      missing > 0 ? (
        <Text dimColor>
          未訳 {missing} 件（/{UNTRANSLATED_COMMAND} で一覧）
        </Text>
      ) : null

    if (current.mode === 'empty') {
      return (
        <Box flexDirection="column" gap={1}>
          <Text dimColor>
            入力欄に「/」に続けてスキル名を入力すると、ここにそのスキルの SKILL.md を表示します。
          </Text>
          {notice}
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
              <Text key={`field:${field.key}`}>
                <Text bold>{field.key}</Text>: {field.value}
              </Text>
            ))}
          </Box>
        )}

        {doc?.path && <Text dimColor>{doc.path}</Text>}
        {notice}
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
