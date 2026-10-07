# 圖文影音遷移狀態與清理流程

LULUKA 已改為三品牌集合入口；舊作品集與合作名單不再作為首頁主體。
`website/` 舊素材已從公開部署白名單與工作目錄移除。33 個媒體原檔在第二次遠端核對及本機未改動檢查成功後刪除，網站公開素材網址已改用 Supabase。

## 備份

完整媒體與 HTML 快照、原始 HEAD 首頁，以及 Git bundle 保存在 checkout 外的
`/workspace/luluka-migration-backups/20261007T033034Z/`。
這是目前機器的復原備份，不是長期異地備份；環境刪除前應保存至受控儲存。
備份含 38 個現有內容檔（約 60 MB）及額外的原始首頁。
本次盤點包含 PNG、JPEG、GIF、SVG 和 HTML，沒有獨立影音檔。

`content.tar.gz` 與 `inventory.json` 已逐檔核對 SHA-256。Git bundle 已確認
包含完整本機歷史。備份、inventory 和上傳 receipt 都不得加入公開 repository。

## 已在 Supabase 建立

- 品牌私密 records、RLS、MFA AAL2 要求與審核函式。
- `luluka-content-archive`：原始素材及 HTML 快照，private，僅服務端可讀寫。
- `luluka-public-media`：只放已核准公開的分享卡與 favicon；這些資源本來就是
  公開網站的一部分。原始作品、照片與完整 HTML 快照不會放在 public bucket。
- `luluka_content_archive`：原始路徑、雜湊、大小與抽出的文案，RLS 開啟，
  匿名與普通 authenticated 使用者沒有資料表權限。

39 份內容（含原始首頁）已上傳，重新下載核對 SHA-256、驗證原始封存無法匿名下載，並核對資料庫紀錄。5 份原已核准公開的分享卡與 favicon 另放公開 bucket。完整 receipt 保存於上述備份目錄。
若金鑰曾貼到聊天或其他非秘密管道，先撤銷，再以新金鑰填入環境設定。

## 執行

```sh
python3 scripts/migrate_media.py \
  --backup-dir /workspace/luluka-migration-backups/20261007T033034Z \
  --project-url https://umstsvobrqgstsjdvpza.supabase.co
```

使用環境設定秘密欄位 `SUPABASE_SERVICE_ROLE_KEY`。預設支援新式 `sb_secret_`
伺服器金鑰；若填入的是 legacy service_role JWT，加入 `--key-mode legacy-jwt`。
新版金鑰使用 apikey header，不當作使用者 JWT。金鑰不會寫入檔案、HTML 或日誌。

上傳採內容雜湊路徑，不覆寫不一致的物件。中文或含空白的原始檔名在 Storage 使用安全 ASCII 名稱，完整原始路徑保留在私密資料庫。超過 6 MiB 的檔案使用 TUS 分塊續傳，每份檔案都重新下載核對 SHA-256，
測試原始封存無法匿名下載，再核對資料庫紀錄。只在全部成功後才產生完整 receipt。
重試可以重用已核對的物件；部分成功不代表可以清除本機原檔。

```sh
python3 scripts/finalize_media_migration.py \
  --backup-dir /workspace/luluka-migration-backups/20261007T033034Z
python3 scripts/build_public.py
python3 scripts/check_public.py
```

清理工具先重新驗證備份與遠端原檔、確認本機媒體未改動，再將分享卡及 favicon
改為 Supabase 公開網址、移除部署清單中的媒體及本機媒體。公開 HTML、CSS、JS
仍留在 GitHub 作為網站程式；私密原始 HTML 與文案副本在 Supabase 保存。
本機五頁桌面與手機版驗證通過，變更已推送 main，正式網址五頁均回傳 HTTP 200 且內容正確。GitHub Pages 仍為 legacy source；切換為 GitHub Actions 的自動請求遭 HTTP 403 拒絕。請在 Settings → Pages 將 Source 改為 GitHub Actions，並重新執行 Deploy reviewed public website，讓部署只包含 .site。

## GitHub 歷史

刪除工作目錄並提交後，媒體仍可能存在於 Git 歷史、分支、fork 與外部快取。
清理歷史需另做歷史重寫、處理所有相關 refs 並 force push，會影響既有 clone。
Git bundle 已保存供復原。經使用者明確授權，main 已以相同的乾淨網站檔案重建 root commit，並使用 force-with-lease 推送。重新從 GitHub clone 驗證，舊媒體不再位於 main 可達歷史；新 clone 沒有媒體檔。既有 clone 請重新 clone，勿把舊分支重新合併或推回 main。GitHub 尚未回收的舊 SHA、fork 與外部快取不在這次可達歷史清理的保證範圍。
GitHub 上曾公開的資料無法保證從他人已保存的副本中收回。

實際殘留檢查：目前網站的舊媒體路徑回傳 404，但舊提交 SHA 的 raw 媒體請求仍回傳 200。這表示 main 可達歷史清理沒有清除 GitHub 端的所有可讀舊物件。若要求這些舊物件不可再讀，需透過 GitHub 的支援/資料移除流程處理，並再測試原 URL；不得將本次歷史重寫描述為完全回收已公開素材。

## 首頁黑金背景

依品牌視覺需求，首頁採用原有黑金光點背景。備份中的 `website/bg.jpg` 保持私有；另以無損 PNG 格式建立公開的首頁展示副本，儲存於 Supabase `luluka-public-media`，已以匿名下載比對 SHA-256。背景檔案不進入 Git 或部署素材清單。目前公開素材為原先五份社群圖與圖示，加上一份經指定公開的背景。

## Noto Sans 字型

一般文字使用 Noto Sans TC，標題保留原字體。Noto Sans CJK TC Regular 取自環境中的 `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`（TC face 3），以 fontTools 產生涵蓋目前公開 HTML 字元與 ASCII 的 WOFF 子集。字型與完整 SIL OFL 1.1 授權存於 Supabase `luluka-public-fonts` 公開 bucket；匿名下載已驗證雜湊與 CORS，字型二進位不進入 Git。新增文字若使用子集外字元，需要重新產生與上傳子集。

授權：https://umstsvobrqgstsjdvpza.supabase.co/storage/v1/object/public/luluka-public-fonts/f776c08b93f08cacbe001699b40099a3e9de6f9378fff7f716b7216f8365d643/OFL.txt
