from tests.pages.unit_page import UnitPage


class UnitTwoPage(UnitPage):
    UNIT_NUMBER = 2
    TITLE = "Economic Growth"
    SUBTITLE = "What makes economies grow \u2014 and what it costs"
    INTRODUCTION = (
        "Learn about economic growth: what it means, why it matters, and what problems it can create. "
        "Understand how countries measure progress, the costs of growing, "
        "and how technology and employment are connected."
    )
    TABS = (
        "Intro", "Key Ideas", "Growth Drivers", "Dictionary", "Timeline",
        "Reading", "Questions", "Media Lab", "Crossword", "Case Study",
        "Perspectives", "Labour",
    )
    DEFINITIONS = (
        ("Growth", "When a country produces more goods and services than before."),
        ("Benefits", "The good things that come from growth: more jobs, more income, better life."),
        ("Costs", "The bad things that can come from growth: pollution, inequality, job losses."),
    )
