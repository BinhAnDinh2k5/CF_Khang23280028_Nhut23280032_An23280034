# execution.py
from typing import Dict, List, Tuple, Sequence, Optional
import math
from collections import deque
import numpy as np
import pandas as pd
from core import TradeEvent, BacktestConfig
from signals import compute_position_size, compute_priority_score


# Chọn cổ mua trong ngày dựa vào tín hiệu và ưu tiên
def select_stocks_to_buy(
    date: pd.Timestamp,
    universe_prices: Dict[str, pd.DataFrame],
    signals_today: Dict[str, Dict],
    cash: float,
    sma_params,
    atr_map: Optional[Dict[str, pd.Series]],
    config: BacktestConfig,
) -> List[Tuple[str, int]]:
    
    max_positions_per_day = config.max_positions_per_day
    sizing_method = config.sizing_method
    fraction = config.fraction
    fixed_amount = config.fixed_amount
    lot_size = config.lot_size
    max_pct_per_ticker = config.max_pct_per_ticker

    candidates = []

    for t, info in signals_today.items():
        if info.get("signal", 0) != 1:
            continue
        full = universe_prices[t]
        if date not in full.index:
            continue

        price = float(full.loc[date, "Open"])

        # lấy tham số SMA cho ticker (nếu là dict) hoặc tuple chung
        if isinstance(sma_params, dict):
            s_l = sma_params.get(t, None)
            if s_l is None:
                short_w, long_w = 10, 50
            else:
                short_w, long_w = int(s_l[0]), int(s_l[1])
        else:
            try:
                short_w, long_w = int(sma_params[0]), int(sma_params[1])
            except Exception:
                short_w, long_w = 10, 50
        
        # sắp xếp theo score giảm dần
        df_up_to_prev = full.loc[:date]
        if len(df_up_to_prev) < long_w:
            continue
        score = compute_priority_score(df_up_to_prev, short_w, long_w, remove_last= False)
        candidates.append((t, price, score))

    if not candidates:
        return []

    candidates.sort(key=lambda x: x[2], reverse=True)

    buy_orders = []
    remaining_cash = cash
    count = 0

    for t, price, score in candidates:
        if count >= max_positions_per_day:
            break
        atr = None
        if atr_map is not None and t in atr_map and date in atr_map[t].index:
            atr = float(atr_map[t].loc[date])

        shares = compute_position_size(cash=remaining_cash, price=price, config=config, atr=atr)
        if shares <= 0:
            continue

        try:
            max_allowed_value = float(remaining_cash) * float(max_pct_per_ticker)
        except Exception:
            max_allowed_value = float(remaining_cash) * 0.10
            

        if shares * price > max_allowed_value:
            max_shares = int(math.floor(max_allowed_value / price / max(1, lot_size)) * max(1, lot_size))
            if max_shares <= 0:
                continue
            shares = max_shares

        cost = shares * price
        if cost > remaining_cash:
            affordable_shares = int(math.floor(remaining_cash / price / max(1, lot_size)) * max(1, lot_size))
            if affordable_shares <= 0:
                continue
            shares = affordable_shares
            cost = shares * price

        if shares <= 0:
            continue

        buy_orders.append((t, shares))
        remaining_cash -= shares * price
        count += 1

    return buy_orders



