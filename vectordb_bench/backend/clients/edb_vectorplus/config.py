from collections.abc import Mapping, Sequence
from typing import Any, TypedDict

from pydantic import BaseModel, SecretStr

from ..api import DBCaseConfig, DBConfig, IndexType, MetricType

EDB_VECTORPLUS_URL_PLACEHOLDER = "postgresql://%s:%s@%s/%s"


class EdbVectorplusConfigDict(TypedDict):
    """These keys will be directly used as kwargs in psycopg connection string,
    so the names must match exactly psycopg API"""

    user: str
    password: str
    host: str
    port: int
    dbname: str


class EdbVectorplusConfig(DBConfig):
    user_name: SecretStr = "postgres"
    password: SecretStr
    host: str = "localhost"
    port: int = 5432
    db_name: str = "vectordb"
    table_name: str = "vdbbench_table_test"

    def to_dict(self) -> EdbVectorplusConfigDict:
        user_str = self.user_name.get_secret_value() if isinstance(self.user_name, SecretStr) else self.user_name
        pwd_str = self.password.get_secret_value()
        return {
            "connect_config": {
                "host": self.host,
                "port": self.port,
                "dbname": self.db_name,
                "user": user_str,
                "password": pwd_str,
            },
            "table_name": self.table_name,
        }


class EdbVectorplusIndexParam(TypedDict):
    metric: str
    lists: int
    rotation: bool
    maintenance_work_mem: str | None
    max_parallel_workers: int | None


class EdbVectorplusSearchParam(TypedDict):
    metric_fun_op: str


class EdbVectorplusSessionCommands(TypedDict):
    session_options: Sequence[dict[str, Any]]


_METRIC_OPS = {
    MetricType.L2: "vector_l2_ops",
    MetricType.IP: "vector_ip_ops",
    MetricType.COSINE: "vector_cosine_ops",
}

_METRIC_FUN_OPS = {
    MetricType.L2: "<->",
    MetricType.IP: "<#>",
    MetricType.COSINE: "<=>",
}


class EdbVectorplusIvfplusIndexConfig(BaseModel, DBCaseConfig):
    """The ivfplus access method (edb_vectorplus extension) divides vectors into lists,
    same as pgvector's ivfflat, plus an optional rotation preprocessing step and its own
    iterative/hierarchical probing knobs."""

    metric_type: MetricType | None = None
    index: IndexType = IndexType.IVFPLUS
    create_index_before_load: bool = False
    create_index_after_load: bool = True

    lists: int | None = None
    probes: int | None = None
    rotation: bool = True
    iterative_scan: str | None = None
    max_probes: int | None = None
    hierarchy_threshold: int | None = None
    maintenance_work_mem: str | None = None
    max_parallel_workers: int | None = None

    def parse_metric_op(self) -> str:
        return _METRIC_OPS[self.metric_type]

    def parse_metric_fun_op(self) -> str:
        return _METRIC_FUN_OPS[self.metric_type]

    def index_param(self) -> EdbVectorplusIndexParam:
        return {
            "metric": self.parse_metric_op(),
            "lists": self.lists,
            "rotation": self.rotation,
            "maintenance_work_mem": self.maintenance_work_mem,
            "max_parallel_workers": self.max_parallel_workers,
        }

    def search_param(self) -> EdbVectorplusSearchParam:
        return {"metric_fun_op": self.parse_metric_fun_op()}

    def session_param(self) -> EdbVectorplusSessionCommands:
        session_parameters = {
            "ivfplus.probes": self.probes,
            "ivfplus.iterative_scan": self.iterative_scan,
            "ivfplus.max_probes": self.max_probes,
            "ivfplus.hierarchy_threshold": self.hierarchy_threshold,
            "enable_seqscan": "off",
        }
        return {"session_options": self._optionally_build_set_options(session_parameters)}

    @staticmethod
    def _optionally_build_set_options(set_mapping: Mapping[str, Any]) -> Sequence[dict[str, Any]]:
        """Walk through options, creating 'SET 'key1 = "value1";' list"""
        session_options = []
        for setting_name, value in set_mapping.items():
            if value:
                session_options.append(
                    {
                        "parameter": {
                            "setting_name": setting_name,
                            "val": str(value),
                        },
                    },
                )
        return session_options


_edb_vectorplus_case_config = {
    IndexType.IVFPLUS: EdbVectorplusIvfplusIndexConfig,
}
