# Repositorio de Bases de Datos — BAV Brand Intelligence Colombia 2026

Todas las bases de datos utilizadas en el modelo de Capital Intangible.

---

## Estructura

```
data/
├── brandscape/          # Fuente primaria: encuesta Brandscape Colombia 2026
├── digital_signals/     # Señales digitales (Google Trends, Wikipedia, Social, Total Search)
├── financiero/          # Datos financieros cruzados con indicadores BAV
└── maestra/             # Bases consolidadas y Base Maestra Excel
```

---

## brandscape/

Datos crudos de la encuesta Brandscape Colombia 2026 (Young & Rubicam / BAV Group).
Segmentados por tipo de audiencia.

| Archivo | Descripción | Marcas |
|---|---|---|
| `brandscape_usuarios_colombia_2026.csv` | Pilares BAV para **Usuarios** de cada marca | 82 |
| `brandscape_no_usuarios_colombia_2026.csv` | Pilares BAV para **No Usuarios** de cada marca | 82 |

**Columnas clave:** `differentiation_c`, `relevance_c`, `esteem_c`, `knowledge_c`, `brand_asset_c`, `brand_stature_c`, `brand_strength_c`

La diferencia `brand_asset_rank_usuarios − brand_asset_rank_no_usuarios` es la base del **Síndrome de París**.

---

## digital_signals/

Señales de presencia y demanda digital en Colombia.

| Archivo | Fuente | Métrica principal |
|---|---|---|
| `gt_scores_colombia_2026.csv` | Google Trends API (pytrends, geo=CO, 12 meses) | `gt_raw_12m_colombia` (0–100) |
| `wiki_scores_colombia_2026.csv` | Wikipedia REST API (pageviews) | `wiki_views_monthly`, `wiki_score` |
| `social_scores_colombia_2026.csv` | YouTube Search Python + TikTok | `youtube_score`, `tiktok_score`, `social_score_compuesto` |
| `totalsearch_scores_colombia_2026.csv` | Consolidado de los tres anteriores + BAV pillars | `ts_score`, `search_gap`, `paris_syndrome` |

### Metodología de scores digitales

**Google Trends:** promedio de interés mensual en 12 meses. Escala relativa 0–100 (Google).

**Wikipedia:** vistas mensuales reales vía API. Normalizadas sobre el máximo del set (Mercado Libre = 1,278,472 vistas). `wiki_score = (vistas / vistas_max) × 100`

**YouTube:** escala logarítmica por suscriptores del canal oficial:
- ≥1M subs → 100 | ≥500K → 85 | ≥100K → 70 | ≥50K → 55 | ≥10K → 40 | ≥1K → 25 | <1K → 10

**Social Score Compuesto:** `(youtube_score × 0.6) + (tiktok_score × 0.4)`

**Total Search Score:** `avg(gt_score, wiki_score, social_score_compuesto)`

---

## financiero/

| Archivo | Descripción |
|---|---|
| `bav_financiero_cruzado_2026.csv` | Ingresos 2024, Activos, Margen, ROE, datos BVC, Intangible Value cruzados con scores BAV |

Fuentes financieras: reportes anuales 2024, BVC (Bolsa de Valores de Colombia), estimaciones internas para empresas no cotizadas.

---

## maestra/

| Archivo | Descripción |
|---|---|
| `bav_scores_colombia_2026_REAL.csv` | Scores BAV consolidados por marca y categoría (82 marcas) |
| `bav_commerce_monobrands_2026.csv` | Scores BX/CO/CX + BavPulse para todas las marcas del modelo |
| `BAV_Brand_Intelligence_Colombia_2026_Base_Maestra.xlsx` | Excel con 3 hojas: Base Maestra (82 marcas), Diccionario de Datos, Fuentes |

---

## Fórmulas del Modelo

| Indicador | Fórmula |
|---|---|
| **Síndrome de París** | `percentil_rank(brand_asset_rank_usuarios − brand_asset_rank_no_usuarios) × 100` |
| **Brand Asset KPI** | `percentil_rank(avg(eDif, eRel, eEst, eFam)) × 100` |
| **BAV Pulse KPI** | `percentil_rank(avg(GT_Raw, Wiki_Raw, Social_Raw)) × 100` |
| **BX Score** | `avg(BAV_Pulse_KPI, BrandAsset_KPI)` |
| **CO Score** | `percentil_rank(Ingresos2024 / TotalActivos2024) × 100` |
| **CX Score** | `avg(CX_KPI, Loyalty_KPI)` |
| **Loyalty KPI** | `percentil_rank(eFam_Raw) × 100` |

---

*Fuente principal: Brandscape Colombia 2026 — BAV Group / Young & Rubicam*
