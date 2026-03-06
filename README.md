# 🗄️ Fireside Blacklist Bot: Development Archive

> [!CAUTION]
> **WARNING: LEGACY CODE & HIGH BUG DENSITY**
> This repository contains unoptimized code from a development phase. It is **riddled with bugs**, logic gaps, and potential stability issues. It is preserved for historical interest—**do not use this for active server moderation.**

> [!IMPORTANT]
> **This repository is officially ARCHIVED.** It serves as a timeline of the Fireside Blacklist Bot, created during **Fall 2025**.

## 📖 Project Overview

Fireside was a Discord security concept designed to create a **Global Blacklist System**. The project aimed to bridge the gap between separate Discord communities, allowing them to share a "reputation database" to keep bad actors out of all participating servers simultaneously.

## ⚠️ Fall 2025 Context & Requirements

The environment requirements (found in the `.env` file) changed significantly between versions.

* **Manual Inspection Required:** Because each version (V1.0, V1.1, V1.2) introduced new features like dynamic status updates and localization, the required environment variables differ.
* **Check the Scripts:** Before attempting to run a specific version, **you must open the script** and look at the `os.getenv` calls at the top of the file to see which variables (e.g., `OWNER_ID`, `BOT_ACTIVITY_TYPE`, `LOCALE`) are necessary for that specific build.

---

## 📂 Version History (The Evolution)

### 🥉 Phase 1: The Foundation (`firesidev1.py`)

* **Status:** Prototype / Buggy
* **Focus:** First implementation of the `blacklist.json` logic and the "Server Access Request" flow.
* **Language:** Hardcoded Dutch.

### 🥈 Phase 2: Performance Attempt (`firesidev1.1.py`)

* **Status:** Beta / Unstable
* **Focus:** API Optimization.
* **Key Changes:** Introduced **User Caching** (`_cached_users`) and background tasks.
* **Warning:** Caching logic in this version is known to cause sync issues with the JSON database.

### 🥇 Phase 3: "Final" State (`fireside.1.2.py`)

* **Status:** Legacy Final / Most Advanced
* **Focus:** Professional UI and Localization.
* **Key Changes:** Added a full English/Dutch translation engine and a global error handler for slash commands.
* **Known Issues:** The most stable of the three, but still prone to race conditions during high-concurrency events (e.g., many users joining at once).

---

## 🛠️ Technical Setup (Archive Reference)

1. **Python Version:** Developed for Python 3.8+ (Fall 2025 era).
2. **Library:** `discord.py` (ensure you use the version compatible with late 2025 intents).
3. **Required Files:** The bot expects `blacklist.json`, `server_configs.json`, and `action_history.json` to exist in the root folder.

---

## 📜 License

This archive is released under the **MIT License**.

---

*Archive curated by **t_62__*** *Origin: Fall 2025*

---

Would you like me to generate a **`.gitignore`** file for you? This is crucial to ensure you don't accidentally upload your `token` or `.env` files to GitHub when you push this archive.
