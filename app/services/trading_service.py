import asyncio
import os
from collections import deque
from datetime import datetime, timedelta
from random import choice

import aiogram.utils.markdown as md
import aiohttp
import pandas as pd
import pytz
from dotenv import load_dotenv

from app.logs import log, logger
from app.models.models import TradingPair

env = os.environ.get
load_dotenv("./.env")

PROXY = env("PROXY")
HEADERS = {
    "user_agents": [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) "
        "AppleWebKit/538 (KHTML, like Gecko) Chrome/36 Safari/538",
        "Mozilla/5.0 (X11; Linux i686) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2599.0 Safari/537.36",
    ]
}


class PSAR:
    def __init__(self, init_af=0.03, max_af=0.1, af_step=0.00265):  # 0.03, 0.1, 00265
        self.max_af = max_af
        self.init_af = init_af
        self.af = init_af
        self.af_step = af_step
        self.extreme_point = None
        self.high_price_trend = []
        self.low_price_trend = []
        self.high_price_window = deque(maxlen=2)
        self.low_price_window = deque(maxlen=2)

        # Lists to track results
        self.psar_list = []
        self.af_list = []
        self.ep_list = []
        self.high_list = []
        self.low_list = []
        self.trend_list = []
        self._num_days = 0

    def calcPSAR(self, high, low):
        if self._num_days >= 3:
            psar = self._calcPSAR()
        else:
            psar = self._initPSARVals(high, low)

        psar = self._updateCurrentVals(psar, high, low)
        self._num_days += 1

        return psar

    def _initPSARVals(self, high, low):
        if len(self.low_price_window) <= 1:
            self.trend = None
            self.extreme_point = high
            return None

        if self.high_price_window[0] < self.high_price_window[1]:
            self.trend = 1
            psar = min(self.low_price_window)
            self.extreme_point = max(self.high_price_window)
        else:
            self.trend = 0
            psar = max(self.high_price_window)
            self.extreme_point = min(self.low_price_window)

        return psar

    def _calcPSAR(self):
        prev_psar = self.psar_list[-1]
        if self.trend == 1:  # Up
            psar = prev_psar + self.af * (self.extreme_point - prev_psar)
            psar = min(psar, min(self.low_price_window))
        else:
            psar = prev_psar - self.af * (prev_psar - self.extreme_point)
            psar = max(psar, max(self.high_price_window))

        return psar

    def _updateCurrentVals(self, psar, high, low):
        if self.trend == 1:
            self.high_price_trend.append(high)
        elif self.trend == 0:
            self.low_price_trend.append(low)

        psar = self._trendReversal(psar, high, low)

        self.psar_list.append(psar)
        self.af_list.append(self.af)
        self.ep_list.append(self.extreme_point)
        self.high_list.append(high)
        self.low_list.append(low)
        self.high_price_window.append(high)
        self.low_price_window.append(low)
        self.trend_list.append(self.trend)

        return psar

    def _handle_reversal(self, psar, high, low):
        reversal = False

        if self.trend == 1 and psar > low:
            self._handle_bullish_reversal(psar, low)
            reversal = True
        elif self.trend == 0 and psar < high:
            self._handle_bearish_reversal(psar, high)
            reversal = True

        return reversal

    def _handle_bullish_reversal(self, psar, low):
        self.trend = 0
        psar = max(self.high_price_trend)
        self.extreme_point = low

    def _handle_bearish_reversal(self, psar, high):
        self.trend = 1
        psar = min(self.low_price_trend)
        self.extreme_point = high

    def _update_af_and_extreme_point(self, high, low):
        if high > self.extreme_point and self.trend == 1:
            self.af = min(self.af + self.af_step, self.max_af)
            self.extreme_point = high
        elif low < self.extreme_point and self.trend == 0:
            self.af = min(self.af + self.af_step, self.max_af)
            self.extreme_point = low

    def _trendReversal(self, psar, high, low):
        reversal = self._handle_reversal(psar, high, low)

        if reversal:
            self.af = self.init_af
            self.high_price_trend.clear()
            self.low_price_trend.clear()
        else:
            self._update_af_and_extreme_point(high, low)

        return psar


@log(logger)
def rsi_index(dataframe, periods=14, ema=True):
    close_delta = dataframe["Close"].diff()

    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)

    if ema:
        # Use exponential moving average
        ma_up = up.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
        ma_down = down.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
    else:
        # Use simple moving average
        ma_up = up.rolling(window=periods, adjust=False).mean()
        ma_down = down.rolling(window=periods, adjust=False).mean()

    rsi = ma_up / ma_down
    rsi = 100 - (100 / (1 + rsi))
    return rsi


@log(logger)
async def get_pair_data(trading_pair: str = "ETHUSDT") -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.binance.com/api/v1/klines?symbol="
            f"{trading_pair.upper()}&interval=1m&limit=200",
            proxy=PROXY,
            headers={"user-agent": choice(HEADERS["user_agents"])} if HEADERS else {},
        ) as response:
            content = await response.json()
            return content


