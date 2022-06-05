from justlend import JustLend
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import schedule
import time
import os

RISK_ALERT_THRESHOLD = 0.015
RISK_ALERT_DIGIT = int(len(str(RISK_ALERT_THRESHOLD).replace(".", "")))

HELP_TEXT = (
    "/risk_check - Get current Risk-value. \n"
    "/risk_alert_set - Set /risk_check notification if risk ups than the threshold. \n"
    "/risk_alert_unset - Unset /risk_alert_set"
)


class TeleBot:
    def __init__(self, addr):
        self._just = JustLend(addr)
        self.last_checked_risk_value = self._just.get_risk_value()

    def remove_job_if_exists(self, name: str, context: CallbackContext) -> bool:
        current_jobs = context.job_queue.get_jobs_by_name(name)
        if not current_jobs:
            return False
        for job in current_jobs:
            job.schedule_removal()
            return True

    def start(self, update: Update, context: CallbackContext) -> None:
        update.message.reply_text(text="/help to see commands.")

    def help(self, update: Update, context: CallbackContext) -> None:
        update.message.reply_text(text=HELP_TEXT)

    # Check risk value
    def risk_check(self, update: Update, context: CallbackContext):
        update.message.reply_text(f"{round(self._just.get_risk_value() * 100, RISK_ALERT_DIGIT)}%")

    def _risk_alert(self, context: CallbackContext):
        diff = self._last_checked_risk_value - self._just.get_risk_value()
        diff = round(diff, RISK_ALERT_DIGIT)
        # TODO: Calculate minus or plus
        if RISK_ALERT_THRESHOLD <= abs(risk_diff):
            job = context.job
            context.bot.send_message(
                job.context,
                text="Risk Alert\n"
                + f"[{self.last_checked_risk_value*100}] -> [{self._just.get_risk_value()*100}]"
                + "\n"
                f"[diff]: {risk_diff}",
            )
            self.last_checked_risk_value = self._just.get_risk_value()

    def risk_alert_set(self, update: Update, context: CallbackContext):
        chat_id = update.message.chat_id
        job_removed = self.remove_job_if_exists(
            str(chat_id) + "_risk_alert_set", context
        )

        if job_removed:
            update.message.reply_text("Risk alert has been removed.")
        else:
            self._last_checked_risk_value = self._just.get_risk_value()
            context.job_queue.run_repeating(
                self._risk_alert,
                interval=60 * 60,
                context=chat_id,
                name=str(chat_id) + "_risk_alert_set",
            )
            update.message.reply_text("Risk alert has been set.")
        )

        if job_removed:
            update.message.reply_text("Alert has been reset.")
        else:
            self.last_checked_risk_value = self._just.get_risk_value()
            update.message.reply_text("Alert has been set.")

    def risk_alert_unset(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        job_removed = self.remove_job_if_exists(str(chat_id) + "_just", context)
        text = "Unalerted   " if job_removed else "You have no active alert."
        update.message.reply_text(text)


if __name__ == "__main__":
    # Wallet Address
    bot = TeleBot(os.environ["ENV_JUSTALERT_ADDR"])

    # Telegram Bot Token
    updater = Updater(os.environ["ENV_JUSTALERT_TOKEN"])
    updater.dispatcher.add_handler(CommandHandler("start", bot.start))
    updater.dispatcher.add_handler(CommandHandler("help", bot.help))

    updater.dispatcher.add_handler(CommandHandler("risk_check", bot.risk_check))
    updater.dispatcher.add_handler(CommandHandler("risk_alert", bot.risk_alert_set))

    updater.dispatcher.add_handler(
        CommandHandler("risk_alert_unset", bot.risk_alert_unset)
    )

    updater.start_polling()

    while True:
        schedule.run_pending()
        time.sleep(1)
