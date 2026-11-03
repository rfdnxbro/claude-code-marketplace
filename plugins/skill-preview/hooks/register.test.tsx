import { expect, mock, test } from 'claude-code/testing'
import type { Engine } from 'claude-code/testing'
import type {
  On,
  PromptChangeInput,
  PromptChangeResult,
  PromptEditInput,
  PromptEditResult,
} from 'claude-code'

import { JA_DESCRIPTIONS } from './ja-descriptions.ts'
import {
  asarLayout,
  idsPattern,
  localeFileRange,
  officialLabelsOf,
  parseMessages,
  parseTranslations,
} from './official.ts'
import {
  findUntranslated,
  formatUntranslated,
  matchCommands,
  parseFrontmatter,
  projectDirs,
  slashQuery,
  translateDescription,
} from './lib.ts'

const PANE = {
  plugin: 'skill-preview',
  component: 'Pane',
  requestId: 'skill-preview',
  props: {
    title: 'スキル',
    isFocused: false,
    bodyColumns: 60,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 40 },
    view: {},
  },
} as const

const HOME = '/home/u'
const ASAR = '/Applications/Claude.app/Contents/Resources/ion-dist.asar'
const DESKTOP_CONFIG = `${HOME}/Library/Application Support/Claude/config.json`
const CWD = '/work/app'

const COMMANDS = [
  { name: 'clear', description: '会話をクリア', source: 'builtin' },
  { name: 'grilling', description: '計画を問い詰める', source: 'user' },
  { name: 'grill-me', description: 'grill me', source: 'user' },
  { name: 'eli5:eli5', description: '5歳児向けに説明', source: 'plugin', plugin: 'eli5' },
  { name: 'deep-research', description: '深い調査', source: 'builtin' },
  { name: 'lint-fix', description: 'lint を直す', source: 'user' },
  { name: 'parent-skill', description: '親のスキル', source: 'user' },
  { name: 'pdf', description: 'PDF を扱う', source: 'user' },
  // 説明の日本語訳を確かめるもの
  { name: 'context', description: 'Show current context usage', source: 'builtin' },
  { name: 'compact', description: 'Compact the conversation (changed in an update)', source: 'builtin' },
  { name: 'commit-commands:commit', description: 'Create a git commit', source: 'plugin', plugin: 'commit-commands' },
  { name: 'init', description: 'Initialize a new CLAUDE.md file with codebase documentation', source: 'user' },
  // 訳が同梱されていない Anthropic 提供のスキル
  { name: 'anthropic-skills:brand-new', description: 'A brand new skill', source: 'plugin', plugin: 'anthropic-skills' },
] as const

const FILES: Record<string, string> = {
  [`${HOME}/.claude/skills/grilling/SKILL.md`]: [
    '---',
    'name: grilling',
    'description: 計画を問い詰める',
    'allowed-tools:',
    '  - Read',
    '  - Grep',
    'model: opus',
    '---',
    '',
    '# Grilling',
    '',
    '質問を1つずつ投げる。',
  ].join('\n'),
  [`${HOME}/.claude/skills/grill-me/SKILL.md`]: '---\nname: grill-me\ndescription: grill me\n---\nGrill me body.',
  [`${HOME}/.claude/plugins/installed_plugins.json`]: JSON.stringify({
    version: 2,
    plugins: {
      'eli5@community': [{ scope: 'user', installPath: '/cache/eli5/1.0.0' }],
      'commit-commands@claude-plugins-official': [{ scope: 'user', installPath: '/cache/commit-commands/1.0.0' }],
    },
  }),
  '/cache/eli5/1.0.0/skills/eli5/SKILL.md': '---\nname: eli5\ndescription: 5歳児向けに説明\n---\nやさしく説明する。',
  '/cache/commit-commands/1.0.0/commands/commit.md':
    '---\nallowed-tools: Bash(git commit:*)\ndescription: "Create a git commit"\n---\n\nコミットを作る手順。',
  // ユーザーが自分で書いた、組み込みと同じ名前のコマンド
  [`${HOME}/.claude/commands/init.md`]:
    '---\ndescription: Initialize a new CLAUDE.md file with codebase documentation\n---\n自作の init。',
  // ネストしたスキル
  [`${HOME}/.claude/skills/tools/lint-fix/SKILL.md`]: '---\nname: lint-fix\n---\nネストした本文。',
  // 作業ディレクトリの親のスキル
  '/work/.claude/skills/parent-skill/SKILL.md': '---\nname: parent-skill\n---\n親の本文。',
  // アカウントから同期されたスキル
  [`${HOME}/.claude/skills/synced/acct/pdf/SKILL.md`]: '---\nname: pdf\n---\n同期した本文。',
}