@log(logger)
async def get_prediction(dataset: list) -> str:
    #  minimum 200 values needed for prediction

    df = pd.DataFrame(
        dataset,
        columns=[
            "Timestamp(open)",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Timestamp(close)",
            "Quote",
            "NumberOfTrades",
            "TakerBuyBase",
            "TakerBuyQuote",
            "Ignore",
        ],
    )
    df = df.astype(
        {"Open": "float", "High": "float", "Low": "float", "Close": "float", "Volume": "float"}
    )

    arg = True
    rsi_diff_l = False
    rsi_diff_s = False
    rsi_indicator = False
    prev_rsi = 1
    pivot_bottom = 1
    pivot_top = 53
    spread_between_sma = bool()

    df["SMA9"] = df.Close.rolling(window=9).mean()
    df["SMA21"] = df.Close.rolling(window=21).mean()
    df["SMA200"] = df.Close.rolling(window=200).mean()
    psar = PSAR()
    df["PSAR"] = df.apply(lambda x: psar.calcPSAR(x["High"], x["Low"]), axis=1)
    df["RSI"] = rsi_index(df, periods=60)

    df = df.dropna()

    if 35 <= df.iloc[-1].RSI <= 43:
        if df.iloc[-1].RSI <= prev_rsi:
            pivot_bottom = df.iloc[-1].RSI
        rsi_indicator = True
    elif df.iloc[-1].RSI >= 53:
        if df.iloc[-1].RSI >= prev_rsi and df.iloc[-1].RSI >= pivot_top:
            pivot_top = df.iloc[-1].RSI
        rsi_indicator = False
    if (
        0.1 <= (100 - (df.iloc[-1].SMA9 / df.iloc[-1].SMA21) * 100) <= 0.2
        and (100 - (df.iloc[-1].SMA9 / df.iloc[-1].SMA200) * 100) >= 0.3
    ):
        spread_between_sma = True
    elif (100 - (df.iloc[-1].SMA9 / df.iloc[-1].SMA21) * 100) <= -0.3:
        spread_between_sma = False

    if (100 - (df.iloc[-1].RSI / pivot_top) * 100) >= 25:
        rsi_diff_l = True
    if ((df.iloc[-1].RSI / pivot_bottom) * 100 - 100) >= 35:
        rsi_diff_s = True
    prev_rsi = df.iloc[-1].RSI
    arg = df.iloc[-1].SMA9 <= df.iloc[-1].SMA21

    if (
        (df.iloc[-1].Close >= df.iloc[-1].SMA21)
        and (arg)
        and (rsi_indicator)
        and (spread_between_sma)
        and (rsi_diff_l)
        and (df.iloc[-1].Close >= df.iloc[-1].PSAR)
    ):
        return "buy"

    if (
        (df.iloc[-1].Close <= df.iloc[-1].SMA21)
        and (arg is False)
        and (rsi_indicator is False)
        and (rsi_diff_s is not None)
    ):
        return "sell"

    return "stay"


@log(logger)
async def announce(stats: dict, user_service, notify_bot):
    for user in await user_service.get_ready_users:
        if stats["percent_change"] >= user["percent"]:
            url = "https://www.binance.com/en/futures/"
            hbold = md.hbold("Trading Pair: ")
            await notify_bot.bot.send_message(
                user["id"],
                f"{hbold + md.hlink(stats['trading_pair'], url + stats['trading_pair'])}"
                + f"\n├Price: {md.hcode(stats['current']['price'])}"
                + f"\n├Prediction: {md.hitalic(stats['prediction'])}",
                parse_mode="html",
                disable_web_page_preview=True,
            )


@log(logger)
async def tracking_loop(user_service, notify_bot, trading_pair: str = "ETHUSDT"):
    last_record = await TradingPairService.get_last_pair(trading_pair)
    tz = pytz.timezone("Europe/Moscow")

    while 1:
        dataset = await get_pair_data(trading_pair)
        stats = {"trading_pair": trading_pair}
        stats["prediction"] = await get_prediction(dataset)
        stats["current"] = {
            "time": datetime.fromtimestamp(dataset[-1][0] // 1000, tz),
            "price": dataset[-1][4],
        }
        stats["hour_ago"] = {
            "time": datetime.fromtimestamp(dataset[-60][6] // 1000, tz),
            "price": dataset[-60][4],
        }

        stats["percent_change"] = (
            abs(
                round(
                    (float(stats["current"]["price"]) - float(stats["hour_ago"]["price"]))
                    / float(stats["current"]["price"]),
                    2,
                )
            )
            * 100
        )

        if stats["percent_change"] >= 1:
            if (not last_record) or (
                last_record["publication_date"] - stats["current"]["time"]
            ) >= timedelta(minutes=60):
                await TradingPairService.add_pair(trading_pair.lower(), stats["current"]["price"])
                last_record = await TradingPairService.get_last_pair(trading_pair)
                await announce(stats, user_service, notify_bot)

        print(stats)

        await asyncio.sleep(0.5)


class TradingPairService:
    def __init__(self) -> None:
        ...

    @classmethod
    @log(logger)
    async def get_last_pair(cls, trading_pair: str):
        pair_obj = (
            await TradingPair.filter(pair=trading_pair.lower()).order_by("-id").first().values()
        )
        return pair_obj

    @classmethod
    @log(logger)
    async def add_pair(cls, trading_pair: str, price: float):
        await TradingPair.create(pair=trading_pair, price=price)
        return 0
