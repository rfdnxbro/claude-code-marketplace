import { expect, mock, test } from 'claude-code/testing'
import type { Engine } from 'claude-code/testing'
import type {
  On,
  PromptChangeInput,
  PromptChangeResult,
  PromptEditInput,
  PromptEditResult,
} from 'claude-code'

import { matchCommands, parseFrontmatter, projectDirs, slashQuery } from './lib.ts'

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
    },
  }),
  '/cache/eli5/1.0.0/skills/eli5/SKILL.md': '---\nname: eli5\ndescription: 5歳児向けに説明\n---\nやさしく説明する。',
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
function engine(on: On): Set<string> {
  const tree = dirs()
  const isFile = (path: string) => FILES[path] !== undefined
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
  on('command.list', () => ({ value: COMMANDS.map(c => ({ ...c })) }))
  on('fs.list', (_, e) => ({
    value: [...(tree[e.path] ?? [])].map(name => {
      const path = `${e.path}/${name}`

      return { name, kind: isFile(path) ? 'file' : 'dir', size: 0, mtimeMs: 0, isLink: false } as const
    }),
  }))
  on('fs.exists', (_, e) => ({ value: isFile(e.path) || tree[e.path] !== undefined }))
  on('fs.stat', (_, e) => {
    if (!isFile(e.path) && tree[e.path] === undefined) throw new Error(`ENOENT: ${e.path}`)

    return { value: { kind: isFile(e.path) ? 'file' : 'dir', size: 0, mtimeMs: 1, isLink: false } as const }
  })
  on('fs.read', (_, e) => {
    const text = FILES[e.path]
    if (text === undefined) throw new Error(`ENOENT: ${e.path}`)

    return { value: text }
  })
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('turn.complete', () => ({ text: '' }))
  on('skill.prompt', (_, e) => ({ text: e.text }))
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
