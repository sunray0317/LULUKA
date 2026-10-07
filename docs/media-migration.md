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

## 思源宋體標題

標題使用 Adobe Source Han Serif TC（思源宋體）Regular 與 Bold；小麥廚坊保留真正的 700 粗體。原檔與授權來自 Adobe 官方 `adobe-fonts/source-han-serif` repository 的 release 分支，以 fontTools 產生目前公開 HTML 字元與 ASCII 的 WOFF 子集。Adobe OFL 保留字名 Source，因此修改過的子集內部更名為 LULUKA Songti TC，字形維持思源宋體。兩個字重與完整授權存放於 Supabase `luluka-public-fonts`，匿名下載 SHA-256 與 CORS 已验证。新增子集外的標題文字需重新產生子集；字型二進位不放入 GitHub。

授權：https://umstsvobrqgstsjdvpza.supabase.co/storage/v1/object/public/luluka-public-fonts/9ff5bb567e1b92c801fc1069e5fbf992ff8efccacb9db94e5959a5b3ba9bb903/source-han-serif-OFL.txt

## 兩個分類入口

首頁與導覽改為飲食生活（Culinary & Retail，`/culinary-retail/`）與文化視覺（Arts & Media，`/arts-media/`）。新分類保留 Coming Soon，小麥廚坊舊網址轉到飲食生活，其餘舊品牌網址轉到文化視覺；舊路徑不列入 sitemap。公開分享圖與思源宋體子集已依新文字更新，均存放於 Supabase。

## 統一 Coming Soon 字體

目前全站文字統一使用現有 Coming Soon 標題的思源宋體子集，包括首頁標誌、分類標題與英文副標、選單、頁尾、Coming Soon 頁，以及隱私頁。字型已依目前 HTML 字元重新產生與上傳，保留黑金配色、置中排版、較寬字距與毛玻璃互動。

## 直式分類卡牌

兩個入口改為 2:3 直式卡牌，使用單色香檳金線刻底圖：飲食生活以餐盤、穀物與餐具呈現，文化視覺以鏡頭、底片與典藏照片呈現。圖像由 image generation 產生，原始檔保留於 checkout 外的 `/workspace/generated_images`，公開展示副本存於 Supabase `luluka-public-media`，匿名 SHA-256 下載比對通過。觸及卡牌時底圖模糊，文字保持清楚。

## 新藝術風格底圖

直式卡牌的底圖改為慕夏式新藝術風格：平面化植物裝飾、流動曲線與幾何象徵，減少寫實陰影與雕刻細節。飲食與文化兩張圖維持單色黑金，生成原檔留在 checkout 外，公開副本以內容雜湊路徑存於 Supabase，匿名下載驗證通過。

## 霧面遊戲卡牌底圖

兩張底圖改為霧面薄紗質感的單色黑金遊戲插圖，移除環繞裝飾邊框。插圖顯示範圍限制於卡牌右下約 2/3 的寬、高，標題與英文分類移至左上。生成原檔留在 checkout 外，公開圖片存於 Supabase，匿名下載雜湊驗證通過。

## 五主題遊戲卡牌

首頁改為視覺設計、品牌孵化、廣告出版、駐地餐飲、時尚生活五個主題，各有 Coming Soon 頁。插圖為原創的可愛 2D 奇幻遊戲場景，維持單色黑金並鋪滿卡牌，搭配圓角內框與浮起互動；圖檔保留在 checkout 外並上傳 Supabase，匿名下載 SHA-256 驗證通過。分享圖、思源宋體子集、選單、canonical 與 sitemap 一併更新。

## 簡潔職業符號卡牌

五張卡牌改用原創金色線條 SVG：筆尖、嫩芽、擴音器、廚師帽、衣架，保留留白與細框。符號存於 Supabase 公開素材 bucket，匿名下載逐一驗證；首頁不再請求繁複遊戲插畫。中文標題採直式排列，英文名稱沿旁側直向閱讀。字型暫沿用已授權的思源宋體子集，待使用者確認「猴尊宋體」來源與網站使用授權後替換。
