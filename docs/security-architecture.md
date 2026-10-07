# LULUKA 公開網站與私密資料架構

## 已實作的邊界

網站是公開的靜態 HTML。`scripts/public-files.json` 是逐檔公開白名單，
`python3 scripts/build_public.py` 只將名單中的檔案複製到 `.site/`。
GitHub Actions 只部署 `.site/`，不部署整個 checkout。新素材不會自動公開。
白名單應與內容審核一起修改；白名單不能判斷檔案內是否含個資或秘密。

公開頁面附有 CSP，禁止網路 API 連線、表單提交、嵌入框架與外部腳本。
首頁內嵌腳本使用 SHA-256 hash 授權；修改腳本時必須同步更新 CSP hash。
為相容現有版型，CSS 仍允許 inline style，不能將此配置描述為完整 XSS 防護。
GitHub Pages 不支援自訂安全回應標頭；若需要 `frame-ancestors`、HSTS、
`X-Content-Type-Options` 等標頭，須在支援它們的主機或反向代理配置並驗證。

`docs/`、`scripts/`、未列入名單的檔案及未來的後端程式不在網站 artifact 中。
這不會讓公開 GitHub repository 的檔案變成私密！如果原始碼 repository 是公開的，
任何提交的資料及 Git 歷史都可能被讀取。不要把私密資料放入這個 repository，
也不要把 `.gitignore` 或 `robots.txt` 當成存取控制。

## 私密儲存（已選擇 Supabase，線上專案尚未接入）

設定步驟見 [Supabase 私密資料設定](supabase-setup.md)。新專案 SQL migration
已加入品牌 RLS、MFA（AAL2）要求、private bucket 及分離的發布審核權限，
並以本機 PostgreSQL 權限測試驗證。尚未取得線上專案設定，不能聲稱已保護實際雲端資料。

建議使用獨立的 Supabase 專案，或具備同等權限能力的服務：

1. 私有物件儲存放原始照片、授權書與内部文件。Bucket 必須是 private。
2. 資料庫內部表放聯絡資料、照片描述、權利紀錄、審核狀態及操作紀錄。
   啟用 RLS；預設拒絕匿名存取。不要只靠前端隱藏選單。
3. 管理後台使用獨立 private repository 與執行服務，必須有登入、MFA、
   伺服器端授權與角色分工。網站訪客不能拿到管理員金鑰。
4. 將角色分成資料編輯、發布審核、系統管理；普通編輯不可自行核准發布。
   以權限及資源擁有關係檢查每次讀寫，包含直接 API 請求。
5. 發布工作只匯出核准的公開欄位與公開衍生圖。禁止直接匯出完整資料表、
   原始檔、私密紀錄或管理 API 回應。發布過的資料可能被搜尋引擎永久快取。
6. 私密下載使用通過授權後產生的短效 signed URL；不要嵌入公開頁面。
   公開圖片應另存縮圖、去除 EXIF/GPS，先審核畫面是否有個資。
7. 金鑰只放後端的安全環境設定；最小權限、輪替、存取稽核、備份與復原測試
   是後端上線必要項目。不要用 GitHub Pages 執行後端或保存秘密。

公開網站 -> 核准的 HTML / CSS / 圖片

已登入管理人員 -> 身分驗證 -> 後端權限檢查 -> 私有資料庫 / 私有檔案

後端發布流程 -> 權利與內容審核 -> 限定欄位的公開匯出 -> 公開白名單

Supabase 線上品牌資料表、RLS、MFA 政策與私有 buckets 已建立並檢查；
39 份原始內容已遷移及重新下載核對，原始封存的匿名下載已遭拒絕；管理員登入與管理後台尚未建立。不可描述為整個私密工作流已完成。
待補齊安全設定後，驗證匿名讀取、
跨使用者讀取、低權限發布均遭拒絕，並驗證授權讀写和備份復原。

## 部署及 SEO

正式網站假設為 `https://luluka.org`。路徑為 `/xiaomai/`、`/kaiaote/`、
`/yongbindata/`。Pages 的 Source 需改成 **GitHub Actions**，才能使用
白名單部署流程；若仍使用「Deploy from a branch」，不能保證部署隔離。
本次尚未修改 GitHub settings、推送或部署正式站。

本機驗證：

```sh
python3 scripts/build_public.py
python3 scripts/check_public.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory .site
```

canonical、sitemap、社群分享圖片與結構化資料已設定。正式部署後，在 Google
Search Console 驗證網域並提交 `https://luluka.org/sitemap.xml`。
SEO 設定不保證排名或收錄。商品、遊戲、館藏尚未提供，本站只公開已確認的
品牌定位，沒有捏造價格、評論、地址、聯絡方式或館藏資料。
