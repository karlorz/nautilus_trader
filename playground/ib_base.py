# fmt: off

import asyncio
import traceback

from nautilus_trader.adapters.interactive_brokers.config import InteractiveBrokersDataClientConfig
from nautilus_trader.adapters.interactive_brokers.config import InteractiveBrokersExecClientConfig
from nautilus_trader.adapters.interactive_brokers.config import InteractiveBrokersInstrumentProviderConfig
from nautilus_trader.adapters.interactive_brokers.config import SymbologyMethod
from nautilus_trader.adapters.interactive_brokers.factories import InteractiveBrokersLiveDataClientFactory
from nautilus_trader.adapters.interactive_brokers.factories import InteractiveBrokersLiveExecClientFactory
from nautilus_trader.config import LiveDataEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import RoutingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.identifiers import InstrumentId
from playground.quickstart.strategies import MACDConfig

# from nautilus_trader.examples.strategies.subscribe import SubscribeStrategy
# from nautilus_trader.examples.strategies.subscribe import SubscribeStrategyConfig
from playground.quickstart.strategies import MACDStrategy


# fmt: on
async def main():
    instrument_provider = InteractiveBrokersInstrumentProviderConfig(
        symbology_method=SymbologyMethod.IB_SIMPLIFIED,
        load_ids=frozenset(
            [
                "EUR/USD.IDEALPRO",
                "BTC/USD.PAXOS",
                "SPY.ARCA",
                "AAPL.NASDAQ",
                "V.NYSE",
                "CLZ28.NYMEX",
                "ESZ28.CME",
            ],
        ),
    )

    # Configure the trading node

    config_node = TradingNodeConfig(
        trader_id="TESTER-001",
        logging=LoggingConfig(log_level="INFO"),
        data_clients={
            "IB": InteractiveBrokersDataClientConfig(
                ibg_host="10.10.1.10",
                ibg_port=4002,
                ibg_client_id=0,
                handle_revised_bars=False,
                use_regular_trading_hours=True,
                # market_data_type=IBMarketDataTypeEnum.DELAYED_FROZEN,  # If unset default is REALTIME
                instrument_provider=instrument_provider,
            ),
        },
        exec_clients={
            "IB": InteractiveBrokersExecClientConfig(
                ibg_host="10.10.1.10",
                ibg_port=4002,
                ibg_client_id=0,
                account_id="DU151042",  # This must match with the IB Gateway/TWS node is connecting to
                instrument_provider=instrument_provider,
                routing=RoutingConfig(
                    default=True,
                ),
            ),
        },
        data_engine=LiveDataEngineConfig(
            time_bars_timestamp_on_close=False,  # Will use opening time as `ts_event` (same like IB)
            validate_data_sequence=True,  # Will make sure DataEngine discards any Bars received out of sequence
        ),
        timeout_connection=90.0,
        timeout_reconciliation=10.0,
        timeout_portfolio=10.0,
        timeout_disconnection=10.0,
        timeout_post_stop=2.0,
    )

    # Instantiate the node with a configuration
    node = TradingNode(config=config_node)

    # Configure your strategy
    strategy_config = MACDConfig(
        instrument_id=InstrumentId.from_str("EUR/USD.IDEALPRO"),
        trade_ticks=False,
        quote_ticks=True,
        bars=True,
    )
    # Instantiate your strategy
    strategy = MACDStrategy(config=strategy_config)

    # Add your strategies and modules
    node.trader.add_strategy(strategy)

    # Register your client factories with the node (can take user-defined factories)
    node.add_data_client_factory("IB", InteractiveBrokersLiveDataClientFactory)
    node.add_exec_client_factory("IB", InteractiveBrokersLiveExecClientFactory)
    node.build()

    try:
        await node.run_async()
    except Exception as e:
        print(e)
        print(traceback.format_exc())
    finally:
        return node


# Stop and dispose of the node with SIGINT/CTRL+C
if __name__ == "__main__":
    node = asyncio.run(main())
    node.dispose()