/** FILES から作るディレクトリの一覧 */
function dirs(): Record<string, Set<string>> {
  const out: Record<string, Set<string>> = {}
  for (const path of Object.keys(FILES)) {
    const parts = path.split('/')
    for (let i = 1; i < parts.length; i++) {
      const dir = parts.slice(0, i).join('/') || '/'
      ;(out[dir] ??= new Set()).add(parts[i] ?? '')
    }
  }

  return out
}

/** エンジン役: ファイルシステムとコマンド一覧などを差し込む。開いているペインの id の集合を返す */
type EngineOptions = {
  /** $.command.list() が返す一覧（省くと COMMANDS） */
  commands?: readonly (typeof COMMANDS)[number][]
  /** $.ui.copy で渡された文字列を入れる */
  copies?: string[]
  /** FILES に足すファイル（パス → 中身） */
  files?: Record<string, string>
  /** Desktop アプリの asar を置く（無ければアプリが無い扱い） */
  asar?: { size: number; mtimeMs: number }
  /** $.process.run の応答（省くと失敗を返す）。呼ばれた argv は runs に入れる */
  run?: (argv: readonly string[]) => string | undefined
  runs?: string[][]
}

function engine(on: On, options: EngineOptions = {}): Set<string> {
  const files: Record<string, string> = { ...FILES, ...options.files }
  const tree = dirs()
  const isFile = (path: string) => files[path] !== undefined
  const panes = new Set<string>()
  mock.store(on)
  mock.env(on, { HOME })
  on('command.register', () => ({ value: { command: 'skill-preview' } }))
  on('ui.open', (_, e) => {
    panes.add(e.id)

    return { value: { isPlaced: true } }
  })
  on('ui.close', (_, e) => {
    panes.delete(e.id)

    return { value: undefined }
  })
  on('ui.panes', () => ({
    value: [...panes].map(id => ({ id, title: id, isShown: true, isFocused: false, isPlaced: true })),
  }))
  on('session.cwd', () => ({ value: CWD }))
  on('command.list', () => ({ value: (options.commands ?? COMMANDS).map(c => ({ ...c })) }))
  on('fs.list', (_, e) => ({
    value: [...(tree[e.path] ?? [])].map(name => {
      const path = `${e.path}/${name}`

      return { name, kind: isFile(path) ? 'file' : 'dir', size: 0, mtimeMs: 0, isLink: false } as const
    }),
  }))
  on('fs.exists', (_, e) => ({ value: isFile(e.path) || tree[e.path] !== undefined }))
  on('fs.stat', (_, e) => {
    if (options.asar && e.path === ASAR) {
      return { value: { kind: 'file', size: options.asar.size, mtimeMs: options.asar.mtimeMs, isLink: false } as const }
    }
    if (!isFile(e.path) && tree[e.path] === undefined) throw new Error(`ENOENT: ${e.path}`)

    return { value: { kind: isFile(e.path) ? 'file' : 'dir', size: 0, mtimeMs: 1, isLink: false } as const }
  })
  on('process.run', (_, e) => {
    options.runs?.push([...e.argv])
    const stdout = options.run?.(e.argv)

    return {
      value: {
        exitCode: stdout === undefined ? 1 : 0,
        stdout: stdout ?? '',
        stderr: '',
        isStdoutTruncated: false,
        isStderrTruncated: false,
      },
    }
  })
  on('fs.read', (_, e) => {
    const text = files[e.path]
    if (text === undefined) throw new Error(`ENOENT: ${e.path}`)

    return { value: text }
  })
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('turn.complete', () => ({ text: '' }))
  on('skill.prompt', (_, e) => ({ text: e.text }))
  on('ui.invalidate', () => ({ value: undefined }))
  on('ui.copy', (_, e) => {
    options.copies?.push(e.text)

    return { value: { isCopied: true } }
  })
  on('command.describe', (_, e) => ({
    description: e.description,
    argumentHint: e.argumentHint,
    isHidden: e.isHidden,
  }))
  // 入力欄の編集: 置き換えを適用した結果を返す
  on('prompt.edit', (_, e) => {
    const text = e.text.slice(0, e.start) + e.inputText + e.text.slice(e.end)

    return { text, cursor: e.start + e.inputText.length }
  })
  on('prompt.change', (_, e) => ({ text: e.text }))

  return panes
}

/** prompt.edit はテストキットの型に無いが、エンジンの $ では呼べる */
type PromptEdit = { edit: (e: PromptEditInput) => Promise<PromptEditResult> }

function edit($: Engine, e: PromptEditInput) {
  return ($.prompt as unknown as PromptEdit).edit(e)
}

/** 送信やクリアで入力欄が空になる（prompt.change） */
type PromptChange = { change: (e: PromptChangeInput) => Promise<PromptChangeResult> }

function clearBox($: Engine) {
  return ($.prompt as unknown as PromptChange).change({ text: '', cursor: 0, origin: { kind: 'clear' } })
}

