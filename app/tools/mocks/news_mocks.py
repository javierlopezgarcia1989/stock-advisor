# app/tools/mocks/news_mocks.py

POSITIVE_NEWS_MOCK = {
    "symbol": "AAPL",
    "articles": [
        {
            "title": "Apple's new iPhone smashes sales records",
            "content": "Apple announced record-breaking sales for its new iPhone model, with demand exceeding all expectations. Analysts are upgrading their price targets.",
            "url": "http://example.com/positive1"
        },
        {
            "title": "AAPL announces revolutionary new M-series chip",
            "content": "The new chip is set to redefine the industry, offering unprecedented performance and efficiency. Stock prices surged on the news.",
            "url": "http://example.com/positive2"
        },
        {
            "title": "Apple's Vision Pro 2 is coming sooner than expected",
            "content": "Sources inside Apple say that the next version of the Vision Pro will be released in early 2025, with a lower price point.",
            "url": "http://example.com/positive3"
        },
        {
            "title": "Apple reports strong growth in its services division",
            "content": "The App Store, Apple Music, and iCloud have all shown significant growth in the last quarter, contributing to a rosy outlook for the company.",
            "url": "http://example.com/positive4"
        },
        {
            "title": "Warren Buffett increases his stake in Apple",
            "content": "Berkshire Hathaway has purchased an additional $1 billion worth of Apple stock, signaling strong confidence in the company's future.",
            "url": "http://example.com/positive5"
        }
    ]
}

NEGATIVE_NEWS_MOCK = {
    "symbol": "TSLA",
    "articles": [
        {
            "title": "Tesla faces major recall over safety concerns",
            "content": "A major safety flaw has been discovered in Tesla's latest model, forcing a massive recall. The news has sent the stock price tumbling.",
            "url": "http://example.com/negative1"
        },
        {
            "title": "Production delays plague Tesla's new factory",
            "content": "Tesla is facing significant production delays at its new Gigafactory, which will impact delivery targets for the year.",
            "url": "http://example.com/negative2"
        },
        {
            "title": "Elon Musk's latest tweets cause controversy",
            "content": "The CEO's recent social media activity has drawn criticism from investors and the public, leading to a drop in stock value.",
            "url": "http://example.com/negative3"
        },
        {
            "title": "Competition heats up in the EV market",
            "content": "Legacy automakers are catching up to Tesla, with several new electric vehicle models set to launch this year.",
            "url": "http://example.com/negative4"
        },
        {
            "title": "Tesla misses quarterly delivery estimates",
            "content": "The company delivered fewer vehicles than analysts expected in the last quarter, raising concerns about demand.",
            "url": "http://example.com/negative5"
        }
    ]
}

NEUTRAL_NEWS_MOCK = {
    "symbol": "GOOGL",
    "articles": [
        {
            "title": "Google releases annual developer survey results",
            "content": "Google has published the results of its annual developer survey, showing trends in programming languages and tools.",
            "url": "http://example.com/neutral1"
        },
        {
            "title": "Alphabet Inc. to hold its annual shareholder meeting next month",
            "content": "The company announced the date for its annual shareholder meeting, where standard corporate matters will be discussed.",
            "url": "http://example.com/neutral2"
        },
        {
            "title": "Google updates its privacy policy",
            "content": "The tech giant has made changes to its privacy policy, which will take effect next month. The changes are minor and not expected to have a major impact.",
            "url": "http://example.com/neutral3"
        },
        {
            "title": "Google Maps adds new features for cyclists",
            "content": "The latest update to Google Maps includes new features for cyclists, such as real-time bike-sharing information.",
            "url": "http://example.com/neutral4"
        },
        {
            "title": "Google's self-driving car project, Waymo, reaches 10 million miles",
            "content": "Waymo, the self-driving car company under Alphabet, has reached a major milestone of 10 million miles driven on public roads.",
            "url": "http://example.com/neutral5"
        }
    ]
}

MIXED_NEWS_MOCK = {
    "symbol": "MSFT",
    "articles": [
        {
            "title": "Microsoft beats earnings expectations but guidance disappoints",
            "content": "Microsoft reported strong quarterly earnings, but its forward-looking guidance was weaker than analysts had hoped, causing some uncertainty.",
            "url": "http://example.com/mixed1"
        },
        {
            "title": "New Surface laptop receives praise, but sales are slow",
            "content": "The new Surface laptop has been well-received by critics for its innovative design, but initial sales figures have been sluggish.",
            "url": "http://example.com/mixed2"
        },
        {
            "title": "Microsoft's acquisition of Activision Blizzard faces regulatory hurdles",
            "content": "The massive acquisition is being scrutinized by regulators in the US and Europe, which could delay or even block the deal.",
            "url": "http://example.com/mixed3"
        },
        {
            "title": "Azure cloud services show strong growth",
            "content": "Microsoft's cloud computing platform, Azure, continues to grow at a rapid pace, challenging Amazon Web Services for market leadership.",
            "url": "http://example.com/mixed4"
        },
        {
            "title": "Microsoft announces new AI-powered features for Office 365",
            "content": "The company is integrating artificial intelligence into its popular productivity suite, which could boost user engagement and retention.",
            "url": "http://example.com/mixed5"
        }
    ]
}


ALL_MOCKS = {
    "POSITIVE": POSITIVE_NEWS_MOCK,
    "NEGATIVE": NEGATIVE_NEWS_MOCK,
    "NEUTRAL": NEUTRAL_NEWS_MOCK,
    "MIXED": MIXED_NEWS_MOCK,
    "DEFAULT": MIXED_NEWS_MOCK 
}
