from ccxt import exchanges

# print all available exchanges as django textchoice
for exchange in exchanges:
    print('{0} = "{1}"'.format(exchange.upper(), exchange))
