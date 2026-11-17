# Arbitrum liquidations and Chainlink SVR auctions, 8–15 November 2026

Every liquidation on eleven Arbitrum lending markets over one week, and every Chainlink Smart Value Recapture (SVR) auction among them, measured by [Fiftysix](https://fiftysix.tech) from its own Arbitrum node. The watcher that collected it only reads from the chain and holds no keys.

**Analysis:** [Who Keeps the Liquidation Bonus](https://fiftysix.tech/solver/aave-liquidation-bonus-arbitrum/), on what the auctions leave the liquidators who win them.

The window is 8 November 2026 00:00 UTC up to (not including) 16 November 2026 00:00 UTC.

## At a glance

- **428 liquidations** in 6 of the 11 markets watched. 264 of them happened inside a Chainlink SVR auction.
- **136 auctions**, won by 13 different solvers. The most active won 64% of them.
- **The winning bid takes almost the whole bonus.** Across the 121 auctions we could fully price, the winning bid was a median of 97% of the bonus the liquidations paid. One auction in ten was below 92%, and one in ten above 101%.
- **The winner keeps very little.** The bonus minus the bid was a median of $1.64 per auction, before gas and before the cost of selling the seized collateral.
- **A higher bid failed twice.** In 2 auctions, a higher bid landed on-chain but failed, and the next solver won with a lower bid.

## Files

| File | What it holds |
|---|---|
| `auctions.csv` | One row per SVR auction transaction (136 rows) |
| `liquidations.csv` | One row per liquidation event (428 rows) |
| `markets.csv` | The markets watched, with their contract addresses (12 rows; 11 watched) |
| `check_tx.py` | Checks any transaction against an Arbitrum node. Python 3, standard library only |
| `LICENSE` | CC BY 4.0 |
| `CITATION.cff` | How to cite this dataset |

Dollar values are in USD at the moment of the transaction (see Prices below). A blank value means no reliable price existed; blanks are never filled in with a later price.

### `auctions.csv`

| Column | Meaning |
|---|---|
| `tx_hash`, `block`, `time_utc` | The auction transaction, its block and its time (UTC) |
| `liquidations` | Number of liquidations in the transaction |
| `markets` | Market ids (see `markets.csv`) of those liquidations |
| `winning_solver` | Address of the solver whose operation succeeded |
| `bid_eth`, `bid_usd` | The winning bid, in ETH and in USD |
| `eth_usd` | The ETH price used to value the bid |
| `bonus_usd` | Total realized bonus of the transaction's liquidations (see Method) |
| `bid_share_of_bonus` | `bid_usd` ÷ `bonus_usd`. Blank when the bonus could not be fully priced |
| `solver_ops` | Number of Atlas solver operations recorded in the transaction |
| `higher_bid_failed` | 1 if a higher bid's operation ran and failed before the winner's succeeded |
| `top_failed_bid_eth` | That failed bid, in ETH |
| `oracle_update_in_tx` | 1 if the transaction carries a Chainlink price update |

### `liquidations.csv`

| Column | Meaning |
|---|---|
| `tx_hash`, `log_index`, `block`, `time_utc` | Where the liquidation event is on-chain, and when |
| `market`, `family` | Market id (see `markets.csv`) and the protocol event type |
| `debt_asset`, `debt_symbol`, `debt_repaid`, `debt_repaid_usd` | The debt token, its symbol, the amount repaid (in token units) and its USD value |
| `collateral_asset`, `collateral_symbol`, `collateral_seized`, `collateral_seized_usd` | The collateral token, its symbol, the amount seized (in token units) and its USD value |
| `realized_bonus_usd` | Collateral seized minus debt repaid, in USD (Aave and Morpho only; see Method) |
| `liquidator` | The liquidator address named in the event |
| `tx_to`, `tx_index` | The contract the transaction called, and the transaction's position in its block |
| `priority_fee_usd` | Priority fee the transaction paid, in USD |
| `in_auction` | 1 if the liquidation happened inside an SVR auction transaction |
| `oracle_update_in_tx` | 1 if the transaction carries a Chainlink price update |
| `flash_loan` | 1 if the transaction used a flash loan |
| `dust` | 1 if under $100 of debt was repaid. These rows are kept, only flagged |

## How to check a row

`check_tx.py` reads a transaction straight from an Arbitrum node, with no other code from us. For each hash it prints the status, block, time and recipient; every Atlas solver operation (its bid, and whether it ran and succeeded); the Chainlink update events; and every token transfer, summed per token, sender and receiver. It only reads, using `eth_getTransactionByHash`, `eth_getTransactionReceipt`, `eth_getBlockByNumber` and `eth_call`.

```
python3 check_tx.py 0x7ed7f7c130a5fc9d55007971d62b7325d264fe1116414ee3abf5e5a0187d8e53
RPC=https://your-arbitrum-rpc python3 check_tx.py <hash> <hash> ...
```

Pass full 66-character hashes. `RPC` defaults to `http://127.0.0.1:8547`, a local Arbitrum (Nitro) node.

## Method

- **Liquidations** are each protocol's own liquidation events, read from the node.
- **Auctions** are Atlas `SolverTxResult` events in the same transaction. The winning bid is the bid of the solver operation that succeeded, paid in ETH. Losing bids usually do not land on-chain, so how many solvers competed is not visible.
- **Prices.** When a liquidation's transaction carries a Chainlink price update (every SVR auction does), the asset it prices is valued at that update: the price the protocol itself used for the liquidation. Otherwise, prices come from the Chainlink feeds' round history at the block's time. The node is pruned and cannot read old state, but round history stays readable. In fast markets the public feed lagged the in-transaction update by up to about 1%. Tokens with no Chainlink feed fall back to Aave's oracle.
- **Realized bonus** is collateral seized minus debt repaid, at those prices, from the event's own amounts. On Aave the seized amount is already net of the protocol's liquidation fee. It is measured for Aave and Morpho only; for the other markets the column is blank. The Dolomite figure in the analysis comes from a separate estimate and is not in this dataset.
- **Price updates** are detected from Chainlink's aggregator events. That includes an undocumented update event emitted by Chainlink's upgraded Arbitrum aggregators (topic `0x8d530b9d…`, with one indexed round id).

## Known limits

- The bonus is valued at oracle prices. What a winner actually makes depends on the price it sells the collateral at, which in fast markets in this window differed from the oracle by roughly ±1.5%.
- Coverage is the markets in `markets.csv`. Other Arbitrum lenders are not included.
- The watcher restarted repeatedly on 8–9 November 2026. That affected how long positions were seen open, which is not part of this dataset. Every liquidation and auction from those days was recovered from the chain's logs and receipts.

## Corrections

Three errors were found and fixed before this export. All three made the opportunity look bigger than it was.

- **Bid prices.** An early version priced past bids at the current ETH price. Every bid is now priced at its own block time.
- **Multi-liquidation transactions.** An early version gave every liquidation in a transaction the first one's figures. Each liquidation now carries its own realized bonus, back-filled for all rows.
- **Collateral prices in auctions.** An early version valued SVR liquidations at the public Chainlink feed, which lagged in fast markets. They are now valued at the Chainlink update inside their own transaction, back-filled for all rows.

If you find another, please open an issue.

## Licence and citation

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): use it for anything, with credit. Please cite as:

> Fiftysix (2026). *Arbitrum liquidations and Chainlink SVR auctions, 8–15 November 2026.* https://github.com/fiftysixtech/arbitrum-liquidations-2026-11

GitHub's "Cite this repository" button gives the same in other formats.
