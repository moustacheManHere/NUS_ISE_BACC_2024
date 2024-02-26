import random
import pandas as pd

recipe_list = ["A", "B", "C", "D", "E"]

processing_time = {"A": 4, "B": 3, "C": 5, "D": 2, "E": 6}

recipe_selection = {
    1: ["A", "B", "D"],
    2: ["C", "E"],
    3: ["B", "D", "E"],
    4: ["B", "C"],
    5: ["A", "C", "D"],
}

recipe_switch_downtime = {
    "A": [0, 1, 1, 3, 1],
    "B": [1, 0, 1, 1, 2],
    "C": [1, 1, 0, 1, 2],
    "D": [3, 1, 1, 0, 2],
    "E": [1, 2, 2, 2, 0],
}

recipe_material = {
    "A": {"X": 24},
    "B": {"Y": 22},
    "C": {"X": 6, "Y": 9},
    "D": {"X": 20, "Y": 15, "Z": 6},
    "E": {"Y": 8, "Z": 4},
}


class Lot:
    def __init__(self, id: int, recipe_list: list) -> None:
        self.id = id
        self.step = 0
        self.hour = 0
        self.max_hour = processing_time[recipe_list[0]]
        self.recipe_list = recipe_list
        self.recipe = recipe_list[0]

    def next_hour(self):
        self.hour += 1
        if self.hour == self.max_hour:
            return True
        return False

    def next_step(self):
        self.step += 1
        if self.step == 5:
            return
        self.recipe = self.recipe_list[self.step]
        self.max_hour = processing_time[self.recipe]
        self.hour = 0


class Equipment:
    def __init__(self, name: str, capabilities: list) -> None:
        self.name = name
        self.capabilities = capabilities
        self.status = "IDLE"
        self.processing_lot: Lot = None
        self.switching_cooldown = 0

    def check_capability(self, item: str):
        return item in self.capabilities

    def process_lot(self, lot: Lot):
        if self.status != lot.recipe and self.status not in ["IDLE", "SWITCH"]:
            self.switching_cooldown = recipe_switch_downtime[self.status][
                recipe_list.index(lot.recipe)
            ]
            self.status = "SWITCH"
        else:
            self.status = lot.recipe
        self.processing_lot = lot


class Material:
    def __init__(self, pricing_tier: list) -> None:
        self.pricing_tier = pricing_tier
        self.amount = 0
        self.total_used = 0

    def topup(self, amount):
        self.amount += amount
        if amount < 51:
            return amount * self.pricing_tier[0]
        elif amount < 501:
            return amount * self.pricing_tier[1]
        return amount * self.pricing_tier[2]

    def use(self, amount):
        self.amount -= amount
        self.total_used += amount
        return amount