/** 入力欄の文字をすべて消す（Backspace） */
function eraseAll($: Engine, text: string) {
  return edit($, {
    origin: { kind: 'composer' },
    text,
    cursor: text.length,
    start: 0,
    end: text.length,
    inputText: '',
  })
}

const ELI5_RUN = {
  skill: 'eli5:eli5',
  text: 'やさしく説明する。',
  source: 'plugin',
  pluginName: 'eli5',
  path: '/cache/eli5/1.0.0/skills/eli5/SKILL.md',
  frontmatter: { name: 'eli5', description: '5歳児向けに説明' },
} as const

/** 入力欄に1文字ずつ打つ */
async function typeText($: Engine, text: string) {
  let draft = ''
  for (const char of text) {
    await edit($, {
      origin: { kind: 'composer' },
      text: draft,
      cursor: draft.length,
      start: draft.length,
      end: draft.length,
      inputText: char,
    })
    draft += char
  }
}

test('入力の先頭トークンを取り出す', async () => {
  expect(slashQuery('/gri')).toBe('gri')
  expect(slashQuery('/grilling 引数')).toBe('grilling')
  expect(slashQuery('/')).toBe('')
  expect(slashQuery('普通の文')).toBe(undefined)
})

test('完全一致を優先し、コロンの後ろでも一致させる', async () => {
  const names = (q: string) => matchCommands(COMMANDS, q, 6).map(c => c.name)
  expect(names('grill')).toEqual(['grilling', 'grill-me'])
  expect(names('grill-me')).toEqual(['grill-me'])
  expect(names('eli')).toEqual(['eli5:eli5'])
  expect(names('eli5')).toEqual(['eli5:eli5'])
  expect(names('zzz')).toEqual([])
})

test('作業ディレクトリから根までをたどり、ホームは除く', async () => {
  expect(projectDirs('/work/app/src', HOME)).toEqual(['/work/app/src', '/work/app', '/work', '/'])
  expect(projectDirs(`${HOME}/proj`, HOME)).toEqual([`${HOME}/proj`, '/home', '/'])
})

test('frontmatter のリストとブロックスカラーを読む', async () => {
  const { entries, body } = parseFrontmatter(
    '---\nname: x\ndescription: >\n  一行目\n  二行目\nallowed-tools:\n  - Read\n  - "Bash(git:*)"\n---\n\n本文',
  )
  expect(entries).toEqual([
    ['name', 'x'],
    ['description', '一行目 二行目'],
    ['allowed-tools', 'Read, Bash(git:*)'],
  ])
  expect(body).toBe('本文')
})

test('/gri と打つと一致したスキルの SKILL.md がペインに出る', async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await clock.settle()

  await typeText($, '/gri')
  await clock.advance(100)

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /入力中のプレビュー/ }))?.text).toBe(
      '入力中のプレビュー（/gri）',
    )
    expect(await ui.find({ type: 'Text', text: /^\/grilling/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /model: opus/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /allowed-tools: Read, Grep/ })).toBeDefined()
    expect(await ui.find({ type: 'Markdown', text: /質問を1つずつ投げる/ })).toBeDefined()
    // 候補が2件あるので Button で切り替えられる
    expect(await ui.find({ key: 'pick:grill-me' })).toBeDefined()
    await ui.unmount()
  }

  // Button で grill-me に切り替える
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  await ui.press({ key: 'pick:grill-me' })
  expect(await ui.find({ type: 'Markdown', text: /Grill me body/ })).toBeDefined()
  await ui.unmount()
})

test('プラグインのスキルは installed_plugins.json から引ける', async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await typeText($, '/eli')
  await clock.advance(100)

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /plugin: eli5/ })).toBeDefined()
  expect(await ui.find({ type: 'Markdown', text: /やさしく説明する/ })).toBeDefined()
  await ui.unmount()
})

test('ファイルの無い組み込みコマンドは説明文だけを出す', async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await typeText($, '/deep')
  await clock.advance(100)

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /builtin/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /^深い調査$/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /説明文だけを表示/ })).toBeDefined()
  await ui.unmount()
})

test('スキルが実行されると実行中として表示し、ターン完了で直前に実行に変わる', async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await $.skill.prompt({ ...ELI5_RUN })
  await clock.settle()

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /実行中/ })).toBeDefined()
  expect(await ui.find({ type: 'Markdown', text: /やさしく説明する/ })).toBeDefined()
  await ui.unmount()

  await $.turn.complete({
    answer: '',
    durationMs: 1,
    isAborted: false,
    turnId: 't1',
    reason: 'answer',
  })
  const after = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await after.find({ type: 'Text', text: /直前に実行/ })).toBeDefined()
  await after.unmount()
})

