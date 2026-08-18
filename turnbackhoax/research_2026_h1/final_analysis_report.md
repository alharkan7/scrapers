# TurnBackHoax Analysis Report (Jan - Jul 2026)

The data pipeline successfully processed **4,374 hoaxes** from January 1st to July 31st, 2026. Here are the primary findings from the three core research angles:

## 1. The Economy of Despair (Scams & Aid Hoaxes)
**Total Identified:** 1,153 Hoaxes (26% of all data)
Scammers continue to prey on economic desperation, primarily through fake government grants (*Hibah*, *Bansos*), fake job vacancies (*Lowongan*, *CPNS*), and impersonation of the Minister of Finance (Purbaya).

* **Top Spread Vectors:** WhatsApp (3,012 mentions) and Facebook (1,302 mentions).
* **Statistical Finding:** There is a highly statistically significant relationship ($p < 0.0001$) showing that Economic Scams spread disproportionately on WhatsApp and TikTok, whereas Political hoaxes spread mostly on Facebook.

## 2. Political Disinformation (Prabowo's Early Presidency)
**Total Identified:** 1,571 Hoaxes (35% of all data)
Political disinformation remains the largest single category, but the focus is split heavily between domestic politics and geopolitics.

* **Top Domestic Targets:** Prabowo Subianto (300 hoaxes), Joko Widodo (159 hoaxes), and Gibran Rakabuming (101 hoaxes). We also saw emerging narratives around the Free Nutritious Meals program (MBG) and corruption (KPK).
* **Geopolitics (The Global Crisis):** The Middle East conflict (Iran, Israel, Gaza) was the single largest political topic, spawning **586 unique hoaxes**. US Politics (Trump/Biden) followed with 178 hoaxes.

## 3. The Anti-Disinfo Paradox (Reality vs Legislation)
The dataset empirically highlights the gap in categorization. Officially, TurnBackHoax labeled almost 80% of these articles as "Uncategorized". However, via keyword inference, we proved that:
* ~33% are Political
* ~26% are Economic Scams
* ~8% are Medical/Health Disinformation (which spiked massively in May 2026)

This provides empirical data for the research paper: while the government may cite "foreign propaganda" for new speech laws, everyday citizens are primarily facing domestic economic scams on WhatsApp and TikTok.

## 4. Emerging Threats (The May Health Scare & Rise of AI)
A newly developed script (`06_emerging_threats_2026.py`) identified two critical emerging trends in the 2026 data:

* **The May Health Scare:** A massive 23.4% of all hoaxes in May 2026 were health-related. A highly coordinated narrative pushed conspiracies around "sudden death" (*Kematian, Mendadak*), child autism (*Autisme, Anak*), and Bill Gates.
* **The Rise of Deepfakes & AI:** A staggering **32.2%** of all 2026 hoaxes (1,409 total) relied on AI, deepfakes, or advanced media manipulation (*kloning suara, suntingan, rekayasa video*). This format weaponization was distributed across all categories, including 468 Political hoaxes and 375 Economic Scams.

---

## Visualizations

### Temporal Spikes in Hoaxes (Jan-Jul 2026)
![Temporal Spikes](/Users/alharkan/Documents/Repositories/Archive/scrapers/turnbackhoax/research_2026_h1/visualizations/temporal_spikes.png)
*Notice the massive spike in Health (Kesehatan) and Economic Scams in May 2026.*

### Platform vs. Hoax Category
![Platform Heatmap](/Users/alharkan/Documents/Repositories/Archive/scrapers/turnbackhoax/research_2026_h1/visualizations/platform_heatmap.png)
*Visualizing the Chi-Square test: Scams dominate TikTok and WhatsApp, while Politics dominate Facebook.*

### Topic Modeling (Latent Dirichlet Allocation)
![Topic Modeling](/Users/alharkan/Documents/Repositories/Archive/scrapers/turnbackhoax/research_2026_h1/visualizations/topic_modeling_bars.png)
*Unsupervised machine learning extracted 5 primary topics, perfectly matching the qualitative findings above (e.g., Topic 5 is Israel/Iran, Topic 2 is Prabowo/Gibran/MBG).*
