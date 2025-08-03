from flask import Blueprint, render_template, request, redirect, url_for, flash
from apps import db
from apps.fuzzy.models import WorkloadData, WorkloadResult, RoughSetRule
from apps.fuzzy.forms import UploadCSVForm
import pandas as pd
from itertools import combinations

blueprint = Blueprint('fuzzy_blueprint', __name__, url_prefix='/fuzzy')

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

@blueprint.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadCSVForm()
    if request.method == 'POST' and form.validate_on_submit():
        file = form.file.data
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            for _, row in df.iterrows():
                db.session.add(WorkloadData(
                    job_id=row['Job_ID'],
                    submit_time=row['Submit_Time'],
                    start_time=row['Start_Time'],
                    end_time=row['End_Time'],
                    requested_cpus=row['Requested_CPUs'],
                    used_cpus=row['Used_CPUs'],
                    requested_memory=row['Requested_Memory(MB)'],
                    used_memory=row['Used_Memory(MB)'],
                    execution_time=row['Execution_Time(Seconds)'],
                    queue_wait_time=row['Queue_Wait_Time(Seconds)'],
                    user_id=row['User_ID'],
                    job_type=row['Job_Type'],
                    priority_level=row['Priority_Level'],
                    node_count=row['Node_Count'],
                    interarrival_time=row['Interarrival_Time']
                ))
            db.session.commit()
            flash("Data uploaded and stored successfully.")
            return redirect(url_for('fuzzy_blueprint.upload'))
        else:
            flash("Invalid file format. Please upload a CSV file.", "danger")
    return render_template('fuzzy/upload.html', form=form)

@blueprint.route('/fuzzyfication')
def fuzzyfication():
    WorkloadResult.query.delete()
    RoughSetRule.query.delete()
    db.session.commit()

    raw_data = WorkloadData.query.all()

    for row in raw_data:
        cpu = row.used_cpus
        mem = row.used_memory
        if cpu >= 2 or mem >= 20000:
            status = 'Overutilized'
        elif cpu == 1 and 10000 <= mem < 20000:
            status = 'Optimal'
        else:
            status = 'Underutilized'

        db.session.add(WorkloadResult(
            job_id=row.job_id,
            submit_time=row.submit_time,
            start_time=row.start_time,
            end_time=row.end_time,
            requested_cpus=row.requested_cpus,
            used_cpus=row.used_cpus,
            requested_memory=row.requested_memory,
            used_memory=row.used_memory,
            execution_time=row.execution_time,
            queue_wait_time=row.queue_wait_time,
            user_id=row.user_id,
            job_type=row.job_type,
            priority_level=row.priority_level,
            node_count=row.node_count,
            interarrival_time=row.interarrival_time,
            resource_status=status,
            input_id=row.id
        ))
    db.session.commit()

    df = pd.DataFrame([{
        'CPU': row.used_cpus,
        'MEM': row.used_memory,
        'EXEC': row.execution_time
    } for row in raw_data])

    df['CPU_Level'] = pd.cut(df['CPU'], bins=[-1, 0.5, 1.5, float('inf')], labels=['Low', 'Medium', 'High'])
    df['Mem_Level'] = pd.cut(df['MEM'], bins=[-1, 10000, 20000, float('inf')], labels=['Low', 'Medium', 'High'])
    df['Exec_Level'] = pd.cut(df['EXEC'], bins=3, labels=['Short', 'Medium', 'Long'])

    def classify(cpu, mem):
        if cpu == 'High' or mem == 'High':
            return 'Overutilized'
        elif cpu == 'Medium' and mem == 'Medium':
            return 'Optimal'
        else:
            return 'Underutilized'

    df['Resource_Status'] = df.apply(lambda r: classify(r['CPU_Level'], r['Mem_Level']), axis=1)

    rst = RoughSetModule(df, ['CPU_Level', 'Mem_Level', 'Exec_Level'], 'Resource_Status')
    results = rst.run_all()

    for rule_dict, decision in results['rules']:
        rule = RoughSetRule(
            cpu_level=rule_dict.get('CPU_Level'),
            mem_level=rule_dict.get('Mem_Level'),
            exec_level=rule_dict.get('Exec_Level'),
            resource_status=decision
        )
        db.session.add(rule)
    db.session.commit()

    flash("Fuzzy-RST classification and rule extraction completed.")
    return redirect(url_for('fuzzy_blueprint.results'))

@blueprint.route('/results')
def results():
    results = WorkloadResult.query.all()
    return render_template('fuzzy/fuzzyfication.html', results=results)

@blueprint.route('/rules')
def rules():
    rules = RoughSetRule.query.all()
    return render_template('fuzzy/rules.html', rules=rules)

@blueprint.route('/logs')
def logs():
    raw_data = WorkloadData.query.all()

    df = pd.DataFrame([{
        'CPU': row.used_cpus,
        'MEM': row.used_memory,
        'EXEC': row.execution_time
    } for row in raw_data])

    df['CPU_Level'] = pd.cut(df['CPU'], bins=[-1, 0.5, 1.5, float('inf')], labels=['Low', 'Medium', 'High'])
    df['Mem_Level'] = pd.cut(df['MEM'], bins=[-1, 10000, 20000, float('inf')], labels=['Low', 'Medium', 'High'])
    df['Exec_Level'] = pd.cut(df['EXEC'], bins=3, labels=['Short', 'Medium', 'Long'])

    df['Resource_Status'] = df.apply(lambda r: 'Overutilized' if r['CPU_Level'] == 'High' or r['Mem_Level'] == 'High'
                                      else 'Optimal' if r['CPU_Level'] == 'Medium' and r['Mem_Level'] == 'Medium'
                                      else 'Underutilized', axis=1)

    rst = RoughSetModule(df, ['CPU_Level', 'Mem_Level', 'Exec_Level'], 'Resource_Status')
    result = rst.run_all()

    return render_template('fuzzy/logs.html', result=result)
