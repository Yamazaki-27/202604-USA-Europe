# build_log.md — 202509-InnovationEXPOinTOKYO

---

## 2026-07-27 ビルド実行

### 実行日時
2026-07-27（初回ビルド。PUBLISH_SUMMARY.md 不在のため全工程実行）

### 対象フォルダー
`202509-InnovationEXPOinTOKYO/`

---

### 1. make-report

**ステータス：done**

- Nippou.txt（Shift-JIS）を UTF-8 変換して読解。前川・奥村（貴史）・佐倉（遼）3名分の日報を統合
- 写真：全31枚（自社ブース写真14枚・見学写真17枚）を Read ツールで目視確認
- EXIF・GPS・タイムスタンプを PowerShell（.NET System.Drawing）で取得し、時系列・撮影場所を特定
  - Windows環境のため sips 系コマンドは .NET (System.Drawing.Image) で代替
- 向き補正：EXIF orientation=6 の6枚を90度回転補正（タイムスタンプ保持）
- リサイズ：横幅1600px超の写真を1600pxへ縮小（22枚、タイムスタンプ保持）
- 写真の採否：31枚 → 本文採用22枚／OtherPictures 9枚（ほぼ同一カット・重複構図のみ間引き、unUsedなし）
- 展示会公式情報をWeb検索し、会期・会場・主催者・出展規模を確認（出典明記）
- README.md「出張報告書」テーブルに行を追加

---

### 2. review-report

**ステータス：done**

- バックアップ作成：`backup/Report_publish_*.md`
- 画像リンク確認：初稿で4枚（IMG_2020・IMG_2022・IMG_20250912_165404・IMG_20250912_164950）の参照漏れを検出し本文へ追加
- ほぼ同一カット1枚（IMG_2025.jpeg、IMG_2011と8秒差）をOtherPicturesへ整理
- 全31枚の画像リンクとOtherPictures章の内容を突合し、漏れ・リンク切れゼロを確認
- edit_log.md 作成

---

### 3. publish-report

**ステータス：Ready for Publish（98/100）**

- Markdown構文：問題なし
- 画像リンク：全リンク正常（ゼロ切れ）
- 「その他の写真」章：9枚すべて掲載確認
- CHANGELOG.md 作成
- release_notes.md 作成
- PUBLISH_SUMMARY.md 作成

---

### 4. archive-report

**ステータス：done**

| ファイル | 操作 |
|---|---|
| `KnowledgeBase/Companies/LEAD_TECH.md` | 新規作成 |
| `KnowledgeBase/Companies/ハクオウロボティクス.md` | 新規作成 |
| `KnowledgeBase/Companies/マキテック.md` | 新規作成 |
| `KnowledgeBase/Companies/京町産業.md` | 新規作成 |
| `KnowledgeBase/Companies/ナブテスコ.md` | 追記（INNOVATION EXPO 2025 東京の観察を追加） |
| `KnowledgeBase/Trends/2025.md` | INNOVATION EXPO 2025（東京）セクション追記 |
| `KnowledgeBase/Ideas/DriveUnit_InHouseProduction.md` | 薄型・5トンクラス電動車ニーズを追記 |
| `KnowledgeBase/Ideas/ABM_MultiPalletCapacity.md` | 新規作成 |
| `Reports/archive_log.md` | INNOVATION EXPO 2025（東京）エントリ追記 |

---

### 生成・更新ファイル一覧

```
202509-InnovationEXPOinTOKYO/
  Report.md               (新規作成)
  edit_log.md             (新規)
  CHANGELOG.md            (新規)
  release_notes.md        (新規)
  PUBLISH_SUMMARY.md      (新規)
  build_log.md            (新規)
  backup/                 (バックアップ)
  Images/
    OtherPictures/        (9枚)
    自社ブース写真/         (10枚)
    見学写真/               (12枚)

KnowledgeBase/Companies/LEAD_TECH.md              (新規)
KnowledgeBase/Companies/ハクオウロボティクス.md      (新規)
KnowledgeBase/Companies/マキテック.md               (新規)
KnowledgeBase/Companies/京町産業.md                 (新規)
KnowledgeBase/Companies/ナブテスコ.md               (追記)
KnowledgeBase/Trends/2025.md                       (INNOVATION EXPO 2025東京 追記)
KnowledgeBase/Ideas/DriveUnit_InHouseProduction.md (追記)
KnowledgeBase/Ideas/ABM_MultiPalletCapacity.md     (新規)
README.md                                          (出張報告書テーブル・知識ベーステーブル更新)
Reports/archive_log.md                             (INNOVATION EXPO 2025東京 追記)
```

---

### 特記事項

- **未解決の前提条件**：作業開始時点で `Future-Products-Lab` リポジトリに、本レポートとは無関係な既存のマージコンフリクト（README.md「講演会レポート」テーブル、202608-TanabeKenkyukai関連）が残っていた。本ビルドはそのコンフリクト箇所（README.md 101〜105行目付近）には一切触れず、「出張報告書」テーブルなど別セクションのみを編集した。git add・commit は実行していない。マージの解消はユーザー側で対応が必要。
- 燈株式会社のAI活用アプリケーションについて、後日説明の内容は本レポート作成時点で未確認（Report.md内に「要確認」と明記）

### 次に必要な作業

- なし（git add・commit はユーザーが手動で実施。上記マージコンフリクトの解消を先に推奨）
