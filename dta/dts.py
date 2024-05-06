import hashlib
import time
import json
import random
import string
import os
from collections import OrderedDict

class Transaction:
    def __init__(self, sender, receiver, amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = time.time()
        self.signature = None

    def calculate_hash(self):
        transaction_details = str(self.sender) + str(self.receiver) + str(self.amount) + str(self.timestamp)
        return hashlib.sha256(transaction_details.encode()).hexdigest()

    def sign_transaction(self, private_key):
        transaction_details = OrderedDict({"sender": self.sender, "receiver": self.receiver, "amount": self.amount, "timestamp": self.timestamp})
        transaction_details = json.dumps(transaction_details, indent=4, separators=(',', ':')).encode()
        self.signature = hashlib.sha256(transaction_details + private_key.encode()).hexdigest()

    def verify_signature(self):
        if self.sender == "Genesis":
            return True
        transaction_details = OrderedDict({"sender": self.sender, "receiver": self.receiver, "amount": self.amount, "timestamp": self.timestamp})
        transaction_details = json.dumps(transaction_details, indent=4, separators=(',', ':')).encode()
        return self.signature == hashlib.sha256(transaction_details + self.sender.encode()).hexdigest()

class Block:
    def __init__(self, transactions, previous_hash):
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = time.time()
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_details = str(self.transactions) + str(self.previous_hash) + str(self.timestamp) + str(self.nonce)
        return hashlib.sha256(block_details.encode()).hexdigest()

    def mine_block(self, difficulty):
        while self.hash[:difficulty] != '0' * difficulty:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print("Блок найден:", self.hash)

class Blockchain:
    def __init__(self):
        self.chain = []
        self.difficulty = 2
        self.pending_transactions = []
        self.mining_reward = 1
        self.addresses = {}

    def create_genesis_block(self):
        return Block(transactions=[], previous_hash='0')

    def add_block(self, block):
        self.chain.append(block)

    def get_latest_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        if transaction.sender != "Genesis":
            self.pending_transactions.append(transaction)
        else:
            return "Неверная транзакция!"

    def mine_pending_transactions(self, miner_reward_address):
        reward_transaction = Transaction("Genesis", miner_reward_address, self.mining_reward)
        self.pending_transactions.append(reward_transaction)
        new_block = Block(self.pending_transactions, self.get_latest_block().hash)
        new_block.mine_block(self.difficulty)
        self.add_block(new_block)
        self.pending_transactions = []

    def is_transaction_valid(self, transaction):
        if transaction.sender == "Genesis":
            return True
        if transaction.amount <= 0:
            return False
        if not transaction.verify_signature():
            return False
        sender_balance = self.get_balance(transaction.sender)
        return sender_balance >= transaction.amount

    def confirm_transaction(self, transaction):
        transaction_confirmed = False
        for block in self.chain:
            if transaction in block.transactions:
                transaction_confirmed = True
                break
        return transaction_confirmed

    def find_transactions_for_address(self, address):
        transactions = []
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.sender == address or transaction.receiver == address:
                    transactions.append(transaction)
        return transactions

    def get_balance(self, address):
        balance = 0
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.sender == address:
                    balance -= transaction.amount
                if transaction.receiver == address:
                    balance += transaction.amount
        return balance

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    def get_all_addresses_and_balances(self):
        addresses_balances = {}
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.sender not in addresses_balances:
                    addresses_balances[transaction.sender] = 0
                if transaction.receiver not in addresses_balances:
                    addresses_balances[transaction.receiver] = 0
                addresses_balances[transaction.sender] -= transaction.amount
                addresses_balances[transaction.receiver] += transaction.amount
        return addresses_balances

    def is_empty(self):
        return len(self.chain) == 0

    def generate_address(self):
        alphabet = string.ascii_letters + string.digits + "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        address = ''.join(random.choice(alphabet) for i in range(10))
        private_key = ''.join(random.choice(alphabet) for i in range(20))
        self.addresses[address] = private_key
        return address, private_key

    def is_valid_private_key(self, private_key):
        return len(private_key) == 20 and all(c in string.ascii_letters + string.digits + "абвгдеёжзийклмнопрстуфхцчшщъыьэюя" for c in private_key)

    def save_blockchain(self, filename):
        with open(filename, 'w') as file:
            blockchain_data = {
                "chain": [[block.transactions, block.previous_hash, block.timestamp, block.nonce, block.hash] for block in self.chain],
                "difficulty": self.difficulty,
                "pending_transactions": [[transaction.sender, transaction.receiver, transaction.amount, transaction.timestamp, transaction.signature] for transaction in self.pending_transactions],
                "mining_reward": self.mining_reward,
                "addresses": self.addresses
            }
            json.dump(blockchain_data, file, indent=4)

    def load_blockchain(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                blockchain_data = json.load(file)
                self.chain = [Block(transactions, previous_hash) for transactions, previous_hash, _, _, _ in blockchain_data["chain"]]
                self.difficulty = blockchain_data["difficulty"]
                self.pending_transactions = [Transaction(sender, receiver, amount) for sender, receiver, amount, _, _ in blockchain_data["pending_transactions"]]
                self.mining_reward = blockchain_data["mining_reward"]
                self.addresses = blockchain_data["addresses"]

class UserInterface:
    def __init__(self, blockchain):
        self.blockchain = blockchain

    def main_menu(self):
        while True:
            print("1. Добавить транзакцию")
            print("2. Добыть ожидающие транзакции")
            print("3. Показать блокчейн")
            print("4. Проверить баланс")
            print("5. Сгенерировать новый адрес")
            print("6. Показать все адреса и балансы")
            print("7. Отправить криптовалюту")
            print("8. Сохранить блокчейн в файл")
            print("9. Загрузить блокчейн из файла")
            choice = input("Введите ваш выбор: ")
            if choice == "1":
                self.add_transaction_menu()
            elif choice == "2":
                self.mine_pending_transactions_menu()
            elif choice == "3":
                self.display_blockchain_menu()
            elif choice == "4":
                self.check_balance_menu()
            elif choice == "5":
                self.generate_address_menu()
            elif choice == "6":
                self.display_all_addresses_and_balances_menu()
            elif choice == "7":
                self.send_crypto_menu()
            elif choice == "8":
                self.save_blockchain_menu()
            elif choice == "9":
                self.load_blockchain_menu()

    def add_transaction_menu(self):
        sender = input("Введите адрес отправителя: ")
        receiver = input("Введите адрес получателя: ")
        amount = float(input("Введите сумму: "))
        private_key = input("Введите приватный ключ отправителя: ")
        if not self.blockchain.is_valid_private_key(private_key):
            print("Неверный приватный ключ!")
            return
        transaction = Transaction(sender, receiver, amount)
        transaction.sign_transaction(private_key)
        if self.blockchain.is_transaction_valid(transaction):
            self.blockchain.add_transaction(transaction)
            print("Транзакция успешно добавлена!")
        else:
            print("Неверная транзакция!")

    def mine_pending_transactions_menu(self):
        miner_reward_address = input("Введите адрес для награды майнера: ")
        self.blockchain.mine_pending_transactions(miner_reward_address)
        print("Ожидающие транзакции успешно добыты!")

    def display_blockchain_menu(self):
        for block in self.blockchain.chain:
            print(block.__dict__)
            print("-" * 30)

    def check_balance_menu(self):
        address = input("Введите адрес для проверки баланса: ")
        balance = self.blockchain.get_balance(address)
        print(f"Баланс адреса {address}: {balance}")

    def generate_address_menu(self):
        address, private_key = self.blockchain.generate_address()
        print(f"Сгенерирован новый адрес: {address}")
        print(f"Соответствующий приватный ключ: {private_key}")

    def display_all_addresses_and_balances_menu(self):
        addresses_balances = self.blockchain.get_all_addresses_and_balances()
        for address, balance in addresses_balances.items():
            print(f"Адрес: {address}, Баланс: {balance}")

    def send_crypto_menu(self):
        sender = input("Введите адрес отправителя: ")
        private_key = input("Введите приватный ключ отправителя: ")
        receiver = input("Введите адрес получателя: ")
        amount = float(input("Введите сумму: "))
        if not self.blockchain.is_valid_private_key(private_key):
            print("Неверный приватный ключ!")
            return
        transaction = Transaction(sender, receiver, amount)
        transaction.sign_transaction(private_key)
        if self.blockchain.is_transaction_valid(transaction):
            self.blockchain.add_transaction(transaction)
            print("Транзакция успешно добавлена!")
            self.blockchain.mine_pending_transactions(sender)
            print("Ожидающие транзакции успешно добыты!")
        else:
            print("Неверная транзакция!")

    def save_blockchain_menu(self):
        filename = input("Введите имя файла для сохранения блокчейна: ")
        self.blockchain.save_blockchain(filename)
        print("Блокчейн успешно сохранен в файле!")

    def load_blockchain_menu(self):
        filename = input("Введите имя файла для загрузки блокчейна: ")
        self.blockchain.load_blockchain(filename)
        print("Блокчейн успешно загружен из файла!")

if __name__ == "__main__":
    blockchain = Blockchain()
    if blockchain.is_empty():
        genesis_block = blockchain.create_genesis_block()
        blockchain.add_block(genesis_block)
    ui = UserInterface(blockchain)
    ui.main_menu()