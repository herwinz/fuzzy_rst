from apps import db

class WorkloadData(db.Model):
    __tablename__ = 'workload_data'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(50))
    submit_time = db.Column(db.String(50))
    start_time = db.Column(db.String(50))
    end_time = db.Column(db.String(50))
    requested_cpus = db.Column(db.Integer)
    used_cpus = db.Column(db.Integer)
    requested_memory = db.Column(db.Integer)
    used_memory = db.Column(db.Integer)
    execution_time = db.Column(db.Float)
    queue_wait_time = db.Column(db.Float)
    user_id = db.Column(db.String(50))
    job_type = db.Column(db.String(50))
    priority_level = db.Column(db.String(20))
    node_count = db.Column(db.Integer)
    interarrival_time = db.Column(db.Integer)


class WorkloadResult(db.Model):
    __tablename__ = 'workload_result'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(50))
    submit_time = db.Column(db.String(50))
    start_time = db.Column(db.String(50))
    end_time = db.Column(db.String(50))
    requested_cpus = db.Column(db.Integer)
    used_cpus = db.Column(db.Integer)
    requested_memory = db.Column(db.Integer)
    used_memory = db.Column(db.Integer)
    execution_time = db.Column(db.Float)
    queue_wait_time = db.Column(db.Float)
    user_id = db.Column(db.String(50))
    job_type = db.Column(db.String(50))
    priority_level = db.Column(db.String(20))
    node_count = db.Column(db.Integer)
    interarrival_time = db.Column(db.Integer)
    resource_status = db.Column(db.String(20))
    input_id = db.Column(db.Integer, db.ForeignKey('workload_data.id'))
    input_ref = db.relationship("WorkloadData", backref=db.backref("results", lazy=True))


class RoughSetRule(db.Model):
    __tablename__ = 'rough_set_rules'

    id = db.Column(db.Integer, primary_key=True)
    cpu_level = db.Column(db.String(10), nullable=False)
    mem_level = db.Column(db.String(10), nullable=False)
    exec_level = db.Column(db.String(10), nullable=False)
    resource_status = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"<RoughSetRule({self.cpu_level}, {self.mem_level}, {self.exec_level}) => {self.resource_status}>"
