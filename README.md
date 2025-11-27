# Telegram Job Application Bot

An automated Telegram bot that streamlines the job application process for your company. Applicants can apply directly through Telegram, and you receive AI-powered evaluations and notifications.

## Features

### For Applicants
- 🤖 Interactive conversation flow
- 💼 Multiple position options with role-specific questions
- 📄 CV upload (PDF)
- 🖼️ Proof of work submissions (images, videos, links)
- 📝 Optional quizzes (language, AI tools, IQ tests)
- ✅ Instant confirmation upon submission

### For Admins
- 📬 Real-time Telegram notifications for new applicants
- 🤖 AI-powered applicant evaluation and rating
- 📊 Automatic storage in Google Sheets
- 🔘 Quick action buttons (send quiz, schedule interview, approve/reject)
- 📈 Application statistics

## Architecture

```
telebewerber/
├── src/
│   ├── bot/
│   │   ├── handlers/          # Conversation handlers
│   │   │   ├── application.py # Main applicant flow
│   │   │   ├── admin.py       # Admin commands & notifications
│   │   │   └── quiz.py        # Quiz functionality
│   │   └── conversations/     # Conversation states & keyboards
│   ├── models/                # Data models
│   │   ├── applicant.py       # Applicant data structure
│   │   └── position.py        # Job position definitions
│   ├── services/              # External integrations
│   │   ├── storage.py         # Session storage
│   │   ├── ai_evaluator.py   # AI evaluation
│   │   └── sheets.py          # Google Sheets integration
│   ├── config/                # Configuration
│   └── main.py               # Application entrypoint
├── data/                     # Local data storage
├── .env                      # Environment variables (create from .env.example)
├── requirements.txt          # Python dependencies
└── README.md
```

## Setup

### Prerequisites

- Python 3.10+
- Telegram Bot Token ([Get one from @BotFather](https://t.me/BotFather))
- Google Sheets API credentials (optional)
- Claude or OpenAI API key (optional, for AI evaluation)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd telebewerber
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in your credentials:
   - `TELEGRAM_BOT_TOKEN`: Your bot token from @BotFather
   - `ADMIN_CHAT_ID`: Your Telegram user ID (get from [@userinfobot](https://t.me/userinfobot))
   - `GOOGLE_SHEETS_ID`: Your Google Sheets spreadsheet ID
   - `GOOGLE_SHEETS_CREDENTIALS_FILE`: Path to your service account JSON
   - `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`: Your AI provider API key

5. **Set up Google Sheets (optional)**

   a. Create a new Google Sheets spreadsheet

   b. Get the spreadsheet ID from the URL:
      `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`

   c. Create a service account:
      - Go to [Google Cloud Console](https://console.cloud.google.com/)
      - Create a new project or select existing
      - Enable Google Sheets API
      - Create service account credentials
      - Download JSON key file

   d. Share your spreadsheet with the service account email

6. **Run the bot**
   ```bash
   cd src
   python main.py
   ```

## Usage

### For Applicants

1. Start a chat with your bot
2. Send `/start` to begin the application
3. Follow the interactive prompts:
   - Select position
   - Answer position-specific questions
   - Provide contact information
   - Upload CV
   - Upload proof of work (if required)
4. Receive confirmation

### For Admins

- Receive notifications when applicants complete applications
- Use admin commands:
  - `/admin` - Admin panel info
  - `/stats` - View application statistics
- Click action buttons in notifications to:
  - Send quiz to applicant
  - Send interview link
  - Approve/reject applicant

## Customization

### Adding New Positions

Edit `src/models/position.py` and add new positions to the `POSITIONS` dictionary:

```python
POSITIONS = {
    "new_role": Position(
        id="new_role",
        name="New Role Name",
        description="Role description",
        questions=[
            Question("q1", "Your question?", QuestionType.TEXT),
            Question("q2", "Choose one:", QuestionType.CHOICE,
                    ["Option A", "Option B", "Option C"]),
        ],
        requires_cv=True,
        requires_proof_of_work=True,
        proof_of_work_description="Share your portfolio"
    ),
}
```

### Configuring AI Evaluation

The AI evaluator analyzes applicant responses and provides a rating (0-10) and feedback.

**Using Claude (Anthropic):**
```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key
AI_MODEL=claude-3-5-sonnet-20241022
```

**Using OpenAI:**
```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_key
AI_MODEL=gpt-4o
```

## Deployment

### Railway / Render

1. Push your code to GitHub
2. Create new service on Railway/Render
3. Connect your GitHub repository
4. Add environment variables from `.env`
5. Set start command: `cd src && python main.py`

### VPS / Server

1. SSH into your server
2. Clone the repository
3. Install dependencies
4. Set up environment variables
5. Run with process manager (e.g., `pm2`, `systemd`, `supervisor`)

Example with systemd:

```ini
[Unit]
Description=Telegram Job Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/telebewerber/src
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Development

### Project Structure Philosophy

- **Separation of concerns**: Bot logic, data models, and services are clearly separated
- **Modular design**: Easy to add new handlers, questions, or integrations
- **Configuration-driven**: All secrets and settings via environment variables
- **Extensible**: Simple to add new features like quizzes, interviews, etc.

### Adding New Features

1. **New conversation flow**: Add handlers in `src/bot/handlers/`
2. **New data fields**: Update `src/models/applicant.py`
3. **New integrations**: Add services in `src/services/`
4. **New keyboards**: Update `src/bot/conversations/keyboards.py`

## Troubleshooting

### Bot doesn't respond
- Check your `TELEGRAM_BOT_TOKEN` is correct
- Ensure the bot is running (`python main.py`)
- Check logs for errors

### Admin notifications not working
- Verify `ADMIN_CHAT_ID` matches your Telegram user ID
- Check bot has permission to send messages

### Google Sheets not saving
- Verify service account has access to the spreadsheet
- Check `GOOGLE_SHEETS_ID` is correct
- Ensure credentials file path is valid

### AI evaluation failing
- Verify API key is correct
- Check you have credits/quota
- Review logs for specific error messages

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use this for your company's recruitment process!

## Support

For issues or questions, please open an issue on GitHub.
