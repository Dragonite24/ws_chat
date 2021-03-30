import json
from twisted.internet import reactor, protocol
from twisted.internet.protocol import ServerFactory as SerFactory, connectionDone
from twisted.internet.endpoints import TCP4ServerEndpoint


# Создает наш сервер
# Фабрика - класс который хранит постоянную конфигурацию и создает серверы
# У каждого клиента есть собственный серверный протокол

# value, type

class Server(protocol.Protocol):
    def __init__(self, clients: dict, my_id):
        print("Init server")
        self.clients = clients
        self.my_id = my_id
        self.another_client = None

    def connectionMade(self):
        """ Вызывается при установлении соединения клиента"""
        self.clients[self.my_id] = self

    # Закодировать json
    @staticmethod
    def __encodeJson(**kwargs):
        """**kwargs - аргументы ключевого слова"""
        return json.dumps(kwargs)

    def sendMessage(self, **kwargs):
        """ Отправка сообщений """
        if kwargs.get('where'):
            where = kwargs['where']
            del kwargs['where']
            where.transport.write(self.__encodeJson(**kwargs).encode("utf-8"))
        else:
            self.transport.write(self.__encodeJson(**kwargs).encode("utf-8"))

    def dataReceived(self, data):
        # data - bytes
        # отправляем данные конкретному клиенту, который подключен к этому серверу
        print(data)
        try:
            # декодируем данные для отправки другому клиенту
            data = json.loads(data.decode("utf-8"))
        except UnicodeDecodeError:
            self.sendMessage(value="Не удалось декодировать, используйте utf-8", type="error")
            return
        except json.JSONDecodeError:
            self.sendMessage(value="Не удалось декодировать, используйте json", type="error")
            return

        if not data.get('type') or not data.get('value'):
            self.sendMessage(value=f"Неверные данные", type='error')
            return

        if data['type'] == "user_choose":
            try:
                another_client = int(data['value'])
                if another_client in self.clients.keys():
                    self.another_client = another_client
                else:
                    raise KeyError

            except ValueError:
                self.sendMessage(value="Напишите другой идентификатор (int)", type="error")
            except KeyError:
                self.sendMessage(value="Клиент не найден", type="error")

            else:
                self.sendMessage(value=f"Разговор с {self.another_client}", type='user_chosen')

        elif data['type'] == "new_message":
            if not self.anothertClient:
                self.sendMessage(value="У вас нет клиента, которому вы могли бы отправить свое сообщение", type="error")
            try:
                self.sendMessage(value=data['value'], where=self.clients[self.another_client], type="new_message")
            except KeyError:
                self.sendMessage(value="Что-то пошло не так, попробуйте выбрать другого клиента", type="error")
                self.another_client = None

    def disconnecting(self):
        del self.clients[self.my_id]

    def connectionLost(self, reason=connectionDone):
        self.disconnecting()


class ServerFactory(SerFactory):
    def __init__(self):
        print("Init factory")
        self.clients = {}
        self.last_id = 0

    def buildProtocol(self, addr):
        self.last_id += 1
        return Server(self.clients, self.last_id)


if __name__ == "__main__":
    # Если порт занят, попробуйте 12346
    endpoint = TCP4ServerEndpoint(reactor, 12345)

    # Слушаем входящие сообщения
    endpoint.listen(ServerFactory())
    reactor.run()  # @UndefinedVariable
