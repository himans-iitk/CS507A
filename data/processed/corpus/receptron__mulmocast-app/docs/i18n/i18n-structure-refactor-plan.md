# i18n 翻訳キー構造リファクタリング計画書 - Final
**作成日**: 2025-07-24  
**作成者**: Claude Code  
**バージョン**: Final - 実用的な単一ファイル管理（使い回し重視）

## 📋 概要
- **単一ファイル管理** - `en.ts`と`ja.ts`で全翻訳を管理
- **Ctrl+F検索重視** - 人力での検索・使い回しを考慮
- **4つのカテゴリ分類** - 共通UI、一般的文言、スタイル、コンポーネント固有
- **実用的な落とし所** - 完璧より管理しやすさを優先

## 🔍 設計原則

1. **使い回し重視** - `image`, `text`, `title`等の汎用語は共通化
2. **検索性優先** - 検索で簡単に見つけられる構造
3. **分類による整理** - 4つのカテゴリで論理的に分類
4. **管理の簡素化** - 複雑な階層は避け、実用性を重視

## 🎯 構造比較（Before / After）

### Before: 現在の構造
```
├── generating
├── form/
│   ├── cancel
│   ├── changeBeatTypeFirst
│   └── template_selector/
├── panels/
│   ├── aiAssistantChat
│   └── openOutputProduct
├── beat/
│   ├── badge/ (全種別フラット)
│   └── form/ (全種別フラット)
└── project/
    ├── generate/
    └── scriptEditor/
```

### After: 新構造（使い回し重視の単一ファイル管理）
```
├── message/ (既存・変更なし)
├── menu/ (既存・変更なし)
├── settings/ (既存・変更なし)
├── dashboard/ (既存・変更なし)
├── ui/           # 共通UI文言（使い回し重視）
│   ├── common/   # 汎用的な名詞
│   ├── actions/  # 汎用的なアクション（役割別キー分離）
│   ├── status/   # 汎用的なステータス
│   ├── elements/ # 汎用的なUI要素
│   ├── tabs/     # タブ関連
│   └── validation/ # バリデーション
├── beat/         # Beat関連（スキーマベース + UI.common参照）
│   ├── textSlide/
│   ├── markdown/
│   ├── chart/
│   ├── mermaid/
│   ├── html_tailwind/
│   ├── imagePrompt/
│   ├── htmlPrompt/
│   ├── web/
│   ├── image/
│   ├── movie/
│   ├── audio/
│   ├── beat/
│   ├── actions/
│   ├── template/
│   ├── preview/
│   └── mediaFile/
├── parameters/   # パラメータ設定（スキーマベース + UI.common参照）
│   ├── imageParams/
│   ├── audioParams/
│   ├── movieParams/
│   ├── htmlPrompt/
│   ├── textSlideParams/
│   ├── speechOptions/
│   ├── captionParams/
│   └── canvasSizeParams/
├── chat/         # チャット機能
├── generate/     # 生成機能
│   ├── types/
│   ├── status/
│   └── progress/
└── product/      # 成果物表示
    ├── tabs/
    ├── movie/
    ├── pdf/
    ├── html/
    ├── podcast/
    └── slide/
```

## 🎯 最終構造

