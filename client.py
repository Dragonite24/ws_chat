import json
from twisted.internet import reactor, protocol
from twisted.internet.protocol import ReconnectingClientFactory as ClientFact
from twisted.internet.endpoints import TCP4ClientEndpoint

from sys import stderr


# Фабрика (класс который хранит постоянную конфигурацию и создает серверы)
# У каждого клиента есть собственный серверный протокол

class Client(protocol.Protocol):
    def __init__(self):
        print("Клиент создан")
        reactor.callInThread(self.messageInput)

    @staticmethod
    def __encodeJson(**kwargs):
        """**kwargs - аргументы ключевого слова"""
        return json.dumps(kwargs)

    def sendMessage(self, **kwargs):
        self.transport.write(self.__encodeJson(**kwargs).encode("utf-8"))

    def messageInput(self):
        while True:
            self.sendMessage(value=input("value: "), type=input("type: "))

    def dataReceived(self, data):
        try:
            data = json.loads(data.decode("utf-8"))
        except UnicodeDecodeError or json.JSONDecodeError:
            print('Что-то пошло не так :(', file=stderr)
            return

        if data['type'] == 'error':
            print(data.get('value', "Неизвестная ошибка"), file=stderr)
        else:
            print(data.get('value', "В сообщении нет значения (value)"))


class ClientFactory(ClientFact):

    def buildProtocol(self, addr):
        return Client()

    def clientConnectionLost(self, connector, unused_reason):
        self.retry(connector)

    def clientConnectionFailed(self, connector, reason):
        print(reason)
        self.retry(connector)


if __name__ == '__main__':
    endpoint = TCP4ClientEndpoint(reactor, 'localhost', 12345)
    # Подключаемся как клиент
    endpoint.connect(ClientFactory())
    reactor.run()
