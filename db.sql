CREATE TABLE `intervals_timeouts` (
  `key` varchar(255) PRIMARY KEY,
  `value` longtext
)

CREATE TABLE `trade` (
  `key` varchar(255) PRIMARY KEY,
  `value` longtext
)

CREATE TABLE `txns` (
  `id` varchar(255) PRIMARY KEY,
  `data` json NOT NULL,
  `item_id` varchar(255) NOT NULL,
  `buyer` varchar(255) NOT NULL
)

CREATE TABLE `user_trade` (
  `key` varchar(255) PRIMARY KEY,
  `value` longtext
)

CREATE TABLE `lockmanager` (
  `key` varchar(255) PRIMARY KEY,
  `value` longtext
)
CREATE TABLE items (
  id VARCHAR(255) PRIMARY KEY,
  data JSON NOT NULL,
  seller VARCHAR(255) NOT NULL,
  tags VARCHAR(255)
);

CREATE TABLE `wallets` (
  `key` varchar(255) PRIMARY KEY,
  `value` longtext
)

CREATE TABLE `wallet_checker_queue` (
  `key` varchar(255) PRIMARY KEY,
  `value` longtext
)



                            