```typescript
// common.ts - 技術用語のみ（変更なし）
export const common = {
  beatTypes: {
    markdown: "Markdown",
    textSlide: "Text Slide",
    imagePrompt: "Image Prompt",
    // ...
  },
  formats: {
    json: "JSON",
    pdf: "PDF",
    // ...
  },
};

// en.ts / ja.ts の構造
const lang = {
  // 既存のトップレベル（変更なし）
  message: { ... },
  menu: { ... },
  settings: { ... },
  dashboard: { ... },
  
  // 1. 共通UI文言（汎用語・使い回し重視）
  ui: {
    // 汎用的な名詞
    common: {
      title: "Title",
      text: "Text",
      image: "Image",
      audio: "Audio",
      video: "Video",
      movie: "Movie",
      file: "File",
      url: "URL",
      prompt: "Prompt",
      contents: "Contents",
      content: "Content",
      data: "Data",
      code: "Code",
      name: "Name",
      description: "Description",
      size: "Size",
      width: "Width",
      height: "Height",
      duration: "Duration",
      quality: "Quality",
      style: "Style",
      type: "Type",
      format: "Format",
      language: "Language",
      provider: "Provider",
      model: "Model",
      speed: "Speed",
      volume: "Volume",
      padding: "Padding",
      beat: "Beat",
      slide: "Slide",
      chart: "Chart",
      speaker: "Speaker",
      chat: "Chat",
      panel: "Panel",
      parameters: "Parameters",
    },
    
    // 汎用的なアクション（役割別キー分離）
    actions: {
      // プレースホルダーなし版とプレースホルダーあり版をペアで配置
      add: "Add",
      addThing: "Add {thing}",
      browse: "Browse",
      browseThing: "Browse {thing}",
      cancel: "Cancel",
      change: "Change",
      changeThing: "Change {thing}",
      clear: "Clear",
      clearThing: "Clear {thing}",
      close: "Close",
      closeThing: "Close {thing}",
      copy: "Copy",
      copyThing: "Copy {thing}",
      create: "Create",
      createThing: "Create {thing}",
      delete: "Delete",
      deleteThing: "Delete {thing}",
      download: "Download",
      downloadThing: "Download {thing}",
      edit: "Edit",
      editThing: "Edit {thing}",
      export: "Export",
      exportThing: "Export {thing}",
      fetch: "Fetch",
      fetchThing: "Fetch {thing}",
      filter: "Filter",
      filterThing: "Filter {thing}",
      generate: "Generate",
      generateThing: "Generate {thing}",
      import: "Import",
      importThing: "Import {thing}",
      insert: "Insert",
      insertThing: "Insert {thing}",
      open: "Open",
      openThing: "Open {thing}",
      paste: "Paste",
      pasteThing: "Paste {thing}",
      pause: "Pause",
      pauseThing: "Pause {thing}",
      play: "Play",
      playThing: "Play {thing}",
      preview: "Preview",
      previewThing: "Preview {thing}",
      refresh: "Refresh",
      refreshThing: "Refresh {thing}",
      reset: "Reset",
      resetThing: "Reset {thing}",
      save: "Save",
      search: "Search",
      searchThing: "Search {thing}",
      sort: "Sort",
      sortThing: "Sort {thing}",
      stop: "Stop",
      stopThing: "Stop {thing}",
      upload: "Upload",
      uploadThing: "Upload {thing}",
      view: "View",
      viewThing: "View {thing}",
    },
    
    // 汎用的なステータス
    status: {
      loading: "Loading...",
      generating: "Generating...",
      processing: "Processing...",
      saving: "Saving...",
      uploading: "Uploading...",
      downloading: "Downloading...",
      complete: "Complete",
      success: "Success",
      error: "Error",
      warning: "Warning",
      failed: "Failed",
      cancelled: "Cancelled",
      ready: "Ready",
      pending: "Pending",
      running: "Running",
    },
    
    // 汎用的なUI要素
    elements: {
      button: "Button",
      input: "Input",
      textarea: "Textarea",
      select: "Select",
      checkbox: "Checkbox",
      radio: "Radio",
      slider: "Slider",
      tab: "Tab",
      panel: "Panel",
      dialog: "Dialog",
      modal: "Modal",
      dropdown: "Dropdown",
      menu: "Menu",
      tooltip: "Tooltip",
      placeholder: "Placeholder",
      label: "Label",
      field: "Field",
      form: "Form",
      table: "Table",
      list: "List",
      card: "Card",
      badge: "Badge",
    },
    
    // タブ関連
    tabs: {
      text: "Text",
      yaml: "YAML",
      json: "JSON",
      media: "Media",
      style: "Style",
      ref: "Ref",
    },
    
    // バリデーション
    validation: {
      required: "This field is required",
      invalid: "Invalid format",
      tooShort: "Too short",
      tooLong: "Too long",
      mustBeNumber: "Must be a number",
      mustBeUrl: "Must be a valid URL",
    },
  },
  
  // 2. Beat関連（スキーマベース + UI.common参照）
  beat: {
    // 各Beat種別の固有フィールド（スキーマベース + プレースホルダー）
    textSlide: {
      titleField: ui.common.title,
      subtitleField: "Subtitle", 
      contentsField: ui.common.contents,
      placeholder: "Slide Contents\\nMarkdown bullets\\n- one\\n- two",
    },
    markdown: {
      contentsField: ui.common.contents,
      placeholder: "Markdown Contents\\n# Title\\nWrite your content here.\\n- Item 1\\n- Item 2",
    },
    chart: {
      titleField: ui.common.title,
      chartDataField: "Chart Data",
      placeholder: "Enter chart data in JSON format\\n{\\\"type\\\": \\\"bar\\\", \\\"data\\\": {...}}",
    },
    mermaid: {
      titleField: ui.common.title,
      codeField: ui.common.code,
      placeholder: "Enter Mermaid diagram code.",
    },
    html_tailwind: {
      htmlField: "HTML",
      placeholder: "Enter HTML with Tailwind CSS classes.",
    },
    imagePrompt: {
      promptField: ui.common.prompt,
      placeholder: "Enter prompt to generate image.",
    },
    htmlPrompt: {
      promptField: ui.common.prompt,
      systemPromptField: "System Prompt",
      dataField: ui.common.data,
      placeholder: "Enter HTML prompt to generate custom slide content.",
    },
    web: {
      urlField: ui.common.url,
      placeholder: "Enter web page URL",
    },
    image: {
      urlField: ui.common.url,
      fileField: ui.common.file,
      placeholder: "Enter image URL or upload file",
    },
    movie: {
      urlField: ui.common.url,
      fileField: ui.common.file,
      placeholder: "Enter movie URL or upload file",
    },
    audio: {
      urlField: ui.common.url,
      fileField: ui.common.file,
      placeholder: "Enter audio URL or upload file",
    },
    beat: {
      idField: "Beat ID",
      referenceField: "Beat Reference",
      placeholder: "Enter beat ID to reference (e.g., beat_1)",
    },
    
    // Beat固有のアクション（プレースホルダー使用例）
    actions: {
      // 汎用アクションと組み合わせて使用：
      // t('ui.actions.add', { thing: t('ui.common.beat') }) → "Add Beat" / "ビートを追加"
      // t('ui.actions.generate', { thing: t('ui.common.image') }) → "Generate Image" / "画像を生成"
      
      // Beat固有でのみ使用される特殊なアクション
      changeBeatTypeFirst: "Change beat type first",
    },
    
    // Beat固有のUI要素
    template: {
      // 汎用アクションをそのまま使用（プレースホルダーなし）
      insert: "Insert",
      change: "Change",
    },
    preview: {
      // プレースホルダー使用例：
      // t('ui.actions.preview', { thing: t('ui.common.video') }) → "Preview Video" / "動画をプレビュー"
      videoPreview: "Video Preview",
      imagePreview: "Image Preview", 
      audioPreview: "Audio Preview",
    },
    mediaFile: {
      dropArea: "Drop file here",
      browseFiles: "Browse Files",
    },
  },
  
  // 3. パラメータ設定（スキーマベース + UI.common参照）
  parameters: {
    // 画像生成パラメータ
    imageParams: {
      title: "Image Parameters",
      provider: "Provider",
      model: "Model",
      style: "Style",
      size: "Size",
      quality: "Quality",
    },
    
    // 音声パラメータ
    audioParams: {
      title: "Audio Parameters",
      provider: "Provider",
      voice: "Voice",
      padding: "Padding",
      movieVolume: "Movie Volume",
    },
    
    // 動画パラメータ
    movieParams: {
      title: "Movie Parameters",
      provider: "Provider",
      model: "Model",
      fillOption: "Fill Option",
      speed: "Speed",
      transitionType: "Transition Type",
      transitionDuration: "Transition Duration (seconds)",
      transitionFade: "Fade",
      transitionSlideLeft: "Slide Out Left",
    },
    
    // HTMLプロンプトパラメータ
    htmlPrompt: {
      title: "HTML Prompt Parameters",
      systemPrompt: "System Prompt",
      prompt: "Prompt",
      data: "Data",
      images: "Images",
    },
    
    // テキストスライドパラメータ
    textSlideParams: {
      title: "Text Slide Parameters",
      cssStyles: "CSS Styles",
      padding: "Padding",
      fontSize: "Font Size",
      backgroundColor: "Background Color",
    },
    
    // 音声合成オプション
    speechOptions: {
      title: "Speech Parameters",
      initialize: "Initialize Speech Parameters",
      // プレースホルダー使用例：
      // t('ui.actions.add', { thing: t('ui.common.speaker') }) → "Add Speaker" / "スピーカーを追加"
      noSpeakers: "No speakers defined",
      speechSpeed: "Speech Speed",
      instruction: "Speech Instruction",
    },
    
    // キャプションパラメータ
    captionParams: {
      title: "Caption Parameters",
      styles: "Caption Styles",
      fontSize: "Font Size",
      position: "Position",
    },
    
    // キャンバスサイズパラメータ
    canvasSizeParams: {
      title: "Canvas Size Parameters",
      width: ui.common.width,
      height: ui.common.height,
      aspectRatio: "Aspect Ratio",
    },
  },
  
  // 4. チャット機能
  chat: {
    title: "AI Assistant Chat",
    openButton: "Open AI Assistant Chat panel",
    guide: "AI-Powered MulmoScript Generation Guide",
    beginnerDesc: "Let's Create Scripts Through Conversation with AI Assistants",
    advancedDesc: "Use ChatGPT or other AI tools to generate your Script content with these proven prompts",
    placeholder: "Type your message...",
    sendButton: "Send",
    // プレースホルダー使用例：
    // t('ui.actions.clear', { thing: t('ui.common.chat') }) → "Clear Chat" / "チャットをクリア"
    thinking: "AI is thinking...",
    errorMessage: "Failed to send message",
  },
  
  // 5. 生成機能
  generate: {
    openButton: "Open Output & Product panel",
    panelTitle: "Output Settings & Generation / Production",
    settingsTitle: "Output Settings & Generation",
    generateButton: "Generate Contents",
    // プレースホルダー使用例：
    // t('ui.actions.cancel', { thing: "Generation" }) → "Cancel Generation" / "生成をキャンセル"
    
    // 生成タイプ
    types: {
      movie: "Movie",
      audio: "Podcast",
      pdfSlide: "PDF (Presenter)",
      pdfHandout: "PDF (Handout)",
    },
    
    // ステータス
    status: {
      success: "Contents generated successfully",
      error: "Failed to generate contents",
    },
    
    // 進捗状態
    progress: {
      preparing: "Preparing...",
      generatingImages: "Generating images...",
      generatingAudio: "Generating audio...",
      creatingMovie: "Creating movie...",
      complete: "Complete!",
      failed: "Generation failed",
    },
  },
  
  // 6. 成果物表示
  product: {
    // タブ
    tabs: {
      movie: "Movie",
      pdf: "PDF",
      html: "HTML",
      podcast: "Podcast",
      slide: "Slide",
    },
    
    // 動画
    movie: {
      title: "Movie Preview",
      description: "Video content playback and preview",
      playButton: "Play",
      pauseButton: "Pause",
      // プレースホルダー使用例：
      // t('ui.actions.download', { thing: "MP4" }) → "Download MP4" / "MP4をダウンロード"
      downloadButton: "Download MP4",
      details: "Duration: {duration} - Resolution: {width}x{height} - Size: {size}",
    },
    
    // PDF
    pdf: {
      title: "PDF Preview",
      description: "PDF document display and download",
      viewButton: "View PDF",
      downloadButton: "Download PDF",
      details: "{pages} pages - {format} format - Size: {size}",
    },
    
    // HTML
    html: {
      title: "HTML Preview",
      description: "Interactive web format display",
      viewButton: "View HTML",
      downloadButton: "Download HTML",
      details: "Interactive content - Responsive design",
    },
    
    // ポッドキャスト
    podcast: {
      title: "Podcast Preview",
      description: "Audio content playback and preview",
      playButton: "Play",
      pauseButton: "Pause",
      downloadButton: "Download MP3",
      details: "Duration: {duration} - Size: {size}",
    },
    
    // スライド
    slide: {
      title: "Slide Preview",
      description: "Slide format display and navigation",
      startButton: "Start Slideshow",
      // プレースホルダー使用例：
      // t('ui.actions.export', { thing: t('ui.common.image') + "s" }) → "Export Images" / "画像をエクスポート"
      exportButton: "Export Images",
      details: "{count} slides - {width}x{height} resolution",
      previousButton: "Previous",
      nextButton: "Next",
    },
  },
  
  languages,
};
```

