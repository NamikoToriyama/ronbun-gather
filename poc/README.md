# POC (Proof of Concept) Directory

This directory contains proof-of-concept code for individual features. Use these files to test components separately before running the integrated main system.

## 📁 File Overview

### 🔍 Search & Translation
- **`arxiv_deepl_poc.py`**: arXiv search + DeepL translation integration test
- **`paper_scraper.py`**: Google Scholar search functionality

### 🈯 Translation
- **`deepl_test.py`**: DeepL API connection and translation test

### 📝 Notion Integration
- **`updated_notion_poc.py`**: Notion API integration (configured for actual database structure)

## 🧪 Running Tests

### 1. DeepL Translation Test
```bash
python poc/deepl_test.py
```
- Test DeepL API connection
- Display usage statistics
- Run sample translation

### 2. Notion Integration Test
```bash
python poc/updated_notion_poc.py
```
- Test Notion database connection
- Create test paper page
- Add abstract to page content

### 3. arXiv + DeepL Integration Test
```bash
python poc/arxiv_deepl_poc.py
```
- Search papers from arXiv
- Translate abstracts to Japanese
- Generate research insights

### 4. Google Scholar Search Test
```bash
python poc/paper_scraper.py
```
- Search papers from Google Scholar
- Extract PDF, DOI, and image links

## ⚙️ Required Configuration

Set the following API keys in your `.env` file:

```bash
# DeepL API (for translation)
DEEPL_API_KEY=your_deepl_api_key

# Notion API (for data storage)
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id
```

## 📊 Notion Database Structure

Create a Notion database with these properties for POCs to work:

| Property Name | Type | Description |
|---------------|------|-------------|
| NAME | Title | Paper title |
| URL | URL | Paper URL |
| Paper | Text | Summary/notes |
| Date Added | Date | Date added |
| Read | Select | Reading status |
| **Keyword** | **Text** | **Search keyword used to find this paper** |

## 🔄 Relationship to Main System

These POC files test individual features that are integrated in `main.py` for automated execution:

1. **arXiv Search** → DeepL Translation → Notion Storage → LINE Notification
2. **Daily cron execution** automates this entire pipeline