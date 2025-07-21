import discord
from discord.ext import tasks, commands
import aiohttp
from datetime import datetime

# ====== 你的設定 ======
TOKEN = "你的 Discord Bot Token"       # ⚠️ 換成你的 Bot Token
CHANNEL_ID = 1234567890                # ⚠️ 換成你的頻道 ID (整數)
CG_KEY = "你的 CoinGlass API Key"      # ⚠️ 換成你的 CoinGlass API Key

CG_API = "https://open-api-v4.coinglass.com/api"
HEADERS = {"coinglass-secret": CG_KEY}

# ====== Intents 修正 ======
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ====== 抓取 ETF 與價格 ======
async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            return await response.json()

async def get_etf_flow(symbol):
    url = f"{CG_API}/etf/{symbol}/flow-history?limit=1"
    data = await fetch_json(url)
    rec = data["data"][0]
    return rec["change_usd"], rec["price"]

async def get_price_change():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
    return {
        "BTC": (data["bitcoin"]["usd"], data["bitcoin"]["usd_24h_change"]),
        "ETH": (data["ethereum"]["usd"], data["ethereum"]["usd_24h_change"])
    }

async def send_report():
    btc_flow, btc_etf_price = await get_etf_flow("bitcoin")
    eth_flow, eth_etf_price = await get_etf_flow("ethereum")
    prices = await get_price_change()

    now = datetime.now().strftime("%Y-%m-%d")
    msg = (
        f"📊 **ETF 資金速報 ({now})**\n\n"
        f"🪙 **BTC 現貨 ETF**\n"
        f"◆ 單日淨流入：${btc_flow/1e6:,.2f}M\n"
        f"◆ ETF 價格：${btc_etf_price:,.2f}\n"
        f"◆ 現貨價格：${prices['BTC'][0]:,.2f} (24h {prices['BTC'][1]:.2f}%)\n\n"
        f"🪙 **ETH 現貨 ETF**\n"
        f"◆ 單日淨流入：${eth_flow/1e6:,.2f}M\n"
        f"◆ ETF 價格：${eth_etf_price:,.2f}\n"
        f"◆ 現貨價格：${prices['ETH'][0]:,.2f} (24h {prices['ETH'][1]:.2f}%)\n\n"
        f"📌 市場情緒參考用，謹慎投資。"
    )

    ch = bot.get_channel(CHANNEL_ID)
    await ch.send(msg)

    if abs(prices['BTC'][1]) > 1.5:
        await ch.send(f"🚨 **BTC 價格波動超過 1.5% ({prices['BTC'][1]:.2f}%)**")
    if abs(prices['ETH'][1]) > 1.5:
        await ch.send(f"🚨 **ETH 價格波動超過 1.5% ({prices['ETH'][1]:.2f}%)**")

# ====== 測試指令 ======
@bot.command()
async def test(ctx):
    await ctx.send("✅ Bot 正常運作！")

# ====== 定時任務 ======
@tasks.loop(minutes=1)
async def scheduled_task():
    now = datetime.now()
    if now.hour == 8 and now.minute == 30:
        await send_report()

@bot.event
async def on_ready():
    print(f"✅ 已登入 {bot.user}")
    scheduled_task.start()

# ====== 啟動 Bot ======
if __name__ == "__main__":
    try:
        print("🚀 嘗試啟動機器人...")
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ 機器人啟動失敗，錯誤原因：{e}")