## 💡 プレースホルダー方式の使用例

### 実際のコードでの使用方法

```javascript
// Vue.jsコンポーネント内での使用例

// ❌ 悪い例（文字列連結）
const buttonText = t('ui.actions.add') + ' ' + t('ui.common.beat');
// 結果: 英語 "Add Beat" / 日本語 "追加 ビート" （不自然）

// ✅ 良い例1（汎用動詞：プレースホルダーなし）
const addButtonText = t('ui.actions.add');
// 結果: 英語 "Add" / 日本語 "追加"
// 用途: 汎用的な「追加」ボタン

// ✅ 良い例2（対象物付き動詞：プレースホルダーあり）
const addBeatButtonText = t('ui.actions.addThing', { thing: t('ui.common.beat') });
// 結果: 英語 "Add Beat" / 日本語 "ビートを追加" （自然）
// 用途: 特定の対象を追加するボタン

// その他の使用例
const generateImageButton = t('ui.actions.generateThing', { thing: t('ui.common.image') });
const deleteSlideButton = t('ui.actions.deleteThing', { thing: t('ui.common.slide') });
const openPanelButton = t('ui.actions.openThing', { thing: t('ui.common.panel') });

// シンプルな動詞のみが必要な場合
const saveButton = t('ui.actions.save');
const cancelButton = t('ui.actions.cancel');
```

