import time, importlib, traceback
from concurrent.futures import ThreadPoolExecutor

from globalState import GlobalState
from imports.utils import log_message

def timers_checker(bot_state: GlobalState, bot):
    for key, value in bot_state.get_all_timers().items():
        if value['type'] == 'interval':
            handle_interval(key, value, bot, bot_state)
        if value['type'] == 'timeout':
            handle_timeout(key, value, bot, bot_state)

def handle_interval(id, interval, bot, bot_state):
    if int(time.time()) < interval['next_call_at']:
        return
    interval['next_call_at'] = int(time.time()) + int(interval['interval'])
    bot_state.update_interval(id, interval)
    module = importlib.import_module(interval['cmd'])
    module.interval_up(interval['context'], bot, bot_state)

def handle_timeout(id, timeout, bot, bot_state):
    if int(time.time()) < timeout['next_call_at']:
        return
    bot_state.remove_timer(id)
    module = importlib.import_module(timeout['cmd'])
    module.timeout_up(timeout['context'], bot, bot_state)

def timer_handler_init(bot_state: GlobalState, bot):
    log_file = "interval_handler_log"
    bot_state.get_all_timers(True)
    while True:
        with ThreadPoolExecutor() as executor:
            try:
                executor.submit(timers_checker, bot_state, bot)
            except Exception as e:
                error_message = f"An error occurred: {str(e)}\n"
                error_message += ''.join(traceback.format_exception(None, e, e.__traceback__))
                # Log the detailed error message
                log_message(error_message, log_file, True)
        time.sleep(10)
