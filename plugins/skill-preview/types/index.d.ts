// skill-preview の $.state の型契約

/** frontmatter の1項目（表示用に文字列化したもの） */
export type SkillField = { key: string; value: string }

/** ペインに表示する1つのスキル */
export type SkillDoc = {
  /** スキル名（`/` なし。プラグインのものは `plugin:skill`） */
  name: string
  /** 出どころ（user / project / plugin: <名前> / builtin など） */
  origin: string
  /** SKILL.md（またはコマンドの .md）の絶対パス。見つからないときは無し */
  path?: string
  description?: string
  /** description と name 以外の frontmatter */
  fields: SkillField[]
  /** frontmatter を除いた本文 */
  body?: string
  /** ファイルを読めなかったときの理由 */
  error?: string
}

/** 入力中の候補 */
export type Candidate = { name: string; origin: string }

/**
 * ペインの表示内容
 * - empty: まだ何も表示していない
 * - typing: 入力欄の `/スキル名` から引いたプレビュー
 * - running: いま実行中のスキル
 * - ran: 直前のターンで実行したスキル
 */
export type PreviewView = {
  mode: 'empty' | 'typing' | 'running' | 'ran'
  /** 入力欄の先頭トークン（typing のとき） */
  query?: string
  candidates: Candidate[]
  selected?: string
  doc?: SkillDoc
}

declare module 'claude-code' {
  interface PluginState {
    'skill-preview': {
      view: Shaped<PreviewView>
    }
  }
}
