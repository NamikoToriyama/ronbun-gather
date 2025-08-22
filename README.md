# ronbun-gather
Automatically collect papers on a regular schedule and notify me via LINE.

## Features
- 🔍 Search papers from arXiv and Google Scholar
- 🈯 Translate abstracts to Japanese using DeepL
- 📝 Save papers to Notion database
- 📱 Send notifications via LINE
- ⏰ Daily automated execution with cron

## Setup

### Prerequisites
- Python 3.7+
- macOS/Linux (for cron scheduling)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ronbun-app
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` and add your API keys:
- `DEEPL_API_KEY`: Get from [DeepL Pro API](https://www.deepl.com/pro-api) (free 500k chars/month)
- `NOTION_TOKEN`: Get from [Notion Integrations](https://www.notion.so/my-integrations)
- `NOTION_DATABASE_ID`: Your Notion database ID
- `LINE_CHANNEL_ACCESS_TOKEN`: From [LINE Developers](https://developers.line.biz/)
- `LINE_USER_ID`: Your LINE user ID

### Manual Testing

Test individual components:

```bash
# Test DeepL translation
python poc/deepl_test.py

# Test Notion integration
python poc/updated_notion_poc.py

# Test arXiv + DeepL integration
python poc/arxiv_deepl_poc.py

# Run full paper collection
python main.py
```

### Automated Daily Execution

Set up cron (automatic task scheduler) to run the paper collection every day at 9 AM:

1. Open crontab (cron configuration):
```bash
crontab -e
```

2. Add the following line (replace with your actual path):
```bash
0 9 * * * cd /Users/your-username/path/to/ronbun-app && source venv/bin/activate && python main.py
```

**Explanation of cron format:** `0 9 * * *`
- `0` = minute (0)
- `9` = hour (9 AM)
- `*` = any day of month
- `*` = any month
- `*` = any day of week
- **Result: Runs every day at 9:00 AM**

3. Verify cron setup:
```bash
crontab -l
```

4. Optional: Create logs directory and add logging:
```bash
mkdir logs
```
Then update cron entry:
```bash
0 9 * * * cd /Users/your-username/path/to/ronbun-app && source venv/bin/activate && python main.py >> logs/daily.log 2>&1
```

## API Setup Guide

### DeepL API
1. Visit [DeepL Pro API](https://www.deepl.com/pro-api)
2. Create free account (500k characters/month)
3. Get API key and add to `.env`

### Notion API
1. Create integration at [Notion Integrations](https://www.notion.so/my-integrations)
2. Create a database with properties: 
   - NAME (title) - Paper title
   - URL (url) - Paper URL  
   - Paper (text) - Summary/notes
   - Date Added (date) - Date added
   - Read (select) - Reading status
   - **Keyword (text) - Search keyword used to find this paper**
3. Share database with your integration
4. Get database ID from URL and add to `.env`

### LINE Messaging API
1. Create channel at [LINE Developers](https://developers.line.biz/)
2. Get channel access token
3. Add bot as friend and get your user ID
4. Add both to `.env`
