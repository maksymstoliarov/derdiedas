.PHONY: run stop

run:
	@echo "Starting with nohup..."
	@nohup python main.py &

stop:
	@echo "Stopping..."
	@pkill -f "python main.py"