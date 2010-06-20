
from pygbot.games.cardutil import Deck

class FluxxDeck(Deck):
    def make_deck(self):
        from pygbot.games.fluxx import goals, rules, keepers, actions

        def make_rules():
            R  = [rules.BasicRules()]
            R += (rules.DrawRuleCard(amount) for amount in (2, 3, 4, 5))
            R += (rules.PlayRuleCard(amount) for amount in (2, 3, 4))
            R += (rules.PlayAllRuleCard())
            R += (rules.HandLimitRuleCard(amount) for amount in (0, 1, 2))
            R += (rules.KeeperLimitRuleCard(amount) for amount in (2, 3, 4))
            R += (rules.NoHandBonusRuleCard(), rules.PoorBonusRuleCard(), rules.RichBonusRuleCard())
            R += (rules.InflationRuleCard(), rules.ReverseOrderRuleCard())
            R += (rules.FirstPlayRandomRuleCard(), rules.DoubleAgendaRuleCard())
            return R

        def make_keepers():
            def m(t):
                if isinstance(t, str):
                    return t,
                return t

            return [keepers.KeeperCard(*m(t)) for t in ("Bread", "Chocolate",  "Cookies",
                                                "Dreams", "Love", "Milk", "Money",
                                                "Peace", "Sleep", ("Television", "TV"),
                                                "The Brain", "The Cosmos", "The Eye",
                                                "The Moon", "The Party", "The Rocket",
                                                "The Sun", "The Toaster", "Time")] + \
                   [keepers.CreeperCard("Radioactive Potato", "Any time the Goal changes, " +
                                "move this card in the counter-turn direction."),
                    keepers.CreeperCard("Death", "If you have this at the start of your " +
                                "turn, discard something else you have in play " +
                                "(a Keeper or a Creeper). You may discard this " +
                                 "anytime it stands alone."),
                    keepers.CreeperCard("Taxes", "If you have Money on the table, " +
                                "discard both that and this."),
                    keepers.CreeperCard("War")]

        def make_goals():
            return [goals.KeeperComboGoalCard("Rocket Science", "TR", "TB"),
                    goals.KeeperComboGoalCard("Time is Money", "TI", "MO"),
                    goals.KeeperComboGoalCard("War = Death", "WA", "DE"),
                    goals.KeeperComboGoalCard("Winning the Lottery", "DR", "MO"),
                    goals.KeeperComboGoalCard("Squishy Chocolate", "TS", "CH"),
                    goals.KeeperComboGoalCard("Milk and Cookies", "MI", "CO"),
                    goals.KeeperComboGoalCard("Rocket to the Moon", "TR", "TM"),
                    goals.KeeperComboGoalCard("Hearts and Minds", "LO", "TB"),
                    goals.KeeperComboGoalCard("The Appliances", "TT", "TV"),
                    goals.KeeperComboGoalCard("Hippyism", "PE", "LO"),
                    goals.KeeperComboGoalCard("Night and Day", "TM", "TS"),
                    goals.KeeperComboGoalCard("Baked Goods", "BR", "CO"),
                    goals.KeeperComboGoalCard("Bed Time", "SL", "TI"),
                    goals.KeeperComboGoalCard("Death by Chocolate", "DE", "CH"),
                    goals.KeeperComboGoalCard("Toast", "BR", "TT"),
                    goals.KeeperComboGoalCard("Chocolate Cookies", "CH", "CO"),
                    goals.KeeperComboGoalCard("Chocolate Milk", "CH", "MI"),
                    goals.KeeperComboGoalCard("Dreamland", "SL", "DR"),
                    goals.KeeperComboGoalCard("Interstellar Spacecraft", "TR", "TC"),
                    goals.KeeperComboGoalCard("Star Gazing", "TC", "TE"),
                    goals.KeeperComboGoalCard("The Mind's Eye", "TB", "TE"),
                    goals.KeeperComboGoalCard("Dough", "BR", "MO"),
                    goals.KeeperComboGoalCard("All That Is Certain", "DE", "TA"),
                    # Custom ones
                    # KeeperComboGoalCard("A Good Investment", "TI", "MO", "TB"),
                    # KeeperComboGoalCard("Gluttony", "MI", "CH", "BR", "CO"),
                    goals.FiveKeepers(),
                    goals.TenCardsInHand(),
                    goals.ExclusionKeeperGoalCard("The Brain (no TV)", "TB", "TV"),
                    goals.ExclusionKeeperGoalCard("Peace (no War)", "PE", "WA"),
                    goals.PartySnacks(),
                    goals.AllYouNeedIsLove()]

        def make_actions():
            return [actions.EverybodyGetsOne(),
                    actions.Jackpot(),
                    actions.TakeAnotherTurn(),
                    actions.NoLimits(),
                    actions.TrashRule(),
                    actions.TrashSomething(),
                    actions.StealSomething(),
                    actions.DiscardDraw(),
                    actions.EmptyTrash(),
                    actions.UseWhatYouTake(),
                    actions.RulesReset(),
                    actions.DrawTwoUseThem()]

        return make_rules() + make_keepers() + make_goals() + make_actions()


if __name__ == "__main__":
    # Test the FluxxDeck
    deck = FluxxDeck()
    for card in deck.cards:
        print card.card_info, "\n\n"