test('入力欄を空にすると入力中のプレビューを閉じ、また打つと開く', async ($, on) => {
  const clock = mock.clock(on)
  const panes = engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await typeText($, '/grilling')
  await clock.advance(100)
  expect(panes.has('skill-preview')).toBe(true)

  // `/` だけ残っているあいだは閉じない
  await edit($, { origin: { kind: 'composer' }, text: '/grilling', cursor: 9, start: 1, end: 9, inputText: '' })
  await clock.advance(500)
  expect(panes.has('skill-preview')).toBe(true)

  await eraseAll($, '/')
  await clock.advance(500)
  expect(panes.has('skill-preview')).toBe(false)

  await typeText($, '/eli')
  await clock.advance(100)
  expect(panes.has('skill-preview')).toBe(true)
})

test('/ で始まらない文に書き換えたときも閉じる', async ($, on) => {
  const clock = mock.clock(on)
  const panes = engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await typeText($, '/grilling')
  await clock.advance(100)
  await edit($, { origin: { kind: 'composer' }, text: '/grilling', cursor: 9, start: 0, end: 9, inputText: 'こんにちは' })
  await clock.advance(500)
  expect(panes.has('skill-preview')).toBe(false)
})

test('送信で入力欄が空になっても、スキルが実行されたら閉じずに実行中を出す', async ($, on) => {
  const clock = mock.clock(on)
  const panes = engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await typeText($, '/eli5 テスト')
  await clock.advance(100)
  await clearBox($)
  await $.skill.prompt({ ...ELI5_RUN })
  await clock.advance(500)
  expect(panes.has('skill-preview')).toBe(true)

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /実行中/ })).toBeDefined()
  await ui.unmount()

  // 実行後の表示は、入力欄が空のままでも残す
  await $.turn.complete({ answer: '', durationMs: 1, isAborted: false, turnId: 't1', reason: 'answer' })
  await clearBox($)
  await clock.advance(500)
  expect(panes.has('skill-preview')).toBe(true)
})

test('スキル以外のコマンドを送信したら閉じる', async ($, on) => {
  const clock = mock.clock(on)
  const panes = engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await typeText($, '/clear')
  await clock.advance(100)
  expect(panes.has('skill-preview')).toBe(true)
  await clearBox($)
  await clock.advance(500)
  expect(panes.has('skill-preview')).toBe(false)
})

test('ネストしたスキル・親ディレクトリのスキル・同期スキルの本文を出す', async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })

  const cases = [
    ['/lint-fix', /ネストした本文/, /user/],
    ['/parent-skill', /親の本文/, /project/],
    ['/pdf', /同期した本文/, /synced/],
  ] as const
  for (const [text, body, origin] of cases) {
    await eraseAll($, '/x')
    await typeText($, text)
    await clock.advance(100)
    const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
    expect(await ui.find({ type: 'Markdown', text: body })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: origin })).toBeDefined()
    await ui.unmount()
  }
})

test('別の場所のパスで実行したことがあっても、今のプロジェクトの索引を優先する', async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await $.skill.prompt({
    skill: 'grilling',
    text: '',
    source: 'projectSettings',
    path: '/elsewhere/grilling/SKILL.md',
    frontmatter: { name: 'grilling' },
  })
  await $.turn.complete({ answer: '', durationMs: 1, isAborted: false, turnId: 't1', reason: 'answer' })
  await typeText($, '/grilling')
  await clock.advance(100)

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Markdown', text: /質問を1つずつ投げる/ })).toBeDefined()
  await ui.unmount()
})

test('実行中に一致しない / を打っても実行中の表示を残す', async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await $.skill.prompt({ ...ELI5_RUN })
  await typeText($, '/zzz')
  await clock.advance(500)

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /実行中/ })).toBeDefined()
  expect(await ui.find({ type: 'Markdown', text: /やさしく説明する/ })).toBeDefined()
  await ui.unmount()
})

test('/skill-preview に一致しない名前を渡すと一致なしを出す', async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await $.command.run({ command: 'skill-preview', args: 'zzz', origin: { kind: 'composer' }, presentation: { isFullscreen: false, columns: 120 } })
  await clock.settle()

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /一致するスキルはありません/ })).toBeDefined()
  await ui.unmount()
})

test('何も一致していないときは案内を出す', async ($, on) => {
  engine(on)
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /スキル名を入力すると/ })).toBeDefined()
  await ui.unmount()
})

// ---------------------------------------------------------------------------
// 説明の日本語訳

const ENGINE = { plugin: 'engine', tier: 'core' } as const

/** command.describe を1回呼ぶ */
function describe($: Engine, command: string, description: string, provider: { plugin: string; tier: 'core' | 'user' } = ENGINE) {
  return $.command.describe({ command, description, isHidden: false, immediate: false, provider })
}

