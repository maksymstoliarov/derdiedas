.PHONY: install run-bot stop-bot

install:
	@echo "Installing Python dependencies..."
	@pip install -r requirements.txt

run-bot:
	@echo "Starting bot with nohup..."
	@nohup python bot.py &

stop-bot:
	@echo "Stopping bot..."
	@pkill -f "python bot.py"