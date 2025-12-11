# Trading system

Trading engine built on python (multiprocessing) + redis deployed on AWS using github actions

## Table of Contents

- [Trading system](#trading-system)
  - [Table of Contents](#table-of-contents)
  - [About](#about)
  - [Features](#features)

## About

Trading engine to automate transactions on trading platforms (mainly cryptos -kraken, binance…- but extensible to equities) based on live markets fluctuations

- Tech stack:
  - python
  - redis
  - docker

## Features

- track markets fluctuations
- trigger transactions (buy/sell/short sell) depending on given criteria