test('原文が一致すれば訳を返し、変わっていれば訳さない', async () => {
  expect(translateDescription('context', 'Show current context usage', 'builtin')).toBe(
    '現在のコンテキストの使用状況を表示する。',
  )
  // Claude Code の更新で原文が変わったとき
  expect(translateDescription('context', 'Show the current context usage', 'builtin')).toBe(undefined)
  // 訳の無いもの
  expect(translateDescription('no-such-command', 'Something', 'builtin')).toBe(undefined)
  // 改行や連続する空白の違いは無視する（SKILL.md の折り返し）
  expect(translateDescription('commit-commands:commit', 'Create a\n  git commit', 'commit-commands')).toBe(
    'git コミットを作る。',
  )
})

test('出どころが組み込み・Anthropic 提供のものと違えば訳さない', async () => {
  // ユーザーやプロジェクトのコマンドは出どころが無い
  expect(translateDescription('context', 'Show current context usage', undefined)).toBe(undefined)
  // 別のプラグインが同じ名前のコマンドを持っていても訳さない
  expect(translateDescription('commit-commands:commit', 'Create a git commit', 'other-plugin')).toBe(undefined)
  expect(translateDescription('context', 'Show current context usage', 'some-plugin')).toBe(undefined)
})

test('可変部分を訳に入れ、すでに訳文ならそのまま返す', async () => {
  expect(translateDescription('model', 'Set the AI model for Claude Code (currently Opus 5.5)', 'builtin')).toBe(
    'Claude Code の AI モデルを設定する（現在は Opus 5.5）。',
  )
  expect(translateDescription('model', 'Set the AI model for Claude Code', 'builtin')).toBe(
    'Claude Code の AI モデルを設定する。',
  )
  // command.describe で書き換えた後の一覧の説明
  expect(translateDescription('model', 'Claude Code の AI モデルを設定する（現在は Fable 5.1）。', 'builtin')).toBe(
    'Claude Code の AI モデルを設定する（現在は Fable 5.1）。',
  )
})

test('訳文の表は可変部分の数がそろい、である調で「。」で終わる', async () => {
  const holes = (text: string) => text.split('{}').length - 1
  for (const [name, entries] of Object.entries(JA_DESCRIPTIONS)) {
    expect(entries.length).toBeGreaterThan(0)
    for (const entry of entries) {
      expect([name, holes(entry.ja)]).toEqual([name, holes(entry.en)])
      expect([name, entry.ja.trim() !== '']).toEqual([name, true])
      // 文体: である調で、すべての訳を「。」で終える（ですます調は使わない）
      expect([name, entry.ja.endsWith('。')]).toEqual([name, true])
      expect([name, /です|ます。/.test(entry.ja)]).toEqual([name, false])
    }
  }
})

test('候補リストの説明を日本語訳に置き換える', async ($, on) => {
  engine(on)
  expect((await describe($, 'context', 'Show current context usage')).description).toBe(
    '現在のコンテキストの使用状況を表示する。',
  )
  expect(
    (await describe($, 'commit-commands:commit', 'Create a git commit', {
      plugin: 'commit-commands@claude-plugins-official',
      tier: 'user',
    })).description,
  ).toBe('git コミットを作る。')
})

test('原文が変わったもの・ユーザーやコミュニティのものは候補リストで英語のまま', async ($, on) => {
  engine(on)
  expect((await describe($, 'context', 'Show the context usage (new wording)')).description).toBe(
    'Show the context usage (new wording)',
  )
  // ユーザーが書いた、組み込みと同じ名前のコマンド
  expect(
    (await describe($, 'init', 'Initialize a new CLAUDE.md file with codebase documentation', {
      plugin: 'user',
      tier: 'user',
    })).description,
  ).toBe('Initialize a new CLAUDE.md file with codebase documentation')
  expect(
    (await describe($, 'eli5:eli5', 'Explain a topic like I am 5', { plugin: 'eli5@claude-community', tier: 'user' }))
      .description,
  ).toBe('Explain a topic like I am 5')
  // Anthropic 提供のプラグインと同じ名前でも、別のマーケットプレイスから入ったものは訳さない
  expect(
    (await describe($, 'commit-commands:commit', 'Create a git commit', {
      plugin: 'commit-commands@someone-else',
      tier: 'user',
    })).description,
  ).toBe('Create a git commit')
})