### 日本語翻訳ファイル（ja.ts）での対応例

```typescript
// ja.ts
const ja = {
  ui: {
    common: {
      beat: "ビート",
      image: "画像", 
      slide: "スライド",
      panel: "パネル",
    },
    actions: {
      // プレースホルダーなし版とプレースホルダーあり版をペアで配置
      add: "追加",
      addThing: "{thing}を追加",
      delete: "削除",
      deleteThing: "{thing}を削除",
      generate: "生成",
      generateThing: "{thing}を生成",
      open: "開く",
      openThing: "{thing}を開く",
      // ...他のペアも同様
    },
  },
};
```

### テンプレート内での使用

```vue
<template>
  <!-- プレースホルダー方式 -->
  <button>{{ $t('ui.actions.add', { thing: $t('ui.common.beat') }) }}</button>
  
  <!-- 動的な値との組み合わせ -->
  <button>{{ $t('ui.actions.download', { thing: fileFormat }) }}</button>
  
  <!-- 複数のプレースホルダー -->
  <span>{{ $t('ui.status.with_count', { count: beatCount, thing: $t('ui.common.beat') }) }}</span>
</template>
```

## 📊 キー変更マッピング

### UI共通化による変更
| 旧キー | 新キー | 理由 |
|--------|--------|------|
| `"Title"` (各所) | `ui.common.title` | 汎用語の共通化 |
| `"Image"` (各所) | `ui.common.image` | 汎用語の共通化 |
| `"Save"` (各所) | `ui.actions.save` | アクションの共通化 |
| `"Loading..."` (各所) | `ui.status.loading` | ステータスの共通化 |

