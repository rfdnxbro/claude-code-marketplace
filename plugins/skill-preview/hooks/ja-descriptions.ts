// 組み込み・Anthropic 提供のスキルとコマンドの説明の日本語訳（README の「説明の日本語訳」を参照）
// en は訳の元にした英語の原文。実行時の説明がこれと一致しないときは訳を使わない
// en と ja の `{}` は可変部分（モデル名など）で、原文の該当部分をそのまま訳に入れる

export type JaEntry = { readonly en: string; readonly ja: string }

export const JA_DESCRIPTIONS: Readonly<Record<string, readonly JaEntry[]>> = {
  // ---- 組み込み
  "__remote-workflow": [
    {
      en: "Run the workflow script delivered in this session environment (server-launched sessions only)",
      ja: "このセッション環境に届いたワークフローのスクリプトを実行する（サーバーから起動したセッションのみ）。",
    },
  ],
  "add-dir": [
    {
      en: "Add a new working directory",
      ja: "作業ディレクトリを追加する。",
    },
  ],
  "advisor": [
    {
      en: "Let Claude consult a stronger model at key moments",
      ja: "要所で Claude がより強いモデルに相談できるようにする。",
    },
  ],
  "agents": [
    {
      en: "(removed) Ask Claude to create/manage subagents, or edit .claude/agents/",
      ja: "（削除済み）サブエージェントの作成・管理を Claude に頼む、または .claude/agents/ を編集する。",
    },
  ],
  "artifact-capabilities": [
    {
      en: "Runtime capabilities a published Artifact page can be granted — behavior static HTML cannot provide on its own, such as the page reading live or connected data, remembering what people do on it (a poll, a sign-up sheet, a checklist, a document edited in place — it saves new versions of itself), keeping state shared across viewers, knowing who is viewing, asking Claude a question of its own, storing files people add, handing the viewer a file to save, or using the viewer's camera, microphone, location, screen or device motion. Serves this user's live capability roster and the typed call definitions. Load it whenever any such runtime behavior would make an artifact more useful, before writing the page.",
      ja: "公開した Artifact ページに付与できるランタイム機能を示す。静的な HTML だけではできない振る舞い（ライブデータや接続先のデータの読み取り、閲覧者の操作の記録（投票、申し込み表、チェックリスト、その場で編集して新しい版を保存するドキュメントなど）、閲覧者のあいだで共有する状態、閲覧者の識別、Claude への独自の質問、閲覧者が追加したファイルの保存、閲覧者へのファイルの受け渡し、閲覧者のカメラ・マイク・位置情報・画面・デバイスの動きの利用など）を扱う。このユーザーの現在の機能一覧と型付きの呼び出し定義を提供する。こうしたランタイムの振る舞いで Artifact が便利になるときは、ページを書く前に読み込む。",
    },
  ],
  "artifact-design": [
    {
      en: "Design guidance and fundamentals for Artifacts.",
      ja: "Artifact のデザインの指針と基本を示す。",
    },
  ],
  "artifact-diagramming": [
    {
      en: "Diagramming know-how for Artifacts - when a picture earns its place, how to draw one that shows the real mechanism, and the inline-SVG mechanics that keep it legible in both themes.",
      ja: "Artifact で図を描くためのノウハウを示す。図が役立つのはどんなときか、実際の仕組みを示す図の描き方、両方のテーマで読みやすく保つインライン SVG の仕組みを扱う。",
    },
  ],
  "artifacts": [
    {
      en: "Browse your published and shared artifacts",
      ja: "公開・共有した Artifact を一覧する。",
    },
  ],
  "auto-mode-setup": [
    {
      en: "Teach auto mode about your environment, plus optional rule tweaks",
      ja: "auto モードに自分の環境を教え、必要ならルールを調整する。",
    },
  ],
  "autocompact": [
    {
      en: "Configure the auto-compact window size",
      ja: "自動コンパクトのウィンドウサイズを設定する。",
    },
  ],
  "background": [
    {
      en: "Send this session to the background and free the terminal",
      ja: "このセッションをバックグラウンドに送り、ターミナルを空ける。",
    },
  ],
  "batch": [
    {
      en: "Research and plan a large-scale change, then execute it in parallel across 5–30 isolated worktree agents that each open a PR.",
      ja: "大規模な変更を調査・計画し、それぞれが PR を開く 5〜30 個の独立した worktree エージェントで並列に実行する。",
    },
  ],
  "branch": [
    {
      en: "Create a branch of the current conversation at this point",
      ja: "会話のこの時点からブランチを作る。",
    },
  ],
  "btw": [
    {
      en: "Ask a quick side question without interrupting the main conversation",
      ja: "メインの会話を中断せずに、ちょっとした質問をする。",
    },
  ],
  "bug": [
    {
      en: "Report a bug or share your conversation",
      ja: "バグを報告する、または会話を共有する。",
    },
  ],
  "cd": [
    {
      en: "Move this session to a new working directory",
      ja: "このセッションを別の作業ディレクトリに移す。",
    },
  ],
  "claude-api": [
    {
      en: "Reference for the Claude API / Anthropic SDK — model ids, pricing, params, streaming, tool use, MCP, agents, caching, token counting, model migration.\nTRIGGER — read BEFORE opening the target file; don't skip because it \"looks like a one-liner\" — whenever: the prompt names Claude/Anthropic in any form (Claude, Anthropic, Fable, Opus, Sonnet, Haiku, `anthropic`, `@anthropic-ai`, `claude-*`, `us.anthropic.*`, `[1m]`); the user asks about an LLM (pricing/model choice/limits/caching) — never answer from memory; OR the task is LLM-shaped with provider unstated (agent/MCP/tool-definition/multi-agent/RAG/LLM-judge/computer-use; generate/summarize/extract/classify/rewrite/converse over NL; debugging refusals/cutoffs/streaming/tool-calls/tokens).\nSKIP only when another provider is being worked on (overrides all triggers): OpenAI/GPT/Gemini/Llama/Mistral/Cohere/Ollama named in the query; OR `grep -rE 'openai|langchain_openai|google.generativeai|genai|mistralai|cohere|ollama'` over the project hits (run this grep FIRST if no provider named — don't Read the file).",
      ja: "Claude API / Anthropic SDK のリファレンスを提供する（モデル ID、料金、パラメーター、ストリーミング、ツール使用、MCP、エージェント、キャッシュ、トークンカウント、モデルの移行）。トリガー: 次のときは、対象のファイルを開く前に読む（「1行で済みそう」に見えても飛ばさない）。プロンプトが Claude / Anthropic に何らかの形で触れているとき（Claude、Anthropic、Fable、Opus、Sonnet、Haiku、`anthropic`、`@anthropic-ai`、`claude-*`、`us.anthropic.*`、`[1m]`）、ユーザーが LLM について尋ねたとき（料金・モデルの選択・上限・キャッシュ。記憶で答えない）、またはプロバイダーが明示されていない LLM 的なタスクのとき（エージェント / MCP / ツール定義 / マルチエージェント / RAG / LLM-judge / computer-use、自然言語の生成・要約・抽出・分類・書き換え・対話、拒否・打ち切り・ストリーミング・ツール呼び出し・トークンのデバッグ）がこれに当たる。スキップ: 別のプロバイダーを扱っているときだけ読まない（すべてのトリガーより優先する）。クエリで OpenAI / GPT / Gemini / Llama / Mistral / Cohere / Ollama が名指しされているとき、またはプロジェクトに対する `grep -rE 'openai|langchain_openai|google.generativeai|genai|mistralai|cohere|ollama'` が一致したときがこれに当たる（プロバイダーが名指しされていなければ、ファイルを Read する前にまずこの grep を実行する）。",
    },
  ],
  "clear": [
    {
      en: "Start a new session with empty context; previous session stays on disk (resumable with /resume)",
      ja: "コンテキストを空にした新しいセッションを始める。前のセッションはディスクに残る（/resume で再開できる）。",
    },
  ],
  "code-review": [
    {
      en: "Review the current diff, or a PR number/branch/path target, for correctness bugs (plus reuse/simplification/efficiency cleanups where the model's review recipe covers them) at the given effort level (low|medium|high|xhigh|max: from few high-confidence findings up to many, some of them uncertain; ultra: deep multi-agent review in the cloud); with no level given, it reuses the level you typed last. Pass --comment to post findings as inline PR comments, or --fix to apply the findings to the working tree after the review. Pass --max-findings <n> to report up to n findings, or --max-findings all for every finding. The choice stays until you pass --max-findings default. For ultra on a GitHub.com PR target, --post asks to post the finished review’s findings to the PR as a single comment from the user’s GitHub account (not a review; the launch dialog still confirms in interactive sessions, while non-interactive mode posts on the flag alone) and --no-post hides that option.",
      ja: "現在の差分、または PR 番号・ブランチ・パスを対象に、指定した effort レベルで正しさのバグ（モデルのレビュー手順が扱う範囲では再利用・簡素化・効率の改善も）をレビューする（low|medium|high|xhigh|max: 確度の高い少数の指摘から、不確かなものを含む多数の指摘まで。ultra: クラウドでのマルチエージェントによる詳細なレビュー）。レベルを省くと前回入力したレベルを使う。--comment で指摘を PR のインラインコメントとして投稿し、--fix でレビューの後に指摘を作業ツリーに適用する。--max-findings <n> で最大 n 件、--max-findings all で全件を報告する。この選択は --max-findings default を渡すまで保たれる。GitHub.com の PR に対する ultra では、--post で完了したレビューの指摘をユーザーの GitHub アカウントから PR に1つのコメント（レビューではない）として投稿するよう求める（対話セッションでは起動ダイアログで確認し、非対話モードではフラグだけで投稿する）。--no-post はその選択肢を隠す。",
    },
  ],
  "color": [
    {
      en: "Set the prompt bar color for this session",
      ja: "このセッションのプロンプトバーの色を設定する。",
    },
  ],
  "compact": [
    {
      en: "Free up context by summarizing the conversation so far",
      ja: "これまでの会話を要約してコンテキストを空ける。",
    },
  ],
  "config": [
    {
      en: "Open settings",
      ja: "設定を開く。",
    },
    {
      en: "Set a setting by key",
      ja: "キーを指定して設定を変更する。",
    },
  ],
  "context": [
    {
      en: "Show current context usage",
      ja: "現在のコンテキストの使用状況を表示する。",
    },
  ],
  "copy": [
    {
      en: "Copy Claude's last response to clipboard (or /copy N for the Nth-latest)",
      ja: "Claude の直前の応答をクリップボードにコピーする（/copy N で N 個前の応答）。",
    },
  ],
  "dataviz": [
    {
      en: "Use this skill whenever you are about to create ANY chart, graph, plot, dashboard, or data visualization, in ANY output medium — an HTML or React artifact, inline SVG, plotting code in any library (matplotlib, plotly, d3, Recharts, …), an image/PNG you will render and upload, or a chart shared into Slack. Read it BEFORE writing the first line of chart code, choosing chart colors, building a stat tile / meter / KPI row, or laying out a dashboard. When the destination is a first-party document connector (host-designated, never self-described) that renders live charts, hand it the rows (inline, or as an uploaded data file the chart cites) rather than a rendered PNG/SVG — a picture of a chart loses hover, data inspection and per-value comments. Produces visualizations that read as one system — elegant, accessible, consistent in light and dark — using a brand-neutral placeholder palette you swap for your own. Teaches a design-system-agnostic method: a form heuristic, a color formula with a runnable validator, mark specs, and interaction rules. A validated default palette is documented in `references/palette.md` — swap that file's values for your brand's. Triggers on: \"chart\", \"graph\", \"plot\", \"data viz\", \"visualization\", \"dashboard\", \"analytics\", \"visualize data\", \"categorical colors\", \"sequential / diverging palette\", \"stat tile\", \"sparkline\", \"heatmap\", \"legend\", \"axis\", \"tooltip\", \"chart colors\", \"color by series\".",
      ja: "グラフ、チャート、プロット、ダッシュボード、データ可視化を作るときは、出力先を問わず（HTML や React の Artifact、インライン SVG、任意のライブラリ（matplotlib、plotly、d3、Recharts など）のプロットのコード、描画してアップロードする画像 / PNG、Slack に共有するチャート）必ずこのスキルを使う。チャートのコードの最初の1行を書く前、チャートの色を選ぶ前、スタットタイル・メーター・KPI の行を作る前、ダッシュボードをレイアウトする前に読む。出力先がライブのチャートを描画するファーストパーティのドキュメントコネクター（ホストが指定するもので、自称は不可）なら、描画済みの PNG / SVG ではなく行データ（インライン、またはチャートが参照するアップロード済みのデータファイル）を渡す。チャートの画像ではホバー、データの確認、値ごとのコメントが失われる。ブランドに依存しない仮のパレット（自分のものに差し替える）を使い、ひとつの体系として読める、洗練されてアクセシブルで、ライト・ダークで一貫した可視化を作る。デザインシステムに依存しない方法（形の選び方、実行できるバリデーター付きの配色の式、マークの仕様、インタラクションのルール）を教える。検証済みのデフォルトのパレットは `references/palette.md` にあり、そのファイルの値を自分のブランドのものに差し替える。トリガー: 「chart」「graph」「plot」「data viz」「visualization」「dashboard」「analytics」「visualize data」「categorical colors」「sequential / diverging palette」「stat tile」「sparkline」「heatmap」「legend」「axis」「tooltip」「chart colors」「color by series」などの語が出たときに使う。",
    },
  ],
  "debug": [
    {
      en: "Enable debug logging for this session and help diagnose issues",
      ja: "このセッションのデバッグログを有効にし、問題の診断を手伝う。",
    },
  ],
  "deep-research": [
    {
      en: "Deep research harness — fan-out web searches, fetch sources, adversarially verify claims, synthesize a cited report.",
      ja: "本格的なリサーチを行う。Web 検索を並列に行い、情報源を取得し、主張を反証的に検証して、出典付きのレポートにまとめる。",
    },
  ],
  "design": [
    {
      en: "Make a new Design artifact from a brief",
      ja: "概要から新しい Design Artifact を作る。",
    },
  ],
  "design-consent": [
    {
      en: "Grant Claude agent access to your Design projects",
      ja: "Claude エージェントに Design プロジェクトへのアクセスを許可する。",
    },
  ],
  "design-login": [
    {
      en: "Authorize design-system access for /design-sync with your claude.ai account",
      ja: "claude.ai アカウントで、/design-sync のデザインシステムへのアクセスを認可する。",
    },
  ],
  "design-revoke": [
    {
      en: "Revoke Claude agent access to your Design projects",
      ja: "Claude エージェントの Design プロジェクトへのアクセスを取り消す。",
    },
  ],
  "design-sync": [
    {
      en: "Push a React design system to claude.ai/design. This runs a converter that bundles the real component code (from Storybook or a bare package) and uploads it. Use when the user runs /design-sync or says \"sync my design system to Claude Design\".",
      ja: "React のデザインシステムを claude.ai/design に送る。実際のコンポーネントのコードを（Storybook または素のパッケージから）バンドルしてアップロードするコンバーターを実行する。ユーザーが /design-sync を実行したときや「デザインシステムを Claude Design に同期して」と言ったときに使う。",
    },
  ],
  "desktop": [
    {
      en: "Continue the current session in Claude Desktop",
      ja: "現在のセッションを Claude Desktop で続ける。",
    },
  ],
  "diff": [
    {
      en: "Toggle the diff panel showing uncommitted changes",
      ja: "未コミットの変更を表示する差分パネルの表示を切り替える。",
    },
  ],
  "doctor": [
    {
      en: "Health-check the user's Claude Code setup and fix issues: diagnose installation health — what the `claude doctor` terminal diagnostics cover — from local data (duplicate or leftover installs, PATH, unparseable settings files, broken or colliding agent definitions, skills whose frontmatter fails to parse); find unused skills, MCP servers, and plugins versus their context cost and disable dead weight; deduplicate local CLAUDE.md files against checked-in ones; trim checked-in CLAUDE.md files by cutting content a session could derive from the codebase (directory layouts, tech-stack lists, architecture overviews) while keeping gotchas, rationale, and non-standard conventions; migrate always-loaded CLAUDE.md guidance into lazy skills and nested CLAUDE.md files; flag slow hooks and context-heavy extensions; check the installed version is current; make auto mode the default permission mode; and pre-approve frequently denied read-only commands. Use when the user asks for a doctor run, checkup, audit, tune-up, or cleanup of their Claude Code setup or configuration.",
      ja: "ユーザーの Claude Code のセットアップを点検し、問題を直す。ローカルのデータからインストールの状態を診断する（`claude doctor` のターミナル診断が扱う範囲。重複や残ったインストール、PATH、解析できない設定ファイル、壊れた・衝突するエージェント定義、frontmatter を解析できないスキル）。コンテキストのコストに見合わない未使用のスキル・MCP サーバー・プラグインを見つけて無効にする。ローカルの CLAUDE.md をチェックイン済みのものと重複排除する。チェックイン済みの CLAUDE.md から、セッションがコードベースから導ける内容（ディレクトリ構成、技術スタックの一覧、アーキテクチャの概要）を削り、落とし穴・理由・標準的でない規約は残す。常に読み込まれる CLAUDE.md の指示を、遅延読み込みのスキルやネストした CLAUDE.md に移す。遅いフックやコンテキストを多く使う拡張を指摘する。インストール済みのバージョンが最新か確かめる。auto モードをデフォルトのパーミッションモードにする。よく拒否される読み取り専用のコマンドを事前に許可する。ユーザーが doctor の実行、点検、監査、調整、Claude Code のセットアップや設定の整理を頼んだときに使う。",
    },
  ],
  "effort": [
    {
      en: "Set effort level for model usage",
      ja: "モデルの effort レベルを設定する。",
    },
  ],
  "exit": [
    {
      en: "Exit the CLI",
      ja: "CLI を終了する。",
    },
  ],
  "export": [
    {
      en: "Export the current conversation to a file or clipboard",
      ja: "現在の会話をファイルまたはクリップボードに書き出す。",
    },
  ],
  "extra-usage": [
    {
      en: "Renamed to /usage-credits",
      ja: "/usage-credits に名前が変わった。",
    },
  ],
  "fast": [
    {
      en: "Toggle fast mode ({})",
      ja: "fast モードを切り替える（{}）。",
    },
  ],
  "feedback": [
    {
      en: "Send feedback to Anthropic or report a bug",
      ja: "Anthropic にフィードバックを送る、またはバグを報告する。",
    },
  ],
  "fewer-permission-prompts": [
    {
      en: "Scan your transcripts for common read-only Bash and MCP tool calls, then add a prioritized allowlist to project .claude/settings.json to reduce permission prompts.",
      ja: "トランスクリプトからよく使われる読み取り専用の Bash と MCP のツール呼び出しを探し、優先度付きの許可リストをプロジェクトの .claude/settings.json に追加して、パーミッションの確認を減らす。",
    },
  ],
  "focus": [
    {
      en: "Toggle focus view: just your prompt, summary, and response",
      ja: "フォーカス表示（プロンプト、要約、応答だけ）を切り替える。",
    },
  ],
  "fork": [
    {
      en: "Copy this conversation into a new background session and keep working here",
      ja: "この会話を新しいバックグラウンドセッションにコピーし、ここでは作業を続ける。",
    },
  ],
  "goal": [
    {
      en: "Set a goal Claude checks before stopping",
      ja: "Claude が止まる前に確かめるゴールを設定する。",
    },
    {
      en: "Set a goal — keep working until the condition is met",
      ja: "ゴールを設定する。条件を満たすまで作業を続ける。",
    },
  ],
  "heapdump": [
    {
      en: "Dump the JS heap to the Desktop; on Linux with no Desktop folder, the home directory",
      ja: "JS ヒープをデスクトップに書き出す（デスクトップフォルダの無い Linux ではホームディレクトリ）。",
    },
  ],
  "help": [
    {
      en: "Show help and available commands",
      ja: "ヘルプと使えるコマンドを表示する。",
    },
  ],
  "hooks": [
    {
      en: "View hook configurations for tool events",
      ja: "ツールイベントのフック設定を表示する。",
    },
  ],
  "ide": [
    {
      en: "Manage IDE integrations and show status",
      ja: "IDE 連携を管理し、状態を表示する。",
    },
  ],
  "import": [
    {
      en: "Import config from another AI coding agent",
      ja: "別の AI コーディングエージェントから設定を取り込む。",
    },
  ],
  "init": [
    {
      en: "Initialize a new CLAUDE.md file with codebase documentation",
      ja: "コードベースの説明を書いた CLAUDE.md を新しく作る。",
    },
  ],
  "insights": [
    {
      en: "Generate a report analyzing your Claude Code sessions",
      ja: "Claude Code のセッションを分析したレポートを作る。",
    },
  ],
  "install-github-app": [
    {
      en: "Set up Claude GitHub Actions for a repository",
      ja: "リポジトリに Claude GitHub Actions を設定する。",
    },
  ],
  "install-slack-app": [
    {
      en: "Install the Claude Slack app",
      ja: "Claude Slack アプリをインストールする。",
    },
  ],
  "keybindings": [
    {
      en: "Open your keyboard shortcuts file",
      ja: "キーボードショートカットの設定ファイルを開く。",
    },
  ],
  "keybindings-help": [
    {
      en: "Use when the user wants to customize keyboard shortcuts, rebind keys, add chord bindings, or modify ~/.claude/keybindings.json. Examples: \"rebind ctrl+s\", \"add a chord shortcut\", \"change the submit key\", \"customize keybindings\".",
      ja: "キーボードショートカットのカスタマイズ、キーの割り当て直し、コードバインド（複数キーの組み合わせ）の追加、~/.claude/keybindings.json の変更をしたいときに使う。例えば「ctrl+s を割り当て直して」「コードのショートカットを追加して」「送信キーを変えて」「キーバインドをカスタマイズして」といった依頼に使う。",
    },
  ],
  "list-agents": [
    {
      en: "List subagents, teammates, and other Claude sessions you can message",
      ja: "メッセージを送れるサブエージェント、チームメイト、他の Claude セッションを一覧する。",
    },
  ],
  "login": [
    {
      en: "Sign in with your Anthropic account",
      ja: "Anthropic アカウントでサインインする。",
    },
  ],
  "logout": [
    {
      en: "Sign out from your Anthropic account",
      ja: "Anthropic アカウントからサインアウトする。",
    },
  ],
  "loop": [
    {
      en: "Run a prompt or slash command on a recurring interval (e.g. /loop 5m /foo). Omit the interval to let the model self-pace.",
      ja: "プロンプトやスラッシュコマンドを一定の間隔で繰り返し実行する（例: /loop 5m /foo）。間隔を省くとモデルが自分でペースを決める。",
    },
  ],
  "mcp": [
    {
      en: "Manage MCP servers",
      ja: "MCP サーバーを管理する。",
    },
  ],
  "memory": [
    {
      en: "Edit CLAUDE.md files and memory settings",
      ja: "CLAUDE.md ファイルとメモリの設定を編集する。",
    },
  ],
  "mobile": [
    {
      en: "Show QR code to download the Claude mobile app",
      ja: "Claude モバイルアプリをダウンロードする QR コードを表示する。",
    },
  ],
  "model": [
    {
      en: "Set the AI model for Claude Code (currently {})",
      ja: "Claude Code の AI モデルを設定する（現在は {}）。",
    },
    {
      en: "Set the AI model for Claude Code",
      ja: "Claude Code の AI モデルを設定する。",
    },
  ],
  "output-style": [
    {
      en: "List output styles or switch to one",
      ja: "出力スタイルを一覧する、または切り替える。",
    },
  ],
  "passes": [
    {
      en: "Share a free week of Claude Code with friends and earn usage credits",
      ja: "Claude Code の1週間の無料パスを友人に共有し、使用量クレジットを得る。",
    },
  ],
  "permissions": [
    {
      en: "Manage allow and deny tool permission rules",
      ja: "ツールの許可・拒否のパーミッションルールを管理する。",
    },
  ],
  "plan": [
    {
      en: "Enable plan mode or view the current session plan",
      ja: "プランモードを有効にする、または現在のセッションのプランを表示する。",
    },
  ],
  "plugin": [
    {
      en: "Manage Claude Code plugins",
      ja: "Claude Code のプラグインを管理する。",
    },
  ],
  "plugin-authoring": [
    {
      en: "Make a mod: a change to Claude's own interface or behaviour, such as a panel or pane that stays beside the chat and updates, a band, status line, toast, slash command, or hook on tool calls. Use to make, change or debug a mod or its hooks module.",
      ja: "mod を作る。mod は Claude 自身のインターフェースや振る舞いを変えるもので、チャットの横に置かれて更新されるパネルやペイン、帯、ステータスライン、トースト、スラッシュコマンド、ツール呼び出しへのフックなどがある。mod やその hooks モジュールの作成・変更・デバッグに使う。",
    },
  ],
  "powerup": [
    {
      en: "Discover Claude Code features through quick interactive lessons",
      ja: "短い対話型のレッスンで Claude Code の機能を知る。",
    },
  ],
  "privacy-settings": [
    {
      en: "View and update your privacy settings",
      ja: "プライバシー設定を表示・変更する。",
    },
  ],
  "radio": [
    {
      en: "Listen to Claude FM lo-fi radio",
      ja: "Claude FM の lo-fi ラジオを聴く。",
    },
  ],
  "rate-limit-options": [
    {
      en: "Manage usage limits and upgrade options",
      ja: "使用量の上限とアップグレードの選択肢を管理する。",
    },
  ],
  "recap": [
    {
      en: "Generate a one-line session recap now",
      ja: "セッションの1行の要約を今すぐ作る。",
    },
  ],
  "release-notes": [
    {
      en: "View release notes",
      ja: "リリースノートを表示する。",
    },
  ],
  "reload-plugins": [
    {
      en: "Activate pending plugin changes in the current session",
      ja: "保留中のプラグインの変更を現在のセッションで有効にする。",
    },
  ],
  "reload-skills": [
    {
      en: "Pick up skills added or changed on disk during this session",
      ja: "このセッション中にディスク上で追加・変更されたスキルを読み込む。",
    },
  ],
  "remote-control": [
    {
      en: "Disconnect Remote Control",
      ja: "Remote Control を切断する。",
    },
  ],
  "remote-env": [
    {
      en: "Choose the default environment for cloud agents",
      ja: "クラウドエージェントのデフォルトの環境を選ぶ。",
    },
  ],
  "rename": [
    {
      en: "Rename the current conversation",
      ja: "現在の会話の名前を変える。",
    },
  ],
  "resume": [
    {
      en: "Resume a previous conversation",
      ja: "以前の会話を再開する。",
    },
  ],
  "rewind": [
    {
      en: "Restore the code and/or conversation to a previous point",
      ja: "コードと会話（またはそのどちらか）を以前の時点に戻す。",
    },
  ],
  "run": [
    {
      en: "Launch and drive this project's app to see a change working. Use when asked to run, start, or screenshot the app, or to confirm a change works in the real app (not just tests). First looks for a project skill that already covers launching the app; otherwise falls back to built-in patterns per project type (CLI, server, TUI, Electron, browser-driven, library).",
      ja: "このプロジェクトのアプリを起動・操作して、変更が動くことを確かめる。アプリの実行・起動・スクリーンショットを頼まれたときや、変更が（テストだけでなく）実際のアプリで動くことを確かめるときに使う。まずアプリの起動を扱うプロジェクトのスキルを探し、無ければプロジェクトの種類（CLI、サーバー、TUI、Electron、ブラウザー操作、ライブラリ）ごとの組み込みのやり方を使う。",
    },
  ],
  "run-skill-generator": [
    {
      en: "Author or improve the run-<unit> skill - a per-project skill that tells agents how to build, launch, and drive this project's app. Use when the user asks to set up the project, get it running, write run instructions, or verify build/run steps work from a clean environment.",
      ja: "run-<unit> スキル（このプロジェクトのアプリのビルド・起動・操作の方法をエージェントに教える、プロジェクトごとのスキル）を作る・改善する。プロジェクトのセットアップ、アプリを動かすこと、実行手順を書くこと、クリーンな環境からビルド・実行の手順が通るかの確認を頼まれたときに使う。",
    },
  ],
  "sandbox": [
    {
      en: "{} sandbox enabled (⏎ to configure)",
      ja: "{} サンドボックスが有効になっている（⏎ で設定する）。",
    },
  ],
  "schedule": [
    {
      en: "Create, update, list, or run scheduled cloud agents (routines) that execute on a cron schedule.",
      ja: "cron のスケジュールで実行するクラウドエージェント（ルーティン）を作成・更新・一覧・実行する。",
    },
  ],
  "scroll-speed": [
    {
      en: "Adjust mouse wheel scroll speed",
      ja: "マウスホイールのスクロール速度を調整する。",
    },
  ],
  "security-review": [
    {
      en: "Complete a security review of the pending changes on the current branch",
      ja: "現在のブランチの保留中の変更をセキュリティレビューする。",
    },
  ],
  "simplify": [
    {
      en: "Review the changed code for reuse, simplification, efficiency, and altitude cleanups, then apply the fixes. Quality only — it does not hunt for bugs; use /code-review for that.",
      ja: "変更したコードを再利用・簡素化・効率・抽象度の観点でレビューし、修正を適用する。品質だけを見てバグは探さない（バグは /code-review を使う）。",
    },
  ],
  "skill-doctor": [
    {
      en: "Show which loaded skills are unused and costing context",
      ja: "読み込まれたスキルのうち、使われずにコンテキストを消費しているものを表示する。",
    },
  ],
  "skills": [
    {
      en: "List available skills",
      ja: "使えるスキルを一覧する。",
    },
  ],
  "slides": [
    {
      en: "Make a new Slides deck artifact from a brief",
      ja: "概要から新しい Slides のデッキの Artifact を作る。",
    },
  ],
  "status": [
    {
      en: "Show Claude Code status including version, model, account, API connectivity, and tool statuses",
      ja: "Claude Code の状態（バージョン、モデル、アカウント、API への接続、ツールの状態）を表示する。",
    },
  ],
  "statusline": [
    {
      en: "Set up Claude Code's status line UI",
      ja: "Claude Code のステータスラインの UI を設定する。",
    },
  ],
  "stickers": [
    {
      en: "Order Claude Code stickers",
      ja: "Claude Code のステッカーを注文する。",
    },
  ],
  "subtask": [
    {
      en: "Send a subagent off with your full context; its result comes back here",
      ja: "会話の全コンテキストを持たせてサブエージェントを送り出す。結果はここに戻る。",
    },
  ],
  "tasks": [
    {
      en: "View and manage everything running in the background",
      ja: "バックグラウンドで実行中のものをすべて表示・管理する。",
    },
  ],
  "team-onboarding": [
    {
      en: "Help teammates ramp on Claude Code with a guide from your usage",
      ja: "自分の使い方をもとにしたガイドで、チームメイトが Claude Code に慣れるのを手伝う。",
    },
  ],
  "teleport": [
    {
      en: "Send this session to the cloud, or resume one from claude.ai",
      ja: "このセッションをクラウドに送る、または claude.ai のセッションを再開する。",
    },
  ],
  "terminal-setup": [
    {
      en: "Install Shift+Enter key binding for newlines",
      ja: "改行用の Shift+Enter のキーバインドをインストールする。",
    },
  ],
  "theme": [
    {
      en: "Change the theme",
      ja: "テーマを変える。",
    },
  ],
  "tui": [
    {
      en: "Set the terminal UI renderer (default | fullscreen)",
      ja: "ターミナル UI のレンダラーを設定する（default | fullscreen）。",
    },
  ],
  "ultrareview": [
    {
      en: "Start a cloud agent that finds and verifies bugs in your branch (~5-15 min, $5-$25 USD) · Runs in a cloud session. See https://code.claude.com/docs/en/claude-code-on-the-web",
      ja: "ブランチのバグを見つけて検証するクラウドエージェントを起動する（約 5〜15 分、5〜25 米ドル）· クラウドセッションで実行する。詳しくは https://code.claude.com/docs/en/claude-code-on-the-web を参照する。",
    },
  ],
  "update-config": [
    {
      en: "Use this skill to configure the Claude Code harness via settings.json. Automated behaviors (\"from now on when X\", \"each time X\", \"whenever X\", \"before/after X\") require hooks configured in settings.json - the harness executes these, not Claude, so memory/preferences cannot fulfill them. Also use for: permissions (\"allow X\", \"add permission\", \"move permission to\"), env vars (\"set X=Y\"), hook troubleshooting, or any changes to settings.json/settings.local.json files. Examples: \"allow npm commands\", \"add bq permission to global settings\", \"move permission to user settings\", \"set DEBUG=true\", \"when claude stops show X\". For simple settings like theme/model, suggest the /config command.",
      ja: "settings.json で Claude Code のハーネスを設定するときに使う。自動の振る舞い（「今後 X のときは」「X のたびに」「X するときはいつも」「X の前 / 後に」）には settings.json に設定したフックが必要で、実行するのは Claude ではなくハーネスなので、メモリや好みの設定では実現できない。ほかに、パーミッション（「X を許可して」「パーミッションを追加して」「パーミッションを〜に移して」）、環境変数（「X=Y を設定して」）、フックのトラブルシューティング、settings.json / settings.local.json の変更にも使う。例えば「npm コマンドを許可して」「グローバル設定に bq のパーミッションを追加して」「パーミッションをユーザー設定に移して」「DEBUG=true を設定して」「Claude が止まったら X を表示して」といった依頼に使う。テーマやモデルのような単純な設定には /config コマンドを勧める。",
    },
  ],
  "upgrade": [
    {
      en: "Upgrade to Max for higher rate limits and more Opus",
      ja: "より高いレート制限とより多くの Opus を使える Max にアップグレードする。",
    },
  ],
  "usage": [
    {
      en: "Show session cost, plan usage, and activity stats",
      ja: "セッションのコスト、プランの使用量、アクティビティの統計を表示する。",
    },
    {
      en: "Show session cost, plan usage, and what's contributing to your limits",
      ja: "セッションのコスト、プランの使用量、上限を消費している要因を表示する。",
    },
  ],
  "usage-credits": [
    {
      en: "Configure usage credits or request them from your admin when you hit a limit",
      ja: "上限に達したときのために使用量クレジットを設定する、または管理者に依頼する。",
    },
  ],
  "verify": [
    {
      en: "Verify that a code change actually does what it's supposed to by exercising it end-to-end and observing behavior — drive the affected flow, not just tests or typecheck. Run before committing nontrivial changes; bootstraps this repo's project verify skill if none exists yet. Don't invoke it on a diff that only touches tests, docs, or other code with no runtime surface to drive (a change to product source always has one) — there's nothing to observe.",
      ja: "コードの変更が本来の動作をするかを、エンドツーエンドで動かして振る舞いを観察して確かめる。テストや型チェックだけでなく、影響を受けるフローを実際に操作する。自明でない変更をコミットする前に実行する。このリポジトリにプロジェクトの verify スキルがまだ無ければ作る。テスト、ドキュメント、その他動かして確かめる実行面の無いコードだけを変える差分には、観察するものが無いので使わない（製品のソースの変更には実行面が必ずある）。",
    },
  ],
  "voice": [
    {
      en: "Toggle voice mode",
      ja: "音声モードを切り替える。",
    },
  ],
  "web-setup": [
    {
      en: "Set up cloud sessions with your GitHub account",
      ja: "GitHub アカウントでクラウドセッションを設定する。",
    },
  ],
  "workflow-authoring": [
    {
      en: "Reference for writing a Workflow tool script (script API and gotchas, resume, quality patterns, worked examples). Load before authoring a script for a workflow the user already opted into; it does not itself authorize running one.",
      ja: "Workflow ツールのスクリプトを書くためのリファレンスを提供する（スクリプト API と注意点、再開、品質のパターン、実例）。ユーザーがすでに同意したワークフローのスクリプトを書く前に読み込む。このスキル自体はワークフローの実行を許可しない。",
    },
  ],
  "workflow-launch-exec": [
    {
      en: "Execute a server-launched workflow handoff (workflow_launch event sessions only)",
      ja: "サーバーから起動したワークフローの引き継ぎを実行する（workflow_launch イベントのセッションのみ）。",
    },
  ],
  "workflows": [
    {
      en: "Browse running and completed workflows",
      ja: "実行中・完了したワークフローを一覧する。",
    },
  ],
  // ---- Anthropic 提供のプラグイン
  "anthropic-skills:built-in-browser": [
    {
      en: "Read this skill before the first step that uses the built-in browser, the browser pane inside the Claude desktop app (also called the in-app browser, the browser pane, Claude's browser, or \"your own browser\"), whose tools are named mcp__Claude_Browser__* when the session runs in the desktop app and mcp__remote-devices__Claude_Browser__* when a cloud session is linked to the person's computer; before those tools are turned on there may be a single enable__mcp__remote-devices__Claude_Browser tool instead. It covers the pane's persistent sign-ins, tabs and preview_start, reading pages as text, site approvals, what the pane cannot open, and what to do when it cannot be reached. It is not for Claude in Chrome (mcp__claude-in-chrome__* tools), which has its own skill, and it does not decide which browser to use.",
      ja: "内蔵ブラウザーを使う最初の手順の前に読む。内蔵ブラウザーは Claude デスクトップアプリ内のブラウザーペイン（アプリ内ブラウザー、ブラウザーペイン、Claude のブラウザー、「自分のブラウザー」とも呼ぶ）で、ツール名はデスクトップアプリで動くセッションでは mcp__Claude_Browser__*、クラウドセッションがユーザーのコンピューターにつながっているときは mcp__remote-devices__Claude_Browser__* である。これらのツールが有効になる前は、enable__mcp__remote-devices__Claude_Browser ツールが1つだけある場合がある。ペインに残るサインイン、タブと preview_start、ページのテキストとしての読み取り、サイトの承認、ペインで開けないもの、接続できないときの対処を扱う。Claude in Chrome（mcp__claude-in-chrome__* ツール）は別のスキルがあるので対象外で、どちらのブラウザーを使うかも決めない。",
    },
  ],
  "anthropic-skills:chrome-browser": [
    {
      en: "Read this skill before the first step that uses Claude in Chrome, the browser extension whose tools are named mcp__claude-in-chrome__* (also called Chrome, the browser extension, or the external browser) and which acts in the person's real Chrome with their own sign-ins; before those tools are turned on there may be a single enable__mcp__claude-in-chrome tool instead. It covers loading the tools in one ToolSearch call, checking the person's open tabs and working in a new tab, site permissions, GIF recordings, console logs, dialogs to avoid, and when to stop and ask. It is not for the built-in browser (mcp__Claude_Browser__* or mcp__remote-devices__Claude_Browser__* tools), which has its own skill, and it does not decide which browser to use.",
      ja: "Claude in Chrome を使う最初の手順の前に読む。Claude in Chrome はツール名が mcp__claude-in-chrome__* のブラウザー拡張（Chrome、ブラウザー拡張、外部ブラウザーとも呼ぶ）で、ユーザー自身のサインイン状態のまま実際の Chrome を操作する。これらのツールが有効になる前は、enable__mcp__claude-in-chrome ツールが1つだけある場合がある。ToolSearch の1回の呼び出しでのツールの読み込み、ユーザーが開いているタブの確認と新しいタブでの作業、サイトの権限、GIF の録画、コンソールのログ、避けるべきダイアログ、止めて確認すべきときを扱う。内蔵ブラウザー（mcp__Claude_Browser__* または mcp__remote-devices__Claude_Browser__* ツール）は別のスキルがあるので対象外で、どちらのブラウザーを使うかも決めない。",
    },
  ],
  "anthropic-skills:computer-use": [
    {
      en: "Read this skill before the first step of any request to do something in an app on the person's own computer (Notes, Finder, System Settings, any desktop app), to look at their screen, or for \"computer use\". Computer use (desktop control) lets Claude take screenshots of the person's desktop and control it with clicks, typing and scrolling through the Claude desktop app; its tools are named mcp__computer-use__* when the session runs in the desktop app and mcp__remote-devices__computer_* when a cloud session is linked to the person's computer; before computer use is turned on for a conversation there may be no such tools, only an enable__mcp__remote-devices__computer tool, which turns it on. It covers turning it on, picking the right tool, the access flow, and the safety rules for tiered apps, links and financial actions. It is not for websites, which go through Claude in Chrome or the built-in browser and their own skills.",
      ja: "ユーザー自身のコンピューターのアプリ（メモ、Finder、システム設定、任意のデスクトップアプリ）で何かをする依頼、画面を見る依頼、「computer use」の依頼では、最初の手順の前に読む。computer use（デスクトップの操作）では、Claude デスクトップアプリを通じて、Claude がユーザーのデスクトップのスクリーンショットを撮り、クリック・入力・スクロールで操作する。ツール名はデスクトップアプリで動くセッションでは mcp__computer-use__*、クラウドセッションがユーザーのコンピューターにつながっているときは mcp__remote-devices__computer_* である。会話で computer use が有効になる前はこれらのツールが無く、有効にする enable__mcp__remote-devices__computer ツールだけがある場合がある。有効にする方法、適切なツールの選び方、アクセスの流れ、段階的な権限のアプリ・リンク・金融操作に関する安全のルールを扱う。Web サイトは Claude in Chrome か内蔵ブラウザーとそれぞれのスキルで扱うので対象外である。",
    },
  ],
  "anthropic-skills:consolidate-memory": [
    {
      en: "Reflective pass over your memory files — merge duplicates, fix stale facts, prune the index.",
      ja: "メモリファイルを振り返って整理する。重複をまとめ、古くなった事実を直し、索引を刈り込む。",
    },
  ],
  "anthropic-skills:deep-research": [
    {
      en: "Use this skill when the user's prompt requires (1) researching a topic across multiple sources, comparing options or alternatives, analyzing trends or history, understanding markets or industries, or reviewing literature or studies and (2) synthesizing that research into a comprehensive, narrative report. If you're planning to search the web or internal knowledge bases, consider using this skill. This skill coordinates research subagents, so use it only when you have a tool for spawning subagents (the Agent or Task tool); otherwise, research the question directly.",
      ja: "ユーザーのプロンプトが (1) 複数の情報源にまたがるトピックの調査、選択肢や代替案の比較、傾向や歴史の分析、市場や業界の理解、文献や研究のレビューを必要とし、かつ (2) その調査を包括的な文章のレポートにまとめる必要があるときに使う。Web や社内のナレッジベースを検索するつもりなら、このスキルの利用を検討する。このスキルは調査用のサブエージェントを指揮するので、サブエージェントを起動するツール（Agent または Task ツール）があるときだけ使い、無ければ直接調べる。",
    },
  ],
  "anthropic-skills:docs": [
    {
      en: "docs (editable docs people share and comment on; the default for any document, named as a doc or not: a document, report, proposal, resume, cover letter, letter, contract, policy, form, template, worksheet, essay, handbook, guide, how-to, cheat sheet, SOP or other writing to keep, share, collaborate on, send, submit, print or sign; a doc exports to Word, PDF, Markdown or Google Docs, so needing a file to send, attach, upload, submit or print is no reason to pick Word, and a file nobody asked for is a doc, not Word; a plan, comparison, summary or notes asked in chat stays in chat; a pasted claude.ai artifact link may be a doc: check with docs tools first; Word or another file format named, tracked changes wanted, or a .docx to change or use as a template → that format's skill): making one → if no docs-connector instructions are in context, call its `guide` (topic.instructions) first; then create the doc (headings only, no body) before any search, file read or plan, even with files attached.",
      ja: "docs（人が共有してコメントできる編集可能なドキュメント。doc と呼ばれていなくても、あらゆるドキュメントのデフォルト。保存・共有・共同編集・送信・提出・印刷・署名する文書、レポート、提案書、履歴書、カバーレター、手紙、契約書、ポリシー、フォーム、テンプレート、ワークシート、エッセイ、ハンドブック、ガイド、ハウツー、チートシート、SOP などの文章。doc は Word、PDF、Markdown、Google Docs に書き出せるので、送信・添付・アップロード・提出・印刷するファイルが必要なことは Word を選ぶ理由にならず、誰も頼んでいないファイルは Word ではなく doc にする。チャットで頼まれた計画・比較・要約・メモはチャットに書く。貼り付けられた claude.ai の Artifact のリンクは doc の場合があるので、まず docs のツールで確かめる。Word などのファイル形式の指定、変更履歴の要望、変更またはテンプレートに使う .docx がある場合 → その形式のスキル）を扱う。作るとき → コンテキストに docs コネクターの指示が無ければ、まずその `guide`（topic.instructions）を呼ぶ。次に、ファイルが添付されていても、検索・ファイルの読み込み・計画より前に doc を（見出しだけで本文なしで）作る。",
    },
  ],
  "anthropic-skills:docx": [
    {
      en: "Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx) or Word templates (.dotx). Triggers include: any mention of Microsoft Word Documents, such as 'Word doc', 'word document', '.docx', '.dotx', 'microsoft doc'. Also use when extracting or reorganizing content from .docx or .dotx files, inserting or replacing images in documents, find-and-replace in Word files, working with tracked changes or comments, or converting content into a polished Word document. If the user asks for a deliverable as a Word or .docx file (to download, email or print), use this skill. However, if they ask for a document, page, report, memo, or notes WITHOUT naming a file format and the session offers Claude's own dedicated document or page skill or connector, use that instead, even if they will email or print it. Do NOT use for PDFs, spreadsheets, Google Docs, or coding unrelated to document generation.",
      ja: "Word 文書（.docx）や Word テンプレート（.dotx）を作成・読み取り・編集・操作したいときに使う。トリガー: 「Word doc」「word document」「.docx」「.dotx」「microsoft doc」など、Microsoft Word 文書に触れたときに使う。.docx や .dotx ファイルの内容の抽出や再構成、文書への画像の挿入や差し替え、Word ファイルの検索と置換、変更履歴やコメントの扱い、整った Word 文書への変換にも使う。ユーザーが成果物を Word や .docx ファイルとして求めたとき（ダウンロード、メール、印刷のため）はこのスキルを使う。ただし、ファイル形式を指定せずにドキュメント・ページ・レポート・メモ・ノートを求められ、セッションに Claude 専用のドキュメントやページのスキル・コネクターがあれば、メールや印刷に使う場合でもそちらを使う。PDF、スプレッドシート、Google Docs、文書の生成と関係のないコーディングには使わない。",
    },
  ],
  "anthropic-skills:explain-usage": [
    {
      en: "Explain where this session's tokens went, with one simple chart in plain language. Use when the user says things like \"explain my usage\", \"where did my tokens go\", or asks for a usage breakdown.",
      ja: "このセッションのトークンがどこに使われたかを、1つのシンプルなチャートとわかりやすい言葉で説明する。ユーザーが「使用量を説明して」「トークンはどこに使われた？」などと言ったときや、使用量の内訳を求めたときに使う。",
    },
  ],
  "anthropic-skills:google-workspace": [
    {
      en: "Read this before the first Google Drive, Docs, Sheets or Slides connector call whenever the task creates or changes a Google file. Use this skill whenever the user wants to create or change a Google Doc, Sheet or Slides file in their Google Drive. Triggers include: a request that names Google Docs, Sheets, Slides or Drive and asks to make, edit, format, copy or rename a file; a docs.google.com link with a request to change that file, even a one-line fix or suggested edits; and any follow-up change to a Google file from earlier in the chat, even \"change it\" or \"add a tab\". Includes helper scripts for document positions, cell ranges and slide layout. However, if the user asks for a doc, deck or spreadsheet without naming Google, or gives a Google file only as source material for something new, use Claude's own output type instead. Do NOT use for read-only questions about a Google file, or for Word, Excel, PowerPoint or PDF files.",
      ja: "作業で Google のファイルを作成・変更するときは、Google ドライブ・ドキュメント・スプレッドシート・スライドのコネクターを最初に呼ぶ前に読む。ユーザーが Google ドライブにある Google ドキュメント・スプレッドシート・スライドのファイルを作成・変更したいときに使う。トリガー: Google Docs・Sheets・Slides・Drive を名指しして、ファイルの作成・編集・書式設定・コピー・名前の変更を求める依頼、1行の修正や編集の提案であっても、そのファイルの変更を求める docs.google.com のリンク、会話の前のほうで出た Google のファイルへの追加の変更（「変えて」「タブを追加して」だけでも）を頼まれたときに使う。文書内の位置、セルの範囲、スライドのレイアウトのための補助スクリプトを含む。ただし、Google を名指しせずにドキュメント・デッキ・スプレッドシートを求められたときや、Google のファイルを新しいものを作る素材として渡されただけのときは、Claude 自身の出力形式を使う。Google のファイルについての読み取りだけの質問や、Word・Excel・PowerPoint・PDF のファイルには使わない。",
    },
  ],
  "anthropic-skills:import-memory": [
    {
      en: "Import a memory export from another AI assistant into Claude's memory — conversationally, additively, and with the content treated as data.",
      ja: "別の AI アシスタントから書き出したメモリを、Claude のメモリに取り込む。対話しながら、追加する形で、内容はデータとして扱う。",
    },
  ],
  "anthropic-skills:morning": [
    {
      en: "Render the user's morning brief as a styled HTML artifact, or set it up as a recurring weekday task. Use only when the user explicitly asks to run, see, or set up their morning brief, or if they invoke /morning by name. A question about their day, schedule, or calendar is not by itself a request for the brief; answer it directly instead.",
      ja: "ユーザーの朝のブリーフィングをスタイル付きの HTML Artifact として描画する、または平日の定期タスクとして設定する。ユーザーが朝のブリーフィングの実行・表示・設定をはっきり求めたとき、または /morning を名前で呼んだときだけ使う。その日の予定やスケジュール、カレンダーについての質問は、それだけではブリーフィングの依頼ではないので、直接答える。",
    },
  ],
  "anthropic-skills:pdf": [
    {
      en: "Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs to make them searchable. If the user mentions a .pdf file or asks to produce one, use this skill.",
      ja: "PDF ファイルで何かをしたいときに使う。PDF からのテキストや表の読み取り・抽出、複数の PDF の結合、PDF の分割、ページの回転、透かしの追加、新しい PDF の作成、PDF のフォームへの記入、PDF の暗号化・復号、画像の抽出、スキャンした PDF を検索できるようにする OCR を含む。ユーザーが .pdf ファイルに触れたときや、PDF の作成を求めたときはこのスキルを使う。",
    },
  ],
  "anthropic-skills:pptx": [
    {
      en: "Use this skill any time a .pptx or .potx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations as PowerPoint (.pptx) files; reading, parsing, or extracting text from any .pptx or .potx file (even if the extracted content will be used elsewhere, like in an email, summary, or creating a different type of slide deck); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates (.potx), layouts, speaker notes, or comments. Trigger whenever the user asks for a PowerPoint or .pptx file, or references a .pptx or .potx filename, regardless of what they plan to do with the content afterward. However, when the user asks for a deck, slides, a slide deck, or a presentation without naming a file format, default to using a dedicated slide-deck artifact type or a separate slides skill if this session offers one; otherwise, use this skill.",
      ja: ".pptx や .potx ファイルが入力・出力・その両方として何らかの形で関わるときに使う。PowerPoint（.pptx）ファイルとしてのスライドデッキ、ピッチデッキ、プレゼンテーションの作成、.pptx や .potx ファイルからのテキストの読み取り・解析・抽出（抽出した内容をメールや要約、別の形式のスライドデッキなど他で使う場合も含む）、既存のプレゼンテーションの編集・変更・更新、スライドファイルの結合や分割、テンプレート（.potx）・レイアウト・スピーカーノート・コメントの扱いを含む。ユーザーが PowerPoint や .pptx ファイルを求めたとき、または .pptx や .potx のファイル名に触れたときは、その後で内容をどう使うかに関係なくトリガーする。ただし、ファイル形式を指定せずにデッキ・スライド・スライドデッキ・プレゼンテーションを求められたときは、セッションにあれば専用のスライドデッキの Artifact 形式や別のスライド用のスキルを優先し、無ければこのスキルを使う。",
    },
  ],
  "anthropic-skills:setup-claude": [
    {
      en: "Guided setup — install role-matched plugins, connect your tools, try a skill.",
      ja: "ガイド付きのセットアップを行う。役割に合ったプラグインを入れ、ツールをつなぎ、スキルを試す。",
    },
  ],
  "anthropic-skills:setup-cowork": [
    {
      en: "Guided setup — install role-matched plugins, connect your tools, try a skill.",
      ja: "ガイド付きのセットアップを行う。役割に合ったプラグインを入れ、ツールをつなぎ、スキルを試す。",
    },
  ],
  "anthropic-skills:skill-creator": [
    {
      en: "Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.",
      ja: "新しいスキルの作成、既存のスキルの変更と改善、スキルの性能の測定を行う。スキルをゼロから作る、スキルを編集・最適化する、eval でスキルをテストする、ばらつきの分析付きでスキルの性能をベンチマークする、スキルの description を最適化してトリガーの精度を上げる、といったときに使う。",
    },
  ],
  "anthropic-skills:xlsx": [
    {
      en: "Use this skill any time a spreadsheet file is the primary input or output. This means any task where the user wants to: open, read, edit, or fix an existing .xlsx, .xlsm, .xltx, .csv, or .tsv file (e.g., adding columns, computing formulas, formatting, charting, cleaning messy data); create a new spreadsheet from scratch or from other data sources; or convert between tabular file formats. Trigger especially when the user references a spreadsheet file by name or path — even casually (like \"the xlsx in my downloads\") — and wants something done to it or produced from it. Also trigger for cleaning or restructuring messy tabular data files (malformed rows, misplaced headers, junk data) into proper spreadsheets. The deliverable must be a spreadsheet file. Do NOT trigger when the primary deliverable is a Word document, HTML report, standalone Python script, database pipeline, or Google Sheets API integration, even if tabular data is involved.",
      ja: "スプレッドシートのファイルが主な入力または出力になるときに使う。既存の .xlsx・.xlsm・.xltx・.csv・.tsv ファイルを開く・読む・編集する・直す（列の追加、数式の計算、書式設定、グラフの作成、乱れたデータの整理など）、ゼロから・他のデータ元から新しいスプレッドシートを作る、表形式のファイル形式を変換する、といった作業を含む。ユーザーがスプレッドシートのファイルを名前やパスで（「ダウンロードにある xlsx」のように何気なくでも）指して、何かをしたり何かを作ったりしたいときは特にトリガーする。乱れた表形式のデータファイル（不正な行、ずれたヘッダー、不要なデータ）を整ったスプレッドシートに整理・再構成するときもトリガーする。成果物はスプレッドシートのファイルでなければならない。主な成果物が Word 文書、HTML レポート、単体の Python スクリプト、データベースのパイプライン、Google Sheets API の連携のときは、表形式のデータが関わっていてもトリガーしない。",
    },
  ],
  "code-review:code-review": [
    {
      en: "Code review a pull request",
      ja: "プルリクエストをコードレビューする。",
    },
  ],
  "commit-commands:clean_gone": [
    {
      en: "Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.",
      ja: "[gone] と表示されている git ブランチ（リモートでは削除されたがローカルに残っているもの）を、関連する worktree も含めてすべて削除する。",
    },
  ],
  "commit-commands:commit": [
    {
      en: "Create a git commit",
      ja: "git コミットを作る。",
    },
  ],
  "commit-commands:commit-push-pr": [
    {
      en: "Commit, push, and open a PR",
      ja: "コミットし、push して、PR を開く。",
    },
  ],
  "cowork-plugin-management:cowork-plugin-customizer": [
    {
      en: "Customize a Claude Code plugin for a specific organization's tools and workflows. Use when: customize plugin, set up plugin, configure plugin, tailor plugin, adjust plugin settings, customize plugin connectors, customize plugin skill, tweak plugin, modify plugin configuration.",
      ja: "特定の組織のツールとワークフローに合わせて Claude Code のプラグインをカスタマイズする。プラグインのカスタマイズ、セットアップ、設定、調整、プラグインの設定の変更、プラグインのコネクターやスキルのカスタマイズ、プラグインの微調整、プラグインの構成の変更を頼まれたときに使う。",
    },
  ],
  "cowork-plugin-management:create-cowork-plugin": [
    {
      en: "Guide users through creating a new plugin from scratch in a cowork session. Use when users want to create a plugin, build a plugin, make a new plugin, develop a plugin, scaffold a plugin, start a plugin from scratch, or design a plugin. This skill requires Cowork mode with access to the outputs directory for delivering the final .plugin file.",
      ja: "cowork セッションで、プラグインをゼロから作る手順を案内する。プラグインを作りたい、作成したい、新しく作りたい、開発したい、雛形を作りたい、ゼロから始めたい、設計したいときに使う。このスキルには、完成した .plugin ファイルを渡すための outputs ディレクトリにアクセスできる Cowork モードが必要である。",
    },
  ],
}
