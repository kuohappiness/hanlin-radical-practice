# 翰林版國語部首練習

這是一個可直接由 GitHub Pages 執行的繁體中文部首複習遊戲。學生先選擇年級與範圍，再於星星落地前選出正確部首。

## 目前版本

- 四上翰林版（期中）：可玩，六課共 89 題。
- 四上翰林版（期末）：題庫待匯入。
- 五上翰林版（期中）：可玩。
- 五上翰林版（期末）：題庫待匯入。

## 線上遊戲

https://kuohappiness.github.io/hanlin-radical-practice/

手機、平板與其他電腦都可直接開啟。

## 本機預覽

不需安裝套件。在本目錄執行：

```powershell
node server.js
```

再開啟 `http://127.0.0.1:5173/`。

## 維護

題庫來源、部首快取與建置腳本位於 `source-data/`，通用遊戲產生器位於 `tools/`。完整交接說明請閱讀 [CLAUDE_HANDOFF.md](CLAUDE_HANDOFF.md)。