def main():
    revenue = cost = 0

    alpha = Equipment("Alpha", ["A", "B", "D", "E"])
    beta = Equipment("Beta", ["B", "C", "E"])
    gamma = Equipment("Gamma", ["A", "C", "D"])

    materials = {
        "X": Material([200, 190, 175]),
        "Y": Material([300, 275, 250]),
        "Z": Material([240, 220, 205]),
    }

    idle_lots = []

    # first hour set up
    alpha.process_lot(Lot(1, ["A", "C", "E", "C", "C"]))
    for material, amount in recipe_material[alpha.status].items():
        materials[material].use(amount)

    beta.process_lot(Lot(2, ["B", "C", "E", "C", "C"]))
    for material, amount in recipe_material[beta.status].items():
        materials[material].use(amount)

    gamma.process_lot(Lot(3, ["A", "C", "E", "C", "C"]))
    for material, amount in recipe_material[gamma.status].items():
        materials[material].use(amount)

    lot_id = 4
    print("\tAlpha\t\tBeta\t\t\tGamma")
    print("Hours Lot Recipe Step Lot Recipe Step Lot Recipe Step")
    print(
        f"1\t{alpha.processing_lot.id}\t{alpha.status}\t{alpha.processing_lot.step}\t{beta.processing_lot.id}\t{beta.status}\t{beta.processing_lot.step}\t{gamma.processing_lot.id}\t{gamma.status}\t{gamma.processing_lot.step}"
    )
    rows = [
        [
            1,
            alpha.processing_lot.id,
            alpha.status,
            alpha.processing_lot.step + 1,
            beta.processing_lot.id,
            beta.status,
            beta.processing_lot.step + 1,
            gamma.processing_lot.id,
            gamma.status,
            gamma.processing_lot.step + 1,
        ]
    ]

    # from 2nd hour to 168th hour
    for hour in range(1, 168):

        # for each equipment, their lot will gain one hour, and if step is completed, then...
        if alpha.status == "SWITCH":
            alpha.switching_cooldown -= 1
            alpha_finished = False
            if alpha.switching_cooldown == 0:
                alpha.status = alpha.processing_lot.recipe
        else:
            alpha_finished = alpha.processing_lot.next_hour()

        if beta.status == "SWITCH":
            beta.switching_cooldown -= 1
            beta_finished = False
            if beta.switching_cooldown == 0:
                beta.status = beta.processing_lot.recipe
        else:
            beta_finished = beta.processing_lot.next_hour()

        if gamma.status == "SWITCH":
            gamma.switching_cooldown -= 1
            gamma_finished = False
            if gamma.switching_cooldown == 0:
                gamma.status = gamma.processing_lot.recipe
        else:
            gamma_finished = gamma.processing_lot.next_hour()

        if alpha_finished:
            alpha.processing_lot.next_step()

            if alpha.processing_lot.step == 5:
                revenue += 40000
                alpha.processing_lot = None

            else:
                idle_lots.append(alpha.processing_lot)
                alpha.processing_lot = None

            # now to look for the next lot, scan through and prioritise on the lot with the same recipe, to avoid switching
            unassigned = True
            if idle_lots:
                for i, lot in enumerate(idle_lots):
                    if lot.recipe == alpha.status:
                        alpha.process_lot(lot)
                        idle_lots.pop(i)
                        for material, amount in recipe_material[alpha.status].items():
                            materials[material].use(amount)
                        unassigned = False
                        break

            # if don't have, pick up the first idle lot, but have to switch
            if idle_lots and unassigned:
                for i, lot in enumerate(idle_lots):
                    if alpha.check_capability(lot.recipe):
                        alpha.process_lot(lot)
                        idle_lots.pop(i)
                        for material, amount in recipe_material[lot.recipe].items():
                            materials[material].use(amount)
                        unassigned = False
                        break

            # if idle lots is empty, assign a new lot
            if unassigned:
                alpha.process_lot(Lot(lot_id, ["A", "C", "E", "C", "C"]))
                for material, amount in recipe_material[lot.recipe].items():
                    materials[material].use(amount)
                lot_id += 1

        if beta_finished:
            beta.processing_lot.next_step()

            if beta.processing_lot.step == 5:
                revenue += 40000
                beta.processing_lot = None

            else:
                idle_lots.append(beta.processing_lot)
                beta.processing_lot = None

            # now to look for the next lot, scan through and prioritise on the lot with the same recipe, to avoid switching
            unassigned = True
            if idle_lots:
                for i, lot in enumerate(idle_lots):
                    if lot.recipe == beta.status:
                        beta.process_lot(lot)
                        idle_lots.pop(i)
                        for material, amount in recipe_material[beta.status].items():
                            materials[material].use(amount)
                        unassigned = False
                        break

            # if don't have, pick up the first idle lot, but have to switch
            if idle_lots and unassigned:
                for i, lot in enumerate(idle_lots):
                    if beta.check_capability(lot.recipe):
                        beta.process_lot(lot)
                        idle_lots.pop(i)
                        for material, amount in recipe_material[lot.recipe].items():
                            materials[material].use(amount)
                        unassigned = False
                        break

            # if idle lots is empty, assign a new lot
            if unassigned:
                beta.process_lot(Lot(lot_id, ["B", "C", "E", "C", "C"]))
                for material, amount in recipe_material[lot.recipe].items():
                    materials[material].use(amount)
                lot_id += 1

        if gamma_finished:
            gamma.processing_lot.next_step()

            if gamma.processing_lot.step == 5:
                revenue += 40000
                gamma.processing_lot = None

            else:
                idle_lots.append(gamma.processing_lot)
                gamma.processing_lot = None

            # now to look for the next lot, scan through and prioritise on the lot with the same recipe, to avoid switching
            unassigned = True
            if idle_lots:
                for i, lot in enumerate(idle_lots):
                    if lot.recipe == gamma.status:
                        gamma.process_lot(lot)
                        idle_lots.pop(i)
                        for material, amount in recipe_material[lot.recipe].items():
                            materials[material].use(amount)
                        unassigned = False
                        break

            # if don't have, pick up the first idle lot, but have to switch
            if idle_lots and unassigned:
                for i, lot in enumerate(idle_lots):
                    if gamma.check_capability(lot.recipe):
                        gamma.process_lot(lot)
                        idle_lots.pop(i)
                        for material, amount in recipe_material[lot.recipe].items():
                            materials[material].use(amount)
                        unassigned = False
                        break

            # if still unassgined, assign a new lot
            if unassigned:
                gamma.process_lot(Lot(lot_id, ["A", "C", "E", "C", "C"]))
                for material, amount in recipe_material[lot.recipe].items():
                    materials[material].use(amount)
                lot_id += 1

        print(
            f"{hour+1}\t{alpha.processing_lot.id}\t{alpha.status}\t{alpha.processing_lot.step}\t{beta.processing_lot.id}\t{beta.status}\t{beta.processing_lot.step}\t{gamma.processing_lot.id}\t{gamma.status}\t{gamma.processing_lot.step}"
        )
        rows.append(
            [
                hour + 1,
                "SWITCH" if alpha.status == "SWITCH" else alpha.processing_lot.id,
                alpha.status,
                "SWITCH" if alpha.status == "SWITCH" else alpha.processing_lot.step + 1,
                "SWITCH" if beta.status == "SWITCH" else beta.processing_lot.id,
                beta.status,
                "SWITCH" if beta.status == "SWITCH" else beta.processing_lot.step + 1,
                "SWITCH" if gamma.status == "SWITCH" else gamma.processing_lot.id,
                gamma.status,
                "SWITCH" if gamma.status == "SWITCH" else gamma.processing_lot.step + 1,
            ]
        )

    print()
    for bottle, item in materials.items():
        print(f"{bottle} used: {item.total_used} litres")
        cost += item.topup(item.total_used)

    print()
    print(f"Total cost: {cost}")
    print(f"Total revenue: {revenue}")
    print(f"Total profit: {revenue - cost}")

    results = pd.DataFrame(
        rows,
        columns=[
            "Hour",
            "Alpha lot",
            "Alpha recipe",
            "Alpha step",
            "Beta lot",
            "Beta recipe",
            "Beta step",
            "Gamma lot",
            "Gamma recipe",
            "Gamma step",
        ],
    )
    results.to_excel("result.xlsx")


if __name__ == "__main__":
    main()