test('右ペインの説明も日本語訳にし、原文が変わったものは英語のまま出す', async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await clock.settle()

  /** 入力欄に text を打ち、ペインに description の Text があるか */
  const shows = async (text: string, description: string | RegExp) => {
    await eraseAll($, '/x')
    await typeText($, text)
    await clock.advance(100)
    const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
    const found = await ui.find({ type: 'Text', text: description })
    await ui.unmount()

    return found !== undefined
  }

  // ファイルの無い組み込みコマンド（一覧の説明）
  expect(await shows('/context', '現在のコンテキストの使用状況を表示する。')).toBe(true)
  expect(await shows('/compact', 'Compact the conversation (changed in an update)')).toBe(true)

  // Anthropic 提供のプラグインのコマンド（ファイルの frontmatter の説明）
  expect(await shows('/commit-commands:commit', 'git コミットを作る。')).toBe(true)
  expect(await shows('/commit-commands:commit', /\/cache\/commit-commands\/1\.0\.0\/commands\/commit\.md/)).toBe(true)

  // ユーザーが書いた同じ名前のコマンドは訳さない
  expect(await shows('/init', 'Initialize a new CLAUDE.md file with codebase documentation')).toBe(true)
})

test('実行された組み込みスキルの説明を日本語訳で出す', async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await clock.settle()

  const en = JA_DESCRIPTIONS.simplify?.[0]?.en ?? ''
  await $.skill.prompt({ skill: 'simplify', text: '本文', source: 'built-in', frontmatter: { description: en } })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /^変更したコードを再利用・簡素化/ })).toBeDefined()
  await ui.unmount()

  // 原文が変わっていれば英語のまま
  await $.skill.prompt({
    skill: 'simplify',
    text: '本文',
    source: 'built-in',
    frontmatter: { description: 'Review changed code (reworded)' },
  })
  const after = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await after.find({ type: 'Text', text: 'Review changed code (reworded)' })).toBeDefined()
  await after.unmount()
})

// ---------------------------------------------------------------------------
// 未訳

const RUN_UNTRANSLATED = {
  command: 'skill-preview-untranslated',
  args: '',
  origin: { kind: 'composer' },
  presentation: { isFullscreen: false, columns: 120 },
} as const

test('訳の対象で訳が使えないものだけを未訳として数える', async () => {
  const names = findUntranslated([
    ...COMMANDS,
    // 作者が Anthropic でないプラグインの英語の説明
    { name: '1password:envs', description: 'Manages secrets', source: 'plugin', plugin: '1password' },
    { name: 'mcp__x__y', description: 'An MCP prompt', source: 'mcp' },
    { name: 'empty', description: '', source: 'builtin' },
    // 英語が主体の説明に日本語の語が混じったもの（原文が変わっているので未訳）
    { name: 'help', description: 'Show help and available commands (日本語対応)', source: 'builtin' },
    // ユーザーがアップロードした、もともと日本語のスキル（英語の固有名詞を含む）
    {
      name: 'anthropic-skills:my-probe',
      description: 'Chat 経由でアップロードしたスキルが Claude Code Routines のクラウド実行から呼び出せるかを確かめる。',
      source: 'plugin',
      plugin: 'anthropic-skills',
    },
  ]).map(item => item.name)
  // 原文が変わった組み込み（compact、help）と、訳の無い Anthropic 提供のスキル
  expect(names).toEqual(['compact', 'anthropic-skills:brand-new', 'help'])
})

test('未訳の一覧を Claude に貼れる形で書き出す', async () => {
  const items = findUntranslated(COMMANDS)
  const text = formatUntranslated(items)
  expect(text).toMatch(/未訳の説明が 2 件あります/)
  expect(text).toMatch(/hooks\/ja-descriptions\.ts/)
  const json = /```json\n([\s\S]*)\n```/.exec(text)?.[1] ?? ''
  expect(JSON.parse(json)).toEqual([
    { name: 'compact', source: 'builtin', description: 'Compact the conversation (changed in an update)' },
    {
      name: 'anthropic-skills:brand-new',
      source: 'plugin',
      plugin: 'anthropic-skills',
      description: 'A brand new skill',
    },
  ])
  expect(formatUntranslated([])).toBe('未訳の説明はありません。')
})

test('右ペインに未訳の件数を出し、0 件なら出さない', async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await clock.settle()

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect(await ui.find({ type: 'Text', text: /未訳 2 件/ })).toBeDefined()
    await ui.unmount()
  }

  // 入力中のプレビューでも出す
  await typeText($, '/grilling')
  await clock.advance(100)
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /未訳 2 件（\/skill-preview-untranslated で一覧）/ })).toBeDefined()
  await ui.unmount()
})

test('未訳が無ければペインに件数を出さない', async ($, on) => {
  const clock = mock.clock(on)
  // 訳の対象のものがすべて訳せる一覧
  engine(on, { commands: COMMANDS.filter(c => c.name !== 'compact' && c.name !== 'anthropic-skills:brand-new') })
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await clock.settle()

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /未訳/ })).toBe(undefined)
  await ui.unmount()
})

