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

/**
 * command.describe で受け取ったコマンド（$.command.list() に無い組み込みも含む）
 * - description: 書き換える前の説明（訳と未訳の判定に使う原文）
 * - owner: 出どころ（`builtin`、プラグイン名、別のマーケットプレイスの同名プラグインは `<名前>@<マーケットプレイス>`、`user` / `project`）
 */
export type DescribedCommand = { description: string; owner: string; isHidden: boolean }

declare module 'claude-code' {
  interface PluginState {
    'skill-preview': {
      view: Shaped<PreviewView>
      /** 訳の対象なのに英語のまま表示しているコマンドの数 */
      untranslated: number
      /** command.describe で受け取ったコマンド（名前 → 原文と出どころ） */
      described: Shaped<Record<string, DescribedCommand>>
    }
  }
}
