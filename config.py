server_configs = {
    'LosAngeles': [{'type': 'HTTP', 'url': 'http://google.com', 'interval': 5}],
    'London': [{'type': 'HTTPS', 'url': 'https://google.com', 'interval': 5}],
    'Brisbane': [{'type': 'ICMP', 'server': '8.8.8.8', 'interval': 5}],
    'NewYork': [{'type': 'DNS', 'server': '8.8.4.4', 'queries': [('google.com', 'A')], 'interval': 10}]
}
