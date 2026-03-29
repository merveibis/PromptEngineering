# Lead Capture to CRM

**Platform:** Google Antigravity (Agents + Workflows)
**Dataset:** [Kaggle Marketing Agency B2B Leads](https://www.kaggle.com/datasets/getivan/marketing-agency-b2b-leads) — ODC PDDL (Public Domain)

---

## Architecture

```
HTTP Webhook Trigger  →  process_lead()  →  CRM (Sheets / CSV)  →  Gemini AI Completion
     [Step 0]              [Step 1]              [Step 2]               [Step 3]
```

---

## 5 Kriter Karşılaması

| # | Kriter | Nasıl Karşılanıyor | Dosya |
|---|--------|--------------------|-------|
| 1 | **Veri girişi / Gerçek tetikleyici var mı?** | `POST /webhook/lead` endpoint'i JSON payload alır, HMAC-SHA256 ile doğrular. `GET /health` ile sunucu durumu kontrol edilir. | `main.py` |
| 2 | **Veri işleniyor mu?** | `process_lead()` ham veriyi doğrular, endüstri/kaynak eşler, 0–100 arası ağırlıklı lead skoru hesaplar, UUID üretir, 18 alanlı CRM şemasına dönüştürür. | `functions/process_lead.py` |
| 3 | **Dış sisteme bağlantı kurulmuş mu?** | `append_lead_to_sheet()` Google Sheets API'ye OAuth2 ile bağlanır (yapılandırılmışsa), yoksa `data/crm_leads.csv`'ye yazar. Her çağrıda CRM satır referansı döner. | `functions/sheets_connector.py` |
| 4 | **AI gerçekten kullanılmış mı?** | `categorise_and_summarise()` her lead için Gemini 2.0 Flash Lite'ı çağırır. JSON çıktısı: `category`, `priority` (HOT/WARM/COLD), `summary` (≤30 kelime satış briefi). | `functions/ai_completion.py` |
| 5 | **Workflow baştan sona çalışıyor mu?** | `demo_pipeline.py` ile Kaggle'dan alınan 20 gerçek lead pipeline'dan geçirilir. Tüm adımlar sıralı çalışır ve `crm_leads.csv` çıktısı üretilir. | `demo_pipeline.py` |

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # GEMINI_API_KEY ekle
python main.py
```

## Demo — 20 Kaggle Lead'ini Toplu Çalıştır

```bash
python demo_pipeline.py
```

## Test Webhook (Tekil)

```bash
curl -X POST http://localhost:5000/webhook/lead \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name": "James",
    "last_name": "Johnson",
    "email": "info@1015multimedia.com",
    "company_name": "1015 Multimedia & Marketing",
    "industry": "marketing",
    "source": "website"
  }'
```

## Run Tests

```bash
pytest tests/ -v
```

## Workflow

See `workflow/antigravity_workflow.json` for the Google Antigravity export.
