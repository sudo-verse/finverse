from .nse_client import NSEClient

client = NSEClient()


def get_stock_price(ticker):
    
   

    return client.get_price(ticker)