test('未訳の一覧コマンドは一覧を出力し、クリップボードにも入れる', async ($, on) => {
  const copies: string[] = []
  engine(on, { copies })
  const result = await $.command.run({ ...RUN_UNTRANSLATED })
  expect(result.text).toMatch(/"name": "compact"/)
  expect(result.text).toMatch(/"name": "anthropic-skills:brand-new"/)
  expect(result.text).toMatch(/クリップボードにもコピーしました/)
  expect(copies.length).toBe(1)
  expect(copies[0]).toMatch(/未訳の説明が 2 件あります/)
})

// ---------------------------------------------------------------------------
// command.describe でだけ届くコマンド（$.command.list() に無い組み込み）

test('一覧に無い組み込みも command.describe で受け取れば右ペインに訳を出す', async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await clock.settle()

  for (const name of ['btw', 'help', 'resume'] as const) {
    await describe($, name, JA_DESCRIPTIONS[name]?.[0]?.en ?? '')
  }
  // 隠しコマンドは右ペインの候補から外す
  await $.command.describe({
    command: 'claim-credit',
    description: 'Claim credit',
    isHidden: true,
    immediate: false,
    provider: ENGINE,
  })
  await clock.advance(300)

  const shows = async (text: string, description: string | RegExp) => {
    await eraseAll($, '/x')
    await typeText($, text)
    await clock.advance(100)
    const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
    const found = await ui.find({ type: 'Text', text: description })
    await ui.unmount()

    return found !== undefined
  }
  expect(await shows('/btw', 'メインの会話を中断せずに、ちょっとした質問をする。')).toBe(true)
  expect(await shows('/help', 'ヘルプと使えるコマンドを表示する。')).toBe(true)
  expect(await shows('/resume', '以前の会話を再開する。')).toBe(true)
  expect(await shows('/claim-credit', '一致するスキルはありません。')).toBe(true)
})

test('command.describe で受け取った原文で未訳を数える', async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await clock.settle()
  // 一覧に無い組み込みの原文が変わったもの
  await describe($, 'btw', 'Ask a side question (reworded)')
  // 一覧にあるもの（context）は、書き換え後ではなく受け取った原文で判定する
  await describe($, 'context', 'Show current context usage')
  await clock.advance(300)

  const result = await $.command.run({ ...RUN_UNTRANSLATED })
  expect(result.text).toMatch(/"name": "btw"/)
  expect(result.text).not.toMatch(/"name": "context"/)
})

// ---------------------------------------------------------------------------
// Desktop アプリの公式訳（テストでは合成した asar の内容を使う）

/** 合成した asar の公式訳の定義（キー・英語・ID・日本語） */
const OFFICIAL_MESSAGES = [
  { key: 'btw', en: 'Ask a side question', id: 'Id+btw/01', ja: '公式の btw の説明' },
  { key: 'model', en: 'Set the model', id: 'Id+model02', ja: '公式のモデルの説明' },
  { key: 'addDir', en: 'Add a folder', id: 'Id+addDir3', ja: '公式のフォルダ追加の説明' },
  { key: 'help', en: 'Get help', id: 'Id+help004', ja: '公式のヘルプの説明' },
  { key: 'resume', en: 'Resume', id: 'Id+resume5', ja: '公式の再開の説明' },
  { key: 'mcpSession', en: 'Manage servers', id: 'Id+mcpSes6', ja: '公式のサーバー管理の説明' },
] as const

/** asar の i18n/ja-JP.json の範囲（ヘッダーの offset 5000、大きさ 2000、本体の始まりは 8 + 1000） */
const JA_START = 8 + 1000 + 5000

/** 合成した asar に対する od / head / grep の出力 */
function fakeAsar(argv: readonly string[]): string | undefined {
  const [command, ...args] = argv
  if (command === '/usr/bin/od') return '           4        1000         996         120\n'
  if (command === '/usr/bin/head') {
    const header = JSON.stringify({
      files: { i18n: { files: { 'en-US.json': { size: 2000, offset: '1000' }, 'ja-JP.json': { size: 2000, offset: '5000' } } } },
    })
    return `\u0004\u0000\u0000\u0000xxxxxxxxxxxx${header}`
  }
  if (command === '/usr/bin/grep' && !args.includes('-b')) {
    const defs = OFFICIAL_MESSAGES.map(m => `${m.key}:{defaultMessage:"${m.en}",id:"${m.id}"}`).join(',')
    return `x=ne({${defs}})\nbtw:{defaultMessage:"btw",id:"Other00001"}\n`
  }
  if (command === '/usr/bin/grep') {
    return OFFICIAL_MESSAGES.flatMap((m, i) => [
      // en-US.json の行（範囲外なので使わない）
      `${2008 + i * 10}:"${m.id}": "${m.en}"`,
      `${JA_START + i * 10}:"${m.id}": "${m.ja}"`,
    ]).join('\n')
  }

  return undefined
}

const JA_CONFIG = { [DESKTOP_CONFIG]: JSON.stringify({ locale: 'ja-JP' }) }

