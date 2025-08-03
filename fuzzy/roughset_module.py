import pandas as pd
from itertools import combinations

class RoughSetModule:
    def __init__(self, df, condition_cols, decision_col):
        self.df = df
        self.condition_cols = condition_cols
        self.decision_col = decision_col

    def equivalence_classes(self):
        classes = {}
        for _, row in self.df.iterrows():
            key = tuple(row[col] for col in self.condition_cols)
            if key not in classes:
                classes[key] = set()
            classes[key].add(row[self.decision_col])
        return classes

    def discernibility_matrix(self):
        matrix = []
        for i, j in combinations(self.df.index, 2):
            row_i = self.df.loc[i]
            row_j = self.df.loc[j]
            if row_i[self.decision_col] != row_j[self.decision_col]:
                diff_attrs = [attr for attr in self.condition_cols if row_i[attr] != row_j[attr]]
                if diff_attrs:
                    matrix.append(set(diff_attrs))
        return matrix

    def compute_reduct(self, matrix):
        if not matrix:
            return set()
        return set.intersection(*matrix)

    def generate_rules(self, reduct_cols=None):
        cols = list(reduct_cols) if reduct_cols else self.condition_cols
        rules = []
        grouped = self.df.groupby(cols)
        for conds, group in grouped:
            decision_values = group[self.decision_col].unique()
            if len(decision_values) == 1:
                rule = dict(zip(cols, conds if isinstance(conds, tuple) else (conds,)))
                rules.append((rule, decision_values[0]))
        return rules

    def run_all(self):
        eq_class = self.equivalence_classes()
        matrix = self.discernibility_matrix()
        reduct = self.compute_reduct(matrix)
        rules = self.generate_rules(reduct if reduct else None)
        return {
            'equivalence_class': eq_class,
            'discernibility_matrix': matrix,
            'reduct': reduct,
            'rules': rules
        }
