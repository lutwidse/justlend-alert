from justlend import JustLend
from tdr import TDR
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import schedule
import time
import os

RISK_ALERT_THRESHOLD = 0.015
USDD_CR_THRESHOLD = 0.1

RISK_ALERT_DIGIT = int(len(str(RISK_ALERT_THRESHOLD).replace(".", "")))
USDD_CR_DIGIT = int(len(str(USDD_CR_THRESHOLD).replace(".", "")))

HELP_TEXT = (
    "/risk_check - Get current Risk-value. \n"
    "/risk_alert - Set|Unset /risk_check notification if risk moves than the threshold. \n"
    "/usdd_cr_check - Get current USDD collateralization ratio. \n"
    "/usdd_cr_alert - Set|Unset /usdd_cr_check notification if CR moves than the threshold. \n"
    "/usdd_actual_cr_check \n"
    "/usdd_actual_cr_alert"
)


class TeleBot:
    def __init__(self, addr):
        self._just = JustLend(addr)
        self._tdr = TDR()

        self._last_checked_risk_value = self._just.get_risk_value()
        self._last_checked_usdd_cr_value = self._tdr.get_collateralization_ratio()

    def remove_job_if_exists(self, name: str, context: CallbackContext) -> bool:
        current_jobs = context.job_queue.get_jobs_by_name(name)
        if not current_jobs:
            return False
        for job in current_jobs:
            job.schedule_removal()
            return True

    def start(self, update: Update, context: CallbackContext):
        update.message.reply_text(text="/help to see commands.")

    def help(self, update: Update, context: CallbackContext):
        update.message.reply_text(text=HELP_TEXT)

    # Check risk value
    def risk_check(self, update: Update, context: CallbackContext):
        update.message.reply_text(
            f"{round(self._just.get_risk_value() * 100, RISK_ALERT_DIGIT)}%"
        )

    def _risk_alert(self, context: CallbackContext):
        diff = self._last_checked_risk_value - self._just.get_risk_value()
        diff = round(diff, RISK_ALERT_DIGIT)
        # TODO: Calculate minus or plus
        if RISK_ALERT_THRESHOLD <= abs(diff):
            job = context.job
            context.bot.send_message(
                job.context,
                text="Risk Alert\n"
                + f"[{self._last_checked_risk_value*100}%] -> [{self._just.get_risk_value()*100}%]"
                + "\n"
                f"[Risk Moved]: {diff}",
            )
            self._last_checked_risk_value = self._just.get_risk_value()

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

    # Check USDD collateralization ratio.
    def usdd_cr_check(self, update: Update, context: CallbackContext):
        update.message.reply_text(
            f"{round(self._tdr.get_collateralization_ratio() * 100, USDD_CR_DIGIT)}%"
        )

    def _usdd_cr_alert(self, context: CallbackContext):
        diff = (
            self._last_checked_usdd_cr_value - self._tdr.get_collateralization_ratio()
        )
        diff = round(diff, USDD_CR_DIGIT)
        # TODO: Calculate minus or plus
        if USDD_CR_THRESHOLD <= abs(diff):
            job = context.job
            context.bot.send_message(
                job.context,
                text="USDD CR Alert\n"
                + f"[{round(self._last_checked_usdd_cr_value*100, USDD_CR_DIGIT)}%] -> [{round(self._tdr.get_collateralization_ratio()*100, USDD_CR_DIGIT)}%]"
                + "\n"
                + f"{round(diff*100, USDD_CR_DIGIT)}%",
            )
            self._last_checked_usdd_cr_value = self._tdr.get_collateralization_ratio()

    def usdd_cr_alert_set(self, update: Update, context: CallbackContext):
        chat_id = update.message.chat_id
        job_removed = self.remove_job_if_exists(
            str(chat_id) + "_usdd_cr_alert_set", context
        )

        if job_removed:
            update.message.reply_text("USDD CR alert has been removed.")
        else:
            self._last_checked_risk_value = self._just.get_risk_value()
            context.job_queue.run_repeating(
                self._usdd_cr_alert,
                interval=60 * 30,
                context=chat_id,
                name=str(chat_id) + "_usdd_cr_alert_set",
            )
            update.message.reply_text("USDD CR alert has been set.")

    # Check actual USDD CR.
    def usdd_actual_cr_check(self, update: Update, context: CallbackContext):
        update.message.reply_text(f"{round(self._tdr.get_actual_cr() * 100)}%")

    def _usdd_actual_cr_alert(self, context: CallbackContext):
        if float(self._tdr.get_actual_cr()) < 1.00:
            job = context.job
            context.bot.send_message(
                job.context,
                text="USDD Actual CR Alert\n" + f"[{self._tdr.get_actual_cr() * 100}%]",
            )
            self._last_checked_usdd_cr_value = self._tdr.get_actual_cr()

    def usdd_actual_cr_alert_set(self, update: Update, context: CallbackContext):
        chat_id = update.message.chat_id
        job_removed = self.remove_job_if_exists(
            str(chat_id) + "_usdd_actual_cr_alert_set", context
        )

        if job_removed:
            update.message.reply_text("USDD Actual CR alert has been removed.")
        else:
            context.job_queue.run_repeating(
                self._usdd_actual_cr_alert,
                interval=60 * 30,
                context=chat_id,
                name=str(chat_id) + "_usdd_actual_cr_alert_set",
            )
            update.message.reply_text("USDD Actual CR alert has been set.")


if __name__ == "__main__":
    # Wallet Address
    bot = TeleBot(os.environ["ENV_JUSTALERT_ADDR"])

    # Telegram Bot Token
    updater = Updater(os.environ["ENV_JUSTALERT_TOKEN"])
    updater.dispatcher.add_handler(CommandHandler("start", bot.start))
    updater.dispatcher.add_handler(CommandHandler("help", bot.help))

    updater.dispatcher.add_handler(CommandHandler("risk_check", bot.risk_check))
    updater.dispatcher.add_handler(CommandHandler("risk_alert", bot.risk_alert_set))

    updater.dispatcher.add_handler(CommandHandler("usdd_cr_check", bot.usdd_cr_check))
    updater.dispatcher.add_handler(
        CommandHandler("usdd_cr_alert", bot.usdd_cr_alert_set)
    )

    updater.dispatcher.add_handler(
        CommandHandler("usdd_actual_cr_check", bot.usdd_actual_cr_check)
    )
    updater.dispatcher.add_handler(
        CommandHandler("usdd_actual_cr_alert", bot.usdd_actual_cr_alert_set)
    )

    updater.start_polling()

    while True:
        schedule.run_pending()
        time.sleep(1)
