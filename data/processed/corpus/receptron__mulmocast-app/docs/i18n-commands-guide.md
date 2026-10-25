# MulmoCast App i18n コマンドガイド

MulmoCast アプリケーションの国際化（i18n）を効率的に進めるための5つのClaude Codeコマンドの使い分けガイド。

## 📋 コマンド一覧

| コマンド | 用途 | 実行頻度 | ファイル更新 |
|---------|------|----------|-------------|
| `/i18n-workflow` | プロジェクト全体管理 | 初回・大規模変更時 | 多数 |
| `/i18n-batch` | 複数コンポーネント一括処理 | 定期的 | 複数 |
| `/i18n-scan` | テキスト抽出・分析 | 新規コンポーネント作成時 | なし（分析のみ） |
| `/i18n-component-task` | 個別コンポーネント実装 | 日常的 | 3-4ファイル |
| `/i18n-refactor` | 既存構造の改善 | 問題発見時 | en.ts, ja.ts |

## 🚀 使い分けフローチャート

```
新規プロジェクト or 大規模変更？
├─ はい → `/i18n-workflow complete all`
└─ いいえ
   ├─ 複数コンポーネントを処理？
   │  ├─ はい → `/i18n-batch "pattern" both`
   │  └─ いいえ
   │     ├─ 新しいコンポーネント？
   │     │  ├─ はい → `/i18n-scan` → 人間判断 → `/i18n-component-task`
   │     │  └─ いいえ
   │     │     ├─ 既存構造に問題？
   │     │     │  ├─ はい → `/i18n-refactor all`
   │     │     │  └─ いいえ → `/i18n-component-task`
```

## 📖 詳細な使い分け

### 1. `/i18n-workflow` - プロジェクト全体管理
**🎯 使用タイミング:**
- **初回導入時** - プロジェクト全体のi18n化開始
- **大規模リファクタリング時** - 構造全体の見直し
- **定期メンテナンス時** - 全体の健全性チェック

**💡 実行例:**
```bash
# 初回プロジェクト全体のi18n化
/i18n-workflow complete all

# ページコンポーネントのみ計画的に処理
/i18n-workflow plan pages

# 現在の状況を把握したい
/i18n-workflow audit all
```

**📄 更新されるファイル:**
- 複数の.vueファイル
- `src/renderer/i18n/en.ts`
- `src/renderer/i18n/ja.ts`
- `src/renderer/i18n/common.ts`

---

### 2. `/i18n-batch` - 複数コンポーネント一括処理
**🎯 使用タイミング:**
- **同種コンポーネント群の処理** - UIコンポーネント、ページコンポーネントなど
- **特定ディレクトリの一括更新**
- **workflow後の部分的な追加作業**

**💡 実行例:**
```bash
# プロジェクトコンポーネント全体を処理
/i18n-batch "src/renderer/pages/project/components/*.vue" both

# UIコンポーネントのみスキャン
/i18n-batch "src/renderer/components/ui/**/*.vue" scan

# 新しく追加されたページを一括実装
/i18n-batch "src/renderer/pages/new-feature/**/*.vue" implement
```

**📄 更新されるファイル:**
- 指定されたパターンの.vueファイル群
- 言語ファイル（実装時）

---

### 3. `/i18n-scan` - テキスト抽出・分析
**🎯 使用タイミング:**
- **新規コンポーネント作成後**
- **既存コンポーネントの調査**
- **実装前の準備作業**

**💡 実行例:**
```bash
# 新しく作ったコンポーネントの分析
/i18n-scan src/renderer/pages/project/components/new_feature.vue

# 既存コンポーネントの国際化状況確認
/i18n-scan src/renderer/components/header.vue
```

**📄 更新されるファイル:**
- **なし**（分析レポートのみ出力）

**🔄 次のステップ:**
1. 出力された分析結果を確認
2. common.ts候補を人間が判断
3. `/i18n-component-task` で実装

---

### 4. `/i18n-component-task` - 個別コンポーネント実装
**🎯 使用タイミング:**
- **日常的な開発作業**
- **単一コンポーネントの国際化**
- **scan結果を受けての実装**

**💡 実行例:**
```bash
# 基本的な実装
/i18n-component-task src/renderer/pages/dashboard/dashboard.vue

# scan結果を使った実装
/i18n-component-task src/renderer/components/chat.vue "scan結果のテキスト"
```

**📄 更新されるファイル:**
- 指定された.vueファイル
- `src/renderer/i18n/en.ts`
- `src/renderer/i18n/ja.ts`
- `src/renderer/i18n/common.ts`（必要時）

---

### 5. `/i18n-refactor` - 既存構造の改善
**🎯 使用タイミング:**
- **翻訳キーの構造問題発見時**
- **未翻訳項目の大量発見時**
- **一貫性の問題解決**

**💡 実行例:**
```bash
# 全体的な構造とバランス翻訳の修正
/i18n-refactor all

# 構造のみ整理（翻訳追加なし）
/i18n-refactor structure

# 未翻訳項目のみ修正
/i18n-refactor translations
```

**📄 更新されるファイル:**
- `src/renderer/i18n/en.ts`
- `src/renderer/i18n/ja.ts`

## 🗓️ 実際の開発フロー例

### 初回プロジェクト導入時
```bash
# 1. 全体状況の把握と計画策定
/i18n-workflow complete all
```

### 新機能開発時
```bash
# 1. 新しいコンポーネントの分析
/i18n-scan src/renderer/pages/new-feature/new_component.vue

# 2. 人間による確認（common.ts候補など）

# 3. 実装
/i18n-component-task src/renderer/pages/new-feature/new_component.vue
```

### 複数コンポーネント追加時
```bash
# 1. 一括分析
/i18n-batch "src/renderer/pages/new-feature/**/*.vue" scan

# 2. 人間による確認

# 3. 一括実装
/i18n-batch "src/renderer/pages/new-feature/**/*.vue" implement
```

### 既存構造に問題発見時
```bash
# 1. 構造の修正
/i18n-refactor all

# 2. 個別コンポーネントの追加対応（必要時）
/i18n-component-task src/renderer/components/problem_component.vue
```

## ⚠️ 注意事項

### 実行前の準備
- [ ] Gitの作業ディレクトリをクリーンにする
- [ ] 現在のブランチをバックアップ
- [ ] 開発サーバーを起動して動作確認できる状態にする

### 推奨される実行順序
1. **workflow** → プロジェクト全体の計画と実行
2. **batch** → 追加の範囲処理
3. **scan + component-task** → 個別の細かい調整
4. **refactor** → 問題発見時の修正

### ファイル競合の回避
- 同時に複数の言語ファイルを編集するコマンドは順次実行
- 大規模な変更後は動作確認を行う
- 問題発生時は `git reset` でロールバック可能

## 🔧 トラブルシューティング

### よくある問題と解決方法

**Q: 翻訳キーが重複している**
```bash
/i18n-refactor structure  # 構造を整理
```

**Q: 一部のテキストが翻訳されていない**
```bash
/i18n-refactor translations  # 未翻訳項目を修正
```

**Q: 新しいコンポーネントが正しく処理されない**
```bash
/i18n-scan path/to/component.vue  # まず分析
# 結果を確認後
/i18n-component-task path/to/component.vue
```

**Q: プロジェクト全体の状況が分からない**
```bash
/i18n-workflow audit all  # 現状分析のみ実行
```

このガイドに従って、効率的かつ安全にMulmoCastアプリケーションの国際化を進めることができます。