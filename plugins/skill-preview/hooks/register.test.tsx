import { expect, mock, test } from 'claude-code/testing'
import type { Engine } from 'claude-code/testing'
import type { On, PromptEditInput, PromptEditResult } from 'claude-code'

import { matchCommands, parseFrontmatter, slashQuery } from './lib.ts'

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

/** エンジン役: ファイルシステムとコマンド一覧などを差し込む */
function engine(on: On) {
  const tree = dirs()
  const isFile = (path: string) => FILES[path] !== undefined
  mock.store(on)
  mock.env(on, { HOME })
  on('command.register', () => ({ value: { command: 'skill-preview' } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
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
}

/** prompt.edit はテストキットの型に無いが、エンジンの $ では呼べる */
type PromptEdit = { edit: (e: PromptEditInput) => Promise<PromptEditResult> }

function edit($: Engine, e: PromptEditInput) {
  return ($.prompt as unknown as PromptEdit).edit(e)
}

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
  await $.skill.prompt({
    skill: 'eli5:eli5',
    text: 'やさしく説明する。',
    source: 'plugin',
    pluginName: 'eli5',
    path: '/cache/eli5/1.0.0/skills/eli5/SKILL.md',
    frontmatter: { name: 'eli5', description: '5歳児向けに説明' },
  })
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

test('入力が / で始まらなくなっても直前の表示を残す', async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  await $.session.start({ cwd: CWD, surface: 'desktop', isInteractive: true })
  await typeText($, '/grilling')
  await clock.advance(100)
  await edit($, {
    origin: { kind: 'composer' },
    text: '/grilling',
    cursor: 9,
    start: 0,
    end: 9,
    inputText: 'こんにちは',
  })
  await clock.advance(100)

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Markdown', text: /質問を1つずつ投げる/ })).toBeDefined()
  await ui.unmount()
})

test('何も一致していないときは案内を出す', async ($, on) => {
  engine(on)
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /スキル名を入力すると/ })).toBeDefined()
  await ui.unmount()
})