/** 公式訳の読み込み（session.start の裏で走る）が終わるまで進める */
async function settleOfficial(clock: { settle: () => Promise<void> }) {
  for (let i = 0; i < 5; i++) await clock.settle()
}

test('公式訳の定義と訳文を asar の出力から読む', async () => {
  expect(asarLayout('  4  1000  996  120 ')).toEqual({ headerLength: 120, base: 1008 })
  expect(asarLayout('garbage')).toBe(undefined)
  expect(localeFileRange(fakeAsar(['/usr/bin/head']) ?? '', 1008, 'ja-JP')).toEqual({ start: 6008, end: 8008 })
  expect(localeFileRange('no header', 1008, 'ja-JP')).toBe(undefined)

  const messages = parseMessages(fakeAsar(['/usr/bin/grep']) ?? '')
  expect(messages.map(m => m.key)).toEqual(OFFICIAL_MESSAGES.map(m => m.key))
  expect(parseMessages('btw:{defaultMessage:"btw",id:"x"}')).toEqual([])

  const translations = parseTranslations(fakeAsar(['/usr/bin/grep', '-b']) ?? '', { start: 6008, end: 8008 })
  expect(translations['Id+model02']).toBe('公式のモデルの説明')
  const labels = officialLabelsOf(messages, translations)
  expect(labels['add-dir']).toBe('公式のフォルダ追加の説明')
  expect(labels['mcp-session']).toBe('公式のサーバー管理の説明')
  // ERE の特殊文字（+ と /）を含む ID もエスケープする
  expect(idsPattern(['a+b/c'])).toBe('"(a\\+b\\/c)": "([^"\\\\]|\\\\.)*"')
})

test('公式訳があれば候補リストと右ペインの両方で自前訳より優先する', async ($, on) => {
  const clock = mock.clock(on)
  const runs: string[][] = []
  engine(on, { files: JA_CONFIG, asar: { size: 123, mtimeMs: 7 }, run: fakeAsar, runs })
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await settleOfficial(clock)

  // 候補リスト: 公式訳のあるものは公式訳、無いものは自前訳
  expect((await describe($, 'btw', 'Ask a quick side question without interrupting the main conversation')).description).toBe(
    '公式の btw の説明',
  )
  expect((await describe($, 'model', 'Set the AI model for Claude Code')).description).toBe('公式のモデルの説明')
  expect((await describe($, 'help', 'Show help and available commands')).description).toBe('公式のヘルプの説明')
  expect((await describe($, 'context', 'Show current context usage')).description).toBe(
    '現在のコンテキストの使用状況を表示する。',
  )
  // 公式訳は組み込みにだけ使う
  expect((await describe($, 'resume', 'My resume', { plugin: 'user', tier: 'user' })).description).toBe('My resume')
  await clock.advance(300)

  // 右ペイン
  await typeText($, '/btw')
  await clock.advance(100)
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: '公式の btw の説明' })).toBeDefined()
  await ui.unmount()

  // 公式訳のあるものは、自前訳の原文が変わっていても未訳に数えない
  await describe($, 'btw', 'Ask a side question (reworded)')
  await clock.advance(300)
  const result = await $.command.run({ ...RUN_UNTRANSLATED })
  expect(result.text).not.toMatch(/"name": "btw"/)

  // 2回目の起動では、asar が変わっていなければキャッシュを使い、取り出し直さない
  const before = runs.filter(argv => argv[0] === '/usr/bin/grep').length
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await settleOfficial(clock)
  expect(runs.filter(argv => argv[0] === '/usr/bin/grep').length).toBe(before)
  expect(before).toBe(2)
})

test('UI が日本語でない・アプリが無い・形式が読めないときは自前訳を使う', async ($, on) => {
  const cases: EngineOptions[] = [
    { files: { [DESKTOP_CONFIG]: JSON.stringify({ locale: 'en-US' }) }, asar: { size: 1, mtimeMs: 1 }, run: fakeAsar },
    { files: JA_CONFIG, run: fakeAsar },
    { files: JA_CONFIG, asar: { size: 2, mtimeMs: 2 }, run: argv => (argv[0] === '/usr/bin/od' ? 'broken' : '') },
  ]
  const clock = mock.clock(on)
  const runs: string[][] = []
  let current: EngineOptions = {}
  engine(on, {
    get files() {
      return current.files
    },
    get asar() {
      return current.asar
    },
    run: argv => current.run?.(argv),
    runs,
  })
  for (const options of cases) {
    current = options
    await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
    await settleOfficial(clock)
    expect((await describe($, 'model', 'Set the AI model for Claude Code')).description).toBe(
      'Claude Code の AI モデルを設定する。',
    )
  }
  // UI が日本語でないとき・アプリが無いときは asar を grep しない
  expect(runs.filter(argv => argv[0] === '/usr/bin/grep').length).toBe(0)
})
