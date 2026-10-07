# Supabase 私密資料設定

## 已完成與尚未完成

已提供 migration、公開白名單隔離、本機 PostgreSQL 權限測試及 HTTPS
設定工具。已在指定 Supabase 專案建立線上資料表與 buckets，檢查 RLS、匿名
grants 與 bucket 可見性。39 份原始內容已完成上傳與雜湊驗證。尚無管理後台或管理員 MFA 實際登入驗證。
遷移進度及操作見 [圖文影音遷移](media-migration.md)。

### 資料與權限

- `public.luluka_records`：私密資料，名稱中的 public 是 API schema，
  **不代表資料公開**。匿名權限撤銷，RLS 依品牌與角色控管。
- `luluka_private.brand_memberships`：只由可信 SQL 管理者配置，前端無寫入權限。
  此 schema 不可加入 Supabase 的 exposed schemas。
- `luluka-private` Storage bucket：private，物件路徑為
  `xiaomai/...`、`kaiaote/...` 或 `yongbindata/...`。最高 25 MiB，允許
  JPEG、PNG、WebP、TIFF、PDF。原始照片、PDF 都不能直接放到公開部署。
- viewer 可讀、editor 可讀寫、reviewer 可讀及審核、admin 可管理所屬品牌。
  所有成員均須完成 MFA（JWT AAL2）；密碼登入但未完成 MFA 不允許存取。
- 審核 RPC 只保存指定的公開標題及摘要；拒絕過期版本。編輯者不能審核。
  審核後仍為私密 snapshot，不會自動發布到 HTML，也不提供匿名 API。
  每次公開需由審核者確認內容權利與個資，發布流程必須 escape HTML。

## 專案接入

在 Supabase 建立專案後，於雲端環境設定填入非秘密變數：

- `SUPABASE_URL`：`https://<project-ref>.supabase.co`
- `SUPABASE_PROJECT_REF`：專案 reference ID

若要讓設定工具自動套用，將 Supabase Management API access token 安全填入
`SUPABASE_ACCESS_TOKEN` secret。只允許送往 `api.supabase.com`，不要貼到聊天、
Git、HTML 或命令列參數。此 token 可管理 Supabase 專案，使用最小可用權限，
完成後撤銷或移除綁定；網站執行不需要此 token，也不需要 service_role key。

```sh
python3 scripts/configure_supabase.py --check
python3 scripts/configure_supabase.py --apply
```

此新專案初始化工具會拒絕已有 LULUKA 表、bucket 或任何既有 Storage policy 的專案，避免
寬鬆 policy 與新 policy 以 OR 合併而洩露資料。不能盲目刪除既有 policy。
Migration 是一次性的新專案設定；重跑或既有專案遷移需另行審核。
目前已初始化此專案，不要再執行 `--apply` 初始化。

若不提供 Management API token，可在 Supabase SQL Editor 檢查並執行
`supabase/migrations/202610070001_private_brands.sql`，但仍須檢查既有 Storage
policies 及匿名權限，不能只假設 migration 成功就已安全。

## 第一位管理員及登入

1. 在 Authentication 設定關閉開放註冊，只邀請已知管理人員。啟用 TOTP MFA。
2. 邀請使用者並取得其 Auth user UUID。透過可信 SQL Editor 分配角色，例如：

```sql
-- 將佔位文字換成經確認的管理員 Auth UUID；不是 email，也不是密碼。
insert into luluka_private.brand_memberships (brand, user_id, role)
values
  ('xiaomai', 'REPLACE_WITH_AUTH_USER_UUID'::uuid, 'admin'),
  ('kaiaote', 'REPLACE_WITH_AUTH_USER_UUID'::uuid, 'admin'),
  ('yongbindata', 'REPLACE_WITH_AUTH_USER_UUID'::uuid, 'admin');
```

3. 未來的獨立後台透過 Supabase Auth 登入並完成 MFA，不使用 service_role
   繞過權限。只讀角色、編輯角色和審核角色應使用不同帳號，避免互相共用登入。
4. 後台若透過 cookie 保存登入，使用 HttpOnly、Secure、SameSite 與 CSRF 防護。
   Session、原始資料與 signed URL 不能寫入公開網站或共享快取。

## 驗證範圍

`python3 scripts/test_supabase_permissions.py` 在無對外網路、無公開 port 的
一次性 PostgreSQL 17 container 中執行。映像使用固定 digest，產生臨時密碼，
測試後移除 container。Auth/Storage schemas 是測試 stub，驗證 PostgreSQL
grants、RLS、角色與審核函式；不是實際 Supabase Auth JWT 或 Storage HTTP 測試。

正式專案還必須驗證：匿名讀取失敗、AAL1 被拒、AAL2 授權讀寫成功、跨品牌拒絕、
匿名 Storage public URL 失敗、授權短效下載成功及逾期失效。確認 MFA、備份、
稽核與帳號撤權流程後才能儲存真實資料。管理 API token / service_role 可繞過
一般 RLS 邊界，必須視為高權限秘密，不能給網站訪客。
