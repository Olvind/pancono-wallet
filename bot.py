from replit import db
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from replit import db

# ========================
# CONFIG
# ========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7194082974   # Replace with your Telegram ID

# ========================
# INIT WALLETS
# ========================
def init_wallets():
    if "owner_wallet" not in db:
        db["owner_wallet"] = {"balance": 2100000}
    if "treasury_wallet" not in db:
        db["treasury_wallet"] = {"balance": 1500000}
    if "reserved_wallets_setA" not in db:
        db["reserved_wallets_setA"] = {f"wallet_{i}": {"balance": 500} for i in range(1, 10001)}
    if "reserved_wallets_setB" not in db:
        db["reserved_wallets_setB"] = {f"wallet_{i}": {"balance": 12.8} for i in range(10001, 510001)}

init_wallets()

# ========================
# COMMANDS
# ========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Pancono Wallet!\n\n"
        "Commands:\n"
        "/import <wallet_id> – Import a wallet\n"
        "/balance – Check your wallet balance\n"
        "/send <wallet_id> <amount> – (Admin only) Send PANCA"
    )

async def import_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /import <wallet_id>")
        return

    wallet_id = context.args[0]
    db[f"user_{user_id}"] = wallet_id
    await update.message.reply_text(f"✅ Wallet {wallet_id} imported successfully!")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if f"user_{user_id}" not in db:
        await update.message.reply_text("⚠️ You don’t have a wallet imported.\nUse /import <wallet_id>.")
        return

    wallet_id = db[f"user_{user_id}"]

    # Look up balance
    if wallet_id in db["reserved_wallets_setA"]:
        bal = db["reserved_wallets_setA"][wallet_id]["balance"]
    elif wallet_id in db["reserved_wallets_setB"]:
        bal = db["reserved_wallets_setB"][wallet_id]["balance"]
    elif wallet_id in ["owner_wallet", "treasury_wallet"]:
        bal = db[wallet_id]["balance"]
    else:
        bal = None

    if bal is None:
        await update.message.reply_text("❌ Wallet not found.")
    else:
        await update.message.reply_text(f"💰 Wallet {wallet_id} Balance: {bal} PANCA")

async def send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id
    if sender_id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized. Admin only.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /send <wallet_id> <amount>")
        return

    to_wallet = context.args[0]
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Amount must be a number.")
        return

    treasury = db["treasury_wallet"]
    if treasury["balance"] < amount:
        await update.message.reply_text("❌ Not enough balance in Treasury.")
        return

    # Deduct from Treasury
    treasury["balance"] -= amount
    db["treasury_wallet"] = treasury

    # Add to target wallet
    if to_wallet in db["reserved_wallets_setA"]:
        db["reserved_wallets_setA"][to_wallet]["balance"] += amount
    elif to_wallet in db["reserved_wallets_setB"]:
        db["reserved_wallets_setB"][to_wallet]["balance"] += amount
    else:
        await update.message.reply_text("❌ Target wallet not found.")
        return

    await update.message.reply_text(f"✅ Sent {amount} PANCA to {to_wallet}.")

# ========================
# MAIN APP
# ========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("import", import_wallet))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("send", send))

    app.run_polling()

if __name__ == "__main__":
    main()
