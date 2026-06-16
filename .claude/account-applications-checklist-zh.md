# 帳戶申請與設定檢查清單（中文版）

**用途：** 單一主清單 — Phase 3 開始前從上到下逐項執行。
**規格：** [SPEC-05](../../docs/SPEC-05-deployment.md) · [SPEC-03](../../docs/SPEC-03-monetisation.md) · [SPEC-02](../../docs/SPEC-02-web-system.md) §9

---

## 階段 1 — 域名與託管（現在就做，M3 前完成）

| # | 任務 | 位置 | 備註 |
|---|------|------|------|
| 1.1 | 購買 `.com` 域名 | Namecheap / Cloudflare Registrar | 年費約 $10；AdSense 硬性要求 |
| 1.2 | 將域名 DNS 指向 Vercel | Vercel → Settings → Domains | Vercel 提供 CNAME/A 記錄 |
| 1.3 | 確認 HTTPS 已啟用 | `https://yourdomain.com` | Vercel 自動配置 TLS |
| 1.4 | 在 Vercel 環境變數更新 `NEXT_PUBLIC_SITE_URL` | Vercel → Project → Settings → Env | 必須完全匹配 `https://` 域名 |

---

## 階段 2 — 分析與 Search Console（與 M3 同時執行）

| # | 任務 | 位置 | 備註 |
|---|------|------|------|
| 2.1 | 建立 GA4 資源 | analytics.google.com | 取得 `G-XXXXXXXXXX` 追蹤 ID |
| 2.2 | 將 `NEXT_PUBLIC_GA_MEASUREMENT_ID` 加到 Vercel 環境變數 | Vercel | 貼上 GA4 追蹤 ID |
| 2.3 | 在 `apps/web/app/layout.tsx` 加入 GA4 `<script>` | 程式碼 | Phase 3 實作任務 |
| 2.4 | 將網站加入 Google Search Console | search.google.com/search-console | 選擇「網域」資源類型 |
| 2.5 | 透過 DNS TXT 記錄驗證 GSC 擁有權 | 你的 DNS 提供商 | GSC 會提供 TXT 記錄值 |
| 2.6 | 提交 sitemap | GSC → Sitemaps → `https://yourdomain.com/sitemap.xml` | Vercel 部署 `next-sitemap` 後執行 |
| 2.7 | 等待 15+ 頁面被收錄 | GSC → Coverage | 約 1–2 週；AdSense 申請前必備 |

---

## 階段 3 — 收款設定（AdSense + 聯盟行銷出款前完成）

| # | 任務 | 位置 | 備註 |
|---|------|------|------|
| 3.1 | 建立 Payoneer 帳戶 | payoneer.com | 推薦所有聯盟行銷收款樞紐 |
| 3.2 | 連結 Payoneer → 香港銀行帳戶 | Payoneer → Withdraw → Bank Transfer | 每月批次提領 |
| 3.3 | 建立 PayPal 帳戶（備用） | paypal.com | 部分計畫僅支援 PayPal |
| 3.4 | 注意：AdSense 直接電匯至香港銀行 | AdSense → Payments → Payment method | 每月最低 $100 USD |

---

## 階段 4 — Google AdSense（20+ 篇文章收錄後開始）

| # | 任務 | 位置 | 門檻 |
|---|------|------|------|
| 4.1 | 確認 AdSense 前置檢查清單通過 | SPEC-02 §9 | 全部打勾 |
| 4.2 | 建立 AdSense 帳戶 | adsense.google.com | 需要 Google 帳戶 |
| 4.3 | 輸入網站 URL | AdSense 註冊 | 使用精確域名 |
| 4.4 | 將 AdSense 驗證程式碼貼到 `layout.tsx` | 程式碼 | Phase 3 任務 |
| 4.5 | 提交 W-8BEN 稅務表格 | AdSense → Payments → Tax info | 選擇 W-8BEN（個人）、香港地址、香港身份證 |
| 4.6 | 等待審核 | Email 通知 | 通常 2–4 週 |
| 4.7 | 審核通過後：在 AdSense 儀表板建立廣告單元 | AdSense → Ads | 取得單元 ID |
| 4.8 | 將 `ca-pub-XXXXXXXX` 加到 `NEXT_PUBLIC_ADSENSE_PUBLISHER_ID` | Vercel 環境變數 | |
| 4.9 | 將廣告單元 ID 加到 `monetisation/adsense_config.json` | 程式碼 | |
| 4.10 | 僅在資訊頁啟用 Auto-ads | SPEC-03 §3.3 | |

---

