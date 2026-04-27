# Cardano 101: A Beginner's Guide

## Executive Summary

Cardano is a third-generation, proof-of-stake blockchain platform founded in 2015 by Charles Hoskinson and distinguished by a research-first development philosophy: every protocol decision is grounded in peer-reviewed academic research before implementation. Its consensus mechanism, Ouroboros — the first formally proven secure proof-of-stake protocol — was published at leading academic venues before a single line of mainnet code shipped. ADA, Cardano's native currency, serves as the medium for transaction fees, staking rewards, and on-chain governance participation; it is divisible into one million lovelace units. As of 2026, the network has processed over 120 million transactions [29](https://cardano.org/insights/).

The ecosystem has grown from a research project into a live economic platform supporting 123 curated applications across DeFi, NFTs, governance tools, block explorers, and wallets [31](https://cardano.org/apps/). Staking on Cardano is natively liquid — ADA never leaves the holder's wallet, there is no lock-up period, and there is no slashing risk, a significant design distinction from other proof-of-stake platforms [28](https://cardano.org/stake-pool-delegation/). The Voltaire governance era, enabled by CIP-1694, gives any ADA holder direct influence over the network's future through Delegated Representatives (DReps), the Constitutional Committee, and Stake Pool Operators [26](https://cardano.org/research/).

Safety is a first-class concern for participants. Non-custodial wallets mean users retain sole custody of their assets — no company can freeze or recover funds [25](https://cardano.org/common-scams/). Common scams follow identifiable patterns (giveaway frauds, phishing sites, fake support impersonation, rug pulls), and prepared users can recognize and avoid them. This guide covers all seven curriculum areas — Introduction, Wallets, Staking, Ecosystem, Governance, Safety, and Next Steps — at a level accessible to readers with no prior blockchain experience.

## Table of Contents

- [Chapter 1: Introduction to Blockchain and Cardano](#chapter-1-introduction-to-blockchain-and-cardano)
  - [What Is a Blockchain?](#what-is-a-blockchain)
  - [What Is Cardano?](#what-is-cardano)
  - [Founding History and the Three Entities](#founding-history-and-the-three-entities)
  - [The Ouroboros Protocol: Proof of Stake Without Energy Waste](#the-ouroboros-protocol-proof-of-stake-without-energy-waste)
  - [ADA: Cardano's Native Currency](#ada-cardanos-native-currency)
  - [Why Cardano Matters: Financial Inclusion and Sustainability](#why-cardano-matters-financial-inclusion-and-sustainability)
  - [Cardano's Research-Driven Foundation](#cardanos-research-driven-foundation)
  - [The Cardano Foundation and Enterprise Adoption](#the-cardano-foundation-and-enterprise-adoption)
- [Chapter 2: Cardano Wallets](#chapter-2-cardano-wallets)
  - [What Is a Cardano Wallet?](#what-is-a-cardano-wallet)
  - [Key Cardano Wallets](#key-cardano-wallets)
  - [How to Choose a Wallet](#how-to-choose-a-wallet)
  - [Setting Up a Wallet: Key Concepts](#setting-up-a-wallet-key-concepts)
- [Chapter 3: Staking on Cardano](#chapter-3-staking-on-cardano)
  - [What Is Stake?](#what-is-stake)
  - [How Ouroboros Proof-of-Stake Works](#how-ouroboros-proof-of-stake-works)
  - [Stake Pools and Stake Pool Operators](#stake-pools-and-stake-pool-operators)
  - [Delegation](#delegation)
  - [Rewards Calculation](#rewards-calculation)
  - [No Lock-Up: Liquid Native Staking](#no-lock-up-liquid-native-staking)
  - [Stake Pool Saturation](#stake-pool-saturation)
  - [How to Choose a Stake Pool](#how-to-choose-a-stake-pool)
- [Chapter 4: The Cardano Ecosystem](#chapter-4-the-cardano-ecosystem)
  - [Overview: A Growing On-Chain Economy](#overview-a-growing-on-chain-economy)
  - [ADA: Obtaining and Using the Currency](#ada-obtaining-and-using-the-currency)
  - [The eUTXO Model: A Beginner Introduction](#the-eutxo-model-a-beginner-introduction)
  - [Decentralized Exchanges and DeFi](#decentralized-exchanges-and-defi)
  - [NFTs and Digital Marketplaces](#nfts-and-digital-marketplaces)
  - [Stablecoins, Oracles, and Bridges](#stablecoins-oracles-and-bridges)
  - [Block Explorers and Analytics Tools](#block-explorers-and-analytics-tools)
  - [DApps, Tools, and Community Platforms](#dapps-tools-and-community-platforms)
  - [Developer Tools and Builder Infrastructure](#developer-tools-and-builder-infrastructure)
  - [The Cardano Improvement Proposal (CIP) Process](#the-cardano-improvement-proposal-cip-process)
  - [Enterprise Adoption: Cardano Foundation Solutions](#enterprise-adoption-cardano-foundation-solutions)
- [Chapter 5: Cardano Governance](#chapter-5-cardano-governance)
  - [Development Eras: Byron to Voltaire](#development-eras-byron-to-voltaire)
  - [Cardano Improvement Proposals (CIPs)](#cardano-improvement-proposals-cips)
  - [Voltaire: On-Chain Governance](#voltaire-on-chain-governance)
  - [The Cardano Constitution](#the-cardano-constitution)
  - [Governance Tools and Infrastructure](#governance-tools-and-infrastructure)
  - [Beyond MVG: Continued Governance Evolution](#beyond-mvg-continued-governance-evolution)
- [Chapter 6: Safety and Security](#chapter-6-safety-and-security)
  - [The Absolute Rule: Seed Phrase Protection](#the-absolute-rule-seed-phrase-protection)
  - [Common Scam Types](#common-scam-types)
  - [Safe Practices Summary](#safe-practices-summary)
  - [Verifying Wallet Authenticity](#verifying-wallet-authenticity)
- [Chapter 7: Next Steps and Community Resources](#chapter-7-next-steps-and-community-resources)
  - [Official Documentation: The Cardano Docs Portal](#official-documentation-the-cardano-docs-portal)
  - [Community Channels: Where to Connect](#community-channels-where-to-connect)
  - [The Ambassador Program](#the-ambassador-program)
  - [Community Code of Conduct](#community-code-of-conduct)
  - [Essential Cardano and IOG Content Hub](#essential-cardano-and-iog-content-hub)
- [Sources](#sources)

## Chapter 1: Introduction to Blockchain and Cardano

### What Is a Blockchain?

A blockchain is a shared, tamper-resistant digital ledger that records transactions across a network of computers. Unlike a traditional database controlled by a single company or government, a blockchain is maintained by many independent participants simultaneously — no single party can alter the record unilaterally.

The core insight is simple: when many nodes each hold an identical copy of every transaction, and each new batch of transactions (a "block") is cryptographically linked to the one before it (forming a "chain"), changing any historical entry would require redoing all subsequent work across a majority of the network — making fraud computationally impractical.

Early blockchains such as Bitcoin proved the concept but operated on a "Proof of Work" (PoW) model, in which participants compete to solve energy-intensive mathematical puzzles to win the right to add the next block. This approach is secure but consumes enormous electricity and limits the number of transactions the network can process [77](https://eprint.iacr.org/2016/889.pdf).

Cardano belongs to a third generation of blockchain platforms that replace Proof of Work with Proof of Stake — a mechanism in which participants are selected to add blocks in proportion to the amount of the native currency they hold or have had delegated to them, removing the need for energy-intensive computation.

### What Is Cardano?

Cardano is a decentralized, third-generation proof-of-stake blockchain platform and the home of the ADA cryptocurrency [18](https://docs.cardano.org/about-cardano/introduction).

Three qualities distinguish Cardano from earlier blockchain projects:

| Quality | What It Means |
|---|---|
| Research-first | Every protocol decision is grounded in peer-reviewed academic research published in collaboration with universities [26](https://cardano.org/research/) |
| Formal methods | Core software is written in Haskell, a language that supports mathematical proof of program correctness — reducing the chance of undiscovered bugs [18](https://docs.cardano.org/about-cardano/introduction) |
| Layered architecture | Value accounting (the Settlement Layer) and smart-contract execution (the Computation Layer) are separated, enabling each to be upgraded independently [78](https://resources.cryptocompare.com/asset-management/12/1741690659365.pdf) |

Cardano is described as "the first blockchain platform to evolve out of a scientific philosophy and a research-first driven approach" — rather than copying earlier platforms and iterating informally, its architects commissioned academic research, put it through peer review, and only then implemented it in software.

### Founding History and the Three Entities

The Cardano project began in 2015, led by Charles Hoskinson — one of the original co-founders of Ethereum — through his company IOHK (Input Output Hong Kong), which later rebranded as Input Output Global (IOG) [78](https://resources.cryptocompare.com/asset-management/12/1741690659365.pdf).

From the beginning, responsibility for the ecosystem was distributed across three distinct organizations to prevent over-centralization [21](https://cardano.org/):

| Entity | Role |
|---|---|
| Input Output / IOG | Research and protocol engineering — designs and implements the core technology |
| Cardano Foundation | Standards, advocacy, and adoption — acts as the neutral custodian and promotes Cardano to regulators, enterprises, and the public |
| EMURGO | Commercial adoption — invests in and builds products that drive real-world use of the blockchain |

Since the initial design, two further organizations have joined the ecosystem. **Intersect** is a member-based organization that coordinates community governance and stewards the project's long-term roadmap under the Voltaire era of decentralized self-governance. **PRAGMA** is an open-source software association supporting sustainable development of Cardano-related software. Both are listed as founding ecosystem partners on the Cardano homepage [21](https://cardano.org/).

### The Ouroboros Protocol: Proof of Stake Without Energy Waste

Cardano's consensus mechanism — the algorithm by which network participants agree on which transactions are valid and in what order — is called Ouroboros. It is described as "the first peer-reviewed, verifiably-secure blockchain protocol" based on Proof of Stake [21](https://cardano.org/).

Ouroboros was designed by Professor Aggelos Kiayias and colleagues from five academic institutions (the University of Edinburgh, University of Connecticut, Aarhus University, Tokyo Institute of Technology, and the University of Athens) and published as a peer-reviewed paper [77](https://eprint.iacr.org/2016/889.pdf).

The practical implications for a beginner are:

- **No mining rigs required.** Block producers are chosen based on stake held — not computational power expended — so anyone can participate in securing the network without specialised hardware [77](https://eprint.iacr.org/2016/889.pdf).
- **Provably secure.** Unlike earlier PoS designs that lacked formal security arguments, Ouroboros comes with a mathematical proof that honest participants are incentivized to behave correctly [77](https://eprint.iacr.org/2016/889.pdf).
- **Energy efficient.** The elimination of competitive mining dramatically reduces Cardano's electricity footprint compared to Bitcoin-style networks.

Time on the Cardano network is divided into **epochs** (approximately five days each), which are subdivided into **slots** (one second each). One slot leader is selected per slot to produce a block, with the probability of selection proportional to their stake [26](https://cardano.org/research/). (For how this applies to staking rewards, see [Chapter 3: Staking on Cardano](#chapter-3-staking-on-cardano).)

### ADA: Cardano's Native Currency

ADA is the native cryptocurrency of the Cardano blockchain, serving three primary roles [22](https://cardano.org/what-is-ada/):

- **Transaction fees.** Every operation on the blockchain (sending funds, executing a smart contract, minting a token) requires a small fee paid in ADA.
- **Staking and governance.** ADA holders can delegate their stake to a stake pool to earn rewards, or use their ADA to vote in Cardano's on-chain governance system.
- **Unit of value.** ADA is divisible into one million units called **lovelace**, named after computing pioneer Ada Lovelace, who inspired the currency's name.

ADA is held in wallets. A Cardano wallet is described as a "personal interface to the blockchain, much like a web browser is your interface to the internet" [23](https://cardano.org/get-started/). Crucially, Cardano wallets are non-custodial: no company holds your funds on your behalf, and there is no central service that can freeze or recover your assets. This means the holder is solely responsible for safeguarding their wallet's recovery phrase. (See [Chapter 2: Cardano Wallets](#chapter-2-cardano-wallets) for wallet setup details and [Chapter 6: Safety and Security](#chapter-6-safety-and-security) for seed phrase protection.)

ADA can be obtained through centralized exchanges (such as Binance, Coinbase, or Kraken) or through peer-to-peer means [30](https://cardano.org/where-to-get-ada/).

### Why Cardano Matters: Financial Inclusion and Sustainability

A core motivation behind Cardano's design is extending financial services to populations underserved by traditional banking. Billions of people globally lack access to basic services such as identity verification, credit, and insurance — not because they are unworthy of them, but because the infrastructure to deliver those services profitably at small scale does not exist in their regions. A blockchain that allows anyone with a smartphone to hold a digital identity, receive payments, take a micro-loan, or participate in governance represents a fundamentally different financial stack — one not dependent on the geographic reach of a bank or the willingness of a government to issue documents [78](https://resources.cryptocompare.com/asset-management/12/1741690659365.pdf).

Cardano's goals as stated in its technical documentation include sustainability, scalability, transparency, and supporting decentralized applications (DApps) for enterprise use [18](https://docs.cardano.org/about-cardano/introduction). As of 2026, the network has processed over 120 million transactions, reflecting years of consistent on-chain growth [29](https://cardano.org/insights/).

### Cardano's Research-Driven Foundation

Cardano was conceived not as an iteration of existing blockchains but as a protocol whose every design decision would be grounded in academic peer review. That philosophy, visible from the project's earliest days, distinguishes Cardano from virtually every other major blockchain and shapes the safety guarantees users and developers can rely on today.

#### The Peer-Review-First Philosophy

Before a single line of mainnet code shipped, Cardano's core protocol was subjected to the same scrutiny applied to findings in academic cryptography and distributed systems. The research program produced a catalog of peer-reviewed papers organized by development era — Byron, Shelley, Goguen, Basho, and Voltaire — each era introducing formally specified contributions that preceded protocol deployment [26](https://cardano.org/research/). The papers were submitted to, and accepted at, top-tier venues including CRYPTO, covering topics ranging from consensus theory and stake-pool reward sharing to smart-contract semantics and governance mechanisms [26](https://cardano.org/research/).

Charles Hoskinson, speaking at Tech for Impact Tokyo in October 2025, framed the underlying ambition plainly: "Blockchain isn't about building currencies; it's about transforming the laws of social governance into laws of physics" [41](https://www.iog.io/news/tokyo-diaries-where-it-all-began). That framing — treating protocol rules as verifiable, physics-like laws rather than mutable social agreements — is inseparable from the commitment to formal methods that defines the Cardano research programme.

#### Ouroboros Security Guarantees in Depth

The original Ouroboros paper, authored by Kiayias, Russell, David, and Oliynykov, describes "the first blockchain protocol based on proof of stake with rigorous security guarantees" [77](https://eprint.iacr.org/2016/889.pdf). The security guarantees are not informal claims: the protocol establishes formal persistence and liveness properties and proves that honest behavior constitutes a Nash equilibrium — meaning no individual participant gains by defecting from the protocol rules [77](https://eprint.iacr.org/2016/889.pdf).

The Ouroboros family expanded across Cardano's development eras. The peer-reviewed catalog covers Ouroboros Praos (adaptive security against dynamic corruption), Ouroboros Genesis (bootstrapping security without a trusted checkpoint), and Ouroboros-BFT alongside the original protocol [26](https://cardano.org/research/). Ouroboros-BFT, by Kiayias and Russell (IOHK and University of Edinburgh, 2018), provides Byzantine fault-tolerant ledger consensus: the protocol tolerates up to t Byzantine faults among n participants provided t < n/3, and delivers both persistence and liveness under that bound [79](https://eprint.iacr.org/2018/1049.pdf). BFT-style consensus enables near-instant transaction confirmation in federated settings, a property used during the Byron-to-Shelley transition [79](https://eprint.iacr.org/2018/1049.pdf).

#### Formal Verification: Securing the Smart Contract Layer

Peer review of the protocol is one layer of assurance; formal verification of deployed smart contracts is another. In October 2025, Input Output published results from a next-generation verification tool that operates at the UPLC (Untyped Plutus Core) bytecode level — the actual compiled code that executes on-chain — rather than at the source-code level [39](https://www.iog.io/news/always-secure-and-safer-than-ever-thanks-to-next-level-smart-contract-verification-on-cardano). This distinction matters: source-code verification checks a model, while bytecode verification checks what actually runs.

The tool reimplements Cardano's CEK evaluation machine in the Lean4 proof assistant and combines it with SMT (Satisfiability Modulo Theories) solvers to reason automatically about program behavior [39](https://www.iog.io/news/always-secure-and-safer-than-ever-thanks-to-next-level-smart-contract-verification-on-cardano). In a production test, the verifier analyzed a real mainnet contract — the `processSCOrder` function, spanning more than 1,500 lines of UPLC — and verified 14 security requirements in approximately 10 seconds [39](https://www.iog.io/news/always-secure-and-safer-than-ever-thanks-to-next-level-smart-contract-verification-on-cardano). When a requirement is violated, the tool produces a concrete counterexample rather than a generic error, dramatically accelerating debugging.

#### Academic Partnerships and Ongoing Research

The research enterprise is sustained by a network of university collaborations. Input Output's education and research partnerships span the University of Edinburgh (home of a dedicated blockchain lab led by Professor Aggelos Kiayias, lead author of the original Ouroboros paper), the University of Athens, the University of the West Indies, the University of Wyoming, Carnegie Mellon University, the European Business University of Luxembourg, the University of Malta, and the University of Cantabria [20](https://docs.cardano.org/pioneer-programs/education).

The most recent institutional expansion was announced in April 2026: Input Output and the Archimedes Research Unit of the Athena Research Center in Greece launched a dedicated blockchain technology laboratory (BTL) in Athens [40](https://www.iog.io/news/input-output-launches-new-blockchain-technology-laboratory-at-archimedes). The BTL focuses on decentralized AI, blockchain, and privacy-preserving healthcare applications, with principal investigator Professor Minos Garofalakis and co-investigators Professor Evangelos Markakis and Professor Spyros Voulgaris leading the programme [40](https://www.iog.io/news/input-output-launches-new-blockchain-technology-laboratory-at-archimedes).

Community education programs reinforce the academic spine. The IO education team runs Cardano Days events (achieving a Net Promoter Score of 92), the Plutus Pioneer program, the DRep Pioneer program, and the Haskell Bootcamp, and has partnered with the National Technological University Buenos Aires to deliver a formal Cardano Developer course [20](https://docs.cardano.org/pioneer-programs/education). Community-led programs documented on Cardano Docs include the Cardano Academy (operated by the Cardano Foundation), IO Academy YouTube content, Gimbalabs, and NMKR Docs [17](https://docs.cardano.org/pioneer-programs/community-education).

### The Cardano Foundation and Enterprise Adoption

The Cardano Foundation (CF) is an independent, Swiss-based non-profit whose mandate is to grow and develop Cardano as a global public good. While Input Output researches and engineers the protocol, the Foundation focuses on the institutional, regulatory, and commercial dimensions of adoption — working with businesses, governments, regulators, and policymakers to embed Cardano infrastructure in real-world operations [1](https://cardanofoundation.org/).

#### Enterprise Solutions: Traceability, Authenticity, and Digital Product Passports

The Foundation's enterprise product portfolio is organized around three solution areas that leverage Cardano's core properties — immutability, public verifiability, and energy efficiency.

**Traceability** addresses supply chain integrity across pharmaceuticals, manufacturing, luxury goods, food and agriculture, and global shipping [8](https://cardanofoundation.org/solutions/traceability). Documented deployments include the Bolnisi wine region in Georgia (vineyard-to-glass provenance), Epoch Sports (sports-property authenticity), and Veritree (tree-planting and sustainability verification) [8](https://cardanofoundation.org/solutions/traceability).

**Authenticity** targets counterfeit prevention and digital credentialing across asset tokenization, digital identity, intellectual property protection, and supply chain [9](https://cardanofoundation.org/solutions/authenticity). A notable application is UNDP Tadamon, which issues verifiable credentials on Cardano [9](https://cardanofoundation.org/solutions/authenticity).

**Digital Product Passport (DPP)** responds directly to EU regulatory pressure. The EU Ecodesign for Sustainable Products Regulation — Regulation (EU) 2024/1781 (ESPR) — mandates that products placed on the European market carry a digital product passport [3](https://cardanofoundation.org/solutions/digital-product-passport). Cardano's role is to provide the underlying infrastructure: ensuring record continuity across a product's lifecycle, supplying an immutable audit trail, securing privacy-respecting trust layers, and enabling seamless integration with existing enterprise software stacks [3](https://cardanofoundation.org/solutions/digital-product-passport).

#### The Partner Ecosystem

Enterprise adoption is accelerated by the Foundation's curated partner network. On the accelerator and venture side, anchor partners include: **CV Labs** (global blockchain accelerator), **Techstars** (investment infrastructure and mentorship), **Draper Dragon** (blockchain and AI-focused VC fund — announced an $80 million ecosystem fund targeting Cardano-adjacent opportunities in April 2026 [1](https://cardanofoundation.org/)), and **UNDP Accelerator Labs** (90+ labs across 115 countries) [2](https://cardanofoundation.org/partners?type=Accelerator+%26+Venture). Enterprise partners include Grant Thornton, LCX, Jakala, and Draper University [5](https://cardanofoundation.org/partners?type=Enterprise). International institutional partners include UNHCR and UNDP [1](https://cardanofoundation.org/).

#### The Cardano Academy and Education Reach

The Foundation's education arm — Cardano Academy — provides free, self-paced online learning with more than 1,000 subscribers [1](https://cardanofoundation.org/). The curriculum uses gamification and knowledge testing to drive completion, and awards certification to learners who demonstrate competency [17](https://docs.cardano.org/pioneer-programs/community-education). The Foundation's 2025 Activity and Financial Report was published on-chain — an act that directly demonstrates the transparency properties it promotes to enterprise clients [1](https://cardanofoundation.org/).

### Section References

[1](https://cardanofoundation.org/) — Cardano Foundation Official Homepage
[2](https://cardanofoundation.org/partners?type=Accelerator+%26+Venture) — Cardano Foundation Accelerator & Venture Partners
[3](https://cardanofoundation.org/solutions/digital-product-passport) — Cardano Foundation Digital Product Passport
[5](https://cardanofoundation.org/partners?type=Enterprise) — Cardano Foundation Enterprise Partners
[8](https://cardanofoundation.org/solutions/traceability) — Cardano Foundation Traceability Solution
[9](https://cardanofoundation.org/solutions/authenticity) — Cardano Foundation Authenticity Solution
[17](https://docs.cardano.org/pioneer-programs/community-education) — Cardano Docs Community Education Initiatives
[18](https://docs.cardano.org/about-cardano/introduction) — Cardano Docs Introduction to Cardano
[20](https://docs.cardano.org/pioneer-programs/education) — Cardano Docs Input Output Education
[21](https://cardano.org/) — Cardano.org Homepage
[22](https://cardano.org/what-is-ada/) — What Is ADA
[23](https://cardano.org/get-started/) — Get Started with Cardano
[26](https://cardano.org/research/) — Cardano Research
[29](https://cardano.org/insights/) — Cardano Insights On-Chain Analytics
[30](https://cardano.org/where-to-get-ada/) — Where to Get ADA
[39](https://www.iog.io/news/always-secure-and-safer-than-ever-thanks-to-next-level-smart-contract-verification-on-cardano) — IOG News Smart Contract Verification
[40](https://www.iog.io/news/input-output-launches-new-blockchain-technology-laboratory-at-archimedes) — IOG News Blockchain Technology Laboratory at Archimedes
[41](https://www.iog.io/news/tokyo-diaries-where-it-all-began) — IOG News Tokyo Diaries
[77](https://eprint.iacr.org/2016/889.pdf) — Ouroboros: A Provably Secure Proof-of-Stake Blockchain Protocol
[78](https://resources.cryptocompare.com/asset-management/12/1741690659365.pdf) — Why Cardano — Early Vision Paper
[79](https://eprint.iacr.org/2018/1049.pdf) — Ouroboros-BFT: A Simple Byzantine Fault Tolerant Consensus Protocol


## Chapter 2: Cardano Wallets

A crypto wallet does not store coins the way a physical wallet holds cash. Instead, it stores the cryptographic private keys that prove ownership of funds recorded on the blockchain. Anyone who obtains your private keys — or your recovery phrase, which regenerates them — gains full, irrecoverable control of your assets [27](https://cardano.org/wallets/).

### What Is a Cardano Wallet?

A wallet lets you store, send, and receive ada and other Cardano native tokens [22](https://cardano.org/what-is-ada/). Wallets fall along two axes: connectivity (hot vs. cold) and custody (custodial vs. non-custodial).

**Hot vs. cold wallets.** A hot wallet is connected to the internet and accessible at any time with the correct keys — examples include browser extensions and mobile apps. A cold wallet is an offline wallet used for secure long-term storage; examples include hardware devices (Ledger, Trezor) and paper wallets. Cardano is supported by both Trezor and Ledger hardware wallets [27](https://cardano.org/wallets/).

**Custodial vs. non-custodial wallets.** Centralized exchanges hold custody over ada and other native tokens until the user withdraws funds to a self-controlled wallet [30](https://cardano.org/where-to-get-ada/). Non-custodial wallets keep private keys under the user's sole control; all wallets listed on the Cardano Wallet Finder are non-custodial [27](https://cardano.org/wallets/).

**Full-node vs. light wallets.** Daedalus is a full-node desktop wallet developed by IOHK (Input Output) that downloads and validates the full blockchain locally [27](https://cardano.org/wallets/). Light wallets connect to a remote node and are faster to set up; they include both browser extensions and mobile apps [27](https://cardano.org/wallets/).

### Key Cardano Wallets

The table below summarises the wallets listed on the official Cardano Wallet Finder [27](https://cardano.org/wallets/). Descriptions are provided by the respective project teams; listing does not imply endorsement.

| Wallet | Platforms | Type | Notable Features |
|--------|-----------|------|-----------------|
| Eternl | iOS, Android, Browser Extension | Light | Multi-account, hardware wallet support, multi-asset, governance, QR claim |
| Lace | Browser Extension | Light | Developed by IOG; independently audited; open source; hardware wallet support; governance |
| Typhon | Browser Extension | Light | From creators of CardanoScan; NFT gallery, transaction metadata, vote registration |
| VESPR | iOS, Android | Light | Mobile-first; non-custodial; prioritizes security and ease-of-use; governance; QR claim |
| Yoroi | iOS, Android, Browser Extension | Light | Developed by EMURGO (founding entity); open source; hardware wallet support |
| Daedalus | Desktop | Full Node | Developed by IOHK; validates full blockchain locally; multi-account; open source |
| AdaLite | Web App | Light | Developed by vacuumlabs; hardware wallet support; multi-account |
| Begin Wallet | iOS, Android, Browser Extension | Light | Hardware wallet support (Ledger, Keystone); ENS-style Begin ID; open source cryptographic core |
| GameChanger Wallet | Browser Extension, Web App | Light | Native NFT and token features; DApp connector |
| GeroWallet | Browser Extension | Light | DApp connector; staking |
| Medusa Wallet | Web App | Light | Privacy-focused; designed for untrusted environments |
| NuFi Wallet | Browser Extension | Light | Multi-chain; built-in DEX; hardware wallet support |
| Atomic Wallet | iOS, Android, Desktop | Light | Multi-cryptocurrency; contributed to Cardano Rust library |
| TokeoPay | iOS, Android | Light | Bitcoin and Cardano; NFT support; multi-asset |
| Multisig Platform | Web App | Light | Multi-signature treasury; governance |

### How to Choose a Wallet

The Cardano Wallet Finder recommends three primary checks when evaluating a wallet [27](https://cardano.org/wallets/):

1. **Hardware wallet support.** Connecting a hardware wallet like Ledger or Trezor adds an extra layer of security.
2. **Open source.** Open-source code allows the community to review and verify security.
3. **Track record.** Established wallets have a longer history of reliability.

For new users, the Wallet Finder offers a "I'm new to Cardano" filter that surfaces the easiest options [27](https://cardano.org/wallets/). Mobile wallets such as VESPR are designed with easy setup and non-technical users in mind [27](https://cardano.org/wallets/).

### Setting Up a Wallet: Key Concepts

Every non-custodial Cardano wallet generates a recovery phrase (seed words) during setup. This phrase is the master key to all funds in the wallet. If anyone else obtains the recovery phrase, they gain full control of the wallet with no way to recover the funds [25](https://cardano.org/common-scams/). Before receiving ada, a user must set up a wallet and share their wallet address [30](https://cardano.org/where-to-get-ada/). Some wallets also allow purchasing crypto with a debit or credit card, bank transfer, or Apple Pay, depending on location [30](https://cardano.org/where-to-get-ada/).

### Section References

[22](https://cardano.org/what-is-ada/) — What Is ada, the Native Token of Cardano
[25](https://cardano.org/common-scams/) — Common Cardano Scams, How to Stay Safe
[27](https://cardano.org/wallets/) — Cardano Wallet Finder, Compare and Choose the Best Wallet
[30](https://cardano.org/where-to-get-ada/) — Buy ada, Where to Get Cardano's Native Token


## Chapter 3: Staking on Cardano

### What Is Stake?

Ada held on the Cardano network represents a stake in the network, with the size of the stake proportional to the amount of ada held [28](https://cardano.org/stake-pool-delegation/). The ability to delegate or pledge a stake is fundamental to how Cardano works [28](https://cardano.org/stake-pool-delegation/). Staking on Cardano is non-custodial: ada never leaves the holder's wallet during delegation, and the staked balance remains spendable at all times.

There are two ways an ada holder can earn rewards: by delegating their stake to a stake pool run by someone else, or by running their own stake pool [28](https://cardano.org/stake-pool-delegation/). Rewards earned accrue with the original stake — when rewards are received, the balance of the reward account increases and, consequently, the delegated stake is also increased [28](https://cardano.org/stake-pool-delegation/).

### How Ouroboros Proof-of-Stake Works

Cardano's consensus mechanism is called Ouroboros, a provably secure proof-of-stake blockchain protocol [77](https://eprint.iacr.org/2016/889.pdf). In the Ouroboros model, rather than miners investing computational resources to participate in the leader election process, a process randomly selects one stakeholder proportionally to the stake that each possesses according to the current blockchain ledger [77](https://eprint.iacr.org/2016/889.pdf). This distinguishes proof-of-stake from proof-of-work: the protocol makes no further "artificial" computational demands beyond holding and pledging stake [77](https://eprint.iacr.org/2016/889.pdf).

The Ouroboros protocol is designed to be modular and flexible, allowing for delegation, sidechains, and different forms of random number generation [78](https://resources.cryptocompare.com/asset-management/12/1741690659365.pdf). Its core innovation beyond being proven secure using a rigorous cryptographic model is the ability to evolve as a network grows from thousands to millions of users [78](https://resources.cryptocompare.com/asset-management/12/1741690659365.pdf). (The academic background behind Ouroboros is covered in depth in [Chapter 1: Introduction to Blockchain and Cardano](#chapter-1-introduction-to-blockchain-and-cardano).)

Time on Cardano is divided into epochs, each of which is further divided into slots [77](https://eprint.iacr.org/2016/889.pdf). In each epoch, a snapshot of the current set of stakeholders is taken, and a secure multiparty computation takes place utilizing the blockchain itself as the broadcast channel; the outcome of this process determines which stakeholders will be elected slot leaders for that epoch [77](https://eprint.iacr.org/2016/889.pdf). A slot leader is responsible for creating the next block in the chain and receives a monetary reward for doing so [28](https://cardano.org/stake-pool-delegation/).

The incentive mechanism underpinning staking combines mathematics, economic theory, and game theory to ensure the longevity and health of the Cardano network and ecosystem [28](https://cardano.org/stake-pool-delegation/). Ouroboros has been proven to achieve security properties comparable to those of the Bitcoin blockchain protocol, while offering qualitative efficiency advantages over proof-of-work blockchains [77](https://eprint.iacr.org/2016/889.pdf).

### Stake Pools and Stake Pool Operators

Stake pools are run by stake pool operators (SPOs) — network participants with the skills to reliably ensure consistent uptime of a node, which is essential to the success of the Ouroboros protocol [28](https://cardano.org/stake-pool-delegation/). The protocol uses a probabilistic mechanism to select a leader for each slot; the chance of a stake pool node being selected as slot leader increases proportionately to the amount of stake delegated to that node [28](https://cardano.org/stake-pool-delegation/).

Each time a stake pool node is selected as a slot leader and successfully creates a block, it receives a reward, which is shared with the pool proportionate to the amount each member has delegated [28](https://cardano.org/stake-pool-delegation/). Stake pool operators can deduct their running costs from the awarded ada, as well as specify a profit margin for providing the service [28](https://cardano.org/stake-pool-delegation/).

Key operational resources for SPOs include the Cardano Docs SPO section [16](https://docs.cardano.org/stake-pool-operators/operating-a-stake-pool), community-run Guild Operators tutorials, and SPO community communication channels such as the SPO Telegram announcements channel and the IOG Technical Community Discord [16](https://docs.cardano.org/stake-pool-operators/operating-a-stake-pool).

### Delegation

Delegation is the process by which ada holders delegate the stake associated with their ada to a stake pool [28](https://cardano.org/stake-pool-delegation/). It allows ada holders who do not have the skills or desire to run a node to participate in the network and be rewarded in proportion to the amount of stake delegated [28](https://cardano.org/stake-pool-delegation/).

Delegated stake can be re-delegated to another pool at any time [28](https://cardano.org/stake-pool-delegation/). Re-delegated stake will remain in the current pool until the epoch after next (from the point of re-delegation), after which delegation preferences are updated on-chain and stake moves to the new pool [28](https://cardano.org/stake-pool-delegation/). Rewards continue to be distributed from the end of each epoch, so a delegator receives rewards from their original stake pool for two epochs before new delegation preferences are applied [28](https://cardano.org/stake-pool-delegation/).

Some wallets offer solutions for delegating to different stake pools at the same time [28](https://cardano.org/stake-pool-delegation/).

### Rewards Calculation

The amount of stake delegated to a given stake pool is the primary way the Ouroboros protocol chooses who should add the next block to the blockchain and receive a monetary reward [28](https://cardano.org/stake-pool-delegation/). The more stake is delegated to a stake pool (up to a certain point), the more likely it is to make the next block — and the rewards are shared between everyone who delegated their stake to that pool [28](https://cardano.org/stake-pool-delegation/). A staking calculator is available at cardano.org/calculator to estimate reward amounts; note that the calculator produces only estimates and should not be considered definitive [28](https://cardano.org/stake-pool-delegation/).

### No Lock-Up: Liquid Native Staking

A key distinction of Cardano's staking model is that ada is never locked up during delegation. Holders retain full custody and liquidity: they can spend, send, or re-delegate their ada at any time. Rewards earned accrue to the reward account and are automatically added to the delegated stake balance [28](https://cardano.org/stake-pool-delegation/). Cardano's staking model includes: no minimum amount of ada required to stake; no risk of slashing (losing staked ada); no locking period; full custody retained over delegated ada; and rewards distributed by the protocol itself (not by the pools), ensuring fair distribution [30](https://cardano.org/where-to-get-ada/).

This native liquid staking model is different from liquid staking derivatives offered by some DeFi protocols; the topic of liquid staking derivatives on Cardano is tracked as a content area within the Essential Cardano community resources [58](https://www.essentialcardano.io/search?category=faq&tags=Liquid+Staking).

### Stake Pool Saturation

Saturation is a term used to indicate that a particular stake pool has more stake delegated to it than is ideal for the network [28](https://cardano.org/stake-pool-delegation/). Once a pool reaches the point of saturation it will offer diminishing rewards [28](https://cardano.org/stake-pool-delegation/). The saturation mechanism was designed to prevent centralization by encouraging delegators to delegate to different stake pools, and operators to set up alternative pools so they can continue earning maximum rewards [28](https://cardano.org/stake-pool-delegation/).

### How to Choose a Stake Pool

Choosing a stake pool involves several factors [28](https://cardano.org/stake-pool-delegation/):

- **Performance**: historical success rate in producing blocks; a consistently high performance indicates reliability.
- **Uptime**: pool servers should run without interruption.
- **Margin fees**: pools charge a percentage fee on rewards earned; lower fees can mean more rewards, balanced against pool performance.
- **Fixed fees**: a minimum fixed fee set by the protocol that pools charge per epoch.
- **Saturation point**: staking with a saturated pool decreases rewards; choose a pool below the saturation threshold.
- **Community engagement**: pools that actively engage with the Cardano community through educational content or contributions.
- **Mission-driven pools**: some pools donate a portion of their fees to charitable causes or specific missions.

Pool tools are available at cardano.org/apps to help evaluate and compare pools [28](https://cardano.org/stake-pool-delegation/). Pool desirability measures how desirable a pool is to an ada holder; it is influenced by a pool's margin, fee, performance, total rewards available in the current epoch, and saturation percentage [28](https://cardano.org/stake-pool-delegation/).

### Section References

[16](https://docs.cardano.org/stake-pool-operators/operating-a-stake-pool) — Cardano Docs Operating a Stake Pool
[28](https://cardano.org/stake-pool-delegation/) — Cardano Stake Pool Delegation
[30](https://cardano.org/where-to-get-ada/) — Buy ada, Where to Get Cardano's Native Token
[58](https://www.essentialcardano.io/search?category=faq&tags=Liquid+Staking) — Essential Cardano Liquid Staking FAQ Index
[77](https://eprint.iacr.org/2016/889.pdf) — Ouroboros: A Provably Secure Proof-of-Stake Blockchain Protocol
[78](https://resources.cryptocompare.com/asset-management/12/1741690659365.pdf) — Why Cardano — Early Vision Paper


## Chapter 4: The Cardano Ecosystem

### Overview: A Growing On-Chain Economy

The Cardano ecosystem comprises the applications, tools, services, and communities built on top of the Cardano blockchain. As of 2026, the official Cardano app directory lists 123 curated projects deployed on Cardano mainnet across more than a dozen categories [31](https://cardano.org/apps/).

| Category | Curated count |
|---|---|
| Open-Source projects | 28 |
| NFT projects | 23 |
| Marketplaces | 20 |
| Wallets | 15 |
| Analytics tools | 14 |
| Decentralized Exchanges (DEX) | 12 |
| Governance tools | 11 |
| Games | 10 |
| Block Explorers | 7 |

This breadth reflects Cardano's growth from a research project into a platform supporting real economic activity. Beginners can explore this landscape through curated "favorites" lists maintained by the Cardano Foundation, which highlight projects that have demonstrated reliability and community standing [31](https://cardano.org/apps/).

### ADA: Obtaining and Using the Currency

Ada is the native token of the Cardano blockchain, named after Ada Lovelace — a 19th-century mathematician recognized as the first computer programmer and daughter of the poet Lord Byron [22](https://cardano.org/what-is-ada/). Ada functions as a digital currency: any user anywhere in the world can use it as a secure exchange of value without requiring a third party to mediate the transaction, with every transaction permanently, securely, and transparently recorded on the Cardano blockchain [22](https://cardano.org/what-is-ada/).

Every ada holder also holds a stake in the Cardano network. Ada stored in a wallet can be delegated to a stake pool to earn rewards and participate in the successful running of the network, or a user can run their own stake pool [22](https://cardano.org/what-is-ada/). (For staking mechanics, see [Chapter 3: Staking on Cardano](#chapter-3-staking-on-cardano).)

There are multiple pathways to obtain ada [30](https://cardano.org/where-to-get-ada/):

**Centralized Exchanges (CEXs)** are platforms where cryptocurrencies are traded via an intermediary that facilitates transactions, provides custodial storage, and handles regulatory compliance. CEXs hold custody over ada until the user withdraws funds to a self-controlled wallet. The Cardano "Where to Get ada" page maintains a country-filtered list of exchanges; CoinMarketCap lists the full set of exchanges supporting ada [30](https://cardano.org/where-to-get-ada/).

**Decentralized Exchanges (DEXs)** are platforms for trading cryptocurrencies without a central authority, allowing peer-to-peer trading via smart contracts. Major Cardano DEXs include Minswap (125,919 transactions in the last 30 days), WingRiders (41,416 tx), SundaeSwap (22,826 tx), CSWAP (14,140 tx), and Splash (7,321 tx) [30](https://cardano.org/where-to-get-ada/). DEXs are not suitable for beginners, as the user must already hold ada to use them [30](https://cardano.org/where-to-get-ada/).

**Receiving ada peer-to-peer.** Once a Cardano wallet is set up, sharing the wallet address enables direct peer-to-peer transfers. Some wallets allow purchasing crypto directly with a debit or credit card, bank transfer, or Apple Pay depending on location [30](https://cardano.org/where-to-get-ada/).

**Project Catalyst.** Ada can also be obtained through Cardano's community innovation fund by submitting and winning a project proposal [30](https://cardano.org/where-to-get-ada/).

Ada supply data is tracked publicly. Cardano Insights publishes on-chain charts covering ada supply distribution, historical supply across reserves, rewards, treasury, and deposits, transaction counts, fees, and block production across epochs [29](https://cardano.org/insights/).

### The eUTXO Model: A Beginner Introduction

Cardano's transaction model is called the Extended Unspent Transaction Output model (eUTXO). Understanding it at a basic level helps explain how DeFi on Cardano differs from platforms like Ethereum.

In the account model used by Ethereum, all contract state is stored in a shared, growing data structure. Every storage access requires traversing this structure, meaning costs grow as the system is used more — IOG describes this as a fundamental "growth tax" and characterizes the design as a "trillion dollar mistake" [35](https://www.iog.io/news/the-account-model-a-trillion-dollar-mistake). Note: this characterization is IOG's perspective as Cardano's research and development partner, written to advocate for the eUTXO design.

In the eUTXO model, each unspent output (UTxO) is an independent piece of state stored in a flat map. Spending a UTxO — using it as the input to a new transaction — removes it from the active set, which is also the deletion of that state [35](https://www.iog.io/news/the-account-model-a-trillion-dollar-mistake). This has two practical implications for ordinary users:

1. **Access costs are flat regardless of total network usage.** Specifying a UTxO as input to a transaction tells the validator exactly where the data is, so no runtime lookup across a growing structure is required [35](https://www.iog.io/news/the-account-model-a-trillion-dollar-mistake).
2. **Every UTxO on Cardano holds a minimum ADA deposit proportional to its storage size.** Creating state costs this deposit; consuming (spending) state releases the deposit back to the consumer [35](https://www.iog.io/news/the-account-model-a-trillion-dollar-mistake).

For users who face a failed competing transaction (contention) on a Cardano DEX, the eUTXO model means the failed transaction is cheaply rejected without charging fees, unlike on Ethereum where failed transactions still consume gas [35](https://www.iog.io/news/the-account-model-a-trillion-dollar-mistake).

### Decentralized Exchanges and DeFi

Decentralized Finance (DeFi) on Cardano enables users to trade, lend, borrow, and earn yield directly on-chain — without a centralized company holding their funds.

**Decentralized Exchanges (DEXs)** allow users to swap one token for another directly from their wallets. The DEXs operating on Cardano mainnet include Minswap, SundaeSwap, MuesliSwap, WingRiders, DexHunter, Genius Yield, Splash, CSWAP, and VyFinance [31](https://cardano.org/apps/).

**Lending and borrowing protocols** allow users to deposit ADA or other Cardano Native Tokens as collateral and borrow against them, or to earn interest by supplying liquidity. Protocols in this category include Liqwid Finance, Aada Finance, FluidTokens, Optim Finance, Dano Finance, and Yamfore [31](https://cardano.org/apps/).

Because Cardano uses the eUTXO model rather than an account-based model, DeFi protocols on Cardano are architecturally different from those on Ethereum — but the economic functions (swap, lend, yield) are comparable.

### NFTs and Digital Marketplaces

Non-Fungible Tokens (NFTs) on Cardano represent unique digital assets — artwork, collectibles, in-game items, event tickets, or digital books — whose ownership is recorded on the blockchain. Cardano's native multi-asset ledger means that NFTs can be minted directly at the protocol level without requiring a separate smart contract for each collection, which reduces cost and complexity [78](https://resources.cryptocompare.com/asset-management/12/1741690659365.pdf).

Key platforms in the Cardano NFT ecosystem [31](https://cardano.org/apps/):

| Platform | Function |
|---|---|
| JPG Store | The largest NFT marketplace on Cardano — buy, sell, and discover NFT collections |
| NMKR | NFT minting and token issuance platform for creators and enterprises |
| Book.io | NFT-based eBook platform — purchase and own digital books as verifiable assets |
| Cardahub | NFT community and CNFT discovery hub |

### Stablecoins, Oracles, and Bridges

**Stablecoins** are tokens whose value is pegged to a stable reference asset (typically the US dollar), enabling on-chain commerce and DeFi without exposure to ADA price volatility. Stablecoin projects on Cardano include USDM and Open DJED [31](https://cardano.org/apps/). USDCx launched as a USDC-backed stablecoin in February 2026 [42](https://www.iog.io/news?type=article).

**Oracles** provide blockchains with reliable real-world data (such as asset prices or weather data) that smart contracts can act on. Cardano oracle providers include Charli3 and Orcfax [31](https://cardano.org/apps/).

**Bridges** enable tokens and data to move between Cardano and other blockchains such as Ethereum or BNB Chain, making Cardano interoperable with the wider blockchain ecosystem. Bridge projects include Chainport, Wanchain, Finitum Bridge, and Mynth [31](https://cardano.org/apps/).

### Block Explorers and Analytics Tools

A block explorer is a public website that lets anyone look up any transaction, wallet address, or block on the blockchain — providing transparency into all on-chain activity.

| Tool | Function |
|---|---|
| CardanoScan | The most widely used Cardano block explorer; search transactions, addresses, and tokens |
| CExplorer | Block explorer with detailed staking and pool analytics |
| Pool PM | Visual stake pool browser; useful for delegators choosing a pool |
| eUTxO | Explorer with eUTXO-native visualization of transaction structure |
| AdaStat | On-chain statistics and network analytics |
| TapTools | Portfolio tracker, token analytics, and DeFi data aggregator |
| Dune | Open analytics platform with community-built Cardano dashboards |
| BALANCE Analytics | On-chain analytics focused on DeFi and liquidity |

[31](https://cardano.org/apps/)

### DApps, Tools, and Community Platforms

The Cardano Apps directory groups projects by function: exchanges, lending protocols, NFT platforms, governance tools, block explorers, wallets, analytics dashboards, and identity systems [31](https://cardano.org/apps/). Identity infrastructure on Cardano includes adahandle (human-readable address handles) and Veridian (decentralized identity) [31](https://cardano.org/apps/).

Since the activation of CIP-1694 and the Voltaire governance era, ADA holders can vote on protocol changes, treasury withdrawals, and network parameters directly on-chain. Governance on Cardano operates through three bodies: the Constitutional Committee (CC), Delegated Representatives (DReps), and Stake Pool Operators (SPOs). Any ADA holder can delegate their voting power to a DRep without giving up custody of their ADA — similar to how they delegate staking without moving their funds [18](https://docs.cardano.org/about-cardano/introduction). (See [Chapter 5: Cardano Governance](#chapter-5-cardano-governance) for governance detail.)

Governance tooling [31](https://cardano.org/apps/):

| Tool | Function |
|---|---|
| gov.tools | The official Cardano governance portal — register as a DRep, vote on proposals, and track governance activity |
| Tempo | Governance analytics and DRep (Delegated Representative) dashboard |
| Clarity Protocol | On-chain governance participation and proposal tracking |

Education and community resources in the ecosystem include:

- **Cardano Academy** — free online courses and certifications covering Cardano fundamentals and blockchain concepts.
- **Gimbalabs** — a community-first learning environment described as "a collaborative community and space where dApps and open-source tools are developed in the 'Playground' (Project-Based Learning experiences). All are welcome to join every Tuesday at 4pm UTC" [31](https://cardano.org/apps/). Gimbalabs offers live coding sessions, open spaces, governance sessions, and project-based learning courses in multiple languages including Japanese [45](https://www.essentialcardano.io/podcast).
- **Andamio** — a verified trust protocol for distributed work: "Organizations can mint credentials, verify skills, and find contributors. Individuals can learn, discover opportunities, join project teams" [31](https://cardano.org/apps/).
- **Onboard Ninja** — an onboarding platform for new Cardano users.
- **Essential Cardano** (`essentialcardano.io`) — a community hub for articles, FAQs, glossary, podcasts, and infographics maintained by the Cardano Foundation [44](https://www.essentialcardano.io/).
- **Cardano Forum** — the primary community discussion platform for governance proposals, technical questions, and ecosystem news [46](https://www.essentialcardano.io/community).
- **Cardano Ambassador Program** — a global network of community volunteers who educate and advocate for Cardano in their local languages and regions [12](https://cardano.org/ambassadors/).

### Developer Tools and Builder Infrastructure

The Cardano Developer Portal catalogs 98 builder tools across 14 functional categories: Governance, Hosted Service, IDE, Indexer, NFT, Node Client, Operator Tool, Provider, Serialization, Smart Contracts, Testing, Transaction Builder, and Wallet [19](https://developers.cardano.org/tools/). Tools span 19 programming languages including Haskell, Rust, TypeScript, Python, Go, Java, and C# [19](https://developers.cardano.org/tools/).

The Developer Portal's curated "favorites" identify seven foundational tools [19](https://developers.cardano.org/tools/):

| Tool | Description |
|------|-------------|
| Aiken | A modern smart contract platform for Cardano |
| Blockfrost | Instant and scalable API to the Cardano blockchain |
| cardano-cli | Companion command-line tool to interact with a Cardano node, manipulate addresses, or create transactions |
| Demeter.run | A cloud environment with all the tools for building a dApp |
| Guild Operators Suite | Includes CNTools, gLiveView, and topologyUpdater for stake pool operators |
| Mesh | A feature-complete, open-source TypeScript SDK and off-chain framework including wallet integration, transaction building, a smart contract library, third-party API integration, and UI components |
| Ogmios | A lightweight bridge interface (WebSocket + JSON/RPC) for cardano-node |

The Developer Portal also provides SDK support for TypeScript, Python, Rust, Go, Java, C#, and Swift, with a quickstart command of `npx meshjs your-app-name` for TypeScript projects and `yaci-devkit up` for a local devnet [14](https://developers.cardano.org/). Weekly Developer Office Hours are hosted by Cardano Foundation engineers on YouTube, giving new builders direct access to expert guidance [14](https://developers.cardano.org/).

### The Cardano Improvement Proposal (CIP) Process

The CIP process is the formal mechanism through which the Cardano community proposes, debates, and ratifies protocol changes and new features. A CIP is defined as "a formalised design document for the Cardano community," and the Cardano Foundation "intends CIPs to be the primary mechanisms for proposing new features, collecting community input on an issue, and documenting design decisions" [13](https://cips.cardano.org/).

Alongside CIPs, Cardano Problem Statements (CPSs) serve a complementary function: they document known problems or gaps in the protocol without prescribing solutions [13](https://cips.cardano.org/). This two-document structure separates problem definition from solution design, enabling structured community deliberation.

The CIP revision history serves as a permanent historical record of the protocol's evolution [13](https://cips.cardano.org/). Ambassador contributors are specifically recognized for their software development contribution type, which includes writing CIPs — reflecting how the proposal process connects grassroots participation to formal protocol governance [12](https://cardano.org/ambassadors/).

Cardano's technical development is grounded in peer-reviewed academic research organized by era. The Byron era produced the foundational Ouroboros proof-of-stake papers [26](https://cardano.org/research/). The Shelley era added decentralization and reward-sharing research [26](https://cardano.org/research/). Goguen-era papers introduced the Extended UTXO model, Marlowe, and Plutus smart contract systems [26](https://cardano.org/research/). Basho-era research covers Hydra (layer-2 state channels), Mithril (stake-based threshold signatures), sidechains, and the Djed stablecoin design [26](https://cardano.org/research/). Voltaire-era research addresses the treasury system, on-chain governance, and CIP-1694 [26](https://cardano.org/research/).

Input Output (IOG) publishes articles, research papers, events, and thought leadership through its news portal, which as of April 2026 contains 498 articles [42](https://www.iog.io/news?type=article). Recent publications cover Hydra's adoption phase, Leios scalability development, USDCx stablecoin deployment, Ouroboros Omega, and inter-chain connectivity research [42](https://www.iog.io/news?type=article).

### Enterprise Adoption: Cardano Foundation Solutions

Decentralized storage is one area where the Cardano Foundation operates enterprise-grade solutions. The Foundation's decentralized storage offering is built on a peer-to-peer network where cryptographic protocols handle data management, verification, and access via the blockchain, providing security, privacy, and complete data ownership [6](https://cardanofoundation.org/solutions/decentralized-storage). Use cases include secure storage of critical DeFi financial data underpinning smart contract functionality and enhancing DeFi transparency [6](https://cardanofoundation.org/solutions/decentralized-storage). For the full range of Foundation enterprise solutions, see the OriginateNavio and Digital Product Passport coverage in [Chapter 1](#the-cardano-foundation-and-enterprise-adoption).

### Section References

[6](https://cardanofoundation.org/solutions/decentralized-storage) — Cardano Foundation Decentralized Storage
[12](https://cardano.org/ambassadors/) — Cardano Ambassador Program
[13](https://cips.cardano.org/) — Cardano Improvement Proposals
[14](https://developers.cardano.org/) — Cardano Developer Portal
[18](https://docs.cardano.org/about-cardano/introduction) — Cardano Docs Introduction to Cardano
[19](https://developers.cardano.org/tools/) — Builder Tools Cardano Developer Portal
[22](https://cardano.org/what-is-ada/) — What Is ada, the Native Token of Cardano
[26](https://cardano.org/research/) — Cardano Research
[29](https://cardano.org/insights/) — Cardano Insights Data and Analytics
[30](https://cardano.org/where-to-get-ada/) — Buy ada, Where to Get Cardano's Native Token
[31](https://cardano.org/apps/) — Cardano Apps Directory
[35](https://www.iog.io/news/the-account-model-a-trillion-dollar-mistake) — The account model: a trillion dollar mistake — Input | Output
[42](https://www.iog.io/news?type=article) — IOG News Articles
[44](https://www.essentialcardano.io/) — Essential Cardano
[45](https://www.essentialcardano.io/podcast) — Essential Cardano Podcasts
[46](https://www.essentialcardano.io/community) — Essential Cardano Community Channels
[78](https://resources.cryptocompare.com/asset-management/12/1741690659365.pdf) — Why Cardano — Early Vision Paper


## Chapter 5: Cardano Governance

### Development Eras: Byron to Voltaire

Cardano is designed in development eras, each targeting a distinct phase of the platform's maturity. The era structure is documented on the Cardano research page [26](https://cardano.org/research/), and the early vision paper frames the philosophy behind building in layers and stages [78](https://resources.cryptocompare.com/asset-management/12/1741690659365.pdf).

**Byron** was a period dedicated to building a foundational federated network that enabled the purchase and sale of ada [26](https://cardano.org/research/). The network ran the proof-of-stake Ouroboros consensus protocol [26](https://cardano.org/research/). Research supporting Byron included the original Ouroboros provably secure PoS paper and Ouroboros-BFT, a Byzantine Fault Tolerant consensus protocol [26](https://cardano.org/research/).

**Shelley** was a period of growth and development focused on ensuring greater decentralization [26](https://cardano.org/research/). This phase led to enhanced security and a more robust environment, following the transition where the majority of nodes became operated by network participants rather than IOG-controlled nodes [26](https://cardano.org/research/). The Shelley era's research included Ouroboros Praos, Ouroboros Genesis, and the Reward Sharing Schemes for Stake Pools paper [26](https://cardano.org/research/).

**Goguen** introduced smart-contract functionality, enabling the construction of decentralized applications while supporting multifunctional assets, fungible and non-fungible token standards [26](https://cardano.org/research/). The Goguen era brought the Extended UTXO (eUTXO) model, Plutus smart contracts, Marlowe financial contracts, and native multi-asset support [26](https://cardano.org/research/).

**Basho** is an era of optimization, improving the scalability and interoperability of the network [26](https://cardano.org/research/). Enhancing network performance, Basho introduces sidechains — new blockchains interoperable with the main Cardano chain — with immense potential to extend the network's capabilities [26](https://cardano.org/research/). Basho research includes the Hydra fast isomorphic state channels paper and Mithril stake-based threshold multisignatures [26](https://cardano.org/research/).

**Voltaire** is the era currently enabling the Cardano network to become a self-sustaining system [26](https://cardano.org/research/). Voltaire is introducing a voting and treasury system that allows network participants to use their stake and voting rights to influence the future development of the blockchain [26](https://cardano.org/research/). The governance specification for Voltaire is CIP-1694: An On-Chain Decentralized Governance Mechanism for Voltaire [26](https://cardano.org/research/).

### Cardano Improvement Proposals (CIPs)

Cardano Improvement Proposals are the formal mechanism through which changes and standards for the Cardano ecosystem are proposed and ratified. The CIP repository is maintained at cips.cardano.org [13](https://cips.cardano.org/). CIP-1694 is the foundational governance specification for the Voltaire era, providing the on-chain decentralized governance mechanism [26](https://cardano.org/research/).

The Essential Cardano community knowledge base indexes articles, FAQs, and developer resources related to CIP-1694, DReps, Constitutional Committee, and governance actions [61](https://www.essentialcardano.io/search?category=faq&tags=Voltaire).

### Voltaire: On-Chain Governance

The Voltaire era introduces a structured system of on-chain governance. The Beyond MVG (Minimum Viable Governance) roadmap, tracked through progress reports published in early 2026 [69](https://www.essentialcardano.io/search?category=article&tags=Voltaire), documents the continuing evolution of Cardano's governance system beyond its initial launch.

**Delegate Representatives (DReps)** are participants who can be delegated voting power by ada holders, allowing individuals who do not wish to vote directly on every governance action to have their stake represented [61](https://www.essentialcardano.io/search?category=faq&tags=Voltaire). The DRep Pioneer program, run by IOG, prepares participants to become delegate representatives playing a crucial role in Cardano's governance [20](https://docs.cardano.org/pioneer-programs/education).

**The Constitutional Committee** is a governance body referenced in the governance framework [61](https://www.essentialcardano.io/search?category=faq&tags=Voltaire). The Cardano Constitution was developed through a community-wide constitutional convention process [61](https://www.essentialcardano.io/search?category=faq&tags=Voltaire).

**SPO Governance Voting**: Stake pool operators participate in the governance process alongside DReps and the Constitutional Committee [61](https://www.essentialcardano.io/search?category=faq&tags=Voltaire). SPOs can vote on certain governance actions using their stake pool keys [61](https://www.essentialcardano.io/search?category=faq&tags=Voltaire).

**Project Catalyst** is described as the world's largest decentralized innovation fund — a framework for the Cardano community to turn ideas into impactful real-world projects [46](https://www.essentialcardano.io/community). Catalyst operates as a community-driven treasury allocation mechanism and has its own announcement and community channels [46](https://www.essentialcardano.io/community).

### The Cardano Constitution

The Cardano Constitution is a foundational governance document developed through community participation [61](https://www.essentialcardano.io/search?category=faq&tags=Voltaire). The Essential Cardano content base references the constitutional convention process and interim constitution as steps in the Voltaire rollout [61](https://www.essentialcardano.io/search?category=faq&tags=Voltaire). The constitution establishes principles that constrain governance actions on-chain.

### Governance Tools and Infrastructure

Cardano.org's governance section provides an overview of how Cardano governance works, tools for delegating voting power to a DRep, resources for becoming a DRep, and governance tools for transparent, community-driven decisions [28](https://cardano.org/stake-pool-delegation/). The gov.tools platform enables ada holders to participate in on-chain governance actions including voting and DRep registration.

**Intersect MBO** (Member-Based Organization) is a key institution in the Voltaire ecosystem. Intersect is referenced in community channels listings [46](https://www.essentialcardano.io/community) and in the Essential Cardano tag index [61](https://www.essentialcardano.io/search?category=faq&tags=Voltaire). Intersect maintains its own Twitter and LinkedIn presence for governance-related announcements [46](https://www.essentialcardano.io/community).

### Beyond MVG: Continued Governance Evolution

Essential Cardano published a series of "Beyond MVG" progress reports and a roadmap article in late 2025 and early 2026, documenting Cardano governance's evolution beyond the Minimum Viable Governance milestone [69](https://www.essentialcardano.io/search?category=article&tags=Voltaire). The Beyond MVG roadmap is also illustrated in an infographic published October 2025 [64](https://www.essentialcardano.io/search?category=infographic&tags=Voltaire).

The Essential Cardano Voltaire search index lists articles, infographics, and FAQ content — including "What is Cardano governance about?" — providing an entry point for learners exploring governance in depth [61](https://www.essentialcardano.io/search?category=faq&tags=Voltaire).

### Section References

[13](https://cips.cardano.org/) — Cardano Improvement Proposals
[20](https://docs.cardano.org/pioneer-programs/education) — Cardano Docs Input Output Education
[26](https://cardano.org/research/) — Cardano Research
[28](https://cardano.org/stake-pool-delegation/) — Cardano Stake Pool Delegation
[46](https://www.essentialcardano.io/community) — Essential Cardano Community Channels
[61](https://www.essentialcardano.io/search?category=faq&tags=Voltaire) — Essential Cardano Voltaire FAQ Index
[64](https://www.essentialcardano.io/search?category=infographic&tags=Voltaire) — Essential Cardano Voltaire Infographic Index
[69](https://www.essentialcardano.io/search?category=article&tags=Voltaire) — Essential Cardano Voltaire Article Index
[78](https://resources.cryptocompare.com/asset-management/12/1741690659365.pdf) — Why Cardano — Early Vision Paper


## Chapter 6: Safety and Security

The Cardano network is public and permissionless, which means legitimate projects and scams alike can operate on it [25](https://cardano.org/common-scams/). As artificial intelligence improves, scams are becoming more sophisticated [25](https://cardano.org/common-scams/). Understanding the most common attack vectors is a prerequisite for safe participation.

### The Absolute Rule: Seed Phrase Protection

The recovery phrase (seed words) is the single most important secret in any self-custodial setup. If someone gains access to a user's seed words, they can take full control of the wallet — no spending password provides protection once seed words are known. Once ada is stolen, it is gone forever with no way to recover it [25](https://cardano.org/common-scams/).

Legitimate people on forums and community channels will **never** ask for passwords, recovery phrases, or private keys. Legitimate support representatives will **never** contact users first via private message [25](https://cardano.org/common-scams/).

### Common Scam Types

**Ada Giveaway Scam.** Scammers promise to double ada if a user sends them funds first. These scams frequently feature fake live streams of Charles Hoskinson or other well-known personalities, mimicking genuine events and including a wallet address. Legitimate giveaways never ask for money upfront; once sent, ada is gone forever [25](https://cardano.org/common-scams/).

**Phishing Attacks.** Phishing scams use fake websites, apps, or emails designed to steal sensitive information such as wallet credentials or the recovery phrase. Fraudulent sites often closely mimic popular wallets such as Typhon, VESPR, or Eternl. Users should double-check URLs against actual wallet websites and never share a recovery phrase with anyone, including apparent "support" staff or "moderators" [25](https://cardano.org/common-scams/).

**Fake Investment Opportunities.** Fraudulent schemes promote fake projects claiming to be "Cardano-backed" or "ada-specific" with guaranteed high returns. Victims are urged to send ada to a wallet address. Legitimate projects never promise guaranteed returns; any unsolicited investment offer should be treated with skepticism [25](https://cardano.org/common-scams/).

**Fake Tech Support.** Fraudsters pose as official Cardano support representatives on social media, forums, or email. They often copy the profiles of real moderators and claim to fix wallet issues or troubleshoot problems, then ask for the recovery phrase or private keys. This scam is especially common when new users ask wallet questions in community channels [25](https://cardano.org/common-scams/).

**Rug Pulls.** Fraudulent projects launch on Cardano with big promises and extensive marketing, collect a significant amount of ada from investors, then disappear. Because Cardano is a public, permissionless Layer 1 blockchain, anyone can launch a project on it [25](https://cardano.org/common-scams/). Protective steps include researching the project team's credentials and reputation, checking for audits or transparent documentation, and avoiding projects with anonymous teams or unrealistic promises [25](https://cardano.org/common-scams/).

### Safe Practices Summary

The following table summarises protective actions for each scam type [25](https://cardano.org/common-scams/):

| Scam Type | Key Warning Sign | Protective Action |
|-----------|-----------------|-------------------|
| Giveaway | Asks you to send ada first | Never send ada expecting more back |
| Phishing | URL differs from official wallet site | Verify URLs; consider hardware wallets; use 2FA where possible |
| Fake investment | Promises guaranteed returns | Research thoroughly; be skeptical of unsolicited offers |
| Fake support | Reaches out via private message | Ignore; legitimate support never DMs first or asks for seed words |
| Rug pull | Anonymous team; unrealistic promises | Check audits; only acquire utility tokens when needed; use community scam reports |

Users who believe they have encountered a scam can report it in the Cardano Forum scam-reporting channel [25](https://cardano.org/common-scams/).

### Verifying Wallet Authenticity

Phishing sites often mimic wallet landing pages pixel-for-pixel. Before downloading or interacting with a wallet, verify the URL matches the official site listed on the Cardano Wallet Finder [27](https://cardano.org/wallets/). For additional security, hardware wallets store private keys on a dedicated offline device, greatly reducing the risk from phishing sites or malware on a computer [27](https://cardano.org/wallets/). (See [Chapter 2: Cardano Wallets](#chapter-2-cardano-wallets) for the wallet comparison table and hardware wallet options.)

### Section References

[25](https://cardano.org/common-scams/) — Common Cardano Scams, How to Stay Safe
[27](https://cardano.org/wallets/) — Cardano Wallet Finder, Compare and Choose the Best Wallet


## Chapter 7: Next Steps and Community Resources

After learning Cardano's fundamentals, participants find a rich support infrastructure designed to sustain continued learning, answer questions, and enable active participation [11](https://docs.cardano.org/). Official documentation, community channels, an ambassador network, educational platforms, and a community code of conduct together form the onboarding infrastructure that carries beginners from first exposure to confident participation [46](https://www.essentialcardano.io/community).

### Official Documentation: The Cardano Docs Portal

The Cardano Docs portal at docs.cardano.org is the primary reference for technical and conceptual documentation. It organizes content into five major sections: About Cardano (fundamentals and concepts), Developer Resources (smart contracts, SDKs, API references), Stake Pool Operations (operator guides), Testnets (preview and pre-production environments), and Education (pioneer programs and learning paths) [11](https://docs.cardano.org/).

The portal links directly to key community support resources: Support via Zendesk, Essential Cardano (content hub), Cardano Stack Exchange (Q&A), the Ambassador Program, and the CIPs repository [11](https://docs.cardano.org/). Smart contract documentation covers three languages: Plinth (Haskell-based), Marlowe (domain-specific for financial contracts), and Aiken (modern functional language) [11](https://docs.cardano.org/). Scalability documentation addresses Hydra (layer-2 state channels), Mithril (lightweight chain synchronization), and Leios (next-generation throughput scaling) [11](https://docs.cardano.org/).

All documentation is published under the Creative Commons CC BY 4.0 license, meaning content can be freely shared and adapted with attribution [11](https://docs.cardano.org/).

### Community Channels: Where to Connect

The Cardano community operates across multiple platforms serving different interaction modes [46](https://www.essentialcardano.io/community):

| Channel | Platform | Purpose |
|---------|----------|---------|
| IOHK Twitter / X | Social | Announcements |
| IOHK LinkedIn | Professional | Announcements |
| IOHK YouTube | Video | Announcements and education |
| IOHK Reddit (r/cardano) | Reddit | General discussion |
| Cardano Community Discord | Discord | Education and discussion |
| IOG Technical Community Discord | Discord | Developer education |
| Cardano Announcements | Telegram | Official announcements |
| IO SPO Announcements | Telegram | Stake pool operator news |
| IO DEV Announcements | Telegram | Developer news |
| Cardano Stack Exchange | Q&A | Technical questions |
| Cardano SPO Reddit (r/CardanoStakePools) | Reddit | Stake pool discussion |
| Cardano DEV Reddit (r/CardanoDevelopers) | Reddit | Developer discussion |
| Cardano GitHub | GitHub | Open-source development |
| SPO Digest | Newsletter | Stake pool operator updates |
| Catalyst Announcements | Telegram | Project Catalyst news |
| Catalyst Discord | Discord | Funding community |
| Intersect Twitter / LinkedIn | Social | Governance body announcements |

Project Catalyst is described as "the world's largest decentralized innovation fund — a framework for the Cardano community to turn ideas into impactful real-world projects" [46](https://www.essentialcardano.io/community). Intersect, the member-based organization coordinating Cardano's open development, maintains its own Twitter and LinkedIn presence for governance-related updates [46](https://www.essentialcardano.io/community).

### The Ambassador Program

The Cardano Ambassador Program, established in 2018, is the structured pathway for community members who want to contribute formally to the ecosystem [12](https://cardano.org/ambassadors/). As of the program's current state, there are 84 ambassadors operating across 37 countries and communicating in 17 languages [12](https://cardano.org/ambassadors/).

Ambassadors contribute in seven recognized categories [12](https://cardano.org/ambassadors/):

| Contribution Type | Description |
|-------------------|-------------|
| Content Creation | Articles, videos, educational materials |
| Meetups & Events | Regional gatherings and community events |
| Education & Advocacy | Teaching and representing Cardano |
| Business Development | Partnerships and ecosystem growth |
| Software Development | Code contributions, including CIP authorship |
| Translations | Making Cardano content multilingual |
| Moderation | Managing 50 channels across 9 platforms |

Program benefits include a unique ambassador badge, early and exclusive access to Cardano developments, networking with the core teams, and access to promotional materials and funding [12](https://cardano.org/ambassadors/). New ambassadors begin by participating on the Cardano Forum, progressing through levels as their contributions accumulate [12](https://cardano.org/ambassadors/).

### Community Code of Conduct

All participants in official Cardano channels are bound by the Community Code of Conduct. The standard is clear: "All participants in the community are expected to act lawfully, honestly, ethically and in the best interest of the project" [24](https://cardano.org/community-code-of-conduct/). Trading or shilling of ADA or other tokens in community channels is prohibited [24](https://cardano.org/community-code-of-conduct/).

Prohibited behaviors include name-calling, ad hominem attacks, and responding to the tone of a post rather than its content [24](https://cardano.org/community-code-of-conduct/). The violation system applies a graduated response: a first violation results in a 24-hour suspension, a second violation carries a suspension of up to one month, and a third violation results in a permanent ban across all official Cardano channels [24](https://cardano.org/community-code-of-conduct/).

### Essential Cardano and IOG Content Hub

Essential Cardano (essentialcardano.io) serves as an aggregation hub for articles, videos, FAQs, infographics, podcasts, developer resources, a glossary, and development updates [45](https://www.essentialcardano.io/podcast). The content taxonomy spans hundreds of tags covering every aspect of the Cardano ecosystem, from Aiken and Blockfrost to governance, DeFi, NFTs, and identity [45](https://www.essentialcardano.io/podcast).

IOG's news portal publishes articles, research papers, press releases, events, and thought leadership content. As of April 2026, the portal contains 498 items across those content types, with Blog Posts (453) constituting the majority [42](https://www.iog.io/news?type=article). Prolific authors include Olga Hryniuk (48 articles), Tim Harrison (32), Fernando Sanchez (31), and Charles Hoskinson (25) [42](https://www.iog.io/news?type=article). Recent topics include USDCx deployment, Hydra adoption, Ouroboros Omega, Leios scaling, and inter-chain connectivity [42](https://www.iog.io/news?type=article).

The Cardano Developer Portal additionally hosts developer-focused documentation with a separate community section covering Stack Exchange, the Cardano Forum developers section, and links to hackathons and grants programs [14](https://developers.cardano.org/).

### Section References

[11](https://docs.cardano.org/) — Cardano Docs Portal
[12](https://cardano.org/ambassadors/) — Cardano Ambassador Program
[14](https://developers.cardano.org/) — Cardano Developer Portal
[24](https://cardano.org/community-code-of-conduct/) — Cardano Community Code of Conduct
[42](https://www.iog.io/news?type=article) — IOG News Articles
[45](https://www.essentialcardano.io/podcast) — Essential Cardano Podcasts
[46](https://www.essentialcardano.io/community) — Essential Cardano Community Channels



## Sources

[1] Cardano Foundation Official Homepage — https://cardanofoundation.org/
[2] Cardano Foundation Accelerator & Venture Partners — https://cardanofoundation.org/partners?type=Accelerator+%26+Venture
[3] Cardano Foundation Digital Product Passport — https://cardanofoundation.org/solutions/digital-product-passport
[5] Cardano Foundation Enterprise Partners — https://cardanofoundation.org/partners?type=Enterprise
[6] Cardano Foundation Decentralized Storage — https://cardanofoundation.org/solutions/decentralized-storage
[8] Cardano Foundation Traceability Solution — https://cardanofoundation.org/solutions/traceability
[9] Cardano Foundation Authenticity Solution — https://cardanofoundation.org/solutions/authenticity
[11] Cardano Docs Portal — https://docs.cardano.org/
[12] Cardano Ambassador Program — https://cardano.org/ambassadors/
[13] Cardano Improvement Proposals — https://cips.cardano.org/
[14] Cardano Developer Portal — https://developers.cardano.org/
[16] Cardano Docs: Operating a Stake Pool — https://docs.cardano.org/stake-pool-operators/operating-a-stake-pool
[17] Cardano Docs: Community Education Initiatives — https://docs.cardano.org/pioneer-programs/community-education
[18] Cardano Docs: Introduction to Cardano — https://docs.cardano.org/about-cardano/introduction
[19] Cardano Developer Portal: Builder Tools — https://developers.cardano.org/tools/
[20] Cardano Docs: Input Output Education Programs — https://docs.cardano.org/pioneer-programs/education
[21] Cardano.org Homepage — https://cardano.org/
[22] What Is ADA — https://cardano.org/what-is-ada/
[23] Get Started with Cardano — https://cardano.org/get-started/
[24] Cardano Community Code of Conduct — https://cardano.org/community-code-of-conduct/
[25] Common Cardano Scams: How to Stay Safe — https://cardano.org/common-scams/
[26] Cardano Research — https://cardano.org/research/
[27] Cardano Wallet Finder — https://cardano.org/wallets/
[28] Cardano Stake Pool Delegation — https://cardano.org/stake-pool-delegation/
[29] Cardano Insights: On-Chain Data and Analytics — https://cardano.org/insights/
[30] Where to Get ADA — https://cardano.org/where-to-get-ada/
[31] Cardano Apps Directory — https://cardano.org/apps/
[35] IOG: The Account Model: A Trillion Dollar Mistake — https://www.iog.io/news/the-account-model-a-trillion-dollar-mistake
[39] IOG: Always Secure — Next-Level Smart Contract Verification on Cardano — https://www.iog.io/news/always-secure-and-safer-than-ever-thanks-to-next-level-smart-contract-verification-on-cardano
[40] IOG: Input Output Launches Blockchain Technology Laboratory at Archimedes — https://www.iog.io/news/input-output-launches-new-blockchain-technology-laboratory-at-archimedes
[41] IOG: Tokyo Diaries — Where It All Began — https://www.iog.io/news/tokyo-diaries-where-it-all-began
[42] IOG News Articles — https://www.iog.io/news?type=article
[44] Essential Cardano — https://www.essentialcardano.io/
[45] Essential Cardano Podcasts — https://www.essentialcardano.io/podcast
[46] Essential Cardano Community Channels — https://www.essentialcardano.io/community
[58] Essential Cardano: Liquid Staking FAQ — https://www.essentialcardano.io/search?category=faq&tags=Liquid+Staking
[61] Essential Cardano: Voltaire FAQ — https://www.essentialcardano.io/search?category=faq&tags=Voltaire
[64] Essential Cardano: Voltaire Infographics — https://www.essentialcardano.io/search?category=infographic&tags=Voltaire
[69] Essential Cardano: Voltaire Articles — https://www.essentialcardano.io/search?category=article&tags=Voltaire
[77] Kiayias et al. — Ouroboros: A Provably Secure Proof-of-Stake Blockchain Protocol (peer-reviewed) — https://eprint.iacr.org/2016/889.pdf
[78] Why Cardano — Early Vision Paper — https://resources.cryptocompare.com/asset-management/12/1741690659365.pdf
[79] Kiayias & Russell — Ouroboros-BFT: A Simple Byzantine Fault Tolerant Consensus Protocol (peer-reviewed) — https://eprint.iacr.org/2018/1049.pdf