# Chọn cổ bán: theo signal, stop loss / take profit, hoặc fraction
def select_stocks_to_sell(
    date: pd.Timestamp,
    universe_prices: Dict[str, pd.DataFrame],
    positions: Dict[str, float],
    price_map: Dict[str, float],
    signals_today: Dict[str, Dict],
    last_buy_price: Dict[str, List[Tuple[float, float]]],
    config: BacktestConfig,

)-> List[Tuple[str, int]]:

    stop_loss_pct = config.stop_loss_pct
    take_profit_pct = config.take_profit_pct
    sell_fraction_on_signal = config.sell_fraction_on_signal
    max_sells_per_day = config.max_sells_per_day
    lot = max(1, int(config.lot_size or 1))

    sells = []


    for t, held in positions.items():
        if held is None or held <= 0:
            continue
        price = price_map.get(t, None)
        if price is None or price <= 0 or np.isnan(price):
            continue

        sell_fraction = 0.0
        sig = signals_today.get(t, {}).get("signal", 0)

        if sig == -1:
            sell_fraction = float(sell_fraction_on_signal)
  
        # Kiểm tra stop-loss / take-profit 
        if (stop_loss_pct > 0 or take_profit_pct > 0):
            buy_p = last_buy_price.get(t, None)
            if buy_p is not None and buy_p > 0:
                change = (price - float(buy_p)) / float(buy_p)
                # Nếu vướt mức stop-loss / take-profit thì bán hết
                if stop_loss_pct > 0 and change <= -abs(stop_loss_pct):
                    sell_fraction = 1.0
                elif take_profit_pct > 0 and change >= abs(take_profit_pct):
                    sell_fraction = 1.0


        if sell_fraction <= 0:
            continue
            
        raw_shares = held * sell_fraction

        shares_to_sell = int(math.floor(raw_shares / lot) * lot)

        # nếu quá nhỏ → bán ít nhất 1 lot nếu còn >= 1 lot
        if shares_to_sell <= 0 and held >= lot:
            shares_to_sell = lot

        # nếu còn ít hơn lot thì bán hết phần còn lại ((một số broker cho phép bán < lot; nếu không, sẽ bị điều kiện khác xử lý))
        if shares_to_sell <= 0 and held < lot:
            shares_to_sell = int(held)

        if shares_to_sell > 0:
            sells.append((t, shares_to_sell))

    # giới hạn số giao dịch bán trong 1 ngày
    if max_sells_per_day is not None and max_sells_per_day > 0:
        sells = sells[:max_sells_per_day]

    return sells

# Thực thi danh sách lệnh mua/bán, cập nhật positions, cash và trả events
def execute_orders(
    orders: Sequence[Tuple[str, float]],
    price_map: Dict[str, float],
    positions: Dict[str, float],
    cash: float,
    date: pd.Timestamp,
    config: BacktestConfig,
    is_buy: bool = True,
) -> Tuple[Dict[str, float], float, List[TradeEvent]]:

    events: List[TradeEvent] = []
    fees_per_order = config.fees_per_order
    lot = max(1, config.lot_size)


    for ticker, shares in orders:
        price = price_map.get(ticker, None)
        if price is None or price <= 0 or np.isnan(price):
            continue

        

        if not is_buy:
            # Selling: cộng tiền về cash, trừ phí, giảm position
            held = positions.get(ticker, 0.0)
            sell_shares = shares
            sell_shares = min(shares, held)
            proceeds = sell_shares * price
            cash += proceeds
            cash -= fees_per_order
            positions[ticker] = held - sell_shares
            event = TradeEvent(pd.Timestamp(date), ticker, "SELL", float(price), float(sell_shares), float(cash))
            events.append(event)
        else:
            # Nếu đã có vị thế >0 không mua thêm
            if positions.get(ticker, 0.0) > 0:
                continue
            
            # Buying: kiểm tra đủ tiền, trừ cost và phí, tăng position
            buy_shares = shares
            cost = buy_shares * price
            if cost + fees_per_order > cash:
                affordable_shares = int(math.floor((cash - fees_per_order) / price / lot) * lot)
                if affordable_shares <= 0:
                    continue
                buy_shares = affordable_shares
                cost = buy_shares * price

            cash -= cost
            cash -= fees_per_order
            positions[ticker] = positions.get(ticker, 0.0) + buy_shares
            event = TradeEvent(pd.Timestamp(date), ticker, "BUY", float(price), float(buy_shares), float(cash))
            events.append(event)

    return positions, cash, events