## 階段 5 — 聯盟行銷計畫（10+ 相關文章上線後申請）

### 優先層級（優先申請）

| # | 計畫 | 佣金 | 申請連結 | 狀態 |
|---|------|------|----------|------|
| 5.1 | **Jasper AI** | 25% recurring 12個月 | jasper.ai/affiliate | ☐ 未申請 |
| 5.2 | **Writesonic** | 30% recurring 12個月 | writesonic.com/affiliates | ☐ 未申請 |
| 5.3 | **Surfer SEO** | 25% recurring 終身 | surfer.io/affiliate | ☐ 未申請 |
| 5.4 | **ElevenLabs** | 22% recurring 12個月 | elevenlabs.io/affiliates | ☐ 未申請 |
| 5.5 | **Notion** | $10/免費註冊 | notion.so/affiliate | ☐ 未申請 |

### 次要層級（第一個 affiliate 核准後再申請）

| # | 計畫 | 佣金 | 申請連結 | 狀態 |
|---|------|------|----------|------|
| 5.6 | Semrush | $200/銷售 | semrush.com/partner | ☐ 未申請 |
| 5.7 | Ahrefs | 20% recurring | ahrefs.com/affiliates | ☐ 未申請 |
| 5.8 | Copy.ai | 30% recurring | copy.ai/affiliates | ☐ 未申請 |
| 5.9 | Descript | 15%/銷售 | descript.com/affiliates | ☐ 未申請 |

### 每份聯盟申請

申請時使用以下描述：
>「為開發者與行銷人員提供 AI 工具比較與教學網站。目前透過程式化 SEO 發布 writing、SEO、生產力工具的長篇文章，流量持續成長中。」

核准後：
- [ ] 取得追蹤連結
- [ ] 新增到 `monetisation/affiliate_map/{slug}.json`（相關文章）
- [ ] 如計畫要求，提交 W-8BEN 或當地稅務文件

---

## 階段 6 — 稅務（首次出款前一次性處理）

| # | 任務 | 備註 |
|---|------|------|
| 6.1 | AdSense W-8BEN | 階段 4.5 已提交 |
| 6.2 | 每個聯盟網路提交 W-8BEN | Impact、ShareASale 等通常在註冊時要求 |
| 6.3 | 保留 Payoneer 稅務文件 | Payoneer 可能發出 1099（美源收入） |

香港與美國無租稅協定。美國來源收入預扣 30%，但大多數 AdSense/聯盟收入非美國來源，實際預扣通常為 0%。詳見 SPEC-03 §3.4。

---

## 階段 7 — GitHub Actions（bot 開始運作）

| # | 任務 | 位置 |
|---|------|------|
| 7.1 | 將 `OPENAI_API_KEY` 加到 GitHub Secrets | GitHub → repo → Settings → Secrets → Actions |
| 7.2 | 加入 `ANTHROPIC_API_KEY` | GitHub Secrets |
| 7.3 | 加入 `PERPLEXITY_API_KEY` | GitHub Secrets |
| 7.4 | 加入 `FIRECRAWL_API_KEY` | GitHub Secrets |
| 7.5 | 加入 `VERCEL_DEPLOY_HOOK_URL` | GitHub Secrets（從 Vercel → Project → Settings → Git → Deploy Hooks 取得） |
| 7.6 | 提交 `ci.yml` 到 `.github/workflows/` | SPEC-05 §5.1 |
| 7.7 | 提交 `bot-cron.yml` 到 `.github/workflows/` | SPEC-05 §5.2 |
| 7.8 | 透過 `workflow_dispatch` 手動觸發 `bot-cron.yml` 一次 | GitHub → Actions → Bot cron → Run workflow |

---

## 解鎖順序總覽

```
階段 1（域名）
    ↓
階段 2（GSC + GA4）← 提交 sitemap，等待收錄
    ↓
階段 3（收款帳戶）← 可平行處理，需 1–3 天
    ↓
階段 7（GitHub Actions）← bot 開始生成文章
    ↓  ← 等到 10+ 篇文章收錄
階段 5（聯盟申請）← 審核需 3–14 天
    ↓  ← 等到 20+ 篇文章收錄
階段 4（AdSense 申請）← 審核需 2–4 週
    ↓
階段 6（稅務表格）← 首次出款觸發
```

---

## 狀態欄圖例

| 符號 | 意義 |
|------|------|
| ☐ 未申請 | 尚未開始 |
| ⏳ 已申請 | 已提交，等待審核 |
| ✅ 已核准 | 已上線運作 |
| ❌ 已拒絕 | 需重新申請或調查 |
