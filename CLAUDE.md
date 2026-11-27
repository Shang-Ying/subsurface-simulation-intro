# CLAUDE.md — 陳尚潁個人／研究室網站

這個 repo 同時放兩樣東西：

1. **個人與研究室網站的嵌入頁面**：以 HTML 寫成，由 GitHub Pages 託管，再嵌入 Google Sites 主站 https://sites.google.com/view/synatsu/home。
2. **115-1 資源工程概論的網頁版簡報**：根目錄的 `index.html`。

請用繁體中文和使用者溝通。

## 頁面對照

| 資料夾 | 內容 | 嵌入 Google Sites 的哪一頁 |
|---|---|---|
| `home/` | 首頁：姓名、職稱、研究領域磚塊、聯絡方式 | HOME |
| `news/` | 最新消息時間軸（**由資料檔產生，見下方**） | NEWS |
| `members/` | 研究室成員（學生卡片） | MEMBERS |
| `cv/` | 履歷 | CV |
| `index.html` | 115-1 資源工程概論簡報（網頁版） | 不嵌入（課程用） |
| `explore/`、`fonts/` | 先前的設計方案和字型挑選草稿 | 不嵌入 |

RESEARCH、LIFE、OFFICE HOURS 三頁是 Google Sites 原生頁面，不在這個 repo 裡。

公開網址：`https://shang-ying.github.io/subsurface-simulation-intro/<資料夾>/`

## 發布規則（重要）

- **`main` 和 `gh-pages` 兩個分支必須保持一致。** 推送時兩個都要推：
  `git push origin main && git push origin main:gh-pages`
- 推上去等於網站立刻上線。**推送前先給使用者看改了什麼，等他同意再推。** 在本機改檔和 commit 不需要先問。
- commit 訊息用「頁面: 改了什麼」的格式，例如 `News: …`、`Home: …`、`Members: …`。

## 最新消息（News）的維護方式

**不要手改 `news/index.html` 的時間軸。** 請改 `news/news.yaml`，再執行：

```bash
python3 tools/build_news.py          # 重新產生 news/index.html
python3 tools/build_news.py --check  # 檢查 index.html 是否和 yaml 一致
```

- 新的消息放在 yaml 最上面。各欄位的說明寫在 `tools/build_news.py` 開頭。
- 分類 `cat` 只能是下列其中一個：`paper` 論文、`talk` 演講、`conf` 研討會、`teach` 教學、`service` 服務、`award` 獲獎、`visit` 交流、`project` 計畫。
- 文字中的 `|` 代表中文斷行點，產生時會轉成 `<wbr>`。請標在詞和詞之間，例如 `水文地質學|課程|參訪`，手機上標題才不會從詞中間斷開。
- 地點用 `<span class="at">@ 地點</span>` 標示，會顯示成灰字。
- 論文類加上 `link:`（DOI 網址），會自動產生「Link ↗」按鈕。
- 照片的處理：
  ```bash
  python3 tools/prep_photo.py <原始照片> 2026-12_主題_1 --caption "說明"
  ```
  - 這個指令會轉正方向、去除 EXIF 和 GPS 等資料、縮成 1800 px 大圖加 900 px 小圖，並印出可以直接貼進 yaml 的內容。
  - 檔名格式：`YYYY-MM_主題_序號`。
- 頁面上方的 CSS、篩選按鈕、JS 都直接寫在 `news/index.html` 裡，要改就直接改那個檔；產生腳本只會覆寫 `<main>` 時間軸和年份跳轉列。

## 預覽

```bash
python3 -m http.server 8000
# 打開 http://localhost:8000/news/ 、/home/ 、/members/ 、/cv/
```

頁面是嵌在 Google Sites 的 iframe 裡顯示的，頁面會自己偵測是否在 iframe 中（加上 `framed` class）。手機和平板的版面也要檢查。

## 設計偏好（使用者明確說過的）

- 整體走**正式、精緻、有細節**的風格，不要圓潤可愛。之前把 NEWS、CV、MEMBERS 改成圓角可愛風格，被使用者認為太可愛，已經改回正式風格。
- 喜歡低調的 hover 細節，例如首頁研究領域磚塊滑過時微微轉灰。
- MEMBERS 頁：
  - 「博士生」「專題研究生」這兩組即使目前沒有人，也保留分組標題、內容留白。
  - 不要寫「尚無」「招募中」之類的佔位文字。
  - 不顯示人數。
- 每一頁的進場動畫要依視覺順序（由上到下、由左到右）逐一淡入。目前各頁已經統一，新增元素時要沿用同一套。

## 網站上會用到的基本資料

- 陳尚潁 Shang-Ying Chen，國立成功大學資源工程學系助理教授（2026/8 起）
- 研究室：地下資源與智慧計算研究室 Subsurface Resources and Intelligent Computing Laboratory
- 研究領域：地下資源工程數值模擬，包括地下水、地熱、碳封存、地下儲氣／儲氫、隧道、放射性廢棄物處置，涵蓋流體、熱傳與力學。專長是不確定性量化、資料同化、物理資訊神經網路（PINN）。
- 聯絡：shangying@gs.ncku.edu.tw｜資源新館四樓 43408｜06-2757575 ext. 62835
- Google Scholar `Kh6UKMAAAAAJ`｜ORCID 0000-0003-3036-0798｜ResearchGate `Shang-Ying-Chen`｜LinkedIn `shang-ying-chen-5b34351b9`
- 學歷與經歷：
  - 成大資源工程博士（2022/6）
  - 成大資源工程博士後（2022/8–2026/1）
  - Stanford Energy Science & Engineering 訪問博士後（2024/7–2025/7）
  - Stanford SUETRI-D 訪問研究員（2024/10–2025/4）
  - NSF/GEO 提案評審（2025）
  - 臺南大學綠色能源科技學系助理教授（2026/2–7）

## 待辦／先前的建議（使用者尚未決定）

2026-11 檢視 Google Sites 時提出過以下幾點，使用者還沒決定要做哪些：

- RESEARCH 頁抓不到文字內容，可能需要補上研究主題、代表著作和學術連結。
- 新增「加入我們／Prospective Students」招生區塊。
- 新增 Teaching 頁，整理各學期開課。
- OFFICE HOURS 頁補上地點；確認預約表單不用登入也能開啟。
- LIFE 頁的「RECENT SNAPS」目前是空的。
