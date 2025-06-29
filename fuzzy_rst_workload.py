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
            classes.setdefault(key, set()).add(row[self.decision_col])
        return classes

    def discernibility_matrix(self):
        matrix = []
        indices = self.df.index.tolist()
        for i, j in combinations(indices, 2):
            row_i = self.df.loc[i]
            row_j = self.df.loc[j]
            if row_i[self.decision_col] != row_j[self.decision_col]:
                diff = [col for col in self.condition_cols if row_i[col] != row_j[col]]
                if diff:
                    matrix.append(set(diff))
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
            decisions = group[self.decision_col].unique()
            if len(decisions) == 1:
                rule = dict(zip(cols, conds if isinstance(conds, tuple) else (conds,)))
                rules.append((rule, decisions[0]))
        return rules

    def run_all(self):
        print("🔎 Computing equivalence classes...")
        eq_class = self.equivalence_classes()
        print(f"🧩 Found {len(eq_class)} equivalence classes.")

        print("📐 Building discernibility matrix...")
        matrix = self.discernibility_matrix()
        print(f"🔍 {len(matrix)} discernibility sets generated.")

        print("🧠 Computing reduct...")
        reduct = self.compute_reduct(matrix)
        print(f"🧮 Reduct: {reduct}")

        print("📜 Generating rules from reduct...")
        rules = self.generate_rules(reduct)
        print(f"📘 {len(rules)} decision rules extracted.")

        return {
            'equivalence_class': eq_class,
            'discernibility_matrix': matrix,
            'reduct': reduct,
            'rules': rules
        }

def classify(cpu, mem):
    if cpu == 'High' or mem == 'High':
        return 'Overutilized'
    elif cpu == 'Medium' and mem == 'Medium':
        return 'Optimal'
    else:
        return 'Underutilized'

def main():
    # Load data
    file_path = "Cloud Workload Job Traces for Resource Forecasting.csv"
    df = pd.read_csv(file_path)

    # Fuzzyfication
    df['CPU_Level'] = pd.cut(df['Used_CPUs'], bins=[-1, 0.5, 1.5, float('inf')], labels=['Low', 'Medium', 'High'])
    df['Mem_Level'] = pd.cut(df['Used_Memory(MB)'], bins=[-1, 10000, 20000, float('inf')], labels=['Low', 'Medium', 'High'])
    df['Exec_Level'] = pd.cut(df['Execution_Time(Seconds)'], bins=3, labels=['Short', 'Medium', 'Long'])

    # Decision
    df['Resource_Status'] = df.apply(lambda r: classify(r['CPU_Level'], r['Mem_Level']), axis=1)

    # Run Rough Set
    rst = RoughSetModule(df, ['CPU_Level', 'Mem_Level', 'Exec_Level'], 'Resource_Status')
    results = rst.run_all()

    # Export result
    df.to_csv("output_fuzzy_results.csv", index=False)
    pd.DataFrame([
        {**rule, 'Resource_Status': decision}
        for rule, decision in results['rules']
    ]).to_csv("output_rst_rules.csv", index=False)

    print("\n✅ Saved fuzzy results to 'output_fuzzy_results.csv'")
    print("✅ Saved RST rules to 'output_rst_rules.csv'")

if __name__ == "__main__":
    main()

