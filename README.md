# Arbitrum liquidations and Chainlink SVR auctions

Liquidations on Arbitrum lending markets, 2026-11-08T00:00:00Z to 2026-11-16T00:00:00Z, measured by Fiftysix from its own Arbitrum node with an observation-only watcher that holds no keys. Analysis: fiftysix.tech/solver.

## At a glance

- 428 liquidations across 6 markets; 264 inside a Chainlink SVR auction
- 136 auctions, won by 13 solvers (the most active won 64%)
- winning bid as a share of the bonus the liquidations paid (121 fully priced auctions): p10 92%, median 97%, p90 101%
- bonus minus bid per auction, median $1.64, before gas and before the cost of selling the collateral
- auctions won after a higher bid failed on-chain: 2

## Files

- `auctions.csv`: one row per SVR auction transaction
- `liquidations.csv`: one row per liquidation event
- `markets.csv`: the markets watched, with their contract addresses
- `check_tx.py`: verify any row against an Arbitrum node (standard library only)

## Method

- **Liquidations** are the protocols' own liquidation events, read from the node.
- **Auctions** are Atlas `SolverTxResult` events in the same transaction. The winning bid is the successful solver operation's bid, paid in ETH. Losing bids usually do not land on-chain, so competition depth is not visible.
- **Prices.** Where the liquidation's own transaction carries a Chainlink update (every SVR auction does), the asset it prices is valued at that update's answer: the price the protocol itself used. Otherwise prices are taken at the block's time from the Chainlink feeds' round history (the node is pruned and cannot read old state; round history stays readable). In fast markets the public feed lagged the in-transaction update by up to about 1%. Tokens with no Chainlink feed fall back to Aave's oracle. Where no reliable price exists the value is left blank, never filled with a later price.
- **Realized bonus** is collateral seized minus debt repaid, at those prices, from the event's own amounts. On Aave the seized amount is already net of the protocol's liquidation fee. Measured for Aave and Morpho only.
- **Price updates** are detected from Chainlink's aggregator events, including the undocumented update event of its upgraded Arbitrum aggregators (topic `0x8d530b9d…`, one indexed round id).

## Known limits

- The bonus is valued at oracle prices. What a winner realizes depends on the price it sells the collateral at, which in fast markets differed from the oracle by roughly ±1.5% in this window.
- Rows under $100 of debt are kept but flagged `dust`.
- Coverage is the markets in `markets.csv`; other Arbitrum lenders are not included.
- The watcher restarted repeatedly on 8-9 November 2026. That affected how long positions were seen open, which is not in this dataset; liquidation and auction records were recovered from the chain's logs and receipts.

## Corrections

- Bids are priced at their own block time. An early version priced past bids at the current ETH price; corrected before this export.
- Each liquidation carries its own realized bonus. An early version gave every liquidation in a multi-liquidation transaction the first one's figures; corrected and back-filled before this export.
- SVR-bundled liquidations are priced at the Chainlink update inside their transaction. An early version used the public feed, which lagged it in fast markets; corrected and back-filled before this export.

## Licence and citation

CC BY 4.0 (creativecommons.org/licenses/by/4.0). Please cite as: Fiftysix, *Arbitrum liquidations and Chainlink SVR auctions*, 2026-11-08 to 2026-11-16.