### 具体的な変更例
| 旧キー | 新キー |
|--------|--------|
| `generating` | `ui.status.generating` |
| `form.cancel` | `ui.actions.cancel` |
| `form.template_selector.insert` | `ui.actions.insert` |
| `beat.badge.htmlPrompt` | `common.beatTypes.htmlPrompt` |
| `beat.form.textSlide.title` | `beat.textSlide.titleField` |
| `beat.form.htmlPrompt.contents` | `beat.htmlPrompt.promptField` |
| `project.scriptEditor.movieParams.provider` | `parameters.movieParams.provider` |

## 🔄 実装手順

### Phase 1: UI共通語彙の構築（45分）
1. 現在の翻訳ファイルから汎用的な語彙を抽出
2. `ui.common`, `ui.actions`, `ui.status`を構築
3. 重複する語彙を統合

### Phase 2: Beat構造の再編（1時間）
1. スキーマベースのBeat構造を作成
2. UI共通語彙を参照するように変更
3. Beat固有の文言のみを残す

### Phase 3: Parameters構造の整理（45分）
1. パラメータ構造をスキーマベースに変更
2. UI共通語彙を活用

### Phase 4: その他機能の整理（30分）
1. chat, generate, product構造を整理
2. UI共通語彙を最大限活用

### Phase 5: コンポーネント更新（2時間）
1. 翻訳キーを新構造に変更
2. UI共通語彙の参照に変更
3. 段階的テスト

### Phase 6: 最終検証（30分）
1. 全機能のテスト
2. 翻訳の一貫性確認
3. ドキュメント更新

## 📈 期待効果

1. **使い回し促進** - 汎用語の共通化で重複削減
2. **検索性向上** - Ctrl+Fで簡単に関連する翻訳を発見
3. **管理の簡素化** - 4つのカテゴリで整理された構造
4. **一貫性確保** - 同じ概念には同じ翻訳を使用
5. **保守性向上** - 変更時の影響範囲が明確
6. **新規追加の効率化** - 既存の語彙を組み合わせて新しい翻訳を構築

**総実装時間**: 約5.5時間

## ⚠️ 注意点

1. **参照の複雑化** - `ui.common.title`等の参照が増える
2. **文脈依存** - 汎用語が文脈に適さない場合がある
3. **初期コスト** - 既存コンポーネントの大幅変更が必要

しかし、長期的な保守性とCtrl+F検索による効率性を考慮すると、この構造が最も実用的です。